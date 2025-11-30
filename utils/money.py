# Utilities for money-related constants and helpers
import locale

# Common Vietnamese currency denominations used in counting dialogs
MENH_GIA = [500000, 200000, 100000, 50000, 20000, 10000, 5000, 2000, 1000]


def format_price(value):
    """
    Format number as currency with thousand separators
    
    Args:
        value: Number to format
        
    Returns:
        Formatted string with 2 decimal places and thousand separators
    """
    try:
        return locale.format_string("%.2f", value, grouping=True)
    except Exception as e:
        print(f"Warning: Error formatting price {value}: {e}")
        return str(value)


def tinh_tong_tu_to_tien(spins_with_menhgia):
    """
    Calculate total amount from a list of (spin, menh_gia) pairs.
    spin must provide .value() returning int; menh_gia is the denomination.
    """
    try:
        return sum(spin.value() * mg for spin, mg in spins_with_menhgia)
    except Exception:
        # Fallback if any spin missing
        total = 0
        for pair in spins_with_menhgia:
            try:
                spin, mg = pair
                total += spin.value() * mg
            except Exception:
                continue
        return total
