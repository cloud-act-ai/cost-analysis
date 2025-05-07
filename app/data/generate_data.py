#!/usr/bin/env python3
"""
Generate sample data for FinOps360 cost analysis.
"""
import os
import sys
import csv
import json
import random
import argparse
from datetime import datetime, timedelta

def date_range(start_date, end_date):
    """Generate a range of dates"""
    for n in range(int((end_date - start_date).days) + 1):
        yield start_date + timedelta(n)

def generate_cost_analysis_data(with_header=True):
    """
    Generate sample cost analysis data.
    
    Args:
        with_header: Whether to include a header row in the CSV
        
    Returns:
        Path to the generated file
    """
    output_file = "app/data/cost_analysis_new.csv"
    output_file_no_header = "app/data/cost_analysis_new_no_header.csv"
    
    # Create schema-based header
    schema_file = "app/data/cost_analysis_schema.json"
    with open(schema_file, 'r') as f:
        schema = json.load(f)
    
    header = [field["name"] for field in schema]
    
    # Sample data configuration
    start_date = datetime(2024, 2, 1)
    end_date = datetime(2025, 5, 4)  # Current date - 3 days
    
    # Cloud provider, CTO and environment configuration
    cloud_providers = ["AWS", "GCP", "Azure"]
    cto_orgs = ["Technology", "Engineering", "Infrastructure"]
    
    # Product data
    products = [
        {"id": "P1001", "name": "Commerce Platform", "pillar": "Platform", "subpillar": "Core"},
        {"id": "P1002", "name": "Identity Service", "pillar": "Platform", "subpillar": "Identity"},
        {"id": "P1003", "name": "Data Analytics", "pillar": "Data", "subpillar": "Analytics"},
        {"id": "P1004", "name": "Payment Gateway", "pillar": "Financial", "subpillar": "Payments"},
        {"id": "P1005", "name": "Content API", "pillar": "Content", "subpillar": "API"},
        {"id": "P1006", "name": "Mobile App", "pillar": "Mobile", "subpillar": "Apps"},
        {"id": "P1007", "name": "Search Engine", "pillar": "Platform", "subpillar": "Search"},
        {"id": "P1008", "name": "Recommendation Engine", "pillar": "AI", "subpillar": "Recommendations"},
        {"id": "P1009", "name": "Marketing Analytics", "pillar": "Marketing", "subpillar": "Analytics"},
        {"id": "P1010", "name": "Customer Database", "pillar": "Data", "subpillar": "Storage"},
        {"id": "P1011", "name": "Security Service", "pillar": "Security", "subpillar": "Core"},
        {"id": "P1012", "name": "Notification Service", "pillar": "Platform", "subpillar": "Messaging"},
    ]
    
    # Managed services
    managed_services = {
        "AWS": ["EC2", "S3", "RDS", "Lambda", "Fargate", "DynamoDB", "Redshift"],
        "GCP": ["Compute Engine", "Cloud Storage", "BigQuery", "Cloud Functions", "Cloud Run", "Firestore"],
        "Azure": ["Virtual Machines", "Blob Storage", "SQL Database", "Functions", "CosmosDB", "Synapse"]
    }
    
    # Open the file and write data
    with open(output_file, 'w', newline='') as f:
        writer = csv.writer(f)
        
        # Write header if requested
        if with_header:
            writer.writerow(header)
        
        # Generate data for each date
        rows = []
        for date in date_range(start_date, end_date):
            date_str = date.strftime('%Y-%m-%d')
            
            # Generate data points for each environment and product combination
            for product in products:
                for env in ["PROD", "NON-PROD"]:
                    for cloud in cloud_providers:
                        if random.random() > 0.3:  # 70% chance to include this combination
                            continue
                            
                        cto = random.choice(cto_orgs)
                        managed_service = random.choice(managed_services[cloud])
                        
                        # Base cost with some randomness
                        base_cost = 100 + random.uniform(-20, 200) if env == "PROD" else 40 + random.uniform(-10, 80)
                        
                        # Add weekly pattern - weekends cost less
                        if date.weekday() >= 5:  # Saturday and Sunday
                            base_cost *= 0.6
                            
                        # Add monthly pattern - costs rise toward end of month
                        day_of_month = date.day
                        days_in_month = (date.replace(month=date.month+1, day=1) if date.month < 12 
                                      else date.replace(year=date.year+1, month=1, day=1)).replace(day=1) - timedelta(days=1)
                        days_in_month = days_in_month.day
                        
                        if day_of_month > days_in_month - 5:
                            base_cost *= 1.2  # 20% increase at end of month
                            
                        # Add growth trend over time
                        days_since_start = (date - start_date).days
                        growth_factor = 1 + (days_since_start / 365) * 0.12  # 12% annual growth
                        
                        # Final cost
                        cost = base_cost * growth_factor
                        
                        # Create the row
                        row = [
                            date_str,
                            cto,
                            cloud,
                            product["pillar"],
                            product["subpillar"],
                            product["id"],
                            product["name"],
                            managed_service,
                            env,
                            round(cost, 2)
                        ]
                        
                        rows.append(row)
                        writer.writerow(row)
    
    # Create a no-header version if requested
    if not with_header or True:  # Always create both versions
        with open(output_file_no_header, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerows(rows)
    
    print(f"Generated {len(rows)} rows of cost analysis data")
    return output_file if with_header else output_file_no_header

def generate_avg_daily_cost_data(with_header=True):
    """
    Generate sample average daily cost data.
    
    Args:
        with_header: Whether to include a header row in the CSV
        
    Returns:
        Path to the generated file
    """
    output_file = "app/data/avg_daily_cost.csv"
    output_file_no_header = "app/data/avg_daily_cost_no_header.csv"
    
    # Create schema-based header
    schema_file = "app/data/avg_daily_cost_schema.json"
    with open(schema_file, 'r') as f:
        schema = json.load(f)
    
    header = [field["name"] for field in schema]
    
    # Sample data configuration
    start_date = datetime(2025, 2, 1)
    end_date = datetime(2025, 5, 4)  # Current date - 3 days
    
    # Environment types
    env_types = ["PROD", "NON-PROD"]
    
    # CTO orgs
    cto_orgs = ["Technology", "Engineering", "Infrastructure"]
    
    # Open the file and write data
    with open(output_file, 'w', newline='') as f:
        writer = csv.writer(f)
        
        # Write header if requested
        if with_header:
            writer.writerow(header)
        
        # Generate data for each date
        rows = []
        
        for date in date_range(start_date, end_date):
            date_str = date.strftime('%Y-%m-%d')
            
            for env_type in env_types:
                for cto in cto_orgs:
                    # Different base costs for each environment
                    base_daily_cost = 2500 + random.uniform(-300, 300) if env_type == "PROD" else 1200 + random.uniform(-200, 200)
                    
                    # Add weekly pattern - weekends cost less
                    if date.weekday() >= 5:  # Saturday and Sunday
                        base_daily_cost *= 0.7
                    
                    # Add trend over time
                    days_since_start = (date - start_date).days
                    growth_factor = 1 + (days_since_start / 365) * 0.15  # 15% annual growth
                    
                    # FY averages
                    fy24_avg = base_daily_cost * 0.85  # FY24 was 15% lower
                    fy25_avg = base_daily_cost * 0.92  # FY25 was 8% lower
                    fy26_ytd_avg = base_daily_cost * 0.97  # FY26 YTD is slightly lower
                    
                    # Forecasted is based on YTD but with growth
                    forecast_factor = 1 + (days_since_start / 180) * 0.08  # Growing at 8% per half-year
                    fy26_forecast = base_daily_cost * forecast_factor
                    
                    # Overall FY26 average 
                    fy26_avg = (fy26_ytd_avg + fy26_forecast) / 2
                    
                    # Final daily cost with some random variation
                    daily_cost = base_daily_cost * growth_factor * random.uniform(0.9, 1.1)
                    
                    # Create the row
                    row = [
                        date_str,
                        env_type,
                        cto,
                        round(fy24_avg, 2),
                        round(fy25_avg, 2),
                        round(fy26_ytd_avg, 2),
                        round(fy26_forecast, 2),
                        round(fy26_avg, 2),
                        round(daily_cost, 2)
                    ]
                    
                    rows.append(row)
                    writer.writerow(row)
    
    # Create a no-header version if requested
    if not with_header or True:  # Always create both versions
        with open(output_file_no_header, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerows(rows)
    
    print(f"Generated {len(rows)} rows of average daily cost data")
    return output_file if with_header else output_file_no_header

def main():
    parser = argparse.ArgumentParser(description='Generate sample data for FinOps360 cost analysis')
    parser.add_argument('--no-header', action='store_true', help='Generate CSV files without headers')
    args = parser.parse_args()
    
    # Create all necessary directories
    os.makedirs('app/data', exist_ok=True)
    
    # Generate the data files
    cost_file = generate_cost_analysis_data(not args.no_header)
    avg_file = generate_avg_daily_cost_data(not args.no_header)
    
    print(f"Data generation complete.")
    print(f"- Cost analysis data: {cost_file}")
    print(f"- Average daily cost data: {avg_file}")
    print(f"- No-header versions are also available for BigQuery loading.")

if __name__ == "__main__":
    main()