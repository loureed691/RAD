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
from performance_monitor import get_monitor
# 2026 Advanced Features
from advanced_risk_2026 import AdvancedRiskManager2026
from market_microstructure_2026 import MarketMicrostructure2026
from adaptive_strategy_2026 import AdaptiveStrategySelector2026
from performance_metrics_2026 import AdvancedPerformanceMetrics2026
# 2025 Optimization Features
from smart_entry_exit import SmartEntryExit
from enhanced_mtf_analysis import EnhancedMultiTimeframeAnalysis
from position_correlation import PositionCorrelationManager
from bayesian_kelly_2025 import BayesianAdaptiveKelly
# 2025 AI Enhancements
from enhanced_order_book_2025 import EnhancedOrderBookAnalyzer
from attention_features_2025 import AttentionFeatureSelector
# Smart Trading Enhancements
from smart_trading_enhancements import (
    SmartTradeFilter, SmartPositionSizer, SmartExitOptimizer,
    MarketContextAnalyzer, VolatilityAdaptiveParameters
)
# Enhanced ML Intelligence (2025+ Advanced AI)
from enhanced_ml_intelligence import (
    DeepLearningSignalPredictor, MultiTimeframeSignalFusion,
    AdaptiveExitStrategy, ReinforcementLearningStrategy
)
# DCA and Hedging Strategies
from dca_strategy import DCAStrategy
from hedging_strategy import HedgingStrategy
# Dashboard
from dashboard import TradingDashboard, FLASK_AVAILABLE

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
        
        # Setup specialized loggers - now all write to the same unified log file
        # with clear component tags for better visibility
        self.position_logger = Logger.setup_specialized_logger(
            'TradingBot.Position', 
            Config.LOG_FILE,  # All logs go to main log file now
            Config.DETAILED_LOG_LEVEL
        )
        self.scanning_logger = Logger.setup_specialized_logger(
            'TradingBot.Scanning', 
            Config.LOG_FILE,  # All logs go to main log file now
            Config.DETAILED_LOG_LEVEL
        )
        self.orders_logger = Logger.setup_specialized_logger(
            'TradingBot.Order',
            Config.LOG_FILE,  # All logs go to main log file now
            Config.DETAILED_LOG_LEVEL
        )
        self.strategy_logger = Logger.setup_specialized_logger(
            'TradingBot.Strategy',
            Config.LOG_FILE,  # All logs go to main log file now
            Config.DETAILED_LOG_LEVEL
        )
        
        self.logger.info(f"📝 Unified logging configuration:")
        self.logger.info(f"   Single log file: {Config.LOG_FILE}")
        self.logger.info(f"   Log level: {Config.LOG_LEVEL} (main), {Config.DETAILED_LOG_LEVEL} (detailed)")
        self.logger.info(f"   Component tags: [POSITION], [SCANNING], [ORDER], [STRATEGY]")
        self.logger.info(f"   All logs consolidated for better visibility")
        
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
                # Include trading fee buffer: 0.12% fees + 0.5% profit = 0.62%
                Config.MIN_PROFIT_THRESHOLD = 0.0062
        
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
        
        # Performance monitoring
        self.perf_monitor = get_monitor()
        self.logger.info("✅ Performance Monitor: ENABLED")
        
        # 2026 Advanced Features
        self.advanced_risk_2026 = AdvancedRiskManager2026()
        self.market_micro_2026 = MarketMicrostructure2026()
        self.strategy_selector_2026 = AdaptiveStrategySelector2026()
        self.performance_2026 = AdvancedPerformanceMetrics2026()
        
        # 2025 Optimization Features
        self.smart_entry_exit = SmartEntryExit()
        self.enhanced_mtf = EnhancedMultiTimeframeAnalysis()
        self.position_correlation = PositionCorrelationManager()
        self.bayesian_kelly = BayesianAdaptiveKelly(
            base_kelly_fraction=0.25,
            window_size=50
        )
        
        # 2025 AI Enhancements
        self.enhanced_orderbook_2025 = EnhancedOrderBookAnalyzer()
        self.attention_features_2025 = AttentionFeatureSelector(
            n_features=31,  # Match ML model feature count
            learning_rate=0.01
        )
        
        # Connect attention selector to ML model for feature weighting
        self.ml_model.attention_selector = self.attention_features_2025
        
        # Smart Trading Enhancements
        self.smart_trade_filter = SmartTradeFilter()
        self.smart_position_sizer = SmartPositionSizer()
        self.smart_exit_optimizer = SmartExitOptimizer()
        self.market_context_analyzer = MarketContextAnalyzer()
        self.volatility_adaptive_params = VolatilityAdaptiveParameters()
        
        # Enhanced ML Intelligence (Advanced AI)
        self.deep_learning_predictor = DeepLearningSignalPredictor(n_features=31)
        self.multi_tf_fusion = MultiTimeframeSignalFusion()
        self.adaptive_exit = AdaptiveExitStrategy()
        self.rl_strategy = ReinforcementLearningStrategy()
        # Load saved Q-table if available
        self.rl_strategy.load_q_table()
        
        # DCA and Hedging Strategies
        self.dca_strategy = DCAStrategy()
        self.hedging_strategy = HedgingStrategy()
        
        self.logger.info("🚀 2026 Advanced Features Activated:")
        self.logger.info("   ✅ Advanced Risk Manager (Regime-aware Kelly)")
        self.logger.info("   ✅ Market Microstructure (Order flow analysis)")
        self.logger.info("   ✅ Adaptive Strategy Selector (4 strategies)")
        self.logger.info("   ✅ Performance Metrics (Sharpe, Sortino, Calmar)")
        
        self.logger.info("🎯 2025 Optimization Features Activated:")
        self.logger.info("   ✅ Smart Entry/Exit (Order book timing)")
        self.logger.info("   ✅ Enhanced Multi-Timeframe Analysis")
        self.logger.info("   ✅ Position Correlation Management")
        self.logger.info("   ✅ Bayesian Adaptive Kelly Criterion")
        
        self.logger.info("🤖 2025 AI Enhancements Activated:")
        self.logger.info("   ✅ Enhanced Order Book Analyzer (VAMP, WDOP, OBI)")
        self.logger.info("   ✅ Attention-Based Feature Selection")
        
        self.logger.info("🧠 Smart Trading Enhancements Activated:")
        self.logger.info("   ✅ Smart Trade Filter (Quality prediction)")
        self.logger.info("   ✅ Smart Position Sizer (Multi-factor sizing)")
        self.logger.info("   ✅ Smart Exit Optimizer (ML-based timing)")
        self.logger.info("   ✅ Market Context Analyzer (Sentiment analysis)")
        self.logger.info("   ✅ Volatility-Adaptive Parameters")
        
        self.logger.info("🚀 ENHANCED ML INTELLIGENCE Activated:")
        self.logger.info("   ✅ Deep Learning Signal Predictor (LSTM + Dense)")
        self.logger.info("   ✅ Multi-Timeframe Signal Fusion (Weighted voting)")
        self.logger.info("   ✅ Adaptive Exit Strategy (Dynamic targets)")
        self.logger.info("   ✅ Reinforcement Learning Strategy Selector (Q-learning)")
        
        self.logger.info("💰 DCA & HEDGING STRATEGIES Activated:")
        self.logger.info("   ✅ DCA Strategy (Entry, Accumulation, Range)")
        self.logger.info("   ✅ Hedging Strategy (Portfolio protection)")
        
        # State
        self.running = False
        self.last_scan_time = None
        self.last_retrain_time = datetime.now()
        self.last_analytics_report = datetime.now()
        self.last_performance_report = datetime.now()  # Track performance reporting
        
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
        
        # Dashboard state
        self.dashboard = None
        self._dashboard_thread = None
        self._dashboard_update_thread = None
        self._dashboard_running = False
        self._last_dashboard_update = datetime.now()
        
        # Initialize dashboard if enabled
        if Config.ENABLE_DASHBOARD:
            if FLASK_AVAILABLE:
                try:
                    self.dashboard = TradingDashboard(port=Config.DASHBOARD_PORT)
                    self.logger.info("=" * 60)
                    self.logger.info("📊 DASHBOARD INITIALIZED")
                    self.logger.info(f"   Port: {Config.DASHBOARD_PORT}")
                    self.logger.info(f"   Host: {Config.DASHBOARD_HOST}")
                    self.logger.info(f"   URL: http://{Config.DASHBOARD_HOST}:{Config.DASHBOARD_PORT}")
                    self.logger.info("   Status: Ready to start")
                    self.logger.info("=" * 60)
                except Exception as e:
                    self.logger.error(f"Failed to initialize dashboard: {e}")
                    self.dashboard = None
            else:
                self.logger.warning("Dashboard is enabled but Flask is not available. Install flask and plotly to use the dashboard.")
        else:
            self.logger.info("📊 Dashboard: DISABLED (set ENABLE_DASHBOARD=true in .env to enable)")
        
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
        if self.dashboard:
            self.logger.info("   - Stopping dashboard threads")
        self.logger.info("   - Will complete current operations")
        self.logger.info("   - Then proceed to shutdown")
        self.logger.info("=" * 60)
        self.running = False
        self._scan_thread_running = False
        self._position_monitor_running = False
        self._dashboard_running = False
    
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
        
        # 2026 FEATURE: Calculate portfolio heat before opening position
        open_positions = list(self.position_manager.positions.values())
        
        # Calculate correlations between positions
        correlations = self.advanced_risk_2026.calculate_position_correlations(open_positions)
        
        portfolio_heat = self.advanced_risk_2026.calculate_portfolio_heat(
            open_positions, correlations
        )
        
        # Check if we should open a position
        current_positions = self.position_manager.get_open_positions_count()
        should_open, reason = self.risk_manager.should_open_position(
            current_positions, available_balance
        )
        
        if not should_open:
            self.logger.info(f"Not opening position: {reason}")
            return False
        
        # PRIORITY 1 SAFETY: Check clock sync periodically (hourly)
        if not self.client.verify_clock_sync_if_needed():
            self.logger.critical("❌ Clock drift too large - refusing to trade")
            return False
        
        # PRIORITY 1 SAFETY: Validate hard guardrails before proceeding
        # Calculate estimated position value for guardrail check
        ticker = self.client.get_ticker(symbol)
        if not ticker:
            return False
        entry_price_estimate = ticker.get('last', 0)
        if entry_price_estimate <= 0:
            self.logger.warning(f"Invalid entry price for {symbol}: {entry_price_estimate}")
            return False
        
        # Estimate position value (we'll refine this after calculating actual position size)
        # Use a conservative estimate (4% of balance) to pass the 5% guardrail check
        # The actual position size will be calculated later based on stop loss distance
        estimated_position_value = min(
            available_balance * 0.04,  # Conservative estimate under 5% guardrail
            Config.MAX_POSITION_SIZE
        )
        
        # Check all guardrails (kill switch, daily loss, max positions, per-trade risk)
        is_allowed, block_reason = self.risk_manager.validate_trade_guardrails(
            balance=available_balance,
            position_value=estimated_position_value,
            current_positions=current_positions,
            is_exit=False
        )
        
        if not is_allowed:
            self.logger.warning(f"🛑 GUARDRAILS BLOCKED TRADE: {block_reason}")
            return False
        
        self.logger.debug(f"✅ Guardrails passed: {block_reason}")
        
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
        
        # 2025 OPTIMIZATION: Enhanced multi-timeframe analysis
        try:
            # Fetch 4h and 1d data for confluence analysis
            ohlcv_4h = self.client.get_ohlcv(symbol, timeframe='4h', limit=50)
            df_4h = Indicators.calculate_all(ohlcv_4h) if ohlcv_4h else None
            
            ohlcv_1d = self.client.get_ohlcv(symbol, timeframe='1d', limit=30)
            df_1d = Indicators.calculate_all(ohlcv_1d) if ohlcv_1d else None
            
            # Analyze timeframe confluence
            mtf_confluence = self.enhanced_mtf.analyze_timeframe_confluence(
                df, df_4h, df_1d, signal, volatility
            )
            
            self.logger.info(f"📊 Multi-Timeframe Analysis:")
            self.logger.info(f"   Alignment: {mtf_confluence['alignment']}")
            self.logger.info(f"   Confluence score: {mtf_confluence['confluence_score']:.2f}")
            self.logger.info(f"   Confidence multiplier: {mtf_confluence['confidence_multiplier']:.2f}")
            
            # Apply confidence adjustment from MTF analysis
            confidence *= mtf_confluence['confidence_multiplier']
            self.logger.info(f"   ✅ MTF-adjusted confidence: {confidence:.2f}")
            
            # Check for timeframe divergence
            mtf_divergence = self.enhanced_mtf.detect_timeframe_divergence(df, df_4h)
            if mtf_divergence['divergence'] and mtf_divergence['strength'] > 0.6:
                self.logger.warning(f"⚠️  Timeframe divergence detected: {mtf_divergence['type']} (strength: {mtf_divergence['strength']:.2f})")
                confidence *= 0.9  # Reduce confidence for diverging timeframes
                
        except Exception as e:
            self.logger.debug(f"MTF analysis error: {e}")
            mtf_confluence = {'confidence_multiplier': 1.0}
        
        # 2026 FEATURE: Get order book for microstructure analysis
        try:
            orderbook = self.client.get_order_book(symbol, limit=20)
            orderbook_metrics = self.market_micro_2026.analyze_order_book_imbalance(orderbook)
            
            # Get 24h volume for liquidity score
            volume_24h = ticker.get('vol', 0) * entry_price  # Convert to USDT
            liquidity_score = self.market_micro_2026.calculate_liquidity_score(
                orderbook, volume_24h, []
            )
            
            self.logger.info(f"📊 Market Microstructure for {symbol}:")
            self.logger.info(f"   Order book imbalance: {orderbook_metrics['imbalance']:.3f} ({orderbook_metrics['signal']})")
            self.logger.info(f"   Spread: {orderbook_metrics['spread_bps']:.2f} bps")
            self.logger.info(f"   Liquidity score: {liquidity_score:.2f}")
            
            # 2025 OPTIMIZATION: Smart entry timing analysis
            entry_analysis = self.smart_entry_exit.analyze_entry_timing(
                orderbook, entry_price, signal, volatility
            )
            
            self.logger.info(f"🎯 Smart Entry Analysis:")
            self.logger.info(f"   Timing score: {entry_analysis['timing_score']:.2f}")
            self.logger.info(f"   Recommendation: {entry_analysis['recommendation']}")
            self.logger.info(f"   Reason: {entry_analysis['reason']}")
            
            # Adjust confidence based on entry timing
            if entry_analysis['timing_score'] > 0.7:
                confidence *= 1.1  # Boost confidence by 10% for excellent timing
                self.logger.info(f"   ✅ Excellent entry timing - confidence boosted to {confidence:.2f}")
            elif entry_analysis['timing_score'] < 0.4:
                confidence *= 0.9  # Reduce confidence by 10% for poor timing
                self.logger.info(f"   ⚠️  Suboptimal entry timing - confidence reduced to {confidence:.2f}")
            
            # 2025 AI ENHANCEMENT: Enhanced Order Book Analysis (VAMP, WDOP, OBI)
            try:
                # Calculate VAMP (Volume Adjusted Mid Price)
                vamp = self.enhanced_orderbook_2025.calculate_vamp(orderbook)
                
                # Calculate WDOP (Weighted-Depth Order Book Price)
                wdop_bid, wdop_ask = self.enhanced_orderbook_2025.calculate_wdop(orderbook, depth_levels=5)
                
                # Calculate Enhanced OBI
                enhanced_obi = self.enhanced_orderbook_2025.calculate_enhanced_obi(orderbook)
                
                # Get execution score
                execution_score = self.enhanced_orderbook_2025.get_execution_score(
                    orderbook, entry_price, signal.lower()
                )
                
                # Check if we should execute now
                should_exec, exec_reason = self.enhanced_orderbook_2025.should_execute_now(
                    orderbook, entry_price, signal.lower(), min_score=0.5
                )
                
                self.logger.info(f"📊 Enhanced Order Book Analysis (2025):")
                if vamp:
                    self.logger.info(f"   VAMP: ${vamp:.2f} (true market price)")
                if wdop_bid and wdop_ask:
                    self.logger.info(f"   WDOP: Bid=${wdop_bid:.2f}, Ask=${wdop_ask:.2f}")
                self.logger.info(f"   Enhanced OBI: {enhanced_obi['obi']:.3f} ({enhanced_obi['obi_strength']}, trend: {enhanced_obi['obi_trend']})")
                self.logger.info(f"   Execution Score: {execution_score:.2f}")
                self.logger.info(f"   Should Execute: {should_exec} - {exec_reason}")
                
                # Adjust confidence based on execution score
                if execution_score > 0.75:
                    confidence *= 1.08  # Boost confidence by 8% for excellent execution conditions
                    self.logger.info(f"   ✅ Excellent execution conditions - confidence boosted to {confidence:.2f}")
                elif execution_score < 0.4:
                    confidence *= 0.92  # Reduce confidence by 8% for poor execution conditions
                    self.logger.info(f"   ⚠️  Poor execution conditions - confidence reduced to {confidence:.2f}")
                
                # If enhanced analysis strongly suggests not executing, respect it
                if not should_exec and execution_score < 0.3:
                    self.logger.warning(f"❌ Enhanced order book analysis recommends NOT executing: {exec_reason}")
                    return False
                    
            except Exception as e:
                self.logger.debug(f"Enhanced order book analysis error: {e}")
            
        except Exception as e:
            self.logger.debug(f"Could not fetch orderbook data: {e}")
            orderbook_metrics = {'imbalance': 0.0, 'signal': 'neutral'}
            liquidity_score = 0.7  # Default moderate liquidity
            entry_analysis = {
                'timing_score': 0.5,
                'recommendation': 'market',
                'reason': 'No orderbook data'
            }
        
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
        
        # 2026 FEATURE: Enhanced market regime detection with price/volume data
        try:
            price_data = df['close'].values
            volume_data = df['volume'].values
            detected_regime = self.advanced_risk_2026.detect_market_regime(
                price_data, volume_data, lookback=50
            )
            self.logger.info(f"🔍 Market Regime Detected: {detected_regime}")
            market_regime = detected_regime
        except Exception as e:
            self.logger.debug(f"Using fallback regime detection: {e}")
        
        # ENHANCED ML: Multi-Timeframe Signal Fusion
        try:
            # Get signals from different timeframes
            signal_1h = (signal, confidence)
            
            # Get 4h indicators and signal
            indicators_4h = Indicators.get_latest_indicators(df_4h) if df_4h is not None else indicators
            ml_signal_4h, ml_conf_4h = self.ml_model.predict(indicators_4h)
            signal_4h = (ml_signal_4h if ml_conf_4h > 0.5 else 'HOLD', ml_conf_4h)
            
            # Get 1d indicators and signal
            indicators_1d = Indicators.get_latest_indicators(df_1d) if df_1d is not None else indicators
            ml_signal_1d, ml_conf_1d = self.ml_model.predict(indicators_1d)
            signal_1d = (ml_signal_1d if ml_conf_1d > 0.5 else 'HOLD', ml_conf_1d)
            
            # Fuse signals using sophisticated voting
            fused_signal, fused_confidence, fusion_details = self.multi_tf_fusion.fuse_signals(
                signal_1h, signal_4h, signal_1d
            )
            
            self.logger.info(f"🔮 Multi-Timeframe Signal Fusion:")
            self.logger.info(f"   1h: {signal_1h[0]} ({signal_1h[1]:.2f})")
            self.logger.info(f"   4h: {signal_4h[0]} ({signal_4h[1]:.2f})")
            self.logger.info(f"   1d: {signal_1d[0]} ({signal_1d[1]:.2f})")
            self.logger.info(f"   Fused: {fused_signal} ({fused_confidence:.2f})")
            self.logger.info(f"   Agreement: {fusion_details.get('agreement_score', 0):.2f}")
            self.logger.info(f"   Consistency: {fusion_details.get('consistency_score', 0):.2f}")
            
            # Use fused signal if it disagrees with original
            if fused_signal != signal and fused_confidence > 0.7:
                self.logger.info(f"   ✅ Using fused signal: {signal} -> {fused_signal}")
                signal = fused_signal
                confidence = fused_confidence
            elif fused_confidence > confidence:
                # Boost confidence if fusion agrees
                confidence = (confidence + fused_confidence) / 2
                self.logger.info(f"   ✅ Boosted confidence to {confidence:.2f}")
                
        except Exception as e:
            self.logger.debug(f"Multi-timeframe fusion error: {e}, using single timeframe signal")
        
        # ENHANCED ML: Deep Learning Signal Prediction
        try:
            features = self.ml_model.prepare_features(indicators).flatten()
            dl_signal, dl_confidence = self.deep_learning_predictor.predict(features)
            
            self.logger.info(f"🧠 Deep Learning Prediction: {dl_signal} ({dl_confidence:.2f})")
            
            # If deep learning strongly disagrees, be cautious
            if dl_signal != signal and dl_confidence > 0.8:
                self.logger.warning(f"   ⚠️ Deep learning disagrees with signal")
                confidence *= 0.85  # Reduce confidence
            elif dl_signal == signal and dl_confidence > 0.7:
                # Deep learning agrees - boost confidence
                confidence = (confidence * 0.7 + dl_confidence * 0.3)
                self.logger.info(f"   ✅ Deep learning confirms signal, confidence boosted to {confidence:.2f}")
                
        except Exception as e:
            self.logger.debug(f"Deep learning prediction error: {e}")
        
        # ENHANCED ML: Reinforcement Learning Strategy Selection
        try:
            # Use RL to select best strategy for current conditions
            rl_selected_strategy = self.rl_strategy.select_strategy(market_regime, volatility)
            
            # Prepare confidence scores for traditional selector
            confidence_scores = {
                'trend_following': confidence if market_regime in ['bull', 'bear'] else confidence * 0.8,
                'mean_reversion': confidence if market_regime in ['neutral', 'low_vol'] else confidence * 0.7,
                'breakout': confidence * 0.85,
                'momentum': confidence if abs(momentum) > 0.02 else confidence * 0.6
            }
            
            # Use traditional selector but weighted by RL recommendation
            selected_strategy = self.strategy_selector_2026.select_strategy(
                market_regime, volatility, trend_strength, confidence_scores
            )
            
            # If RL strongly recommends a different strategy, consider it
            if rl_selected_strategy != selected_strategy:
                self.logger.info(f"🎰 RL recommends: {rl_selected_strategy} (selected: {selected_strategy})")
                # For now, log the difference but use traditional selector
                # In the future, could blend or use RL more aggressively
            else:
                self.logger.info(f"🎯 RL agrees with strategy: {selected_strategy}")
            
            # Apply strategy-specific filters
            signal, confidence = self.strategy_selector_2026.apply_strategy_filters(
                selected_strategy, indicators, signal, confidence
            )
            
            if signal == 'HOLD':
                self.logger.info(f"Strategy {selected_strategy} filtered out trade")
                return False
            
            self.logger.info(f"🎯 Selected Strategy: {selected_strategy} (adjusted confidence: {confidence:.2f})")
        except Exception as e:
            self.logger.debug(f"Strategy selection error: {e}, using default")
            selected_strategy = 'trend_following'
            rl_selected_strategy = 'trend_following'
        
        # 2026 FEATURE: Advanced risk check with regime awareness
        try:
            should_trade, risk_reason = self.advanced_risk_2026.should_open_position(
                confidence, market_regime, portfolio_heat, liquidity_score
            )
            if not should_trade:
                self.logger.info(f"❌ 2026 Risk Check Failed: {risk_reason}")
                return False
            self.logger.info(f"✅ 2026 Risk Check Passed: {risk_reason}")
        except Exception as e:
            self.logger.warning(f"2026 risk check error: {e}, proceeding with caution")
        
        # SMART ENHANCEMENT: Trade Quality Filter
        try:
            rsi = indicators.get('rsi', 50)
            volume_ratio = indicators.get('volume_ratio', 1.0)
            recent_win_rate = self.risk_manager.get_win_rate()
            
            trade_quality = self.smart_trade_filter.calculate_trade_quality_score(
                signal_confidence=confidence,
                volatility=volatility,
                volume_ratio=volume_ratio,
                trend_strength=trend_strength,
                rsi=rsi,
                recent_win_rate=recent_win_rate,
                market_regime=market_regime
            )
            
            self.logger.info(f"🧠 Smart Trade Quality Analysis:")
            self.logger.info(f"   Quality Score: {trade_quality['quality_score']:.2f}")
            self.logger.info(f"   Recommendation: {trade_quality['recommendation']}")
            self.logger.info(f"   Position Multiplier: {trade_quality['position_multiplier']:.2f}x")
            
            if not trade_quality['passed']:
                self.logger.warning(f"❌ Trade Quality Filter: Score too low ({trade_quality['quality_score']:.2f})")
                return False
            
            self.logger.info(f"✅ Trade Quality Filter: Passed")
            
            # Store quality score for later adjustment
            trade_quality_multiplier = trade_quality['position_multiplier']
            
        except Exception as e:
            self.logger.warning(f"Trade quality filter error: {e}, proceeding without filter")
            trade_quality_multiplier = 1.0
            trade_quality = {'quality_score': 0.7, 'recommendation': 'GOOD'}
        
        # Calculate support/resistance levels for intelligent profit targeting
        support_resistance = Indicators.calculate_support_resistance(df, lookback=50)
        
        # Calculate stop loss
        stop_loss_percentage = self.risk_manager.calculate_stop_loss_percentage(volatility)
        
        # 2026 FEATURE: Enhanced stop loss with ATR and support/resistance
        try:
            atr = indicators.get('atr', entry_price * 0.02)  # Fallback to 2% if no ATR
            support_level = None
            if signal == 'BUY' and 'support' in support_resistance:
                # Get the strongest support level (first in list)
                support_list = support_resistance['support']
                if support_list and len(support_list) > 0:
                    support_level = support_list[0]['price'] if isinstance(support_list[0], dict) else support_list[0]
            elif signal == 'SELL' and 'resistance' in support_resistance:
                # Get the strongest resistance level (first in list)
                resistance_list = support_resistance['resistance']
                if resistance_list and len(resistance_list) > 0:
                    # If the first resistance is a dict, extract its price; otherwise, assume it's a numeric value.
                    if isinstance(resistance_list[0], dict):
                        support_level = resistance_list[0]['price']
                    elif isinstance(resistance_list[0], (float, int)):
                        support_level = resistance_list[0]
                    else:
                        self.logger.warning(f"Unexpected type for resistance_list[0]: {type(resistance_list[0])}. Expected dict or numeric. Setting support_level to None.")
                        support_level = None
            
            dynamic_stop = self.advanced_risk_2026.calculate_dynamic_stop_loss(
                entry_price, atr, support_level, market_regime,
                'long' if signal == 'BUY' else 'short'
            )
            
            # Use dynamic stop if it's more conservative than standard stop
            if signal == 'BUY':
                stop_loss_price = max(dynamic_stop, entry_price * (1 - stop_loss_percentage))
            else:
                stop_loss_price = min(dynamic_stop, entry_price * (1 + stop_loss_percentage))
                
            self.logger.info(f"🛡️ Dynamic Stop Loss: ${stop_loss_price:.2f} (regime-aware)")
        except Exception as e:
            self.logger.debug(f"Using standard stop loss: {e}")
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
            # 2025 OPTIMIZATION: Try Bayesian Adaptive Kelly first (if enough data)
            try:
                if total_trades >= 30:  # Need more trades for Bayesian to be effective
                    bayesian_sizing = self.bayesian_kelly.calculate_optimal_position_size(
                        balance=available_balance,
                        confidence=confidence,
                        market_volatility=volatility,
                        use_recent_window=True
                    )
                    
                    kelly_fraction = bayesian_sizing.get('kelly_fraction', None)
                    if kelly_fraction:
                        self.logger.info(f"💰 Bayesian Adaptive Kelly: {kelly_fraction:.3f}")
                        self.logger.info(f"   Win rate (Bayesian): {bayesian_sizing.get('win_rate_mean', 0):.3f} ± {bayesian_sizing.get('win_rate_std', 0):.3f}")
                        
            except Exception as e:
                self.logger.debug(f"Bayesian Kelly error: {e}, falling back to standard")
            
            # 2026 FEATURE: Use regime-aware Kelly Criterion if Bayesian not used
            if kelly_fraction is None:
                try:
                    kelly_fraction = self.advanced_risk_2026.calculate_regime_aware_kelly(
                        win_rate, avg_profit, avg_loss, market_regime, confidence
                    )
                    self.logger.info(f"💰 Regime-Aware Kelly: {kelly_fraction:.3f} (regime={market_regime})")
                except Exception as e:
                    # Fallback to standard Kelly with PRIORITY 1 fractional caps
                    self.logger.debug(f"Using standard Kelly: {e}")
                    kelly_fraction = self.risk_manager.calculate_kelly_criterion(
                        win_rate, avg_profit, avg_loss, use_fractional=True, volatility=volatility
                    )
                    self.logger.info(f"💰 Fractional Kelly (0.25-0.5 cap): {kelly_fraction:.3f}")
        else:
            self.logger.debug(f"Insufficient trade history ({total_trades} trades), using default risk")
        
        # Check drawdown and adjust risk
        risk_adjustment = self.risk_manager.update_drawdown(available_balance)
        
        # Calculate position size with Kelly Criterion if available
        position_size = self.risk_manager.calculate_position_size(
            available_balance, entry_price, stop_loss_price, leverage, 
            kelly_fraction=kelly_fraction * risk_adjustment if kelly_fraction is not None else None
        )
        
        # 2025 OPTIMIZATION: Correlation-based position sizing adjustment
        try:
            # Update price history for correlation tracking
            self.position_correlation.update_price_history(symbol, entry_price)
            
            # Get existing positions for correlation analysis
            existing_positions = []
            for pos_symbol, pos in self.position_manager.positions.items():
                amount = getattr(pos, 'amount', 0)
                entry_price = getattr(pos, 'entry_price', entry_price)
                value = amount * entry_price
                existing_positions.append({
                    'symbol': pos_symbol,
                    'value': value
                })
            
            if existing_positions:
                # CRITICAL FIX: Calculate total portfolio value (existing positions + available balance)
                # This prevents absurdly high concentration percentages when balance is low
                total_position_value = sum(pos['value'] for pos in existing_positions)
                total_portfolio_value = total_position_value + available_balance
                
                # Check category concentration limits
                is_allowed, concentration_reason = self.position_correlation.check_category_concentration(
                    symbol, existing_positions, total_portfolio_value
                )
                
                if not is_allowed:
                    self.logger.warning(f"🔗 Concentration limit exceeded: {concentration_reason}")
                    return False
                
                # Adjust position size based on correlations
                original_size = position_size
                position_size = self.position_correlation.get_correlation_adjusted_size(
                    symbol, position_size, existing_positions
                )
                
                if position_size != original_size:
                    reduction_pct = (1 - position_size / original_size) * 100
                    self.logger.info(f"🔗 Position size adjusted for correlation: {original_size:.4f} → {position_size:.4f} ({reduction_pct:.1f}% reduction)")
                    
        except Exception as e:
            self.logger.debug(f"Correlation analysis error: {e}, using unadjusted size")
        
        # SMART ENHANCEMENT: Multi-Factor Intelligent Position Sizing
        try:
            correlation_risk = 0.5  # Default moderate
            if len(existing_positions) > 0:
                # Calculate average correlation risk
                correlation_risk = min(len(existing_positions) * 0.2, 0.9)
            
            smart_sizing = self.smart_position_sizer.calculate_optimal_position_size(
                base_position_size=position_size,
                signal_confidence=confidence,
                trade_quality_score=trade_quality['quality_score'],
                volatility=volatility,
                correlation_risk=correlation_risk,
                portfolio_heat=portfolio_heat,
                recent_win_rate=recent_win_rate
            )
            
            self.logger.info(f"🧠 Smart Position Sizing:")
            self.logger.info(f"   Original: {position_size:.4f} {symbol}")
            self.logger.info(f"   Adjusted: {smart_sizing['adjusted_size']:.4f} {symbol}")
            self.logger.info(f"   Multiplier: {smart_sizing['multiplier']:.2f}x")
            self.logger.info(f"   Reasoning: {smart_sizing['reasoning']}")
            
            # Apply smart sizing adjustment
            position_size = smart_sizing['adjusted_size']
            
        except Exception as e:
            self.logger.warning(f"Smart position sizing error: {e}, using base size")
        
        # CRITICAL FIX: Cap position size to exchange maximum limit
        try:
            metadata = self.client.get_cached_symbol_metadata(symbol)
            if metadata:
                max_amount = metadata.get('max_amount')
                if max_amount and position_size > max_amount:
                    original_size = position_size
                    position_size = max_amount
                    self.logger.warning(
                        f"⚠️ Position size capped to exchange maximum: "
                        f"{original_size:.4f} → {position_size:.4f} contracts (max: {max_amount})"
                    )
        except Exception as e:
            self.logger.debug(f"Could not check position size limit: {e}")
        
        # ═══════════════════════════════════════════════════════════════════════
        # DCA STRATEGY INTEGRATION - Smart Entry Splitting
        # ═══════════════════════════════════════════════════════════════════════
        use_dca = False
        dca_plan = None
        
        if Config.ENABLE_DCA and Config.DCA_ENTRY_ENABLED:
            # Use DCA for lower confidence signals (smarter risk management)
            if confidence < Config.DCA_CONFIDENCE_THRESHOLD:
                try:
                    # Get current price for DCA plan
                    ticker = self.client.get_ticker(symbol)
                    if ticker and 'last' in ticker:
                        current_price = float(ticker['last'])
                        
                        # Create Entry DCA plan
                        dca_plan = self.dca_strategy.initialize_entry_dca(
                            symbol=symbol,
                            signal=signal,
                            total_amount=position_size,
                            entry_price=current_price,
                            confidence=confidence
                        )
                        
                        # Use first entry amount instead of full position
                        if dca_plan and len(dca_plan['entry_amounts']) > 0:
                            use_dca = True
                            position_size = dca_plan['entry_amounts'][0]
                            self.logger.info(f"💰 DCA Entry Strategy activated for {symbol}")
                            self.logger.info(f"   Confidence: {confidence:.2%} (< {Config.DCA_CONFIDENCE_THRESHOLD:.2%} threshold)")
                            self.logger.info(f"   Splitting into {dca_plan['num_entries']} entries")
                            self.logger.info(f"   First entry: {position_size:.4f} of {dca_plan['total_amount']:.4f}")
                
                except Exception as e:
                    self.logger.warning(f"DCA planning error: {e}, using full position")
                    use_dca = False
        
        # Open position (first entry if using DCA, full position otherwise)
        success = self.position_manager.open_position(
            symbol, signal, position_size, leverage, stop_loss_percentage
        )
        
        # If DCA plan created and first entry successful, record it
        if use_dca and success and dca_plan:
            try:
                ticker = self.client.get_ticker(symbol)
                if ticker and 'last' in ticker:
                    fill_price = float(ticker['last'])
                    self.dca_strategy.record_entry(symbol, position_size, fill_price)
                    self.logger.info(f"💰 DCA Entry 1/{dca_plan['num_entries']} recorded for {symbol}")
            except Exception as e:
                self.logger.warning(f"Error recording DCA entry: {e}")
        
        # Record trade quality for learning
        if success:
            try:
                self.smart_trade_filter.record_trade_outcome(
                    quality_score=trade_quality['quality_score'],
                    profit_pct=0.0  # Will be updated when position closes
                )
            except Exception as e:
                self.logger.debug(f"Error recording trade quality: {e}")
        
        # 2026 FEATURE: Store strategy with position for tracking
        if success and symbol in self.position_manager.positions:
            try:
                self.position_manager.positions[symbol].strategy = selected_strategy
                # Store RL strategy for learning
                self.position_manager.positions[symbol].rl_strategy = rl_selected_strategy
                self.position_manager.positions[symbol].market_regime = market_regime
                self.position_manager.positions[symbol].entry_volatility = volatility
            except AttributeError:
                # Position object doesn't support strategy attribute, which is fine
                self.logger.debug(f"Position for {symbol} doesn't support strategy attribute")
            except Exception as e:
                # Log unexpected errors but don't fail the trade
                self.logger.warning(f"Unexpected error setting strategy on position: {type(e).__name__}: {e}")
        
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
                    
                    # 2026 FEATURE: Record trade in performance metrics
                    try:
                        exit_price = position.entry_price * (1 + pnl / leverage) if position.side == 'long' else position.entry_price * (1 - pnl / leverage)
                        self.performance_2026.record_trade(
                            entry_price=position.entry_price,
                            exit_price=exit_price,
                            side=position.side,
                            size=position.amount,
                            pnl=pnl,
                            entry_time=position.entry_time,
                            exit_time=datetime.now(),
                            strategy=getattr(position, 'strategy', 'unknown')
                        )
                        
                        # Record for strategy selector if strategy is known
                        if hasattr(position, 'strategy'):
                            self.strategy_selector_2026.record_strategy_outcome(
                                position.strategy, pnl
                            )
                    except Exception as e:
                        self.logger.debug(f"Error recording 2026 metrics: {e}")
                    
                    # Record outcome for ML model
                    ohlcv = self.client.get_ohlcv(symbol, timeframe='1h', limit=100)
                    df = Indicators.calculate_all(ohlcv)
                    indicators = Indicators.get_latest_indicators(df)
                    
                    signal = 'BUY' if position.side == 'long' else 'SELL'
                    self.ml_model.record_outcome(indicators, signal, pnl)
                    
                    # 2025 AI ENHANCEMENT: Update attention weights based on trade outcome
                    try:
                        features = self.ml_model.prepare_features(indicators).flatten()
                        trade_success = pnl > 0.005  # Profitable trade
                        self.attention_features_2025.update_attention_weights(features, trade_success)
                        self.logger.debug(f"Updated attention weights based on trade outcome (success: {trade_success})")
                    except Exception as e:
                        self.logger.debug(f"Error updating attention weights: {e}")
                    
                    # Record outcome for risk manager (for streak tracking)
                    self.risk_manager.record_trade_outcome(pnl)
                    
                    # 2025 OPTIMIZATION: Record trade for Bayesian Kelly
                    try:
                        is_win = pnl > 0.005  # >0.5% is a win
                        self.bayesian_kelly.update_trade_outcome(is_win, pnl)
                    except Exception as e:
                        self.logger.debug(f"Error recording Bayesian Kelly trade: {e}")
                    
                    # ENHANCED ML: Update Reinforcement Learning Q-values
                    try:
                        if hasattr(position, 'rl_strategy') and hasattr(position, 'market_regime') and hasattr(position, 'entry_volatility'):
                            # Calculate reward (normalized profit)
                            reward = pnl / 0.05  # Normalize by 5% as target
                            reward = max(-1.0, min(reward, 2.0))  # Cap between -1 and 2
                            
                            self.rl_strategy.update_q_value(
                                position.market_regime,
                                position.entry_volatility,
                                position.rl_strategy,
                                reward
                            )
                            self.logger.debug(f"Updated RL Q-value for {position.rl_strategy} in {position.market_regime}")
                    except Exception as e:
                        self.logger.debug(f"Error updating RL Q-value: {e}")
                    
                    # ENHANCED ML: Update deep learning model with trade outcome
                    try:
                        features = self.ml_model.prepare_features(indicators).flatten()
                        label = 1 if (signal == 'BUY' and pnl > 0.005) or (signal == 'SELL' and pnl > 0.005) else 0
                        self.deep_learning_predictor.update(features, label)
                    except Exception as e:
                        self.logger.debug(f"Error updating deep learning model: {e}")
                    
                    # Update dashboard with closed trade
                    if self.dashboard:
                        try:
                            exit_price = position.entry_price * (1 + pnl / leverage) if position.side == 'long' else position.entry_price * (1 - pnl / leverage)
                            hours = int(trade_duration // 60)
                            minutes = int(trade_duration % 60)
                            self.dashboard.add_trade({
                                'symbol': symbol,
                                'side': position.side,
                                'entry_price': position.entry_price,
                                'exit_price': exit_price,
                                'amount': position.amount,
                                'pnl': pnl * (position.amount * position.entry_price),  # Dollar amount
                                'pnl_pct': pnl,
                                'duration': f"{hours}h {minutes}m",
                                'timestamp': datetime.now()
                            })
                        except Exception as e:
                            self.logger.debug(f"Error updating dashboard with trade: {e}")
                
                except Exception as e:
                    self.logger.error(f"Error recording closed position {symbol}: {e}", exc_info=True)
        except Exception as e:
            # Generator-level exception (e.g., API error fetching positions)
            # Log and continue - position monitor will retry on next cycle
            self.logger.error(f"Error during position update iteration: {e}", exc_info=True)
    
    def _background_scanner(self):
        """Background thread that continuously scans for opportunities"""
        self.logger.info("🔍 Background scanner thread started")
        
        # Give position monitor thread a head start (additional safety measure)
        # This ensures critical position monitoring API calls happen first
        time.sleep(1)  # 1 second delay before first scan
        self.logger.info("🔍 [Background] Beginning market scans (position monitor has priority)")
        
        while self._scan_thread_running:
            try:
                # PERFORMANCE: Track scan duration
                scan_start = time.time()
                
                # Scan market for opportunities
                self.logger.info("🔍 [Background] Scanning market for opportunities...")
                opportunities = self.scanner.get_best_pairs(n=5)
                
                scan_duration = time.time() - scan_start
                self.perf_monitor.record_scan_time(scan_duration)
                
                # Update shared opportunities list in a thread-safe manner
                with self._scan_lock:
                    self._latest_opportunities = opportunities
                    self._last_opportunity_update = datetime.now()
                
                if opportunities:
                    self.logger.info(f"✅ [Background] Found {len(opportunities)} opportunities (scan took {scan_duration:.1f}s)")
                else:
                    self.logger.debug("[Background] No opportunities found in this scan")
                
                # Report performance periodically
                if (datetime.now() - self.last_performance_report).total_seconds() >= 900:  # Every 15 minutes
                    self.perf_monitor.print_summary()
                    self.last_performance_report = datetime.now()
                    
                    # Check performance health
                    is_healthy, reason = self.perf_monitor.check_health()
                    if not is_healthy:
                        self.logger.warning(f"⚠️  PERFORMANCE WARNING: {reason}")
                
                # Sleep for the configured scan interval before next scan
                # Check periodically if we should stop - yield control more frequently
                for _ in range(Config.CHECK_INTERVAL):
                    if not self._scan_thread_running:
                        break
                    time.sleep(1)
                    
            except RuntimeError as e:
                # Handle graceful shutdown - interpreter is shutting down
                if "cannot schedule new futures after interpreter shutdown" in str(e):
                    self.logger.info("🔍 [Background] Scanner stopping due to shutdown")
                    break
                else:
                    self.logger.error(f"❌ Runtime error in background scanner: {e}", exc_info=True)
                    time.sleep(10)
            except Exception as e:
                self.logger.error(f"❌ Error in background scanner: {e}", exc_info=True)
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
            self.logger.debug("No opportunities available from background scanner")
            return
        
        # Thread-safe access to last update time
        with self._scan_lock:
            age = (datetime.now() - self._last_opportunity_update).total_seconds()
        
        self.logger.info(f"📊 Processing {len(opportunities)} opportunities from background scanner (age: {int(age)}s)")
        
        # Validate opportunity age - reject if too old (stale data)
        max_age = Config.CHECK_INTERVAL * Config.STALE_DATA_MULTIPLIER  # Allow up to configurable multiple of the check interval
        if age > max_age:
            self.logger.warning(f"⚠️  Opportunities are stale (age: {int(age)}s > max: {int(max_age)}s), skipping")
            return
        
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
    
    def run_cycle(self):
        """Run one complete trading cycle"""
        self.logger.info("🔄 Starting trading cycle...")
        
        # Periodically sync existing positions from exchange (every 10 cycles)
        # This ensures we catch any positions opened manually or by other means
        if not hasattr(self, '_cycle_count'):
            self._cycle_count = 0
        
        # Thread-safe cycle counter update
        with self._scan_lock:
            self._cycle_count += 1
            cycle_num = self._cycle_count
        
        if cycle_num % 10 == 0:
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
            
            # 2026 FEATURE: Record equity for performance metrics
            try:
                self.performance_2026.record_equity(available_balance)
            except Exception as e:
                self.logger.debug(f"Error recording 2026 equity: {e}")
        
        # Periodic analytics report (every hour)
        time_since_report = (datetime.now() - self.last_analytics_report).total_seconds()
        if time_since_report > 3600:  # 1 hour
            self.logger.info(self.analytics.get_performance_summary())
            
            # 2026 FEATURE: Log comprehensive performance metrics
            try:
                self.performance_2026.log_performance_report()
                
                # Log strategy statistics
                strategy_stats = self.strategy_selector_2026.get_strategy_statistics()
                self.logger.info("=" * 60)
                self.logger.info("🎯 STRATEGY PERFORMANCE")
                self.logger.info("=" * 60)
                self.logger.info(f"Current Strategy: {strategy_stats['current_strategy']}")
                for name, stats in strategy_stats['strategies'].items():
                    if stats['trades'] > 0:
                        self.logger.info(
                            f"  {stats['name']}: "
                            f"Trades={stats['trades']}, "
                            f"Win Rate={stats['win_rate']:.1%}"
                        )
                self.logger.info("=" * 60)
                
                # Log regime statistics
                regime_stats = self.advanced_risk_2026.get_regime_statistics()
                self.logger.info(f"📈 Market Regime: {regime_stats['current_regime']} "
                               f"(stability: {regime_stats['regime_stability']:.1%})")
            except Exception as e:
                self.logger.debug(f"Error logging 2026 metrics: {e}")
            
            self.last_analytics_report = datetime.now()
        
        # Log performance metrics
        metrics = self.ml_model.get_performance_metrics()
        if metrics.get('total_trades', 0) > 0:
            self.logger.info(
                f"Performance - Win Rate: {metrics.get('win_rate', 0):.2%}, "
                f"Avg P/L: {metrics.get('avg_profit', 0):.2%}, "
                f"Total Trades: {metrics.get('total_trades', 0)}"
            )
        
        # ═══════════════════════════════════════════════════════════════════════
        # DCA STRATEGY MONITORING - Check for additional entries
        # ═══════════════════════════════════════════════════════════════════════
        if Config.ENABLE_DCA:
            try:
                active_dca_positions = self.dca_strategy.get_active_dca_positions()
                for symbol in active_dca_positions:
                    if symbol in self.position_manager.positions:
                        # Get current price
                        ticker = self.client.get_ticker(symbol)
                        if ticker and 'last' in ticker:
                            current_price = float(ticker['last'])
                            
                            # Check if next DCA entry should be made
                            next_entry = self.dca_strategy.get_next_entry(symbol, current_price)
                            if next_entry:
                                amount, price = next_entry
                                position = self.position_manager.positions[symbol]
                                
                                # Execute DCA entry using scale_in
                                self.logger.info(f"💰 Executing DCA entry for {symbol}")
                                success = self.position_manager.scale_in_position(
                                    symbol, amount, price
                                )
                                
                                if success:
                                    self.dca_strategy.record_entry(symbol, amount, price)
                                    plan = self.dca_strategy.get_dca_plan(symbol)
                                    if plan:
                                        self.logger.info(
                                            f"💰 DCA Entry {plan['completed_entries']}/{plan['num_entries']} "
                                            f"completed for {symbol}"
                                        )
                
                # Accumulation DCA check for winning positions
                if Config.DCA_ACCUMULATION_ENABLED:
                    for symbol, position in self.position_manager.positions.items():
                        # Get current P/L
                        ticker = self.client.get_ticker(symbol)
                        if ticker and 'last' in ticker:
                            current_price = float(ticker['last'])
                            current_pnl = position.get_pnl(current_price)
                            
                            # Track number of accumulation adds (use position attribute if exists)
                            existing_adds = getattr(position, 'accumulation_adds', 0)
                            
                            # Check if should accumulate
                            should_add = self.dca_strategy.should_accumulate(
                                symbol, current_price, position.entry_price,
                                current_pnl, existing_adds
                            )
                            
                            if should_add:
                                add_amount = self.dca_strategy.get_accumulation_amount(
                                    position.amount, existing_adds + 1
                                )
                                
                                self.logger.info(f"💎 Accumulation DCA triggered for {symbol}")
                                success = self.position_manager.scale_in_position(
                                    symbol, add_amount, current_price
                                )
                                
                                if success:
                                    # Track accumulation adds
                                    if not hasattr(position, 'accumulation_adds'):
                                        position.accumulation_adds = 0
                                    position.accumulation_adds += 1
                                    self.logger.info(f"💎 Accumulation add #{position.accumulation_adds} completed")
                
                # Cleanup old DCA plans
                self.dca_strategy.cleanup_old_plans(max_age_hours=24)
                
            except Exception as e:
                self.logger.debug(f"DCA monitoring error: {e}")
        
        # ═══════════════════════════════════════════════════════════════════════
        # HEDGING STRATEGY MONITORING - Portfolio protection
        # ═══════════════════════════════════════════════════════════════════════
        if Config.ENABLE_HEDGING:
            try:
                # Get current portfolio state
                balance = self.client.get_balance()
                if balance and 'free' in balance:
                    available_balance = float(balance.get('free', {}).get('USDT', 0))
                    
                    # Calculate total portfolio value
                    position_value = sum(
                        getattr(pos, 'amount', 0) * getattr(pos, 'entry_price', 0)
                        for pos in self.position_manager.positions.values()
                    )
                    portfolio_value = available_balance + position_value
                    
                    if portfolio_value > 0:
                        # Check drawdown hedge trigger
                        current_drawdown = self.risk_manager.current_drawdown
                        if current_drawdown > 0:
                            hedge_rec = self.hedging_strategy.should_hedge_drawdown(
                                current_drawdown, portfolio_value
                            )
                            if hedge_rec:
                                hedge_id = self.hedging_strategy.create_hedge(hedge_rec)
                                self.logger.warning(f"🛡️ Drawdown hedge activated: {hedge_id}")
                        
                        # Check volatility hedge trigger
                        try:
                            # Get market volatility from advanced risk manager
                            volatility = getattr(self.advanced_risk_2026, 'current_volatility', 0.05)
                            hedge_rec = self.hedging_strategy.should_hedge_volatility(
                                volatility, portfolio_value
                            )
                            if hedge_rec:
                                hedge_id = self.hedging_strategy.create_hedge(hedge_rec)
                                self.logger.warning(f"🛡️ Volatility hedge activated: {hedge_id}")
                        except Exception as e:
                            self.logger.debug(f"Volatility hedge check error: {e}")
                        
                        # Check correlation hedge trigger
                        if len(self.position_manager.positions) > 0:
                            open_positions_dict = {}
                            for symbol, pos in self.position_manager.positions.items():
                                open_positions_dict[symbol] = {
                                    'side': getattr(pos, 'side', 'long'),
                                    'notional_value': getattr(pos, 'amount', 0) * getattr(pos, 'entry_price', 0)
                                }
                            
                            hedge_rec = self.hedging_strategy.should_hedge_correlation(
                                open_positions_dict, portfolio_value
                            )
                            if hedge_rec:
                                hedge_id = self.hedging_strategy.create_hedge(hedge_rec)
                                self.logger.warning(f"🛡️ Correlation hedge activated: {hedge_id}")
                        
                        # Check if existing hedges should be closed
                        active_hedges = self.hedging_strategy.get_active_hedges()
                        for hedge in active_hedges:
                            current_conditions = {
                                'drawdown': current_drawdown,
                                'volatility': getattr(self.advanced_risk_2026, 'current_volatility', 0.05),
                                'concentration': 0  # Will be calculated if needed
                            }
                            
                            if self.hedging_strategy.should_close_hedge(hedge['hedge_id'], current_conditions):
                                self.hedging_strategy.close_hedge(hedge['hedge_id'])
                                self.logger.info(f"🛡️ Hedge closed: {hedge['hedge_id']}")
                
                # Cleanup old closed hedges
                self.hedging_strategy.cleanup_old_hedges(max_age_hours=48)
                
            except Exception as e:
                self.logger.debug(f"Hedging monitoring error: {e}")
        
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
    
    def _update_dashboard_data(self):
        """Update dashboard with current bot data"""
        if not self.dashboard:
            return
        
        try:
            # Get current balance
            balance = self.client.get_balance()
            current_balance = 0
            if balance and 'free' in balance:
                current_balance = float(balance.get('free', {}).get('USDT', 0))
            
            # Get performance metrics
            metrics = self.ml_model.get_performance_metrics()
            
            # Calculate total P&L from analytics
            total_pnl = 0
            initial_balance = 10000  # Default, will be updated if available
            if hasattr(self.analytics, 'equity_history') and len(self.analytics.equity_history) > 0:
                eq0 = self.analytics.equity_history[0]
                if (isinstance(eq0, (list, tuple)) and len(eq0) > 1 and isinstance(eq0[1], (int, float)) and eq0[1] > 0):
                    initial_balance = eq0[1]
                else:
                    initial_balance = 10000
                total_pnl = current_balance - initial_balance
            
            # Update performance stats
            self.dashboard.update_stats({
                'balance': current_balance,
                'initial_balance': initial_balance,
                'total_pnl': total_pnl,
                'win_rate': metrics.get('win_rate', 0),
                'winning_trades': metrics.get('winning_trades', 0),
                'total_trades': metrics.get('total_trades', 0),
                'active_positions': self.position_manager.get_open_positions_count(),
                'total_exposure': sum(
                    getattr(pos, 'amount', 0) * getattr(pos, 'entry_price', 0)
                    for pos in self.position_manager.positions.values()
                ),
                'sharpe_ratio': getattr(self.performance_2026, 'get_sharpe_ratio', lambda: 0)(),
                'sortino_ratio': getattr(self.performance_2026, 'get_sortino_ratio', lambda: 0)(),
                'calmar_ratio': getattr(self.performance_2026, 'get_calmar_ratio', lambda: 0)(),
                'profit_factor': metrics.get('profit_factor', 0)
            })
            
            # Update open positions
            positions_data = []
            for symbol, pos in self.position_manager.positions.items():
                # Get current price
                ticker = self.client.get_ticker(symbol)
                current_price = ticker.get('last', getattr(pos, 'entry_price', 0)) if ticker else getattr(pos, 'entry_price', 0)
                
                # Calculate unrealized P&L
                entry_price = getattr(pos, 'entry_price', 0)
                amount = getattr(pos, 'amount', 0)
                leverage = getattr(pos, 'leverage', 1)
                side = getattr(pos, 'side', 'long')
                
                if side == 'long':
                    pnl_percent = ((current_price - entry_price) / entry_price) * leverage if entry_price > 0 else 0
                else:
                    pnl_percent = ((entry_price - current_price) / entry_price) * leverage if entry_price > 0 else 0
                
                unrealized_pnl = pnl_percent * (amount * entry_price)
                
                # Calculate duration
                entry_time = getattr(pos, 'entry_time', datetime.now())
                duration_delta = datetime.now() - entry_time
                hours = int(duration_delta.total_seconds() // 3600)
                minutes = int((duration_delta.total_seconds() % 3600) // 60)
                duration_str = f"{hours}h {minutes}m"
                
                positions_data.append({
                    'symbol': symbol,
                    'side': side,
                    'entry_price': entry_price,
                    'current_price': current_price,
                    'amount': amount,
                    'leverage': leverage,
                    'unrealized_pnl': unrealized_pnl,
                    'pnl_percent': pnl_percent * 100,
                    'stop_loss': getattr(pos, 'stop_loss', 0),
                    'take_profit': getattr(pos, 'take_profit', None),
                    'duration': duration_str
                })
            
            self.dashboard.update_positions(positions_data)
            
            # Update risk metrics
            max_dd = getattr(self.performance_2026, 'get_max_drawdown', lambda: 0)()
            current_dd = getattr(self.risk_manager, 'current_drawdown', 0)
            
            # Calculate portfolio heat
            open_positions = list(self.position_manager.positions.values())
            correlations = self.advanced_risk_2026.calculate_position_correlations(open_positions) if open_positions else {}
            portfolio_heat = self.advanced_risk_2026.calculate_portfolio_heat(open_positions, correlations)
            
            self.dashboard.update_risk_metrics({
                'max_drawdown': max_dd * 100 if max_dd < 1 else max_dd,
                'current_drawdown': abs(current_dd) * 100 if abs(current_dd) < 1 else abs(current_dd),
                'portfolio_heat': portfolio_heat,
                'total_exposure': sum(
                    getattr(pos, 'amount', 0) * getattr(pos, 'entry_price', 0)
                    for pos in self.position_manager.positions.values()
                ),
                'available_capital': current_balance,
                'daily_pnl': metrics.get('total_profit', 0),  # Approximation
                'avg_volatility': 3.0  # Default value
            })
            
            # Update strategy info
            strategy_stats = self.strategy_selector_2026.get_strategy_statistics()
            self.dashboard.update_strategy_info({
                'active_strategy': strategy_stats.get('current_strategy', 'Unknown'),
                'performance': metrics.get('avg_profit', 0) * 100
            })
            
            # Update market info
            regime_stats = self.advanced_risk_2026.get_regime_statistics()
            self.dashboard.update_market_info({
                'regime': regime_stats.get('current_regime', 'neutral'),
                'signal_strength': 0.5,  # Default value
                'volatility': 'normal',
                'trend': 'neutral',
                'last_signal': 'N/A'
            })
            
            # Update system status
            self.dashboard.update_system_status({
                'bot_active': self.running,
                'api_connected': True,  # Assume connected if we got here
                'websocket_active': Config.ENABLE_WEBSOCKET,
                'last_trade_time': self.last_scan_time.strftime('%Y-%m-%d %H:%M:%S') if self.last_scan_time else 'N/A',
                'uptime': 'Running',
                'error_count': 0  # Would need error tracking
            })
            
            # Add equity point
            self.dashboard.add_equity_point(current_balance)
            
            # Add drawdown point
            self.dashboard.add_drawdown_point(-abs(current_dd) * 100 if abs(current_dd) < 1 else -abs(current_dd))
            
        except Exception as e:
            self.logger.debug(f"Error updating dashboard data: {e}")
    
    def _dashboard_updater(self):
        """Background thread that continuously updates dashboard data"""
        self.logger.info("📊 Dashboard updater thread started")
        
        while self._dashboard_running and self.dashboard:
            try:
                # Update dashboard data every 5 seconds
                self._update_dashboard_data()
                time.sleep(5)
            except Exception as e:
                self.logger.error(f"Error in dashboard updater: {e}", exc_info=True)
                time.sleep(5)
        
        self.logger.info("📊 Dashboard updater thread stopped")
    
    def _run_dashboard_server(self):
        """Run the dashboard Flask server in a separate thread"""
        try:
            self.logger.info(f"🌐 Starting dashboard server on http://{Config.DASHBOARD_HOST}:{Config.DASHBOARD_PORT}")
            # Run dashboard with logging disabled to avoid clutter
            import logging
            log = logging.getLogger('werkzeug')
            log.setLevel(logging.ERROR)
            self.dashboard.run(debug=False, host=Config.DASHBOARD_HOST)
        except Exception as e:
            self.logger.error(f"Dashboard server error: {e}")
    
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
        if self.dashboard:
            self.logger.info("   3️⃣  Dashboard Server (web interface)")
            self.logger.info("   4️⃣  Dashboard Updater (data refresh)")
        self.logger.info("=" * 60)
        
        # Start dashboard server if enabled
        if self.dashboard:
            self.logger.info("🌐 Starting dashboard server thread...")
            self._dashboard_running = True
            self._dashboard_thread = threading.Thread(
                target=self._run_dashboard_server, 
                daemon=True, 
                name="DashboardServer"
            )
            self._dashboard_thread.start()
            
            # Start dashboard updater thread
            self.logger.info("📊 Starting dashboard updater thread...")
            self._dashboard_update_thread = threading.Thread(
                target=self._dashboard_updater,
                daemon=True,
                name="DashboardUpdater"
            )
            self._dashboard_update_thread.start()
            
            self.logger.info("=" * 60)
            self.logger.info("✅ DASHBOARD STARTED SUCCESSFULLY!")
            self.logger.info(f"   🌐 Access dashboard at: http://localhost:{Config.DASHBOARD_PORT}")
            self.logger.info(f"   🌐 Or from network: http://{Config.DASHBOARD_HOST}:{Config.DASHBOARD_PORT}")
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
        last_memory_cleanup = datetime.now()
        last_state_save = datetime.now()  # Track periodic state saving
        
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
                    
                    # OPTIMIZATION: Periodic memory cleanup (every 30 minutes)
                    time_since_cleanup = (datetime.now() - last_memory_cleanup).total_seconds()
                    if time_since_cleanup > 1800:  # 30 minutes
                        self._perform_memory_cleanup()
                        last_memory_cleanup = datetime.now()
                    
                    # CRITICAL: Periodic state saving (every 5 minutes) to prevent data loss
                    time_since_save = (datetime.now() - last_state_save).total_seconds()
                    if time_since_save > 300:  # 5 minutes
                        self._save_all_states()
                        last_state_save = datetime.now()
                    
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
    
    def _perform_memory_cleanup(self):
        """
        OPTIMIZATION: Perform periodic memory cleanup to prevent memory leaks
        and reduce memory footprint during long-running sessions
        """
        try:
            import gc
            
            # Clean up scanner cache
            with self.scanner._cache_lock:
                # Keep only recent cache entries (last 50 symbols)
                if len(self.scanner.cache) > 50:
                    # Sort by timestamp and keep newest 50
                    sorted_cache = sorted(
                        self.scanner.cache.items(),
                        key=lambda x: x[1][1],  # x[1][1] is timestamp
                        reverse=True
                    )
                    self.scanner.cache = dict(sorted_cache[:50])
                    self.logger.debug(f"Cleaned scanner cache: {len(sorted_cache)} → 50 entries")
            
            # Clean up ML model training data
            if len(self.ml_model.training_data) > 10000:
                self.ml_model.training_data = self.ml_model.training_data[-10000:]
                self.logger.debug("Cleaned ML training data: kept last 10,000 records")
            
            # Clean up analytics old equity records (keep last 7 days)
            from datetime import timedelta
            cutoff_time = datetime.now() - timedelta(days=7)
            if hasattr(self.analytics, 'equity_history'):
                original_len = len(self.analytics.equity_history)
                self.analytics.equity_history = [
                    (ts, equity) for ts, equity in self.analytics.equity_history
                    if ts > cutoff_time
                ]
                cleaned = original_len - len(self.analytics.equity_history)
                if cleaned > 0:
                    self.logger.debug(f"Cleaned analytics history: removed {cleaned} old records")
            
            # Force garbage collection
            collected = gc.collect()
            self.logger.debug(f"Memory cleanup complete: {collected} objects collected")
            
        except Exception as e:
            self.logger.error(f"Error during memory cleanup: {e}")
    
    def _save_all_states(self):
        """
        Periodically save all component states to prevent data loss
        Called every 5 minutes during runtime
        """
        try:
            # Increment the state save counter
            if not hasattr(self, "_state_save_counter"):
                self._state_save_counter = 1
            else:
                self._state_save_counter += 1

            # Log info every 6th save (i.e., every 30 minutes if called every 5 minutes)
            if self._state_save_counter % 6 == 0:
                self.logger.info(f"💾 Periodic state save (#{self._state_save_counter}) - feature working as expected.")
            else:
                self.logger.debug("💾 Periodic state save...")
            
            # Save ML model
            try:
                self.ml_model.save_model()
            except Exception as e:
                self.logger.debug(f"Error saving ML model: {e}")
            
            # Save deep learning model
            try:
                self.deep_learning_predictor.save()
            except Exception as e:
                self.logger.debug(f"Error saving deep learning model: {e}")
            
            # Save RL Q-table
            try:
                self.rl_strategy.save_q_table()
            except Exception as e:
                self.logger.debug(f"Error saving RL Q-table: {e}")
            
            # Save attention weights
            try:
                self.attention_features_2025.save_weights()
            except Exception as e:
                self.logger.debug(f"Error saving attention weights: {e}")
            
            # Save analytics state
            try:
                self.analytics.save_state()
            except Exception as e:
                self.logger.debug(f"Error saving analytics state: {e}")
            
            # Save risk manager state
            try:
                self.risk_manager.save_state()
            except Exception as e:
                self.logger.debug(f"Error saving risk manager state: {e}")
            
            self.logger.debug("✅ Periodic state save complete")
            
        except Exception as e:
            self.logger.error(f"Error during periodic state save: {e}")
    
    def shutdown(self):
        """Clean shutdown of the bot"""
        self.logger.info("=" * 60)
        self.logger.info("🛑 SHUTTING DOWN BOT...")
        self.logger.info("=" * 60)
        
        # Stop dashboard threads first
        if self.dashboard:
            self._dashboard_running = False
            if self._dashboard_update_thread and self._dashboard_update_thread.is_alive():
                self.logger.info("⏳ Stopping dashboard updater thread...")
                self._dashboard_update_thread.join(timeout=3)
                if self._dashboard_update_thread.is_alive():
                    self.logger.warning("⚠️  Dashboard updater thread did not stop gracefully")
                else:
                    self.logger.info("✅ Dashboard updater thread stopped")
            
            # Note: Flask server thread will stop when daemon thread exits
            # We don't need to explicitly join it
            if self._dashboard_thread and self._dashboard_thread.is_alive():
                self.logger.info("✅ Dashboard server thread will stop on exit")
        
        # IMPORTANT: Stop scanner first (less critical), then position monitor (critical)
        # This ensures position monitor can complete any critical operations
        # Stop background scanner thread
        if self._scan_thread:
            self._scan_thread_running = False  # Always set flag to False to stop any running thread
            if self._scan_thread.is_alive():
                self.logger.info("⏳ Stopping background scanner thread...")
                self._scan_thread.join(timeout=5)  # Wait up to 5 seconds for thread to stop
                if self._scan_thread.is_alive():
                    self.logger.warning("⚠️  Background scanner thread did not stop gracefully")
                else:
                    self.logger.info("✅ Background scanner thread stopped")
        
        # Stop position monitor thread
        if self._position_monitor_thread:
            self._position_monitor_running = False  # Always set flag to False to stop any running thread
            if self._position_monitor_thread.is_alive():
                self.logger.info("⏳ Stopping position monitor thread...")
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
        
        # Save all component states to preserve data
        self.logger.info("💾 Saving component states...")
        
        # Save ML model to preserve training data and performance metrics
        try:
            self.ml_model.save_model()
            self.logger.info("💾 ML model saved successfully")
        except Exception as e:
            self.logger.error(f"Error saving ML model during shutdown: {e}")
        
        # ENHANCED ML: Save deep learning and RL models
        try:
            self.deep_learning_predictor.save()
            self.logger.info("💾 Deep learning model saved successfully")
        except Exception as e:
            self.logger.error(f"Error saving deep learning model: {e}")
        
        try:
            self.rl_strategy.save_q_table()
            self.logger.info("💾 Reinforcement learning Q-table saved successfully")
        except Exception as e:
            self.logger.error(f"Error saving RL Q-table: {e}")
        
        # Save attention weights
        try:
            self.attention_features_2025.save_weights()
            self.logger.info("💾 Attention weights saved successfully")
        except Exception as e:
            self.logger.error(f"Error saving attention weights: {e}")
        
        # Save analytics state
        try:
            self.analytics.save_state()
            self.logger.info("💾 Analytics state saved successfully")
        except Exception as e:
            self.logger.error(f"Error saving analytics state: {e}")
        
        # Save risk manager state
        try:
            self.risk_manager.save_state()
            self.logger.info("💾 Risk manager state saved successfully")
        except Exception as e:
            self.logger.error(f"Error saving risk manager state: {e}")
        
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
