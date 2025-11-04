"""
CCXT-based CEX (Centralized Exchange) connector.

Provides unified access to multiple centralized exchanges through CCXT library.
Supports spot and futures markets on various exchanges.
"""
import ccxt
from typing import Dict, List, Optional
from datetime import datetime
from .base_connector import BaseExchangeConnector
from logger import Logger


class CEXConnector(BaseExchangeConnector):
    """
    Centralized exchange connector using CCXT library.
    
    Supports multiple exchanges including:
    - Binance, Binance Futures
    - OKX
    - Bybit
    - KuCoin, KuCoin Futures
    - And many more via CCXT
    """
    
    def __init__(self, exchange_id: str, api_key: str = None, api_secret: str = None,
                 api_passphrase: str = None, testnet: bool = False, config: Dict = None):
        """
        Initialize CEX connector
        
        Args:
            exchange_id: CCXT exchange ID (e.g., 'binance', 'okx', 'kucoinfutures')
            api_key: API key
            api_secret: API secret
            api_passphrase: API passphrase (for some exchanges)
            testnet: Use testnet/sandbox
            config: Additional CCXT configuration
        """
        super().__init__(exchange_id, config)
        
        self.api_key = api_key
        self.api_secret = api_secret
        self.api_passphrase = api_passphrase
        self.testnet = testnet
        self.exchange = None
        
        # Supported exchange types
        self.supports_futures = False
        self.supports_spot = False
    
    def connect(self) -> bool:
        """
        Connect to the exchange via CCXT
        
        Returns:
            True if connection successful
        """
        try:
            # Get exchange class from CCXT
            exchange_class = getattr(ccxt, self.exchange_id)
            
            # Build config
            ccxt_config = {
                'enableRateLimit': True,
                'timeout': 30000,
            }
            
            if self.api_key and self.api_secret:
                ccxt_config['apiKey'] = self.api_key
                ccxt_config['secret'] = self.api_secret
            
            if self.api_passphrase:
                ccxt_config['password'] = self.api_passphrase
            
            if self.testnet:
                ccxt_config['sandbox'] = True
            
            # Add custom config
            if self.config:
                ccxt_config.update(self.config)
            
            # Create exchange instance
            self.exchange = exchange_class(ccxt_config)
            
            # Load markets
            self.exchange.load_markets()
            
            # Check capabilities
            self.supports_futures = self.exchange.has.get('fetchFundingRate', False)
            self.supports_spot = True
            
            self.connected = True
            self.last_update = datetime.now()
            
            self.logger.info(
                f"✅ Connected to {self.exchange_id} "
                f"(futures: {self.supports_futures}, spot: {self.supports_spot})"
            )
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to connect to {self.exchange_id}: {e}")
            self.connected = False
            return False
    
    def disconnect(self):
        """Disconnect from exchange"""
        self.exchange = None
        self.connected = False
        self.logger.info(f"🔌 Disconnected from {self.exchange_id}")
    
    def get_balance(self, currency: str = 'USDT') -> float:
        """Get available balance"""
        try:
            if not self.connected or not self.exchange:
                return 0.0
            
            balance = self.exchange.fetch_balance()
            return balance.get(currency, {}).get('free', 0.0)
            
        except Exception as e:
            self.logger.error(f"Error fetching balance: {e}")
            return 0.0
    
    def get_ticker(self, symbol: str) -> Dict:
        """Get ticker data"""
        try:
            if not self.connected or not self.exchange:
                return {}
            
            ticker = self.exchange.fetch_ticker(symbol)
            
            return {
                'symbol': symbol,
                'last': ticker.get('last'),
                'bid': ticker.get('bid'),
                'ask': ticker.get('ask'),
                'volume': ticker.get('baseVolume'),
                'timestamp': ticker.get('timestamp')
            }
            
        except Exception as e:
            self.logger.error(f"Error fetching ticker for {symbol}: {e}")
            return {}
    
    def get_orderbook(self, symbol: str, depth: int = 20) -> Dict:
        """Get order book"""
        try:
            if not self.connected or not self.exchange:
                return {'bids': [], 'asks': []}
            
            orderbook = self.exchange.fetch_order_book(symbol, limit=depth)
            
            return {
                'bids': orderbook.get('bids', []),
                'asks': orderbook.get('asks', []),
                'timestamp': orderbook.get('timestamp')
            }
            
        except Exception as e:
            self.logger.error(f"Error fetching orderbook for {symbol}: {e}")
            return {'bids': [], 'asks': []}
    
    def get_recent_trades(self, symbol: str, limit: int = 100) -> List[Dict]:
        """Get recent trades"""
        try:
            if not self.connected or not self.exchange:
                return []
            
            trades = self.exchange.fetch_trades(symbol, limit=limit)
            
            return [{
                'id': t.get('id'),
                'timestamp': t.get('timestamp'),
                'price': t.get('price'),
                'amount': t.get('amount'),
                'side': t.get('side'),
                'cost': t.get('cost')
            } for t in trades]
            
        except Exception as e:
            self.logger.error(f"Error fetching trades for {symbol}: {e}")
            return []
    
    def place_limit_order(self, symbol: str, side: str, price: float,
                         amount: float, post_only: bool = False) -> Dict:
        """Place limit order"""
        try:
            if not self.connected or not self.exchange:
                return {}
            
            params = {}
            if post_only:
                params['postOnly'] = True
            
            order = self.exchange.create_limit_order(
                symbol, side, amount, price, params
            )
            
            return {
                'order_id': order.get('id'),
                'symbol': symbol,
                'side': side,
                'price': price,
                'amount': amount,
                'status': order.get('status'),
                'timestamp': order.get('timestamp')
            }
            
        except Exception as e:
            self.logger.error(f"Error placing limit order: {e}")
            return {}
    
    def place_market_order(self, symbol: str, side: str, amount: float) -> Dict:
        """Place market order"""
        try:
            if not self.connected or not self.exchange:
                return {}
            
            order = self.exchange.create_market_order(symbol, side, amount)
            
            return {
                'order_id': order.get('id'),
                'symbol': symbol,
                'side': side,
                'amount': amount,
                'filled': order.get('filled'),
                'average': order.get('average'),
                'status': order.get('status'),
                'timestamp': order.get('timestamp')
            }
            
        except Exception as e:
            self.logger.error(f"Error placing market order: {e}")
            return {}
    
    def cancel_order(self, symbol: str, order_id: str) -> bool:
        """Cancel order"""
        try:
            if not self.connected or not self.exchange:
                return False
            
            self.exchange.cancel_order(order_id, symbol)
            return True
            
        except Exception as e:
            self.logger.error(f"Error canceling order {order_id}: {e}")
            return False
    
    def get_order_status(self, symbol: str, order_id: str) -> Dict:
        """Get order status"""
        try:
            if not self.connected or not self.exchange:
                return {}
            
            order = self.exchange.fetch_order(order_id, symbol)
            
            return {
                'order_id': order.get('id'),
                'symbol': symbol,
                'status': order.get('status'),
                'side': order.get('side'),
                'price': order.get('price'),
                'amount': order.get('amount'),
                'filled': order.get('filled'),
                'remaining': order.get('remaining'),
                'timestamp': order.get('timestamp')
            }
            
        except Exception as e:
            self.logger.error(f"Error fetching order status: {e}")
            return {}
    
    def get_open_orders(self, symbol: Optional[str] = None) -> List[Dict]:
        """Get open orders"""
        try:
            if not self.connected or not self.exchange:
                return []
            
            orders = self.exchange.fetch_open_orders(symbol)
            
            return [{
                'order_id': o.get('id'),
                'symbol': o.get('symbol'),
                'side': o.get('side'),
                'price': o.get('price'),
                'amount': o.get('amount'),
                'filled': o.get('filled'),
                'status': o.get('status'),
                'timestamp': o.get('timestamp')
            } for o in orders]
            
        except Exception as e:
            self.logger.error(f"Error fetching open orders: {e}")
            return []
    
    def get_position(self, symbol: str) -> Optional[Dict]:
        """Get position"""
        try:
            if not self.connected or not self.exchange:
                return None
            
            if not self.supports_futures:
                return None
            
            positions = self.exchange.fetch_positions([symbol])
            
            if not positions:
                return None
            
            pos = positions[0]
            
            return {
                'symbol': symbol,
                'side': pos.get('side'),
                'contracts': pos.get('contracts'),
                'entry_price': pos.get('entryPrice'),
                'mark_price': pos.get('markPrice'),
                'unrealized_pnl': pos.get('unrealizedPnl'),
                'leverage': pos.get('leverage')
            }
            
        except Exception as e:
            self.logger.error(f"Error fetching position: {e}")
            return None
    
    def get_funding_rate(self, symbol: str) -> Optional[float]:
        """Get funding rate"""
        try:
            if not self.connected or not self.exchange:
                return None
            
            if not self.supports_futures:
                return None
            
            funding = self.exchange.fetch_funding_rate(symbol)
            return funding.get('fundingRate')
            
        except Exception as e:
            self.logger.error(f"Error fetching funding rate: {e}")
            return None
    
    def get_mark_price(self, symbol: str) -> Optional[float]:
        """Get mark price"""
        try:
            if not self.connected or not self.exchange:
                return None
            
            if not self.supports_futures:
                return None
            
            # Get from ticker or funding rate data
            ticker = self.exchange.fetch_ticker(symbol)
            return ticker.get('info', {}).get('markPrice')
            
        except Exception as e:
            self.logger.error(f"Error fetching mark price: {e}")
            return None
    
    def get_exchange_info(self) -> Dict:
        """Get exchange information"""
        info = super().get_exchange_info()
        
        if self.connected and self.exchange:
            info.update({
                'supports_futures': self.supports_futures,
                'supports_spot': self.supports_spot,
                'maker_fee': self.exchange.fees.get('trading', {}).get('maker', 0.0),
                'taker_fee': self.exchange.fees.get('trading', {}).get('taker', 0.0),
                'markets_count': len(self.exchange.markets) if self.exchange.markets else 0
            })
        
        return info
