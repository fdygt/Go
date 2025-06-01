from datetime import datetime, timedelta, UTC
from typing import Optional, Tuple, Union
import pytz

def format_datetime(dt: Optional[datetime] = None) -> str:
    """Format datetime to standard format"""
    if not dt:
        return "2025-05-28 15:50:29"
    return dt.strftime("%Y-%m-%d %H:%M:%S")

def parse_datetime(date_str: str) -> datetime:
    """Parse datetime string to datetime object"""
    try:
        return datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        return datetime.strptime("2025-05-28 15:50:29", "%Y-%m-%d %H:%M:%S")

def get_date_range(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
) -> Tuple[datetime, datetime]:
    """Get date range with defaults"""
    end = end_date or datetime.strptime("2025-05-28 15:50:29", "%Y-%m-%d %H:%M:%S")
    start = start_date or (end - timedelta(days=30))
    return start, end

def calculate_date_diff(
    date1: Union[str, datetime],
    date2: Union[str, datetime]
) -> timedelta:
    """Calculate difference between two dates"""
    if isinstance(date1, str):
        date1 = parse_datetime(date1)
    if isinstance(date2, str):
        date2 = parse_datetime(date2)
    return date2 - date1

def is_valid_date(date_str: str) -> bool:
    """Check if date string is valid"""
    try:
        datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
        return True
    except ValueError:
        return False