# Example: Backtest simulation (dry run without real trading)
"""
This script demonstrates how to test the bot logic without actually trading.
It simulates market conditions and trading decisions.
"""

import sys
from datetime import datetime
from config import Config
from logger import Logger
from indicators import Indicators
from signals import SignalGenerator
from risk_manager import RiskManager
from ml_model import MLModel

class BacktestSimulator:
    """Simulate trading without executing real orders"""
    
    def __init__(self):
        self.logger = Logger.setup('INFO', 'logs/backtest.log')
        self.signal_generator = SignalGenerator()
        self.risk_manager = RiskManager(
            Config.MAX_POSITION_SIZE,
            Config.RISK_PER_TRADE,
            Config.MAX_OPEN_POSITIONS
        )
        self.ml_model = MLModel('models/backtest_model.pkl')
        
        # Simulated account
        self.balance = 10000  # Start with $10k
        self.positions = []
        self.trades_history = []
    
    def simulate_market_data(self):
        """Generate sample market data for testing"""
        # In a real backtest, you would load historical data
        # For this example, we'll create a simple uptrend
        import random
        
        base_price = 100
        ohlcv_data = []
        
        for i in range(100):
            # Simulate price movement with trend and noise
            trend = i * 0.1
            noise = random.uniform(-2, 2)
            close = base_price + trend + noise
            high = close + random.uniform(0, 1)
            low = close - random.uniform(0, 1)
            open_price = close + random.uniform(-0.5, 0.5)
            volume = random.uniform(900, 1100)
            
            ohlcv_data.append([
                i * 60000,  # timestamp
                open_price,
                high,
                low,
                close,
                volume
            ])
        
        return ohlcv_data
    
    def simulate_trade(self, signal, entry_price, position_size):
        """Simulate opening a position"""
        position = {
            'signal': signal,
            'entry_price': entry_price,
            'size': position_size,
            'entry_time': datetime.now()
        }
        self.positions.append(position)
        self.logger.info(f"Simulated {signal} position: {position_size:.4f} @ ${entry_price:.2f}")
    
    def simulate_exit(self, position, exit_price):
        """Simulate closing a position"""
        entry_price = position['entry_price']
        size = position['size']
        signal = position['signal']
        
        if signal == 'BUY':
            pnl = ((exit_price - entry_price) / entry_price) * Config.LEVERAGE
        else:
            pnl = ((entry_price - exit_price) / entry_price) * Config.LEVERAGE
        
        profit = self.balance * pnl * Config.RISK_PER_TRADE
        self.balance += profit
        
        trade = {
            'entry_price': entry_price,
            'exit_price': exit_price,
            'pnl': pnl,
            'profit': profit,
            'exit_time': datetime.now()
        }
        self.trades_history.append(trade)
        
        self.logger.info(f"Simulated exit: P/L {pnl:.2%}, Profit ${profit:.2f}, Balance: ${self.balance:.2f}")
        
        return pnl
    
    def run_backtest(self):
        """Run a simple backtest simulation"""
        self.logger.info("="*60)
        self.logger.info("Starting Backtest Simulation")
        self.logger.info("="*60)
        self.logger.info(f"Initial Balance: ${self.balance:.2f}")
        
        # Generate sample data
        ohlcv_data = self.simulate_market_data()
        
        # Calculate indicators
        df = Indicators.calculate_all(ohlcv_data)
        if df.empty:
            self.logger.error("Failed to calculate indicators")
            return
        
        # Generate signal
        signal, confidence, reasons = self.signal_generator.generate_signal(df)
        
        self.logger.info(f"\nSignal Analysis:")
        self.logger.info(f"  Signal: {signal}")
        self.logger.info(f"  Confidence: {confidence:.2%}")
        self.logger.info(f"  Reasons: {reasons}")
        
        # Simulate trading decision
        if signal != 'HOLD' and confidence >= 0.6:
            indicators = Indicators.get_latest_indicators(df)
            entry_price = indicators['close']
            
            # Calculate position size
            stop_loss_pct = self.risk_manager.calculate_stop_loss_percentage(
                indicators.get('bb_width', 0.03)
            )
            
            if signal == 'BUY':
                stop_loss_price = entry_price * (1 - stop_loss_pct)
            else:
                stop_loss_price = entry_price * (1 + stop_loss_pct)
            
            position_size = self.risk_manager.calculate_position_size(
                self.balance, entry_price, stop_loss_price, Config.LEVERAGE
            )
            
            # Simulate trade
            self.simulate_trade(signal, entry_price, position_size)
            
            # Simulate some price movement
            import random
            if signal == 'BUY':
                exit_price = entry_price * (1 + random.uniform(0.01, 0.05))
            else:
                exit_price = entry_price * (1 - random.uniform(0.01, 0.05))
            
            # Simulate exit
            if self.positions:
                position = self.positions.pop(0)
                pnl = self.simulate_exit(position, exit_price)
                
                # Record for ML model
                self.ml_model.record_outcome(indicators, signal, pnl)
        
        # Show results
        self.logger.info("\n" + "="*60)
        self.logger.info("Backtest Results")
        self.logger.info("="*60)
        self.logger.info(f"Final Balance: ${self.balance:.2f}")
        self.logger.info(f"Total P/L: ${self.balance - 10000:.2f}")
        self.logger.info(f"Return: {((self.balance - 10000) / 10000) * 100:.2f}%")
        self.logger.info(f"Trades Executed: {len(self.trades_history)}")
        
        if self.trades_history:
            avg_pnl = sum(t['pnl'] for t in self.trades_history) / len(self.trades_history)
            self.logger.info(f"Average Trade P/L: {avg_pnl:.2%}")

def main():
    """Run the backtest simulation"""
    print("\n" + "="*60)
    print("KuCoin Trading Bot - Backtest Simulation")
    print("="*60)
    print("\nThis is a DRY RUN - No real trades will be executed")
    print("Testing bot logic with simulated market data\n")
    
    try:
        simulator = BacktestSimulator()
        simulator.run_backtest()
        
        print("\n✓ Backtest simulation complete")
        print("Check logs/backtest.log for details")
        
    except Exception as e:
        print(f"\n✗ Simulation error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
