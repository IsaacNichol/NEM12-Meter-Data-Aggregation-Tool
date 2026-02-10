"""Utility functions for NEM12 meter data processing."""

import os
import re
from datetime import datetime, time
from typing import List, Optional
import pytz


def parse_time_string(time_str: str) -> time:
    """
    Parse various time formats to datetime.time object.

    Supports:
    - HH:MM (24-hour)
    - HH:MM:SS (24-hour)
    - HH:MM AM/PM (12-hour)
    - HH:MM:SS AM/PM (12-hour)

    Args:
        time_str: Time string to parse

    Returns:
        datetime.time object

    Raises:
        ValueError: If time format is invalid
    """
    time_str = time_str.strip()

    # Try 24-hour formats first
    for fmt in ['%H:%M:%S', '%H:%M']:
        try:
            dt = datetime.strptime(time_str, fmt)
            return dt.time()
        except ValueError:
            continue

    # Try 12-hour formats
    for fmt in ['%I:%M:%S %p', '%I:%M %p']:
        try:
            dt = datetime.strptime(time_str.upper(), fmt)
            return dt.time()
        except ValueError:
            continue

    raise ValueError(f"Invalid time format: '{time_str}'. Use HH:MM (24-hour) or HH:MM AM/PM (12-hour)")


def validate_time_format(time_str: str) -> bool:
    """
    Validate if a string is a valid time format.

    Args:
        time_str: Time string to validate

    Returns:
        True if valid, False otherwise
    """
    try:
        parse_time_string(time_str)
        return True
    except ValueError:
        return False


def find_nem12_files(directory: str = '.') -> List[str]:
    """
    Find all CSV files in a directory that might be NEM12 files.

    Args:
        directory: Directory to search (default: current directory)

    Returns:
        List of CSV file paths
    """
    csv_files = []
    for file in os.listdir(directory):
        if file.endswith('.csv') or file.endswith('.CSV'):
            csv_files.append(os.path.join(directory, file))
    return sorted(csv_files)


def validate_nem12_structure(filepath: str) -> tuple[bool, str]:
    """
    Quick validation of NEM12 file structure.

    Checks for:
    - 100 header record
    - 900 footer record
    - At least one 200/300 record pair

    Args:
        filepath: Path to NEM12 file

    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        with open(filepath, 'r', encoding='utf-8-sig') as f:
            lines = f.readlines()

        if not lines:
            return False, "File is empty"

        # Check for 100 header
        if not lines[0].strip().startswith('100'):
            return False, "Missing 100 header record"

        # Check for 900 footer
        if not lines[-1].strip().startswith('900'):
            return False, "Missing 900 footer record"

        # Check for at least one 200 and 300 record
        has_200 = any(line.strip().startswith('200') for line in lines)
        has_300 = any(line.strip().startswith('300') for line in lines)

        if not has_200:
            return False, "No 200 (meter header) records found"
        if not has_300:
            return False, "No 300 (interval data) records found"

        return True, ""

    except Exception as e:
        return False, f"Error reading file: {str(e)}"


def get_australian_timezone(state: str) -> pytz.timezone:
    """
    Get the timezone for an Australian state.

    Args:
        state: Australian state code (NSW, VIC, QLD, SA, WA, TAS, NT, ACT)

    Returns:
        pytz timezone object
    """
    state = state.upper()

    # Timezone mapping
    timezone_map = {
        'NSW': 'Australia/Sydney',
        'VIC': 'Australia/Melbourne',
        'QLD': 'Australia/Brisbane',
        'SA': 'Australia/Adelaide',
        'WA': 'Australia/Perth',
        'TAS': 'Australia/Hobart',
        'NT': 'Australia/Darwin',
        'ACT': 'Australia/Sydney',
    }

    tz_name = timezone_map.get(state, 'Australia/Sydney')
    return pytz.timezone(tz_name)


def format_currency(amount: float) -> str:
    """
    Format a number as Australian currency.

    Args:
        amount: Dollar amount

    Returns:
        Formatted string (e.g., "$1,234.56")
    """
    return f"${amount:,.2f}"


def format_number(number: float, decimals: int = 2) -> str:
    """
    Format a number with thousands separators.

    Args:
        number: Number to format
        decimals: Number of decimal places

    Returns:
        Formatted string (e.g., "1,234.56")
    """
    return f"{number:,.{decimals}f}"
