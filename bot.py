"""
Main trading bot orchestrator
"""
import time
import signal
import sys
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
            Config.API_PASSPHRASE
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
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        # Sync existing positions from exchange
        synced_positions = self.position_manager.sync_existing_positions()
        if synced_positions > 0:
            self.logger.info(f"📊 Managing {synced_positions} existing position(s) from exchange")
    
    def signal_handler(self, sig, frame):
        """Handle shutdown signals gracefully"""
        self.logger.info("🛑 Shutdown signal received, closing positions...")
        self.running = False
    
    def execute_trade(self, opportunity: dict) -> bool:
        """Execute a trade based on opportunity"""
        # Bug fix: Safely access opportunity dictionary with validation
        symbol = opportunity.get('symbol')
        signal = opportunity.get('signal')
        confidence = opportunity.get('confidence')
        
        if not symbol or not signal or confidence is None:
            self.logger.error(f"Invalid opportunity data: {opportunity}")
            return False
        
        # Check if we already have a position for this symbol
        if self.position_manager.has_position(symbol):
            self.logger.debug(f"Already have position for {symbol}, skipping")
            return False
        
        # Get current balance
        balance = self.client.get_balance()
        
        # Check if balance fetch was successful
        if not balance or 'free' not in balance:
            self.logger.error("Failed to fetch balance from exchange")
            return False
        
        available_balance = float(balance.get('free', {}).get('USDT', 0))
        
        if available_balance <= 0:
            self.logger.warning("💰 No available balance")
            return False
        
        # Check portfolio diversification
        open_position_symbols = list(self.position_manager.positions.keys())
        is_diversified, div_reason = self.risk_manager.check_portfolio_diversification(
            symbol, open_position_symbols
        )
        
        if not is_diversified:
            self.logger.info(f"Diversification check failed for {symbol}: {div_reason}")
            return False
        
        # Check if we should open a position
        current_positions = self.position_manager.get_open_positions_count()
        should_open, reason = self.risk_manager.should_open_position(
            current_positions, available_balance
        )
        
        if not should_open:
            self.logger.info(f"Not opening position: {reason}")
            return False
        
        # Validate trade
        is_valid, reason = self.risk_manager.validate_trade(
            symbol, signal, confidence
        )
        
        if not is_valid:
            self.logger.info(f"Trade not valid: {reason}")
            return False
        
        # Get market data for position sizing
        ticker = self.client.get_ticker(symbol)
        if not ticker:
            return False
        
        # Bug fix: Safely access 'last' price with validation
        entry_price = ticker.get('last')
        if not entry_price or entry_price <= 0:
            self.logger.warning(f"Invalid entry price for {symbol}: {entry_price}")
            return False
        
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
        
        # Adaptive position sizing using Kelly Criterion if we have performance history
        metrics = self.ml_model.get_performance_metrics()
        
        # Check drawdown and adjust risk
        risk_adjustment = self.risk_manager.update_drawdown(available_balance)
        
        if metrics.get('total_trades', 0) >= 20:  # Need at least 20 trades for Kelly
            win_rate = metrics.get('win_rate', 0.5)
            avg_profit = abs(metrics.get('avg_profit', 0.02))
            
            # Use actual tracked average loss if available, otherwise estimate
            avg_loss = metrics.get('avg_loss', 0)
            # Bug fix: Use threshold comparison for float values instead of == 0
            if avg_loss <= 0.0001 or metrics.get('losses', 0) < 5:
                # FIX BUG 4: Not enough loss data - use conservative estimate based on volatility
                # rather than avg_profit * 1.5 which may not reflect actual risk
                # Use max of: current stop loss %, or 2x avg_profit (conservative)
                avg_loss = max(stop_loss_percentage, avg_profit * 2.0)
            
            optimal_risk = self.risk_manager.calculate_kelly_criterion(
                win_rate, avg_profit, avg_loss
            )
            # Apply drawdown protection
            risk_per_trade = optimal_risk * risk_adjustment
            self.logger.info(f"🎯 Using Kelly-optimized risk: {optimal_risk:.2%} × {risk_adjustment:.0%} = {risk_per_trade:.2%} (win rate: {win_rate:.2%}, avg profit: {avg_profit:.2%}, avg loss: {avg_loss:.2%})")
        else:
            # Apply drawdown protection to default risk
            risk_per_trade = self.risk_manager.risk_per_trade * risk_adjustment
            if risk_adjustment < 1.0:
                self.logger.info(f"Using default risk with drawdown protection: {self.risk_manager.risk_per_trade:.2%} × {risk_adjustment:.0%} = {risk_per_trade:.2%}")
        
        # Calculate position size with optimized risk
        position_size = self.risk_manager.calculate_position_size(
            available_balance, entry_price, stop_loss_price, leverage, risk_per_trade
        )
        
        # Open position
        success = self.position_manager.open_position(
            symbol, signal, position_size, leverage, stop_loss_percentage
        )
        
        return success
    
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
        
        # Update existing positions
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
        
        # Scan market for opportunities
        opportunities = self.scanner.get_best_pairs(n=5)
        
        # Try to execute trades for top opportunities
        for opportunity in opportunities:
            try:
                if self.position_manager.get_open_positions_count() >= Config.MAX_OPEN_POSITIONS:
                    self.logger.info("Maximum positions reached")
                    break
                
                # ENHANCEMENT: Validate opportunity dict before using
                if not isinstance(opportunity, dict) or 'symbol' not in opportunity:
                    self.logger.warning(f"Invalid opportunity data: {opportunity}")
                    continue
                
                self.logger.info(
                    f"🔎 Evaluating opportunity: {opportunity.get('symbol', 'UNKNOWN')} - "
                    f"Score: {opportunity.get('score', 0):.1f}, Signal: {opportunity.get('signal', 'UNKNOWN')}, "
                    f"Confidence: {opportunity.get('confidence', 0):.2f}"
                )
                
                success = self.execute_trade(opportunity)
                if success:
                    self.logger.info(f"✅ Trade executed for {opportunity.get('symbol', 'UNKNOWN')}")
            
            except Exception as e:
                self.logger.error(f"Error processing opportunity: {e}", exc_info=True)
                continue
        
        # Check if we should retrain the ML model
        time_since_retrain = (datetime.now() - self.last_retrain_time).total_seconds()
        if time_since_retrain > Config.RETRAIN_INTERVAL:
            self.logger.info("🤖 Retraining ML model...")
            if self.ml_model.train():
                self.logger.info("ML model retrained successfully")
            self.last_retrain_time = datetime.now()
        
        self.last_scan_time = datetime.now()
    
    def run(self):
        """Main bot loop"""
        self.running = True
        self.logger.info("=" * 60)
        self.logger.info("🚀 BOT STARTED SUCCESSFULLY!")
        self.logger.info("=" * 60)
        self.logger.info(f"⏱️  Check interval: {Config.CHECK_INTERVAL}s")
        self.logger.info(f"📊 Max positions: {Config.MAX_OPEN_POSITIONS}")
        self.logger.info(f"💪 Leverage: {Config.LEVERAGE}x")
        self.logger.info("=" * 60)
        
        try:
            while self.running:
                try:
                    self.run_cycle()
                    
                    # Wait before next cycle
                    self.logger.info(f"⏸️  Waiting {Config.CHECK_INTERVAL}s before next cycle...")
                    time.sleep(Config.CHECK_INTERVAL)
                    
                except Exception as e:
                    self.logger.error(f"❌ Error in trading cycle: {e}", exc_info=True)
                    time.sleep(60)  # Wait a bit longer on error
        
        except KeyboardInterrupt:
            self.logger.info("⌨️  Received keyboard interrupt")
        
        finally:
            self.shutdown()
    
    def shutdown(self):
        """Clean shutdown of the bot"""
        self.logger.info("=" * 60)
        self.logger.info("🛑 SHUTTING DOWN BOT...")
        self.logger.info("=" * 60)
        
        # Close all positions if configured to do so
        if getattr(Config, "CLOSE_POSITIONS_ON_SHUTDOWN", False):
            for symbol in list(self.position_manager.positions.keys()):
                try:
                    pnl = self.position_manager.close_position(symbol, 'shutdown')
                    if pnl is None:
                        self.logger.warning(f"⚠️  Failed to close position {symbol} during shutdown - may still be open on exchange")
                except Exception as e:
                    self.logger.error(f"Error closing position {symbol} during shutdown: {e}")
        
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
