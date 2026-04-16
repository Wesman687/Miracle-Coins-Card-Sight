"""
Auto SKU Generation Utility for Miracle Coins
Generates SKUs based on coin properties like year, denomination, mint mark, grade, etc.
"""

import re
from typing import Optional
from decimal import Decimal

def generate_sku(
    title: str,
    year: Optional[int] = None,
    denomination: Optional[str] = None,
    mint_mark: Optional[str] = None,
    grade: Optional[str] = None,
    category_name: Optional[str] = None
) -> str:
    """
    Generate an auto SKU based on coin properties
    
    Format: [CATEGORY]-[YEAR]-[DENOMINATION]-[MINT]-[GRADE]-[SEQUENCE]
    Example: ASE-2023-1OZ-NM-MS70-001
    
    Args:
        title: Coin title
        year: Year of the coin
        denomination: Denomination (e.g., "1 oz", "1 dollar")
        mint_mark: Mint mark (e.g., "S", "CC", "No Mark")
        grade: Grade (e.g., "MS70", "AU58")
        category_name: Category name for prefix
    
    Returns:
        Generated SKU string
    """
    
    # Determine category prefix
    category_prefix = _get_category_prefix(category_name, title)
    
    # Format year
    year_str = str(year) if year else "0000"
    
    # Format denomination
    denomination_str = _format_denomination(denomination, title)
    
    # Format mint mark
    mint_str = _format_mint_mark(mint_mark)
    
    # Format grade
    grade_str = _format_grade(grade)
    
    # Generate sequence number (this would be determined by existing SKUs)
    sequence = "001"  # This should be calculated based on existing SKUs
    
    # Build SKU parts
    sku_parts = [category_prefix, year_str, denomination_str, mint_str, grade_str, sequence]
    
    # Filter out empty parts
    sku_parts = [part for part in sku_parts if part]
    
    # Join with hyphens
    sku = "-".join(sku_parts)
    
    # Ensure SKU is not too long (max 50 characters)
    if len(sku) > 50:
        sku = sku[:50]
    
    return sku

def _get_category_prefix(category_name: Optional[str], title: str) -> str:
    """Get category prefix for SKU"""
    if category_name:
        # Use category name to determine prefix
        category_lower = category_name.lower()
        if "silver eagle" in category_lower:
            return "ASE"
        elif "morgan" in category_lower:
            return "MOR"
        elif "peace" in category_lower:
            return "PEA"
        elif "kennedy" in category_lower:
            return "KEN"
        elif "walking liberty" in category_lower:
            return "WAL"
        elif "mercury" in category_lower:
            return "MER"
        elif "roosevelt" in category_lower:
            return "ROO"
        elif "washington" in category_lower:
            return "WAS"
        elif "standing liberty" in category_lower:
            return "STA"
        elif "barber" in category_lower:
            return "BAR"
        elif "liberty head" in category_lower:
            return "LIB"
        elif "buffalo" in category_lower:
            return "BUF"
        elif "indian head" in category_lower:
            return "IND"
        elif "gold" in category_lower:
            return "GLD"
        else:
            # Use first 3 letters of category
            return category_name[:3].upper()
    
    # Fall back to title analysis
    title_lower = title.lower()
    if "silver eagle" in title_lower:
        return "ASE"
    elif "morgan" in title_lower:
        return "MOR"
    elif "peace" in title_lower:
        return "PEA"
    elif "kennedy" in title_lower:
        return "KEN"
    elif "walking liberty" in title_lower:
        return "WAL"
    elif "mercury" in title_lower:
        return "MER"
    elif "roosevelt" in title_lower:
        return "ROO"
    elif "washington" in title_lower:
        return "WAS"
    elif "standing liberty" in title_lower:
        return "STA"
    elif "barber" in title_lower:
        return "BAR"
    elif "liberty head" in title_lower:
        return "LIB"
    elif "buffalo" in title_lower:
        return "BUF"
    elif "indian head" in title_lower:
        return "IND"
    elif "gold" in title_lower:
        return "GLD"
    else:
        # Use first 3 letters of title
        return title[:3].upper()

def _format_denomination(denomination: Optional[str], title: str) -> str:
    """Format denomination for SKU"""
    if not denomination:
        # Try to extract from title
        denomination = _extract_denomination_from_title(title)
    
    if not denomination:
        return "1OZ"  # Default
    
    denomination_lower = denomination.lower()
    
    # Standardize common denominations
    if "dollar" in denomination_lower or "$1" in denomination_lower:
        return "1DOL"
    elif "half dollar" in denomination_lower or "50" in denomination_lower:
        return "50C"
    elif "quarter" in denomination_lower or "25" in denomination_lower:
        return "25C"
    elif "dime" in denomination_lower or "10" in denomination_lower:
        return "10C"
    elif "nickel" in denomination_lower or "5" in denomination_lower:
        return "5C"
    elif "penny" in denomination_lower or "cent" in denomination_lower or "1" in denomination_lower:
        return "1C"
    elif "ounce" in denomination_lower or "oz" in denomination_lower:
        return "1OZ"
    elif "gram" in denomination_lower or "g" in denomination_lower:
        # Extract number of grams
        grams_match = re.search(r'(\d+(?:\.\d+)?)\s*g', denomination_lower)
        if grams_match:
            grams = grams_match.group(1)
            return f"{grams}G"
        return "1G"
    else:
        # Use first 3 characters, cleaned up
        cleaned = re.sub(r'[^a-zA-Z0-9]', '', denomination)[:3].upper()
        return cleaned or "1OZ"

