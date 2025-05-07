import csv
import random
import datetime
import calendar

def generate_date_range(start_date, end_date):
    """
    Generate all dates between start_date and end_date.
    Returns a list of date objects.
    """
    delta = end_date - start_date
    return [start_date + datetime.timedelta(days=i) for i in range(delta.days + 1)]

def get_quarter(month):
    """
    Given a month (1-12), return quarter number (1-4)
    """
    if 1 <= month <= 3:
        return 1
    elif 4 <= month <= 6:
        return 2
    elif 7 <= month <= 9:
        return 3
    else:
        return 4

def get_fiscal_year(date_obj):
    """
    Calculate fiscal year based on a date.
    Assuming fiscal year runs July through June.
    """
    if 1 <= date_obj.month <= 6:
        return f"FY{date_obj.year - 1}"
    else:
        return f"FY{date_obj.year}"

def generate_finops_data(start_date="2024-01-01", end_date="2026-12-31"):
    """
    Generate FinOps data matching the new schema for all days between start_date and end_date.
    """
    # Parse input dates
    start = datetime.datetime.strptime(start_date, "%Y-%m-%d").date()
    end = datetime.datetime.strptime(end_date, "%Y-%m-%d").date()
    
    # Generate all dates in the range
    all_dates = generate_date_range(start, end)
    
    # Define seed entities based on new schema
    
    # CTOs/Tech leadership
    ctos = ["Michael Chen", "Sarah Johnson", "David Rodriguez", "Emma Williams", "James Smith"]
    
    # Product Pillar Teams
    product_pillars = [
        "Core Platform",
        "Data Analytics", 
        "Enterprise Solutions",
        "User Experience",
        "Infrastructure Services"
    ]
    
    # Products by pillar
    products = {
        "Core Platform": [
            "API Gateway", 
            "Authentication Services", 
            "Message Queue",
            "Payment Processing"
        ],
        "Data Analytics": [
            "Data Lake", 
            "Reporting Dashboard", 
            "Prediction Engine",
            "Customer Insights"
        ],
        "Enterprise Solutions": [
            "ERP System", 
            "CRM Platform", 
            "Business Intelligence",
            "Workflow Management"
        ],
        "User Experience": [
            "Web Frontend", 
            "Mobile App", 
            "Design System",
            "Content Delivery"
        ],
        "Infrastructure Services": [
            "Database Service", 
            "Compute Platform", 
            "Storage Service",
            "Identity Management"
        ]
    }
    
    # Managed Services
    managed_services = {
        "AWS": [
            "EC2", "S3", "RDS", "Lambda", "DynamoDB", 
            "Redshift", "CloudFront", "EKS", "ECS", "SQS"
        ],
        "Azure": [
            "VM", "Blob Storage", "SQL Database", "Functions", 
            "Cosmos DB", "Synapse", "CDN", "AKS", "Container Registry", "Service Bus"
        ],
        "GCP": [
            "Compute Engine", "Cloud Storage", "Cloud SQL", "Cloud Functions", 
            "Bigtable", "BigQuery", "Cloud CDN", "GKE", "Cloud Run", "Pub/Sub"
        ]
    }
    
    # Clouds
    clouds = ["AWS", "Azure", "GCP"]
    
    # Environments with probabilities for more realistic distribution
    environments = {
        "p": 0.40,    # Production
        "np": 0.60    # Non-Production
    }
    
    data_rows = []
    
    # Generate one record per cloud per product per day
    # This approach creates a consistent dataset across the time range
    for date_obj in all_dates:
        for cloud in clouds:
            for pillar in product_pillars:
                for product in products[pillar]:
                    # Assign a fixed CTO for each product (for consistency)
                    cto = ctos[hash(product) % len(ctos)]
                    
                    # Generate both production and non-production entries
                    for env, env_prob in environments.items():
                        # Skip some entries based on probability
                        if random.random() > env_prob:
                            continue
                            
                        # Select managed service
                        managed_service = random.choice(managed_services[cloud])
                        
                        # Generate cost with some randomness but consistent trends
                        # Base cost depends on the environment (prod costs more)
                        base_cost = 500 if env == "p" else 200
                        
                        # Add product-specific component (some products cost more)
                        product_factor = 1.0 + (hash(product) % 5) / 10.0  # 1.0 to 1.4
                        
                        # Add time-based growth (costs increase over time)
                        days_from_start = (date_obj - start).days
                        growth_factor = 1.0 + (days_from_start / 365) * 0.15  # 15% annual growth
                        
                        # Add some daily variance
                        daily_variance = random.uniform(0.8, 1.2)
                        
                        # Calculate final cost
                        cost = round(base_cost * product_factor * growth_factor * daily_variance, 2)
                        
                        # Build the data row matching the new schema
                        row = {
                            "year": date_obj.year,
                            "fy": get_fiscal_year(date_obj),
                            "qtr": get_quarter(date_obj.month),
                            "month": date_obj.month,
                            "cloud": cloud,
                            "cto": cto,
                            "tr_product_pillar_team": pillar,
                            "tr_product": product,
                            "managed_service": managed_service,
                            "environment": env,
                            "cost": cost
                        }
                        
                        data_rows.append(row)
    
    return data_rows

