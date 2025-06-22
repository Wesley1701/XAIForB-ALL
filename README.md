# Capstone Project Group 3
- Boy Stroo (1061576)
- Niels Poldervaart (1006334)
- Quinn Rachman (1009001)
- Rick van Alphen (1006306)
- Wesley Zwaal (1026606)

## Dev Container:
### Requirements:
[Dev Containers Extension](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers)

### Quick Start:
- Clone repo :)
```
git clone https://github.com/Wesley1701/XAIForB-ALL.git
cd XAIForB-All
```
- Open Project in VS Code
- Reopen in Dev Container
  - Press `F1` (or `Cmd+Shift+P` / `Ctrl+Shift+P`)
  - Type `Dev Containers: Reopen in Container`
  - Wait while VS Code builds the container (first time only - Can take a few minutes)
  - You're now inside the dev container, extensions are installed inside the container so you probably miss some of your personal extensions

## Download Datasets
- Download ALL Dataset:
  - Run `download_gdc_files.py` by using this command: `python3 download_gdc_files.py ./REQUIRED/acute_variants_leukemia_manifest.txt ./data/GDC/downloads --workers 6`

- Download B-ALL Dataset:
  - Run `download_gdc_files.py` by using this command: `python3 download_gdc_files.py ./REQUIRED/common_precursor_b_all_manifest.txt ./data/GDC/downloads --workers 6`

> [!CAUTION]
> Might need to run the download commands again if there are missing files.

## Combine GDC files into dataset
### Covnert ALL .tsv files to .pq file
- Open `gdc_to_qp.ipynb`
- In first code block:
  - Change `METADATA_FILE` to `./data/REQUIRED/acute_variants_leukemia_metadata.json`
  - Change `OUTPUT_FILE` to `./data/ALL.pq`
- Run All code blocks
- Wait until code finishes

### Covnert ALL .tsv files to .pq file
- Open `gdc_to_qp.ipynb`
- In first code block:
  - Change `METADATA_FILE` to `./data/REQUIRED/common_precursor_b_all_metadata.json`
  - Change `OUTPUT_FILE` to `./data/B_ALL.pq`
- Run All code blocks
- Wait until code finishes

## Run Workflow
- Open `main_notebook.ipynb`
- Run All code blocks

> [!IMPORTANT]
> Make sure that the dataset `.pq` files are inside the `./data/`