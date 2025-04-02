import yaml
import os
from dataclasses import dataclass
from datetime import datetime


@dataclass
class FinOpsConfig:
    """Configuration settings for FinOps analysis."""
    file_path: str
    output_dir: str
    month: str
    year: str
    parent_grouping: str
    parent_grouping_value: str
    child_grouping: str
    top_n: int
    include_applications: bool
    generate_html: bool
    export_csv: bool
    page_title: str
    company_name: str
    logo_path: str


def load_config(config_path="config.yaml"):
    """Load configuration from YAML file."""
    with open(config_path, 'r') as f:
        config_data = yaml.safe_load(f)
    
    return FinOpsConfig(
        file_path=config_data['data']['file_path'],
        output_dir=config_data['data']['output_dir'],
        month=config_data['analysis']['month'],
        year=config_data['analysis']['year'],
        parent_grouping=config_data['analysis']['parent_grouping'],
        parent_grouping_value=config_data['analysis']['parent_grouping_value'],
        child_grouping=config_data['analysis']['child_grouping'],
        top_n=config_data['analysis']['top_n'],
        include_applications=config_data['analysis']['include_applications'],
        generate_html=config_data['report']['generate_html'],
        export_csv=config_data['report']['export_csv'],
        page_title=config_data['report']['page_title'],
        company_name=config_data['report']['company_name'],
        logo_path=config_data['report']['logo_path']
    )


def get_output_filename(config, extension="html"):
    """Generate output filename with timestamp."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{config.output_dir}/finops_report_{config.month}_{config.year}_{timestamp}.{extension}"