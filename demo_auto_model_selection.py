"""
Demo script showing automatic model selection in action
Simulates trading with both models and shows automatic switching
"""
import time
import random
from ml_model import MLModel

def generate_sample_indicators(trend='neutral'):
    """Generate sample indicators based on market trend"""
    base_price = 100
    
    if trend == 'bullish':
        rsi = random.uniform(55, 75)
        macd = random.uniform(0.3, 0.8)
        momentum = random.uniform(0.01, 0.03)
        volume_ratio = random.uniform(1.2, 2.0)
    elif trend == 'bearish':
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
    """Simulate trade outcome based on signal and market trend"""
    if signal == 'BUY':
        if market_trend == 'bullish':
            return random.uniform(0.01, 0.025)
        elif market_trend == 'bearish':
            return random.uniform(-0.02, -0.008)
        else:
            return random.uniform(-0.005, 0.01)
    elif signal == 'SELL':
        if market_trend == 'bearish':
            return random.uniform(0.01, 0.025)
        elif market_trend == 'bullish':
            return random.uniform(-0.02, -0.008)
        else:
            return random.uniform(-0.005, 0.01)
    else:
        return 0.0

def main():
    print("=" * 70)
    print("🤖 AUTOMATIC MODEL SELECTION DEMO")
    print("=" * 70)
    print("\nThis demo shows the bot automatically selecting the best model")
    print("(batch vs incremental) based on real-time performance.\n")
    
    # Initialize model with auto-selection
    model = MLModel('models/demo_auto_select.pkl', auto_select_best=True)
    
    print("✓ Both batch and incremental models initialized")
    print("✓ Auto-selection enabled (will compare every hour)\n")
    
    # Seed both models with some initial trades
    print("Seeding models with initial trades...")
    sample_indicators = generate_sample_indicators('bullish')
    for i in range(10):
        profit = 0.01 + (i * 0.001)
        model.record_outcome(sample_indicators, 'BUY', profit)
    print(f"✓ Both models seeded with 10 profitable trades\n")
    
    # Simulate trades in different market conditions
    market_phases = [
        ('bullish', 20, '📈 BULLISH MARKET - Testing both models'),
        ('neutral', 15, '➡️  NEUTRAL MARKET - Models adapting'),
        ('bearish', 20, '📉 BEARISH MARKET - Observing performance'),
    ]
    
    trade_num = 0
    
    for phase_name, num_trades, phase_label in market_phases:
        print(f"\n{phase_label}")
        print("-" * 70)
        
        for i in range(num_trades):
            trade_num += 1
            
            # Generate indicators
            indicators = generate_sample_indicators(phase_name)
            
            # Get prediction
            signal, confidence = model.predict(indicators)
            
            # Simulate trade if confident enough
            if signal != 'HOLD' and confidence > 0.3:
                profit_loss = simulate_trade_outcome(signal, phase_name)
                
                # Record outcome (both models learn)
                model.record_outcome(indicators, signal, profit_loss)
                
                outcome = "✅" if profit_loss > 0.005 else ("❌" if profit_loss < -0.005 else "➖")
                current_model = "🔄 Incremental" if model.use_incremental else "📚 Batch"
                
                print(f"Trade #{trade_num:3d}: {signal:4s} @ {confidence:.2f} → {profit_loss:+.2%} {outcome} | Using: {current_model}")
            else:
                print(f"Trade #{trade_num:3d}: HOLD (low confidence: {confidence:.2f})")
            
            time.sleep(0.05)
        
        # Show current performance
        print(f"\n📊 Current Status:")
        print(f"   Batch Model    - Trades: {model.batch_metrics['total_trades']}, Win Rate: {model.batch_metrics['win_rate']:.1%}")
        print(f"   Incremental    - Trades: {model.incremental_metrics['total_trades']}, Win Rate: {model.incremental_metrics['win_rate']:.1%}")
        print(f"   Active Model: {'Incremental' if model.use_incremental else 'Batch'}")
    
    # Final summary
    print("\n" + "=" * 70)
    print("📊 FINAL PERFORMANCE COMPARISON")
    print("=" * 70)
    
    batch_score = (
        model.batch_metrics.get('win_rate', 0) * 0.4 +
        model.batch_metrics.get('accuracy', 0) * 0.3 +
        min(model.batch_metrics.get('avg_profit', 0) * 50, 1.0) * 0.3
    )
    
    incr_score = (
        model.incremental_metrics.get('win_rate', 0) * 0.4 +
        model.incremental_metrics.get('accuracy', 0) * 0.3 +
        min(model.incremental_metrics.get('avg_profit', 0) * 50, 1.0) * 0.3
    )
    
    print(f"\nBatch Model:")
    print(f"  Total Trades: {model.batch_metrics['total_trades']}")
    print(f"  Win Rate: {model.batch_metrics['win_rate']:.1%}")
    print(f"  Composite Score: {batch_score:.3f}")
    
    print(f"\nIncremental Model:")
    print(f"  Total Trades: {model.incremental_metrics['total_trades']}")
    print(f"  Win Rate: {model.incremental_metrics['win_rate']:.1%}")
    print(f"  Accuracy: {model.incremental_metrics.get('accuracy', 0):.1%}")
    print(f"  Composite Score: {incr_score:.3f}")
    
    winner = "Incremental" if incr_score > batch_score else "Batch"
    print(f"\n🏆 Better Performing Model: {winner}")
    print(f"\n✨ The system automatically selected the best model without manual intervention!")
    print("=" * 70)

if __name__ == "__main__":
    main()
