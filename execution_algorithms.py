"""
Advanced Order Execution Algorithms
TWAP, VWAP, Iceberg, and Transaction Cost Analysis
"""
import time
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from logger import Logger

class ExecutionAlgorithms:
    """Advanced order execution strategies for optimal trade execution"""

    def __init__(self, client):
        """
        Initialize execution algorithms

        Args:
            client: KuCoinClient instance for order execution
        """
        self.client = client
        self.logger = Logger.get_logger()
        self.execution_history = []

    def execute_twap(self, symbol: str, side: str, total_amount: float,
                    duration_minutes: int, leverage: int = 10,
                    num_slices: int = None) -> Dict:
        """
        Execute Time-Weighted Average Price (TWAP) order
        Splits order into equal slices over time

        Args:
            symbol: Trading pair symbol
            side: 'buy' or 'sell'
            total_amount: Total order amount
            duration_minutes: Time to complete execution
            leverage: Leverage to use
            num_slices: Number of order slices (auto-calculated if None)

        Returns:
            Execution summary with avg price and slippage
        """
        try:
            # Auto-calculate number of slices (one per minute, max 60)
            if num_slices is None:
                num_slices = min(duration_minutes, 60)

            slice_amount = total_amount / num_slices
            interval_seconds = (duration_minutes * 60) / num_slices

            self.logger.info(
                f"Starting TWAP execution: {total_amount} {symbol} over {duration_minutes}m "
                f"({num_slices} slices of {slice_amount:.4f})"
            )

            fills = []
            total_filled = 0.0
            start_time = time.time()

            for i in range(num_slices):
                # Execute slice
                order = self.client.create_market_order(
                    symbol, side, slice_amount, leverage,
                    max_slippage=0.003  # 0.3% slippage tolerance per slice
                )

                if order:
                    fills.append({
                        'price': order.get('average', order.get('price', 0)),
                        'amount': order.get('filled', slice_amount),
                        'timestamp': datetime.now()
                    })
                    total_filled += order.get('filled', 0)

                    self.logger.debug(
                        f"TWAP slice {i+1}/{num_slices}: "
                        f"filled {order.get('filled', 0)} @ {order.get('average', 0)}"
                    )

                # Wait for next slice (unless it's the last one)
                if i < num_slices - 1:
                    time.sleep(interval_seconds)

            # Calculate execution metrics
            if fills:
                avg_price = sum(f['price'] * f['amount'] for f in fills) / total_filled
                execution_time = time.time() - start_time

                summary = {
                    'strategy': 'TWAP',
                    'symbol': symbol,
                    'side': side,
                    'total_amount': total_amount,
                    'total_filled': total_filled,
                    'avg_price': avg_price,
                    'num_slices': len(fills),
                    'execution_time_seconds': execution_time,
                    'fills': fills
                }

                self.execution_history.append(summary)

                self.logger.info(
                    f"TWAP execution complete: "
                    f"filled {total_filled}/{total_amount} @ avg {avg_price:.2f} "
                    f"in {execution_time:.1f}s"
                )

                return summary
            else:
                self.logger.error("TWAP execution failed: no fills")
                return {}

        except Exception as e:
            self.logger.error(f"Error in TWAP execution: {e}")
            return {}

    def execute_vwap(self, symbol: str, side: str, total_amount: float,
                    duration_minutes: int, leverage: int = 10) -> Dict:
        """
        Execute Volume-Weighted Average Price (VWAP) order
        Weights slices based on historical volume patterns

        Args:
            symbol: Trading pair symbol
            side: 'buy' or 'sell'
            total_amount: Total order amount
            duration_minutes: Time to complete execution
            leverage: Leverage to use

        Returns:
            Execution summary with avg price and slippage
        """
        try:
            # Get historical volume data to determine weights
            ohlcv = self.client.get_ohlcv(symbol, timeframe='1m', limit=60)

            if not ohlcv or len(ohlcv) < 10:
                self.logger.warning("Insufficient volume data for VWAP, falling back to TWAP")
                return self.execute_twap(symbol, side, total_amount, duration_minutes, leverage)

            # Calculate volume weights for last N minutes
            recent_volumes = [candle[5] for candle in ohlcv[-duration_minutes:]]
            total_volume = sum(recent_volumes)

            if total_volume == 0:
                self.logger.warning("Zero volume detected, falling back to TWAP")
                return self.execute_twap(symbol, side, total_amount, duration_minutes, leverage)

            # Calculate weights based on volume distribution
            volume_weights = [v / total_volume for v in recent_volumes]

            self.logger.info(
                f"Starting VWAP execution: {total_amount} {symbol} over {duration_minutes}m "
                f"(volume-weighted)"
            )

            fills = []
            total_filled = 0.0
            start_time = time.time()

            # Execute slices according to volume weights
            for i, weight in enumerate(volume_weights):
                slice_amount = total_amount * weight

                # Skip very small slices
                if slice_amount < 0.01:
                    continue

                # Execute slice
                order = self.client.create_market_order(
                    symbol, side, slice_amount, leverage,
                    max_slippage=0.003
                )

                if order:
                    fills.append({
                        'price': order.get('average', order.get('price', 0)),
                        'amount': order.get('filled', slice_amount),
                        'weight': weight,
                        'timestamp': datetime.now()
                    })
                    total_filled += order.get('filled', 0)

                # Wait between slices (1 minute per slice)
                if i < len(volume_weights) - 1:
                    time.sleep(60)

            # Calculate execution metrics
            if fills:
                avg_price = sum(f['price'] * f['amount'] for f in fills) / total_filled
                execution_time = time.time() - start_time

                summary = {
                    'strategy': 'VWAP',
                    'symbol': symbol,
                    'side': side,
                    'total_amount': total_amount,
                    'total_filled': total_filled,
                    'avg_price': avg_price,
                    'num_slices': len(fills),
                    'execution_time_seconds': execution_time,
                    'fills': fills
                }

                self.execution_history.append(summary)

                self.logger.info(
                    f"VWAP execution complete: "
                    f"filled {total_filled}/{total_amount} @ avg {avg_price:.2f}"
                )

                return summary
            else:
                self.logger.error("VWAP execution failed: no fills")
                return {}

        except Exception as e:
            self.logger.error(f"Error in VWAP execution: {e}")
            return {}

    def execute_iceberg(self, symbol: str, side: str, total_amount: float,
                       visible_amount: float, price: float,
                       leverage: int = 10, max_duration_minutes: int = 60) -> Dict:
        """
        Execute Iceberg order (large order split into smaller visible chunks)

        Args:
            symbol: Trading pair symbol
            side: 'buy' or 'sell'
            total_amount: Total order amount (the "iceberg")
            visible_amount: Amount visible in order book per slice
            price: Limit price for orders
            leverage: Leverage to use
            max_duration_minutes: Maximum time to attempt execution

        Returns:
            Execution summary
        """
        try:
            num_slices = int(np.ceil(total_amount / visible_amount))

            self.logger.info(
                f"Starting Iceberg execution: {total_amount} {symbol} "
                f"(visible: {visible_amount}, {num_slices} slices)"
            )

            fills = []
            total_filled = 0.0
            start_time = time.time()
            max_duration_seconds = max_duration_minutes * 60

            remaining_amount = total_amount

            while remaining_amount > 0 and (time.time() - start_time) < max_duration_seconds:
                # Place limit order for visible amount
                slice_amount = min(visible_amount, remaining_amount)

                # Attempt to call create_limit_order with post_only, handle missing method or unsupported parameter
                try:
                    if hasattr(self.client, "create_limit_order"):
                        try:
                            order = self.client.create_limit_order(
                                symbol, side, slice_amount, price, leverage,
                                post_only=True  # Maker order for better fees
                            )
                        except TypeError as te:
                            self.logger.error(
                                f"create_limit_order does not accept 'post_only' parameter: {te}"
                            )
                            order = None
                    else:
                        self.logger.error("Client does not implement create_limit_order method.")
                        order = None
                except Exception as e:
                    self.logger.error(f"Error calling create_limit_order: {e}")
                    order = None

                if not order:
                    self.logger.warning("Failed to create iceberg slice, retrying...")
                    time.sleep(5)
                    continue

                order_id = order.get('id')

                # Wait for order to fill (with timeout)
                filled_order = self.client.wait_for_order_fill(
                    order_id, symbol, timeout=120, check_interval=5
                )

                if filled_order and filled_order['status'] == 'closed':
                    fills.append({
                        'price': filled_order['average'],
                        'amount': filled_order['filled'],
                        'timestamp': datetime.now()
                    })
                    total_filled += filled_order['filled']
                    remaining_amount -= filled_order['filled']

                    self.logger.debug(
                        f"Iceberg slice filled: {filled_order['filled']} @ {filled_order['average']}"
                    )
                else:
                    # Order not filled, cancel and try again with market order if near end
                    self.client.cancel_order(order_id, symbol)

                    if (time.time() - start_time) > max_duration_seconds * 0.8:
                        # Near timeout, execute remaining as market order
                        self.logger.info(f"Executing remaining {remaining_amount} as market order")
                        market_order = self.client.create_market_order(
                            symbol, side, remaining_amount, leverage
                        )
                        if market_order:
                            fills.append({
                                'price': market_order.get('average', price),
                                'amount': market_order.get('filled', remaining_amount),
                                'timestamp': datetime.now()
                            })
                            total_filled += market_order.get('filled', 0)
                        break

            # Calculate execution metrics
            if fills:
                avg_price = sum(f['price'] * f['amount'] for f in fills) / total_filled
                execution_time = time.time() - start_time

                summary = {
                    'strategy': 'Iceberg',
                    'symbol': symbol,
                    'side': side,
                    'total_amount': total_amount,
                    'total_filled': total_filled,
                    'avg_price': avg_price,
                    'num_slices': len(fills),
                    'execution_time_seconds': execution_time,
                    'fills': fills
                }

                self.execution_history.append(summary)

                self.logger.info(
                    f"Iceberg execution complete: "
                    f"filled {total_filled}/{total_amount} @ avg {avg_price:.2f}"
                )

                return summary
            else:
                self.logger.error("Iceberg execution failed: no fills")
                return {}

        except Exception as e:
            self.logger.error(f"Error in Iceberg execution: {e}")
            return {}

    def calculate_transaction_costs(self, execution_summary: Dict,
                                   reference_price: float,
                                   maker_fee: float = 0.0002,
                                   taker_fee: float = 0.0006) -> Dict:
        """
        Analyze transaction costs for an execution

        Args:
            execution_summary: Summary from execute_* method
            reference_price: Reference price at start of execution
            maker_fee: Maker fee rate (default 0.02%)
            taker_fee: Taker fee rate (default 0.06%)

        Returns:
            Dictionary with cost analysis
        """
        try:
            avg_price = execution_summary.get('avg_price', 0)
            total_filled = execution_summary.get('total_filled', 0)
            side = execution_summary.get('side', 'buy')
            strategy = execution_summary.get('strategy', 'unknown')

            # Calculate slippage
            if side == 'buy':
                slippage_pct = (avg_price - reference_price) / reference_price
            else:
                slippage_pct = (reference_price - avg_price) / reference_price

            # Estimate fees (assume 50/50 maker/taker for TWAP/VWAP, 100% maker for Iceberg)
            if strategy == 'Iceberg':
                estimated_fee_rate = maker_fee
            else:
                estimated_fee_rate = (maker_fee + taker_fee) / 2

            position_value = total_filled * avg_price
            estimated_fees = position_value * estimated_fee_rate

            # Total transaction cost
            slippage_cost = abs(slippage_pct) * position_value
            total_cost = slippage_cost + estimated_fees
            total_cost_pct = total_cost / position_value

            analysis = {
                'reference_price': reference_price,
                'avg_execution_price': avg_price,
                'slippage_pct': slippage_pct,
                'slippage_cost': slippage_cost,
                'estimated_fees': estimated_fees,
                'total_transaction_cost': total_cost,
                'total_cost_pct': total_cost_pct,
                'position_value': position_value,
                'cost_breakdown': {
                    'slippage': slippage_cost,
                    'fees': estimated_fees
                }
            }

            self.logger.info(
                f"Transaction Cost Analysis ({strategy}): "
                f"slippage={slippage_pct:.4%}, fees=${estimated_fees:.2f}, "
                f"total_cost=${total_cost:.2f} ({total_cost_pct:.4%})"
            )

            return analysis

        except Exception as e:
            self.logger.error(f"Error calculating transaction costs: {e}")
            return {}

    def get_best_execution_strategy(self, symbol: str, amount: float,
                                   urgency: str = 'medium') -> str:
        """
        Recommend best execution strategy based on conditions

        Args:
            symbol: Trading pair symbol
            amount: Order amount
            urgency: 'high', 'medium', or 'low'

        Returns:
            Recommended strategy: 'market', 'twap', 'vwap', or 'iceberg'
        """
        try:
            # Get order book depth
            order_book = self.client.get_order_book(symbol, limit=20)

            if not order_book:
                return 'market'  # Default to market if can't get order book

            # Calculate available liquidity
            side_liquidity = order_book.get('asks', []) if amount > 0 else order_book.get('bids', [])
            total_liquidity = sum(level[1] for level in side_liquidity)

            # Decision logic
            liquidity_ratio = total_liquidity / abs(amount) if amount != 0 else 0

            if urgency == 'high':
                # Need immediate execution
                return 'market'
            elif liquidity_ratio < 1.5:
                # Low liquidity - use Iceberg to minimize market impact
                return 'iceberg'
            elif amount > 1000:  # Large order threshold
                # Large order - use VWAP for optimal execution
                return 'vwap'
            elif urgency == 'low':
                # Can afford to wait - use TWAP for best average
                return 'twap'
            else:
                # Default to market for standard orders
                return 'market'

        except Exception as e:
            self.logger.error(f"Error determining execution strategy: {e}")
            return 'market'
