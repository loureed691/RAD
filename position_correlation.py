"""
Position Correlation Manager
Intelligent portfolio diversification through correlation analysis
"""
import numpy as np
from typing import Dict, List, Tuple
from logger import Logger
from datetime import datetime, timedelta


class PositionCorrelationManager:
    """
    Manages portfolio correlations for optimal diversification:
    - Real-time correlation calculation between positions
    - Correlation-aware position sizing
    - Portfolio heat mapping
    - Sector/category concentration limits
    - Dynamic correlation thresholds
    """

    def __init__(self):
        self.logger = Logger.get_logger()

        # Enhanced correlation groups with more granularity
        self.asset_categories = {
            # Major cryptocurrencies
            'btc_group': ['BTC', 'BTCUSDT', 'XBTUSD'],
            'eth_group': ['ETH', 'ETHUSDT'],

            # DeFi tokens
            'defi_protocols': ['UNI', 'AAVE', 'COMP', 'MKR', 'SNX'],
            'defi_exchanges': ['SUSHI', 'CAKE', '1INCH'],

            # Layer 1 blockchains
            'layer1_high_cap': ['SOL', 'ADA', 'AVAX', 'DOT'],
            'layer1_mid_cap': ['NEAR', 'ATOM', 'ALGO', 'FTM'],

            # Layer 2 solutions
            'layer2': ['MATIC', 'OP', 'ARB', 'LRC', 'IMX'],

            # Meme coins (highly correlated during trends)
            'meme_coins': ['DOGE', 'SHIB', 'PEPE', 'FLOKI'],

            # Exchange tokens
            'exchange_tokens': ['BNB', 'OKB', 'FTT', 'KCS'],

            # Gaming/Metaverse
            'gaming_meta': ['SAND', 'MANA', 'AXS', 'GALA'],

            # AI/Data tokens
            'ai_data': ['FET', 'OCEAN', 'GRT', 'RNDR']
        }

        # Correlation thresholds
        self.high_correlation_threshold = 0.7
        self.moderate_correlation_threshold = 0.5

        # Category concentration limits (% of portfolio)
        self.category_limits = {
            'single_category': 0.4,  # Max 40% in any single category
            'correlated_group': 0.6  # Max 60% in highly correlated assets
        }

        # Price history cache for correlation calculation
        self.price_history = {}  # symbol -> list of prices
        self.max_history_length = 100

        self.logger.info("🔗 Position Correlation Manager initialized")

    def get_asset_category(self, symbol: str) -> str:
        """
        Determine which category an asset belongs to

        Args:
            symbol: Trading pair symbol

        Returns:
            Category name or 'unknown'
        """
        try:
            # Extract base asset
            base = symbol.replace('USDT', '').replace('USD', '').replace('PERP', '')

            for category, assets in self.asset_categories.items():
                if base in assets or symbol in assets:
                    return category

            return 'unknown'

        except Exception as e:
            self.logger.debug(f"Error determining asset category: {e}")
            return 'unknown'

    def update_price_history(self, symbol: str, price: float):
        """
        Update price history for correlation calculation

        Args:
            symbol: Trading pair symbol
            price: Current price
        """
        try:
            if symbol not in self.price_history:
                self.price_history[symbol] = []

            self.price_history[symbol].append({
                'price': price,
                'timestamp': datetime.now()
            })

            # Keep only recent history
            if len(self.price_history[symbol]) > self.max_history_length:
                self.price_history[symbol] = self.price_history[symbol][-self.max_history_length:]

        except Exception as e:
            self.logger.debug(f"Error updating price history: {e}")

    def calculate_correlation(self, symbol1: str, symbol2: str,
                            lookback_periods: int = 50) -> float:
        """
        Calculate correlation between two assets

        Args:
            symbol1: First symbol
            symbol2: Second symbol
            lookback_periods: Number of periods to analyze

        Returns:
            Correlation coefficient (-1 to 1)
        """
        try:
            # Check if we have enough history
            if symbol1 not in self.price_history or symbol2 not in self.price_history:
                # Use category-based correlation estimate
                cat1 = self.get_asset_category(symbol1)
                cat2 = self.get_asset_category(symbol2)

                if cat1 == cat2 and cat1 != 'unknown':
                    return 0.8  # High correlation within same category
                elif self._are_categories_related(cat1, cat2):
                    return 0.5  # Moderate correlation for related categories
                else:
                    return 0.2  # Low correlation assumption

            history1 = self.price_history[symbol1][-lookback_periods:]
            history2 = self.price_history[symbol2][-lookback_periods:]

            # Need at least 10 data points
            if len(history1) < 10 or len(history2) < 10:
                cat1 = self.get_asset_category(symbol1)
                cat2 = self.get_asset_category(symbol2)
                if cat1 == cat2:
                    return 0.8
                else:
                    return 0.3

            # Align histories by timestamp (simple approach: use min length)
            min_len = min(len(history1), len(history2))
            prices1 = [h['price'] for h in history1[-min_len:]]
            prices2 = [h['price'] for h in history2[-min_len:]]

            # Calculate returns
            returns1 = np.diff(prices1) / prices1[:-1]
            returns2 = np.diff(prices2) / prices2[:-1]

            # Calculate correlation
            if len(returns1) < 5 or len(returns2) < 5:
                return 0.3  # Not enough data

            correlation = np.corrcoef(returns1, returns2)[0, 1]

            # Handle NaN
            if np.isnan(correlation):
                return 0.3

            return correlation

        except Exception as e:
            self.logger.debug(f"Error calculating correlation: {e}")
            return 0.3  # Default moderate correlation

    def _are_categories_related(self, cat1: str, cat2: str) -> bool:
        """
        Check if two categories are related

        Args:
            cat1: First category
            cat2: Second category

        Returns:
            True if categories are related
        """
        related_groups = [
            {'defi_protocols', 'defi_exchanges'},
            {'layer1_high_cap', 'layer1_mid_cap'},
            {'btc_group', 'eth_group'},  # Majors often move together
            {'gaming_meta', 'ai_data'}  # Tech-focused tokens
        ]

        for group in related_groups:
            if cat1 in group and cat2 in group:
                return True

        return False

    def calculate_portfolio_correlation_matrix(self,
                                              positions: List[Dict]) -> Dict[str, Dict[str, float]]:
        """
        Calculate correlation matrix for all open positions

        Args:
            positions: List of position dictionaries

        Returns:
            Correlation matrix as nested dict
        """
        try:
            symbols = [p['symbol'] for p in positions]

            if not symbols:
                return {}

            matrix = {}
            for sym1 in symbols:
                matrix[sym1] = {}
                for sym2 in symbols:
                    if sym1 == sym2:
                        matrix[sym1][sym2] = 1.0
                    else:
                        matrix[sym1][sym2] = self.calculate_correlation(sym1, sym2)

            return matrix

        except Exception as e:
            self.logger.error(f"Error calculating correlation matrix: {e}")
            return {}

    def calculate_portfolio_heat(self, positions: List[Dict],
                                correlation_matrix: Dict = None) -> float:
        """
        Calculate portfolio concentration/heat score

        Args:
            positions: List of positions
            correlation_matrix: Pre-calculated correlation matrix

        Returns:
            Heat score (0.0 = well diversified, 1.0 = highly concentrated)
        """
        try:
            if not positions or len(positions) == 0:
                return 0.0

            if len(positions) == 1:
                return 0.5  # Single position = moderate heat

            # Calculate correlation matrix if not provided
            if correlation_matrix is None:
                correlation_matrix = self.calculate_portfolio_correlation_matrix(positions)

            # Calculate weighted average correlation
            total_correlation = 0.0
            pair_count = 0

            symbols = [p['symbol'] for p in positions]
            for i, sym1 in enumerate(symbols):
                for sym2 in symbols[i+1:]:
                    if sym1 in correlation_matrix and sym2 in correlation_matrix[sym1]:
                        corr = abs(correlation_matrix[sym1][sym2])
                        total_correlation += corr
                        pair_count += 1

            if pair_count == 0:
                return 0.3  # Default moderate heat

            avg_correlation = total_correlation / pair_count

            # Also consider category concentration
            category_counts = {}
            for position in positions:
                category = self.get_asset_category(position['symbol'])
                category_counts[category] = category_counts.get(category, 0) + 1

            # Calculate category concentration (Herfindahl index)
            total_positions = len(positions)
            concentration = sum((count / total_positions) ** 2
                              for count in category_counts.values())

            # Combine correlation and concentration
            # High correlation or high concentration = high heat
            heat_score = (avg_correlation * 0.6) + (concentration * 0.4)

            return min(heat_score, 1.0)

        except Exception as e:
            self.logger.error(f"Error calculating portfolio heat: {e}")
            return 0.5

    def get_correlation_adjusted_size(self,
                                     symbol: str,
                                     base_size: float,
                                     existing_positions: List[Dict],
                                     correlation_matrix: Dict = None) -> float:
        """
        Adjust position size based on correlation with existing positions

        Args:
            symbol: Symbol to trade
            base_size: Base position size
            existing_positions: Current positions
            correlation_matrix: Pre-calculated correlation matrix

        Returns:
            Adjusted position size
        """
        try:
            if not existing_positions:
                return base_size  # No adjustment needed

            # Calculate average correlation with existing positions
            correlations = []
            for position in existing_positions:
                pos_symbol = position['symbol']
                corr = self.calculate_correlation(symbol, pos_symbol)
                correlations.append(abs(corr))

            avg_correlation = np.mean(correlations) if correlations else 0.0

            # Reduce size if highly correlated
            if avg_correlation > self.high_correlation_threshold:
                # Reduce by up to 40% for very high correlation
                reduction = 0.4 * ((avg_correlation - self.high_correlation_threshold) /
                                  (1.0 - self.high_correlation_threshold))
                adjusted_size = base_size * (1.0 - reduction)

                self.logger.info(
                    f"🔗 High correlation detected ({avg_correlation:.2f}): "
                    f"Reducing position size by {reduction*100:.1f}%"
                )

            elif avg_correlation > self.moderate_correlation_threshold:
                # Reduce by up to 20% for moderate correlation
                reduction = 0.2 * ((avg_correlation - self.moderate_correlation_threshold) /
                                  (self.high_correlation_threshold - self.moderate_correlation_threshold))
                adjusted_size = base_size * (1.0 - reduction)

                self.logger.info(
                    f"🔗 Moderate correlation detected ({avg_correlation:.2f}): "
                    f"Reducing position size by {reduction*100:.1f}%"
                )
            else:
                # Low correlation - no adjustment
                adjusted_size = base_size

            return adjusted_size

        except Exception as e:
            self.logger.error(f"Error calculating correlation-adjusted size: {e}")
            return base_size

    def check_category_concentration(self,
                                    symbol: str,
                                    existing_positions: List[Dict],
                                    portfolio_value: float) -> Tuple[bool, str]:
        """
        Check if adding a position would exceed category concentration limits

        Args:
            symbol: Symbol to add
            existing_positions: Current positions
            portfolio_value: Total portfolio value

        Returns:
            (allowed, reason) tuple
        """
        try:
            if not existing_positions:
                return True, "First position"

            new_category = self.get_asset_category(symbol)

            # Calculate current category allocations
            category_values = {}
            for position in existing_positions:
                pos_category = self.get_asset_category(position['symbol'])
                pos_value = position.get('value', 0)
                category_values[pos_category] = category_values.get(pos_category, 0) + pos_value

            # Check single category limit
            # Skip concentration check for 'unknown' category as it contains diverse, unrelated assets
            if new_category in category_values and new_category != 'unknown':
                category_pct = category_values[new_category] / portfolio_value
                if category_pct > self.category_limits['single_category']:
                    return False, f"Category '{new_category}' already at {category_pct:.1%} (limit: {self.category_limits['single_category']:.1%})"

            # Check correlated group limit
            # Sum all highly correlated positions
            correlated_value = 0.0
            for position in existing_positions:
                corr = self.calculate_correlation(symbol, position['symbol'])
                if abs(corr) > self.high_correlation_threshold:
                    correlated_value += position.get('value', 0)

            if correlated_value > 0:
                correlated_pct = correlated_value / portfolio_value
                if correlated_pct > self.category_limits['correlated_group']:
                    return False, f"Correlated positions already at {correlated_pct:.1%} (limit: {self.category_limits['correlated_group']:.1%})"

            return True, "Concentration limits satisfied"

        except Exception as e:
            self.logger.error(f"Error checking category concentration: {e}")
            return True, "Error checking concentration (allowing trade)"
