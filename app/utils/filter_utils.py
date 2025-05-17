"""
Utilities for handling search filters in the FinOps360 dashboard.
"""
import logging
from typing import Dict, Any, List, Optional, Tuple

from app.utils.config_loader import load_config

logger = logging.getLogger(__name__)

def format_sql_filters(
    cto: Optional[str] = None, 
    pillar: Optional[str] = None, 
    product: Optional[str] = None,
    include_where: bool = False
) -> Dict[str, str]:
    """
    Format SQL filter conditions safely, escaping single quotes to prevent SQL injection.
    
    Args:
        cto: CTO organization filter value
        pillar: Pillar team filter value
        product: Product ID filter value
        include_where: Whether to include WHERE keyword instead of AND for first condition
        
    Returns:
        Dictionary with filter conditions ready for SQL substitution
    """
    # Helper to escape single quotes in SQL strings
    def escape_sql_string(s: str) -> str:
        if s is None:
            return ""
        return s.replace("'", "''")
    
    # Start with empty filters
    filters = {
        'cto_filter': "",
        'pillar_filter': "",
        'product_filter': ""
    }
    
    # Track if we've added any filters
    has_filters = False
    
    # Add CTO filter if provided
    if cto:
        safe_cto = escape_sql_string(cto)
        prefix = "WHERE" if include_where and not has_filters else "AND"
        filters['cto_filter'] = f"{prefix} cto = '{safe_cto}'"
        has_filters = True
    
    # Add Pillar filter if provided  
    if pillar:
        safe_pillar = escape_sql_string(pillar)
        prefix = "WHERE" if include_where and not has_filters else "AND"
        filters['pillar_filter'] = f"{prefix} tr_product_pillar_team = '{safe_pillar}'"
        has_filters = True
    
    # Add Product filter if provided
    if product:
        safe_product = escape_sql_string(product)
        prefix = "WHERE" if include_where and not has_filters else "AND"
        filters['product_filter'] = f"{prefix} tr_product_id = '{safe_product}'"
        has_filters = True
    
    return filters

def get_filter_values(filters: Dict[str, Any]) -> Tuple[Optional[str], Optional[str], Optional[str], bool]:
    """
    Extract filter values from request parameters.
    
    Args:
        filters: Dictionary with filter parameters
        
    Returns:
        Tuple of (cto, pillar, product, show_sql)
    """
    # Get filter values with empty string fallback
    selected_cto = filters.get('cto', '')
    selected_pillar = filters.get('pillar', '')
    selected_product = filters.get('product', '')
    show_sql = filters.get('show_sql', False)
    
    # Convert empty strings to None for consistency
    selected_cto = selected_cto if selected_cto else None
    selected_pillar = selected_pillar if selected_pillar else None
    selected_product = selected_product if selected_product else None
    
    # Log active filters
    if selected_cto or selected_pillar or selected_product:
        logger.info(f"Active filters: CTO='{selected_cto}', Pillar='{selected_pillar}', Product='{selected_product}'")
    
    return selected_cto, selected_pillar, selected_product, show_sql

def get_filter_defaults_from_config() -> Dict[str, Any]:
    """
    Get default filter values from configuration.
    
    Returns:
        Dictionary with default filter values
    """
    try:
        config = load_config("config.yaml")
        filter_config = config.get('filters', {})
        
        return {
            'default_cto': filter_config.get('default_cto', None),
            'default_pillar': filter_config.get('default_pillar', None),
            'default_product': filter_config.get('default_product', None)
        }
    except Exception as e:
        logger.error(f"Error loading filter defaults from config: {e}")
        return {
            'default_cto': None,
            'default_pillar': None, 
            'default_product': None
        }

def validate_filters(cto: Optional[str], pillar: Optional[str], product: Optional[str]) -> bool:
    """
    Validate that the filter combinations make sense.
    For example, ensure a selected product belongs to the selected pillar.
    
    This can be expanded with actual validation logic in the future.
    
    Args:
        cto: Selected CTO organization
        pillar: Selected pillar team
        product: Selected product ID
        
    Returns:
        True if filters are valid, False otherwise
    """
    # Simple validation for now - could be expanded in the future
    # with actual data validation
    return True