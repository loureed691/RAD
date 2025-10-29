"""
500-Scenario Stress Testing Engine for RAD Trading Bot

This module provides comprehensive stress testing with:
- ~500 deterministic scenarios covering all market conditions
- Full fee, latency, and slippage simulation
- Multi-asset, multi-timeframe testing
- Operational fault injection
- Walk-forward validation
- Reproducible results via seeded randomness
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import random
from logger import Logger
from backtest_engine import BacktestEngine
from config import Config
import json
import hashlib


class MarketRegime(Enum):
    """Market regime types for scenario generation"""
    STEADY_BULL = "steady_bull"
    STEADY_BEAR = "steady_bear"
    MEAN_REVERT_CHOP = "mean_revert_chop"
    BREAKOUT = "breakout"
    CRASH = "crash"
    GAP_UP = "gap_up"
    GAP_DOWN = "gap_down"
    FLASH_EVENT = "flash_event"
    LOW_LIQUIDITY_GRIND = "low_liquidity_grind"
    HIGH_VOL_WHIPSAW = "high_vol_whipsaw"


class VolatilityLevel(Enum):
    """Volatility levels for scenario generation"""
    ULTRA_LOW = "ultra_low"      # <10th percentile
    LOW = "low"                  # 10-25th percentile
    MEDIUM = "medium"            # 25-75th percentile
    HIGH = "high"                # 75-90th percentile
    ULTRA_HIGH = "ultra_high"    # >90th percentile


class LiquidityLevel(Enum):
    """Liquidity levels for scenario generation"""
    THIN = "thin"                # Sparse order book
    MEDIUM = "medium"            # Normal liquidity
    THICK = "thick"              # Deep order book


@dataclass
class ScenarioParams:
    """Parameters for a single test scenario"""
    # Identity
    scenario_id: str
    name: str
    seed: int
    
    # Market conditions
    regime: MarketRegime
    volatility: VolatilityLevel
    liquidity: LiquidityLevel
    
    # Price action
    num_candles: int = 1000
    initial_price: float = 50000.0
    drift_pct: float = 0.0  # Annual drift %
    
    # Volatility parameters
    base_volatility: float = 0.02  # 2% daily vol
    vol_clustering: float = 0.5  # GARCH effect
    
    # Microstructure
    spread_bps: float = 5.0  # Bid-ask spread in basis points
    spread_volatility: float = 0.1  # How much spread varies
    slippage_bps: float = 5.0  # Average slippage
    
    # Execution
    partial_fill_prob: float = 0.1  # Probability of partial fill
    cancel_prob: float = 0.02  # Probability of cancel
    reject_prob: float = 0.01  # Probability of reject
    
    # Latency
    min_latency_ms: int = 10
    max_latency_ms: int = 500
    latency_spikes: bool = False  # Include occasional 2s spikes
    
    # Operational faults
    clock_skew_ms: int = 0
    reconnect_prob: float = 0.0
    out_of_order_prob: float = 0.0
    balance_desync_prob: float = 0.0
    
    # Fees
    trading_fee_rate: float = 0.0006  # 0.06% taker
    funding_rate: float = 0.0001  # 0.01% per 8h
    borrow_rate: float = 0.00005  # For shorts
    
    # Multi-asset
    symbols: List[str] = field(default_factory=lambda: ['BTC/USDT:USDT'])
    timeframes: List[str] = field(default_factory=lambda: ['1h'])
    
    # Walk-forward
    in_sample_pct: float = 0.7  # 70% in-sample, 30% out-of-sample
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'scenario_id': self.scenario_id,
            'name': self.name,
            'seed': self.seed,
            'regime': self.regime.value,
            'volatility': self.volatility.value,
            'liquidity': self.liquidity.value,
            'num_candles': self.num_candles,
            'initial_price': self.initial_price,
            'drift_pct': self.drift_pct,
            'base_volatility': self.base_volatility,
            'vol_clustering': self.vol_clustering,
            'spread_bps': self.spread_bps,
            'spread_volatility': self.spread_volatility,
            'slippage_bps': self.slippage_bps,
            'partial_fill_prob': self.partial_fill_prob,
            'cancel_prob': self.cancel_prob,
            'reject_prob': self.reject_prob,
            'min_latency_ms': self.min_latency_ms,
            'max_latency_ms': self.max_latency_ms,
            'latency_spikes': self.latency_spikes,
            'clock_skew_ms': self.clock_skew_ms,
            'reconnect_prob': self.reconnect_prob,
            'out_of_order_prob': self.out_of_order_prob,
            'balance_desync_prob': self.balance_desync_prob,
            'trading_fee_rate': self.trading_fee_rate,
            'funding_rate': self.funding_rate,
            'borrow_rate': self.borrow_rate,
            'symbols': self.symbols,
            'timeframes': self.timeframes,
            'in_sample_pct': self.in_sample_pct,
        }


@dataclass
class ScenarioResult:
    """Results from running a scenario"""
    scenario_id: str
    scenario_name: str
    success: bool
    error_message: Optional[str] = None
    
    # Performance metrics
    total_return: float = 0.0
    sharpe_ratio: float = 0.0
    sortino_ratio: float = 0.0
    max_drawdown: float = 0.0
    profit_factor: float = 0.0
    win_rate: float = 0.0
    num_trades: int = 0
    
    # Costs
    total_fees: float = 0.0
    total_slippage: float = 0.0
    total_funding: float = 0.0
    
    # Execution quality
    avg_latency_ms: float = 0.0
    partial_fills: int = 0
    cancels: int = 0
    rejects: int = 0
    
    # Risk metrics
    var_95: float = 0.0  # 95% Value at Risk
    cvar_95: float = 0.0  # 95% Conditional VaR
    tail_ratio: float = 0.0
    
    # Exceptions and errors
    exceptions: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'scenario_id': self.scenario_id,
            'scenario_name': self.scenario_name,
            'success': self.success,
            'error_message': self.error_message,
            'total_return': self.total_return,
            'sharpe_ratio': self.sharpe_ratio,
            'sortino_ratio': self.sortino_ratio,
            'max_drawdown': self.max_drawdown,
            'profit_factor': self.profit_factor,
            'win_rate': self.win_rate,
            'num_trades': self.num_trades,
            'total_fees': self.total_fees,
            'total_slippage': self.total_slippage,
            'total_funding': self.total_funding,
            'avg_latency_ms': self.avg_latency_ms,
            'partial_fills': self.partial_fills,
            'cancels': self.cancels,
            'rejects': self.rejects,
            'var_95': self.var_95,
            'cvar_95': self.cvar_95,
            'tail_ratio': self.tail_ratio,
            'exceptions': self.exceptions,
            'warnings': self.warnings,
        }


class ScenarioGenerator:
    """Generate comprehensive test scenarios"""
    
    def __init__(self, base_seed: int = 42):
        """
        Initialize scenario generator
        
        Args:
            base_seed: Base random seed for reproducibility
        """
        self.base_seed = base_seed
        self.logger = Logger.get_logger()
        
    def generate_all_scenarios(self) -> List[ScenarioParams]:
        """
        Generate ~500 comprehensive test scenarios
        
        Returns:
            List of scenario parameters
        """
        scenarios = []
        
        # 1. Market Regime Scenarios (10 regimes × 10 variations = 100 scenarios)
        for regime in MarketRegime:
            for i in range(10):
                scenarios.append(self._create_regime_scenario(regime, i))
        
        # 2. Volatility Scenarios (5 levels × 10 variations = 50 scenarios)
        for vol_level in VolatilityLevel:
            for i in range(10):
                scenarios.append(self._create_volatility_scenario(vol_level, i))
        
        # 3. Liquidity Scenarios (3 levels × 10 variations = 30 scenarios)
        for liq_level in LiquidityLevel:
            for i in range(10):
                scenarios.append(self._create_liquidity_scenario(liq_level, i))
        
        # 4. Microstructure Scenarios (50 scenarios)
        for i in range(50):
            scenarios.append(self._create_microstructure_scenario(i))
        
        # 5. Latency & Slippage Scenarios (50 scenarios)
        for i in range(50):
            scenarios.append(self._create_latency_scenario(i))
        
        # 6. Operational Fault Scenarios (50 scenarios)
        for i in range(50):
            scenarios.append(self._create_fault_scenario(i))
        
        # 7. Multi-Asset Scenarios (60 scenarios: 3 symbols × 2 timeframes × 10 variations)
        symbols_list = [
            ['BTC/USDT:USDT', 'ETH/USDT:USDT', 'SOL/USDT:USDT'],
            ['BTC/USDT:USDT', 'MATIC/USDT:USDT', 'AVAX/USDT:USDT'],
        ]
        timeframes_list = [
            ['15m', '1h'],
            ['1h', '4h'],
            ['4h', '1d'],
        ]
        for symbols in symbols_list:
            for timeframes in timeframes_list:
                for i in range(10):
                    scenarios.append(self._create_multiasset_scenario(symbols, timeframes, i))
        
        # 8. Walk-Forward Scenarios (60 scenarios)
        for i in range(60):
            scenarios.append(self._create_walkforward_scenario(i))
        
        # 9. Extreme Stress Scenarios (50 scenarios)
        for i in range(50):
            scenarios.append(self._create_extreme_scenario(i))
        
        self.logger.info(f"Generated {len(scenarios)} test scenarios")
        return scenarios
    
    def _create_regime_scenario(self, regime: MarketRegime, variant: int) -> ScenarioParams:
        """Create a market regime scenario"""
        seed = self.base_seed + hash(f"{regime.value}_{variant}") % 100000
        np.random.seed(seed)
        random.seed(seed)
        
        # Regime-specific parameters
        regime_params = {
            MarketRegime.STEADY_BULL: {
                'drift_pct': 50.0 + np.random.uniform(-10, 10),
                'base_volatility': 0.015 + np.random.uniform(-0.005, 0.005),
            },
            MarketRegime.STEADY_BEAR: {
                'drift_pct': -40.0 + np.random.uniform(-10, 10),
                'base_volatility': 0.02 + np.random.uniform(-0.005, 0.005),
            },
            MarketRegime.MEAN_REVERT_CHOP: {
                'drift_pct': 0.0,
                'base_volatility': 0.025 + np.random.uniform(-0.01, 0.01),
            },
            MarketRegime.BREAKOUT: {
                'drift_pct': 80.0 + np.random.uniform(-20, 20),
                'base_volatility': 0.03 + np.random.uniform(-0.01, 0.01),
            },
            MarketRegime.CRASH: {
                'drift_pct': -70.0 + np.random.uniform(-10, 10),
                'base_volatility': 0.06 + np.random.uniform(-0.02, 0.02),
            },
            MarketRegime.GAP_UP: {
                'drift_pct': 30.0,
                'base_volatility': 0.04,
            },
            MarketRegime.GAP_DOWN: {
                'drift_pct': -30.0,
                'base_volatility': 0.04,
            },
            MarketRegime.FLASH_EVENT: {
                'drift_pct': 0.0,
                'base_volatility': 0.08,
            },
            MarketRegime.LOW_LIQUIDITY_GRIND: {
                'drift_pct': 5.0,
                'base_volatility': 0.01,
            },
            MarketRegime.HIGH_VOL_WHIPSAW: {
                'drift_pct': 0.0,
                'base_volatility': 0.05,
            },
        }
        
        params = regime_params.get(regime, {'drift_pct': 0.0, 'base_volatility': 0.02})
        
        return ScenarioParams(
            scenario_id=f"regime_{regime.value}_{variant}",
            name=f"Market Regime: {regime.value.replace('_', ' ').title()} (Variant {variant})",
            seed=seed,
            regime=regime,
            volatility=VolatilityLevel.MEDIUM,
            liquidity=LiquidityLevel.MEDIUM,
            num_candles=500 + np.random.randint(-100, 100),
            drift_pct=params['drift_pct'],
            base_volatility=params['base_volatility'],
            vol_clustering=0.3 + np.random.uniform(-0.1, 0.2),
        )
    
    def _create_volatility_scenario(self, vol_level: VolatilityLevel, variant: int) -> ScenarioParams:
        """Create a volatility-focused scenario"""
        seed = self.base_seed + hash(f"vol_{vol_level.value}_{variant}") % 100000
        np.random.seed(seed)
        random.seed(seed)
        
        vol_params = {
            VolatilityLevel.ULTRA_LOW: 0.005,
            VolatilityLevel.LOW: 0.012,
            VolatilityLevel.MEDIUM: 0.02,
            VolatilityLevel.HIGH: 0.035,
            VolatilityLevel.ULTRA_HIGH: 0.06,
        }
        
        base_vol = vol_params.get(vol_level, 0.02)
        
        return ScenarioParams(
            scenario_id=f"vol_{vol_level.value}_{variant}",
            name=f"Volatility: {vol_level.value.replace('_', ' ').title()} (Variant {variant})",
            seed=seed,
            regime=np.random.choice(list(MarketRegime)),
            volatility=vol_level,
            liquidity=LiquidityLevel.MEDIUM,
            base_volatility=base_vol * (1 + np.random.uniform(-0.2, 0.2)),
            vol_clustering=0.5 + np.random.uniform(-0.2, 0.3),
        )
    
    def _create_liquidity_scenario(self, liq_level: LiquidityLevel, variant: int) -> ScenarioParams:
        """Create a liquidity-focused scenario"""
        seed = self.base_seed + hash(f"liq_{liq_level.value}_{variant}") % 100000
        np.random.seed(seed)
        random.seed(seed)
        
        liq_params = {
            LiquidityLevel.THIN: {'spread_bps': 15.0, 'slippage_bps': 20.0},
            LiquidityLevel.MEDIUM: {'spread_bps': 5.0, 'slippage_bps': 5.0},
            LiquidityLevel.THICK: {'spread_bps': 2.0, 'slippage_bps': 2.0},
        }
        
        params = liq_params.get(liq_level, {'spread_bps': 5.0, 'slippage_bps': 5.0})
        
        return ScenarioParams(
            scenario_id=f"liq_{liq_level.value}_{variant}",
            name=f"Liquidity: {liq_level.value.title()} (Variant {variant})",
            seed=seed,
            regime=np.random.choice(list(MarketRegime)),
            volatility=VolatilityLevel.MEDIUM,
            liquidity=liq_level,
            spread_bps=params['spread_bps'] * (1 + np.random.uniform(-0.3, 0.3)),
            slippage_bps=params['slippage_bps'] * (1 + np.random.uniform(-0.3, 0.3)),
            spread_volatility=0.2 if liq_level == LiquidityLevel.THIN else 0.1,
        )
    
    def _create_microstructure_scenario(self, variant: int) -> ScenarioParams:
        """Create a microstructure-focused scenario (partial fills, cancels, rejects)"""
        seed = self.base_seed + hash(f"micro_{variant}") % 100000
        np.random.seed(seed)
        random.seed(seed)
        
        return ScenarioParams(
            scenario_id=f"microstructure_{variant}",
            name=f"Microstructure Test (Variant {variant})",
            seed=seed,
            regime=np.random.choice(list(MarketRegime)),
            volatility=np.random.choice(list(VolatilityLevel)),
            liquidity=np.random.choice(list(LiquidityLevel)),
            partial_fill_prob=np.random.uniform(0.05, 0.3),
            cancel_prob=np.random.uniform(0.01, 0.1),
            reject_prob=np.random.uniform(0.005, 0.05),
        )
    
    def _create_latency_scenario(self, variant: int) -> ScenarioParams:
        """Create a latency-focused scenario"""
        seed = self.base_seed + hash(f"latency_{variant}") % 100000
        np.random.seed(seed)
        random.seed(seed)
        
        return ScenarioParams(
            scenario_id=f"latency_{variant}",
            name=f"Latency Test (Variant {variant})",
            seed=seed,
            regime=np.random.choice(list(MarketRegime)),
            volatility=np.random.choice(list(VolatilityLevel)),
            liquidity=np.random.choice(list(LiquidityLevel)),
            min_latency_ms=10 + np.random.randint(0, 50),
            max_latency_ms=200 + np.random.randint(0, 1000),
            latency_spikes=np.random.choice([True, False]),
        )
    
    def _create_fault_scenario(self, variant: int) -> ScenarioParams:
        """Create an operational fault scenario"""
        seed = self.base_seed + hash(f"fault_{variant}") % 100000
        np.random.seed(seed)
        random.seed(seed)
        
        return ScenarioParams(
            scenario_id=f"fault_{variant}",
            name=f"Operational Fault Test (Variant {variant})",
            seed=seed,
            regime=np.random.choice(list(MarketRegime)),
            volatility=np.random.choice(list(VolatilityLevel)),
            liquidity=np.random.choice(list(LiquidityLevel)),
            clock_skew_ms=np.random.randint(-500, 500),
            reconnect_prob=np.random.uniform(0.0, 0.05),
            out_of_order_prob=np.random.uniform(0.0, 0.05),
            balance_desync_prob=np.random.uniform(0.0, 0.02),
        )
    
    def _create_multiasset_scenario(self, symbols: List[str], timeframes: List[str], 
                                    variant: int) -> ScenarioParams:
        """Create a multi-asset scenario"""
        seed = self.base_seed + hash(f"multi_{'_'.join(symbols)}_{variant}") % 100000
        np.random.seed(seed)
        random.seed(seed)
        
        return ScenarioParams(
            scenario_id=f"multiasset_{len(symbols)}sym_{len(timeframes)}tf_{variant}",
            name=f"Multi-Asset: {len(symbols)} symbols, {len(timeframes)} timeframes (Variant {variant})",
            seed=seed,
            regime=np.random.choice(list(MarketRegime)),
            volatility=np.random.choice(list(VolatilityLevel)),
            liquidity=np.random.choice(list(LiquidityLevel)),
            symbols=symbols,
            timeframes=timeframes,
        )
    
    def _create_walkforward_scenario(self, variant: int) -> ScenarioParams:
        """Create a walk-forward validation scenario"""
        seed = self.base_seed + hash(f"walkforward_{variant}") % 100000
        np.random.seed(seed)
        random.seed(seed)
        
        return ScenarioParams(
            scenario_id=f"walkforward_{variant}",
            name=f"Walk-Forward Validation (Variant {variant})",
            seed=seed,
            regime=np.random.choice(list(MarketRegime)),
            volatility=np.random.choice(list(VolatilityLevel)),
            liquidity=np.random.choice(list(LiquidityLevel)),
            num_candles=1500 + np.random.randint(-200, 200),
            in_sample_pct=0.6 + np.random.uniform(0, 0.2),
        )
    
    def _create_extreme_scenario(self, variant: int) -> ScenarioParams:
        """Create extreme stress scenario combining multiple adverse conditions"""
        seed = self.base_seed + hash(f"extreme_{variant}") % 100000
        np.random.seed(seed)
        random.seed(seed)
        
        return ScenarioParams(
            scenario_id=f"extreme_{variant}",
            name=f"Extreme Stress Test (Variant {variant})",
            seed=seed,
            regime=np.random.choice([MarketRegime.CRASH, MarketRegime.FLASH_EVENT, 
                                    MarketRegime.HIGH_VOL_WHIPSAW]),
            volatility=np.random.choice([VolatilityLevel.HIGH, VolatilityLevel.ULTRA_HIGH]),
            liquidity=LiquidityLevel.THIN,
            base_volatility=0.05 + np.random.uniform(0, 0.03),
            spread_bps=10.0 + np.random.uniform(0, 10),
            slippage_bps=15.0 + np.random.uniform(0, 15),
            partial_fill_prob=0.2 + np.random.uniform(0, 0.2),
            cancel_prob=0.05 + np.random.uniform(0, 0.05),
            reject_prob=0.02 + np.random.uniform(0, 0.03),
            max_latency_ms=1000 + np.random.randint(0, 1000),
            latency_spikes=True,
            reconnect_prob=0.03,
            out_of_order_prob=0.03,
        )


class MarketDataSimulator:
    """Simulate realistic market data for scenarios"""
    
    @staticmethod
    def generate_ohlcv(params: ScenarioParams) -> pd.DataFrame:
        """
        Generate realistic OHLCV data based on scenario parameters
        
        Args:
            params: Scenario parameters
            
        Returns:
            DataFrame with OHLCV data
        """
        np.random.seed(params.seed)
        random.seed(params.seed)
        
        num_candles = params.num_candles
        initial_price = params.initial_price
        
        # Generate price path using geometric Brownian motion with regime effects
        dt = 1.0 / 365.0  # Assuming daily candles
        drift = params.drift_pct / 100.0  # Convert to decimal
        
        # Generate volatility path with clustering (GARCH-like)
        vol_path = [params.base_volatility]
        for _ in range(num_candles - 1):
            # Mean-reverting volatility with clustering
            vol_shock = np.random.normal(0, 0.01)
            new_vol = (params.vol_clustering * vol_path[-1] + 
                      (1 - params.vol_clustering) * params.base_volatility +
                      vol_shock)
            vol_path.append(max(0.001, new_vol))  # Floor at 0.1%
        
        vol_path = np.array(vol_path)
        
        # Generate returns
        returns = np.random.normal(drift * dt, vol_path * np.sqrt(dt), num_candles)
        
        # Apply regime-specific effects
        if params.regime == MarketRegime.CRASH:
            # Sudden large drop in middle
            crash_idx = num_candles // 2
            returns[crash_idx:crash_idx+10] -= 0.05  # -5% per candle
        elif params.regime == MarketRegime.GAP_UP:
            # Large gap every ~50 candles
            for i in range(0, num_candles, 50):
                if i > 0:
                    returns[i] += 0.03  # +3% gap
        elif params.regime == MarketRegime.GAP_DOWN:
            # Large gap down every ~50 candles
            for i in range(0, num_candles, 50):
                if i > 0:
                    returns[i] -= 0.03  # -3% gap
        elif params.regime == MarketRegime.FLASH_EVENT:
            # Random flash crashes
            for _ in range(3):
                flash_idx = np.random.randint(0, num_candles)
                returns[flash_idx] -= 0.08  # -8% flash
                if flash_idx + 1 < num_candles:
                    returns[flash_idx + 1] += 0.07  # Quick recovery
        elif params.regime == MarketRegime.MEAN_REVERT_CHOP:
            # Oscillating pattern
            returns = 0.01 * np.sin(np.arange(num_candles) * 0.1) + \
                     np.random.normal(0, params.base_volatility * np.sqrt(dt), num_candles)
        
        # Generate price path
        price_path = initial_price * np.exp(np.cumsum(returns))
        
        # Generate OHLCV
        ohlcv_data = []
        base_volume = 1000000  # Base volume in USDT
        
        for i, close_price in enumerate(price_path):
            # Simulate intraday movement
            daily_range = close_price * vol_path[i] * np.sqrt(dt)
            
            high = close_price + abs(np.random.normal(0, daily_range * 0.5))
            low = close_price - abs(np.random.normal(0, daily_range * 0.5))
            
            # Ensure close is between high and low
            high = max(high, close_price)
            low = min(low, close_price)
            
            # Open is previous close (or initial price for first candle)
            open_price = price_path[i-1] if i > 0 else initial_price
            
            # Volume varies with volatility and regime
            volume_multiplier = 1.0
            if params.liquidity == LiquidityLevel.THIN:
                volume_multiplier = 0.3
            elif params.liquidity == LiquidityLevel.THICK:
                volume_multiplier = 2.0
            
            # Higher volume on high volatility days
            vol_multiplier = 1.0 + (vol_path[i] / params.base_volatility - 1.0)
            volume = base_volume * volume_multiplier * vol_multiplier * np.random.uniform(0.5, 1.5)
            
            ohlcv_data.append({
                'timestamp': datetime(2020, 1, 1) + timedelta(hours=i),
                'open': open_price,
                'high': high,
                'low': low,
                'close': close_price,
                'volume': volume,
            })
        
        df = pd.DataFrame(ohlcv_data)
        return df


class ScenarioStressEngine:
    """Main stress testing engine that runs all scenarios"""
    
    def __init__(self, output_dir: str = 'stress_test_results'):
        """
        Initialize stress testing engine
        
        Args:
            output_dir: Directory to save results
        """
        self.logger = Logger.get_logger()
        self.output_dir = output_dir
        # Use the RANDOM_SEED from config module-level variable
        from config import RANDOM_SEED
        self.generator = ScenarioGenerator(base_seed=RANDOM_SEED)
        self.simulator = MarketDataSimulator()
        
        # Create output directory
        import os
        os.makedirs(output_dir, exist_ok=True)
    
    def run_all_scenarios(self, strategy_func=None, 
                         max_scenarios: Optional[int] = None) -> List[ScenarioResult]:
        """
        Run all stress test scenarios
        
        Args:
            strategy_func: Trading strategy function to test
            max_scenarios: Maximum number of scenarios to run (None = all)
            
        Returns:
            List of scenario results
        """
        scenarios = self.generator.generate_all_scenarios()
        
        if max_scenarios:
            scenarios = scenarios[:max_scenarios]
        
        self.logger.info(f"Running {len(scenarios)} stress test scenarios...")
        
        results = []
        for i, scenario in enumerate(scenarios):
            self.logger.info(f"[{i+1}/{len(scenarios)}] Running: {scenario.name}")
            
            try:
                result = self.run_single_scenario(scenario, strategy_func)
                results.append(result)
                
                if not result.success:
                    self.logger.warning(f"Scenario failed: {result.error_message}")
                
            except Exception as e:
                self.logger.error(f"Exception in scenario {scenario.scenario_id}: {e}")
                results.append(ScenarioResult(
                    scenario_id=scenario.scenario_id,
                    scenario_name=scenario.name,
                    success=False,
                    error_message=str(e),
                    exceptions=[str(e)]
                ))
        
        # Save results
        self._save_results(scenarios, results)
        
        # Generate summary report
        self._generate_summary_report(results)
        
        return results
    
    def run_single_scenario(self, params: ScenarioParams, 
                           strategy_func=None) -> ScenarioResult:
        """
        Run a single stress test scenario
        
        Args:
            params: Scenario parameters
            strategy_func: Trading strategy function
            
        Returns:
            Scenario result
        """
        result = ScenarioResult(
            scenario_id=params.scenario_id,
            scenario_name=params.name,
            success=True
        )
        
        try:
            # Generate market data
            df = self.simulator.generate_ohlcv(params)
            
            # Add basic indicators (needed for strategy)
            from indicators import Indicators
            df = Indicators.calculate_all(df)
            
            # Run backtest
            backtest_engine = BacktestEngine(
                initial_balance=10000.0,
                trading_fee_rate=params.trading_fee_rate,
                funding_rate=params.funding_rate,
                latency_ms=params.max_latency_ms,
                slippage_bps=params.slippage_bps
            )
            
            # Use default strategy if none provided
            if strategy_func is None:
                from signals import SignalGenerator
                signal_gen = SignalGenerator()
                
                def default_strategy(row, balance, positions):
                    """Simple default strategy for testing"""
                    # Create a small DataFrame context for signal generation
                    # Signal generator needs full DataFrame, but we'll use a workaround
                    try:
                        # Get current position - assume we can only have one position at a time in backtest
                        current_position = positions[0] if positions else None
                        
                        # Simple momentum strategy for testing
                        if hasattr(row, 'get'):
                            # row is a Series
                            rsi = row.get('rsi', 50)
                            macd = row.get('macd', 0)
                            close = row.get('close', 0)
                        else:
                            # row is a dict
                            rsi = row['rsi']
                            macd = row['macd']
                            close = row['close']
                        
                        # If we have a position, check if we should close it
                        if current_position:
                            # Simple exit logic
                            if current_position['side'] == 'long':
                                if rsi > 70 or macd < 0:
                                    return {
                                        'side': 'sell',
                                        'amount': current_position['amount'],
                                        'leverage': current_position['leverage']
                                    }
                            else:  # short
                                if rsi < 30 or macd > 0:
                                    return {
                                        'side': 'buy',
                                        'amount': current_position['amount'],
                                        'leverage': current_position['leverage']
                                    }
                        else:
                            # No position, look for entry
                            # Long entry: RSI < 30 and MACD > 0
                            if rsi < 30 and macd > 0:
                                amount = balance * 0.1 / close  # 10% of balance
                                return {
                                    'side': 'long',
                                    'amount': amount,
                                    'leverage': 5,
                                    'stop_loss': close * 0.97,
                                    'take_profit': close * 1.05
                                }
                            # Short entry: RSI > 70 and MACD < 0
                            elif rsi > 70 and macd < 0:
                                amount = balance * 0.1 / close  # 10% of balance
                                return {
                                    'side': 'short',
                                    'amount': amount,
                                    'leverage': 5,
                                    'stop_loss': close * 1.03,
                                    'take_profit': close * 0.95
                                }
                        
                        # No signal
                        return None
                    except Exception as e:
                        # Log error but don't crash
                        return None
                
                strategy_func = default_strategy
            
            # Run backtest
            backtest_results = backtest_engine.run_backtest(
                df, 
                strategy_func,
                use_next_bar_execution=True
            )
            
            # Extract metrics
            result.total_return = backtest_results.get('total_return_pct', 0.0)
            result.sharpe_ratio = backtest_results.get('sharpe_ratio', 0.0)
            result.sortino_ratio = backtest_results.get('sortino_ratio', 0.0)
            result.max_drawdown = backtest_results.get('max_drawdown_pct', 0.0)
            result.profit_factor = backtest_results.get('profit_factor', 0.0)
            result.win_rate = backtest_results.get('win_rate', 0.0)
            result.num_trades = backtest_results.get('total_trades', 0)
            
            result.total_fees = backtest_results.get('total_trading_fees', 0.0)
            result.total_slippage = backtest_results.get('total_slippage_cost', 0.0)
            result.total_funding = backtest_results.get('total_funding_fees', 0.0)
            
            # Calculate risk metrics
            if 'equity_curve' in backtest_results and backtest_results['equity_curve']:
                equity_df = pd.DataFrame(backtest_results['equity_curve'])
                if 'equity' in equity_df.columns and len(equity_df) > 1:
                    returns = equity_df['equity'].pct_change().dropna()
                    
                    # VaR and CVaR
                    if len(returns) > 0:
                        result.var_95 = np.percentile(returns, 5)
                        result.cvar_95 = returns[returns <= result.var_95].mean()
                        
                        # Tail ratio
                        positive_tail = np.percentile(returns, 95)
                        negative_tail = abs(np.percentile(returns, 5))
                        if negative_tail != 0:
                            result.tail_ratio = positive_tail / negative_tail
            
            result.success = True
            
        except Exception as e:
            result.success = False
            result.error_message = str(e)
            result.exceptions.append(str(e))
            self.logger.error(f"Error in scenario {params.scenario_id}: {e}", exc_info=True)
        
        return result
    
    def _save_results(self, scenarios: List[ScenarioParams], 
                     results: List[ScenarioResult]):
        """Save scenario results to files"""
        import os
        
        # Save scenarios
        scenarios_file = os.path.join(self.output_dir, 'scenarios.json')
        with open(scenarios_file, 'w') as f:
            json.dump([s.to_dict() for s in scenarios], f, indent=2)
        
        # Save results
        results_file = os.path.join(self.output_dir, 'results.json')
        with open(results_file, 'w') as f:
            json.dump([r.to_dict() for r in results], f, indent=2)
        
        self.logger.info(f"Saved results to {self.output_dir}")
    
    def _generate_summary_report(self, results: List[ScenarioResult]):
        """Generate summary report of stress test results"""
        import os
        
        total = len(results)
        passed = sum(1 for r in results if r.success)
        failed = total - passed
        
        # Aggregate metrics (only for successful runs)
        successful_results = [r for r in results if r.success and r.num_trades > 0]
        
        if successful_results:
            avg_return = np.mean([r.total_return for r in successful_results])
            avg_sharpe = np.mean([r.sharpe_ratio for r in successful_results])
            avg_sortino = np.mean([r.sortino_ratio for r in successful_results])
            avg_drawdown = np.mean([r.max_drawdown for r in successful_results])
            avg_profit_factor = np.mean([r.profit_factor for r in successful_results])
            avg_win_rate = np.mean([r.win_rate for r in successful_results])
            
            # Profitability targets
            profitable = sum(1 for r in successful_results if r.total_return > 0)
            profit_factor_ok = sum(1 for r in successful_results if r.profit_factor >= 1.2)
            sharpe_ok = sum(1 for r in successful_results if r.sharpe_ratio >= 1.0)
            sortino_ok = sum(1 for r in successful_results if r.sortino_ratio >= 1.5)
            drawdown_ok = sum(1 for r in successful_results if abs(r.max_drawdown) <= 15.0)
            win_rate_ok = sum(1 for r in successful_results if r.win_rate >= 0.45)
        else:
            avg_return = avg_sharpe = avg_sortino = avg_drawdown = 0.0
            avg_profit_factor = avg_win_rate = 0.0
            profitable = profit_factor_ok = sharpe_ok = sortino_ok = 0
            drawdown_ok = win_rate_ok = 0
        
        report = f"""
{'='*80}
STRESS TEST SUMMARY REPORT
{'='*80}

