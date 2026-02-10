"""Time-of-Use (TOU) configuration module for interactive period setup."""

from dataclasses import dataclass, field
from datetime import time
from typing import List, Optional
from src.utils import parse_time_string, validate_time_format


@dataclass
class TimeRange:
    """Represents a time range within a day."""
    start_time: time
    end_time: time

    def contains(self, check_time: time) -> bool:
        """
        Check if a time falls within this range.

        Handles midnight wrap-around (e.g., 23:00-02:00).

        Args:
            check_time: Time to check

        Returns:
            True if time is in range, False otherwise
        """
        if self.start_time <= self.end_time:
            # Normal range within same day (e.g., 09:00-17:00)
            return self.start_time <= check_time < self.end_time
        else:
            # Wraps around midnight (e.g., 23:00-02:00)
            return check_time >= self.start_time or check_time < self.end_time

    def __str__(self) -> str:
        """String representation of time range."""
        return f"{self.start_time.strftime('%H:%M')}-{self.end_time.strftime('%H:%M')}"


@dataclass
class PeriodDefinition:
    """Defines a time-of-use period with different rates for different day types."""
    name: str
    weekday_ranges: List[TimeRange] = field(default_factory=list)
    weekend_ranges: List[TimeRange] = field(default_factory=list)
    holiday_ranges: List[TimeRange] = field(default_factory=list)
    price_per_kwh: Optional[float] = None

    def matches(self, check_time: time, day_type: str) -> bool:
        """
        Check if a time matches this period for a given day type.

        Args:
            check_time: Time to check
            day_type: 'weekday', 'weekend', or 'holiday'

        Returns:
            True if time matches this period, False otherwise
        """
        if day_type == 'holiday' and self.holiday_ranges:
            ranges = self.holiday_ranges
        elif day_type == 'weekend' and self.weekend_ranges:
            ranges = self.weekend_ranges
        elif day_type == 'weekday' and self.weekday_ranges:
            ranges = self.weekday_ranges
        else:
            return False

        return any(time_range.contains(check_time) for time_range in ranges)


