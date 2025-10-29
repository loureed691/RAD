"""
Risk management system for the trading bot
"""
from typing import Dict, List, Tuple
from logger import Logger
import joblib
import os
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
        self.state_path = 'models/risk_manager_state.pkl'
        
        # Drawdown tracking for protection
        self.peak_balance = 0.0
        self.current_drawdown = 0.0
        self.drawdown_threshold = 0.15  # Reduce risk at 15% drawdown
        self.last_drawdown_warning_level = 0.0  # Track when we last warned about drawdown
        self.drawdown_warning_threshold = 0.10  # Only warn when drawdown increases by 10%
        
        # PROFITABILITY FIX: Daily loss limit to prevent catastrophic losses
        self.daily_loss_limit = 0.10  # Stop trading if lose 10% in a day
        self.daily_start_balance = 0.0
        self.daily_loss = 0.0
        from datetime import date
        self.trading_date = date.today()
        
        # PRIORITY 1 SAFETY: Hard guardrails
        self.kill_switch_active = False  # Global kill switch - halts new entries, allows exits
        self.max_risk_per_trade_pct = 0.05  # Max 5% of equity per trade
        self.kill_switch_reason = ""  # Reason for kill switch activation
        
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
        
        # Load existing state if available
        self.load_state()
    
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
            
            # CRITICAL FIX: Track daily loss for daily loss limit protection
            # Only count losses toward daily loss tracking
            self.daily_loss += abs(pnl)
            if self.daily_loss >= self.daily_loss_limit:
                self.logger.warning(
                    f"⚠️ Daily loss limit reached or exceeded: {self.daily_loss:.2%} / {self.daily_loss_limit:.2%}"
                )
        else:
            # Breakeven trade - reset streaks but don't count in wins/losses
            self.win_streak = 0
            self.loss_streak = 0
        
        # Track recent trades (rolling window)
        self.recent_trades.append(pnl)
        # MEMORY: Keep only last N trades (more efficient than pop(0))
        if len(self.recent_trades) > self.max_recent_trades:
            self.recent_trades = self.recent_trades[-self.max_recent_trades:]
    
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
    
    def calculate_kelly_fraction(self, win_rate: float = None, avg_win: float = None, 
                                 avg_loss: float = None, volatility_adj: float = 1.0) -> float:
        """
        Calculate optimal Kelly Criterion fraction for position sizing
        
        OPTIMIZATION: Uses actual performance metrics with volatility adjustment
        
        Formula: f = (bp - q) / b
        where:
            b = avg_win / avg_loss (payoff ratio)
            p = win_rate (probability of winning)
            q = 1 - p (probability of losing)
            f = optimal fraction to risk
        
        Args:
            win_rate: Override win rate (uses tracked if None)
            avg_win: Override average win (uses tracked if None)
            avg_loss: Override average loss (uses tracked if None)
            volatility_adj: Volatility adjustment factor (higher = more conservative)
        
        Returns:
            Kelly fraction (typically 0.005 to 0.03 for half-Kelly with caps)
        """
        # Use provided values or fall back to tracked metrics
        p = win_rate if win_rate is not None else self.get_win_rate()
        win = avg_win if avg_win is not None else self.get_avg_win()
        loss = avg_loss if avg_loss is not None else self.get_avg_loss()
        
        # Need minimum data for reliable Kelly
        if self.total_trades < 10:
            return self.risk_per_trade  # Use default until enough data
        
        # If insufficient loss data, estimate conservatively
        if loss == 0:
            if win > 0:
                loss = win * 0.6  # Conservative estimate: losses are 60% of wins
            else:
                return self.risk_per_trade  # Not enough data
        
        # Calculate payoff ratio (b)
        b = win / loss if loss > 0 else 1.5
        
        # Calculate Kelly fraction: f = (bp - q) / b
        q = 1 - p
        f = (b * p - q) / b if b > 0 else 0
        
        # OPTIMIZATION: Apply half-Kelly for safety (reduces risk of ruin)
        f = f * 0.5
        
        # OPTIMIZATION: Adjust for market volatility
        # Higher volatility = reduce Kelly fraction
        f = f / volatility_adj
        
        # OPTIMIZATION: Cap at reasonable bounds (0.5% to 3%)
        # This prevents over-betting even with good historical performance
        f = max(0.005, min(f, 0.03))
        
        # OPTIMIZATION: If Kelly suggests less than default risk, use Kelly
        # If Kelly suggests more, use Kelly but with caution
        if f < self.risk_per_trade:
            return f  # Kelly is more conservative, use it
        elif f > self.risk_per_trade * 1.5:
            # Kelly is too aggressive, moderate it
            return self.risk_per_trade * 1.2
        else:
            return f
    
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
        
        PERFORMANCE: Optimized to O(n) by using set membership instead of nested loops
        
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
        
        # PERFORMANCE OPTIMIZATION: Build set of assets in target group for O(1) lookup
        # This replaces the nested loop which was O(n*m) with O(n) complexity
        group_assets_set = set(self.correlation_groups.get(asset_group, []))
        
        # Count positions in same group using optimized set membership check
        same_group_count = 0
        for pos in open_positions:
            pos_base = pos.symbol.split('/')[0].replace('USDT', '').replace('USD', '')
            # Check if any group asset is in position base (more efficient check)
            if any(asset in pos_base for asset in group_assets_set):
                same_group_count += 1
        
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
        # Validate balance first
        if balance <= 0:
            self.logger.error(f"Invalid balance: {balance}. Cannot calculate position size.")
            return 0.0
        
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
        
        # Validate entry_price to prevent division by zero
        if entry_price <= 0:
            self.logger.error(f"Invalid entry_price: {entry_price}. Cannot calculate position size.")
            return 0.0
        
        # Validate stop_loss_price
        if stop_loss_price <= 0:
            self.logger.error(f"Invalid stop_loss_price: {stop_loss_price}. Cannot calculate position size.")
            return 0.0
        
        # Ensure stop loss is different from entry price
        if abs(entry_price - stop_loss_price) < 0.0001:  # Essentially the same price
            self.logger.error(f"Stop loss price ({stop_loss_price}) is too close to entry price ({entry_price})")
            return 0.0
        
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
        
        # Convert to contracts (entry_price already validated above)
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
        # PROFITABILITY FIX: Check daily loss limit first
        if self.daily_loss >= self.daily_loss_limit:
            self.logger.warning(f"Daily loss limit reached: {self.daily_loss:.2%} >= {self.daily_loss_limit:.2%}")
            return False, f"Daily loss limit reached ({self.daily_loss:.1%}). Stop trading for today."
        
        # Check if we have too many open positions
        if current_positions >= self.max_open_positions:
            return False, f"Maximum positions reached ({self.max_open_positions})"
        
        # Check if we have sufficient balance
        if balance < min_balance:
            return False, f"Insufficient balance (${balance:.2f} < ${min_balance})"
        
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
            return False, f"Confidence too low ({confidence:.2f} < {min_confidence})"
        
        # Additional validation can be added here
        # e.g., check for recent losses, market conditions, etc.
        
        return True, "OK"
    
    def calculate_stop_loss_percentage(self, volatility: float) -> float:
        """
        Calculate stop loss percentage based on market volatility
        
        Args:
            volatility: ATR or other volatility measure
        
        Returns:
            Stop loss percentage (e.g., 0.05 for 5%)
        """
        # MONEY LOSS FIX: Tighter base stop loss to prevent excessive losses with leverage
        # With average leverage of 6x, we want max -10% ROI loss on stop = ~1.7% price stop
        # Base stop loss reduced from 1.5% to 1.2% for better protection
        base_stop = 0.012  # 1.2%
        
        # Adjust based on volatility (adaptive approach)
        # Higher volatility = wider stop loss to avoid premature stops
        if volatility < 0.02:
            # Low volatility - tighter stops
            volatility_adjustment = volatility * 1.0  # Reduced multiplier from 1.2
        elif volatility < 0.05:
            # Medium volatility - standard adjustment
            volatility_adjustment = volatility * 1.2  # Reduced from 1.5
        else:
            # High volatility - wider stops but capped
            volatility_adjustment = min(volatility * 1.5, 0.02)  # Reduced cap from 0.03 to 0.02
        
        stop_loss = base_stop + volatility_adjustment
        
        # MONEY LOSS FIX: Tighter caps to prevent excessive losses with leverage
        # Cap between 1.0% and 2.5% (reduced from 1.0%-4.0%)
        # With 6x leverage: 2.5% price stop = -15% ROI (at emergency threshold)
        # This ensures stops trigger BEFORE emergency stops
        stop_loss = max(0.010, min(stop_loss, 0.025))
        
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
            Maximum leverage to use (2-12x, reduced from 3-20x)
        """
        # 1. More conservative base leverage from volatility regime (REDUCED)
        if volatility > 0.10:
            base_leverage = 2  # Extreme volatility - minimal leverage (was 3)
            volatility_regime = 'extreme'
        elif volatility > 0.08:
            base_leverage = 3  # Very high volatility (was 4)
            volatility_regime = 'very_high'
        elif volatility > 0.05:
            base_leverage = 4  # High volatility (was 6)
            volatility_regime = 'high'
        elif volatility > 0.03:
            base_leverage = 6  # Medium volatility (was 8)
            volatility_regime = 'medium'
        elif volatility > 0.02:
            base_leverage = 8  # Normal volatility (was 11)
            volatility_regime = 'normal'
        elif volatility > 0.01:
            base_leverage = 10  # Low volatility (was 14)
            volatility_regime = 'low'
        else:
            base_leverage = 11  # Very low volatility (was 16, max now 12)
            volatility_regime = 'very_low'
        
        # 2. More conservative confidence adjustment (±2x instead of ±4x)
        if confidence >= 0.85:
            # Exceptionally high confidence
            confidence_adj = 2  # (was 4)
        elif confidence >= 0.80:
            # Very high confidence
            confidence_adj = 2  # (was 3)
        elif confidence >= 0.75:
            # High confidence
            confidence_adj = 1  # (was 2)
        elif confidence >= 0.65:
            # Good confidence
            confidence_adj = 1  # (was 1)
        elif confidence >= 0.55:
            # Acceptable confidence
            confidence_adj = 0
        else:
            # Lower confidence - reduce leverage more aggressively
            confidence_adj = -2  # (was -3)
        
        # 3. Momentum adjustment (±1x instead of ±2x)
        momentum_adj = 0
        if abs(momentum) > 0.03:  # Strong momentum
            momentum_adj = 1  # (was 2)
        elif abs(momentum) > 0.02:  # Good momentum
            momentum_adj = 1  # (was 1)
        elif abs(momentum) < 0.005:  # Weak momentum
            momentum_adj = -1
        
        # 4. Trend strength adjustment (±1x instead of ±2x)
        trend_adj = 0
        if trend_strength > 0.7:  # Strong trend
            trend_adj = 1  # (was 2)
        elif trend_strength > 0.5:  # Moderate trend
            trend_adj = 1  # (was 1)
        elif trend_strength < 0.3:  # Weak/no trend
            trend_adj = -1
        
        # 5. More conservative market regime adjustment (±2x instead of ±3x)
        regime_adj = 0
        if market_regime == 'trending':
            regime_adj = 2  # Can be more aggressive in trends (was 3)
        elif market_regime == 'ranging':
            regime_adj = -2  # More conservative in ranges
        
        # 6. More conservative performance streak adjustment (±2x)
        streak_adj = 0
        if self.win_streak >= 5:
            # Hot streak - can be slightly more aggressive
            streak_adj = 1  # (was 2)
        elif self.win_streak >= 3:
            streak_adj = 1
        elif self.loss_streak >= 4:
            # Cold streak - reduce leverage significantly
            streak_adj = -2  # (was -3)
        elif self.loss_streak >= 2:
            streak_adj = -1  # (was -2)
        
        # 7. More conservative recent performance adjustment (±2x instead of ±3x)
        recent_adj = 0
        recent_win_rate = self.get_recent_win_rate()
        if len(self.recent_trades) >= 5:  # Need minimum data
            if recent_win_rate >= 0.75:
                recent_adj = 2  # Excellent recent performance (was 3)
            elif recent_win_rate >= 0.70:
                recent_adj = 1  # (was 2)
            elif recent_win_rate >= 0.60:
                recent_adj = 1  # Good recent performance
            elif recent_win_rate <= 0.30:
                recent_adj = -2  # Poor recent performance (was -3)
            elif recent_win_rate <= 0.40:
                recent_adj = -1  # Below average performance (was -2)
        
        # 8. Drawdown adjustment (overrides other factors) - MORE AGGRESSIVE
        drawdown_adj = 0
        if self.current_drawdown > 0.15:  # Lowered from 0.20
            drawdown_adj = -8  # Severe drawdown protection (was -10 at >0.20)
        elif self.current_drawdown > 0.10:  # Lowered from 0.15
            drawdown_adj = -5  # Moderate drawdown protection (was -6 at >0.15)
        elif self.current_drawdown > 0.05:  # Lowered from 0.10, NEW threshold
            drawdown_adj = -2  # Light drawdown protection (was -3 at >0.10)
        
        # Calculate final leverage with improved bounds management
        # Cap individual adjustment categories to prevent runaway negative leverage
        total_adj = confidence_adj + momentum_adj + trend_adj + regime_adj + streak_adj + recent_adj
        
        # Apply drawdown adjustment separately (it's intentionally strong)
        # but ensure combined adjustments don't exceed reasonable bounds
        if drawdown_adj < -5:  # Changed from -10
            # Severe drawdown - limit other adjustments' impact
            total_adj = max(total_adj, -3)  # Cap other negative adjustments (was -5)
        
        final_leverage = base_leverage + total_adj + drawdown_adj
        
        # Apply hard limits (2x minimum, 12x maximum) - REDUCED from 3-20x
        final_leverage = max(2, min(final_leverage, 12))
        
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
            return False, f"Too many positions in {new_group} group ({current_count}/{max_group_concentration})"
        
        # Don't allow exact duplicate symbols
        if new_symbol in open_positions:
            return False, f"Already have position in {new_symbol}"
        
        return True, "Portfolio diversification OK"
    
    def calculate_kelly_criterion(self, win_rate: float, avg_win: float, 
                                  avg_loss: float, use_fractional: bool = True,
                                  volatility: float = 0.03) -> float:
        """
        Calculate optimal position size using Kelly Criterion with HARD fractional caps (0.25-0.5)
        and volatility targeting to prevent leverage jumps during regime flips
        
        PRIORITY 1 SAFETY: Kelly is capped at 0.25-0.5 to prevent over-leveraging
        
        Args:
            win_rate: Historical win rate (0-1)
            avg_win: Average win percentage
            avg_loss: Average loss percentage (positive number)
            use_fractional: Whether to use adaptive fractional Kelly (default: True)
            volatility: Current market volatility for regime-aware adjustment
        
        Returns:
            Optimal fraction of capital to risk (0-1), HARD CAPPED at 0.25-0.5 Kelly
        """
        if win_rate <= 0 or avg_win <= 0 or avg_loss <= 0:
            return self.risk_per_trade  # Use default if no history
        
        # Kelly formula: f = (bp - q) / b
        # where b = ratio of win to loss, p = win prob, q = loss prob
        b = avg_win / avg_loss
        p = win_rate
        q = 1 - win_rate
        
        kelly_fraction = (b * p - q) / b
        
        # PRIORITY 1: Enforce HARD fractional Kelly cap (0.25-0.5)
        if use_fractional:
            # Start with quarter-Kelly as baseline (0.25) for safety
            fraction = 0.25
            
            # VOLATILITY TARGETING: Adjust for market volatility to prevent leverage jumps
            # Lower fraction in high volatility, allow slightly higher in low volatility
            if volatility > 0.06:
                # High volatility regime - use minimum Kelly (0.25)
                fraction = 0.25
                self.logger.debug(f"High volatility ({volatility:.1%}) - using min Kelly: 0.25")
            elif volatility < 0.02:
                # Low volatility regime - can use up to 0.40 Kelly
                fraction = 0.40
                self.logger.debug(f"Low volatility ({volatility:.1%}) - using Kelly: 0.40")
            else:
                # Medium volatility - use 0.30 Kelly
                fraction = 0.30
                self.logger.debug(f"Medium volatility ({volatility:.1%}) - using Kelly: 0.30")
            
            # Adjust fraction based on recent performance stability (within caps)
            if len(self.recent_trades) >= 5:
                recent_win_rate = self.get_recent_win_rate()
                
                # If recent performance matches historical, can be slightly more aggressive
                performance_consistency = 1.0 - abs(recent_win_rate - win_rate)
                
                if performance_consistency > 0.90 and volatility < 0.04:
                    # Exceptional consistency + low vol - can use up to 0.5 Kelly (HARD CAP)
                    fraction = min(fraction * 1.25, 0.5)
                elif performance_consistency > 0.85:
                    # Very consistent performance - increase slightly
                    fraction = min(fraction * 1.15, 0.45)
                elif performance_consistency < 0.50:
                    # Inconsistent performance - reduce to minimum
                    fraction = 0.25
            
            # HARD REDUCTION during losing streaks (safety first)
            if self.loss_streak >= 3:
                fraction = 0.25  # Drop to minimum on 3+ loss streak
                self.logger.warning(f"Loss streak {self.loss_streak} - reducing to min Kelly: 0.25")
            elif self.loss_streak >= 2:
                fraction = min(fraction * 0.75, 0.35)  # 25% reduction on 2+ loss streak
            
            # Modest increase during win streaks (still capped)
            if self.win_streak >= 5:
                fraction = min(fraction * 1.15, 0.5)  # Max 15% increase, HARD CAP at 0.5
            elif self.win_streak >= 3:
                fraction = min(fraction * 1.08, 0.45)  # Max 8% increase, cap at 0.45
            
            # HARD CAP enforcement: 0.25 <= fraction <= 0.5
            fraction = max(0.25, min(fraction, 0.5))
            
            conservative_kelly = kelly_fraction * fraction
        else:
            # Standard quarter-Kelly (conservative default)
            conservative_kelly = kelly_fraction * 0.25
        
        # PRIORITY 1: HARD BOUNDS - between 0.5% and 2.5% of portfolio
        # This ensures we never risk more than 2.5% even with best Kelly
        optimal_risk = max(0.005, min(conservative_kelly, 0.025))
        
        self.logger.debug(
            f"Kelly calculation: raw={kelly_fraction:.3f}, "
            f"fraction={fraction if use_fractional else 0.25:.2f}, "
            f"final={optimal_risk:.3f} (volatility={volatility:.1%})"
        )
        
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
    
    def _should_log_drawdown_warning(self, current_drawdown: float) -> bool:
        """
        Check if drawdown warning should be logged based on threshold
        
        Args:
            current_drawdown: Current drawdown percentage
            
        Returns:
            True if warning should be logged
        """
        return abs(current_drawdown - self.last_drawdown_warning_level) >= self.drawdown_warning_threshold
    
    def update_drawdown(self, current_balance: float) -> float:
        """
        Update drawdown tracking and return risk adjustment factor
        
        Args:
            current_balance: Current account balance
            
        Returns:
            Risk adjustment factor (0.5-1.0) based on drawdown
        """
        # Initialize daily tracking if not set
        if self.daily_start_balance == 0.0:
            self.daily_start_balance = current_balance
            self.logger.debug(f"Initialized daily start balance: ${current_balance:.2f}")
        
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
            # Only warn if drawdown increased significantly since last warning
            if self._should_log_drawdown_warning(self.current_drawdown):
                self.logger.warning(f"⚠️  High drawdown detected: {self.current_drawdown:.1%} - Reducing risk to 50%")
                self.last_drawdown_warning_level = self.current_drawdown
        elif self.current_drawdown > self.drawdown_threshold:  # >15% drawdown
            risk_adjustment = 0.75
            # Only log at INFO level for moderate drawdown if it changed significantly
            if self._should_log_drawdown_warning(self.current_drawdown):
                self.logger.info(f"📉 Moderate drawdown: {self.current_drawdown:.1%} - Reducing risk to 75%")
                self.last_drawdown_warning_level = self.current_drawdown
        else:
            risk_adjustment = 1.0
            # Reset warning tracker when drawdown recovers
            if self.last_drawdown_warning_level > 0:
                self.last_drawdown_warning_level = 0.0
        
        return risk_adjustment
    
    # PRIORITY 1 SAFETY: Kill Switch and Guardrails
    
    def activate_kill_switch(self, reason: str) -> None:
        """
        Activate the global kill switch - halts all new entries but allows exits
        
        Args:
            reason: Reason for activation (logged for audit)
        """
        self.kill_switch_active = True
        self.kill_switch_reason = reason
        self.logger.critical(f"🛑 KILL SWITCH ACTIVATED: {reason}")
        self.logger.critical("   ⚠️  No new positions will be opened")
        self.logger.critical("   ✓ Existing positions can still be closed")
    
    def deactivate_kill_switch(self) -> None:
        """Deactivate the global kill switch - resumes normal trading"""
        if self.kill_switch_active:
            self.logger.info(f"✅ KILL SWITCH DEACTIVATED (was: {self.kill_switch_reason})")
        self.kill_switch_active = False
        self.kill_switch_reason = ""
    
    def is_kill_switch_active(self) -> tuple[bool, str]:
        """
        Check if kill switch is active
        
        Returns:
            Tuple of (is_active, reason)
        """
        return self.kill_switch_active, self.kill_switch_reason
    
    def validate_trade_guardrails(self, balance: float, position_value: float, 
                                  current_positions: int, is_exit: bool = False) -> tuple[bool, str]:
        """
        Validate all hard guardrails before allowing a trade
        
        Args:
            balance: Current account balance
            position_value: Value of position being opened
            current_positions: Number of currently open positions
            is_exit: True if this is an exit trade (always allowed)
        
        Returns:
            Tuple of (is_allowed, blocking_reason)
        """
        # Always allow exits even if kill switch is active
        if is_exit:
            return True, "exit_allowed"
        
        # 1. Check kill switch
        if self.kill_switch_active:
            reason = f"Kill switch active: {self.kill_switch_reason}"
            self.logger.warning(f"🛑 Trade blocked - {reason}")
            return False, reason
        
        # 2. Check daily loss limit
        if self.daily_loss >= self.daily_loss_limit:
            reason = f"Daily loss limit reached: {self.daily_loss:.1%} >= {self.daily_loss_limit:.1%}"
            self.logger.warning(f"🛑 Trade blocked - {reason}")
            # Auto-activate kill switch on daily loss limit
            self.activate_kill_switch("Daily loss limit breach")
            return False, reason
        
        # 3. Check max concurrent positions
        if current_positions >= self.max_open_positions:
            reason = f"Max concurrent positions reached: {current_positions} >= {self.max_open_positions}"
            self.logger.warning(f"🛑 Trade blocked - {reason}")
            return False, reason
        
        # 4. Check per-trade max risk as % of equity
        if balance > 0:
            trade_risk_pct = position_value / balance
            if trade_risk_pct > self.max_risk_per_trade_pct:
                reason = f"Per-trade risk too high: {trade_risk_pct:.1%} > {self.max_risk_per_trade_pct:.1%} of equity"
                self.logger.warning(f"🛑 Trade blocked - {reason}")
                return False, reason
        
        # All checks passed
        return True, "guardrails_passed"
    
    def save_state(self):
        """Save risk manager state to disk"""
        try:
            os.makedirs('models', exist_ok=True)
            joblib.dump({
                'peak_balance': self.peak_balance,
                'current_drawdown': self.current_drawdown,
                'daily_start_balance': self.daily_start_balance,
                'daily_loss': self.daily_loss,
                'trading_date': self.trading_date,
                'win_streak': self.win_streak,
                'loss_streak': self.loss_streak,
                'recent_trades': self.recent_trades,
                'total_trades': self.total_trades,
                'wins': self.wins,
                'losses': self.losses,
                'total_profit': self.total_profit,
                'total_loss': self.total_loss
            }, self.state_path)
            self.logger.info(f"💾 Risk manager state saved ({self.total_trades} trades tracked)")
        except Exception as e:
            self.logger.error(f"Error saving risk manager state: {e}")
    
    def load_state(self):
        """Load risk manager state from disk"""
        try:
            if os.path.exists(self.state_path):
                data = joblib.load(self.state_path)
                self.peak_balance = data.get('peak_balance', 0.0)
                self.current_drawdown = data.get('current_drawdown', 0.0)
                self.daily_start_balance = data.get('daily_start_balance', 0.0)
                self.daily_loss = data.get('daily_loss', 0.0)
                self.trading_date = data.get('trading_date', None)
                self.win_streak = data.get('win_streak', 0)
                self.loss_streak = data.get('loss_streak', 0)
                self.recent_trades = data.get('recent_trades', [])
                self.total_trades = data.get('total_trades', 0)
                self.wins = data.get('wins', 0)
                self.losses = data.get('losses', 0)
                self.total_profit = data.get('total_profit', 0.0)
                self.total_loss = data.get('total_loss', 0.0)
                
                # Reset trading_date if it's a new day
                from datetime import date
                if self.trading_date != date.today():
                    self.trading_date = date.today()
                    self.daily_start_balance = 0.0
                    self.daily_loss = 0.0
                
                self.logger.info(f"📂 Risk manager state loaded ({self.total_trades} trades, win rate: {self.get_win_rate():.1%})")
        except Exception as e:
            self.logger.error(f"Error loading risk manager state: {e}")
