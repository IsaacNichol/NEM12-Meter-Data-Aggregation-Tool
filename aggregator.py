"""Meter data aggregation module for classifying and aggregating intervals."""

import pandas as pd
import holidays
from datetime import datetime
from typing import List
from tou_config import PeriodDefinition


class MeterDataAggregator:
    """Aggregates meter interval data by time-of-use periods."""

    def __init__(self, df: pd.DataFrame, periods: List[PeriodDefinition], state: str):
        """
        Initialize aggregator.

        Args:
            df: DataFrame with interval data from NEM12 parser
            periods: List of PeriodDefinition objects
            state: Australian state code for holiday detection
        """
        self.df = df.copy()
        self.periods = periods
        self.state = state
        self.holidays = holidays.country_holidays('AU', subdiv=state)

    def classify_intervals(self) -> pd.DataFrame:
        """
        Add 'period' column to DataFrame classifying each interval.

        Returns:
            DataFrame with added 'period' column
        """
        # Add day type classification
        self.df['day_type'] = self.df['timestamp'].apply(self._classify_day_type)

        # Add period classification
        self.df['period'] = self.df.apply(
            lambda row: self._classify_interval(row['timestamp'], row['day_type']),
            axis=1
        )

        return self.df

    def _classify_day_type(self, timestamp: datetime) -> str:
        """
        Classify a timestamp as 'holiday', 'weekend', or 'weekday'.

        Priority: holiday > weekend > weekday

        Args:
            timestamp: Datetime to classify

        Returns:
            'holiday', 'weekend', or 'weekday'
        """
        # Check if it's a public holiday
        if timestamp.date() in self.holidays:
            return 'holiday'

        # Check if it's a weekend (Saturday=5, Sunday=6)
        if timestamp.weekday() >= 5:
            return 'weekend'

        return 'weekday'

    def _classify_interval(self, timestamp: datetime, day_type: str) -> str:
        """
        Classify an interval into a period based on time and day type.

        Args:
            timestamp: Timestamp of interval
            day_type: 'holiday', 'weekend', or 'weekday'

        Returns:
            Period name or 'Unclassified'
        """
        interval_time = timestamp.time()

        # Check each period in order (first match wins)
        for period in self.periods:
            if period.matches(interval_time, day_type):
                return period.name

        return 'Unclassified'

    def aggregate(self) -> pd.DataFrame:
        """
        Aggregate data by period.

        Returns:
            DataFrame with aggregated results per period
        """
        # Ensure intervals are classified
        if 'period' not in self.df.columns:
            self.classify_intervals()

        # Group by period and aggregate
        agg_results = self.df.groupby('period').agg(
            total_kwh=('consumption_kwh', 'sum'),
            interval_count=('consumption_kwh', 'count'),
            avg_kwh_per_interval=('consumption_kwh', 'mean'),
            min_date=('timestamp', 'min'),
            max_date=('timestamp', 'max'),
            estimated_count=('is_estimate', 'sum')
        ).reset_index()

        # Calculate percentage of total consumption
        total_consumption = agg_results['total_kwh'].sum()
        agg_results['percentage'] = (agg_results['total_kwh'] / total_consumption * 100) if total_consumption > 0 else 0

        # Add cost calculation if prices are available
        agg_results['total_cost'] = None

        for i, row in agg_results.iterrows():
            period_name = row['period']

            # Find matching period definition
            period_def = next((p for p in self.periods if p.name == period_name), None)

            if period_def and period_def.price_per_kwh is not None:
                cost = row['total_kwh'] * period_def.price_per_kwh
                agg_results.at[i, 'total_cost'] = cost

        # Sort by total_kwh descending (except Unclassified goes last)
        agg_results['sort_key'] = agg_results.apply(
            lambda row: (0, -row['total_kwh']) if row['period'] != 'Unclassified' else (1, 0),
            axis=1
        )
        agg_results = agg_results.sort_values('sort_key').drop('sort_key', axis=1)

        return agg_results

    def get_summary_stats(self) -> dict:
        """
        Get summary statistics about the aggregated data.

        Returns:
            Dictionary with summary information
        """
        if 'period' not in self.df.columns:
            self.classify_intervals()

        stats = {
            'total_intervals': len(self.df),
            'total_kwh': self.df['consumption_kwh'].sum(),
            'date_range_start': self.df['timestamp'].min(),
            'date_range_end': self.df['timestamp'].max(),
            'total_days': (self.df['timestamp'].max() - self.df['timestamp'].min()).days + 1,
            'estimated_intervals': self.df['is_estimate'].sum(),
            'estimated_percentage': (self.df['is_estimate'].sum() / len(self.df) * 100) if len(self.df) > 0 else 0,
            'unclassified_intervals': (self.df['period'] == 'Unclassified').sum(),
            'unclassified_percentage': ((self.df['period'] == 'Unclassified').sum() / len(self.df) * 100) if len(self.df) > 0 else 0,
        }

        # Count by day type
        day_type_counts = self.df['day_type'].value_counts().to_dict()
        stats['weekday_intervals'] = day_type_counts.get('weekday', 0)
        stats['weekend_intervals'] = day_type_counts.get('weekend', 0)
        stats['holiday_intervals'] = day_type_counts.get('holiday', 0)

        return stats
