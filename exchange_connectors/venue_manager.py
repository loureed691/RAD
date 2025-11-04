"""
Multi-venue manager for coordinating trading across exchanges.

Manages connections to multiple exchanges and provides unified access.
"""
from typing import Dict, List, Optional
from datetime import datetime
from logger import Logger
from .base_connector import BaseExchangeConnector
from .cex_connector import CEXConnector
from .dydx_connector import DydxConnector
from .hyperliquid_connector import HyperliquidConnector


class VenueManager:
    """
    Manages multiple exchange venues for cross-venue trading.
    
    Provides:
    - Unified interface to multiple exchanges
    - Venue health monitoring
    - Cross-venue price comparison
    - Best execution venue selection
    """
    
    def __init__(self):
        """Initialize venue manager"""
        self.venues: Dict[str, BaseExchangeConnector] = {}
        self.logger = Logger.get_logger()
        self.logger.info("🌐 Venue Manager initialized")
    
    def add_venue(self, venue_id: str, connector: BaseExchangeConnector):
        """
        Add a venue to the manager
        
        Args:
            venue_id: Unique venue identifier
            connector: Exchange connector instance
        """
        self.venues[venue_id] = connector
        self.logger.info(f"✅ Added venue: {venue_id}")
    
    def remove_venue(self, venue_id: str):
        """
        Remove a venue
        
        Args:
            venue_id: Venue to remove
        """
        if venue_id in self.venues:
            self.venues[venue_id].disconnect()
            del self.venues[venue_id]
            self.logger.info(f"❌ Removed venue: {venue_id}")
    
    def connect_all(self) -> Dict[str, bool]:
        """
        Connect to all venues
        
        Returns:
            Dict of venue_id -> connection_success
        """
        results = {}
        for venue_id, connector in self.venues.items():
            try:
                success = connector.connect()
                results[venue_id] = success
                if success:
                    self.logger.info(f"✅ Connected to {venue_id}")
                else:
                    self.logger.warning(f"⚠️ Failed to connect to {venue_id}")
            except Exception as e:
                self.logger.error(f"❌ Error connecting to {venue_id}: {e}")
                results[venue_id] = False
        
        return results
    
    def disconnect_all(self):
        """Disconnect from all venues"""
        for venue_id, connector in self.venues.items():
            try:
                connector.disconnect()
                self.logger.info(f"🔌 Disconnected from {venue_id}")
            except Exception as e:
                self.logger.error(f"Error disconnecting from {venue_id}: {e}")
    
    def get_venue(self, venue_id: str) -> Optional[BaseExchangeConnector]:
        """
        Get connector for a venue
        
        Args:
            venue_id: Venue identifier
        
        Returns:
            Connector or None
        """
        return self.venues.get(venue_id)
    
    def get_all_venues(self) -> List[str]:
        """Get list of all venue IDs"""
        return list(self.venues.keys())
    
    def get_connected_venues(self) -> List[str]:
        """Get list of connected venue IDs"""
        return [vid for vid, conn in self.venues.items() if conn.connected]
    
    def health_check_all(self) -> Dict[str, bool]:
        """
        Perform health check on all venues
        
        Returns:
            Dict of venue_id -> health_status
        """
        results = {}
        for venue_id, connector in self.venues.items():
            results[venue_id] = connector.health_check()
        
        return results
    
    def get_best_price(self, symbol: str, side: str) -> Optional[Dict]:
        """
        Find best price across all venues
        
        Args:
            symbol: Trading pair
            side: 'buy' or 'ask'
        
        Returns:
            Dict with venue_id and price, or None
        """
        best_venue = None
        best_price = None
        
        for venue_id, connector in self.venues.items():
            if not connector.connected:
                continue
            
            try:
                ticker = connector.get_ticker(symbol)
                if not ticker:
                    continue
                
                price = ticker.get('ask' if side == 'buy' else 'bid')
                if price is None:
                    continue
                
                if best_price is None:
                    best_price = price
                    best_venue = venue_id
                elif side == 'buy' and price < best_price:
                    best_price = price
                    best_venue = venue_id
                elif side == 'sell' and price > best_price:
                    best_price = price
                    best_venue = venue_id
            
            except Exception as e:
                self.logger.error(f"Error getting price from {venue_id}: {e}")
        
        if best_venue:
            return {
                'venue_id': best_venue,
                'price': best_price,
                'symbol': symbol,
                'side': side
            }
        
        return None
    
    def get_all_prices(self, symbol: str) -> Dict[str, Dict]:
        """
        Get prices from all venues
        
        Args:
            symbol: Trading pair
        
        Returns:
            Dict of venue_id -> ticker_data
        """
        prices = {}
        
        for venue_id, connector in self.venues.items():
            if not connector.connected:
                continue
            
            try:
                ticker = connector.get_ticker(symbol)
                if ticker:
                    prices[venue_id] = ticker
            except Exception as e:
                self.logger.error(f"Error getting ticker from {venue_id}: {e}")
        
        return prices
    
    def get_arbitrage_opportunities(self, symbol: str, min_spread: float = 0.001) -> List[Dict]:
        """
        Find arbitrage opportunities across venues
        
        Args:
            symbol: Trading pair
            min_spread: Minimum spread to consider (fraction)
        
        Returns:
            List of arbitrage opportunities
        """
        prices = self.get_all_prices(symbol)
        opportunities = []
        
        # Compare all venue pairs
        venue_ids = list(prices.keys())
        for i, venue1 in enumerate(venue_ids):
            for venue2 in venue_ids[i+1:]:
                ticker1 = prices[venue1]
                ticker2 = prices[venue2]
                
                # Check if we can buy on venue1 and sell on venue2
                buy_price = ticker1.get('ask')
                sell_price = ticker2.get('bid')
                
                if buy_price and sell_price:
                    spread = (sell_price - buy_price) / buy_price
                    
                    if spread > min_spread:
                        opportunities.append({
                            'type': 'cross_venue_arbitrage',
                            'buy_venue': venue1,
                            'sell_venue': venue2,
                            'buy_price': buy_price,
                            'sell_price': sell_price,
                            'spread': spread,
                            'spread_bps': spread * 10000,
                            'symbol': symbol,
                            'timestamp': datetime.now()
                        })
                
                # Check reverse direction
                buy_price = ticker2.get('ask')
                sell_price = ticker1.get('bid')
                
                if buy_price and sell_price:
                    spread = (sell_price - buy_price) / buy_price
                    
                    if spread > min_spread:
                        opportunities.append({
                            'type': 'cross_venue_arbitrage',
                            'buy_venue': venue2,
                            'sell_venue': venue1,
                            'buy_price': buy_price,
                            'sell_price': sell_price,
                            'spread': spread,
                            'spread_bps': spread * 10000,
                            'symbol': symbol,
                            'timestamp': datetime.now()
                        })
        
        # Sort by spread (highest first)
        opportunities.sort(key=lambda x: x['spread'], reverse=True)
        
        return opportunities
    
    def get_stats(self) -> Dict:
        """
        Get venue manager statistics
        
        Returns:
            Dict with stats
        """
        total = len(self.venues)
        connected = len(self.get_connected_venues())
        
        return {
            'total_venues': total,
            'connected_venues': connected,
            'disconnected_venues': total - connected,
            'venues': {
                vid: {
                    'connected': conn.connected,
                    'last_update': conn.last_update
                }
                for vid, conn in self.venues.items()
            }
        }
