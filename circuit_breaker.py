"""
Circuit breaker system for preventing catastrophic losses
Automatically halts trading during losing streaks to protect capital
"""
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from logger import Logger


class CircuitBreaker:
    """Circuit breaker system to prevent catastrophic losses during losing streaks"""
    
    def __init__(self):
        """Initialize circuit breaker"""
        self.logger = Logger.get_logger()
        
        # Circuit breaker state
        self.is_tripped = False
        self.trip_reason = ""
        self.trip_time: Optional[datetime] = None
        self.cooldown_minutes = 60  # Default 1 hour cooldown
        
        # Loss streak tracking
        self.consecutive_losses = 0
        self.max_consecutive_losses = 5  # Trip at 5 consecutive losses
        
        # Drawdown tracking
        self.recent_trades: List[Dict] = []
        self.max_recent_trades = 20
        
        # Quick loss tracking (multiple losses in short time)
        self.recent_loss_timestamps: List[datetime] = []
        self.quick_loss_window_minutes = 30  # 30 minute window
        self.max_losses_in_window = 3  # Max 3 losses in 30 minutes
        
        # Win streak recovery
        self.consecutive_wins = 0
        self.wins_to_reset = 2  # 2 consecutive wins resets circuit breaker
        
    def record_trade_outcome(self, was_profitable: bool, pnl_pct: float):
        """Record a trade outcome for circuit breaker logic
        
        Args:
            was_profitable: Whether the trade was profitable (after fees)
            pnl_pct: P&L percentage (leveraged ROI)
        """
        trade_record = {
            'timestamp': datetime.now(),
            'profitable': was_profitable,
            'pnl_pct': pnl_pct
        }
        
        self.recent_trades.append(trade_record)
        
        # Keep only recent trades
        if len(self.recent_trades) > self.max_recent_trades:
            self.recent_trades = self.recent_trades[-self.max_recent_trades:]
        
        # Update streaks
        if was_profitable:
            self.consecutive_losses = 0
            self.consecutive_wins += 1
            
            # Check for recovery
            if self.is_tripped and self.consecutive_wins >= self.wins_to_reset:
                self._reset_circuit_breaker()
        else:
            self.consecutive_wins = 0
            self.consecutive_losses += 1
            self.recent_loss_timestamps.append(datetime.now())
            
            # Clean old timestamps
            cutoff_time = datetime.now() - timedelta(minutes=self.quick_loss_window_minutes)
            self.recent_loss_timestamps = [
                ts for ts in self.recent_loss_timestamps if ts > cutoff_time
            ]
            
            # Check circuit breaker conditions
            self._check_circuit_breaker()
    
    def _check_circuit_breaker(self):
        """Check if circuit breaker should trip"""
        if self.is_tripped:
            return  # Already tripped
        
        # Check 1: Consecutive losses
        if self.consecutive_losses >= self.max_consecutive_losses:
            self._trip_circuit_breaker(
                f"{self.consecutive_losses} consecutive losses",
                cooldown_minutes=60
            )
            return
        
        # Check 2: Multiple losses in short time period
        if len(self.recent_loss_timestamps) >= self.max_losses_in_window:
            self._trip_circuit_breaker(
                f"{len(self.recent_loss_timestamps)} losses in {self.quick_loss_window_minutes} minutes",
                cooldown_minutes=90  # Longer cooldown for rapid losses
            )
            return
        
        # Check 3: Severe recent drawdown
        if len(self.recent_trades) >= 10:
            recent_pnl = sum(t['pnl_pct'] for t in self.recent_trades[-10:])
            if recent_pnl < -0.15:  # -15% cumulative loss in last 10 trades
                self._trip_circuit_breaker(
                    f"Severe drawdown: {recent_pnl:.1%} in last 10 trades",
                    cooldown_minutes=120  # 2 hour cooldown for severe losses
                )
                return
    
    def _trip_circuit_breaker(self, reason: str, cooldown_minutes: int):
        """Trip the circuit breaker
        
        Args:
            reason: Reason for tripping
            cooldown_minutes: Cooldown period in minutes
        """
        self.is_tripped = True
        self.trip_reason = reason
        self.trip_time = datetime.now()
        self.cooldown_minutes = cooldown_minutes
        
        cooldown_until = self.trip_time + timedelta(minutes=cooldown_minutes)
        
        self.logger.warning("=" * 80)
        self.logger.warning("🚨 CIRCUIT BREAKER TRIPPED!")
        self.logger.warning("=" * 80)
        self.logger.warning(f"Reason: {reason}")
        self.logger.warning(f"Cooldown: {cooldown_minutes} minutes")
        self.logger.warning(f"Trading halted until: {cooldown_until.strftime('%Y-%m-%d %H:%M:%S')}")
        self.logger.warning(f"Will resume if: 2 consecutive wins or cooldown expires")
        self.logger.warning("=" * 80)
    
    def _reset_circuit_breaker(self):
        """Reset the circuit breaker after recovery"""
        if not self.is_tripped:
            return
        
        self.logger.info("=" * 80)
        self.logger.info("✅ CIRCUIT BREAKER RESET - Trading Resumed")
        self.logger.info("=" * 80)
        self.logger.info(f"Reason: {self.consecutive_wins} consecutive wins")
        self.logger.info(f"Original trip reason: {self.trip_reason}")
        self.logger.info("=" * 80)
        
        self.is_tripped = False
        self.trip_reason = ""
        self.trip_time = None
        self.consecutive_losses = 0
    
    def can_trade(self) -> tuple[bool, str]:
        """Check if trading is allowed
        
        Returns:
            Tuple of (can_trade, reason)
        """
        if not self.is_tripped:
            return True, "Circuit breaker: OK"
        
        # Check if cooldown has expired
        if self.trip_time:
            cooldown_end = self.trip_time + timedelta(minutes=self.cooldown_minutes)
            if datetime.now() >= cooldown_end:
                self._reset_circuit_breaker()
                return True, "Circuit breaker: Cooldown expired, trading resumed"
        
        # Still tripped
        time_remaining = ""
        if self.trip_time:
            cooldown_end = self.trip_time + timedelta(minutes=self.cooldown_minutes)
            minutes_remaining = (cooldown_end - datetime.now()).total_seconds() / 60
            time_remaining = f" ({int(minutes_remaining)} minutes remaining)"
        
        return False, f"Circuit breaker: TRIPPED - {self.trip_reason}{time_remaining}"
    
    def get_status(self) -> Dict:
        """Get circuit breaker status
        
        Returns:
            Dict with status information
        """
        can_trade, message = self.can_trade()
        
        status = {
            'is_tripped': self.is_tripped,
            'can_trade': can_trade,
            'message': message,
            'consecutive_losses': self.consecutive_losses,
            'consecutive_wins': self.consecutive_wins,
            'recent_losses_count': len(self.recent_loss_timestamps),
        }
        
        if self.is_tripped and self.trip_time:
            cooldown_end = self.trip_time + timedelta(minutes=self.cooldown_minutes)
            status['tripped_at'] = self.trip_time.isoformat()
            status['cooldown_until'] = cooldown_end.isoformat()
            status['trip_reason'] = self.trip_reason
        
        # Calculate recent performance
        if len(self.recent_trades) >= 5:
            recent_wins = sum(1 for t in self.recent_trades[-10:] if t['profitable'])
            recent_total = min(len(self.recent_trades), 10)
            status['recent_win_rate'] = recent_wins / recent_total
            status['recent_pnl'] = sum(t['pnl_pct'] for t in self.recent_trades[-10:])
        
        return status
    
    def force_reset(self):
        """Manually reset the circuit breaker (use with caution)"""
        self.logger.warning("⚠️  Circuit breaker manually reset")
        self._reset_circuit_breaker()
