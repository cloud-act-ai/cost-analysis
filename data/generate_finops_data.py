import csv
import random
import datetime

def generate_random_date_2024():
    """
    Returns a random date in 2024 as M/D/YY format (e.g. 8/7/24).
    """
    # 2024 is a leap year, so there are 366 days
    start = datetime.date(2023, 1, 1)
    end = datetime.date(2025, 4, 30)
    delta = end - start
    random_day = random.randrange(delta.days + 1)
    date = start + datetime.timedelta(days=random_day)
    # Format: M/D/YY
    return date.strftime("%-m/%-d/%y")

def get_wm_week(date_obj):
    """
    Example function to approximate 'Week XX' from the date.
    You can adapt logic as needed.
    """
    # Convert date string back to date object
    # We'll do a rough calculation of the 'week' in the year.
    # If you'd like consistent 'Week 01', 'Week 02', etc., you can refine this logic.
    start_of_year = datetime.date(2024, 1, 1)
    # Convert M/D/YY to date object
    # (We already have date as string from generate_random_date_2024, so let's parse it.)
    dt = datetime.datetime.strptime(date_obj, "%m/%d/%y").date()
    delta_weeks = (dt - start_of_year).days // 7 + 1
    return f"Week {delta_weeks:02d}"

def get_quarter(month):
    """
    Given a month (1-12), return 'Q1', 'Q2', 'Q3', or 'Q4'
    """
    if 1 <= month <= 3:
        return "Q1"
    elif 4 <= month <= 6:
        return "Q2"
    elif 7 <= month <= 9:
        return "Q3"
    else:
        return "Q4"

def get_month_name(month):
    """
    Convert numeric month to short name (e.g. 1 -> 'Jan')
    """
    return ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"][month - 1]

def generate_finops_data(num_rows=100000):
    """
    Generate a list of dictionaries, each containing
    the columns specified for FinOps data.
    """
    tr_products = [
        "INTL DATA AND ANALYTICS POC",
        "Big Data Pipeline",
        "Analytics Tools",
        "ML Platform",
        "Data Lakehouse",
        "ETL/ELT Jobs",
        "Streaming Analytics"
    ]
    orgs = ["Sunbird", "Moonbird", "Starling", "Eagle", "Hawk"]
    org_ads = [
        "all@sunbird.com",
        "finance@sunbird.com",
        "tech@moonbird.io",
        "info@starling.org",
        "eagle-team@eagle.net"
    ]
    vps = ["Bob", "Alice", "Charlie", "Diana", "Emily"]
    pillars = ["Retail", "Finance", "Marketing", "Operations", "Engineering"]
    applications = ["checkout", "sales", "reporting", "inventory", "riskengine"]
    clouds = ["AWS", "Azure", "GCP"]
    envs = ["Prod", "Stage", "Dev"]
    FYS=["2024", "2025", "2023"]
    
    data_rows = []

    for _ in range(num_rows):
        date_str = generate_random_date_2024()         # e.g. "8/7/24"
        # parse the month from that date to fill in QTR, Month, etc.
        dt_obj = datetime.datetime.strptime(date_str, "%m/%d/%y").date()
        month_num = dt_obj.month

        row = {}
        row["DATE"] = date_str
        row["WM_WEEK"] = get_wm_week(date_str)         # e.g. "Week 01"
        row["QTR"] = get_quarter(month_num)            # e.g. "Q1"
        row["Month"] = get_month_name(month_num)       # e.g. "Aug"
        row["FY"] = random.choice(FYS)                             # or you can randomize the fiscal year
        row["TR_PRODUCT"] = random.choice(tr_products)
        row["ORG"] = random.choice(orgs)
        row["Org_AD"] = random.choice(org_ads)
        row["VP"] = random.choice(vps)
        row["PILLAR"] = random.choice(pillars)
        row["Application_Name"] = random.choice(applications)
        row["Cloud"] = random.choice(clouds)
        row["Env"] = random.choice(envs)
        # Random cost in some range - adjust as you please
        row["Cost"] = round(random.uniform(50, 10000), 4)

        data_rows.append(row)

    return data_rows

def write_csv(filename="finops_data.csv", num_rows=10000):
    """
    Generate the data and write out to a CSV.
    """
    fieldnames = [
        "DATE", "WM_WEEK", "QTR", "Month", "FY", "TR_PRODUCT",
        "ORG", "Org_AD", "VP", "PILLAR", "Application_Name",
        "Cloud", "Env", "Cost"
    ]
    
    data = generate_finops_data(num_rows)

    with open(filename, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in data:
            writer.writerow(row)

if __name__ == "__main__":
    write_csv("finops_data.csv", 100000)
    print("CSV file 'finops_data.csv' with 10,000 rows has been generated!")
