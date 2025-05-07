#!/bin/bash
# Optimize project structure by keeping only essential files for the dashboard

echo "Optimizing FinOps360 Cost Analysis project structure..."

# Create backup directory
echo "Creating backup directory..."
mkdir -p backup_full

# First, back up the entire project
echo "Backing up current project state..."
find . -type f -not -path "./backup*/*" -not -path "./.git/*" -exec cp --parents {} backup_full/ \;

# Create essential directories structure
mkdir -p essential/common
mkdir -p essential/data
mkdir -p essential/templates
mkdir -p essential/reports

# Copy essential files
echo "Copying essential files to new structure..."

# Core dashboard generation files
cp run.sh essential/
cp create_html_report.py essential/
cp config.yaml essential/
cp requirements.txt essential/
cp README.md essential/
cp cleanup.sh essential/

# Common utilities
cp common/finops_config.py essential/common/
cp common/finops_bigquery.py essential/common/

# Data files and scripts
cp data/cost_analysis_schema.json essential/data/
cp data/avg_daily_cost_schema.json essential/data/
cp data/create_avg_daily_view.sql essential/data/
cp data/generate_updated_data.py essential/data/
cp data/load_to_bigquery.sh essential/data/
cp data/run_bigquery_views.sh essential/data/
cp data/create_views.sh essential/data/

# HTML templates
cp templates/dashboard_template.html essential/templates/

# Move essential directory to replace current structure
echo "Are you sure you want to replace current directory structure with optimized version? (y/n)"
read -p "This will move non-essential files to backup/ directory: " confirm

if [ "$confirm" == "y" ] || [ "$confirm" == "Y" ]; then
    # Create another backup for safety
    mkdir -p backup_final
    find . -type f -not -path "./backup*/*" -not -path "./essential/*" -not -path "./.git/*" -exec cp --parents {} backup_final/ \;
    
    # Now move files to backup and replace with essential
    find . -type f -not -path "./backup*/*" -not -path "./essential/*" -not -path "./.git/*" | while read file; do
        rel_path="${file:2}" # Remove leading ./
        if [ -f "essential/$rel_path" ]; then
            # File is in essential, so it stays
            echo "Keeping: $rel_path"
        else
            # Move non-essential file to backup
            mkdir -p "backup/$(dirname "$rel_path")"
            mv "$file" "backup/$rel_path"
            echo "Moved to backup: $rel_path"
        fi
    done
    
    # Copy essential files to main directory
    cp -r essential/* .
    rm -rf essential
    
    echo "Project structure optimized successfully!"
    echo "Non-essential files backed up to backup/ directory"
    echo "Full project backup saved to backup_full/ directory"
else
    echo "Operation cancelled. Essential files are in the 'essential/' directory."
    echo "You can manually move them if desired."
fi