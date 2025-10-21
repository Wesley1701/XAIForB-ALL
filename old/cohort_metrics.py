import os
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
import pandas as pd
import numpy as np
from combat.pycombat import pycombat
import pyarrow.parquet as pq
import gc
from inmoose.pycombat import pycombat_norm
from inmoose.cohort_qc.cohort_metric import CohortMetric
from inmoose.cohort_qc.qc_report import QCReport

def validate_batch_correction_with_inmoose(original_data_path, corrected_data_path, metadata_path, output_report_dir="data/reports"):
    """
    Validate batch correction using inmoose's built-in QC tools.
    """
    print("Loading data for validation...")

    try:
        original_df = pd.read_parquet(original_data_path)
        corrected_df = pd.read_parquet(corrected_data_path)
        metadata_df = pd.read_parquet(metadata_path)
    except Exception as e:
        print(f"Error loading data files: {e}")
        return None, None

    if 'sample_id' in metadata_df.columns:
        metadata_df = metadata_df.set_index('sample_id')

    common_samples = original_df.index
    common_samples = common_samples.intersection(corrected_df.index)
    common_samples = common_samples.intersection(metadata_df.index)

    if len(common_samples) == 0:
        print("Error: No common samples across all dataframes. Check indices and content.")
        return None, None

    original_aligned = original_df.loc[common_samples]
    corrected_aligned = corrected_df.loc[common_samples]
    clinical_df_aligned = metadata_df.loc[common_samples].copy()

    print(f"Number of common samples for QC: {len(common_samples)}")
    print(f"Original data (aligned) shape: {original_aligned.shape}")
    print(f"Corrected data (aligned) shape: {corrected_aligned.shape}")
    print(f"Clinical data (aligned) shape: {clinical_df_aligned.shape}")

    print("Transposing expression data for CohortMetric (Genes x Samples)...")
    original_aligned_T = original_aligned.T
    corrected_aligned_T = corrected_aligned.T
    print(f"Original data (transposed) shape: {original_aligned_T.shape}")
    print(f"Corrected data (transposed) shape: {corrected_aligned_T.shape}")


    print("\nCreating CohortMetric object...")
    try:
        cohort_qc = CohortMetric(
            clinical_df=clinical_df_aligned,
            batch_column="batch",
            data_expression_df=corrected_aligned_T,
            data_expression_df_before=original_aligned_T,
            covariates=["condition"]
        )
    except ValueError as e:
        print(f"\nERROR: Failed to create CohortMetric: {e}")
        print("This often means your 'batch_column' or 'covariates' column in clinical_df_aligned")
        print("has too few unique values (e.g., only one batch/condition found).")
        print("Please check the 'DEBUG: Batch distribution...' output above.")
        return None, None


    print("Processing cohort metrics (this may take a few minutes for larger datasets)...")
    cohort_qc.process()

    del original_aligned, corrected_aligned, clinical_df_aligned
    del original_df, corrected_df, metadata_df
    del common_samples
    gc.collect()

    print("Generating QC Report...")
    os.makedirs(output_report_dir, exist_ok=True)

    qc_report = QCReport(cohort_qc)

    report_path = os.path.join(output_report_dir, 'inmoose_qc_report.html')
    print(f"Saving QC report to {report_path}...")
    qc_report.save_report(output_path=output_report_dir)

    print("\n" + "="*50)
    print("BATCH CORRECTION VALIDATION SUMMARY")
    print("="*50)
    print(f"Batch correction validation completed!")
    print(f"QC report saved to '{report_path}'")
    print(f"Clinical data samples: {len(clinical_df_aligned)}")
    print(f"Expression data samples: {corrected_aligned_T.shape[1]}")
    print(f"Number of genes: {corrected_aligned_T.shape[0]}")

    return qc_report, cohort_qc

if __name__ == "__main__":
    qc_report, cohort_qc = validate_batch_correction_with_inmoose(
        original_data_path="data/merged_dataset_log_transformed.pq",
        corrected_data_path="data/merged_dataset_batch_corrected.pq",
        metadata_path="data/merged_metadata.pq"
    )