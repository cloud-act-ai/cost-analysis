#!/bin/bash
# FinOps360 Cost Analysis Cleanup Script

echo "FinOps360 Cost Analysis Cleanup"
echo "------------------------------"

# Clean Python cache files
echo "Cleaning Python cache files..."
find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
find . -name "*.pyc" -type f -delete
find . -name "*.pyo" -type f -delete
find . -name "*.pyd" -type f -delete
find . -name ".pytest_cache" -type d -exec rm -rf {} + 2>/dev/null || true
find . -name ".coverage" -type f -delete
find . -name ".coverage.*" -type f -delete

# Clean IDE and OS files
echo "Cleaning IDE and OS specific files..."
find . -name ".DS_Store" -type f -delete
find . -name "*.swp" -type f -delete
find . -name "*.swo" -type f -delete

# Remove generated reports
echo "Cleaning generated HTML reports..."
find ./reports -name "*.html" -type f -delete

# Remove configuration files
echo "Removing configuration files..."
rm -f config.yaml credentials.json 2>/dev/null || true

echo "Cleanup complete!"