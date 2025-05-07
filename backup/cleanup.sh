#!/bin/bash
# Clean up script for removing unnecessary files in the FinOps360 cost analysis project

# Create a backup directory
echo "Creating backup directory..."
mkdir -p backup

# 1. Clean up duplicate data files
echo "Cleaning up duplicate data files..."
# These are actually used by BigQuery loading scripts, so we'll keep them

# 2. Remove outdated schema files
echo "Removing outdated schema files..."
if [ -f "data/finops_schema.json" ]; then
  cp data/finops_schema.json backup/
  rm data/finops_schema.json
  echo "  Moved data/finops_schema.json to backup/"
fi

if [ -f "finops_schema.json" ]; then
  cp finops_schema.json backup/
  rm finops_schema.json
  echo "  Moved finops_schema.json to backup/"
fi

# 3. Delete old output files
echo "Deleting old output files..."
if [ -d "output" ]; then
  mkdir -p backup/output
  cp -r output/* backup/output/
  rm -f output/env_analysis_report_month_*.html
  rm -f output/env_analysis_report_month_*.txt
  echo "  Moved old output reports to backup/output/"
fi

# 4. Clean up duplicate scripts
echo "Cleaning up duplicate scripts..."
if [ -f "data/run_data_generator.py" ]; then
  cp data/run_data_generator.py backup/
  rm data/run_data_generator.py
  echo "  Moved data/run_data_generator.py to backup/"
fi

if [ -f "data/generate_finops_data.py" ]; then
  cp data/generate_finops_data.py backup/
  rm data/generate_finops_data.py
  echo "  Moved data/generate_finops_data.py to backup/"
fi

# 5. Remove example files
echo "Removing example files..."
if [ -d "examples" ]; then
  mkdir -p backup/examples
  cp -r examples/* backup/examples/
  rm -rf examples
  echo "  Moved examples/ directory to backup/"
fi

# 6. Remove duplicate finops_data files in the root directory
echo "Removing duplicate finops_data files..."
if [ -f "finops_data.csv" ]; then
  cp finops_data.csv backup/
  rm finops_data.csv
  echo "  Moved finops_data.csv to backup/"
fi

if [ -f "finops_data_noheader.csv" ]; then
  cp finops_data_noheader.csv backup/
  rm finops_data_noheader.csv
  echo "  Moved finops_data_noheader.csv to backup/"
fi

echo "Clean up complete! All removed files were backed up to the 'backup' directory."
echo "To restore any files, copy them back from the backup directory."