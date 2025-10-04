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
    
    def get_active_futures(self) -> List[Dict]:
        """Get all active futures trading pairs (perpetual swaps and quarterly futures) - USDT pairs only"""
        try:
            markets = self.exchange.load_markets()
            futures = [
                {
                    'symbol': symbol,
                    'info': market
                }
                for symbol, market in markets.items()
                if (market.get('swap') or market.get('future')) and market.get('active') and ':USDT' in symbol
            ]
            self.logger.info(f"Found {len(futures)} active USDT futures pairs")
            
            # Log details of found pairs for debugging
            if futures:
                swap_count = sum(1 for f in futures if markets[f['symbol']].get('swap'))
                future_count = sum(1 for f in futures if markets[f['symbol']].get('future'))
                self.logger.debug(f"Breakdown: {swap_count} perpetual swaps, {future_count} dated futures")
            
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
                           leverage: int = 10) -> Optional[Dict]:
        """Create a market order with leverage"""
        try:
            # Validate and cap amount to exchange limits
            validated_amount = self.validate_and_cap_amount(symbol, amount)
            
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
            self.logger.info(f"Created {side} order for {validated_amount} {symbol} at {leverage}x leverage")
            return order
        except Exception as e:
            self.logger.error(f"Error creating market order: {e}")
            return None
    
    def create_limit_order(self, symbol: str, side: str, amount: float, 
                          price: float, leverage: int = 10) -> Optional[Dict]:
        """Create a limit order with leverage.

        Cross margin mode is enforced when setting leverage.
        """
        try:
            # Validate and cap amount to exchange limits
            validated_amount = self.validate_and_cap_amount(symbol, amount)
            
            # Switch to cross margin mode first (fixes error 330006)
            self.exchange.set_margin_mode('cross', symbol)
            
            # Set leverage with cross margin mode
            self.exchange.set_leverage(leverage, symbol, params={"marginMode": "cross"})
            
            # Create limit order with cross margin mode explicitly set
            order = self.exchange.create_order(
                symbol=symbol,
                type='limit',
                side=side,
                amount=validated_amount,
                price=price,
                params={"marginMode": "cross"}
            )
            self.logger.info(f"Created {side} limit order for {validated_amount} {symbol} at {price}")
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
    
    def close_position(self, symbol: str) -> bool:
        """Close a position"""
        try:
            positions = self.get_open_positions()
            for pos in positions:
                if pos['symbol'] == symbol:
                    contracts = float(pos['contracts'])
                    side = 'sell' if pos['side'] == 'long' else 'buy'
                    self.create_market_order(symbol, side, abs(contracts))
                    self.logger.info(f"Closed position for {symbol}")
                    return True
            return False
        except Exception as e:
            self.logger.error(f"Error closing position: {e}")
            return False
