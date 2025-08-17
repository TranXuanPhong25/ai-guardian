# 🧪 PII Evaluation Benchmarks

This folder contains all benchmark and evaluation tools for testing the PII detection, masking, and unmasking services.

## 📁 Files Structure

### Core Evaluation Scripts
- **`accurate_pii_evaluation.py`** - Main comprehensive PII evaluation script with ground truth validation
- **`generate_test_data.py`** - Generates synthetic CSV test data with known PII

### Test Data
- **`simple_test_data.csv`** - Simple test dataset for quick validation
- **`complex_test_data_with_pii.csv`** - Complex dataset with mixed PII types
- **`labeled_dataset.json`** - Ground truth labels for accuracy validation

### Results & Reports
- **`accurate_pii_evaluation.json`** - Latest evaluation results in JSON format
- **`FINAL_ACCURACY_REPORT.md`** - Detailed accuracy analysis report

### Documentation
- **`PII_EVALUATION_README.md`** - Detailed guide for running evaluations
- **`requirements_evaluation.txt`** - Python dependencies for evaluation scripts

## 🚀 Quick Start

### Run Standard Evaluation:
```bash
cd benchmarks
python accurate_pii_evaluation.py
```

### Run Quick Test:
```bash
python accurate_pii_evaluation.py quick
```

### Run Comprehensive Test:
```bash
python accurate_pii_evaluation.py comprehensive
```

### Generate New Test Data:
```bash
python generate_test_data.py
```

## 📊 Test Modes

| Mode | Dataset Size | Detection Samples | Masking Samples | Time | Reliability |
|------|-------------|------------------|----------------|------|-------------|
| Quick | 200 | 50 | 10 | ~30s | Low |
| Standard | 500 | 200 | 50 | ~2 min | Medium |
| Comprehensive | 1000 | 500 | 100 | ~5 min | High |

## 🔗 Dependencies

Make sure to install evaluation requirements:
```bash
pip install -r requirements_evaluation.txt
```

## 📈 Output

All evaluation scripts generate:
- Console output with detailed metrics
- JSON results files for automation
- Statistical reliability indicators
- Performance improvement analysis

For detailed usage instructions, see `PII_EVALUATION_README.md`.
