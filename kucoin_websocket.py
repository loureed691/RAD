"""
KuCoin Futures WebSocket Client for Real-Time Market Data
Handles ticker, candlestick, and orderbook data via WebSocket
Trading operations remain on REST API
"""
import json
import time
import threading
import websocket
import hmac
import hashlib
import base64
from typing import Dict, Optional, Callable, List
from datetime import datetime
from logger import Logger


class KuCoinWebSocket:
    """WebSocket client for KuCoin Futures real-time market data"""
    
    # KuCoin Futures WebSocket endpoints
    WS_PUBLIC_URL = "wss://ws-api-futures.kucoin.com"
    WS_PRIVATE_URL = "wss://ws-api-futures.kucoin.com"
    
    def __init__(self, api_key: str = None, api_secret: str = None, api_passphrase: str = None):
        """
        Initialize WebSocket client
        
        Args:
            api_key: Optional API key for private channels
            api_secret: Optional API secret for private channels
            api_passphrase: Optional API passphrase for private channels
        """
        self.logger = Logger.get_logger()
        self.api_key = api_key
        self.api_secret = api_secret
        self.api_passphrase = api_passphrase
        
        # WebSocket connection
        self.ws = None
        self.ws_thread = None
        self.connected = False
        self.should_reconnect = True
        
        # Data storage (thread-safe)
        self._data_lock = threading.Lock()
        self._tickers = {}  # symbol -> ticker data
        self._candles = {}  # (symbol, timeframe) -> list of candles
        self._orderbooks = {}  # symbol -> orderbook data
        
        # Subscriptions
        self._subscriptions = set()
        
        # Connection token (for authentication)
        self._token = None
        self._connect_id = None
        
        self.logger.info("🔌 KuCoin WebSocket client initialized")
    
    def connect(self):
        """Establish WebSocket connection"""
        if self.connected:
            self.logger.warning("WebSocket already connected")
            return
        
        try:
            # Get connection token from REST API (public endpoint)
            import requests
            response = requests.post(
                "https://api-futures.kucoin.com/api/v1/bullet-public",
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('code') == '200000':
                    self._token = data['data']['token']
                    instance_server = data['data']['instanceServers'][0]
                    ws_url = f"{instance_server['endpoint']}?token={self._token}"
                    
                    self.logger.info(f"📡 Connecting to KuCoin Futures WebSocket...")
                    
                    # Create WebSocket connection
                    self.ws = websocket.WebSocketApp(
                        ws_url,
                        on_open=self._on_open,
                        on_message=self._on_message,
                        on_error=self._on_error,
                        on_close=self._on_close
                    )
                    
                    # Start WebSocket in separate thread
                    self.ws_thread = threading.Thread(
                        target=self.ws.run_forever,
                        daemon=True
                    )
                    self.ws_thread.start()
                    
                    # Wait for connection
                    max_wait = 10
                    start = time.time()
                    while not self.connected and time.time() - start < max_wait:
                        time.sleep(0.1)
                    
                    if self.connected:
                        self.logger.info("✅ WebSocket connected successfully")
                    else:
                        self.logger.error("❌ WebSocket connection timeout")
                else:
                    self.logger.error(f"Failed to get WebSocket token: {data}")
            else:
                self.logger.error(f"Failed to get WebSocket token: HTTP {response.status_code}")
        except Exception as e:
            self.logger.error(f"Error connecting to WebSocket: {e}")
    
    def disconnect(self):
        """Close WebSocket connection"""
        self.should_reconnect = False
        if self.ws:
            self.ws.close()
        self.connected = False
        self.logger.info("🔌 WebSocket disconnected")
    
    def _on_open(self, ws):
        """Handle WebSocket connection opened"""
        self.connected = True
        self._connect_id = str(int(time.time() * 1000))
        self.logger.info("✅ WebSocket connection opened")
        
        # Send ping to keep connection alive
        self._start_ping()
        
        # Resubscribe to channels if any
        if self._subscriptions:
            self.logger.info(f"Resubscribing to {len(self._subscriptions)} channels...")
            for subscription in list(self._subscriptions):
                if subscription.startswith('ticker:'):
                    symbol = subscription.split(':')[1]
                    self._subscribe_ticker(symbol)
                elif subscription.startswith('candles:'):
                    parts = subscription.split(':')
                    symbol = parts[1]
                    timeframe = parts[2]
                    self._subscribe_candles(symbol, timeframe)
    
    def _on_message(self, ws, message):
        """Handle incoming WebSocket message"""
        try:
            data = json.loads(message)
            msg_type = data.get('type')
            
            if msg_type == 'welcome':
                self.logger.debug("Received welcome message")
            elif msg_type == 'ack':
                self.logger.debug(f"Subscription acknowledged: {data.get('id')}")
            elif msg_type == 'message':
                self._handle_data_message(data)
            elif msg_type == 'pong':
                self.logger.debug("Received pong")
            elif msg_type == 'error':
                # Only log error messages at WARNING level if they contain meaningful info
                error_code = data.get('code')
                error_msg = data.get('data', 'Unknown error')
                if error_code or error_msg != 'Unknown error':
                    self.logger.warning(f"WebSocket error message: {error_code} - {error_msg}")
            else:
                # Only log truly unknown message types
                if msg_type:
                    self.logger.debug(f"Received message type: {msg_type}")
        except Exception as e:
            self.logger.error(f"Error processing WebSocket message: {e}")
    
    def _on_error(self, ws, error):
        """Handle WebSocket error"""
        self.logger.error(f"WebSocket error: {error}")
    
    def _on_close(self, ws, close_status_code, close_msg):
        """Handle WebSocket connection closed"""
        self.connected = False
        self.logger.warning(f"WebSocket connection closed: {close_status_code} - {close_msg}")
        
        # Attempt reconnection if enabled
        if self.should_reconnect:
            self.logger.info("Attempting to reconnect WebSocket in 5 seconds...")
            time.sleep(5)
            self.connect()
    
    def _start_ping(self):
        """Start ping thread to keep connection alive"""
        def ping_loop():
            while self.connected and self.should_reconnect:
                try:
                    if self.ws:
                        ping_msg = {
                            "id": str(int(time.time() * 1000)),
                            "type": "ping"
                        }
                        self.ws.send(json.dumps(ping_msg))
                        self.logger.debug("Sent ping")
                except Exception as e:
                    self.logger.error(f"Error sending ping: {e}")
                time.sleep(20)  # Ping every 20 seconds
        
        ping_thread = threading.Thread(target=ping_loop, daemon=True)
        ping_thread.start()
    
    def _handle_data_message(self, data):
        """Handle data messages from WebSocket"""
        try:
            subject = data.get('subject')
            topic = data.get('topic', '')
            payload = data.get('data', {})
            
            # Handle ticker updates
            if 'ticker' in topic:
                symbol = topic.split(':')[1] if ':' in topic else None
                if symbol:
                    self._update_ticker(symbol, payload)
            
            # Handle candlestick updates
            elif 'candle' in topic:
                parts = topic.split(':')
                if len(parts) >= 2:
                    symbol = parts[1]
                    timeframe = parts[2] if len(parts) > 2 else '1min'
                    self._update_candle(symbol, timeframe, payload)
            
            # Handle orderbook updates
            elif 'level2' in topic or 'depth' in topic:
                symbol = topic.split(':')[1] if ':' in topic else None
                if symbol:
                    self._update_orderbook(symbol, payload)
        except Exception as e:
            self.logger.error(f"Error handling data message: {e}")
    
    def _update_ticker(self, symbol: str, data: dict):
        """Update ticker data (thread-safe)"""
        with self._data_lock:
            self._tickers[symbol] = {
                'symbol': symbol,
                'last': float(data.get('price', 0)),
                'bid': float(data.get('bestBidPrice', 0)),
                'ask': float(data.get('bestAskPrice', 0)),
                'volume': float(data.get('volume', 0)),
                'quoteVolume': float(data.get('turnover', 0)),
                'timestamp': int(data.get('ts', time.time() * 1000)),
                'datetime': datetime.fromtimestamp(int(data.get('ts', time.time() * 1000)) / 1000).isoformat()
            }
            self.logger.debug(f"Updated ticker for {symbol}: {self._tickers[symbol]['last']}")
    
    def _update_candle(self, symbol: str, timeframe: str, data: dict):
        """Update candlestick data (thread-safe)"""
        with self._data_lock:
            key = (symbol, timeframe)
            if key not in self._candles:
                self._candles[key] = []
            
            # Parse candle data
            candle = data.get('candles', [])
            if len(candle) >= 6:
                # Format: [timestamp, open, high, low, close, volume]
                new_candle = [
                    int(candle[0]),  # timestamp
                    float(candle[1]),  # open
                    float(candle[2]),  # high
                    float(candle[3]),  # low
                    float(candle[4]),  # close
                    float(candle[5])   # volume
                ]
                
                # Update or append candle
                candles = self._candles[key]
                if candles and candles[-1][0] == new_candle[0]:
                    # Update existing candle
                    candles[-1] = new_candle
                else:
                    # Append new candle
                    candles.append(new_candle)
                    # Keep only last 500 candles
                    if len(candles) > 500:
                        candles.pop(0)
                
                self.logger.debug(f"Updated candle for {symbol} {timeframe}")
    
    def _update_orderbook(self, symbol: str, data: dict):
        """Update orderbook data (thread-safe)"""
        with self._data_lock:
            self._orderbooks[symbol] = {
                'symbol': symbol,
                'bids': data.get('bids', []),
                'asks': data.get('asks', []),
                'timestamp': int(data.get('ts', time.time() * 1000))
            }
            self.logger.debug(f"Updated orderbook for {symbol}")
    
    def subscribe_ticker(self, symbol: str):
        """
        Subscribe to ticker updates for a symbol
        
        Args:
            symbol: Trading pair symbol (e.g., 'BTC/USDT:USDT')
        """
        if not self.connected:
            self.logger.warning("WebSocket not connected, cannot subscribe")
            return False
        
        # Convert symbol format (BTC/USDT:USDT -> BTCUSDT)
        kucoin_symbol = symbol.replace('/', '').replace(':', '')
        
        self._subscriptions.add(f'ticker:{symbol}')
        return self._subscribe_ticker(kucoin_symbol)
    
    def _subscribe_ticker(self, kucoin_symbol: str):
        """Internal method to subscribe to ticker"""
        try:
            sub_msg = {
                "id": str(int(time.time() * 1000)),
                "type": "subscribe",
                "topic": f"/contractMarket/ticker:{kucoin_symbol}",
                "privateChannel": False,
                "response": True
            }
            self.ws.send(json.dumps(sub_msg))
            self.logger.info(f"📊 Subscribed to ticker: {kucoin_symbol}")
            return True
        except Exception as e:
            self.logger.error(f"Error subscribing to ticker {kucoin_symbol}: {e}")
            return False
    
    def subscribe_candles(self, symbol: str, timeframe: str = '1h'):
        """
        Subscribe to candlestick updates for a symbol
        
        Args:
            symbol: Trading pair symbol (e.g., 'BTC/USDT:USDT')
            timeframe: Timeframe (1min, 5min, 15min, 30min, 1hour, 4hour, 1day, 1week)
        """
        if not self.connected:
            self.logger.warning("WebSocket not connected, cannot subscribe")
            return False
        
        # Convert symbol format
        kucoin_symbol = symbol.replace('/', '').replace(':', '')
        
        # Convert timeframe to KuCoin format
        tf_map = {
            '1m': '1min', '5m': '5min', '15m': '15min', '30m': '30min',
            '1h': '1hour', '4h': '4hour', '1d': '1day', '1w': '1week'
        }
        kucoin_tf = tf_map.get(timeframe, timeframe)
        
        self._subscriptions.add(f'candles:{symbol}:{timeframe}')
        return self._subscribe_candles(kucoin_symbol, kucoin_tf)
    
    def _subscribe_candles(self, kucoin_symbol: str, kucoin_tf: str):
        """Internal method to subscribe to candles"""
        try:
            sub_msg = {
                "id": str(int(time.time() * 1000)),
                "type": "subscribe",
                "topic": f"/contractMarket/candle:{kucoin_symbol}_{kucoin_tf}",
                "privateChannel": False,
                "response": True
            }
            self.ws.send(json.dumps(sub_msg))
            self.logger.info(f"📈 Subscribed to candles: {kucoin_symbol} {kucoin_tf}")
            return True
        except Exception as e:
            self.logger.error(f"Error subscribing to candles {kucoin_symbol}: {e}")
            return False
    
    def get_ticker(self, symbol: str) -> Optional[Dict]:
        """
        Get cached ticker data from WebSocket stream
        
        Args:
            symbol: Trading pair symbol
            
        Returns:
            Ticker dict or None if not available
        """
        with self._data_lock:
            ticker = self._tickers.get(symbol)
            if ticker:
                # Check if data is fresh (< 10 seconds old)
                age = time.time() * 1000 - ticker['timestamp']
                if age < 10000:  # 10 seconds
                    return ticker.copy()
                else:
                    self.logger.debug(f"Ticker data for {symbol} is stale ({age/1000:.1f}s old)")
            return None
    
    def get_ohlcv(self, symbol: str, timeframe: str = '1h', limit: int = 100) -> Optional[List]:
        """
        Get cached OHLCV data from WebSocket stream
        
        Args:
            symbol: Trading pair symbol
            timeframe: Timeframe
            limit: Maximum number of candles to return
            
        Returns:
            List of OHLCV candles or None if not available
        """
        with self._data_lock:
            key = (symbol, timeframe)
            candles = self._candles.get(key)
            if candles:
                # Return up to 'limit' most recent candles
                return candles[-limit:] if len(candles) > limit else candles.copy()
            return None
    
    def is_connected(self) -> bool:
        """Check if WebSocket is connected"""
        return self.connected
    
    def has_ticker(self, symbol: str) -> bool:
        """Check if ticker data is available for symbol"""
        with self._data_lock:
            return symbol in self._tickers
    
    def has_candles(self, symbol: str, timeframe: str) -> bool:
        """Check if candle data is available for symbol and timeframe"""
        with self._data_lock:
            return (symbol, timeframe) in self._candles
