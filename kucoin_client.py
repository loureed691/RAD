"""
KuCoin Futures API Client Wrapper
"""
import ccxt
import time
from typing import List, Dict, Optional
from logger import Logger

class KuCoinClient:
    """Wrapper for KuCoin Futures API using ccxt"""
    
    def __init__(self, api_key: str, api_secret: str, api_passphrase: str):
        """Initialize KuCoin client"""
        self.logger = Logger.get_logger()
        
        try:
            self.exchange = ccxt.kucoinfutures({
                'apiKey': api_key,
                'secret': api_secret,
                'password': api_passphrase,
                'enableRateLimit': True,
            })
            self.logger.info("KuCoin Futures client initialized successfully")
            
            # Set position mode to one-way (single position per symbol)
            # This prevents error 330011: "position mode does not match"
            try:
                self.exchange.set_position_mode(hedged=False)
                self.logger.info("Set position mode to ONE_WAY (hedged=False)")
            except Exception as e:
                # Some exchanges may not support this or it might already be set
                self.logger.warning(f"Could not set position mode: {e}")
                
        except Exception as e:
            self.logger.error(f"Failed to initialize KuCoin client: {e}")
            raise
    
    def get_active_futures(self, include_volume: bool = True) -> List[Dict]:
        """Get all active futures trading pairs (perpetual swaps and quarterly futures) - USDT pairs only
        
        Args:
            include_volume: If True, fetch ticker data to include 24h volume (adds API call overhead)
        
        Returns:
            List of futures with symbol, info, swap, future, and optionally quoteVolume
        """
        try:
            markets = self.exchange.load_markets()
            futures = [
                {
                    'symbol': symbol,
                    'info': market,
                    'swap': market.get('swap', False),
                    'future': market.get('future', False)
                }
                for symbol, market in markets.items()
                if (market.get('swap') or market.get('future')) and market.get('active') and ':USDT' in symbol
            ]
            self.logger.info(f"Found {len(futures)} active USDT futures pairs")
            
            # Optionally fetch volume data from tickers
            if include_volume:
                try:
                    tickers = self.exchange.fetch_tickers()
                    for future in futures:
                        symbol = future['symbol']
                        if symbol in tickers:
                            ticker = tickers[symbol]
                            # Add 24h quote volume (volume in quote currency, e.g., USDT)
                            future['quoteVolume'] = ticker.get('quoteVolume', 0)
                    self.logger.debug(f"Added volume data for {len(futures)} futures")
                except Exception as e:
                    self.logger.warning(f"Could not fetch volume data: {e}")
                    # Continue without volume data
            
            # Log details of found pairs for debugging
            if futures:
                swap_only_count = sum(1 for f in futures if f.get('swap') and not f.get('future'))
                future_only_count = sum(1 for f in futures if f.get('future') and not f.get('swap'))
                both_count = sum(1 for f in futures if f.get('swap') and f.get('future'))
                self.logger.debug(
                    f"Breakdown: {swap_only_count} perpetual swaps only, "
                    f"{future_only_count} dated futures only, "
                    f"{both_count} instruments that are both swap and future"
                )
            
            return futures
        except Exception as e:
            self.logger.error(f"Error fetching active futures: {e}")
            return []
    
    def get_ticker(self, symbol: str) -> Optional[Dict]:
        """Get ticker information for a symbol"""
        try:
            ticker = self.exchange.fetch_ticker(symbol)
            return ticker
        except Exception as e:
            self.logger.error(f"Error fetching ticker for {symbol}: {e}")
            return None
    
    def get_ohlcv(self, symbol: str, timeframe: str = '1h', limit: int = 100) -> List:
        """Get OHLCV data for a symbol with retry logic"""
        max_retries = 3
        retry_delay = 1
        
        for attempt in range(max_retries):
            try:
                ohlcv = self.exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
                if not ohlcv:
                    self.logger.warning(f"Empty OHLCV data returned for {symbol}")
                    return []
                
                self.logger.debug(f"Fetched {len(ohlcv)} candles for {symbol}")
                return ohlcv
            except Exception as e:
                if attempt < max_retries - 1:
                    self.logger.warning(f"Error fetching OHLCV for {symbol} (attempt {attempt+1}/{max_retries}): {e}")
                    time.sleep(retry_delay * (attempt + 1))
                else:
                    self.logger.error(f"Failed to fetch OHLCV for {symbol} after {max_retries} attempts: {e}")
                    return []
        
        return []
    
    def get_balance(self) -> Dict:
        """Get account balance"""
        try:
            balance = self.exchange.fetch_balance()
            return balance
        except Exception as e:
            self.logger.error(f"Error fetching balance: {e}")
            return {}
    
    def get_market_limits(self, symbol: str) -> Optional[Dict]:
        """Get market limits for a symbol (min/max order size)"""
        try:
            markets = self.exchange.load_markets()
            if symbol in markets:
                market = markets[symbol]
                limits = {
                    'amount': {
                        'min': market.get('limits', {}).get('amount', {}).get('min'),
                        'max': market.get('limits', {}).get('amount', {}).get('max')
                    },
                    'cost': {
                        'min': market.get('limits', {}).get('cost', {}).get('min'),
                        'max': market.get('limits', {}).get('cost', {}).get('max')
                    }
                }
                return limits
            return None
        except Exception as e:
            self.logger.error(f"Error fetching market limits for {symbol}: {e}")
            return None
    
    def validate_and_cap_amount(self, symbol: str, amount: float) -> float:
        """Validate and cap order amount to exchange limits
        
        Args:
            symbol: Trading pair symbol
            amount: Desired order amount in contracts
            
        Returns:
            Validated amount capped at exchange limits
        """
        limits = self.get_market_limits(symbol)
        if not limits:
            # If we can't get limits, apply a conservative default cap
            # KuCoin typically has a 10,000 contract limit
            default_max = 10000
            if amount > default_max:
                self.logger.warning(
                    f"Amount {amount:.4f} exceeds default limit {default_max}, "
                    f"capping to {default_max}"
                )
                return default_max
            return amount
        
        # Check minimum
        min_amount = limits['amount']['min']
        if min_amount and amount < min_amount:
            self.logger.warning(
                f"Amount {amount:.4f} below minimum {min_amount}, "
                f"adjusting to minimum"
            )
            return min_amount
        
        # Check maximum
        max_amount = limits['amount']['max']
        if max_amount and amount > max_amount:
            self.logger.warning(
                f"Amount {amount:.4f} exceeds maximum {max_amount}, "
                f"capping to {max_amount}"
            )
            return max_amount
        
        return amount
    
    def create_market_order(self, symbol: str, side: str, amount: float, 
                           leverage: int = 10, max_slippage: float = 0.01,
                           validate_depth: bool = True) -> Optional[Dict]:
        """Create a market order with leverage and slippage protection
        
        Args:
            symbol: Trading pair symbol
            side: 'buy' or 'sell'
            amount: Order amount in contracts
            leverage: Leverage to use
            max_slippage: Maximum acceptable slippage (default 1%)
            validate_depth: Check order book depth before large orders
        
        Returns:
            Order dict if successful, None otherwise
        """
        try:
            # Validate and cap amount to exchange limits
            validated_amount = self.validate_and_cap_amount(symbol, amount)
            
            # For large orders, check order book depth
            if validate_depth and validated_amount > 100:  # Threshold for "large" order
                order_book = self.get_order_book(symbol, limit=20)
                if order_book:
                    levels = order_book['bids'] if side == 'sell' else order_book['asks']
                    total_liquidity = sum(level[1] for level in levels)
                    
                    if total_liquidity < validated_amount * 1.5:
                        self.logger.warning(
                            f"Low liquidity for {symbol}: order size {validated_amount} vs "
                            f"book depth {total_liquidity:.2f}. Potential high slippage."
                        )
            
            # Get current price for slippage validation
            ticker = self.get_ticker(symbol)
            if ticker:
                reference_price = ticker['last']
                self.logger.debug(f"Reference price for {symbol}: {reference_price}")
            
            # Switch to cross margin mode first (fixes error 330006)
            self.exchange.set_margin_mode('cross', symbol)
            
            # Set leverage with cross margin mode
            self.exchange.set_leverage(leverage, symbol, params={"marginMode": "cross"})
            
            # Create market order with cross margin mode explicitly set
            order = self.exchange.create_order(
                symbol=symbol,
                type='market',
                side=side,
                amount=validated_amount,
                params={"marginMode": "cross"}
            )
            
            # Log order details
            avg_price = order.get('average') or order.get('price', 'N/A')
            self.logger.info(
                f"Created {side} market order for {validated_amount} {symbol} "
                f"at {leverage}x leverage (avg fill: {avg_price})"
            )
            
            # Check actual slippage if we have both prices
            if ticker and order.get('average'):
                actual_slippage = abs(order['average'] - reference_price) / reference_price
                if actual_slippage > max_slippage:
                    self.logger.warning(
                        f"High slippage detected: {actual_slippage:.2%} "
                        f"(reference: {reference_price}, filled: {order['average']})"
                    )
            
            return order
        except Exception as e:
            self.logger.error(f"Error creating market order: {e}")
            return None
    
    def create_limit_order(self, symbol: str, side: str, amount: float, 
                          price: float, leverage: int = 10, post_only: bool = False,
                          reduce_only: bool = False) -> Optional[Dict]:
        """Create a limit order with leverage.

        Cross margin mode is enforced when setting leverage.
        
        Args:
            symbol: Trading pair symbol
            side: 'buy' or 'sell'
            amount: Order amount in contracts
            price: Limit price
            leverage: Leverage to use
            post_only: If True, ensures order is a maker order (reduces fees)
            reduce_only: If True, order only reduces position (safer exits)
        """
        try:
            # Validate and cap amount to exchange limits
            validated_amount = self.validate_and_cap_amount(symbol, amount)
            
            # Switch to cross margin mode first (fixes error 330006)
            self.exchange.set_margin_mode('cross', symbol)
            
            # Set leverage with cross margin mode
            self.exchange.set_leverage(leverage, symbol, params={"marginMode": "cross"})
            
            # Build order parameters
            params = {"marginMode": "cross"}
            if post_only:
                params["postOnly"] = True
            if reduce_only:
                params["reduceOnly"] = True
            
            # Create limit order with cross margin mode explicitly set
            order = self.exchange.create_order(
                symbol=symbol,
                type='limit',
                side=side,
                amount=validated_amount,
                price=price,
                params=params
            )
            self.logger.info(
                f"Created {side} limit order for {validated_amount} {symbol} at {price} "
                f"(post_only={post_only}, reduce_only={reduce_only})"
            )
            return order
        except Exception as e:
            self.logger.error(f"Error creating limit order: {e}")
            return None
    
    def cancel_order(self, order_id: str, symbol: str) -> bool:
        """Cancel an order"""
        try:
            self.exchange.cancel_order(order_id, symbol)
            self.logger.info(f"Cancelled order {order_id} for {symbol}")
            return True
        except Exception as e:
            self.logger.error(f"Error cancelling order: {e}")
            return False
    
    def get_open_positions(self) -> List[Dict]:
        """Get all open positions"""
        try:
            positions = self.exchange.fetch_positions()
            open_positions = [pos for pos in positions if float(pos.get('contracts', 0)) > 0]
            return open_positions
        except Exception as e:
            self.logger.error(f"Error fetching positions: {e}")
            return []
    
    def close_position(self, symbol: str, use_limit: bool = False, 
                      slippage_tolerance: float = 0.002) -> bool:
        """Close a position with optional limit order for better execution
        
        Args:
            symbol: Trading pair symbol
            use_limit: If True, uses limit order instead of market order
            slippage_tolerance: Maximum acceptable slippage (default 0.2%)
        
        Returns:
            True if position closed successfully, False otherwise
        """
        try:
            positions = self.get_open_positions()
            for pos in positions:
                if pos['symbol'] == symbol:
                    contracts = float(pos['contracts'])
                    side = 'sell' if pos['side'] == 'long' else 'buy'
                    
                    if use_limit:
                        # Get current market price
                        ticker = self.get_ticker(symbol)
                        if not ticker:
                            self.logger.error(f"Could not get ticker for {symbol}, falling back to market order")
                            order = self.create_market_order(symbol, side, abs(contracts))
                        else:
                            current_price = ticker['last']
                            # Set limit price with slippage tolerance
                            if side == 'sell':
                                limit_price = current_price * (1 - slippage_tolerance)
                            else:
                                limit_price = current_price * (1 + slippage_tolerance)
                            
                            order = self.create_limit_order(
                                symbol, side, abs(contracts), limit_price, 
                                reduce_only=True
                            )
                    else:
                        order = self.create_market_order(symbol, side, abs(contracts))
                    
                    if order:
                        self.logger.info(f"Closed position for {symbol}")
                        return True
                    else:
                        self.logger.error(f"Failed to create close order for {symbol}")
                        return False
            return False
        except Exception as e:
            self.logger.error(f"Error closing position: {e}")
            return False
    
    def create_stop_limit_order(self, symbol: str, side: str, amount: float,
                               stop_price: float, limit_price: float, 
                               leverage: int = 10, reduce_only: bool = False) -> Optional[Dict]:
        """Create a stop-limit order for stop loss or take profit
        
        Args:
            symbol: Trading pair symbol
            side: 'buy' or 'sell'
            amount: Order amount in contracts
            stop_price: Stop trigger price
            limit_price: Limit price after stop triggers
            leverage: Leverage to use
            reduce_only: If True, order only reduces position
        
        Returns:
            Order dict if successful, None otherwise
        """
        try:
            # Validate and cap amount to exchange limits
            validated_amount = self.validate_and_cap_amount(symbol, amount)
            
            # Switch to cross margin mode first
            self.exchange.set_margin_mode('cross', symbol)
            
            # Set leverage with cross margin mode
            self.exchange.set_leverage(leverage, symbol, params={"marginMode": "cross"})
            
            # Build order parameters
            params = {
                "marginMode": "cross",
                "stopPrice": stop_price
            }
            if reduce_only:
                params["reduceOnly"] = True
            
            # Create stop-limit order
            order = self.exchange.create_order(
                symbol=symbol,
                type='limit',
                side=side,
                amount=validated_amount,
                price=limit_price,
                params=params
            )
            self.logger.info(
                f"Created {side} stop-limit order for {validated_amount} {symbol} "
                f"(stop={stop_price}, limit={limit_price}, reduce_only={reduce_only})"
            )
            return order
        except Exception as e:
            self.logger.error(f"Error creating stop-limit order: {e}")
            return None
    
    def get_order_status(self, order_id: str, symbol: str) -> Optional[Dict]:
        """Get the status of an order
        
        Args:
            order_id: Order ID to check
            symbol: Trading pair symbol
        
        Returns:
            Order status dict with fields like 'status', 'filled', 'remaining', etc.
        """
        try:
            order = self.exchange.fetch_order(order_id, symbol)
            return {
                'id': order['id'],
                'status': order['status'],  # 'open', 'closed', 'canceled', 'expired'
                'filled': order.get('filled', 0),
                'remaining': order.get('remaining', 0),
                'amount': order.get('amount', 0),
                'price': order.get('price'),
                'average': order.get('average'),  # Average fill price
                'cost': order.get('cost', 0),
                'timestamp': order.get('timestamp')
            }
        except Exception as e:
            self.logger.error(f"Error fetching order status for {order_id}: {e}")
            return None
    
    def wait_for_order_fill(self, order_id: str, symbol: str, 
                           timeout: int = 30, check_interval: int = 2) -> Optional[Dict]:
        """Wait for an order to be filled (or partially filled)
        
        Args:
            order_id: Order ID to monitor
            symbol: Trading pair symbol
            timeout: Maximum time to wait in seconds
            check_interval: How often to check order status in seconds
        
        Returns:
            Final order status dict, or None if timeout or error
        """
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            status = self.get_order_status(order_id, symbol)
            
            if not status:
                self.logger.error(f"Could not get status for order {order_id}")
                return None
            
            # Order is fully filled
            if status['status'] == 'closed' and status['remaining'] == 0:
                self.logger.info(f"Order {order_id} fully filled at avg price {status['average']}")
                return status
            
            # Order is canceled or expired
            if status['status'] in ['canceled', 'expired']:
                self.logger.warning(f"Order {order_id} was {status['status']}")
                return status
            
            # Order is partially filled
            if status['filled'] > 0 and status['remaining'] > 0:
                self.logger.info(
                    f"Order {order_id} partially filled: "
                    f"{status['filled']}/{status['amount']} contracts"
                )
            
            time.sleep(check_interval)
        
        # Timeout reached
        final_status = self.get_order_status(order_id, symbol)
        if final_status and final_status['filled'] > 0:
            self.logger.warning(
                f"Order {order_id} timeout: partially filled "
                f"{final_status['filled']}/{final_status['amount']} contracts"
            )
        else:
            self.logger.warning(f"Order {order_id} timeout: not filled")
        
        return final_status
    
    def get_order_book(self, symbol: str, limit: int = 20) -> Optional[Dict]:
        """Get order book depth for a symbol
        
        Args:
            symbol: Trading pair symbol
            limit: Number of bid/ask levels to fetch
        
        Returns:
            Dict with 'bids' and 'asks' lists, or None if error
        """
        try:
            order_book = self.exchange.fetch_order_book(symbol, limit=limit)
            return {
                'bids': order_book.get('bids', []),  # List of [price, amount]
                'asks': order_book.get('asks', []),  # List of [price, amount]
                'timestamp': order_book.get('timestamp')
            }
        except Exception as e:
            self.logger.error(f"Error fetching order book for {symbol}: {e}")
            return None
    
    def validate_price_with_slippage(self, symbol: str, side: str, 
                                    expected_price: float, 
                                    max_slippage: float = 0.005) -> tuple[bool, float]:
        """Validate current market price is within acceptable slippage
        
        Args:
            symbol: Trading pair symbol
            side: 'buy' or 'sell'
            expected_price: Expected/reference price
            max_slippage: Maximum acceptable slippage (default 0.5%)
        
        Returns:
            Tuple of (is_valid, current_price)
        """
        try:
            ticker = self.get_ticker(symbol)
            if not ticker:
                return False, 0.0
            
            current_price = ticker['last']
            
            if side == 'buy':
                # For buys, we don't want price to have gone up too much
                slippage = (current_price - expected_price) / expected_price
            else:
                # For sells, we don't want price to have gone down too much
                slippage = (expected_price - current_price) / expected_price
            
            is_valid = slippage <= max_slippage
            
            if not is_valid:
                self.logger.warning(
                    f"Price slippage {slippage:.2%} exceeds maximum {max_slippage:.2%} "
                    f"for {side} {symbol} (expected: {expected_price}, current: {current_price})"
                )
            
            return is_valid, current_price
            
        except Exception as e:
            self.logger.error(f"Error validating price slippage: {e}")
            return False, 0.0
