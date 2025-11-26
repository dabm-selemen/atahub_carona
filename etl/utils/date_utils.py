"""
Date Utilities

Functions for date manipulation, chunking, and range generation for ETL operations.
"""

from datetime import date, datetime, timedelta
from typing import List, Tuple
from dateutil.relativedelta import relativedelta
import structlog

logger = structlog.get_logger(__name__)


def generate_quarterly_chunks(
    start_date: date,
    end_date: date
) -> List[Tuple[date, date]]:
    """
    Generate quarterly date chunks for ETL processing

    Divides date range into 3-month chunks for manageable processing.

    Args:
        start_date: Start date
        end_date: End date

    Returns:
        List of (start, end) date tuples

    Example:
        >>> generate_quarterly_chunks(date(2023, 1, 1), date(2023, 12, 31))
        [
            (date(2023, 1, 1), date(2023, 3, 31)),
            (date(2023, 4, 1), date(2023, 6, 30)),
            (date(2023, 7, 1), date(2023, 9, 30)),
            (date(2023, 10, 1), date(2023, 12, 31))
        ]
    """
    chunks = []
    current_start = start_date

    while current_start <= end_date:
        # Calculate end of quarter (3 months)
        current_end = current_start + relativedelta(months=3) - timedelta(days=1)

        # Don't exceed final end date
        if current_end > end_date:
            current_end = end_date

        chunks.append((current_start, current_end))

        # Move to next quarter
        current_start = current_end + timedelta(days=1)

    logger.info(
        "quarterly_chunks_generated",
        start_date=str(start_date),
        end_date=str(end_date),
        num_chunks=len(chunks)
    )

    return chunks


def generate_monthly_chunks(
    start_date: date,
    end_date: date
) -> List[Tuple[date, date]]:
    """
    Generate monthly date chunks

    Args:
        start_date: Start date
        end_date: End date

    Returns:
        List of (start, end) date tuples for each month

    Example:
        >>> generate_monthly_chunks(date(2023, 1, 1), date(2023, 3, 31))
        [
            (date(2023, 1, 1), date(2023, 1, 31)),
            (date(2023, 2, 1), date(2023, 2, 28)),
            (date(2023, 3, 1), date(2023, 3, 31))
        ]
    """
    chunks = []
    current_start = start_date

    while current_start <= end_date:
        # Calculate end of month
        current_end = (current_start + relativedelta(months=1)) - timedelta(days=1)

        # Don't exceed final end date
        if current_end > end_date:
            current_end = end_date

        chunks.append((current_start, current_end))

        # Move to next month
        current_start = current_end + timedelta(days=1)

    logger.info(
        "monthly_chunks_generated",
        start_date=str(start_date),
        end_date=str(end_date),
        num_chunks=len(chunks)
    )

    return chunks


def get_incremental_date_window(
    last_sync_date: date,
    lookback_days: int = 7
) -> Tuple[date, date]:
    """
    Calculate date window for incremental updates

    Includes lookback period to capture late API updates.

    Args:
        last_sync_date: Date of last successful sync
        lookback_days: Number of days to look back (captures late updates)

    Returns:
        (window_start, window_end) tuple

    Example:
        >>> get_incremental_date_window(date(2024, 1, 15), lookback_days=7)
        (date(2024, 1, 8), date(2024, 1, 26))  # Assuming today is 2024-01-26
    """
    window_start = last_sync_date - timedelta(days=lookback_days)
    window_end = date.today()

    logger.info(
        "incremental_window_calculated",
        last_sync_date=str(last_sync_date),
        lookback_days=lookback_days,
        window_start=str(window_start),
        window_end=str(window_end),
        window_days=(window_end - window_start).days
    )

    return window_start, window_end


def parse_api_date(date_str: str) -> date:
    """
    Parse date from API response

    Handles various date formats from API.

    Args:
        date_str: Date string from API (e.g., "2023-01-15" or "2023-01-15T00:00:00")

    Returns:
        date object

    Raises:
        ValueError: If date format is invalid
    """
    if not date_str:
        raise ValueError("Empty date string")

    # Try ISO format (YYYY-MM-DD)
    try:
        return date.fromisoformat(date_str[:10])
    except (ValueError, TypeError) as e:
        logger.error("date_parse_error", date_str=date_str, error=str(e))
        raise ValueError(f"Invalid date format: {date_str}")


