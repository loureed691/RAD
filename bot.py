"""
Main trading bot orchestrator
"""
import time
import signal
import sys
import threading
import pandas as pd
from datetime import datetime, timedelta
from config import Config
from logger import Logger
from kucoin_client import KuCoinClient
from market_scanner import MarketScanner
from position_manager import PositionManager
from risk_manager import RiskManager
from ml_model import MLModel
from indicators import Indicators
from advanced_analytics import AdvancedAnalytics

class TradingBot:
    """Main trading bot that orchestrates all components"""
    
    def __init__(self):
        """Initialize the trading bot"""
        # Validate configuration
        Config.validate()
        
        # Setup logger
        self.logger = Logger.setup(Config.LOG_LEVEL, Config.LOG_FILE)
        self.logger.info("=" * 60)
        self.logger.info("🤖 INITIALIZING ADVANCED KUCOIN FUTURES TRADING BOT")
        self.logger.info("=" * 60)
        
        # Setup specialized loggers for detailed tracking
        self.position_logger = Logger.setup_specialized_logger(
            'PositionLogger', 
            Config.POSITION_LOG_FILE, 
            Config.DETAILED_LOG_LEVEL
        )
        self.scanning_logger = Logger.setup_specialized_logger(
            'ScanningLogger', 
            Config.SCANNING_LOG_FILE, 
            Config.DETAILED_LOG_LEVEL
        )
        self.orders_logger = Logger.setup_specialized_logger(
            'OrdersLogger',
            Config.ORDERS_LOG_FILE,
            Config.DETAILED_LOG_LEVEL
        )
        self.strategy_logger = Logger.setup_specialized_logger(
            'StrategyLogger',
            Config.STRATEGY_LOG_FILE,
            Config.DETAILED_LOG_LEVEL
        )
        
        self.logger.info(f"📝 Logging configuration:")
        self.logger.info(f"   Main log: {Config.LOG_FILE} (level: {Config.LOG_LEVEL})")
        self.logger.info(f"   Position tracking: {Config.POSITION_LOG_FILE} (level: {Config.DETAILED_LOG_LEVEL})")
        self.logger.info(f"   Market scanning: {Config.SCANNING_LOG_FILE} (level: {Config.DETAILED_LOG_LEVEL})")
        self.logger.info(f"   Order execution: {Config.ORDERS_LOG_FILE} (level: {Config.DETAILED_LOG_LEVEL})")
        self.logger.info(f"   Strategy analysis: {Config.STRATEGY_LOG_FILE} (level: {Config.DETAILED_LOG_LEVEL})")
        
        # Initialize components
        self.client = KuCoinClient(
            Config.API_KEY,
            Config.API_SECRET,
            Config.API_PASSPHRASE,
            enable_websocket=Config.ENABLE_WEBSOCKET
        )
        
        # Get balance and auto-configure trading parameters if not set in .env
        balance = self.client.get_balance()
        
        # Check if balance fetch was successful by checking for expected structure
        if balance and 'free' in balance:
            available_balance = float(balance.get('free', {}).get('USDT', 0))
            self.logger.info(f"💰 Available balance: ${available_balance:.2f} USDT")
            Config.auto_configure_from_balance(available_balance)
        else:
            self.logger.warning("⚠️  Could not fetch balance, using default configuration")
            # Set defaults if balance fetch fails
            if Config.LEVERAGE is None:
                Config.LEVERAGE = 10
            if Config.MAX_POSITION_SIZE is None:
                Config.MAX_POSITION_SIZE = 1000
            if Config.RISK_PER_TRADE is None:
                Config.RISK_PER_TRADE = 0.02
            if Config.MIN_PROFIT_THRESHOLD is None:
                Config.MIN_PROFIT_THRESHOLD = 0.005
        
        self.scanner = MarketScanner(self.client)
        
        self.position_manager = PositionManager(
            self.client,
            Config.TRAILING_STOP_PERCENTAGE
        )
        
        self.risk_manager = RiskManager(
            Config.MAX_POSITION_SIZE,
            Config.RISK_PER_TRADE,
            Config.MAX_OPEN_POSITIONS
        )
        
        self.ml_model = MLModel(Config.ML_MODEL_PATH)
        
        # Advanced analytics module
        self.analytics = AdvancedAnalytics()
        
        # State
        self.running = False
        self.last_scan_time = None
        self.last_retrain_time = datetime.now()
        self.last_analytics_report = datetime.now()
        
        # Background scanning state
        self._scan_thread = None
        self._scan_thread_running = False
        self._scan_lock = threading.Lock()
        self._latest_opportunities = []
        self._last_opportunity_update = datetime.now()
        
        # Position monitoring state - separate from scanning
        self._position_monitor_thread = None
        self._position_monitor_running = False
        self._position_monitor_lock = threading.Lock()  # Lock for position monitor timing
        self._last_position_check = datetime.now()
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        # Sync existing positions from exchange
        synced_positions = self.position_manager.sync_existing_positions()
        if synced_positions > 0:
            self.logger.info(f"📊 Managing {synced_positions} existing position(s) from exchange")
    
    def signal_handler(self, sig, frame):
        """Handle shutdown signals gracefully"""
        signal_name = 'SIGINT (Ctrl+C)' if sig == signal.SIGINT else f'SIGTERM ({sig})'
        self.logger.info("=" * 60)
        self.logger.info(f"🛑 Shutdown signal received: {signal_name}")
        self.logger.info("=" * 60)
        self.logger.info("⏳ Gracefully stopping bot...")
        self.logger.info("   - Stopping trading cycle")
        self.logger.info("   - Stopping background scanning thread")
        self.logger.info("   - Stopping position monitoring thread")
        self.logger.info("   - Will complete current operations")
        self.logger.info("   - Then proceed to shutdown")
        self.logger.info("=" * 60)
        self.running = False
        self._scan_thread_running = False
        self._position_monitor_running = False
    
    def execute_trade(self, opportunity: dict) -> bool:
        """
        Execute a trade based on opportunity
        
        IMPORTANT: This method ALWAYS uses fresh live data from the exchange.
        Cached data from scanning is NEVER used for actual trading decisions.
        All market data, prices, and indicators are fetched in real-time.
        """
        # Bug fix: Safely access opportunity dictionary with validation
        symbol = opportunity.get('symbol')
        signal = opportunity.get('signal')
        confidence = opportunity.get('confidence')
        
        if not symbol or not signal or confidence is None:
            self.logger.error(f"❌ TRADE REJECTED - Invalid opportunity data: {opportunity}")
            self.logger.error(f"   Symbol: {symbol}, Signal: {signal}, Confidence: {confidence}")
            return False
        
        self.logger.info(f"🔍 EVALUATING TRADE: {symbol}")
        self.logger.info(f"   Signal: {signal}, Confidence: {confidence:.2f}")
        
        # Check if we already have a position for this symbol
        if self.position_manager.has_position(symbol):
            self.logger.info(f"❌ TRADE REJECTED - Already have position for {symbol}")
            return False
        
        # Get current balance
        balance = self.client.get_balance()
        
        # Check if balance fetch was successful
        if not balance or 'free' not in balance:
            self.logger.error("❌ TRADE REJECTED - Failed to fetch balance from exchange")
            self.logger.error(f"   Balance response: {balance}")
            return False
        
        available_balance = float(balance.get('free', {}).get('USDT', 0))
        self.logger.info(f"   Available balance: ${available_balance:.2f} USDT")
        
        if available_balance <= 0:
            self.logger.warning("❌ TRADE REJECTED - No available balance")
            return False
        
        # Check portfolio diversification
        open_position_symbols = list(self.position_manager.positions.keys())
        is_diversified, div_reason = self.risk_manager.check_portfolio_diversification(
            symbol, open_position_symbols
        )
        
        if not is_diversified:
            self.logger.info(f"❌ TRADE REJECTED - Diversification check failed for {symbol}: {div_reason}")
            self.logger.info(f"   Current positions: {open_position_symbols}")
            return False
        
        self.logger.info(f"   ✓ Diversification check passed")
        
        # Check if we should open a position
        current_positions = self.position_manager.get_open_positions_count()
        should_open, reason = self.risk_manager.should_open_position(
            current_positions, available_balance
        )
        
        if not should_open:
            self.logger.info(f"❌ TRADE REJECTED - Not opening position: {reason}")
            self.logger.info(f"   Current positions: {current_positions}/{Config.MAX_OPEN_POSITIONS}")
            return False
        
        self.logger.info(f"   ✓ Position limit check passed ({current_positions}/{Config.MAX_OPEN_POSITIONS})")
        
        # Validate trade
        is_valid, reason = self.risk_manager.validate_trade(
            symbol, signal, confidence
        )
        
        if not is_valid:
            self.logger.info(f"❌ TRADE REJECTED - Trade validation failed: {reason}")
            self.logger.info(f"   Signal: {signal}, Confidence: {confidence:.2f}")
            return False
        
        self.logger.info(f"   ✓ Trade validation passed (confidence: {confidence:.2f})")
        
        # Get market data for position sizing
        ticker = self.client.get_ticker(symbol)
        if not ticker:
            self.logger.error(f"❌ TRADE REJECTED - Failed to fetch ticker for {symbol}")
            return False
        
        # Bug fix: Safely access 'last' price with validation
        entry_price = ticker.get('last')
        if not entry_price or entry_price <= 0:
            self.logger.warning(f"❌ TRADE REJECTED - Invalid entry price for {symbol}: {entry_price}")
            return False
        
        self.logger.info(f"   Entry price: ${entry_price:.6f}")
        
        # Get volatility for stop loss calculation
        ohlcv = self.client.get_ohlcv(symbol, timeframe='1h', limit=100)
        df = Indicators.calculate_all(ohlcv)
        indicators = Indicators.get_latest_indicators(df)
        volatility = indicators.get('bb_width', 0.03)
        
        # Get additional market context for smarter leverage calculation
        momentum = indicators.get('momentum', 0.0)
        
        # Calculate trend strength from moving averages
        close = indicators.get('close', entry_price)
        sma_20 = indicators.get('sma_20', close)
        sma_50 = indicators.get('sma_50', close)
        
        if sma_50 > 0 and not pd.isna(sma_50) and not pd.isna(sma_20):
            trend_strength = abs(sma_20 - sma_50) / sma_50
            trend_strength = min(trend_strength * 10, 1.0)  # Scale to 0-1
        else:
            trend_strength = 0.5
        
        # Detect market regime for leverage adjustment
        market_regime = self.scanner.signal_generator.detect_market_regime(df)
        
        # Calculate support/resistance levels for intelligent profit targeting
        support_resistance = Indicators.calculate_support_resistance(df, lookback=50)
        
        # Calculate stop loss
        stop_loss_percentage = self.risk_manager.calculate_stop_loss_percentage(volatility)
        
        if signal == 'BUY':
            stop_loss_price = entry_price * (1 - stop_loss_percentage)
        else:
            stop_loss_price = entry_price * (1 + stop_loss_percentage)
        
        # Calculate safe leverage with enhanced multi-factor analysis
        leverage = self.risk_manager.get_max_leverage(
            volatility, confidence, momentum, trend_strength, market_regime
        )
        leverage = min(leverage, Config.LEVERAGE)
        
        # Get Kelly Criterion fraction from risk_manager (uses performance history with adaptive logic)
        # Get performance metrics from risk_manager
        win_rate = self.risk_manager.get_win_rate()
        avg_profit = self.risk_manager.get_avg_win()
        avg_loss = self.risk_manager.get_avg_loss()
        total_trades = self.risk_manager.total_trades
        
        # Only use Kelly if we have sufficient trade history (20+ trades)
        kelly_fraction = None
        if total_trades >= 20 and win_rate > 0 and avg_profit > 0 and avg_loss > 0:
            # Use risk_manager's superior adaptive Kelly implementation
            kelly_fraction = self.risk_manager.calculate_kelly_criterion(
                win_rate, avg_profit, avg_loss, use_fractional=True
            )
        
        # Check drawdown and adjust risk
        risk_adjustment = self.risk_manager.update_drawdown(available_balance)
        
        # Calculate position size with Kelly Criterion if available
        position_size = self.risk_manager.calculate_position_size(
            available_balance, entry_price, stop_loss_price, leverage, 
            kelly_fraction=kelly_fraction * risk_adjustment if kelly_fraction is not None else None
        )
        
        # Log final trade parameters
        self.logger.info(f"   ✓ All validation checks passed - Attempting to open position")
        self.logger.info(f"   Leverage: {leverage}x, Position size: ${position_size:.2f}")
        self.logger.info(f"   Stop loss: ${stop_loss_price:.6f} ({stop_loss_percentage:.2%})")
        
        # Open position
        success = self.position_manager.open_position(
            symbol, signal, position_size, leverage, stop_loss_percentage
        )
        
        if success:
            self.logger.info(f"✅ TRADE EXECUTED - Successfully opened {signal} position for {symbol}")
        else:
            self.logger.error(f"❌ TRADE FAILED - Position manager failed to open position for {symbol}")
        
        return success
    
    def update_open_positions(self):
        """Update existing open positions - called frequently for live monitoring"""
        # Update existing positions
        # CRITICAL FIX: Wrap generator iteration in try/except to handle generator exceptions
        # Without this, if update_positions() raises during iteration (e.g., API errors),
        # the entire update_open_positions() call fails and NO positions get updated
        try:
            for symbol, pnl, position in self.position_manager.update_positions():
                try:
                    profit_icon = "📈" if pnl > 0 else "📉"
                    self.logger.info(f"{profit_icon} Position closed: {symbol}, P/L: {pnl:.2%}")
                    
                    # Record trade for analytics
                    trade_duration = (datetime.now() - position.entry_time).total_seconds() / 60
                    
                    # DEFENSIVE: Ensure leverage is not zero (should never happen, but be safe)
                    leverage = position.leverage if position.leverage > 0 else 1
                    
                    self.analytics.record_trade({
                        'symbol': symbol,
                        'side': position.side,
                        'entry_price': position.entry_price,
                        'exit_price': position.entry_price * (1 + pnl / leverage) if position.side == 'long' else position.entry_price * (1 - pnl / leverage),
                        'pnl': pnl,
                        'pnl_pct': pnl,
                        'duration': trade_duration,
                        'leverage': position.leverage
                    })
                    
                    # Record outcome for ML model
                    ohlcv = self.client.get_ohlcv(symbol, timeframe='1h', limit=100)
                    df = Indicators.calculate_all(ohlcv)
                    indicators = Indicators.get_latest_indicators(df)
                    
                    signal = 'BUY' if position.side == 'long' else 'SELL'
                    self.ml_model.record_outcome(indicators, signal, pnl)
                    
                    # Record outcome for risk manager (for streak tracking)
                    self.risk_manager.record_trade_outcome(pnl)
                
                except Exception as e:
                    self.logger.error(f"Error recording closed position {symbol}: {e}", exc_info=True)
        except Exception as e:
            # Generator-level exception (e.g., API error fetching positions)
            # Log and continue - position monitor will retry on next cycle
            self.logger.error(f"Error during position update iteration: {e}", exc_info=True)
    
    def _background_scanner(self):
        """Background thread that continuously scans for opportunities"""
        self.logger.info("🔍 Background scanner thread started")
        self.logger.info(f"   Scan interval: {Config.CHECK_INTERVAL}s")
        self.logger.info(f"   Max workers: {Config.MAX_WORKERS}")
        
        # Give position monitor thread a head start (additional safety measure)
        # This ensures critical position monitoring API calls happen first
        time.sleep(1)  # 1 second delay before first scan
        self.logger.info("🔍 [Background] Beginning market scans (position monitor has priority)")
        
        while self._scan_thread_running:
            try:
                # Scan market for opportunities
                self.logger.info("🔍 [Background] Scanning market for opportunities...")
                scan_start = datetime.now()
                opportunities = self.scanner.get_best_pairs(n=5)
                scan_duration = (datetime.now() - scan_start).total_seconds()
                
                # Update shared opportunities list in a thread-safe manner
                with self._scan_lock:
                    self._latest_opportunities = opportunities
                    self._last_opportunity_update = datetime.now()
                
                if opportunities:
                    self.logger.info(f"✅ [Background] Found {len(opportunities)} opportunities (scan took {scan_duration:.1f}s)")
                    # Log summary of opportunities
                    for i, opp in enumerate(opportunities[:3], 1):  # Show top 3
                        self.logger.info(
                            f"   {i}. {opp.get('symbol', 'UNKNOWN')}: "
                            f"Signal={opp.get('signal', 'UNKNOWN')}, "
                            f"Confidence={opp.get('confidence', 0):.2f}, "
                            f"Score={opp.get('score', 0):.1f}"
                        )
                else:
                    self.logger.info(f"ℹ️  [Background] No opportunities found in this scan (scan took {scan_duration:.1f}s)")
                
                # Sleep for the configured scan interval before next scan
                # Check periodically if we should stop - yield control more frequently
                for _ in range(Config.CHECK_INTERVAL):
                    if not self._scan_thread_running:
                        break
                    time.sleep(1)
                    
            except Exception as e:
                self.logger.error(f"❌ Error in background scanner: {e}", exc_info=True)
                self.logger.error(f"   Scanner will retry after brief delay")
                # Sleep briefly and continue
                time.sleep(10)
        
        self.logger.info("🔍 Background scanner thread stopped")
    
    def _position_monitor(self):
        """Dedicated thread for monitoring positions - runs independently of scanning"""
        self.logger.info("👁️ Position monitor thread started")
        
        while self._position_monitor_running:
            try:
                # Only update if we have positions
                if self.position_manager.get_open_positions_count() > 0:
                    # Thread-safe access to timing variable
                    with self._position_monitor_lock:
                        time_since_last = (datetime.now() - self._last_position_check).total_seconds()
                    
                    # Update positions at configured interval
                    if time_since_last >= Config.POSITION_UPDATE_INTERVAL:
                        self.update_open_positions()
                        # Thread-safe update of timing variable
                        with self._position_monitor_lock:
                            self._last_position_check = datetime.now()
                
                # Short sleep to avoid CPU hogging but stay responsive
                time.sleep(Config.LIVE_LOOP_INTERVAL)  # Use config constant for consistency
                
            except Exception as e:
                self.logger.error(f"❌ Error in position monitor: {e}", exc_info=True)
                time.sleep(1)
        
        self.logger.info("👁️ Position monitor thread stopped")
    
    def _get_latest_opportunities(self):
        """Get the latest opportunities from background scanner in a thread-safe manner"""
        with self._scan_lock:
            return list(self._latest_opportunities)  # Return a copy
    
    def scan_for_opportunities(self):
        """Execute trades for opportunities from background scanner"""
        # Get opportunities from background scanner
        opportunities = self._get_latest_opportunities()
        
        if not opportunities:
            self.logger.debug("ℹ️  No opportunities available from background scanner")
            return
        
        # Thread-safe access to last update time
        with self._scan_lock:
            age = (datetime.now() - self._last_opportunity_update).total_seconds()
        
        self.logger.info(f"📊 Processing {len(opportunities)} opportunities from background scanner (age: {int(age)}s)")
        
        # Validate opportunity age - reject if too old (stale data)
        max_age = Config.CHECK_INTERVAL * Config.STALE_DATA_MULTIPLIER  # Allow up to configurable multiple of the check interval
        if age > max_age:
            self.logger.warning(f"⚠️  OPPORTUNITIES REJECTED - Data is stale (age: {int(age)}s > max: {int(max_age)}s)")
            self.logger.warning(f"   Background scanner may be slow or encountering errors")
            return
        
        self.logger.info(f"   ✓ Opportunity data is fresh (age: {int(age)}s <= max: {int(max_age)}s)")
        
        # Try to execute trades for top opportunities
        trades_attempted = 0
        trades_executed = 0
        
        for opportunity in opportunities:
            try:
                if self.position_manager.get_open_positions_count() >= Config.MAX_OPEN_POSITIONS:
                    self.logger.info(f"⚠️  Maximum positions reached ({Config.MAX_OPEN_POSITIONS}), stopping trade execution")
                    break
                
                # ENHANCEMENT: Validate opportunity dict before using
                if not isinstance(opportunity, dict) or 'symbol' not in opportunity:
                    self.logger.warning(f"⚠️  Invalid opportunity data (not a dict or missing symbol): {opportunity}")
                    continue
                
                trades_attempted += 1
                
                self.logger.info(
                    f"🔎 Evaluating opportunity {trades_attempted}/{len(opportunities)}: {opportunity.get('symbol', 'UNKNOWN')} - "
                    f"Score: {opportunity.get('score', 0):.1f}, Signal: {opportunity.get('signal', 'UNKNOWN')}, "
                    f"Confidence: {opportunity.get('confidence', 0):.2f}"
                )
                
                success = self.execute_trade(opportunity)
                if success:
                    trades_executed += 1
                    self.logger.info(f"✅ Trade {trades_executed} executed for {opportunity.get('symbol', 'UNKNOWN')}")
            
            except Exception as e:
                self.logger.error(f"Error processing opportunity: {e}", exc_info=True)
                continue
        
        # Summary logging
        if trades_attempted > 0:
            self.logger.info(f"📊 SCAN SUMMARY: Attempted {trades_attempted} trades, executed {trades_executed}")
        else:
            self.logger.info(f"📊 SCAN SUMMARY: No valid opportunities to attempt")
    
    def run_cycle(self):
        """Run one complete trading cycle"""
        self.logger.info("🔄 Starting trading cycle...")
        
        # Periodically sync existing positions from exchange (every 10 cycles)
        # This ensures we catch any positions opened manually or by other means
        if not hasattr(self, '_cycle_count'):
            self._cycle_count = 0
        self._cycle_count += 1
        
        if self._cycle_count % 10 == 0:
            self.logger.debug("Periodic sync of existing positions...")
            self.position_manager.sync_existing_positions()
        
        # Update ML model's adaptive threshold in signal generator
        adaptive_threshold = self.ml_model.get_adaptive_confidence_threshold()
        self.scanner.signal_generator.set_adaptive_threshold(adaptive_threshold)
        self.logger.debug(f"Using adaptive confidence threshold: {adaptive_threshold:.2f}")
        
        # Note: Position updates are now handled by dedicated position monitor thread
        # No need to update positions here - they're continuously monitored
        
        # Record current equity for analytics
        balance = self.client.get_balance()
        if balance and 'free' in balance:
            available_balance = float(balance.get('free', {}).get('USDT', 0))
            self.analytics.record_equity(available_balance)
        
        # Periodic analytics report (every hour)
        time_since_report = (datetime.now() - self.last_analytics_report).total_seconds()
        if time_since_report > 3600:  # 1 hour
            self.logger.info(self.analytics.get_performance_summary())
            self.last_analytics_report = datetime.now()
        
        # Log performance metrics
        metrics = self.ml_model.get_performance_metrics()
        if metrics.get('total_trades', 0) > 0:
            self.logger.info(
                f"Performance - Win Rate: {metrics.get('win_rate', 0):.2%}, "
                f"Avg P/L: {metrics.get('avg_profit', 0):.2%}, "
                f"Total Trades: {metrics.get('total_trades', 0)}"
            )
        
        # Execute trades from opportunities found by background scanner
        self.scan_for_opportunities()
        
        # Check if we should retrain the ML model
        time_since_retrain = (datetime.now() - self.last_retrain_time).total_seconds()
        if time_since_retrain > Config.RETRAIN_INTERVAL:
            self.logger.info("🤖 Retraining ML model...")
            if self.ml_model.train():
                self.logger.info("ML model retrained successfully")
            self.last_retrain_time = datetime.now()
        
        self.last_scan_time = datetime.now()
    
    def run(self):
        """Main bot loop with truly live continuous monitoring"""
        self.running = True
        self.logger.info("=" * 60)
        self.logger.info("🚀 BOT STARTED SUCCESSFULLY!")
        self.logger.info("=" * 60)
        self.logger.info(f"⏱️  Opportunity scan interval: {Config.CHECK_INTERVAL}s")
        self.logger.info(f"⚡ Position monitoring: DEDICATED THREAD (independent of scanning)")
        self.logger.info(f"🔥 Position update throttle: {Config.POSITION_UPDATE_INTERVAL}s minimum between API calls")
        self.logger.info(f"📊 Max positions: {Config.MAX_OPEN_POSITIONS}")
        self.logger.info(f"💪 Leverage: {Config.LEVERAGE}x")
        self.logger.info(f"⚙️  Parallel workers: {Config.MAX_WORKERS} (market scanning)")
        self.logger.info("=" * 60)
        self.logger.info("🚨 THREAD START PRIORITY:")
        self.logger.info("   1️⃣  Position Monitor (CRITICAL - starts first)")
        self.logger.info("   2️⃣  Background Scanner (starts after with delay)")
        self.logger.info("=" * 60)
        
        # CRITICAL: Start position monitor thread FIRST to ensure priority access to API
        # This prevents API call collisions and ensures critical position monitoring
        # happens before less critical market scanning
        self.logger.info("👁️ Starting dedicated position monitor thread (PRIORITY: CRITICAL)...")
        self._position_monitor_running = True
        self._position_monitor_thread = threading.Thread(target=self._position_monitor, daemon=True, name="PositionMonitor")
        self._position_monitor_thread.start()
        
        # Give position monitor a head start to establish priority
        time.sleep(0.5)  # 500ms delay ensures position monitor is running first
        
        # Start background scanner thread AFTER position monitor
        self.logger.info("🔍 Starting background scanner thread (PRIORITY: NORMAL)...")
        self._scan_thread_running = True
        self._scan_thread = threading.Thread(target=self._background_scanner, daemon=True, name="BackgroundScanner")
        self._scan_thread.start()
        
        self.logger.info("=" * 60)
        self.logger.info("✅ Both threads started - Position Monitor has API priority")
        self.logger.info("=" * 60)
        
        # Initialize timing for full cycles
        last_full_cycle = datetime.now()
        
        try:
            while self.running:
                try:
                    # Main loop now only handles full trading cycles (analytics, ML retraining, etc.)
                    # Position monitoring is handled by dedicated thread
                    time_since_last_cycle = (datetime.now() - last_full_cycle).total_seconds()
                    
                    if time_since_last_cycle >= Config.CHECK_INTERVAL:
                        # Run full trading cycle (includes opportunity scanning)
                        self.run_cycle()
                        last_full_cycle = datetime.now()
                    
                    # Very short sleep to avoid CPU hogging while staying responsive
                    # Main loop is now lightweight - heavy work delegated to background threads
                    time.sleep(Config.LIVE_LOOP_INTERVAL)  # Default 50ms - very responsive
                    
                except Exception as e:
                    self.logger.error(f"❌ Error in trading loop: {e}", exc_info=True)
                    time.sleep(1)  # Brief wait on error, then continue monitoring
        
        except KeyboardInterrupt:
            self.logger.info("=" * 60)
            self.logger.info("⌨️  Keyboard Interrupt (Ctrl+C) received")
            self.logger.info("=" * 60)
            self.logger.info("⏳ Initiating graceful shutdown...")
            self.logger.info("=" * 60)
        
        finally:
            self.shutdown()
    
    def shutdown(self):
        """Clean shutdown of the bot"""
        self.logger.info("=" * 60)
        self.logger.info("🛑 SHUTTING DOWN BOT...")
        self.logger.info("=" * 60)
        
        # IMPORTANT: Stop scanner first (less critical), then position monitor (critical)
        # This ensures position monitor can complete any critical operations
        # Stop background scanner thread
        if self._scan_thread and self._scan_thread.is_alive():
            self.logger.info("⏳ Stopping background scanner thread...")
            self._scan_thread_running = False
            self._scan_thread.join(timeout=5)  # Wait up to 5 seconds for thread to stop
            if self._scan_thread.is_alive():
                self.logger.warning("⚠️  Background scanner thread did not stop gracefully")
            else:
                self.logger.info("✅ Background scanner thread stopped")
        
        # Stop position monitor thread
        if self._position_monitor_thread and self._position_monitor_thread.is_alive():
            self.logger.info("⏳ Stopping position monitor thread...")
            self._position_monitor_running = False
            self._position_monitor_thread.join(timeout=5)  # Wait up to 5 seconds for thread to stop
            if self._position_monitor_thread.is_alive():
                self.logger.warning("⚠️  Position monitor thread did not stop gracefully")
            else:
                self.logger.info("✅ Position monitor thread stopped")
        
        # Close all positions if configured to do so
        if getattr(Config, "CLOSE_POSITIONS_ON_SHUTDOWN", False):
            for symbol in list(self.position_manager.positions.keys()):
                try:
                    pnl = self.position_manager.close_position(symbol, 'shutdown')
                    if pnl is None:
                        self.logger.warning(f"⚠️  Failed to close position {symbol} during shutdown - may still be open on exchange")
                except Exception as e:
                    self.logger.error(f"Error closing position {symbol} during shutdown: {e}")
        
        # Save ML model to preserve training data and performance metrics
        try:
            self.ml_model.save_model()
            self.logger.info("💾 ML model saved successfully")
        except Exception as e:
            self.logger.error(f"Error saving ML model during shutdown: {e}")
        
        # Close WebSocket and API connections
        try:
            self.client.close()
            self.logger.info("🔌 API connections closed")
        except Exception as e:
            self.logger.error(f"Error closing API connections: {e}")
        
        self.logger.info("=" * 60)
        self.logger.info("✅ BOT SHUTDOWN COMPLETE")
        self.logger.info("=" * 60)

def main():
    """Main entry point"""
    try:
        bot = TradingBot()
        bot.run()
    except Exception as e:
        logger = Logger.get_logger()
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
