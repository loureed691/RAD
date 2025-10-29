"""
Strategy Collision Detection and Prevention

This module detects and prevents strategy collisions where multiple signals
could fight each other or double-submit orders for the same symbol.

Key Features:
- Single-writer pattern enforcement for order placement
- Unique, namespaced order ID generation with deduplication
- Debouncing to prevent rapid signal changes
- Idempotent order handlers
- Signal conflict resolution
"""
import time
import threading
from typing import Dict, List, Optional, Set, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from collections import defaultdict
from enum import Enum
from logger import Logger


class SignalSource(Enum):
    """Sources of trading signals"""
    MAIN_STRATEGY = "main_strategy"
    ML_MODEL = "ml_model"
    DCA_STRATEGY = "dca_strategy"
    HEDGING_STRATEGY = "hedging_strategy"
    RISK_MANAGER = "risk_manager"
    TRAILING_STOP = "trailing_stop"
    TAKE_PROFIT = "take_profit"
    STOP_LOSS = "stop_loss"


class SignalAction(Enum):
    """Types of trading actions"""
    OPEN_LONG = "open_long"
    OPEN_SHORT = "open_short"
    CLOSE_LONG = "close_long"
    CLOSE_SHORT = "close_short"
    ADD_TO_POSITION = "add_to_position"
    REDUCE_POSITION = "reduce_position"


@dataclass
class TradingSignal:
    """Represents a trading signal with full context"""
    symbol: str
    action: SignalAction
    source: SignalSource
    amount: float
    price: Optional[float] = None
    timestamp: datetime = field(default_factory=datetime.now)
    confidence: float = 1.0
    metadata: Dict = field(default_factory=dict)
    
    def get_fingerprint(self) -> str:
        """Generate unique fingerprint for deduplication"""
        return f"{self.symbol}_{self.action.value}_{self.source.value}_{self.amount:.8f}"


