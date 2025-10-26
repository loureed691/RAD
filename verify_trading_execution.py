"""
Bot Log Trading Execution Verifier

This tool analyzes bot.log to verify that trading strategies and orders
are being executed correctly. It checks:
1. Order execution (buy/sell orders with proper parameters)
2. Risk management (stop loss, take profit settings)
3. Position monitoring and updates
4. Strategy execution quality
5. Trading performance metrics
"""

import re
import sys
from datetime import datetime, timedelta
from collections import defaultdict
from typing import Dict, List, Tuple, Optional


class OrderExecution:
    """Represents a single order execution"""
    
    def __init__(self, data: Dict):
        self.timestamp = data.get('timestamp')
        self.order_id = data.get('order_id')
        self.order_type = data.get('type')
        self.side = data.get('side')
        self.symbol = data.get('symbol')
        self.amount = data.get('amount')
        self.leverage = data.get('leverage')
        self.reference_price = data.get('reference_price')
        self.fill_price = data.get('fill_price')
        self.filled_amount = data.get('filled_amount')
        self.total_cost = data.get('total_cost')
        self.status = data.get('status')
        self.slippage = data.get('slippage')
        self.stop_loss = data.get('stop_loss')
        self.take_profit = data.get('take_profit')
        
    def is_valid(self) -> bool:
        """Check if order execution has all required fields"""
        required = [self.order_id, self.side, self.symbol, self.amount, 
                   self.fill_price, self.status]
        return all(x is not None for x in required)
    
    def has_risk_management(self) -> bool:
        """Check if order has stop loss and take profit"""
        return self.stop_loss is not None and self.take_profit is not None
    
    def is_successful(self) -> bool:
        """Check if order was successfully filled"""
        return self.status == 'closed' and self.filled_amount is not None


class PositionUpdate:
    """Represents a position monitoring update"""
    
    def __init__(self, data: Dict):
        self.timestamp = data.get('timestamp')
        self.symbol = data.get('symbol')
        self.entry_price = data.get('entry_price')
        self.current_price = data.get('current_price')
        self.amount = data.get('amount')
        self.leverage = data.get('leverage')
        self.pnl_percent = data.get('pnl_percent')
        self.pnl_amount = data.get('pnl_amount')
        self.stop_loss = data.get('stop_loss')
        self.take_profit = data.get('take_profit')
        self.status = data.get('status', 'open')
        

