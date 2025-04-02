import pandas as pd
import os
from jinja2 import Template
from datetime import datetime


def format_currency(value):
    """Format numeric value as currency."""
    return f"${value:,.2f}"


def format_percent(value):
    """Format numeric value as percentage."""
    return f"{value:.2f}%"


def format_change(value):
    """Format change value with sign."""
    prefix = '+' if value > 0 else ''
    return f"{prefix}{format_currency(value)}"


def generate_html_report(config, analysis_results, current_month, previous_month, current_year, previous_year):
    """Generate HTML report from analysis results."""
    
    # Create directory if it doesn't exist
    os.makedirs(config.output_dir, exist_ok=True)
    
    # Prepare data for template
    top_investments = analysis_results['top_investments']
    top_efficiencies = analysis_results['top_efficiencies']
    
    # Format investment data for HTML table
    investments_data = []
    for _, row in top_investments.iterrows():
        investments_data.append({
            'name': row[config.child_grouping],
            'previous_cost': format_currency(row['Total_Cost_previous']),
            'current_cost': format_currency(row['Total_Cost_current']),
            'change': format_change(row['Change']),
            'percent_change': format_percent(abs(row['Percent_Change']))
        })
    
    # Format efficiency data for HTML table
    efficiencies_data = []
    for _, row in top_efficiencies.iterrows():
        efficiencies_data.append({
            'name': row[config.child_grouping],
            'previous_cost': format_currency(row['Total_Cost_previous']),
            'current_cost': format_currency(row['Total_Cost_current']),
            'change': format_change(row['Change']),
            'percent_change': format_percent(abs(row['Percent_Change']))
        })
    
    # Format summary data
    summary = {
        'previous_spend': format_currency(analysis_results['total_previous']),
        'current_spend': format_currency(analysis_results['total_current']),
        'efficiencies': format_change(analysis_results['efficiencies']),
        'investments': format_change(analysis_results['investments']),
        'net_change': format_change(analysis_results['net_change']),
        'percent_change': format_percent(analysis_results['percent_change'])
    }
    
    # Generate HTML using Jinja2 template
    html_template = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ page_title }}</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }
        header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 30px;
            border-bottom: 1px solid #ddd;
            padding-bottom: 10px;
        }
        .summary-box {
            background-color: #f5f5f5;
            border-radius: 5px;
            padding: 20px;
            margin-bottom: 30px;
        }
        .summary-title {
            font-size: 24px;
            font-weight: bold;
            margin-bottom: 15px;
        }
        .summary-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 15px;
        }
        .summary-item {
            margin-bottom: 10px;
        }
        .summary-label {
            font-weight: bold;
            display: block;
        }
        .summary-value {
            font-size: 24px;
            color: #004085;
        }
        .positive {
            color: #28a745;
        }
        .negative {
            color: #dc3545;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 30px;
        }
        th, td {
            padding: 12px 15px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }
        th {
            background-color: #f2f2f2;
            font-weight: bold;
        }
        tr:hover {
            background-color: #f5f5f5;
        }
        .section-title {
            font-size: 20px;
            font-weight: bold;
            margin: 30px 0 15px;
            border-bottom: 2px solid #004085;
            padding-bottom: 5px;
        }
        .report-subtitle {
            color: #666;
            margin-bottom: 20px;
        }
        footer {
            margin-top: 50px;
            padding-top: 20px;
            border-top: 1px solid #ddd;
            color: #666;
            font-size: 14px;
        }
    </style>
</head>
<body>
    <header>
        <h1>{{ page_title }}</h1>
        <div>
            {% if logo_path %}
            <img src="{{ logo_path }}" alt="{{ company_name }} Logo" height="50">
            {% else %}
            <h2>{{ company_name }}</h2>
            {% endif %}
        </div>
    </header>
    
    <p class="report-subtitle">
        Comparing {{ current_month }} {{ current_year }} with {{ previous_month }} {{ previous_year }} 
        for {{ parent_grouping }}: {{ parent_grouping_value }}
    </p>
    
    <div class="summary-box">
        <div class="summary-title">Summary</div>
        <div class="summary-grid">
            <div class="summary-item">
                <span class="summary-label">Previous Month Spend:</span>
                <div class="summary-value">{{ summary.previous_spend }}</div>
            </div>
            <div class="summary-item">
                <span class="summary-label">Efficiencies (Cost Reduction):</span>
                <div class="summary-value negative">{{ summary.efficiencies }}</div>
            </div>
            <div class="summary-item">
                <span class="summary-label">Investments (Cost Increase):</span>
                <div class="summary-value positive">{{ summary.investments }}</div>
            </div>
            <div class="summary-item">
                <span class="summary-label">Current Month Spend:</span>
                <div class="summary-value">{{ summary.current_spend }}</div>
            </div>
            <div class="summary-item">
                <span class="summary-label">Net Change:</span>
                <div class="summary-value {% if summary.net_change.startswith('+') %}positive{% else %}negative{% endif %}">
                    {{ summary.net_change }} ({{ summary.percent_change }})
                </div>
            </div>
        </div>
    </div>
    
    <div class="section-title">Top {{ top_n }} Investments ({{ child_grouping }})</div>
    <table>
        <thead>
            <tr>
                <th>{{ child_grouping }}</th>
                <th>Previous Cost</th>
                <th>Current Cost</th>
                <th>Change</th>
                <th>% Change</th>
            </tr>
        </thead>
        <tbody>
            {% for item in investments %}
            <tr>
                <td>{{ item.name }}</td>
                <td>{{ item.previous_cost }}</td>
                <td>{{ item.current_cost }}</td>
                <td class="positive">{{ item.change }}</td>
                <td>{{ item.percent_change }}</td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
    
    <div class="section-title">Top {{ top_n }} Efficiencies ({{ child_grouping }})</div>
    <table>
        <thead>
            <tr>
                <th>{{ child_grouping }}</th>
                <th>Previous Cost</th>
                <th>Current Cost</th>
                <th>Change</th>
                <th>% Change</th>
            </tr>
        </thead>
        <tbody>
            {% for item in efficiencies %}
            <tr>
                <td>{{ item.name }}</td>
                <td>{{ item.previous_cost }}</td>
                <td>{{ item.current_cost }}</td>
                <td class="negative">{{ item.change }}</td>
                <td>{{ item.percent_change }}</td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
    
    <footer>
        Generated on {{ timestamp }} | {{ company_name }} FinOps Report
    </footer>
</body>
</html>
    """
    
    template = Template(html_template)
    rendered_html = template.render(
        page_title=config.page_title,
        company_name=config.company_name,
        logo_path=config.logo_path,
        parent_grouping=config.parent_grouping,
        parent_grouping_value=config.parent_grouping_value,
        child_grouping=config.child_grouping,
        top_n=config.top_n,
        current_month=current_month,
        previous_month=previous_month,
        current_year=current_year,
        previous_year=previous_year,
        summary=summary,
        investments=investments_data,
        efficiencies=efficiencies_data,
        timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )
    
    # Write to file
    output_filename = os.path.join(
        config.output_dir, 
        f"finops_report_{config.month}_{config.year}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
    )
    
    with open(output_filename, 'w') as f:
        f.write(rendered_html)
    
    return output_filename