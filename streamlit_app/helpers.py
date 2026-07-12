"""Helper functions for formatting and utilities."""
import datetime
from typing import Union

def format_currency(value: Union[int, float]) -> str:
    """Format value in lakhs or crores."""
    if value >= 100:
        return f"₹{value / 100:.2f} Cr"
    return f"₹{value:.2f} L"

def format_percentage(value: Union[int, float]) -> str:
    """Format value as percentage."""
    return f"{value:.2f}%"

def get_current_date_str() -> str:
    """Get current date as string."""
    return datetime.date.today().strftime("%Y-%m-%d")

def clean_html(html_str: str) -> str:
    """Strip whitespace from each line in HTML string."""
    if not html_str:
        return ""
    return "\n".join([line.strip() for line in html_str.split("\n")])
