
from pathlib import Path

# Project configuration
PROJECT_NAME = "YottaFlex AI Delinquency & Collections Management"

# Project root directory
BASE_DIR = Path(__file__).resolve().parent

# Reproducible random seed
RANDOM_SEED = 20261022

# Dataset configuration
STARTER_LOAN_COUNT = 100
FULL_LOAN_COUNT = 10_000

INSTALLMENTS_PER_LOAN = 3
DATASET_MONTHS = 12

# Synthetic data reference date
AS_OF_DATE = "2026-10-22"

# Output directories
DATA_DIR = BASE_DIR / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
GROUND_TRUTH_DIR = DATA_DIR / "ground_truth"

# Database
DATABASE_PATH = BASE_DIR / "data" / "yottaflex.db"
DATABASE_URL = f"sqlite:///{DATABASE_PATH}"

# Create required directories if missing
for directory in [
    RAW_DATA_DIR,
    PROCESSED_DATA_DIR,
    GROUND_TRUTH_DIR,
]:
    directory.mkdir(parents=True, exist_ok=True)