def _extract_denomination_from_title(title: str) -> Optional[str]:
    """Extract denomination from title"""
    title_lower = title.lower()
    
    # Look for common patterns
    if "silver eagle" in title_lower:
        return "1 oz"
    elif "morgan dollar" in title_lower:
        return "1 dollar"
    elif "peace dollar" in title_lower:
        return "1 dollar"
    elif "kennedy half" in title_lower:
        return "half dollar"
    elif "walking liberty half" in title_lower:
        return "half dollar"
    elif "mercury dime" in title_lower:
        return "dime"
    elif "roosevelt dime" in title_lower:
        return "dime"
    elif "washington quarter" in title_lower:
        return "quarter"
    elif "standing liberty quarter" in title_lower:
        return "quarter"
    
    return None

def _format_mint_mark(mint_mark: Optional[str]) -> str:
    """Format mint mark for SKU"""
    if not mint_mark:
        return "NM"  # No Mark
    
    mint_mark_upper = mint_mark.upper()
    
    # Standardize mint marks
    mint_map = {
        "NO MARK": "NM",
        "NONE": "NM",
        "PHILADELPHIA": "NM",  # Philadelphia has no mark
        "P": "NM",
        "DENVER": "D",
        "D": "D",
        "SAN FRANCISCO": "S",
        "S": "S",
        "CARSON CITY": "CC",
        "CC": "CC",
        "NEW ORLEANS": "O",
        "O": "O",
        "WEST POINT": "W",
        "W": "W",
    }
    
    return mint_map.get(mint_mark_upper, mint_mark_upper[:2])

def _format_grade(grade: Optional[str]) -> str:
    """Format grade for SKU"""
    if not grade:
        return "UNG"  # Ungraded
    
    grade_upper = grade.upper()
    
    # Remove common prefixes/suffixes and standardize
    grade_clean = re.sub(r'^(PCGS|NGC|ANACS|ICG)\s*', '', grade_upper)
    grade_clean = re.sub(r'\s*(PCGS|NGC|ANACS|ICG)$', '', grade_clean)
    
    # Standardize common grades
    grade_map = {
        "MS70": "MS70",
        "MS69": "MS69",
        "MS68": "MS68",
        "MS67": "MS67",
        "MS66": "MS66",
        "MS65": "MS65",
        "MS64": "MS64",
        "MS63": "MS63",
        "MS62": "MS62",
        "MS61": "MS61",
        "MS60": "MS60",
        "AU58": "AU58",
        "AU55": "AU55",
        "AU53": "AU53",
        "AU50": "AU50",
        "XF45": "XF45",
        "XF40": "XF40",
        "VF35": "VF35",
        "VF30": "VF30",
        "VF25": "VF25",
        "VF20": "VF20",
        "F15": "F15",
        "F12": "F12",
        "VG10": "VG10",
        "VG8": "VG8",
        "G6": "G6",
        "G4": "G4",
        "AG3": "AG3",
        "FA2": "FA2",
        "PO1": "PO1",
        "UNCIRCULATED": "UNC",
        "UNC": "UNC",
        "BRILLIANT UNCIRCULATED": "BU",
        "BU": "BU",
        "PROOF": "PRF",
        "PRF": "PRF",
        "CIRCULATED": "CIR",
        "CIR": "CIR",
    }
    
    return grade_map.get(grade_clean, grade_clean[:4])

def generate_next_sequence_number(db_session, base_sku: str) -> str:
    """
    Generate the next sequence number for a base SKU
    
    Args:
        db_session: Database session
        base_sku: Base SKU without sequence number
    
    Returns:
        Next sequence number (e.g., "001", "002", etc.)
    """
    # Import here to avoid circular imports
    from app.models import Coin
    
    # Find existing SKUs that start with the base SKU
    existing_skus = db_session.query(Coin.sku).filter(
        Coin.sku.like(f"{base_sku}-%")
    ).all()
    
    if not existing_skus:
        return "001"
    
    # Extract sequence numbers
    sequence_numbers = []
    for (sku,) in existing_skus:
        if sku and sku.count('-') >= 5:  # Ensure it has sequence number
            parts = sku.split('-')
            if len(parts) >= 6:
                try:
                    seq_num = int(parts[-1])
                    sequence_numbers.append(seq_num)
                except ValueError:
                    continue
    
    if not sequence_numbers:
        return "001"
    
    # Get the next sequence number
    next_sequence = max(sequence_numbers) + 1
    
    # Format with leading zeros
    return f"{next_sequence:03d}"

def generate_complete_sku(
    db_session,
    title: str,
    year: Optional[int] = None,
    denomination: Optional[str] = None,
    mint_mark: Optional[str] = None,
    grade: Optional[str] = None,
    category_name: Optional[str] = None
) -> str:
    """
    Generate a complete unique SKU with sequence number
    
    Args:
        db_session: Database session
        title: Coin title
        year: Year of the coin
        denomination: Denomination
        mint_mark: Mint mark
        grade: Grade
        category_name: Category name
    
    Returns:
        Complete unique SKU
    """
    # Generate base SKU without sequence
    base_sku = generate_sku(
        title=title,
        year=year,
        denomination=denomination,
        mint_mark=mint_mark,
        grade=grade,
        category_name=category_name
    )
    
    # Remove the default sequence number
    if base_sku.endswith("-001"):
        base_sku = base_sku[:-4]
    
    # Generate next sequence number
    sequence = generate_next_sequence_number(db_session, base_sku)
    
    # Combine base SKU with sequence
    return f"{base_sku}-{sequence}"

# Example usage:
# sku = generate_complete_sku(
#     db_session=db,
#     title="2023 Silver Eagle",
#     year=2023,
#     denomination="1 oz",
#     mint_mark="No Mark",
#     grade="MS70",
#     category_name="Silver Eagles"
# )
# Result: "ASE-2023-1OZ-NM-MS70-001"
