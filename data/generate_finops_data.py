import csv
import random
import datetime

def generate_random_date_2024():
    """
    Returns a random date in 2024 as YYYY-MM-DD format.
    """
    start = datetime.date(2023, 1, 1)
    end = datetime.date(2025, 4, 30)
    delta = end - start
    random_day = random.randrange(delta.days + 1)
    date = start + datetime.timedelta(days=random_day)
    return date.isoformat()  # Format: YYYY-MM-DD

def get_week_number(date_obj):
    """
    Get the week number in the year from a date.
    """
    dt = datetime.datetime.strptime(date_obj, "%Y-%m-%d").date()
    return dt.isocalendar()[1]

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

def get_month_name(month):
    """
    Convert numeric month to short name (e.g. 1 -> 'Jan')
    """
    return ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"][month - 1]

def generate_finops_data(num_rows=100000):
    """
    Generate a list of dictionaries with the new schema.
    """
    # CTOs/Tech leadership
    ctos = ["Michael Chen", "Sarah Johnson", "David Rodriguez", "Emma Williams", "James Smith"]
    
    # VPs under each CTO
    vps_by_cto = {
        "Michael Chen": ["Bob Jenkins", "Alice Taylor"],
        "Sarah Johnson": ["Charlie Adams", "Diana Miller"],
        "David Rodriguez": ["Emily Parker", "Frank Thomas"],
        "Emma Williams": ["George Wilson", "Hannah Davis"],
        "James Smith": ["Isabel Martinez", "Jack Brown"]
    }
    
    # Pillar teams
    pillar_teams = ["Retail", "Finance", "Marketing", "Operations", "Engineering"]
    
    # Subpillars for each pillar team
    subpillars = {
        "Retail": [(1, "E-commerce"), (2, "Store Operations"), (3, "Supply Chain")],
        "Finance": [(4, "Accounting"), (5, "Financial Planning"), (6, "Audit")],
        "Marketing": [(7, "Digital Marketing"), (8, "Brand Management"), (9, "Analytics")],
        "Operations": [(10, "Logistics"), (11, "Customer Service"), (12, "Process Optimization")],
        "Engineering": [(13, "Infrastructure"), (14, "Development"), (15, "Quality Assurance")]
    }
    
    # Products by subpillar
    products = {
        1: [(101, "Checkout System"), (102, "Product Catalog")],
        2: [(103, "Inventory Management"), (104, "POS System")],
        3: [(105, "Warehouse Control"), (106, "Shipping Automation")],
        4: [(107, "GL System"), (108, "Billing Platform")],
        5: [(109, "Budget Forecasting"), (110, "Financial Reporting")],
        6: [(111, "Compliance Tracking"), (112, "Risk Assessment")],
        7: [(113, "Campaign Management"), (114, "Social Media Analytics")],
        8: [(115, "Asset Management"), (116, "Brand Portal")],
        9: [(117, "Customer Analytics"), (118, "Market Research")],
        10: [(119, "Fleet Management"), (120, "Routing Optimization")],
        11: [(121, "CRM System"), (122, "Support Ticketing")],
        12: [(123, "Workflow Automation"), (124, "Performance Monitoring")],
        13: [(125, "Cloud Platform"), (126, "Network Management")],
        14: [(127, "Development Tools"), (128, "CI/CD Pipeline")],
        15: [(129, "Test Automation"), (130, "Bug Tracking")]
    }
    
    # Application names
    applications = ["MainApp", "SupportApp", "AdminPortal", "DataProcessor", "APIGateway", 
                    "FrontendUI", "BackendService", "MobileApp", "AnalyticsDashboard", "IntegrationHub"]
    
    # Service names
    services = {
        "AWS": ["EC2", "S3", "RDS", "Lambda", "DynamoDB", "Redshift", "CloudFront"],
        "Azure": ["VM", "Blob Storage", "SQL Database", "Functions", "Cosmos DB", "Synapse", "CDN"],
        "GCP": ["Compute Engine", "Cloud Storage", "Cloud SQL", "Cloud Functions", "Bigtable", "BigQuery", "Cloud CDN"]
    }
    
    # Environments with probabilities to ensure more realistic distribution
    envs = ["Prod", "Stage", "Dev", "Test", "QA"]
    env_weights = [0.35, 0.15, 0.3, 0.1, 0.1]  # 35% Prod, 15% Stage, 30% Dev, etc.
    
    # Clouds with regions
    clouds = ["AWS", "Azure", "GCP"]
    regions = {
        "AWS": ["us-east-1", "us-west-2", "eu-west-1", "ap-southeast-1", "sa-east-1"],
        "Azure": ["eastus", "westus2", "northeurope", "southeastasia", "brazilsouth"],
        "GCP": ["us-central1", "us-west1", "europe-west1", "asia-southeast1", "southamerica-east1"]
    }
    
    # Project IDs by cloud
    project_patterns = {
        "AWS": ["aws-acct-{}", "aws-proj-{}", "aws-{}-platform"],
        "Azure": ["azure-sub-{}", "azure-res-{}", "az-{}-infra"],
        "GCP": ["gcp-proj-{}", "gcp-{}-app", "g-cloud-{}"]
    }
    
    data_rows = []

    for _ in range(num_rows):
        # Generate date and derived time fields
        date_str = generate_random_date_2024()
        dt_obj = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
        year = dt_obj.year
        month_num = dt_obj.month
        month_name = get_month_name(month_num)
        quarter = get_quarter(month_num)
        week = get_week_number(date_str)
        
        # Generate fiscal year - assume FY runs July-June
        # If current month is Jan-Jun, FY is the previous year
        # If current month is Jul-Dec, FY is the current year
        if 1 <= month_num <= 6:
            fy = f"FY{year - 1}"
        else:
            fy = f"FY{year}"
        
        # Generate organizational hierarchy
        cto = random.choice(ctos)
        vp = random.choice(vps_by_cto[cto])
        pillar = random.choice(pillar_teams)
        subpillar_id, subpillar_name = random.choice(subpillars[pillar])
        product_id, product = random.choice(products[subpillar_id])
        
        # Generate application and owner
        application = random.choice(applications)
        owner = f"{random.choice(['dev', 'admin', 'svc', 'app'])}.{application.lower()}@example.com"
        
        # Generate cloud details
        cloud = random.choice(clouds)
        region = random.choice(regions[cloud])
        service = random.choice(services[cloud])
        
        # Generate environment with weighted selection
        environment = random.choices(envs, weights=env_weights, k=1)[0]
        
        # Generate project ID
        pattern = random.choice(project_patterns[cloud])
        project_id = pattern.format(random.randint(1000, 9999))
        
        # Generate cost - larger range for production environments
        if environment == "Prod":
            cost = round(random.uniform(1000, 25000), 2)
        else:
            cost = round(random.uniform(100, 8000), 2)

        row = {
            "date": date_str,
            "year": year,
            "cloud": cloud,
            "cto": cto,
            "vp": vp,
            "tr_product_pillar_team": pillar,
            "tr_subpillar_id": subpillar_id,
            "tr_subpillar_name": subpillar_name,
            "tr_product": product,
            "tr_product_id": product_id,
            "owner": owner,
            "application": application,
            "service_name": service,
            "environment": environment,
            "region": region,
            "project_id": project_id,
            "cost": cost,
            "fy": fy,
            "qtr": quarter,
            "week": week,
            # Add fields needed for the environment cost analysis
            "Month": month_name,
            "ORG": application,  # Use application as the organization for compatibility
            "PILLAR": pillar,
            "Application_Name": application,
            "Env": environment,  # Map environment to Env
            "WM_WEEK": f"Week {week:02d}"
        }

        data_rows.append(row)

    return data_rows

def write_csv(filename="finops_data.csv", num_rows=10000):
    """
    Generate the data and write out to a CSV.
    """
    fieldnames = [
        "date", "year", "cloud", "cto", "vp", "tr_product_pillar_team", 
        "tr_subpillar_id", "tr_subpillar_name", "tr_product", "tr_product_id", 
        "owner", "application", "service_name", "environment", "region", 
        "project_id", "cost", "fy", "qtr", "week",
        # Additional fields for backward compatibility with environment analysis
        "Month", "ORG", "PILLAR", "Application_Name", "Env", "WM_WEEK", "Cloud"
    ]
    
    data = generate_finops_data(num_rows)

    with open(filename, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in data:
            # Ensure Cloud field is populated for backward compatibility
            row["Cloud"] = row["cloud"]
            writer.writerow(row)

if __name__ == "__main__":
    write_csv("finops_data.csv", 100000)
    print("CSV file 'finops_data.csv' with 100,000 rows has been generated!")
