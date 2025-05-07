#!/usr/bin/env python3
"""Script to run the data generator"""
import os
import sys
import subprocess

# Get the directory of this script
script_dir = os.path.dirname(os.path.abspath(__file__))

# Change to the project root directory
os.chdir(os.path.dirname(script_dir))

# Run the data generator script
generator_path = os.path.join(script_dir, 'generate_updated_data.py')
print(f"Running {generator_path}")

# Import and run the generator directly
sys.path.insert(0, script_dir)
from generate_updated_data import generate_cost_data, generate_avg_daily_cost_data, create_headerless_file, create_bigquery_schema_files

# Create schema files
cost_schema_file, avg_schema_file = create_bigquery_schema_files()

# Generate cost data
cost_file = generate_cost_data(start_date="2024-01-01", end_date="2026-12-31")
avg_file = generate_avg_daily_cost_data(start_date="2023-01-01", end_date="2026-12-31")

# Create headerless versions
cost_headerless = os.path.join("data", "cost_analysis_new_no_header.csv")
avg_headerless = os.path.join("data", "avg_daily_cost_no_header.csv")
create_headerless_file(cost_file, cost_headerless)
create_headerless_file(avg_file, avg_headerless)

print("Data generation completed!")