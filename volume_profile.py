"""
Volume Profile Analysis for identifying high-volume price levels (POC, VAH, VAL)
"""
import pandas as pd
import numpy as np
from typing import Dict, Tuple, List
from logger import Logger


class VolumeProfile:
    """Analyze volume distribution across price levels for smarter trading"""

    def __init__(self):
        self.logger = Logger.get_logger()

    def calculate_volume_profile(self, df: pd.DataFrame, num_bins: int = 50) -> Dict:
        """
        Calculate volume profile to identify key price levels

        Args:
            df: DataFrame with OHLCV data
            num_bins: Number of price bins to divide the range into

        Returns:
            Dict with POC (Point of Control), VAH (Value Area High), VAL (Value Area Low)
        """
        if df.empty or len(df) < 20:
            return {'poc': None, 'vah': None, 'val': None, 'volume_nodes': []}

        try:
            # Get price range
            price_min = df['low'].min()
            price_max = df['high'].max()

            if price_max <= price_min:
                return {'poc': None, 'vah': None, 'val': None, 'volume_nodes': []}

            # Create price bins
            bin_edges = np.linspace(price_min, price_max, num_bins + 1)
            bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2

            # Calculate volume at each price level
            volume_at_price = np.zeros(num_bins)

            for idx, row in df.iterrows():
                # Distribute volume across price range of the candle
                low, high, volume = row['low'], row['high'], row['volume']

                # Find bins that this candle touches
                low_bin = np.searchsorted(bin_edges, low, side='right') - 1
                high_bin = np.searchsorted(bin_edges, high, side='left')

                # Clamp to valid range
                low_bin = max(0, min(low_bin, num_bins - 1))
                high_bin = max(0, min(high_bin, num_bins - 1))

                # Distribute volume evenly across touched bins
                if low_bin == high_bin:
                    volume_at_price[low_bin] += volume
                else:
                    bins_touched = high_bin - low_bin + 1
                    for bin_idx in range(low_bin, high_bin + 1):
                        volume_at_price[bin_idx] += volume / bins_touched

            # Find Point of Control (highest volume price level)
            poc_idx = np.argmax(volume_at_price)
            poc = bin_centers[poc_idx]

            # Calculate Value Area (70% of volume)
            total_volume = volume_at_price.sum()
            target_volume = total_volume * 0.70

            # Start from POC and expand outward until 70% volume is captured
            va_volume = volume_at_price[poc_idx]
            lower_idx = poc_idx
            upper_idx = poc_idx

            while va_volume < target_volume and (lower_idx > 0 or upper_idx < num_bins - 1):
                # Determine which direction to expand (higher volume)
                lower_volume = volume_at_price[lower_idx - 1] if lower_idx > 0 else 0
                upper_volume = volume_at_price[upper_idx + 1] if upper_idx < num_bins - 1 else 0

                if lower_volume > upper_volume and lower_idx > 0:
                    lower_idx -= 1
                    va_volume += lower_volume
                elif upper_idx < num_bins - 1:
                    upper_idx += 1
                    va_volume += upper_volume
                else:
                    break

            val = bin_centers[lower_idx]  # Value Area Low
            vah = bin_centers[upper_idx]  # Value Area High

            # Identify significant volume nodes (local maxima above average)
            avg_volume = volume_at_price.mean()
            volume_nodes = []
            for i in range(1, num_bins - 1):
                if (volume_at_price[i] > volume_at_price[i-1] and
                    volume_at_price[i] > volume_at_price[i+1] and
                    volume_at_price[i] > avg_volume * 1.5):
                    volume_nodes.append({
                        'price': bin_centers[i],
                        'volume': volume_at_price[i],
                        'strength': volume_at_price[i] / volume_at_price[poc_idx]
                    })

            return {
                'poc': poc,
                'vah': vah,
                'val': val,
                'volume_nodes': volume_nodes,
                'total_volume': total_volume
            }

        except Exception as e:
            self.logger.error(f"Error calculating volume profile: {e}")
            return {'poc': None, 'vah': None, 'val': None, 'volume_nodes': []}

    def is_near_high_volume_node(self, current_price: float, volume_profile: Dict,
                                  threshold: float = 0.02) -> Tuple[bool, str]:
        """
        Check if current price is near a significant volume node

        Args:
            current_price: Current market price
            volume_profile: Volume profile dict from calculate_volume_profile()
            threshold: Distance threshold as percentage (default 2%)

        Returns:
            Tuple of (is_near, node_type) where node_type is 'POC', 'VAH', 'VAL', or 'NODE'
        """
        if not volume_profile or volume_profile.get('poc') is None:
            return False, ''

        poc = volume_profile['poc']
        vah = volume_profile['vah']
        val = volume_profile['val']

        # Check POC (strongest level)
        if abs(current_price - poc) / current_price < threshold:
            return True, 'POC'

        # Check VAH
        if abs(current_price - vah) / current_price < threshold:
            return True, 'VAH'

        # Check VAL
        if abs(current_price - val) / current_price < threshold:
            return True, 'VAL'

        # Check other volume nodes
        for node in volume_profile.get('volume_nodes', []):
            if abs(current_price - node['price']) / current_price < threshold:
                return True, 'NODE'

        return False, ''

    def get_support_resistance_from_volume(self, current_price: float,
                                          volume_profile: Dict) -> Dict:
        """
        Identify support and resistance levels from volume profile

        Args:
            current_price: Current market price
            volume_profile: Volume profile dict from calculate_volume_profile()

        Returns:
            Dict with support and resistance levels from volume analysis
        """
        if not volume_profile or volume_profile.get('poc') is None:
            return {'support': None, 'resistance': None, 'strength': 0.0}

        poc = volume_profile['poc']
        vah = volume_profile['vah']
        val = volume_profile['val']
        nodes = volume_profile.get('volume_nodes', [])

        # Collect all significant levels
        levels = [
            {'price': poc, 'strength': 1.0, 'type': 'POC'},
            {'price': vah, 'strength': 0.8, 'type': 'VAH'},
            {'price': val, 'strength': 0.8, 'type': 'VAL'}
        ]

        # Add volume nodes
        for node in nodes:
            levels.append({
                'price': node['price'],
                'strength': node['strength'],
                'type': 'NODE'
            })

        # Find closest support (below current price)
        support_levels = [level for level in levels if level['price'] < current_price]
        if support_levels:
            support = max(support_levels, key=lambda x: x['price'])
        else:
            support = None

        # Find closest resistance (above current price)
        resistance_levels = [level for level in levels if level['price'] > current_price]
        if resistance_levels:
            resistance = min(resistance_levels, key=lambda x: x['price'])
        else:
            resistance = None

        return {
            'support': support['price'] if support else None,
            'support_type': support['type'] if support else None,
            'support_strength': support['strength'] if support else 0.0,
            'resistance': resistance['price'] if resistance else None,
            'resistance_type': resistance['type'] if resistance else None,
            'resistance_strength': resistance['strength'] if resistance else 0.0,
            'in_value_area': val <= current_price <= vah if val and vah else False
        }
