"""
Risk management system for the trading bot
"""
from typing import Dict, List, Tuple
from logger import Logger
try:
    import numpy as np
except ImportError as e:
    Logger.get_logger().error("Numpy is required but not installed. Please install numpy to proceed.")
    raise

class RiskManager:
    """Manage trading risk and position sizing"""
    
    def __init__(self, max_position_size: float, risk_per_trade: float, 
                 max_open_positions: int):
        """
        Initialize risk manager
        
        Args:
            max_position_size: Maximum position size in USDT
            risk_per_trade: Risk per trade as percentage of balance (0.01 = 1%)
            max_open_positions: Maximum number of concurrent positions
        """
        self.max_position_size = max_position_size
        self.risk_per_trade = risk_per_trade
        self.max_open_positions = max_open_positions
        self.logger = Logger.get_logger()
        
        # Drawdown tracking for protection
        self.peak_balance = 0.0
        self.current_drawdown = 0.0
        self.drawdown_threshold = 0.15  # Reduce risk at 15% drawdown
        
        # Performance streak tracking for adaptive leverage
        self.win_streak = 0
        self.loss_streak = 0
        self.recent_trades = []  # Last 10 trades for rolling performance
        self.max_recent_trades = 10
        
        # Performance metrics for Kelly Criterion
        self.total_trades = 0
        self.wins = 0
        self.losses = 0
        self.total_profit = 0.0  # Sum of all winning trades
        self.total_loss = 0.0    # Sum of all losing trades (as positive)
        
        # Correlation tracking for portfolio diversification
        self.correlation_groups = {
            'major_coins': ['BTC', 'ETH'],
            'defi': ['UNI', 'AAVE', 'SUSHI', 'LINK'],
            'layer1': ['SOL', 'AVAX', 'DOT', 'NEAR', 'ATOM'],
            'layer2': ['MATIC', 'OP', 'ARB'],
            'meme': ['DOGE', 'SHIB', 'PEPE'],
            'exchange': ['BNB', 'OKB', 'FTT']
        }
    
    def record_trade_outcome(self, pnl: float):
        """
        Record trade outcome to track win/loss streaks and performance metrics
        
        Args:
            pnl: Profit/loss percentage (positive for win, negative for loss)
        """
        is_win = pnl > 0.005  # Consider >0.5% as win
        is_loss = pnl < -0.005  # Consider <-0.5% as loss
        
        # Track total trades
        self.total_trades += 1
        
        # Update streaks
        if is_win:
            self.win_streak += 1
            self.loss_streak = 0
            self.wins += 1
            self.total_profit += pnl
        elif is_loss:
            self.loss_streak += 1
            self.win_streak = 0
            self.losses += 1
            self.total_loss += abs(pnl)
        else:
            # Breakeven trade - reset streaks but don't count in wins/losses
            self.win_streak = 0
            self.loss_streak = 0
        
        # Track recent trades (rolling window)
        self.recent_trades.append(pnl)
        if len(self.recent_trades) > self.max_recent_trades:
            self.recent_trades.pop(0)
    
    def get_win_rate(self) -> float:
        """Calculate overall win rate"""
        if self.total_trades == 0:
            return 0.5
        counted_trades = self.wins + self.losses
        if counted_trades == 0:
            return 0.5
        return self.wins / counted_trades
    
    def get_avg_win(self) -> float:
        """Calculate average win percentage"""
        if self.wins == 0:
            return 0.0
        return self.total_profit / self.wins
    
    def get_avg_loss(self) -> float:
        """Calculate average loss percentage (as positive number)"""
        if self.losses == 0:
            return 0.0
        return self.total_loss / self.losses
    
    def get_recent_win_rate(self) -> float:
        """Calculate win rate from recent trades"""
        if not self.recent_trades:
            return 0.5
        
        wins = sum(1 for pnl in self.recent_trades if pnl > 0)
        return wins / len(self.recent_trades)
    
    def get_portfolio_heat(self, open_positions: List) -> float:
        """
        Calculate portfolio heat (total risk exposure)
        
        Args:
            open_positions: List of open Position objects
        
        Returns:
            Portfolio heat as percentage of total capital at risk
        """
        if not open_positions:
            return 0.0
        
        total_risk = 0.0
        for pos in open_positions:
            # Risk per position = distance to stop loss * position value
            if pos.side == 'long':
                risk_distance = (pos.entry_price - pos.stop_loss) / pos.entry_price
            else:
                risk_distance = (pos.stop_loss - pos.entry_price) / pos.entry_price
            
            position_value = pos.amount * pos.entry_price
            position_risk = position_value * abs(risk_distance)
            total_risk += position_risk
        
        return total_risk
    
    def check_correlation_risk(self, symbol: str, open_positions: List) -> Tuple[bool, str]:
        """
        Check if adding this symbol would create too much correlation risk
        
        Args:
            symbol: Symbol to check (e.g., 'BTC/USDT:USDT')
            open_positions: List of open Position objects
        
        Returns:
            Tuple of (is_safe, reason)
        """
        # Extract base asset from symbol
        base_asset = symbol.split('/')[0].replace('USDT', '').replace('USD', '')
        
        # Find which group this asset belongs to
        asset_group = None
        for group, assets in self.correlation_groups.items():
            if any(a in base_asset for a in assets):
                asset_group = group
                break
        
        if not asset_group:
            # Unknown asset, allow but with caution
            return True, "unknown_group"
        
        # Count positions in same group
        same_group_count = 0
        for pos in open_positions:
            pos_base = pos.symbol.split('/')[0].replace('USDT', '').replace('USD', '')
            for asset in self.correlation_groups.get(asset_group, []):
                if asset in pos_base:
                    same_group_count += 1
                    break
        
        # Allow max 2 positions from same correlation group
        if same_group_count >= 2:
            return False, f"too_many_in_{asset_group}_group"
        
        return True, "ok"
    
    def adjust_risk_for_conditions(self, base_risk: float, market_volatility: float = 0.03,
                                   win_rate: float = 0.5) -> float:
        """
        Dynamically adjust risk based on market conditions and performance
        
        Args:
            base_risk: Base risk percentage (e.g., 0.02 for 2%)
            market_volatility: Current market volatility (e.g., ATR or BB width)
            win_rate: Recent win rate (0 to 1)
        
        Returns:
            Adjusted risk percentage
        """
        adjusted_risk = base_risk
        
        # 1. Adjust for win/loss streaks
        if self.win_streak >= 3:
            # On a hot streak - increase risk slightly
            adjusted_risk *= 1.2
            self.logger.debug(f"Win streak adjustment: +20% (streak: {self.win_streak})")
        elif self.loss_streak >= 3:
            # On a cold streak - reduce risk significantly
            adjusted_risk *= 0.5
            self.logger.debug(f"Loss streak adjustment: -50% (streak: {self.loss_streak})")
        
        # 2. Adjust for recent performance
        if win_rate > 0.65:
            # High win rate - can afford slightly more risk
            adjusted_risk *= 1.15
            self.logger.debug(f"Win rate adjustment: +15% (rate: {win_rate:.1%})")
        elif win_rate < 0.35:
            # Low win rate - reduce risk
            adjusted_risk *= 0.7
            self.logger.debug(f"Win rate adjustment: -30% (rate: {win_rate:.1%})")
        
        # 3. Adjust for market volatility
        if market_volatility > 0.06:
            # High volatility - reduce risk
            adjusted_risk *= 0.75
            self.logger.debug(f"Volatility adjustment: -25% (vol: {market_volatility:.1%})")
        elif market_volatility < 0.02:
            # Low volatility - can take slightly more risk
            adjusted_risk *= 1.1
            self.logger.debug(f"Volatility adjustment: +10% (vol: {market_volatility:.1%})")
        
        # 4. Adjust for drawdown
        if self.current_drawdown > 0.20:
            # Severe drawdown - cut risk in half
            adjusted_risk *= 0.5
            self.logger.warning(f"Drawdown protection: -50% (DD: {self.current_drawdown:.1%})")
        elif self.current_drawdown > 0.15:
            # Moderate drawdown - reduce risk
            adjusted_risk *= 0.75
            self.logger.info(f"Drawdown protection: -25% (DD: {self.current_drawdown:.1%})")
        
        # Cap adjusted risk at reasonable bounds (0.5% to 4%)
        adjusted_risk = max(0.005, min(adjusted_risk, 0.04))
        
        if adjusted_risk != base_risk:
            self.logger.info(f"Risk adjusted: {base_risk:.2%} → {adjusted_risk:.2%}")
        
        return adjusted_risk
    
    def analyze_order_book_imbalance(self, orderbook: Dict) -> Dict:
        """
        Analyze order book for bid/ask imbalance to optimize entry timing
        
        Args:
            orderbook: Dict with 'bids' and 'asks' arrays
        
        Returns:
            Dict with imbalance metrics
        """
        if not orderbook or 'bids' not in orderbook or 'asks' not in orderbook:
            return {'imbalance': 0.0, 'signal': 'neutral', 'confidence': 0.0}
        
        try:
            bids = orderbook['bids'][:20]  # Top 20 bids
            asks = orderbook['asks'][:20]  # Top 20 asks
            
            if not bids or not asks:
                return {'imbalance': 0.0, 'signal': 'neutral', 'confidence': 0.0}
            
            # Calculate total bid and ask volume
            bid_volume = sum(float(bid[1]) for bid in bids)
            ask_volume = sum(float(ask[1]) for ask in asks)
            
            total_volume = bid_volume + ask_volume
            if total_volume == 0:
                return {'imbalance': 0.0, 'signal': 'neutral', 'confidence': 0.0}
            
            # Calculate imbalance (-1 to 1, positive = more bids)
            imbalance = (bid_volume - ask_volume) / total_volume
            
            # Calculate spread
            best_bid = float(bids[0][0])
            best_ask = float(asks[0][0])
            
            # BUG FIX: Prevent division by zero if best_bid is 0
            if best_bid == 0:
                return {'imbalance': 0.0, 'signal': 'neutral', 'confidence': 0.0}
            
            spread_pct = (best_ask - best_bid) / best_bid
            
            # Determine signal strength
            signal = 'neutral'
            confidence = abs(imbalance)
            
            if imbalance > 0.15:  # Strong buy pressure
                signal = 'bullish'
            elif imbalance < -0.15:  # Strong sell pressure
                signal = 'bearish'
            elif abs(imbalance) < 0.05:  # Balanced
                signal = 'neutral'
            
            # Tight spread indicates good liquidity
            liquidity_score = 1.0 if spread_pct < 0.001 else 0.5
            
            return {
                'imbalance': imbalance,
                'signal': signal,
                'confidence': confidence,
                'spread_pct': spread_pct,
                'liquidity_score': liquidity_score,
                'bid_volume': bid_volume,
                'ask_volume': ask_volume
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing order book: {e}")
            return {'imbalance': 0.0, 'signal': 'neutral', 'confidence': 0.0}
    
    def calculate_position_size(self, balance: float, entry_price: float, 
                               stop_loss_price: float, leverage: int, 
                               risk_per_trade: float = None, kelly_fraction: float = None) -> float:
        """
        Calculate safe position size based on risk management with optional Kelly Criterion
        
        Args:
            balance: Account balance in USDT
            entry_price: Entry price for the trade
            stop_loss_price: Stop loss price
            leverage: Leverage to use
            risk_per_trade: Optional override for risk per trade
            kelly_fraction: Optional Kelly Criterion fraction for optimal sizing
        
        Returns:
            Position size in contracts
        """
        # Use Kelly Criterion if provided and valid, otherwise use standard risk
        if kelly_fraction is not None and kelly_fraction > 0:
            # Kelly suggests optimal fraction of capital to risk
            # Apply it as risk per trade with safety bounds
            risk = min(kelly_fraction, self.risk_per_trade * 1.5)  # Cap at 1.5x standard risk
            self.logger.debug(f"Using Kelly-optimized risk: {risk:.2%} (Kelly: {kelly_fraction:.2%})")
        else:
            # Use provided risk or default
            risk = risk_per_trade if risk_per_trade is not None else self.risk_per_trade
        
        # Calculate risk amount
        risk_amount = balance * risk
        
        # Calculate price distance to stop loss
        price_distance = abs(entry_price - stop_loss_price) / entry_price
        
        # Calculate position size based on risk
        # Risk = Position_Value * Price_Distance (leverage doesn't affect risk calculation)
        # Position_Value = Risk / Price_Distance
        if price_distance > 0:
            position_value = risk_amount / price_distance
        else:
            position_value = self.max_position_size
        
        # Cap at maximum position size
        position_value = min(position_value, self.max_position_size)
        
        # Convert to contracts
        position_size = position_value / entry_price
        
        self.logger.debug(
            f"Calculated position size: {position_size:.4f} contracts "
            f"(${position_value:.2f} value) for risk ${risk_amount:.2f} ({risk:.2%})"
        )
        
        return position_size
    
    def should_open_position(self, current_positions: int, balance: float, 
                            min_balance: float = 1) -> tuple[bool, str]:
        """
        Check if a new position should be opened
        
        Returns:
            Tuple of (should_open, reason)
        """
        # Check if we have too many open positions
        if current_positions >= self.max_open_positions:
            self.logger.debug(
                f"Cannot open position: max positions reached "
                f"({current_positions}/{self.max_open_positions})"
            )
            return False, f"Maximum positions reached ({self.max_open_positions})"
        
        # Check if we have sufficient balance
        if balance < min_balance:
            self.logger.debug(f"Cannot open position: insufficient balance ${balance:.2f} < ${min_balance}")
            return False, f"Insufficient balance (${balance:.2f} < ${min_balance})"
        
        self.logger.debug(
            f"Position check passed: {current_positions}/{self.max_open_positions} positions, "
            f"balance ${balance:.2f}"
        )
        return True, "OK"
    
    def validate_trade(self, symbol: str, signal: str, confidence: float, 
                      min_confidence: float = 0.6) -> tuple[bool, str]:
        """
        Validate if a trade should be executed
        
        Returns:
            Tuple of (is_valid, reason)
        """
        # Check confidence threshold
        if confidence < min_confidence:
            self.logger.debug(
                f"Trade validation failed for {symbol}: "
                f"confidence {confidence:.2f} < threshold {min_confidence:.2f}"
            )
            return False, f"Confidence too low ({confidence:.2f} < {min_confidence})"
        
        # Additional validation can be added here
        # e.g., check for recent losses, market conditions, etc.
        
        self.logger.debug(f"Trade validation passed for {symbol}: confidence {confidence:.2f} >= {min_confidence:.2f}")
        return True, "OK"
    
    def calculate_stop_loss_percentage(self, volatility: float) -> float:
        """
        Calculate stop loss percentage based on market volatility
        
        Args:
            volatility: ATR or other volatility measure
        
        Returns:
            Stop loss percentage (e.g., 0.05 for 5%)
        """
        # Base stop loss
        base_stop = 0.025  # 2.5%
        
        # Adjust based on volatility (adaptive approach)
        # Higher volatility = wider stop loss to avoid premature stops
        if volatility < 0.02:
            # Low volatility - tighter stops
            volatility_adjustment = volatility * 1.5
        elif volatility < 0.05:
            # Medium volatility - standard adjustment
            volatility_adjustment = volatility * 2.0
        else:
            # High volatility - wider stops but capped
            volatility_adjustment = min(volatility * 2.5, 0.06)
        
        stop_loss = base_stop + volatility_adjustment
        
        # Cap between 1.5% and 8%
        stop_loss = max(0.015, min(stop_loss, 0.08))
        
        return stop_loss
    
    def get_max_leverage(self, volatility: float, confidence: float, 
                        momentum: float = 0.0, trend_strength: float = 0.5,
                        market_regime: str = 'neutral') -> int:
        """
        Calculate maximum safe leverage based on multiple market conditions and performance
        
        Args:
            volatility: Market volatility measure (ATR or BB width)
            confidence: Signal confidence (0-1)
            momentum: Current price momentum (-1 to 1)
            trend_strength: Trend strength indicator (0-1)
            market_regime: Market regime ('trending', 'ranging', 'neutral')
        
        Returns:
            Maximum leverage to use (3-20x)
        """
        # 1. Enhanced base leverage from volatility regime classification
        if volatility > 0.10:
            base_leverage = 3  # Extreme volatility - minimal leverage
            volatility_regime = 'extreme'
        elif volatility > 0.08:
            base_leverage = 4  # Very high volatility
            volatility_regime = 'very_high'
        elif volatility > 0.05:
            base_leverage = 6  # High volatility
            volatility_regime = 'high'
        elif volatility > 0.03:
            base_leverage = 8  # Medium volatility
            volatility_regime = 'medium'
        elif volatility > 0.02:
            base_leverage = 11  # Normal volatility
            volatility_regime = 'normal'
        elif volatility > 0.01:
            base_leverage = 14  # Low volatility
            volatility_regime = 'low'
        else:
            base_leverage = 16  # Very low volatility
            volatility_regime = 'very_low'
        
        # 2. Enhanced confidence adjustment (±4x instead of ±3x)
        if confidence >= 0.85:
            # Exceptionally high confidence
            confidence_adj = 4
        elif confidence >= 0.80:
            # Very high confidence
            confidence_adj = 3
        elif confidence >= 0.75:
            # High confidence
            confidence_adj = 2
        elif confidence >= 0.65:
            # Good confidence
            confidence_adj = 1
        elif confidence >= 0.55:
            # Acceptable confidence
            confidence_adj = 0
        else:
            # Lower confidence - reduce leverage more aggressively
            confidence_adj = -3
        
        # 3. Momentum adjustment (±2x)
        momentum_adj = 0
        if abs(momentum) > 0.03:  # Strong momentum
            momentum_adj = 2
        elif abs(momentum) > 0.02:  # Good momentum
            momentum_adj = 1
        elif abs(momentum) < 0.005:  # Weak momentum
            momentum_adj = -1
        
        # 4. Trend strength adjustment (±2x)
        trend_adj = 0
        if trend_strength > 0.7:  # Strong trend
            trend_adj = 2
        elif trend_strength > 0.5:  # Moderate trend
            trend_adj = 1
        elif trend_strength < 0.3:  # Weak/no trend
            trend_adj = -1
        
        # 5. Enhanced market regime adjustment (±3x instead of ±2x)
        regime_adj = 0
        if market_regime == 'trending':
            regime_adj = 3  # Can be more aggressive in trends
        elif market_regime == 'ranging':
            regime_adj = -2  # More conservative in ranges
        
        # 6. Performance streak adjustment (±3x)
        streak_adj = 0
        if self.win_streak >= 5:
            # Hot streak - can be slightly more aggressive
            streak_adj = 2
        elif self.win_streak >= 3:
            streak_adj = 1
        elif self.loss_streak >= 4:
            # Cold streak - reduce leverage significantly
            streak_adj = -3
        elif self.loss_streak >= 2:
            streak_adj = -2
        
        # 7. Enhanced recent performance adjustment (±3x instead of ±2x)
        recent_adj = 0
        recent_win_rate = self.get_recent_win_rate()
        if len(self.recent_trades) >= 5:  # Need minimum data
            if recent_win_rate >= 0.75:
                recent_adj = 3  # Excellent recent performance
            elif recent_win_rate >= 0.70:
                recent_adj = 2
            elif recent_win_rate >= 0.60:
                recent_adj = 1  # Good recent performance
            elif recent_win_rate <= 0.30:
                recent_adj = -3  # Poor recent performance
            elif recent_win_rate <= 0.40:
                recent_adj = -2  # Below average performance
        
        # 8. Drawdown adjustment (overrides other factors)
        drawdown_adj = 0
        if self.current_drawdown > 0.20:
            drawdown_adj = -10  # Severe drawdown protection - override most factors
        elif self.current_drawdown > 0.15:
            drawdown_adj = -6  # Moderate drawdown protection
        elif self.current_drawdown > 0.10:
            drawdown_adj = -3  # Light drawdown protection
        
        # Calculate final leverage with improved bounds management
        # Cap individual adjustment categories to prevent runaway negative leverage
        total_adj = confidence_adj + momentum_adj + trend_adj + regime_adj + streak_adj + recent_adj
        
        # Apply drawdown adjustment separately (it's intentionally strong)
        # but ensure combined adjustments don't exceed reasonable bounds
        if drawdown_adj < -10:
            # Severe drawdown - limit other adjustments' impact
            total_adj = max(total_adj, -5)  # Cap other negative adjustments
        
        final_leverage = base_leverage + total_adj + drawdown_adj
        
        # Apply hard limits (3x minimum, 20x maximum)
        final_leverage = max(3, min(final_leverage, 20))
        
        # Log reasoning for transparency (only when adjustments are significant)
        if abs(confidence_adj) > 1 or abs(streak_adj) > 1 or abs(drawdown_adj) > 0:
            self.logger.debug(
                f"Leverage calculation: base={base_leverage}x ({volatility_regime} vol), "
                f"conf={confidence_adj:+d}, mom={momentum_adj:+d}, trend={trend_adj:+d}, "
                f"regime={regime_adj:+d}, streak={streak_adj:+d}, recent={recent_adj:+d}, "
                f"drawdown={drawdown_adj:+d} → {final_leverage}x"
            )
        
        return final_leverage
    
    def get_symbol_group(self, symbol: str) -> str:
        """
        Identify which correlation group a symbol belongs to
        
        Returns:
            Group name or 'other'
        """
        # Extract base currency from symbol (e.g., 'BTC/USDT:USDT' -> 'BTC')
        base = symbol.split('/')[0] if '/' in symbol else symbol.split('-')[0]
        
        for group_name, coins in self.correlation_groups.items():
            if base in coins:
                return group_name
        
        return 'other'
    
    def check_portfolio_diversification(self, new_symbol: str, 
                                       open_positions: List[str]) -> Tuple[bool, str]:
        """
        Check if adding a new position would over-concentrate portfolio
        
        Args:
            new_symbol: Symbol to potentially add
            open_positions: List of currently open position symbols
        
        Returns:
            Tuple of (is_diversified, reason)
        """
        if not open_positions:
            self.logger.debug(f"Diversification check passed for {new_symbol}: no existing positions")
            return True, "No existing positions"
        
        new_group = self.get_symbol_group(new_symbol)
        
        # Count positions in each group
        group_counts = {}
        for pos_symbol in open_positions:
            group = self.get_symbol_group(pos_symbol)
            group_counts[group] = group_counts.get(group, 0) + 1
        
        # Check if new position would over-concentrate
        current_count = group_counts.get(new_group, 0)
        total_positions = len(open_positions)
        
        # Maximum concentration depends on group type
        # 'other' group gets higher limit (70%) since assets are uncorrelated
        # Correlated groups get 40% limit
        if new_group == 'other':
            max_group_concentration = max(2, int(self.max_open_positions * 0.7))
        else:
            max_group_concentration = max(2, int(self.max_open_positions * 0.4))
        
        if current_count >= max_group_concentration:
            self.logger.debug(
                f"Diversification check failed for {new_symbol}: "
                f"too many positions in {new_group} group ({current_count}/{max_group_concentration})"
            )
            return False, f"Too many positions in {new_group} group ({current_count}/{max_group_concentration})"
        
        # Don't allow exact duplicate symbols
        if new_symbol in open_positions:
            self.logger.debug(f"Diversification check failed: already have position in {new_symbol}")
            return False, f"Already have position in {new_symbol}"
        
        self.logger.debug(
            f"Diversification check passed for {new_symbol}: "
            f"{new_group} group has {current_count}/{max_group_concentration} positions"
        )
        return True, "Portfolio diversification OK"
    
    def calculate_kelly_criterion(self, win_rate: float, avg_win: float, 
                                  avg_loss: float, use_fractional: bool = True) -> float:
        """
        Calculate optimal position size using Kelly Criterion with enhanced adaptive fractional adjustment
        
        Args:
            win_rate: Historical win rate (0-1)
            avg_win: Average win percentage
            avg_loss: Average loss percentage (positive number)
            use_fractional: Whether to use adaptive fractional Kelly (default: True)
        
        Returns:
            Optimal fraction of capital to risk (0-1)
        """
        if win_rate <= 0 or avg_win <= 0 or avg_loss <= 0:
            return self.risk_per_trade  # Use default if no history
        
        # Kelly formula: f = (bp - q) / b
        # where b = ratio of win to loss, p = win prob, q = loss prob
        b = avg_win / avg_loss
        p = win_rate
        q = 1 - win_rate
        
        kelly_fraction = (b * p - q) / b
        
        # Enhanced adaptive fractional Kelly based on performance confidence
        if use_fractional:
            # Start with half-Kelly as baseline (0.5)
            fraction = 0.5
            
            # Adjust fraction based on recent performance stability
            if len(self.recent_trades) >= 5:
                recent_win_rate = self.get_recent_win_rate()
                
                # If recent performance matches historical, can be more aggressive
                performance_consistency = 1.0 - abs(recent_win_rate - win_rate)
                
                if performance_consistency > 0.90:
                    # Exceptional consistency - can use 65% Kelly
                    fraction = 0.65
                elif performance_consistency > 0.85:
                    # Very consistent performance - can use 60% Kelly
                    fraction = 0.6
                elif performance_consistency > 0.70:
                    # Good consistency - use 55% Kelly
                    fraction = 0.55
                elif performance_consistency < 0.50:
                    # Inconsistent performance - more conservative (35% Kelly)
                    fraction = 0.35
                elif performance_consistency < 0.60:
                    # Below average consistency - 45% Kelly
                    fraction = 0.45
            
            # Additional adjustment for win rate quality
            if win_rate >= 0.65:
                # High win rate - can be slightly more aggressive
                fraction = min(fraction * 1.1, 0.7)  # Max 10% increase, capped at 70%
            elif win_rate <= 0.45:
                # Low win rate - be more conservative
                fraction = max(fraction * 0.85, 0.3)  # 15% reduction, min 30%
            
            # Further reduce during losing streaks
            if self.loss_streak >= 3:
                fraction *= 0.65  # 35% reduction during 3+ loss streak (was 30%)
            elif self.loss_streak >= 2:
                fraction *= 0.85  # 15% reduction during 2+ loss streak
            
            # Can increase slightly during win streaks (but capped more conservatively)
            if self.win_streak >= 5:
                fraction = min(fraction * 1.15, 0.7)  # Max 15% increase, capped at 70%
            elif self.win_streak >= 3:
                fraction = min(fraction * 1.08, 0.7)  # Max 8% increase
            
            conservative_kelly = kelly_fraction * fraction
        else:
            # Standard half-Kelly
            conservative_kelly = kelly_fraction * 0.5
        
        # Enhanced cap with better bounds: between 0.5% and 3.5% of portfolio
        optimal_risk = max(0.005, min(conservative_kelly, 0.035))
        
        return optimal_risk
    
    def calculate_var(self, returns: List[float], confidence_level: float = 0.95) -> float:
        """
        Calculate Value at Risk (VaR) at specified confidence level
        
        Args:
            returns: List of historical returns
            confidence_level: Confidence level (default 95%)
        
        Returns:
            VaR value (maximum expected loss at confidence level)
        """
        if not returns or len(returns) < 10:
            return 0.0
        
        try:
            # Sort returns in ascending order
            sorted_returns = sorted(returns)
            
            # Calculate VaR at the specified percentile
            index = int((1 - confidence_level) * len(sorted_returns))
            var = abs(sorted_returns[index])
            
            return var
        except Exception as e:
            self.logger.error(f"Error calculating VaR: {e}")
            return 0.0
    
    def calculate_cvar(self, returns: List[float], confidence_level: float = 0.95) -> float:
        """
        Calculate Conditional Value at Risk (CVaR/Expected Shortfall)
        Average loss beyond VaR threshold
        
        Args:
            returns: List of historical returns
            confidence_level: Confidence level (default 95%)
        
        Returns:
            CVaR value (average loss beyond VaR)
        """
        if not returns or len(returns) < 10:
            return 0.0
        
        try:
            # Sort returns in ascending order
            sorted_returns = sorted(returns)
            
            # Calculate cutoff index for VaR
            var_index = int((1 - confidence_level) * len(sorted_returns))
            
            # CVaR is the average of all losses beyond VaR
            tail_losses = sorted_returns[:var_index + 1]
            cvar = abs(np.mean(tail_losses)) if tail_losses else 0.0
            
            return cvar
        except Exception as e:
            self.logger.error(f"Error calculating CVaR: {e}")
            return 0.0
    
    def get_risk_metrics(self, returns: List[float]) -> Dict:
        """
        Calculate comprehensive risk metrics including VaR and CVaR
        
        Args:
            returns: List of historical returns
        
        Returns:
            Dictionary with risk metrics
        """
        try:
            var_95 = self.calculate_var(returns, 0.95)
            var_99 = self.calculate_var(returns, 0.99)
            cvar_95 = self.calculate_cvar(returns, 0.95)
            cvar_99 = self.calculate_cvar(returns, 0.99)
            
            # Calculate other useful metrics
            avg_return = np.mean(returns) if returns else 0.0
            std_return = np.std(returns) if returns else 0.0
            
            return {
                'var_95': var_95,
                'var_99': var_99,
                'cvar_95': cvar_95,
                'cvar_99': cvar_99,
                'avg_return': avg_return,
                'std_return': std_return,
                'sharpe_estimate': avg_return / std_return if std_return > 0 else 0.0
            }
        except Exception as e:
            self.logger.error(f"Error calculating risk metrics: {e}")
            return {}
    
    def detect_market_regime(self, returns: List[float], 
                           volatility: float,
                           trend_strength: float = 0.5) -> str:
        """
        Detect current market regime for regime-based position sizing
        
        Args:
            returns: Recent returns
            volatility: Current volatility measure
            trend_strength: Trend strength indicator (0-1)
        
        Returns:
            Market regime: 'bull_trending', 'bear_trending', 'high_volatility', 
                          'low_volatility', 'ranging', 'neutral'
        """
        try:
            if not returns or len(returns) < 5:
                return 'neutral'
            
            # Calculate metrics - handle both list and numpy array inputs
            if isinstance(returns, np.ndarray):
                returns_list = returns.tolist()
            else:
                returns_list = returns
            
            avg_return = np.mean(returns_list[-10:]) if len(returns_list) >= 10 else np.mean(returns_list)
            recent_vol = np.std(returns_list[-10:]) if len(returns_list) >= 10 else np.std(returns_list)
            
            # Regime classification
            if volatility > 0.06:
                return 'high_volatility'
            elif volatility < 0.015:
                return 'low_volatility'
            elif avg_return > 0.02 and trend_strength > 0.6:
                return 'bull_trending'
            elif avg_return < -0.02 and trend_strength > 0.6:
                return 'bear_trending'
            elif abs(avg_return) < 0.01 and trend_strength < 0.4:
                return 'ranging'
            else:
                return 'neutral'
                
        except Exception as e:
            self.logger.error(f"Error detecting market regime: {e}")
            return 'neutral'
    
    def regime_based_position_sizing(self, base_size: float, regime: str, 
                                    confidence: float) -> float:
        """
        Adjust position size based on market regime
        
        Args:
            base_size: Base position size
            regime: Detected market regime
            confidence: Signal confidence
        
        Returns:
            Adjusted position size
        """
        try:
            # Regime-based multipliers
            regime_multipliers = {
                'bull_trending': 1.3,      # More aggressive in bull trends
                'bear_trending': 0.6,      # Very conservative in bear trends
                'high_volatility': 0.5,    # Reduce size in high volatility
                'low_volatility': 1.2,     # Can be more aggressive in low volatility
                'ranging': 0.8,            # Slightly conservative in ranging markets
                'neutral': 1.0             # Standard sizing
            }
            
            multiplier = regime_multipliers.get(regime, 1.0)
            
            # Further adjust based on confidence
            if confidence > 0.8:
                multiplier *= 1.1
            elif confidence < 0.6:
                multiplier *= 0.85
            
            adjusted_size = base_size * multiplier
            
            self.logger.debug(
                f"Regime-based sizing: {regime} regime, "
                f"multiplier={multiplier:.2f}, "
                f"size: {base_size:.4f} → {adjusted_size:.4f}"
            )
            
            return adjusted_size
            
        except Exception as e:
            self.logger.error(f"Error in regime-based sizing: {e}")
            return base_size
    
    def update_drawdown(self, current_balance: float) -> float:
        """
        Update drawdown tracking and return risk adjustment factor
        
        Args:
            current_balance: Current account balance
            
        Returns:
            Risk adjustment factor (0.5-1.0) based on drawdown
        """
        # Track peak balance
        if current_balance > self.peak_balance:
            self.peak_balance = current_balance
        
        # Calculate current drawdown
        if self.peak_balance > 0:
            self.current_drawdown = (self.peak_balance - current_balance) / self.peak_balance
        else:
            self.current_drawdown = 0.0
        
        # Adjust risk based on drawdown
        if self.current_drawdown > 0.20:  # >20% drawdown - aggressive protection
            risk_adjustment = 0.5
            self.logger.warning(f"⚠️  High drawdown detected: {self.current_drawdown:.1%} - Reducing risk to 50%")
        elif self.current_drawdown > self.drawdown_threshold:  # >15% drawdown
            risk_adjustment = 0.75
            self.logger.info(f"📉 Moderate drawdown: {self.current_drawdown:.1%} - Reducing risk to 75%")
        else:
            risk_adjustment = 1.0
        
        return risk_adjustment