class TOUConfigurator:
    """Interactive CLI configurator for time-of-use periods."""

    VALID_STATES = ['NSW', 'VIC', 'QLD', 'SA', 'WA', 'TAS', 'NT', 'ACT']

    def __init__(self):
        """Initialize configurator."""
        self.periods: List[PeriodDefinition] = []
        self.state: Optional[str] = None

    def run_interactive_config(self) -> tuple[List[PeriodDefinition], str]:
        """
        Run interactive configuration to define TOU periods.

        Returns:
            Tuple of (period_definitions, state)
        """
        print("\n" + "=" * 50)
        print("Time-of-Use Period Configuration")
        print("=" * 50)

        # Get Australian state
        self.state = self._get_state()

        # Get number of periods
        num_periods = self._get_num_periods()

        # Configure each period
        for i in range(num_periods):
            print(f"\n--- Configuring Period {i + 1} of {num_periods} ---")
            period = self._configure_period()
            self.periods.append(period)

        # Show summary
        self._show_summary()

        return self.periods, self.state

    def _get_state(self) -> str:
        """Get Australian state from user."""
        while True:
            print(f"\nAvailable states: {', '.join(self.VALID_STATES)}")
            state = input("Enter your Australian state (e.g., NSW): ").strip().upper()

            if state in self.VALID_STATES:
                print(f"✓ State set to: {state}")
                return state
            else:
                print(f"✗ Invalid state. Please choose from: {', '.join(self.VALID_STATES)}")

    def _get_num_periods(self) -> int:
        """Get number of periods to define."""
        while True:
            try:
                num = input("\nHow many time-of-use periods do you want to define? (e.g., 3 for Peak/Shoulder/Off-peak): ").strip()
                num = int(num)
                if num < 1:
                    print("✗ Please enter at least 1 period")
                    continue
                if num > 10:
                    print("✗ Maximum 10 periods supported")
                    continue
                return num
            except ValueError:
                print("✗ Please enter a valid number")

    def _configure_period(self) -> PeriodDefinition:
        """Configure a single period interactively."""
        # Get period name
        name = input("\nPeriod name (e.g., Peak, Off-peak, Shoulder): ").strip()
        while not name:
            print("✗ Period name cannot be empty")
            name = input("Period name: ").strip()

        period = PeriodDefinition(name=name)

        # Configure weekday ranges
        print(f"\n--- {name}: Weekday Time Ranges ---")
        period.weekday_ranges = self._get_time_ranges("weekday")

        # Configure weekend ranges
        print(f"\n--- {name}: Weekend Time Ranges ---")
        use_same = input("Use same time ranges as weekdays? (y/n): ").strip().lower()
        if use_same == 'y':
            period.weekend_ranges = period.weekday_ranges.copy()
            print("✓ Using same ranges as weekdays")
        else:
            period.weekend_ranges = self._get_time_ranges("weekend")

        # Configure holiday ranges
        print(f"\n--- {name}: Public Holiday Time Ranges ---")
        use_same = input("Use same time ranges as weekends? (y/n): ").strip().lower()
        if use_same == 'y':
            period.holiday_ranges = period.weekend_ranges.copy()
            print("✓ Using same ranges as weekends")
        else:
            period.holiday_ranges = self._get_time_ranges("public holidays")

        # Get optional price
        print(f"\n--- {name}: Pricing (Optional) ---")
        price_input = input("Price per kWh in dollars (press Enter to skip): ").strip()
        if price_input:
            try:
                price = float(price_input)
                if price < 0:
                    print("✗ Price must be positive, skipping pricing")
                else:
                    period.price_per_kwh = price
                    print(f"✓ Price set to: ${price:.4f}/kWh")
            except ValueError:
                print("✗ Invalid price format, skipping pricing")

        return period

    def _get_time_ranges(self, day_type: str) -> List[TimeRange]:
        """
        Get time ranges for a day type interactively.

        Args:
            day_type: Description of day type (e.g., "weekday", "weekend")

        Returns:
            List of TimeRange objects
        """
        ranges = []

        print(f"Enter time ranges for {day_type} (format: HH:MM-HH:MM, e.g., 07:00-09:00)")
        print("You can add multiple ranges (e.g., morning peak and evening peak)")
        print("Press Enter without input when done")

        while True:
            range_input = input(f"  Time range #{len(ranges) + 1} (or Enter to finish): ").strip()

            if not range_input:
                if not ranges:
                    print("✗ At least one time range is required")
                    continue
                break

            # Parse range
            try:
                time_range = self._parse_time_range(range_input)
                ranges.append(time_range)
                print(f"  ✓ Added range: {time_range}")
            except ValueError as e:
                print(f"  ✗ {str(e)}")
                print("  Try again (e.g., 07:00-09:00 or 7:00 AM-9:00 AM)")

        return ranges

    def _parse_time_range(self, range_str: str) -> TimeRange:
        """
        Parse a time range string into TimeRange object.

        Args:
            range_str: String like "07:00-09:00" or "7:00 AM-9:00 AM"

        Returns:
            TimeRange object

        Raises:
            ValueError: If format is invalid
        """
        # Split on hyphen or dash
        parts = range_str.replace('–', '-').replace('—', '-').split('-')

        if len(parts) != 2:
            raise ValueError("Format should be: START-END (e.g., 07:00-09:00)")

        start_str = parts[0].strip()
        end_str = parts[1].strip()

        try:
            start_time = parse_time_string(start_str)
            end_time = parse_time_string(end_str)
        except ValueError as e:
            raise ValueError(f"Invalid time format: {str(e)}")

        # Allow same start and end time to represent full day
        if start_time == end_time and start_time.hour == 0 and start_time.minute == 0:
            # 00:00-00:00 means all day - set end to 23:59
            end_time = time(23, 59, 59)

        return TimeRange(start_time=start_time, end_time=end_time)

    def _show_summary(self):
        """Display summary of configured periods."""
        print("\n" + "=" * 50)
        print("Configuration Summary")
        print("=" * 50)
        print(f"State: {self.state}")
        print(f"Number of periods: {len(self.periods)}")

        for i, period in enumerate(self.periods, 1):
            print(f"\n{i}. {period.name}")

            if period.weekday_ranges:
                ranges_str = ", ".join(str(r) for r in period.weekday_ranges)
                print(f"   Weekdays: {ranges_str}")

            if period.weekend_ranges:
                ranges_str = ", ".join(str(r) for r in period.weekend_ranges)
                print(f"   Weekends: {ranges_str}")

            if period.holiday_ranges:
                ranges_str = ", ".join(str(r) for r in period.holiday_ranges)
                print(f"   Holidays: {ranges_str}")

            if period.price_per_kwh is not None:
                print(f"   Price: ${period.price_per_kwh:.4f}/kWh")

        print("\n" + "=" * 50)
