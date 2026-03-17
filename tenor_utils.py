"""
Tenor Normalization Utility
Converts tenors to standard format: 12M → 1Y, 24M → 2Y, etc.
"""

def normalize_tenor(tenor):
    """
    Normalize tenor to standard format
    - 12M → 1Y
    - 24M → 2Y
    - 36M → 3Y
    - etc.
    
    Args:
        tenor: String like "12M", "1Y", "24M", etc.
    
    Returns:
        Normalized tenor string
    """
    tenor = str(tenor).strip().upper()
    
    # If it's already in years, return as-is
    if tenor.endswith('Y'):
        return tenor
    
    # If it's in months, check if it can be converted to years
    if tenor.endswith('M'):
        try:
            months = int(tenor.replace('M', ''))
            
            # Convert to years if it's a multiple of 12
            if months >= 12 and months % 12 == 0:
                years = months // 12
                return f"{years}Y"
            
            # Otherwise return as-is
            return tenor
        except ValueError:
            return tenor
    
    # If it's in weeks, return as-is
    if tenor.endswith('W'):
        return tenor
    
    # Unknown format, return as-is
    return tenor


def tenor_to_months(tenor):
    """
    Convert tenor to months for sorting/filtering
    
    Args:
        tenor: String like "6M", "1Y", "2W"
    
    Returns:
        Number of months (float)
    """
    tenor = str(tenor).strip().upper()
    
    if tenor.endswith('W'):
        weeks = float(tenor.replace('W', ''))
        return weeks / 4.33  # Approximate weeks to months
    
    elif tenor.endswith('M'):
        return float(tenor.replace('M', ''))
    
    elif tenor.endswith('Y'):
        years = float(tenor.replace('Y', ''))
        return years * 12
    
    else:
        # Try to extract number and assume years
        import re
        match = re.search(r'\d+', tenor)
        if match:
            return float(match.group()) * 12
        return 0


def filter_tenors_by_range(tenors, min_years=None, max_years=None):
    """
    Filter tenors by year range
    
    Args:
        tenors: List of tenor strings
        min_years: Minimum years (inclusive), None for no minimum
        max_years: Maximum years (exclusive), None for no maximum
    
    Returns:
        Filtered list of tenors
    """
    filtered = []
    
    for tenor in tenors:
        months = tenor_to_months(tenor)
        years = months / 12
        
        # Check minimum
        if min_years is not None and years < min_years:
            continue
        
        # Check maximum
        if max_years is not None and years >= max_years:
            continue
        
        filtered.append(tenor)
    
    return filtered


# Test the functions
if __name__ == "__main__":
    test_tenors = ['6M', '9M', '12M', '18M', '24M', '1Y', '2Y', '36M', '3Y', '5Y']
    
    print("Tenor Normalization Tests:")
    print("="*50)
    for tenor in test_tenors:
        normalized = normalize_tenor(tenor)
        months = tenor_to_months(tenor)
        print(f"{tenor:6} → {normalized:6} ({months:5.1f} months)")
    
    print("\nRange Filter Tests:")
    print("="*50)
    
    # 0-2Y range
    short_term = filter_tenors_by_range(test_tenors, min_years=0, max_years=2)
    print(f"0-2Y: {', '.join(short_term)}")
    
    # 2Y+ range
    long_term = filter_tenors_by_range(test_tenors, min_years=2, max_years=None)
    print(f"2Y+:  {', '.join(long_term)}")
