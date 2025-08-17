# 🧪 PII Evaluation Benchmarks

This folder contains all benchmark and evaluation tools for testing the PII detection, masking, and unmasking services.

## 📁 Files Structure

### Core Evaluation Scripts
- **`accurate_pii_evaluation.py`** - Main comprehensive PII evaluation script with ground truth validation
- **`generate_test_data.py`** - Generates synthetic CSV test data with known PII
- **`comprehensive_entity_test.py`** - Detailed testing for all entity types in pseudonym_map
- **`quick_entity_test.py`** - Quick validation of common entity types (now supports 100-1000+ cases per entity)
- **`massive_entity_test.py`** - Large-scale performance testing (1000-10000+ cases per entity)
- **`PII_Evaluation_Colab.ipynb`** - Google Colab notebook for cloud-based testing and visualization
- **`demo_detection_only.py`** - Performance comparison demo between detection-only and full pipeline modes

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

## 🎯 Features

### Test Modes
- **� Detection-Only Mode**: Test PII detection accuracy without masking/unmasking (faster execution)
- **🔄 Full Pipeline Mode**: Complete test including detection, masking, and unmasking roundtrip
- **📊 Multiple Scales**: From small (10-100 cases) to massive (10,000+ cases per entity)
- **🌍 English Data**: All test data generated in English for consistent Presidio performance

### Performance Analysis
- **⚡ Batch Processing**: Efficient processing of large datasets with batch optimization
- **📈 Throughput Measurement**: Cases per second processing speed analysis
- **💾 JSON Export**: Detailed results with timestamps and statistical summaries
- **📋 Entity-Specific Metrics**: Individual performance analysis for each PII type

### Local Testing

#### Run Standard Evaluation:
```bash
cd benchmarks
python accurate_pii_evaluation.py
```

#### Run Quick Test:
```bash
python accurate_pii_evaluation.py quick
```

#### Run Comprehensive Test:
```bash
python accurate_pii_evaluation.py comprehensive
```

#### Test Specific Entity Types:
```bash
# Quick validation of common entities (100+ cases per entity)
python quick_entity_test.py

# Test all entity types in pseudonym_map
python comprehensive_entity_test.py

# Large-scale performance testing
python massive_entity_test.py
```

#### Detection-Only Mode:
```bash
# Only test PII detection without masking/unmasking (faster)
python quick_entity_test.py --detection-only
python comprehensive_entity_test.py --detection-only
python massive_entity_test.py --detection-only

# Combine with scale options
python quick_entity_test.py --large --detection-only
python massive_entity_test.py --massive --detection-only
```

#### Performance Comparison Demo:
```bash
# Compare detection-only vs full pipeline performance
python demo_detection_only.py
```

### Google Colab Testing
1. **Upload** `PII_Evaluation_Colab.ipynb` to [Google Colab](https://colab.research.google.com)
2. **Run all cells** to install dependencies and setup environment
3. **Choose your test mode:**
   - **Quick Test**: 80 test cases (10 per entity type)
   - **Medium Test**: 800 test cases (100 per entity type)
   - **Large Test**: 4,000 test cases (500 per entity type)
   - **Massive Test**: 8,000+ test cases (1000+ per entity type)
4. **View results** with built-in visualizations and statistics

💡 **The Colab notebook includes all service implementations and doesn't require a running backend server.**
python quick_entity_test.py

# Quick test with different scales
python quick_entity_test.py --small      # 10 cases per entity
python quick_entity_test.py --medium     # 100 cases per entity  
python quick_entity_test.py --large      # 500 cases per entity
python quick_entity_test.py --massive    # 1000 cases per entity

# Custom number of cases
python quick_entity_test.py --cases 250

# Comprehensive entity testing
python comprehensive_entity_test.py

# Test specific entities only
python comprehensive_entity_test.py --entities PERSON EMAIL_ADDRESS PHONE_NUMBER

# List available entities
python comprehensive_entity_test.py --list

# Test with more samples per entity
python comprehensive_entity_test.py --samples 10

# Massive scale performance testing
python massive_entity_test.py --small     # 100 cases per entity
python massive_entity_test.py --medium    # 500 cases per entity
python massive_entity_test.py --large     # 1000 cases per entity
python massive_entity_test.py --massive   # 5000 cases per entity
python massive_entity_test.py --extreme   # 10000 cases per entity
```

### Generate New Test Data:
```bash
python generate_test_data.py
```

## 📊 Test Modes & Scales

### Standard Evaluation Modes:
| Mode | Dataset Size | Detection Samples | Masking Samples | Time | Reliability |
|------|-------------|------------------|----------------|------|-------------|
| Quick | 200 | 50 | 10 | ~30s | Low |
| Standard | 500 | 200 | 50 | ~2 min | Medium |
| Comprehensive | 1000 | 500 | 100 | ~5 min | High |

### Entity Testing Scales:
| Scale | Cases per Entity | Total Cases (8 entities) | Time | Use Case |
|-------|-----------------|-------------------------|------|----------|
| Small | 10 | 80 | ~30s | Quick validation |
| Medium | 100 | 800 | ~3-5 min | Regular testing |
| Large | 500 | 4,000 | ~15-20 min | Thorough testing |
| Massive | 1,000 | 8,000 | ~30-45 min | Performance analysis |
| Extreme | 5,000+ | 40,000+ | ~2-3 hours | Stress testing |

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
