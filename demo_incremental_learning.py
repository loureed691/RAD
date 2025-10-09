"""
Demo script showing incremental/online learning in action
Simulates a trading session with the incremental model learning in real-time
"""
import time
import random
from incremental_ml_model import IncrementalMLModel

def generate_sample_indicators(price_trend='neutral'):
    """Generate sample indicators based on market trend"""
    base_price = 100
    
    if price_trend == 'bullish':
        rsi = random.uniform(55, 75)
        macd = random.uniform(0.3, 0.8)
        momentum = random.uniform(0.01, 0.03)
        volume_ratio = random.uniform(1.2, 2.0)
    elif price_trend == 'bearish':
        rsi = random.uniform(25, 45)
        macd = random.uniform(-0.8, -0.3)
        momentum = random.uniform(-0.03, -0.01)
        volume_ratio = random.uniform(1.2, 2.0)
    else:  # neutral
        rsi = random.uniform(45, 55)
        macd = random.uniform(-0.2, 0.2)
        momentum = random.uniform(-0.01, 0.01)
        volume_ratio = random.uniform(0.8, 1.2)
    
    return {
        'rsi': rsi,
        'macd': macd,
        'macd_signal': macd - random.uniform(0.1, 0.2),
        'macd_diff': random.uniform(0.1, 0.3),
        'stoch_k': rsi + random.uniform(-5, 5),
        'stoch_d': rsi + random.uniform(-3, 3),
        'bb_width': random.uniform(0.03, 0.06),
        'volume_ratio': volume_ratio,
        'momentum': momentum,
        'roc': random.uniform(0.8, 1.2),
        'atr': random.uniform(2.0, 3.5),
        'close': base_price + random.uniform(-5, 5),
        'bb_high': base_price + 5,
        'bb_low': base_price - 5,
        'bb_mid': base_price,
        'ema_12': base_price + random.uniform(-2, 2),
        'ema_26': base_price + random.uniform(-3, 3),
        'sma_20': base_price + random.uniform(-2, 2),
        'sma_50': base_price + random.uniform(-4, 4)
    }

def simulate_trade_outcome(signal, market_trend):
    """Simulate trade outcome based on signal and actual market trend"""
    # BUY signals work well in bullish markets
    if signal == 'BUY':
        if market_trend == 'bullish':
            return random.uniform(0.01, 0.025)  # Good profit
        elif market_trend == 'bearish':
            return random.uniform(-0.02, -0.008)  # Loss
        else:
            return random.uniform(-0.005, 0.01)  # Small win or loss
    # SELL signals work well in bearish markets
    elif signal == 'SELL':
        if market_trend == 'bearish':
            return random.uniform(0.01, 0.025)  # Good profit
        elif market_trend == 'bullish':
            return random.uniform(-0.02, -0.008)  # Loss
        else:
            return random.uniform(-0.005, 0.01)  # Small win or loss
    else:  # HOLD
        return 0.0

def main():
    print("=" * 70)
    print("🔄 INCREMENTAL/ONLINE LEARNING DEMO")
    print("=" * 70)
    print("\nThis demo simulates a trading session where the model learns")
    print("continuously from each trade outcome in real-time.\n")
    
    # Initialize incremental model
    model = IncrementalMLModel('models/demo_incremental.pkl')
    
    # Simulate trading in different market conditions
    market_phases = [
        ('bullish', 15, '📈 BULLISH MARKET'),
        ('neutral', 10, '➡️  NEUTRAL MARKET'),
        ('bearish', 15, '📉 BEARISH MARKET'),
        ('bullish', 10, '📈 RECOVERY PHASE')
    ]
    
    trade_num = 0
    
    for phase_name, num_trades, phase_label in market_phases:
        print(f"\n{phase_label} ({num_trades} trades)")
        print("-" * 70)
        
        for i in range(num_trades):
            trade_num += 1
            
            # Generate indicators based on market phase
            indicators = generate_sample_indicators(phase_name)
            
            # Get model prediction
            signal, confidence = model.predict(indicators)
            
            # For demo purposes, force some trades initially to seed the model
            # After 10 trades, use the model's actual predictions
            if trade_num <= 10:
                # Seed the model with correct signals based on market trend
                if phase_name == 'bullish':
                    signal = 'BUY'
                elif phase_name == 'bearish':
                    signal = 'SELL'
                confidence = 0.5  # Use moderate confidence for seeding
            
            # Simulate trade execution and outcome
            if signal != 'HOLD' and confidence > 0.3:
                profit_loss = simulate_trade_outcome(signal, phase_name)
                
                # Model learns from this trade immediately!
                model.learn_one(indicators, signal, profit_loss)
                
                # Display results
                outcome = "✅ WIN" if profit_loss > 0.005 else ("❌ LOSS" if profit_loss < -0.005 else "➖ NEUTRAL")
                print(f"Trade #{trade_num:3d}: {signal:4s} @ {confidence:.2f} confidence → {profit_loss:+.2%} {outcome}")
            else:
                print(f"Trade #{trade_num:3d}: HOLD (low confidence: {confidence:.2f})")
            
            # Small delay for demo effect
            time.sleep(0.1)
        
        # Show performance metrics after each phase
        metrics = model.get_performance_metrics()
        print(f"\n📊 Phase Summary:")
        print(f"   Total Trades: {metrics['total_trades']}")
        print(f"   Win Rate: {metrics['win_rate']:.1%}")
        print(f"   Model Accuracy: {metrics['accuracy']:.1%}")
        print(f"   F1 Score: {metrics['f1_score']:.1%}")
        print(f"   Adaptive Threshold: {model.get_adaptive_confidence_threshold():.2f}")
    
    # Final summary
    print("\n" + "=" * 70)
    print("📊 FINAL RESULTS")
    print("=" * 70)
    
    final_metrics = model.get_performance_metrics()
    print(f"Total Trades Processed: {final_metrics['total_trades']}")
    print(f"Overall Win Rate: {final_metrics['win_rate']:.1%}")
    print(f"Model Accuracy: {final_metrics['accuracy']:.1%}")
    print(f"F1 Score: {final_metrics['f1_score']:.1%}")
    print(f"Precision: {final_metrics['precision']:.1%}")
    print(f"Recall: {final_metrics['recall']:.1%}")
    print(f"\nAverage Winning Trade: {final_metrics['avg_profit']:.2%}")
    print(f"Average Losing Trade: {final_metrics['avg_loss']:.2%}")
    
    if final_metrics['total_trades'] >= 20:
        kelly = model.get_kelly_fraction()
        print(f"\nKelly Criterion: {kelly:.1%} of capital per trade")
    
    print("\n✨ Key Benefit: The model adapted in real-time to changing market")
    print("   conditions without any manual retraining!")
    print("\n" + "=" * 70)

if __name__ == "__main__":
    main()