class StrategyCollisionDetector:
    """
    Detects and prevents strategy collisions
    
    Ensures:
    - Only one order per symbol per time window
    - No conflicting signals from different strategies
    - Debouncing to prevent rapid signal changes
    - Idempotent signal processing
    """
    
    def __init__(self, debounce_seconds: float = 5.0):
        """
        Initialize collision detector
        
        Args:
            debounce_seconds: Minimum time between signals for same symbol
        """
        self.logger = Logger.get_logger()
        
        # Single-writer pattern: Lock per symbol to ensure only one order at a time
        self.symbol_locks: Dict[str, threading.Lock] = defaultdict(threading.Lock)
        
        # Track recent signals for deduplication
        self.recent_signals: Dict[str, TradingSignal] = {}  # symbol -> signal
        self.signal_timestamps: Dict[str, datetime] = {}  # symbol -> timestamp
        
        # Debouncing: Track last action time per symbol
        self.last_action_time: Dict[str, datetime] = {}  # symbol -> timestamp
        self.debounce_seconds = debounce_seconds
        
        # Conflict tracking
        self.conflicting_signals: List[Tuple[TradingSignal, TradingSignal, str]] = []
        
        # Statistics
        self.signals_processed = 0
        self.signals_blocked = 0
        self.conflicts_detected = 0
        self.deduplication_hits = 0
        
        # Global lock for thread-safe operations
        self.global_lock = threading.Lock()
    
    def should_process_signal(self, signal: TradingSignal) -> Tuple[bool, str]:
        """
        Check if signal should be processed
        
        Returns:
            Tuple of (should_process, reason)
        """
        with self.global_lock:
            self.signals_processed += 1
            
            # Check for recent identical signal (deduplication)
            fingerprint = signal.get_fingerprint()
            if signal.symbol in self.recent_signals:
                recent = self.recent_signals[signal.symbol]
                if recent.get_fingerprint() == fingerprint:
                    # Identical signal within short time - deduplicate
                    time_diff = (signal.timestamp - self.signal_timestamps[signal.symbol]).total_seconds()
                    if time_diff < 60:  # 1 minute dedup window
                        self.deduplication_hits += 1
                        return False, f"Duplicate signal within {time_diff:.1f}s"
            
            # Check debounce period
            if signal.symbol in self.last_action_time:
                time_since_last = (signal.timestamp - self.last_action_time[signal.symbol]).total_seconds()
                if time_since_last < self.debounce_seconds:
                    self.signals_blocked += 1
                    return False, f"Debounce active, {self.debounce_seconds - time_since_last:.1f}s remaining"
            
            # Check for conflicting signals from different sources
            conflict_check = self._check_signal_conflicts(signal)
            if not conflict_check[0]:
                self.conflicts_detected += 1
                self.conflicting_signals.append((signal, conflict_check[2], conflict_check[1]))
                return False, conflict_check[1]
            
            return True, "OK"
    
    def _check_signal_conflicts(self, new_signal: TradingSignal) -> Tuple[bool, str, Optional[TradingSignal]]:
        """
        Check if new signal conflicts with recent signals
        
        Returns:
            Tuple of (is_valid, reason, conflicting_signal)
        """
        if new_signal.symbol not in self.recent_signals:
            return True, "No recent signals", None
        
        recent = self.recent_signals[new_signal.symbol]
        
        # Allow signals from same source (they're updates)
        if recent.source == new_signal.source:
            return True, "Same source", None
        
        # Check for conflicting actions
        # Opening long while we recently signaled short = conflict
        if (new_signal.action == SignalAction.OPEN_LONG and 
            recent.action == SignalAction.OPEN_SHORT):
            return False, f"Conflict: LONG signal conflicts with recent SHORT from {recent.source.value}", recent
        
        if (new_signal.action == SignalAction.OPEN_SHORT and 
            recent.action == SignalAction.OPEN_LONG):
            return False, f"Conflict: SHORT signal conflicts with recent LONG from {recent.source.value}", recent
        
        # Closing opposite direction signals should be allowed (take profit/stop loss)
        # unless they're both trying to open new positions
        
        # Risk manager and stop loss/take profit should always take precedence
        priority_sources = {SignalSource.RISK_MANAGER, SignalSource.STOP_LOSS, 
                           SignalSource.TAKE_PROFIT, SignalSource.TRAILING_STOP}
        
        if new_signal.source in priority_sources:
            return True, f"Priority source {new_signal.source.value}", None
        
        # DCA and hedging should not conflict with main strategy
        # They work alongside it
        non_conflicting = {SignalSource.DCA_STRATEGY, SignalSource.HEDGING_STRATEGY}
        if new_signal.source in non_conflicting and recent.source not in non_conflicting:
            return True, f"Non-conflicting source {new_signal.source.value}", None
        
        return True, "No conflict detected", None
    
    def register_signal(self, signal: TradingSignal):
        """Register a signal after it's been processed"""
        with self.global_lock:
            self.recent_signals[signal.symbol] = signal
            self.signal_timestamps[signal.symbol] = signal.timestamp
            self.last_action_time[signal.symbol] = signal.timestamp
    
    def acquire_symbol_lock(self, symbol: str, timeout: float = 5.0) -> bool:
        """
        Acquire exclusive lock for symbol (single-writer pattern)
        
        Args:
            symbol: Trading symbol
            timeout: Maximum time to wait for lock
            
        Returns:
            True if lock acquired, False if timeout
        """
        return self.symbol_locks[symbol].acquire(timeout=timeout)
    
    def release_symbol_lock(self, symbol: str):
        """Release exclusive lock for symbol"""
        try:
            self.symbol_locks[symbol].release()
        except Exception as e:
            self.logger.warning(f"Error releasing lock for {symbol}: {e}")
    
    def get_statistics(self) -> Dict:
        """Get collision detection statistics"""
        with self.global_lock:
            return {
                'signals_processed': self.signals_processed,
                'signals_blocked': self.signals_blocked,
                'conflicts_detected': self.conflicts_detected,
                'deduplication_hits': self.deduplication_hits,
                'block_rate': self.signals_blocked / self.signals_processed if self.signals_processed > 0 else 0,
                'conflict_rate': self.conflicts_detected / self.signals_processed if self.signals_processed > 0 else 0,
            }
    
    def get_recent_conflicts(self, limit: int = 10) -> List[Dict]:
        """Get recent conflicting signals"""
        with self.global_lock:
            conflicts = []
            for new_signal, old_signal, reason in self.conflicting_signals[-limit:]:
                conflicts.append({
                    'new_signal': {
                        'symbol': new_signal.symbol,
                        'action': new_signal.action.value,
                        'source': new_signal.source.value,
                        'timestamp': new_signal.timestamp.isoformat(),
                    },
                    'old_signal': {
                        'symbol': old_signal.symbol if isinstance(old_signal, TradingSignal) else 'N/A',
                        'action': old_signal.action.value if isinstance(old_signal, TradingSignal) else 'N/A',
                        'source': old_signal.source.value if isinstance(old_signal, TradingSignal) else 'N/A',
                    } if isinstance(old_signal, TradingSignal) else {},
                    'reason': reason,
                })
            return conflicts
    
    def clear_old_signals(self, max_age_seconds: float = 300.0):
        """Clear signals older than max_age_seconds"""
        with self.global_lock:
            now = datetime.now()
            to_remove = []
            
            for symbol, timestamp in self.signal_timestamps.items():
                age = (now - timestamp).total_seconds()
                if age > max_age_seconds:
                    to_remove.append(symbol)
            
            for symbol in to_remove:
                if symbol in self.recent_signals:
                    del self.recent_signals[symbol]
                if symbol in self.signal_timestamps:
                    del self.signal_timestamps[symbol]
            
            if to_remove:
                self.logger.debug(f"Cleared {len(to_remove)} old signals")


