import yaml
import os
import pandas as pd
from dataclasses import dataclass
from datetime import datetime


@dataclass
class FinOpsConfig:
    """Configuration settings for FinOps analysis."""
    file_path: str
    output_dir: str
    period_type: str
    period_value: str
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
    display_columns: list = None  # New field for configurable columns
    
    def validate(self, df=None):
        """Validate configuration settings."""
        # Validate period type
        valid_period_types = ['month', 'quarter', 'week', 'year']
        if self.period_type not in valid_period_types:
            raise ValueError(f"Invalid period_type: {self.period_type}. Must be one of {valid_period_types}")
        
        # Validate period value based on type
        if self.period_type == 'month':
            valid_months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
            if self.period_value not in valid_months:
                raise ValueError(f"Invalid month: {self.period_value}. Must be one of {valid_months}")
        
        elif self.period_type == 'quarter':
            valid_quarters = ['Q1', 'Q2', 'Q3', 'Q4']
            if self.period_value not in valid_quarters:
                raise ValueError(f"Invalid quarter: {self.period_value}. Must be one of {valid_quarters}")
        
        elif self.period_type == 'week':
            try:
                week_num = int(self.period_value)
                if week_num < 1 or week_num > 53:
                    raise ValueError(f"Invalid week number: {self.period_value}. Must be between 1 and 53")
            except ValueError:
                raise ValueError(f"Invalid week number: {self.period_value}. Must be an integer between 1 and 53")
        
        elif self.period_type == 'year':
            try:
                year = int(self.period_value)
                if year < 2000 or year > 2100:
                    raise ValueError(f"Invalid year: {self.period_value}. Must be between 2000 and 2100")
            except ValueError:
                raise ValueError(f"Invalid year: {self.period_value}. Must be a valid year (e.g., 2023)")
        
        # Validate grouping columns if dataframe is provided
        if df is not None:
            # Check parent grouping
            if self.parent_grouping not in df.columns:
                raise ValueError(f"Invalid parent_grouping: '{self.parent_grouping}'. Must be a column in the dataset. Available columns: {list(df.columns)}")
            
            # Check child grouping
            if self.child_grouping not in df.columns:
                raise ValueError(f"Invalid child_grouping: '{self.child_grouping}'. Must be a column in the dataset. Available columns: {list(df.columns)}")
            
            # Check if parent_grouping_value exists in the dataset
            if self.parent_grouping_value and self.parent_grouping_value not in df[self.parent_grouping].unique():
                raise ValueError(f"Invalid parent_grouping_value: '{self.parent_grouping_value}'. Must be a value in the {self.parent_grouping} column. Available values: {list(df[self.parent_grouping].unique())}")
            
            # Check display columns
            if self.display_columns:
                for col in self.display_columns:
                    if col not in df.columns:
                        raise ValueError(f"Invalid column '{col}' in display_columns. Must be a column in the dataset. Available columns: {list(df.columns)}")


def load_config(config_path="config.yaml"):
    """Load configuration from YAML file."""
    with open(config_path, 'r') as f:
        config_data = yaml.safe_load(f)
    
    # Get display columns if specified
    display_columns = None
    if 'display_columns' in config_data.get('analysis', {}):
        display_columns = config_data['analysis']['display_columns']
    
    config = FinOpsConfig(
        file_path=config_data['data']['file_path'],
        output_dir=config_data['data']['output_dir'],
        period_type=config_data['analysis']['period_type'],
        period_value=str(config_data['analysis']['period_value']),
        year=str(config_data['analysis']['year']),
        parent_grouping=config_data['analysis']['parent_grouping'],
        parent_grouping_value=config_data['analysis']['parent_grouping_value'],
        child_grouping=config_data['analysis']['child_grouping'],
        top_n=config_data['analysis']['top_n'],
        include_applications=config_data['analysis']['include_applications'],
        generate_html=config_data['report']['generate_html'],
        export_csv=config_data['report']['export_csv'],
        page_title=config_data['report']['page_title'],
        company_name=config_data['report']['company_name'],
        logo_path=config_data['report']['logo_path'],
        display_columns=display_columns
    )
    
    # Validate configuration
    config.validate()
    
    return config


def validate_config_with_data(config, df):
    """Validate configuration with actual data."""
    config.validate(df)
    

def get_output_filename(config, report_type, current_period_display=None, extension="html"):
    """Generate output filename with descriptive naming."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Format the parent grouping in a readable way
    parent_info = f"{config.parent_grouping}_{config.parent_grouping_value}".replace(" ", "_")
    
    # Create a clean period info string if provided
    period_info = ""
    if current_period_display:
        period_info = f"{config.period_type}_{current_period_display}".replace(" ", "_")
    else:
        period_info = f"{config.period_type}_{config.period_value}_{config.year}"
    
    # Generate final filename
    return f"{config.output_dir}/{report_type}_report_{parent_info}_{period_info}_{timestamp}.{extension}"