def parse_api_datetime(datetime_str: str) -> datetime:
    """
    Parse datetime from API response

    Args:
        datetime_str: Datetime string from API (e.g., "2023-01-15T10:30:00")

    Returns:
        datetime object

    Raises:
        ValueError: If datetime format is invalid
    """
    if not datetime_str:
        raise ValueError("Empty datetime string")

    # Try ISO format
    try:
        # Remove timezone info if present (API returns inconsistent formats)
        clean_str = datetime_str.replace("Z", "").split("+")[0].split(".")[0]
        return datetime.fromisoformat(clean_str)
    except (ValueError, TypeError) as e:
        logger.error("datetime_parse_error", datetime_str=datetime_str, error=str(e))
        raise ValueError(f"Invalid datetime format: {datetime_str}")


def format_date_for_api(d: date) -> str:
    """
    Format date for API request (YYYY-MM-DD)

    Args:
        d: date object

    Returns:
        Formatted date string
    """
    return d.strftime("%Y-%m-%d")


def get_date_range_description(start: date, end: date) -> str:
    """
    Get human-readable description of date range

    Args:
        start: Start date
        end: End date

    Returns:
        Description string

    Example:
        >>> get_date_range_description(date(2023, 1, 1), date(2023, 12, 31))
        "2023-01-01 to 2023-12-31 (365 days)"
    """
    days = (end - start).days + 1
    return f"{start} to {end} ({days} days)"


def is_date_in_range(d: date, start: date, end: date) -> bool:
    """
    Check if date is within range (inclusive)

    Args:
        d: Date to check
        start: Range start
        end: Range end

    Returns:
        True if date is in range
    """
    return start <= d <= end


def get_current_quarter(d: date = None) -> Tuple[date, date]:
    """
    Get start and end dates of current quarter

    Args:
        d: Date to find quarter for (defaults to today)

    Returns:
        (quarter_start, quarter_end) tuple

    Example:
        >>> get_current_quarter(date(2023, 5, 15))
        (date(2023, 4, 1), date(2023, 6, 30))
    """
    if d is None:
        d = date.today()

    # Determine quarter
    quarter = (d.month - 1) // 3 + 1

    # Calculate start and end
    start_month = (quarter - 1) * 3 + 1
    quarter_start = date(d.year, start_month, 1)

    end_month = quarter * 3
    quarter_end = (date(d.year, end_month, 1) + relativedelta(months=1)) - timedelta(days=1)

    return quarter_start, quarter_end


def days_between(start: date, end: date) -> int:
    """
    Calculate number of days between two dates

    Args:
        start: Start date
        end: End date

    Returns:
        Number of days (can be negative if end < start)
    """
    return (end - start).days


# ============================================================================
# TESTING
# ============================================================================

if __name__ == "__main__":
    # Test date utilities
    print("=== Date Utilities Tests ===\n")

    # Test 1: Quarterly chunks
    print("1. Quarterly chunks for 2023:")
    chunks = generate_quarterly_chunks(date(2023, 1, 1), date(2023, 12, 31))
    for i, (start, end) in enumerate(chunks, 1):
        print(f"   Q{i}: {get_date_range_description(start, end)}")

    # Test 2: Incremental window
    print("\n2. Incremental window:")
    last_sync = date(2024, 1, 15)
    window = get_incremental_date_window(last_sync, lookback_days=7)
    print(f"   Window: {get_date_range_description(window[0], window[1])}")

    # Test 3: Current quarter
    print("\n3. Current quarter:")
    q_start, q_end = get_current_quarter()
    print(f"   {get_date_range_description(q_start, q_end)}")

    # Test 4: Date parsing
    print("\n4. Date parsing:")
    test_dates = [
        "2023-01-15",
        "2023-01-15T00:00:00",
        "2023-01-15T10:30:45"
    ]
    for date_str in test_dates:
        try:
            parsed = parse_api_date(date_str)
            print(f"   ✅ {date_str} → {parsed}")
        except ValueError as e:
            print(f"   ❌ {date_str} → {e}")

    print("\n✅ All tests completed")