class OrderIDGenerator:
    """
    Generate unique, namespaced order IDs
    
    Format: {strategy}_{symbol}_{timestamp_ms}_{sequence}
    Example: main_BTC-USDT_1698765432123_001
    """
    
    def __init__(self):
        self.sequence_counters: Dict[str, int] = defaultdict(int)
        self.lock = threading.Lock()
        self.generated_ids: Set[str] = set()
    
    def generate(self, strategy: str, symbol: str) -> str:
        """
        Generate unique order ID
        
        Args:
            strategy: Strategy name (e.g., 'main', 'dca', 'hedge')
            symbol: Trading symbol
            
        Returns:
            Unique order ID string
        """
        with self.lock:
            timestamp_ms = int(time.time() * 1000)
            
            # Get next sequence number for this combination
            key = f"{strategy}_{symbol}_{timestamp_ms}"
            self.sequence_counters[key] += 1
            sequence = self.sequence_counters[key]
            
            # Generate ID
            order_id = f"{strategy}_{symbol}_{timestamp_ms}_{sequence:03d}"
            
            # Ensure uniqueness (should never happen, but be safe)
            while order_id in self.generated_ids:
                self.sequence_counters[key] += 1
                sequence = self.sequence_counters[key]
                order_id = f"{strategy}_{symbol}_{timestamp_ms}_{sequence:03d}"
            
            self.generated_ids.add(order_id)
            
            # Cleanup old IDs (keep last 10000)
            if len(self.generated_ids) > 10000:
                # Remove oldest 20%
                to_remove = list(self.generated_ids)[:2000]
                for old_id in to_remove:
                    self.generated_ids.discard(old_id)
            
            return order_id
    
    def is_duplicate(self, order_id: str) -> bool:
        """Check if order ID already exists"""
        with self.lock:
            return order_id in self.generated_ids


# Global instances for bot-wide use
_collision_detector = None
_order_id_generator = None


def get_collision_detector() -> StrategyCollisionDetector:
    """Get global collision detector instance"""
    global _collision_detector
    if _collision_detector is None:
        _collision_detector = StrategyCollisionDetector()
    return _collision_detector


