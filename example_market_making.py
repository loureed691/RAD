"""
Example: Basic Avellaneda-Stoikov Market Making

This script demonstrates how to use the market making components
in a simple trading loop.
"""
import time
import numpy as np
from datetime import datetime

from avellaneda_stoikov import AvellanedaStoikovMarketMaker
from delta_hedger import DeltaHedger
from market_microstructure_2026 import MarketMicrostructure2026


def simulate_market_data():
    """Simulate market data for demonstration"""
    # In real use, fetch from exchange
    base_price = 50000.0
    price_change = np.random.randn() * 50
    
    return {
        'mid_price': base_price + price_change,
        'bid': base_price + price_change - 5,
        'ask': base_price + price_change + 5,
        'volatility': 0.5,  # 50% annualized
        'orderbook': {
            'bids': [[base_price - i*5, 10.0] for i in range(1, 11)],
            'asks': [[base_price + i*5, 10.0] for i in range(1, 11)]
        },
        'trades': [
            {'price': base_price + np.random.randn()*10, 'amount': np.random.rand(), 'side': 'buy'}
            for _ in range(20)
        ]
    }


def main():
    """Main market making loop"""
    print("=" * 60)
    print("Avellaneda-Stoikov Market Making Example")
    print("=" * 60)
    print()
    
    # 1. Initialize components
    print("Initializing components...")
    
    market_maker = AvellanedaStoikovMarketMaker(
        risk_aversion=0.1,        # Balanced risk
        terminal_time=1.0,
        target_inventory=0.0,     # Market neutral
        max_inventory=5.0,        # Max 5 units long/short
        min_spread=0.0001,        # 0.01% minimum
        max_spread=0.005          # 0.5% maximum
    )
    
    hedger = DeltaHedger(
        hedge_threshold=3.0,      # Hedge when |inventory| > 3
        target_delta=0.0,
        hedge_ratio=0.8,          # Hedge 80% of excess
        max_hedge_latency=60.0
    )
    
    microstructure = MarketMicrostructure2026()
    
    # Simulated state
    current_inventory = 0.0
    
    print("✅ Components initialized")
    print()
    
    # 2. Run market making loop (simulate 10 iterations)
    print("Starting market making loop...")
    print()
    
    for iteration in range(10):
        print(f"--- Iteration {iteration + 1} ---")
        
        # Fetch market data (simulated)
        data = simulate_market_data()
        
        # Get microstructure signals
        signals = microstructure.get_microstructure_signals(
            orderbook=data['orderbook'],
            trades=data['trades']
        )
        
        print(f"📊 Market: ${data['mid_price']:.2f}")
        print(f"   Microprice: ${signals['microprice']:.2f}")
        print(f"   Queue imbalance: {signals['queue_imbalance']:.3f}")
        print(f"   Kyle's λ: {signals['kyle_lambda']:.6f}")
        
        # Update market maker
        market_maker.update_market_data(
            mid_price=data['mid_price'],
            volatility=data['volatility'],
            inventory=current_inventory,
            microprice=signals['microprice'],
            order_flow_imbalance=signals['queue_imbalance'],
            kyle_lambda=signals['kyle_lambda']
        )
        
        # Get optimal quotes
        bid_price, ask_price = market_maker.compute_quotes()
        
        if bid_price and ask_price:
            spread = ask_price - bid_price
            spread_pct = (spread / data['mid_price']) * 100
            
            print(f"💱 Quotes:")
            print(f"   Bid: ${bid_price:.2f}")
            print(f"   Ask: ${ask_price:.2f}")
            print(f"   Spread: ${spread:.2f} ({spread_pct:.3f}%)")
            
            # Simulate random fill (simplified)
            if np.random.random() < 0.3:  # 30% fill probability
                side = np.random.choice(['buy', 'sell'])
                fill_price = bid_price if side == 'buy' else ask_price
                fill_size = 0.1
                
                if side == 'buy':
                    current_inventory += fill_size
                else:
                    current_inventory -= fill_size
                
                print(f"   ✅ Filled: {side} {fill_size} @ ${fill_price:.2f}")
            else:
                print(f"   ⏳ No fill")
        
        print(f"📦 Inventory: {current_inventory:.2f}")
        
        # Check hedging
        hedger.update_inventory(current_inventory)
        if hedger.should_hedge():
            hedge_rec = hedger.get_hedge_recommendation(
                current_price=data['mid_price'],
                microprice=signals['microprice']
            )
            
            print(f"🛡️ Hedge recommendation:")
            print(f"   {hedge_rec['side'].upper()} {hedge_rec['hedge_size']:.2f}")
            print(f"   Urgency: {hedge_rec['urgency']}")
            print(f"   Strategy: {hedge_rec['strategy']}")
            
            # Simulate hedge execution
            if hedge_rec['side'] == 'buy':
                current_inventory += hedge_rec['hedge_size']
            else:
                current_inventory -= hedge_rec['hedge_size']
            
            hedger.record_hedge(
                hedge_rec['hedge_size'],
                hedge_rec['side'],
                data['mid_price'],
                hedge_rec['estimated_cost']
            )
            
            print(f"   ✅ Hedge executed, new inventory: {current_inventory:.2f}")
        
        print()
        time.sleep(0.5)  # Pause for readability
    
    # 3. Show summary
    print("=" * 60)
    print("Summary")
    print("=" * 60)
    
    mm_metrics = market_maker.get_metrics()
    hedge_metrics = hedger.get_hedge_metrics()
    
    print(f"Market Maker:")
    print(f"   Quotes generated: {mm_metrics['quotes_generated']}")
    print(f"   Final inventory: {mm_metrics['inventory']:.2f}")
    print(f"   Inventory utilization: {mm_metrics['inventory_utilization']*100:.1f}%")
    print()
    
    print(f"Hedger:")
    print(f"   Total hedges: {hedge_metrics['total_hedges']}")
    print(f"   Total hedge costs: ${hedge_metrics['total_hedge_costs']:.2f}")
    print(f"   Is hedged: {hedge_metrics['is_hedged']}")
    print()
    
    print("✅ Example complete!")


if __name__ == '__main__':
    main()