class TradingLogAnalyzer:
    """Analyzes bot.log for trading execution verification"""
    
    def __init__(self, log_file: str):
        self.log_file = log_file
        self.orders: List[OrderExecution] = []
        self.position_updates: List[PositionUpdate] = []
        self.errors: List[str] = []
        self.warnings: List[str] = []
        
    def parse_log(self):
        """Parse the log file and extract orders and position updates"""
        print(f"📖 Parsing log file: {self.log_file}")
        
        try:
            with open(self.log_file, 'r') as f:
                lines = f.readlines()
        except Exception as e:
            print(f"❌ Error reading log file: {e}")
            return False
        
        print(f"   Total lines: {len(lines)}")
        
        # Parse orders
        i = 0
        while i < len(lines):
            line = lines[i]
            
            # Look for order execution blocks
            if 'ORDER EXECUTED:' in line:
                order_data = self._parse_order_block(lines, i)
                if order_data:
                    order = OrderExecution(order_data)
                    self.orders.append(order)
                # Move to next line after parsing block
                i += 1
            
            # Look for position updates
            elif '--- Position:' in line and ('(LONG)' in line or '(SHORT)' in line):
                pos_data = self._parse_position_block(lines, i)
                if pos_data:
                    position = PositionUpdate(pos_data)
                    self.position_updates.append(position)
                i += 1
            else:
                i += 1
        
        print(f"   Found {len(self.orders)} order executions")
        print(f"   Found {len(self.position_updates)} position updates")
        return True
    
    def _parse_order_block(self, lines: List[str], start_idx: int) -> Optional[Dict]:
        """Parse an order execution block from the log"""
        order_data = {}
        
        # Get timestamp from the ORDER EXECUTED line
        timestamp_match = re.search(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})', lines[start_idx])
        if timestamp_match:
            order_data['timestamp'] = timestamp_match.group(1)
        
        # Get symbol from ORDER EXECUTED line
        symbol_match = re.search(r'ORDER EXECUTED: (.+)$', lines[start_idx])
        if symbol_match:
            order_data['symbol'] = symbol_match.group(1).strip()
        
        # Parse the next 20 lines for order details
        for i in range(start_idx + 1, min(start_idx + 20, len(lines))):
            line = lines[i]
            
            if 'Order ID:' in line:
                match = re.search(r'Order ID: (\d+)', line)
                if match:
                    order_data['order_id'] = match.group(1)
            
            elif 'Type:' in line and 'Order ID' not in line:
                match = re.search(r'Type: (\w+)', line)
                if match:
                    order_data['type'] = match.group(1)
            
            elif 'Side:' in line:
                match = re.search(r'Side: (\w+)', line)
                if match:
                    order_data['side'] = match.group(1)
            
            elif 'Amount:' in line and 'Filled Amount' not in line:
                match = re.search(r'Amount: ([\d.]+)', line)
                if match:
                    order_data['amount'] = float(match.group(1))
            
            elif 'Leverage:' in line:
                match = re.search(r'Leverage: ([\d.]+)x', line)
                if match:
                    order_data['leverage'] = float(match.group(1))
            
            elif 'Reference Price:' in line:
                match = re.search(r'Reference Price: ([\d.]+)', line)
                if match:
                    order_data['reference_price'] = float(match.group(1))
            
            elif 'Average Fill Price:' in line:
                match = re.search(r'Average Fill Price: ([\d.]+)', line)
                if match:
                    order_data['fill_price'] = float(match.group(1))
            
            elif 'Filled Amount:' in line:
                match = re.search(r'Filled Amount: ([\d.]+)', line)
                if match:
                    order_data['filled_amount'] = float(match.group(1))
            
            elif 'Total Cost:' in line:
                match = re.search(r'Total Cost: ([\d.]+)', line)
                if match:
                    order_data['total_cost'] = float(match.group(1))
            
            elif 'Status:' in line:
                match = re.search(r'Status: (\w+)', line)
                if match:
                    order_data['status'] = match.group(1)
            
            elif 'Slippage:' in line:
                match = re.search(r'Slippage: ([\d.]+)%', line)
                if match:
                    order_data['slippage'] = float(match.group(1))
            
            elif 'Stop Loss:' in line:
                match = re.search(r'Stop Loss: ([\d.]+)', line)
                if match:
                    order_data['stop_loss'] = float(match.group(1))
            
            elif 'Take Profit:' in line:
                match = re.search(r'Take Profit: ([\d.]+)', line)
                if match:
                    order_data['take_profit'] = float(match.group(1))
        
        return order_data if order_data else None
    
    def _parse_position_block(self, lines: List[str], start_idx: int) -> Optional[Dict]:
        """Parse a position update block from the log"""
        pos_data = {}
        
        # Get timestamp
        timestamp_match = re.search(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})', lines[start_idx])
        if timestamp_match:
            pos_data['timestamp'] = timestamp_match.group(1)
        
        # Get symbol from "Position: SYMBOL (LONG/SHORT)"
        symbol_match = re.search(r'Position: (.+?) \((LONG|SHORT)\)', lines[start_idx])
        if symbol_match:
            pos_data['symbol'] = symbol_match.group(1).strip()
            pos_data['side'] = symbol_match.group(2)
        
        # Parse the next 15 lines for position details
        for i in range(start_idx + 1, min(start_idx + 15, len(lines))):
            line = lines[i]
            
            if 'Entry Price:' in line:
                match = re.search(r'Entry Price: ([\d.]+)', line)
                if match:
                    pos_data['entry_price'] = float(match.group(1))
            
            elif 'Current Price:' in line:
                match = re.search(r'Current Price: ([\d.]+)', line)
                if match:
                    pos_data['current_price'] = float(match.group(1))
            
            elif 'Amount:' in line and 'contracts' in line:
                match = re.search(r'Amount: ([\d.]+)', line)
                if match:
                    pos_data['amount'] = float(match.group(1))
            
            elif 'Leverage:' in line:
                match = re.search(r'Leverage: ([\d.]+)x', line)
                if match:
                    pos_data['leverage'] = float(match.group(1))
            
            elif 'Current P/L:' in line:
                # Extract percentage and dollar amount
                pnl_match = re.search(r'Current P/L: ([+-]?[\d.]+)% \(\$([+-]?[\d.]+)\)', line)
                if pnl_match:
                    pos_data['pnl_percent'] = float(pnl_match.group(1))
                    pos_data['pnl_amount'] = float(pnl_match.group(2))
            
            elif 'Stop Loss:' in line:
                match = re.search(r'Stop Loss: ([\d.]+)', line)
                if match:
                    pos_data['stop_loss'] = float(match.group(1))
            
            elif 'Take Profit:' in line:
                match = re.search(r'Take Profit: ([\d.]+)', line)
                if match:
                    pos_data['take_profit'] = float(match.group(1))
        
        return pos_data if pos_data else None
    
    def verify_orders(self) -> Dict:
        """Verify order executions are correct"""
        print("\n" + "=" * 80)
        print("📋 VERIFYING ORDER EXECUTIONS")
        print("=" * 80)
        
        results = {
            'total_orders': len(self.orders),
            'valid_orders': 0,
            'successful_orders': 0,
            'orders_with_risk_mgmt': 0,
            'buy_orders': 0,
            'sell_orders': 0,
            'avg_slippage': 0,
            'max_slippage': 0,
            'issues': []
        }
        
        if not self.orders:
            print("⚠️  No orders found in log file")
            return results
        
        total_slippage = 0
        slippage_count = 0
        
        for order in self.orders:
            # Count valid orders
            if order.is_valid():
                results['valid_orders'] += 1
            else:
                results['issues'].append(f"Invalid order: {order.order_id} - missing required fields")
            
            # Count successful orders
            if order.is_successful():
                results['successful_orders'] += 1
            
            # Check risk management
            if order.has_risk_management():
                results['orders_with_risk_mgmt'] += 1
            
            # Count buy/sell
            if order.side == 'BUY':
                results['buy_orders'] += 1
            elif order.side == 'SELL':
                results['sell_orders'] += 1
            
            # Track slippage
            if order.slippage is not None:
                total_slippage += order.slippage
                slippage_count += 1
                if order.slippage > results['max_slippage']:
                    results['max_slippage'] = order.slippage
                
                # Warn on high slippage
                if order.slippage > 1.0:
                    results['issues'].append(
                        f"High slippage on {order.symbol} {order.side}: {order.slippage:.2f}%"
                    )
        
        if slippage_count > 0:
            results['avg_slippage'] = total_slippage / slippage_count
        
        # Print summary
        print(f"\n📊 Order Execution Summary:")
        print(f"   Total Orders: {results['total_orders']}")
        print(f"   Valid Orders: {results['valid_orders']} ({results['valid_orders']/results['total_orders']*100:.1f}%)")
        print(f"   Successful Orders: {results['successful_orders']} ({results['successful_orders']/results['total_orders']*100:.1f}%)")
        print(f"   Buy Orders: {results['buy_orders']}")
        print(f"   Sell Orders: {results['sell_orders']}")
        print(f"   Average Slippage: {results['avg_slippage']:.3f}%")
        print(f"   Max Slippage: {results['max_slippage']:.3f}%")
        
        # Check if orders have risk management
        buy_orders = [o for o in self.orders if o.side == 'BUY']
        if buy_orders:
            risk_mgmt_pct = results['orders_with_risk_mgmt'] / len(buy_orders) * 100
            print(f"   Orders with Risk Management: {results['orders_with_risk_mgmt']}/{len(buy_orders)} ({risk_mgmt_pct:.1f}%)")
            
            if risk_mgmt_pct < 100:
                self.warnings.append(
                    f"Only {risk_mgmt_pct:.1f}% of buy orders have stop loss/take profit set"
                )
        
        return results
    
    def verify_positions(self) -> Dict:
        """Verify position monitoring is working correctly"""
        print("\n" + "=" * 80)
        print("📍 VERIFYING POSITION MONITORING")
        print("=" * 80)
        
        results = {
            'total_updates': len(self.position_updates),
            'positions_monitored': set(),
            'positions_with_sl_tp': 0,
            'avg_update_frequency': 0,
            'issues': []
        }
        
        if not self.position_updates:
            print("⚠️  No position updates found in log file")
            return results
        
        # Group updates by symbol
        position_updates_by_symbol = defaultdict(list)
        for update in self.position_updates:
            if update.symbol:
                position_updates_by_symbol[update.symbol].append(update)
                results['positions_monitored'].add(update.symbol)
        
        # Analyze each position
        print(f"\n📊 Position Monitoring Summary:")
        print(f"   Total Position Updates: {results['total_updates']}")
        print(f"   Unique Positions Monitored: {len(results['positions_monitored'])}")
        
        for symbol, updates in position_updates_by_symbol.items():
            # Check if position has stop loss and take profit
            has_sl_tp = any(u.stop_loss is not None and u.take_profit is not None for u in updates)
            if has_sl_tp:
                results['positions_with_sl_tp'] += 1
            else:
                results['issues'].append(f"Position {symbol} missing stop loss or take profit")
            
            # Calculate update frequency
            if len(updates) > 1:
                timestamps = [datetime.strptime(u.timestamp, '%Y-%m-%d %H:%M:%S') for u in updates if u.timestamp]
                if len(timestamps) > 1:
                    time_diffs = [(timestamps[i+1] - timestamps[i]).total_seconds() for i in range(len(timestamps)-1)]
                    avg_freq = sum(time_diffs) / len(time_diffs)
                    
                    # Warn if updates are too infrequent (> 5 minutes)
                    if avg_freq > 300:
                        results['issues'].append(
                            f"Position {symbol} updates infrequent: avg {avg_freq:.0f}s between updates"
                        )
        
        risk_mgmt_pct = results['positions_with_sl_tp'] / len(results['positions_monitored']) * 100 if results['positions_monitored'] else 0
        print(f"   Positions with Stop Loss/Take Profit: {results['positions_with_sl_tp']}/{len(results['positions_monitored'])} ({risk_mgmt_pct:.1f}%)")
        
        if risk_mgmt_pct < 100:
            self.warnings.append(
                f"Only {risk_mgmt_pct:.1f}% of monitored positions have stop loss and take profit"
            )
        
        return results
    
    def analyze_trading_performance(self) -> Dict:
        """Analyze overall trading performance from orders"""
        print("\n" + "=" * 80)
        print("📈 ANALYZING TRADING PERFORMANCE")
        print("=" * 80)
        
        results = {
            'total_trades': 0,
            'winning_trades': 0,
            'losing_trades': 0,
            'win_rate': 0,
            'avg_profit': 0,
            'avg_loss': 0,
            'total_pnl': 0,
            'issues': []
        }
        
        # Match buy and sell orders to determine trades
        trades_by_symbol = defaultdict(list)
        
        for order in self.orders:
            if order.symbol and order.side:
                trades_by_symbol[order.symbol].append(order)
        
        profits = []
        losses = []
        
        for symbol, symbol_orders in trades_by_symbol.items():
            # Find pairs of buy/sell orders
            buys = [o for o in symbol_orders if o.side == 'BUY']
            sells = [o for o in symbol_orders if o.side == 'SELL']
            
            # Simple matching: each sell closes a portion of buys
            for sell in sells:
                for buy in buys:
                    if buy.fill_price and sell.fill_price:
                        # Calculate P/L for this trade portion
                        pnl_pct = ((sell.fill_price - buy.fill_price) / buy.fill_price) * 100
                        
                        if pnl_pct > 0:
                            profits.append(pnl_pct)
                        else:
                            losses.append(abs(pnl_pct))
                        
                        break  # Match one buy per sell (simplified)
        
        results['total_trades'] = len(profits) + len(losses)
        results['winning_trades'] = len(profits)
        results['losing_trades'] = len(losses)
        
        if results['total_trades'] > 0:
            results['win_rate'] = (results['winning_trades'] / results['total_trades']) * 100
        
        if profits:
            results['avg_profit'] = sum(profits) / len(profits)
        
        if losses:
            results['avg_loss'] = sum(losses) / len(losses)
        
        if profits or losses:
            results['total_pnl'] = sum(profits) - sum(losses)
        
        print(f"\n📊 Trading Performance Summary:")
        print(f"   Total Trades: {results['total_trades']}")
        print(f"   Winning Trades: {results['winning_trades']}")
        print(f"   Losing Trades: {results['losing_trades']}")
        print(f"   Win Rate: {results['win_rate']:.1f}%")
        print(f"   Average Profit: {results['avg_profit']:.2f}%")
        print(f"   Average Loss: {results['avg_loss']:.2f}%")
        print(f"   Total P/L: {results['total_pnl']:+.2f}%")
        
        # Check for concerning patterns
        if results['win_rate'] < 40:
            self.warnings.append(f"Low win rate: {results['win_rate']:.1f}%")
        
        if results['avg_loss'] > results['avg_profit']:
            self.warnings.append(
                f"Average loss ({results['avg_loss']:.2f}%) exceeds average profit ({results['avg_profit']:.2f}%)"
            )
        
        return results
    
    def generate_report(self):
        """Generate a comprehensive report"""
        print("\n" + "=" * 80)
        print("📄 TRADING EXECUTION VERIFICATION REPORT")
        print("=" * 80)
        
        # Run all verifications
        order_results = self.verify_orders()
        position_results = self.verify_positions()
        performance_results = self.analyze_trading_performance()
        
        # Print issues and warnings
        if self.errors:
            print("\n❌ ERRORS:")
            for error in self.errors:
                print(f"   - {error}")
        
        if self.warnings:
            print("\n⚠️  WARNINGS:")
            for warning in self.warnings:
                print(f"   - {warning}")
        
        all_issues = order_results['issues'] + position_results['issues'] + performance_results['issues']
        if all_issues:
            print("\n⚠️  ISSUES FOUND:")
            for issue in all_issues:
                print(f"   - {issue}")
        
        # Overall assessment
        print("\n" + "=" * 80)
        print("✅ OVERALL ASSESSMENT")
        print("=" * 80)
        
        total_issues = len(self.errors) + len(self.warnings) + len(all_issues)
        
        if total_issues == 0:
            print("✅ All checks passed! Trading execution is working correctly.")
            print("   - Orders are being executed properly")
            print("   - Risk management is in place")
            print("   - Position monitoring is active")
            print("   - Trading performance is being tracked")
        elif len(self.errors) > 0:
            print(f"❌ CRITICAL: {len(self.errors)} errors found that require immediate attention")
        elif len(self.warnings) > 0:
            print(f"⚠️  {len(self.warnings)} warnings found that should be reviewed")
        else:
            print(f"ℹ️  {len(all_issues)} minor issues found")
        
        print("\n" + "=" * 80)
        return {
            'orders': order_results,
            'positions': position_results,
            'performance': performance_results,
            'errors': self.errors,
            'warnings': self.warnings,
            'total_issues': total_issues
        }


def main():
    """Main entry point"""
    import sys
    
    log_file = sys.argv[1] if len(sys.argv) > 1 else 'bot.log'
    
    print("=" * 80)
    print("🤖 BOT LOG TRADING EXECUTION VERIFIER")
    print("=" * 80)
    print(f"Log file: {log_file}\n")
    
    analyzer = TradingLogAnalyzer(log_file)
    
    if not analyzer.parse_log():
        print("❌ Failed to parse log file")
        return 1
    
    report = analyzer.generate_report()
    
    # Return exit code based on issues found
    if report['errors']:
        return 2  # Critical errors
    elif report['warnings']:
        return 1  # Warnings
    else:
        return 0  # All good


if __name__ == '__main__':
    sys.exit(main())
