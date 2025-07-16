# Sample Data Files

This directory contains various sample JSON files for testing the converter:

## Quick Testing
- `small_10.json` - 10 records for basic functionality testing
- `medium_100.json` - 100 records for feature testing
- `flat_structure.json` - 50 records with no nested objects
- `nested_structure.json` - 20 records with deeply nested data

## Performance Testing
- `medium_1k.json` - 1,000 records
- `large_10k.json` - 10,000 records
- `large_50k.json` - 50,000 records

## Stress Testing (if generated)
- `huge_100k.json` - 100,000 records (~25-50 MB)
- `huge_250k.json` - 250,000 records (~60-120 MB)
- `huge_500k.json` - 500,000 records (~120-250 MB)

## Usage
```bash
# Test with small file
python json_to_csv_converter.py samples/small_10.json

# Test CLI with specific fields
python json_to_csv_cli.py samples/medium_100.json output.csv id,name,email,industry

# Stress test with large file
python json_to_csv_converter.py samples/large_50k.json
```

## Regenerating Data
Run `python generate_sample_data.py` to recreate these files.