def write_csv(filename="finops_data.csv", start_date="2024-01-01", end_date="2026-12-31"):
    """
    Generate the data and write out to a CSV.
    """
    fieldnames = [
        "year", "fy", "qtr", "month", "cloud", 
        "cto", "tr_product_pillar_team", "tr_product",
        "managed_service", "environment", "cost"
    ]
    
    print(f"Generating data from {start_date} to {end_date}...")
    data = generate_finops_data(start_date, end_date)
    
    print(f"Writing {len(data)} rows to {filename}...")
    with open(filename, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        # We write the header for human readability, but the BigQuery loader will skip it
        writer.writeheader()
        for row in data:
            writer.writerow(row)
    
    # Also create a headerless version for direct BigQuery loading
    headerless_filename = filename.replace(".csv", "_noheader.csv")
    with open(headerless_filename, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        # No header row
        for row in data:
            writer.writerow(row)
    
    print(f"CSV file '{filename}' with {len(data)} rows has been generated!")
    print(f"Headerless version also created as '{headerless_filename}' for direct BigQuery loading")

def write_bigquery_schema_json(filename="finops_schema.json"):
    """
    Generate a BigQuery schema JSON file.
    """
    schema = [
        {"name": "year", "type": "INTEGER", "mode": "NULLABLE", "description": "Calendar year"},
        {"name": "fy", "type": "STRING", "mode": "NULLABLE", "description": "Fiscal year (FYxxxx format)"},
        {"name": "qtr", "type": "INTEGER", "mode": "NULLABLE", "description": "Quarter (1-4)"},
        {"name": "month", "type": "INTEGER", "mode": "NULLABLE", "description": "Month (1-12)"},
        {"name": "cloud", "type": "STRING", "mode": "NULLABLE", "description": "Cloud provider (AWS, Azure, GCP)"},
        {"name": "cto", "type": "STRING", "mode": "NULLABLE", "description": "CTO/Tech leadership"},
        {"name": "tr_product_pillar_team", "type": "STRING", "mode": "NULLABLE", "description": "Product pillar team"},
        {"name": "tr_product", "type": "STRING", "mode": "NULLABLE", "description": "Product name"},
        {"name": "managed_service", "type": "STRING", "mode": "NULLABLE", "description": "Cloud managed service"},
        {"name": "environment", "type": "STRING", "mode": "NULLABLE", "description": "Environment (p=prod, np=non-prod)"},
        {"name": "cost", "type": "FLOAT", "mode": "NULLABLE", "description": "Daily cost in USD"}
    ]
    
    import json
    with open(filename, 'w') as f:
        json.dump(schema, f, indent=2)
    
    print(f"BigQuery schema file '{filename}' has been generated!")

if __name__ == "__main__":
    # Generate a full dataset from 2024 to 2026
    write_csv("finops_data.csv", "2024-01-01", "2026-12-31")
    
    # Also generate a BigQuery schema file
    write_bigquery_schema_json("finops_schema.json")
    
    print("Done!")