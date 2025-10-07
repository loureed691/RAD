#!/usr/bin/env python3
"""
Demonstration of keyboard shutdown functionality
This script shows how the bot responds to Ctrl+C (SIGINT)
"""
import signal
import sys
import time

class ShutdownDemo:
    """Simple demo class to show keyboard interrupt handling"""
    
    def __init__(self):
        self.running = False
        # Register signal handlers just like the real bot
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        print("=" * 60)
        print("KEYBOARD SHUTDOWN DEMONSTRATION")
        print("=" * 60)
        print("This demo simulates the bot's keyboard shutdown handling.")
        print("Press Ctrl+C to trigger graceful shutdown.")
        print("=" * 60)
    
    def signal_handler(self, sig, frame):
        """Handle shutdown signals gracefully (mimics real bot)"""
        signal_name = 'SIGINT (Ctrl+C)' if sig == signal.SIGINT else f'SIGTERM ({sig})'
        print()
        print("=" * 60)
        print(f"🛑 Shutdown signal received: {signal_name}")
        print("=" * 60)
        print("⏳ Gracefully stopping bot...")
        print("   - Stopping trading cycle")
        print("   - Will complete current operations")
        print("   - Then proceed to shutdown")
        print("=" * 60)
        self.running = False
    
    def run_cycle(self):
        """Simulate a trading cycle"""
        print(f"[{time.strftime('%H:%M:%S')}] Running trading cycle...")
        time.sleep(1)
    
    def run(self):
        """Main loop (mimics real bot)"""
        self.running = True
        print()
        print("=" * 60)
        print("🚀 BOT STARTED (Demo Mode)")
        print("=" * 60)
        print("⏱️  Cycle interval: 2s")
        print("🔄 Running... (Press Ctrl+C to stop)")
        print("=" * 60)
        
        try:
            cycle_count = 0
            while self.running:
                try:
                    cycle_count += 1
                    print(f"\n--- Cycle {cycle_count} ---")
                    self.run_cycle()
                    
                    # Wait before next cycle
                    if self.running:  # Check if still running before sleeping
                        print(f"⏸️  Waiting 2s before next cycle...")
                        time.sleep(2)
                    
                except Exception as e:
                    print(f"❌ Error in trading cycle: {e}")
                    time.sleep(2)
        
        except KeyboardInterrupt:
            print()
            print("=" * 60)
            print("⌨️  Keyboard Interrupt (Ctrl+C) received")
            print("=" * 60)
            print("⏳ Initiating graceful shutdown...")
            print("=" * 60)
        
        finally:
            self.shutdown()
    
    def shutdown(self):
        """Clean shutdown (mimics real bot)"""
        print()
        print("=" * 60)
        print("🛑 SHUTTING DOWN BOT...")
        print("=" * 60)
        print("💾 Saving data...")
        time.sleep(0.5)
        print("✅ Data saved")
        print("=" * 60)
        print("✅ BOT SHUTDOWN COMPLETE")
        print("=" * 60)

def main():
    """Run the demonstration"""
    demo = ShutdownDemo()
    demo.run()

if __name__ == "__main__":
    main()
