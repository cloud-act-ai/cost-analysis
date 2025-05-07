#!/usr/bin/env python3
"""
Mock FinOps Dashboard for local development.
Uses sample data instead of BigQuery for testing.
"""
import os
import argparse
import pandas as pd
from datetime import datetime, timedelta
import matplotlib.pyplot as plt

def load_data(data_path="finops_data.csv"):
    """Load CSV data."""
    try:
        df = pd.read_csv(data_path)
        print(f"Loaded {len(df)} rows from {data_path}")
        return df
    except Exception as e:
        print(f"Error loading data: {e}")
        return None

def generate_comparison_report(df, comparison_type="month"):
    """Generate a simple comparison report."""
    print(f"Generating {comparison_type} comparison report...")
    
    today = datetime.now()
    
    if comparison_type == "month":
        # Current month
        current_month = today.month
        current_year = today.year
        
        # Previous month
        if current_month > 1:
            prev_month = current_month - 1
            prev_year = current_year
        else:
            prev_month = 12
            prev_year = current_year - 1
            
        # Filter data
        current_data = df[(df['year'] == current_year) & (df['month'] == current_month)]
        prev_data = df[(df['year'] == prev_year) & (df['month'] == prev_month)]
        
        # Month names
        month_names = ["January", "February", "March", "April", "May", "June", 
                      "July", "August", "September", "October", "November", "December"]
        current_month_name = month_names[current_month-1]
        prev_month_name = month_names[prev_month-1]
        
        # Print summary
        print("\n====================================")
        print(f"Comparison: {prev_month_name} {prev_year} vs {current_month_name} {current_year}")
        print("====================================")
        
    elif comparison_type == "day":
        # Use the last two days in the dataset for day comparison
        max_date = df['date'].max() if 'date' in df.columns else None
        if max_date:
            current_date = pd.to_datetime(max_date)
            prev_date = current_date - timedelta(days=1)
            
            # Filter data
            current_data = df[df['date'] == current_date]
            prev_data = df[df['date'] == prev_date]
            
            # Print summary
            print("\n====================================")
            print(f"Comparison: {prev_date.strftime('%Y-%m-%d')} vs {current_date.strftime('%Y-%m-%d')}")
            print("====================================")
        else:
            # Create date column from components if missing
            if 'day_of_month' not in df.columns:
                df['day_of_month'] = 1
                
            df['date'] = pd.to_datetime(
                df['year'].astype(str) + '-' + 
                df['month'].astype(str) + '-' + 
                df['day_of_month'].astype(str)
            )
            
            # Try again with the date column
            max_date = df['date'].max()
            current_date = pd.to_datetime(max_date)
            prev_date = current_date - timedelta(days=1)
            
            # Filter data
            current_data = df[df['date'] == current_date]
            prev_data = df[df['date'] == prev_date]
            
            # Print summary
            print("\n====================================")
            print(f"Comparison: {prev_date.strftime('%Y-%m-%d')} vs {current_date.strftime('%Y-%m-%d')}")
            print("====================================")
    else:
        print(f"Comparison type '{comparison_type}' not implemented in this mock version.")
        return
    
    # Calculate totals
    current_total = current_data['cost'].sum()
    prev_total = prev_data['cost'].sum()
    
    # Calculate environment totals
    current_prod = current_data[current_data['environment'] == 'p']['cost'].sum()
    prev_prod = prev_data[prev_data['environment'] == 'p']['cost'].sum()
    
    current_nonprod = current_data[current_data['environment'] == 'np']['cost'].sum()
    prev_nonprod = prev_data[prev_data['environment'] == 'np']['cost'].sum()
    
    # Calculate percent changes
    total_change = ((current_total - prev_total) / prev_total * 100) if prev_total > 0 else 0
    prod_change = ((current_prod - prev_prod) / prev_prod * 100) if prev_prod > 0 else 0
    nonprod_change = ((current_nonprod - prev_nonprod) / prev_nonprod * 100) if prev_nonprod > 0 else 0
    
    # Print report
    print(f"\nTotal Cost:")
    print(f"  Previous: ${prev_total:,.2f}")
    print(f"  Current:  ${current_total:,.2f}")
    print(f"  Change:   {total_change:+.2f}%")
    
    print(f"\nProduction Cost:")
    print(f"  Previous: ${prev_prod:,.2f}")
    print(f"  Current:  ${current_prod:,.2f}")
    print(f"  Change:   {prod_change:+.2f}%")
    
    print(f"\nNon-Production Cost:")
    print(f"  Previous: ${prev_nonprod:,.2f}")
    print(f"  Current:  ${current_nonprod:,.2f}")
    print(f"  Change:   {nonprod_change:+.2f}%")
    
    # Simple visualization
    plt.figure(figsize=(10, 6))
    
    # Plot bar chart
    x = ['Total', 'Production', 'Non-Production']
    prev_values = [prev_total, prev_prod, prev_nonprod]
    current_values = [current_total, current_prod, current_nonprod]
    
    x_pos = range(len(x))
    width = 0.35
    
    plt.bar([p - width/2 for p in x_pos], prev_values, width, label='Previous Period')
    plt.bar([p + width/2 for p in x_pos], current_values, width, label='Current Period')
    
    # Add labels and title
    plt.xlabel('Category')
    plt.ylabel('Cost ($)')
    plt.title(f'Cost Comparison: Previous vs Current {comparison_type.capitalize()}')
    plt.xticks(x_pos, x)
    plt.legend()
    
    # Add value labels
    for i, v in enumerate(prev_values):
        plt.text(i - width/2, v + 100, f'${v:,.0f}', ha='center')
    
    for i, v in enumerate(current_values):
        plt.text(i + width/2, v + 100, f'${v:,.0f}', ha='center')
    
    # Add percent change
    changes = [total_change, prod_change, nonprod_change]
    for i, change in enumerate(changes):
        color = 'red' if change > 0 else 'green'
        plt.text(i, max(prev_values[i], current_values[i]) + 500, 
                f'{change:+.1f}%', ha='center', color=color, fontweight='bold')
    
    # Save the figure
    os.makedirs('output', exist_ok=True)
    plot_file = f'output/comparison_{comparison_type}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png'
    plt.savefig(plot_file)
    plt.close()
    
    print(f"\nComparison chart saved to {plot_file}")
    
    # Try to open the image
    try:
        os.system(f"open {plot_file}")
    except:
        print("Could not automatically open the image. Please open it manually.")

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Mock FinOps Dashboard")
    
    parser.add_argument('--data', type=str, default="finops_data.csv",
                       help="Path to CSV data file (default: finops_data.csv)")
    parser.add_argument('--comparison', type=str, choices=['day', 'week', 'month', 'year'], 
                       default='month', help="Comparison type (default: month)")
    
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_args()
    
    # Load data
    df = load_data(args.data)
    
    if df is not None:
        # Generate report
        generate_comparison_report(df, args.comparison)