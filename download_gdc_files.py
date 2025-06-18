import sys
import hashlib
import requests
import argparse
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
import time
from tqdm import tqdm
import pandas as pd

class GDCDownloader:
    def __init__(self, manifest_path, download_dir, max_workers=4, chunk_size=8192):
        self.manifest_path = Path(manifest_path)
        self.download_dir = Path(download_dir)
        self.max_workers = max_workers
        self.chunk_size = chunk_size
        self.base_url = "https://api.gdc.cancer.gov/data/"

        self.lock = Lock()
        self.completed = 0
        self.failed = 0
        self.skipped = 0

        self.download_dir.mkdir(parents=True, exist_ok=True)

        self.manifest = self.load_manifest()
        self.total_files = len(self.manifest)

        print(f"Loaded manifest with {self.total_files} files")
        print(f"Download directory: {self.download_dir}")
        print(f"Max workers: {self.max_workers}")

    def load_manifest(self):
        """Load and parse the manifest file."""
        try:
            manifest = pd.read_csv(self.manifest_path, sep='\t')
            required_columns = ['id', 'filename', 'md5', 'size']

            if not all(col in manifest.columns for col in required_columns):
                raise ValueError(f"Manifest missing required columns: {required_columns}")

            return manifest
        except Exception as e:
            print(f"Error loading manifest: {e}")
            sys.exit(1)

    def calculate_md5(self, file_path):
        """Calculate MD5 hash of a file."""
        hash_md5 = hashlib.md5()
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(self.chunk_size), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception:
            return None

    def verify_file(self, file_path, expected_md5, expected_size):
        """Verify file integrity using MD5 hash and size."""
        if not file_path.exists():
            return False

        if file_path.stat().st_size != expected_size:
            return False

        actual_md5 = self.calculate_md5(file_path)
        return actual_md5 == expected_md5

    def download_file(self, file_info, pbar):
        """Download a single file with verification."""
        file_id = file_info['id']
        filename = file_info['filename']
        expected_md5 = file_info['md5']
        expected_size = int(file_info['size'])

        file_path = self.download_dir / filename

        if self.verify_file(file_path, expected_md5, expected_size):
            with self.lock:
                self.skipped += 1
                pbar.set_postfix({
                    'Completed': self.completed,
                    'Failed': self.failed,
                    'Skipped': self.skipped,
                    'Current': filename[:30] + '...' if len(filename) > 30 else filename
                })
            return {'status': 'skipped', 'filename': filename, 'message': 'File already exists and verified'}

        url = f"{self.base_url}/{file_id}"

        try:
            response = requests.get(url, stream=True, timeout=30)
            response.raise_for_status()

            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=self.chunk_size):
                    if chunk:
                        f.write(chunk)

            if self.verify_file(file_path, expected_md5, expected_size):
                with self.lock:
                    self.completed += 1
                    pbar.update(1)
                    pbar.set_postfix({
                        'Completed': self.completed,
                        'Failed': self.failed,
                        'Skipped': self.skipped,
                        'Current': filename[:30] + '...' if len(filename) > 30 else filename
                    })
                return {'status': 'success', 'filename': filename}
            else:
                file_path.unlink(missing_ok=True)
                raise Exception("MD5 verification failed")

        except Exception as e:
            file_path.unlink(missing_ok=True)

            with self.lock:
                self.failed += 1
                pbar.set_postfix({
                    'Completed': self.completed,
                    'Failed': self.failed,
                    'Skipped': self.skipped,
                    'Current': filename[:30] + '...' if len(filename) > 30 else filename
                })

            return {'status': 'failed', 'filename': filename, 'error': str(e)}

    def get_pending_files(self):
        """Get list of files that need to be downloaded."""
        pending_files = []

        for _, row in self.manifest.iterrows():
            file_path = self.download_dir / row['filename']
            if not self.verify_file(file_path, row['md5'], int(row['size'])):
                pending_files.append(row.to_dict())

        return pending_files

    def download_all(self):
        """Download all files using multithreading."""
        pending_files = self.get_pending_files()

        if not pending_files:
            print("All files are already downloaded and verified!")
            return

        print(f"Found {len(pending_files)} files to download")

        total_size = sum(int(f['size']) for f in pending_files)
        print(f"Total size to download: {self.format_size(total_size)}")

        pbar = tqdm(total=len(pending_files), desc="Downloading", unit="files")
        pbar.set_postfix({
            'Completed': 0,
            'Failed': 0,
            'Skipped': 0,
            'Current': 'Starting...'
        })

        start_time = time.time()
        results = []

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_file = {
                executor.submit(self.download_file, file_info, pbar): file_info
                for file_info in pending_files
            }

            for future in as_completed(future_to_file):
                result = future.result()
                results.append(result)

        pbar.close()

        end_time = time.time()
        duration = end_time - start_time

        print(f"\nDownload Summary:")
        print(f"Total files processed: {len(pending_files)}")
        print(f"Successfully downloaded: {self.completed}")
        print(f"Already existed (skipped): {self.skipped}")
        print(f"Failed downloads: {self.failed}")
        print(f"Total time: {self.format_time(duration)}")

        if self.failed > 0:
            print(f"\nFailed downloads:")
            for result in results:
                if result['status'] == 'failed':
                    print(f"  - {result['filename']}: {result.get('error', 'Unknown error')}")
            print(f"\nRe-run the script to retry failed downloads.")

    @staticmethod
    def format_size(bytes_size):
        """Format bytes to human readable format."""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_size < 1024.0:
                return f"{bytes_size:.2f} {unit}"
            bytes_size /= 1024.0
        return f"{bytes_size:.2f} PB"

    @staticmethod
    def format_time(seconds):
        """Format seconds to human readable format."""
        if seconds < 60:
            return f"{seconds:.1f}s"
        elif seconds < 3600:
            return f"{int(seconds // 60)}m {int(seconds % 60)}s"
        else:
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            return f"{hours}h {minutes}m"

def check_gdc_api():
    """Check if GDC API is reachable."""
    try:
        response = requests.get("https://api.gdc.cancer.gov/status", timeout=10)
        response.raise_for_status()
        return True
    except requests.RequestException as e:
        print(f"Error connecting to GDC API: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description='Download files from GDC using manifest file')
    parser.add_argument('manifest', help='Path to the manifest.txt file')
    parser.add_argument('download_dir', help='Directory to download files to')
    parser.add_argument('--workers', type=int, default=4, help='Number of worker threads (default: 4)')
    parser.add_argument('--chunk-size', type=int, default=8192, help='Download chunk size in bytes (default: 8192)')

    args = parser.parse_args()

    check_gdc_api()

    if not Path(args.manifest).exists():
        print(f"Error: Manifest file '{args.manifest}' not found")
        sys.exit(1)

    downloader = GDCDownloader(
        manifest_path=args.manifest,
        download_dir=args.download_dir,
        max_workers=args.workers,
        chunk_size=args.chunk_size
    )

    try:
        downloader.download_all()
    except KeyboardInterrupt:
        print("\nDownload interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

# python3 download_gdc_files.py /path/to/manifest.txt /path/to/downloads --workers 4 --chunk-size 8192
if __name__ == "__main__":
    main()