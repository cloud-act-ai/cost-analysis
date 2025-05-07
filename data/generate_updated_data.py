#!/usr/bin/env python3
"""
Generate sample FinOps data for testing with the updated schema.
This script creates test data matching both the cost-analysis-new schema and avg_daily_cost_table.
"""
import csv
import random
import datetime
import os
import sys
import json
import argparse
from typing import List, Dict, Any, Tuple

def generate_date_range(start_date, end_date):
    """Generate a list of dates between start_date and end_date."""
    delta = end_date - start_date
    return [start_date + datetime.timedelta(days=i) for i in range(delta.days + 1)]

def generate_cost_data(start_date="2024-01-01", end_date="2026-12-31", output_dir="data"):
    """
    Generate sample cost data for the cost-analysis-new schema.
    
    Args:
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
        output_dir: Directory to save the output CSV
    
    Returns:
        Path to the generated CSV file
    """
    # Parse input dates
    start = datetime.datetime.strptime(start_date, "%Y-%m-%d").date()
    end = datetime.datetime.strptime(end_date, "%Y-%m-%d").date()
    
    # Generate all dates in the range
    all_dates = generate_date_range(start, end)
    
    # Define seed entities
    clouds = ["AWS", "GCP", "Azure"]
    
    # Define CTOs
    ctos = [
        "TEST MARKETS", 
        "ARGENTINA TECHNOLOGY", 
        "GLOBAL PLATFORM", 
        "CONSUMER EXPERIENCE", 
        "SUPPLY CHAIN TECH"
    ]
    
    # Define product pillar teams
    product_pillars = {
        "TEST MARKETS": ["ARGENTINA TECHNOLOGY", "BRAZIL TECHNOLOGY", "MEXICO TECH"],
        "ARGENTINA TECHNOLOGY": ["INVENTORY SYSTEMS", "CUSTOMER SYSTEMS", "LOGISTICS TECH"],
        "GLOBAL PLATFORM": ["API PLATFORM", "CLOUD PLATFORM", "INFRASTRUCTURE"],
        "CONSUMER EXPERIENCE": ["MOBILE", "WEB", "CHECKOUT"],
        "SUPPLY CHAIN TECH": ["WAREHOUSE MGMT", "TRANSPORT MGMT", "VENDOR SYSTEMS"]
    }
    
    # Define products
    products = {
        "ARGENTINA TECHNOLOGY": ["inventory", "security", "checkout", "logistics"],
        "BRAZIL TECHNOLOGY": ["orders", "catalog", "pricing", "promotions"],
        "MEXICO TECH": ["user-accounts", "cart", "search", "recommendations"],
        "INVENTORY SYSTEMS": ["stock-tracking", "replenishment", "allocation"],
        "CUSTOMER SYSTEMS": ["profiles", "preferences", "history", "support"],
        "LOGISTICS TECH": ["routing", "scheduling", "delivery", "tracking"],
        "API PLATFORM": ["api-gateway", "event-broker", "service-mesh"],
        "CLOUD PLATFORM": ["compute", "storage", "database", "networking"],
        "INFRASTRUCTURE": ["monitoring", "logging", "security", "backup"],
        "MOBILE": ["ios-app", "android-app", "mobile-web", "notifications"],
        "WEB": ["frontend", "cms", "seo", "analytics"],
        "CHECKOUT": ["payments", "cart", "tax", "shipping"],
        "WAREHOUSE MGMT": ["receiving", "picking", "packing", "shipping"],
        "TRANSPORT MGMT": ["fleet", "routing", "tracking", "scheduling"],
        "VENDOR SYSTEMS": ["onboarding", "catalog", "payments", "performance"]
    }
    
    # Define product IDs (we'll generate these)
    product_ids = {}
    for team, prods in products.items():
        product_ids[team] = {}
        for product in prods:
            product_ids[team][product] = str(random.randint(100, 9999))
    
    # Define managed services
    managed_services = {
        "AWS": ["EC2", "S3", "RDS", "Lambda", "DynamoDB", "ADVANCED DATA SECURITY", "ECS", "EKS"],
        "Azure": ["VM", "Blob Storage", "SQL Database", "Functions", "Cosmos DB", "SECURITY CENTER", "AKS"],
        "GCP": ["Compute Engine", "Cloud Storage", "Cloud SQL", "Cloud Functions", "Bigtable", "SECURITY COMMAND", "GKE"]
    }
    
    # Create output directory if it doesn't exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Create output file
    output_file = os.path.join(output_dir, "cost_analysis_new.csv")
    
    # Define CSV headers
    headers = [
        "date", "cto", "cloud", "tr_product_pillar_team", "tr_subpillar_name", 
        "tr_product_id", "tr_product", "managed_service", "environment", "cost"
    ]
    
    # Open the file for writing
    with open(output_file, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(headers)  # Write headers
        
        # Generate records
        for date_obj in all_dates:
            # Get date string
            date_str = date_obj.strftime("%Y-%m-%d")
            
            for cto in ctos:
                # Select pillar teams for this CTO
                available_pillars = product_pillars.get(cto, [cto])
                
                for pillar in available_pillars:
                    # Get or generate subpillar (use empty string if not available)
                    if pillar in products:
                        subpillar_name = ""
                    else:
                        subpillar_name = pillar
                        # Find the parent pillar
                        for parent, subs in product_pillars.items():
                            if pillar in subs:
                                pillar = parent
                                break
                    
                    # Get products for this pillar
                    pillar_products = products.get(subpillar_name if subpillar_name else pillar, ["default"])
                    
                    for product in pillar_products:
                        # Get product ID
                        product_id = product_ids.get(subpillar_name if subpillar_name else pillar, {}).get(product, str(random.randint(100, 9999)))
                        
                        for cloud in clouds:
                            # Get managed services for this cloud
                            cloud_services = managed_services.get(cloud, ["Generic Service"])
                            managed_service = random.choice(cloud_services)
                            
                            # Generate for both PROD and NON-PROD
                            for env in ["PROD", "NON-PROD"]:
                                # Calculate cost with various factors
                                base_cost = random.uniform(1, 10)  # Base cost
                                
                                # Production costs more
                                env_factor = 2.5 if env == "PROD" else 1.0
                                
                                # Different clouds have different costs
                                cloud_factor = 1.2 if cloud == "AWS" else 1.1 if cloud == "Azure" else 1.0
                                
                                # Cost grows over time
                                days_since_start = (date_obj - start).days
                                growth_factor = 1.0 + (days_since_start / 365 * 0.2)  # 20% annual growth
                                
                                # Random daily variance
                                daily_variance = random.uniform(0.8, 1.2)
                                
                                # Calculate final cost
                                cost = round(base_cost * env_factor * cloud_factor * growth_factor * daily_variance, 2)
                                
                                # Write record
                                writer.writerow([
                                    date_str,
                                    cto,
                                    cloud,
                                    pillar,
                                    subpillar_name,
                                    product_id,
                                    product,
                                    managed_service,
                                    env,
                                    cost
                                ])
    
    print(f"Generated cost analysis data with {len(all_dates)} days, saved to {output_file}")
    return output_file

def generate_avg_daily_cost_data(start_date="2023-01-01", end_date="2026-12-31", output_dir="data"):
    """
    Generate average daily cost data for the avg_daily_cost_table schema.
    
    Args:
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
        output_dir: Directory to save the output CSV
    
    Returns:
        Path to the generated CSV file
    """
    # Parse input dates
    start = datetime.datetime.strptime(start_date, "%Y-%m-%d").date()
    end = datetime.datetime.strptime(end_date, "%Y-%m-%d").date()
    
    # Generate monthly dates (first of each month)
    current_date = start.replace(day=1)
    monthly_dates = []
    while current_date <= end:
        monthly_dates.append(current_date)
        # Get next month
        if current_date.month == 12:
            current_date = current_date.replace(year=current_date.year + 1, month=1)
        else:
            current_date = current_date.replace(month=current_date.month + 1)
    
    # Define CTOs and environments
    ctos = [
        "Inventory Markets", 
        "Technology Platform",
        "Customer Experience",
        "Supply Chain",
        "Security & Compliance"
    ]
    
    environments = ["prod", "Non-Prod"]
    
    # Create output file
    output_file = os.path.join(output_dir, "avg_daily_cost.csv")
    
    # Define CSV headers
    headers = [
        "date", "environment_type", "cto", "fy24_avg_daily_spend", "fy25_avg_daily_spend", 
        "fy26_ytd_avg_daily_spend", "fy26_forecasted_avg_daily_spend", "fy26_avg_daily_spend", "daily_cost"
    ]
    
    # Open the file for writing
    with open(output_file, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(headers)  # Write headers
        
        # Generate records
        for date_obj in monthly_dates:
            date_str = date_obj.strftime("%Y-%m-%d")
            
            for cto in ctos:
                for env in environments:
                    # Generate base spending amounts that grow over fiscal years
                    fy24_base = random.uniform(100000, 200000) if env == "prod" else random.uniform(20000, 50000)
                    
                    # FY25 is higher than FY24
                    fy25_avg = fy24_base * random.uniform(1.15, 1.35)
                    
                    # FY26 YTD is higher than FY25
                    fy26_ytd_avg = fy25_avg * random.uniform(1.1, 1.3)
                    
                    # Forecasted spending (only for recent dates)
                    if date_obj.year >= 2025:
                        fy26_forecast = fy26_ytd_avg * random.uniform(1.05, 1.15)
                    else:
                        fy26_forecast = 0.0
                    
                    # Total FY26 spending (YTD + forecasted)
                    fy26_total = fy26_ytd_avg + (fy26_forecast if fy26_forecast > 0 else 0)
                    
                    # Daily cost around the average for the current date
                    if date_obj.year == 2023:
                        daily_cost = fy24_base * random.uniform(0.9, 1.1)
                    elif date_obj.year == 2024:
                        daily_cost = fy25_avg * random.uniform(0.9, 1.1)
                    else:
                        daily_cost = fy26_ytd_avg * random.uniform(0.9, 1.1)
                    
                    # Write record
                    writer.writerow([
                        date_str,
                        env,
                        cto,
                        round(fy24_base, 2),
                        round(fy25_avg, 2),
                        round(fy26_ytd_avg, 2),
                        round(fy26_forecast, 2),
                        round(fy26_total, 2),
                        round(daily_cost, 2)
                    ])
    
    print(f"Generated average daily cost data with {len(monthly_dates)} months, saved to {output_file}")
    return output_file

def create_bigquery_schema_files(output_dir="data"):
    """
    Create schema files for BigQuery loading.
    
    Args:
        output_dir: Directory to save the schema files
    """
    # Cost Analysis New schema
    cost_schema = [
        {"name": "date", "type": "DATE", "mode": "NULLABLE", "description": "Date of the cost entry"},
        {"name": "cto", "type": "STRING", "mode": "NULLABLE", "description": "CTO/Tech leadership organization"},
        {"name": "cloud", "type": "STRING", "mode": "NULLABLE", "description": "Cloud provider (AWS, Azure, GCP)"},
        {"name": "tr_product_pillar_team", "type": "STRING", "mode": "NULLABLE", "description": "Product pillar team"},
        {"name": "tr_subpillar_name", "type": "STRING", "mode": "NULLABLE", "description": "Sub-pillar name"},
        {"name": "tr_product_id", "type": "STRING", "mode": "NULLABLE", "description": "Product ID"},
        {"name": "tr_product", "type": "STRING", "mode": "NULLABLE", "description": "Product name"},
        {"name": "managed_service", "type": "STRING", "mode": "NULLABLE", "description": "Cloud managed service"},
        {"name": "environment", "type": "STRING", "mode": "NULLABLE", "description": "Environment (PROD, NON-PROD)"},
        {"name": "cost", "type": "FLOAT", "mode": "NULLABLE", "description": "Daily cost in USD"}
    ]
    
    # Avg Daily Cost schema
    avg_schema = [
        {"name": "date", "type": "DATE", "mode": "NULLABLE", "description": "Date of the cost entry"},
        {"name": "environment_type", "type": "STRING", "mode": "NULLABLE", "description": "Environment type (prod, non-prod)"},
        {"name": "cto", "type": "STRING", "mode": "NULLABLE", "description": "CTO/Tech leadership organization"},
        {"name": "fy24_avg_daily_spend", "type": "FLOAT", "mode": "NULLABLE", "description": "FY24 average daily spend"},
        {"name": "fy25_avg_daily_spend", "type": "FLOAT", "mode": "NULLABLE", "description": "FY25 average daily spend"},
        {"name": "fy26_ytd_avg_daily_spend", "type": "FLOAT", "mode": "NULLABLE", "description": "FY26 year-to-date average daily spend"},
        {"name": "fy26_forecasted_avg_daily_spend", "type": "FLOAT", "mode": "NULLABLE", "description": "FY26 forecasted average daily spend"},
        {"name": "fy26_avg_daily_spend", "type": "FLOAT", "mode": "NULLABLE", "description": "FY26 total average daily spend"},
        {"name": "daily_cost", "type": "FLOAT", "mode": "NULLABLE", "description": "Current daily cost"}
    ]
    
    # Write schema files
    cost_schema_file = os.path.join(output_dir, "cost_analysis_schema.json")
    with open(cost_schema_file, 'w') as f:
        json.dump(cost_schema, f, indent=2)
    
    avg_schema_file = os.path.join(output_dir, "avg_daily_cost_schema.json")
    with open(avg_schema_file, 'w') as f:
        json.dump(avg_schema, f, indent=2)
    
    print(f"Created schema files at {cost_schema_file} and {avg_schema_file}")
    return cost_schema_file, avg_schema_file

def create_headerless_file(input_file, output_file):
    """Create a copy of the CSV file without headers."""
    with open(input_file, 'r') as infile:
        reader = csv.reader(infile)
        next(reader)  # Skip header
        
        with open(output_file, 'w', newline='') as outfile:
            writer = csv.writer(outfile)
            for row in reader:
                writer.writerow(row)
    
    print(f"Created headerless version at {output_file}")

def parse_args():
    parser = argparse.ArgumentParser(description="Generate test data for FinOps analysis (updated schema)")
    parser.add_argument('--cost-start-date', type=str, default="2024-01-01", 
                       help="Start date for cost data in YYYY-MM-DD format")
    parser.add_argument('--cost-end-date', type=str, default="2026-12-31",
                       help="End date for cost data in YYYY-MM-DD format")
    parser.add_argument('--avg-start-date', type=str, default="2023-01-01", 
                       help="Start date for average cost data in YYYY-MM-DD format")
    parser.add_argument('--avg-end-date', type=str, default="2026-12-31",
                       help="End date for average cost data in YYYY-MM-DD format")
    parser.add_argument('--output-dir', type=str, default="data",
                       help="Directory for output files")
    parser.add_argument('--no-header', action='store_true',
                       help="Also generate CSVs without headers for BigQuery loading")
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_args()
    
    try:
        # Generate schema files
        create_bigquery_schema_files(args.output_dir)
        
        # Generate the cost analysis CSV file
        cost_file = generate_cost_data(
            start_date=args.cost_start_date,
            end_date=args.cost_end_date,
            output_dir=args.output_dir
        )
        
        # Generate the average daily cost CSV file
        avg_file = generate_avg_daily_cost_data(
            start_date=args.avg_start_date,
            end_date=args.avg_end_date,
            output_dir=args.output_dir
        )
        
        # Optionally create headerless versions
        if args.no_header:
            cost_headerless = os.path.join(args.output_dir, "cost_analysis_new_no_header.csv")
            avg_headerless = os.path.join(args.output_dir, "avg_daily_cost_no_header.csv")
            create_headerless_file(cost_file, cost_headerless)
            create_headerless_file(avg_file, avg_headerless)
            
        print("Data generation completed successfully!")
        
    except Exception as e:
        print(f"Error generating data: {e}")
        sys.exit(1)