def get_order_id_generator() -> OrderIDGenerator:
    """Get global order ID generator instance"""
    global _order_id_generator
    if _order_id_generator is None:
        _order_id_generator = OrderIDGenerator()
    return _order_id_generator


def main():
    """Test collision detection"""
    print("\n" + "="*80)
    print("STRATEGY COLLISION DETECTOR TEST")
    print("="*80 + "\n")
    
    detector = get_collision_detector()
    id_gen = get_order_id_generator()
    
    # Test 1: Normal signal flow
    print("Test 1: Normal signal flow")
    signal1 = TradingSignal(
        symbol="BTC/USDT:USDT",
        action=SignalAction.OPEN_LONG,
        source=SignalSource.MAIN_STRATEGY,
        amount=0.1,
        confidence=0.8
    )
    should_process, reason = detector.should_process_signal(signal1)
    print(f"  Signal 1: {should_process} - {reason}")
    if should_process:
        detector.register_signal(signal1)
        order_id = id_gen.generate("main", signal1.symbol)
        print(f"  Generated order ID: {order_id}")
    
    # Test 2: Duplicate signal (should be blocked)
    print("\nTest 2: Duplicate signal")
    signal2 = TradingSignal(
        symbol="BTC/USDT:USDT",
        action=SignalAction.OPEN_LONG,
        source=SignalSource.MAIN_STRATEGY,
        amount=0.1,
        confidence=0.8
    )
    should_process, reason = detector.should_process_signal(signal2)
    print(f"  Signal 2 (duplicate): {should_process} - {reason}")
    
    # Test 3: Conflicting signal (should be blocked)
    print("\nTest 3: Conflicting signal")
    signal3 = TradingSignal(
        symbol="BTC/USDT:USDT",
        action=SignalAction.OPEN_SHORT,
        source=SignalSource.ML_MODEL,
        amount=0.1,
        confidence=0.7
    )
    should_process, reason = detector.should_process_signal(signal3)
    print(f"  Signal 3 (conflicting SHORT): {should_process} - {reason}")
    
    # Test 4: Priority signal (should override)
    print("\nTest 4: Priority signal (stop loss)")
    signal4 = TradingSignal(
        symbol="BTC/USDT:USDT",
        action=SignalAction.CLOSE_LONG,
        source=SignalSource.STOP_LOSS,
        amount=0.1,
        confidence=1.0
    )
    should_process, reason = detector.should_process_signal(signal4)
    print(f"  Signal 4 (stop loss): {should_process} - {reason}")
    
    # Test 5: Different symbol (should work)
    print("\nTest 5: Different symbol")
    signal5 = TradingSignal(
        symbol="ETH/USDT:USDT",
        action=SignalAction.OPEN_LONG,
        source=SignalSource.MAIN_STRATEGY,
        amount=1.0,
        confidence=0.75
    )
    should_process, reason = detector.should_process_signal(signal5)
    print(f"  Signal 5 (ETH): {should_process} - {reason}")
    if should_process:
        detector.register_signal(signal5)
        order_id = id_gen.generate("main", signal5.symbol)
        print(f"  Generated order ID: {order_id}")
    
    # Show statistics
    print("\n" + "-"*80)
    print("Statistics:")
    stats = detector.get_statistics()
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    # Show recent conflicts
    print("\nRecent conflicts:")
    conflicts = detector.get_recent_conflicts()
    for i, conflict in enumerate(conflicts, 1):
        print(f"  {i}. {conflict['reason']}")
        print(f"     New: {conflict['new_signal']['action']} from {conflict['new_signal']['source']}")
        if conflict['old_signal']:
            print(f"     Old: {conflict['old_signal'].get('action', 'N/A')} from {conflict['old_signal'].get('source', 'N/A')}")
    
    print("\n✅ Collision detection test complete!")


if __name__ == '__main__':
    main()
