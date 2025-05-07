#!/bin/bash
# Script to load FinOps data to BigQuery
# This script will create new tables with updated schemas and load the data

# Configuration
PROJECT_ID="finops360-dev-2025"
DATASET="test"
COST_TABLE="cost_analysis_new"
AVG_TABLE="avg_daily_cost_table"
COST_SCHEMA_FILE="app/data/cost_analysis_schema.json"
AVG_SCHEMA_FILE="app/data/avg_daily_cost_schema.json"
COST_DATA_FILE="app/data/cost_analysis_new_no_header.csv"
AVG_DATA_FILE="app/data/avg_daily_cost_no_header.csv"

# Print configuration
echo "Loading data to BigQuery with the following configuration:"
echo "  Project: $PROJECT_ID"
echo "  Dataset: $DATASET"
echo "  Cost Analysis Table: $COST_TABLE"
echo "  Average Daily Cost Table: $AVG_TABLE"
echo "  Cost Schema: $COST_SCHEMA_FILE"
echo "  Average Daily Schema: $AVG_SCHEMA_FILE"
echo "  Cost Data: $COST_DATA_FILE"
echo "  Average Daily Data: $AVG_DATA_FILE"

# Check if necessary files exist
if [ ! -f "$COST_SCHEMA_FILE" ]; then
  echo "Error: Cost schema file $COST_SCHEMA_FILE not found!"
  exit 1
fi

if [ ! -f "$AVG_SCHEMA_FILE" ]; then
  echo "Error: Average daily schema file $AVG_SCHEMA_FILE not found!"
  exit 1
fi

if [ ! -f "$COST_DATA_FILE" ]; then
  echo "Error: Cost data file $COST_DATA_FILE not found!"
  echo "Running data generation script to create it..."
  python3 app/data/generate_data.py --no-header
  if [ ! -f "$COST_DATA_FILE" ]; then
    echo "Error: Failed to generate cost data file!"
    exit 1
  fi
fi

if [ ! -f "$AVG_DATA_FILE" ]; then
  echo "Error: Average daily data file $AVG_DATA_FILE not found!"
  echo "Running data generation script to create it..."
  python3 app/data/generate_data.py --no-header
  if [ ! -f "$AVG_DATA_FILE" ]; then
    echo "Error: Failed to generate average daily data file!"
    exit 1
  fi
fi

# Check if bq command is available
if ! command -v bq &> /dev/null; then
  echo "Error: Google Cloud CLI's bq command not found!"
  echo "Please install the Google Cloud CLI from https://cloud.google.com/sdk/docs/install"
  exit 1
fi

# Check if the user is logged in
if ! bq ls &> /dev/null; then
  echo "Error: You need to be logged in to Google Cloud to use bq."
  echo "Please run 'gcloud auth login' first."
  exit 1
fi


# Function to create and load a table
function process_table() {
  local table_name=$1
  local schema_file=$2
  local data_file=$3
  
  # Delete the table if it exists
  echo "Checking if table $table_name exists..."
  if bq ls "$PROJECT_ID:$DATASET" 2>/dev/null | grep -q "$table_name"; then
    echo "Table $PROJECT_ID:$DATASET.$table_name exists, deleting it..."
    bq rm -f "$PROJECT_ID:$DATASET.$table_name"
    if [ $? -ne 0 ]; then
      echo "Error: Failed to delete the table!"
      return 1
    fi
    echo "Table $table_name deleted successfully."
  else
    echo "Table $table_name does not exist, proceeding with creation."
  fi

  # Create the table with the schema
  echo "Creating table $PROJECT_ID:$DATASET.$table_name..."
  bq mk --table "$PROJECT_ID:$DATASET.$table_name" "$schema_file"
  if [ $? -ne 0 ]; then
    echo "Error: Failed to create the table $table_name! Trying alternative approach..."
    
    # Try an alternative approach to create the table
    echo "Creating table $table_name using query approach..."
    
    # Get schema from the schema file
    local schema_content=$(cat "$schema_file")
    
    # Create a SQL schema definition based on the JSON schema
    local TMP_SCHEMA_FILE=$(mktemp)
    echo "CREATE OR REPLACE TABLE \`$PROJECT_ID.$DATASET.$table_name\` (" > "$TMP_SCHEMA_FILE"
    
    # Parse the JSON schema file to extract columns for SQL
    # This is a simplified approach that assumes the schema file has the expected format
    python3 -c "
import json, sys
with open('$schema_file', 'r') as f:
    schema = json.load(f)
columns = []
for field in schema:
    name = field['name']
    type_map = {'STRING': 'STRING', 'INTEGER': 'INT64', 'FLOAT': 'FLOAT64', 'DATE': 'DATE'}
    type_sql = type_map.get(field['type'], 'STRING')
    columns.append(f'  {name} {type_sql}')
print(',\\n'.join(columns))
" >> "$TMP_SCHEMA_FILE"
    echo ");" >> "$TMP_SCHEMA_FILE"
    
    # Run the query to create the table
    bq query --use_legacy_sql=false < "$TMP_SCHEMA_FILE"
    if [ $? -ne 0 ]; then
      echo "Error: Both approaches to create the table $table_name failed!"
      rm "$TMP_SCHEMA_FILE"
      return 1
    fi
    rm "$TMP_SCHEMA_FILE"
    echo "Table $table_name created successfully using alternative approach."
  else
    echo "Table $table_name created successfully."
  fi

  # Load the data into the table
  echo "Loading data from $data_file into table $table_name..."
  bq load --source_format=CSV "$PROJECT_ID:$DATASET.$table_name" "$data_file"
  if [ $? -ne 0 ]; then
    echo "Error: Failed to load data into the table $table_name!"
    
    # Try with autodetect schema if the fixed schema fails
    echo "Trying with autodetect schema..."
    bq load --source_format=CSV --autodetect "$PROJECT_ID:$DATASET.$table_name" "$data_file"
    
    if [ $? -ne 0 ]; then
      echo "Error: Both loading approaches failed for $table_name!"
      return 1
    fi
    
    echo "Data loaded successfully into $table_name with autodetected schema."
  else
    echo "Data loaded successfully into $table_name."
  fi

  # Verify the data
  echo "Verifying data load for $table_name..."
  COUNT=$(bq query --use_legacy_sql=false --format=csv "SELECT COUNT(*) FROM \`$PROJECT_ID.$DATASET.$table_name\`" | tail -n 1)
  echo "Loaded $COUNT rows into $PROJECT_ID:$DATASET.$table_name"
  
  return 0
}

# Process the cost analysis table
echo "===== Processing Cost Analysis Table ====="
process_table "$COST_TABLE" "$COST_SCHEMA_FILE" "$COST_DATA_FILE"
COST_RESULT=$?

# Process the average daily cost table
echo "===== Processing Average Daily Cost Table ====="
process_table "$AVG_TABLE" "$AVG_SCHEMA_FILE" "$AVG_DATA_FILE"
AVG_RESULT=$?

# Check results
if [ $COST_RESULT -eq 0 ] && [ $AVG_RESULT -eq 0 ]; then
  echo "All tables processed successfully!"
else
  echo "Some tables failed to process properly. Please check the logs."
  exit 1
fi

echo "Done!"