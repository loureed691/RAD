"""
Base connector interface for all exchange connectors.

Defines the standard interface that all exchange connectors must implement,
whether CEX (centralized) or DEX (decentralized).
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from logger import Logger


class BaseExchangeConnector(ABC):
    """
    Abstract base class for exchange connectors.
    
    All exchange connectors (CEX, DEX) must implement these methods
    to provide a unified interface for the trading system.
    """
    
    def __init__(self, exchange_id: str, config: Dict = None):
        """
        Initialize connector
        
        Args:
            exchange_id: Unique identifier for this exchange
            config: Exchange-specific configuration
        """
        self.exchange_id = exchange_id
        self.config = config or {}
        self.logger = Logger.get_logger()
        self.connected = False
        self.last_update = None
        
        self.logger.info(f"🔌 Initializing connector for {exchange_id}")
    
    @abstractmethod
    def connect(self) -> bool:
        """
        Connect to the exchange
        
        Returns:
            True if connection successful
        """
        pass
    
    @abstractmethod
    def disconnect(self):
        """Disconnect from the exchange"""
        pass
    
    @abstractmethod
    def get_balance(self, currency: str = 'USDT') -> float:
        """
        Get available balance
        
        Args:
            currency: Currency symbol
        
        Returns:
            Available balance
        """
        pass
    
    @abstractmethod
    def get_ticker(self, symbol: str) -> Dict:
        """
        Get current ticker data
        
        Args:
            symbol: Trading pair symbol
        
        Returns:
            Ticker dict with 'last', 'bid', 'ask', 'volume'
        """
        pass
    
    @abstractmethod
    def get_orderbook(self, symbol: str, depth: int = 20) -> Dict:
        """
        Get order book
        
        Args:
            symbol: Trading pair symbol
            depth: Number of levels per side
        
        Returns:
            Orderbook dict with 'bids' and 'asks' lists
        """
        pass
    
    @abstractmethod
    def get_recent_trades(self, symbol: str, limit: int = 100) -> List[Dict]:
        """
        Get recent trades
        
        Args:
            symbol: Trading pair symbol
            limit: Number of trades to fetch
        
        Returns:
            List of trade dicts
        """
        pass
    
    @abstractmethod
    def place_limit_order(self, symbol: str, side: str, price: float,
                         amount: float, post_only: bool = False) -> Dict:
        """
        Place a limit order
        
        Args:
            symbol: Trading pair symbol
            side: 'buy' or 'sell'
            price: Limit price
            amount: Order amount
            post_only: Post-only flag (maker-only)
        
        Returns:
            Order dict with 'order_id', 'status', etc.
        """
        pass
    
    @abstractmethod
    def place_market_order(self, symbol: str, side: str, amount: float) -> Dict:
        """
        Place a market order
        
        Args:
            symbol: Trading pair symbol
            side: 'buy' or 'sell'
            amount: Order amount
        
        Returns:
            Order dict
        """
        pass
    
    @abstractmethod
    def cancel_order(self, symbol: str, order_id: str) -> bool:
        """
        Cancel an order
        
        Args:
            symbol: Trading pair symbol
            order_id: Order ID to cancel
        
        Returns:
            True if cancellation successful
        """
        pass
    
    @abstractmethod
    def get_order_status(self, symbol: str, order_id: str) -> Dict:
        """
        Get order status
        
        Args:
            symbol: Trading pair symbol
            order_id: Order ID
        
        Returns:
            Order status dict
        """
        pass
    
    @abstractmethod
    def get_open_orders(self, symbol: Optional[str] = None) -> List[Dict]:
        """
        Get open orders
        
        Args:
            symbol: Trading pair symbol (optional, None = all pairs)
        
        Returns:
            List of open order dicts
        """
        pass
    
    @abstractmethod
    def get_position(self, symbol: str) -> Optional[Dict]:
        """
        Get current position for a symbol
        
        Args:
            symbol: Trading pair symbol
        
        Returns:
            Position dict or None
        """
        pass
    
    @abstractmethod
    def get_funding_rate(self, symbol: str) -> Optional[float]:
        """
        Get current funding rate (for perpetual futures)
        
        Args:
            symbol: Trading pair symbol
        
        Returns:
            Current funding rate or None
        """
        pass
    
    @abstractmethod
    def get_mark_price(self, symbol: str) -> Optional[float]:
        """
        Get mark price (for perpetual futures)
        
        Args:
            symbol: Trading pair symbol
        
        Returns:
            Mark price or None
        """
        pass
    
    def get_exchange_info(self) -> Dict:
        """
        Get exchange information
        
        Returns:
            Dict with exchange capabilities and limits
        """
        return {
            'exchange_id': self.exchange_id,
            'connected': self.connected,
            'last_update': self.last_update,
            'supports_futures': False,
            'supports_spot': False,
            'supports_margin': False,
            'maker_fee': 0.0,
            'taker_fee': 0.0
        }
    
    def health_check(self) -> bool:
        """
        Perform health check on connection
        
        Returns:
            True if connector is healthy
        """
        try:
            if not self.connected:
                return False
            
            # Try to fetch ticker for a common pair
            self.get_ticker('BTC/USDT')
            return True
        except Exception as e:
            self.logger.error(f"Health check failed for {self.exchange_id}: {e}")
            return False
