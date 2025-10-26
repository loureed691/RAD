"""
Adaptive confidence threshold manager
Adjusts signal confidence requirements based on recent performance
"""
from typing import Dict, List
from datetime import datetime, timedelta
from logger import Logger


class AdaptiveConfidenceManager:
    """Manages adaptive confidence thresholds to improve trade quality"""
    
    def __init__(self, base_threshold: float = 0.60):
        """Initialize adaptive confidence manager
        
        Args:
            base_threshold: Base confidence threshold (default 60%)
        """
        self.logger = Logger.get_logger()
        self.base_threshold = base_threshold
        self.current_threshold = base_threshold
        
        # Performance tracking
        self.recent_trades: List[Dict] = []
        self.max_recent_trades = 50  # Track last 50 trades
        
        # Threshold bounds
        self.min_threshold = 0.50  # Never go below 50%
        self.max_threshold = 0.85  # Never go above 85%
        
        # Adjustment parameters
        self.adjustment_sensitivity = 0.02  # How much to adjust per evaluation
        
    def record_trade_outcome(self, confidence: float, was_profitable: bool):
        """Record a trade outcome for threshold learning
        
        Args:
            confidence: Confidence level of the signal that was traded
            was_profitable: Whether the trade was profitable (after fees)
        """
        trade_record = {
            'timestamp': datetime.now(),
            'confidence': confidence,
            'profitable': was_profitable
        }
        
        self.recent_trades.append(trade_record)
        
        # Keep only recent trades
        if len(self.recent_trades) > self.max_recent_trades:
            self.recent_trades = self.recent_trades[-self.max_recent_trades:]
    
    def get_adaptive_threshold(self) -> float:
        """Calculate adaptive confidence threshold based on recent performance
        
        Returns:
            Adjusted confidence threshold
        """
        if len(self.recent_trades) < 10:
            # Not enough data, use base threshold
            return self.base_threshold
        
        # Calculate win rate by confidence bucket
        low_conf_trades = [t for t in self.recent_trades if t['confidence'] < 0.65]
        mid_conf_trades = [t for t in self.recent_trades if 0.65 <= t['confidence'] < 0.75]
        high_conf_trades = [t for t in self.recent_trades if t['confidence'] >= 0.75]
        
        low_conf_win_rate = sum(1 for t in low_conf_trades if t['profitable']) / len(low_conf_trades) if low_conf_trades else 0
        mid_conf_win_rate = sum(1 for t in mid_conf_trades if t['profitable']) / len(mid_conf_trades) if mid_conf_trades else 0
        high_conf_win_rate = sum(1 for t in high_conf_trades if t['profitable']) / len(high_conf_trades) if high_conf_trades else 0
        
        # Overall recent win rate
        overall_win_rate = sum(1 for t in self.recent_trades if t['profitable']) / len(self.recent_trades)
        
        # Adjust threshold based on performance
        new_threshold = self.current_threshold
        
        # If overall win rate is low (<55%), increase threshold
        if overall_win_rate < 0.55:
            new_threshold += self.adjustment_sensitivity
            adjustment_reason = f"Low win rate ({overall_win_rate:.1%})"
            
        # If overall win rate is high (>70%), can decrease threshold to capture more opportunities
        elif overall_win_rate > 0.70:
            new_threshold -= self.adjustment_sensitivity / 2  # More conservative decrease
            adjustment_reason = f"High win rate ({overall_win_rate:.1%})"
            
        # If low confidence trades are losing, increase threshold
        elif low_conf_win_rate < 0.50 and len(low_conf_trades) >= 5:
            new_threshold += self.adjustment_sensitivity
            adjustment_reason = f"Low confidence trades losing ({low_conf_win_rate:.1%})"
            
        else:
            adjustment_reason = "Performance stable"
        
        # Apply bounds
        new_threshold = max(self.min_threshold, min(new_threshold, self.max_threshold))
        
        # Log if threshold changed significantly
        if abs(new_threshold - self.current_threshold) > 0.01:
            self.logger.info(
                f"🎯 Adaptive threshold: {self.current_threshold:.1%} → {new_threshold:.1%} "
                f"(Reason: {adjustment_reason}, Win rate: {overall_win_rate:.1%})"
            )
        
        self.current_threshold = new_threshold
        return self.current_threshold
    
    def should_trade(self, confidence: float) -> bool:
        """Check if a signal confidence meets the adaptive threshold
        
        Args:
            confidence: Signal confidence level
            
        Returns:
            True if confidence meets threshold, False otherwise
        """
        threshold = self.get_adaptive_threshold()
        return confidence >= threshold
    
    def get_statistics(self) -> Dict:
        """Get confidence threshold statistics
        
        Returns:
            Dict with threshold statistics
        """
        if not self.recent_trades:
            return {
                'current_threshold': self.current_threshold,
                'base_threshold': self.base_threshold,
                'recent_trades': 0
            }
        
        # Calculate statistics
        profitable_trades = sum(1 for t in self.recent_trades if t['profitable'])
        win_rate = profitable_trades / len(self.recent_trades) if self.recent_trades else 0
        
        avg_confidence = sum(t['confidence'] for t in self.recent_trades) / len(self.recent_trades)
        
        return {
            'current_threshold': self.current_threshold,
            'base_threshold': self.base_threshold,
            'min_threshold': self.min_threshold,
            'max_threshold': self.max_threshold,
            'recent_trades': len(self.recent_trades),
            'win_rate': win_rate,
            'avg_confidence': avg_confidence
        }