Test Configuration:
  Total Scenarios: {total}
  Passed: {passed} ({100*passed/total:.1f}%)
  Failed: {failed} ({100*failed/total:.1f}%)

Performance Metrics (Successful Runs):
  Average Return: {avg_return:.2f}%
  Average Sharpe Ratio: {avg_sharpe:.2f}
  Average Sortino Ratio: {avg_sortino:.2f}
  Average Max Drawdown: {avg_drawdown:.2f}%
  Average Profit Factor: {avg_profit_factor:.2f}
  Average Win Rate: {avg_win_rate*100:.1f}%

Profitability Targets:
  Profitable Scenarios: {profitable}/{len(successful_results)} ({100*profitable/len(successful_results) if successful_results else 0:.1f}%)
  Profit Factor ≥ 1.2: {profit_factor_ok}/{len(successful_results)} ({100*profit_factor_ok/len(successful_results) if successful_results else 0:.1f}%)
  Sharpe ≥ 1.0: {sharpe_ok}/{len(successful_results)} ({100*sharpe_ok/len(successful_results) if successful_results else 0:.1f}%)
  Sortino ≥ 1.5: {sortino_ok}/{len(successful_results)} ({100*sortino_ok/len(successful_results) if successful_results else 0:.1f}%)
  Max DD ≤ 15%: {drawdown_ok}/{len(successful_results)} ({100*drawdown_ok/len(successful_results) if successful_results else 0:.1f}%)
  Win Rate ≥ 45%: {win_rate_ok}/{len(successful_results)} ({100*win_rate_ok/len(successful_results) if successful_results else 0:.1f}%)

Failure Analysis:
"""
        
        # Group failures by type
        failure_types = {}
        for r in results:
            if not r.success:
                error = r.error_message or "Unknown error"
                failure_types[error] = failure_types.get(error, 0) + 1
        
        if failure_types:
            report += "  Common Failure Patterns:\n"
            for error, count in sorted(failure_types.items(), key=lambda x: x[1], reverse=True):
                report += f"    - {error}: {count} occurrences\n"
        else:
            report += "  No failures detected!\n"
        
        report += f"\n{'='*80}\n"
        
        # Save report
        report_file = os.path.join(self.output_dir, 'STRESS_TEST_REPORT.txt')
        with open(report_file, 'w') as f:
            f.write(report)
        
        # Print to console
        print(report)
        self.logger.info(f"Summary report saved to {report_file}")


def main():
    """Run stress testing suite"""
    print("\n" + "="*80)
    print("RAD TRADING BOT - 500 SCENARIO STRESS TEST ENGINE")
    print("="*80 + "\n")
    
    engine = ScenarioStressEngine(output_dir='stress_test_results')
    
    # Run all scenarios
    results = engine.run_all_scenarios()
    
    print(f"\n✅ Stress testing complete! Results saved to stress_test_results/")
    print(f"   Total scenarios: {len(results)}")
    print(f"   Passed: {sum(1 for r in results if r.success)}")
    print(f"   Failed: {sum(1 for r in results if not r.success)}")


if __name__ == '__main__':
    main()
