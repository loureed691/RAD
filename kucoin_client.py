"""
KuCoin Futures API Client Wrapper
"""
import ccxt
import time
import threading
import queue
from typing import List, Dict, Optional, Callable, Any
from logger import Logger
from enum import IntEnum
from kucoin_websocket import KuCoinWebSocket
from functools import wraps


def track_api_performance(func):
    """Decorator to track API call performance"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        success = True
        retried = False
        
        try:
            result = func(*args, **kwargs)
            return result
        except Exception as e:
            success = False
            # Check if this was a retry scenario
            if 'attempt' in str(e).lower() or 'retry' in str(e).lower():
                retried = True
            raise
        finally:
            duration = time.time() - start_time
            # Import here to avoid circular dependency
            try:
                from performance_monitor import get_monitor
                monitor = get_monitor()
                monitor.record_api_call(duration, success, retried)
            except Exception as monitor_exc:
                Logger.get_logger().debug(f"Performance monitoring failed in track_api_performance: {monitor_exc}")
    
    return wrapper


class APICallPriority(IntEnum):
    """Priority levels for API calls - lower number = higher priority"""
    CRITICAL = 1   # Order execution, position closing - MUST execute first
    HIGH = 2       # Position monitoring, balance checks
    NORMAL = 3     # Market scanning, ticker fetching
    LOW = 4        # Analytics, non-critical data

class KuCoinClient:
    """Wrapper for KuCoin Futures API using ccxt with API call prioritization"""
    
    def __init__(self, api_key: str, api_secret: str, api_passphrase: str, enable_websocket: bool = True):
        """Initialize KuCoin client with priority queue system and WebSocket support"""
        self.logger = Logger.get_logger()
        self.orders_logger = Logger.get_orders_logger()
        
        # Initialize API call priority queue system
        # This ensures trading operations always execute before scanning operations
        self._pending_critical_calls = 0  # Track critical calls in progress
        self._critical_call_lock = threading.Lock()
        self._closing = False  # Flag to indicate client is shutting down
        
        # RELIABILITY: Circuit breaker for API failures
        self._consecutive_failures = 0
        self._max_consecutive_failures = 5  # Threshold for circuit breaker
        self._circuit_breaker_active = False
        self._circuit_breaker_reset_time = None
        self._circuit_breaker_timeout = 60  # Seconds before retry
        
        # PRIORITY 1 SAFETY: Symbol metadata cache for exchange invariant validation
        self._symbol_metadata_cache = {}  # Cache symbol specs (min qty, price step, etc.)
        self._metadata_cache_time = None
        self._metadata_refresh_interval = 3600  # Refresh every hour
        self._metadata_lock = threading.Lock()
        
        # PRIORITY 1 SAFETY: Clock sync tracking
        self._server_time_offset = 0  # Milliseconds difference between local and server
        self._last_sync_check = None
        self._max_time_drift_ms = 5000  # Max 5 seconds drift allowed
        self._sync_check_interval = 3600  # Check every hour
        
        # PERFORMANCE: OHLCV candle cache to avoid refetching all historical data
        # Stores candles by (symbol, timeframe) key to minimize API calls
        self._candle_cache = {}  # {(symbol, timeframe): list of candles}
        self._candle_cache_lock = threading.Lock()
        self._max_cached_candles = 500  # Keep up to 500 candles per symbol/timeframe
        
        try:
            self.exchange = ccxt.kucoinfutures({
                'apiKey': api_key,
                'secret': api_secret,
                'password': api_passphrase,
                'enableRateLimit': True,
                # PERFORMANCE: Enable session reuse for better connection management
                'timeout': 30000,  # 30 second timeout
                'options': {
                    'defaultType': 'future',
                    'adjustForTimeDifference': True,
                },
            })
            self.logger.info("KuCoin Futures client initialized successfully")
            self.logger.info("✅ API Call Priority System: ENABLED (Trading operations have priority)")
            
            # PRIORITY 1 SAFETY: Verify clock sync at startup
            self._verify_clock_sync()
            
            # Set position mode to one-way (single position per symbol)
            # This prevents error 330011: "position mode does not match"
            try:
                self.exchange.set_position_mode(hedged=False)
                self.logger.info("Set position mode to ONE_WAY (hedged=False)")
            except Exception as e:
                # Some exchanges may not support this or it might already be set
                self.logger.warning(f"Could not set position mode: {e}")
            
            # Initialize WebSocket for real-time market data
            self.websocket = None
            self.enable_websocket = enable_websocket
            if enable_websocket:
                try:
                    self.websocket = KuCoinWebSocket(api_key, api_secret, api_passphrase)
                    self.websocket.connect()
                    if self.websocket.is_connected():
                        self.logger.info("✅ WebSocket API: ENABLED (Real-time market data)")
                        self.logger.info("   📊 Data Source: WebSocket for tickers & OHLCV")
                        self.logger.info("   💼 Trading: REST API for orders & positions")
                    else:
                        self.logger.warning("⚠️  WebSocket connection failed, will use REST API only")
                        self.websocket = None
                except Exception as e:
                    self.logger.warning(f"⚠️  Could not initialize WebSocket: {e}, will use REST API only")
                    self.websocket = None
                
        except Exception as e:
            self.logger.error(f"Failed to initialize KuCoin client: {e}")
            raise
    
    def _wait_for_critical_calls(self, priority: APICallPriority):
        """
        Wait if there are pending critical calls and current call is not critical.
        This ensures trading operations complete before scanning operations start.
        """
        if priority > APICallPriority.CRITICAL:
            # Non-critical call - wait for any pending critical calls to complete
            max_wait = 5.0  # Maximum 5 seconds wait
            start_time = time.time()
            
            while time.time() - start_time < max_wait:
                with self._critical_call_lock:
                    if self._pending_critical_calls == 0:
                        break
                time.sleep(0.05)  # Short sleep to avoid busy waiting
    
    def _track_critical_call(self, priority: APICallPriority, increment: bool):
        """Track critical API calls in progress"""
        if priority == APICallPriority.CRITICAL:
            with self._critical_call_lock:
                if increment:
                    self._pending_critical_calls += 1
                else:
                    self._pending_critical_calls = max(0, self._pending_critical_calls - 1)
    
    def _should_use_rest_api(self) -> bool:
        """
        Check if we should use REST API instead of WebSocket due to subscription limits.
        
        Returns:
            True if we should use REST API, False if we can use WebSocket
        """
        if not self.websocket or not self.websocket.is_connected():
            return True
        
        # Check if we're approaching subscription limit (leave buffer of 30)
        subscription_count = self.websocket.get_subscription_count()
        if subscription_count >= 350:
            self.logger.debug(f"WebSocket subscription count high ({subscription_count}), using REST API")
            return True
        
        return False
    
    def _check_circuit_breaker(self, is_critical: bool = False) -> bool:
        """
        Check if circuit breaker is active and should block API calls.
        
        Args:
            is_critical: If True, allows the call even during circuit breaker cooldown
                        (for critical operations like position updates, stop loss checks)
        
        Returns:
            True if call should proceed, False if blocked by circuit breaker
        """
        with self._critical_call_lock:
            if self._circuit_breaker_active:
                # Check if timeout has elapsed
                if time.time() >= self._circuit_breaker_reset_time:
                    self.logger.info("🔄 Circuit breaker timeout elapsed, attempting reset...")
                    self._circuit_breaker_active = False
                    self._consecutive_failures = 0
                    return True
                else:
                    # Critical operations can bypass circuit breaker
                    if is_critical:
                        remaining = int(self._circuit_breaker_reset_time - time.time())
                        self.logger.debug(f"⚠️ Circuit breaker active but allowing critical operation (retry in {remaining}s)")
                        return True
                    # Still in timeout period for non-critical operations
                    remaining = int(self._circuit_breaker_reset_time - time.time())
                    self.logger.warning(f"⛔ Circuit breaker active, retry in {remaining}s")
                    return False
            return True
    
    def _record_api_success(self):
        """Record successful API call for circuit breaker"""
        with self._critical_call_lock:
            if self._consecutive_failures > 0:
                self.logger.debug(f"✅ API call succeeded, resetting failure count from {self._consecutive_failures}")
            self._consecutive_failures = 0
    
    def _record_api_failure(self):
        """Record failed API call for circuit breaker"""
        with self._critical_call_lock:
            self._consecutive_failures += 1
            self.logger.warning(f"⚠️ API call failed ({self._consecutive_failures}/{self._max_consecutive_failures})")
            
            if self._consecutive_failures >= self._max_consecutive_failures:
                if not self._circuit_breaker_active:
                    self.logger.error(f"🚨 CIRCUIT BREAKER ACTIVATED after {self._consecutive_failures} consecutive failures")
                    self.logger.error(f"   Will retry after {self._circuit_breaker_timeout}s cooldown period")
                    self._circuit_breaker_active = True
                    self._circuit_breaker_reset_time = time.time() + self._circuit_breaker_timeout
    
    def _handle_api_error(self, func: Callable, max_retries: int = 3, 
                          exponential_backoff: bool = True, 
                          operation_name: str = "API call",
                          is_critical: bool = False) -> Any:
        """
        Handle API errors with retry logic and exponential backoff.
        
        Args:
            func: Function to execute (should be a lambda or callable)
            max_retries: Maximum number of retry attempts
            exponential_backoff: If True, use exponential backoff (1s, 2s, 4s, etc.)
            operation_name: Name of the operation for logging
            is_critical: If True, uses more aggressive retry for critical operations (closing positions, etc.)
            
        Returns:
            Result from func if successful, None if all retries failed
            
        Handles:
            - RateLimitExceeded (429): Retry with backoff
            - NetworkError: Retry with backoff
            - InsufficientFunds: Log and return None (no retry)
            - InvalidOrder: Log and return None (no retry)
            - AuthenticationError: Log and raise (critical error)
            - ExchangeError: Retry for transient errors, fail for permanent ones
        """
        last_exception = None
        
        # For critical operations (closing positions), use more retries
        # to ensure trades are executed even with transient errors
        effective_retries = max_retries * 3 if is_critical else max_retries
        
        for attempt in range(effective_retries):
            try:
                # RELIABILITY: Check circuit breaker before API call
                # Critical operations can bypass circuit breaker during cooldown
                if not self._check_circuit_breaker(is_critical=is_critical):
                    self.logger.warning(f"⛔ {operation_name} blocked by circuit breaker")
                    return None
                
                result = func()
                
                # Record success for circuit breaker
                self._record_api_success()
                
                # Log if we recovered from an error
                if attempt > 0:
                    self.logger.info(
                        f"{operation_name} succeeded after {attempt} retry attempt(s)"
                    )
                
                return result
                
            except ccxt.RateLimitExceeded as e:
                last_exception = e
                # Calculate backoff delay
                base_delay = 1  # Base delay in seconds
                if exponential_backoff:
                    delay = (2 ** attempt) * base_delay  # 1s, 2s, 4s, 8s...
                else:
                    delay = base_delay  # Fixed 1s delay
                
                # Cap maximum delay at 30 seconds
                delay = min(delay, 30)
                
                if attempt < effective_retries - 1:
                    self.logger.warning(
                        f"Rate limit exceeded for {operation_name} "
                        f"(attempt {attempt + 1}/{effective_retries}). "
                        f"Waiting {delay}s before retry... Error: {str(e)}"
                    )
                    time.sleep(delay)
                else:
                    self.logger.error(
                        f"Rate limit exceeded for {operation_name} after {effective_retries} attempts. "
                        f"Error: {str(e)}"
                    )
                    
            except ccxt.InsufficientFunds as e:
                # Don't retry - this is a permanent error until balance changes
                self.logger.error(
                    f"Insufficient funds for {operation_name}: {str(e)}"
                )
                return None
                
            except ccxt.InvalidOrder as e:
                # Don't retry - order parameters are invalid
                # Check if this is the expected "no position to close" error
                error_str = str(e)
                if '300009' in error_str or 'No open positions to close' in error_str:
                    # This is expected when trying to close an already-closed position
                    # Log at DEBUG level instead of ERROR
                    self.logger.debug(
                        f"Position already closed for {operation_name}: {error_str}"
                    )
                else:
                    # Other invalid order errors should still be logged as ERROR
                    self.logger.error(
                        f"Invalid order parameters for {operation_name}: {error_str}"
                    )
                return None
                
            except ccxt.AuthenticationError as e:
                # Don't retry - credentials are wrong, this is critical
                self.logger.error(
                    f"Authentication failed for {operation_name}: {str(e)}"
                )
                raise  # Re-raise to stop bot execution
                
            except ccxt.NetworkError as e:
                last_exception = e
                # Retry for network errors
                if exponential_backoff:
                    delay = (2 ** attempt)
                else:
                    delay = 2
                    
                delay = min(delay, 30)
                
                if attempt < effective_retries - 1:
                    self.logger.warning(
                        f"Network error for {operation_name} "
                        f"(attempt {attempt + 1}/{effective_retries}). "
                        f"Waiting {delay}s before retry... Error: {str(e)}"
                    )
                    time.sleep(delay)
                else:
                    self.logger.error(
                        f"Network error for {operation_name} after {effective_retries} attempts. "
                        f"Error: {str(e)}"
                    )
                    
            except ccxt.ExchangeError as e:
                last_exception = e
                error_str = str(e).lower()
                
                # Check for specific KuCoin error codes
                # 400 errors - usually permanent (bad request)
                if '400' in error_str or 'invalid' in error_str:
                    self.logger.error(
                        f"Invalid request for {operation_name}: {str(e)}"
                    )
                    return None
                    
                # 403 errors - permission denied (permanent)
                elif '403' in error_str or 'permission' in error_str or 'forbidden' in error_str:
                    self.logger.error(
                        f"Permission denied for {operation_name}: {str(e)}"
                    )
                    return None
                    
                # 429 errors - rate limit (should be caught above, but just in case)
                elif '429' in error_str or 'too many' in error_str:
                    if exponential_backoff:
                        delay = (2 ** attempt)
                    else:
                        delay = 2
                    delay = min(delay, 30)
                    
                    if attempt < effective_retries - 1:
                        self.logger.warning(
                            f"Rate limit error for {operation_name} "
                            f"(attempt {attempt + 1}/{effective_retries}). "
                            f"Waiting {delay}s before retry... Error: {str(e)}"
                        )
                        time.sleep(delay)
                    else:
                        self.logger.error(
                            f"Rate limit error for {operation_name} after {effective_retries} attempts. "
                            f"Error: {str(e)}"
                        )
                        
                # 500 errors - server error (transient, retry)
                elif '500' in error_str or '502' in error_str or '503' in error_str or '504' in error_str:
                    if exponential_backoff:
                        delay = (2 ** attempt)
                    else:
                        delay = 2
                    delay = min(delay, 30)
                    
                    if attempt < effective_retries - 1:
                        self.logger.warning(
                            f"Server error for {operation_name} "
                            f"(attempt {attempt + 1}/{effective_retries}). "
                            f"Waiting {delay}s before retry... Error: {str(e)}"
                        )
                        time.sleep(delay)
                    else:
                        self.logger.error(
                            f"Server error for {operation_name} after {effective_retries} attempts. "
                            f"Error: {str(e)}"
                        )
                else:
                    # Unknown exchange error - log and don't retry
                    self.logger.error(
                        f"Exchange error for {operation_name}: {str(e)}"
                    )
                    return None
                    
            except Exception as e:
                # Catch-all for unexpected errors
                last_exception = e
                self.logger.error(
                    f"Unexpected error for {operation_name}: {type(e).__name__}: {str(e)}"
                )
                # Don't retry unexpected errors
                return None
        
        # All retries exhausted
        if last_exception:
            self.logger.error(
                f"Failed {operation_name} after {effective_retries} attempts. "
                f"Last error: {type(last_exception).__name__}: {str(last_exception)}"
            )
            # Record failure for circuit breaker
            self._record_api_failure()
        
        return None
    
    def _execute_with_priority(self, func: Callable, priority: APICallPriority, 
                               call_name: str, *args, **kwargs) -> Any:
        """
        Execute an API call with priority handling.
        Critical calls (orders, position closing) execute immediately.
        Non-critical calls (scanning) wait for critical calls to complete.
        """
        # Wait for critical calls if this is a non-critical call
        self._wait_for_critical_calls(priority)
        
        # Track if this is a critical call
        self._track_critical_call(priority, increment=True)
        
        try:
            # Log priority for critical operations
            if priority == APICallPriority.CRITICAL:
                self.logger.debug(f"🔴 CRITICAL API call: {call_name}")
            
            # Execute the actual API call
            result = func(*args, **kwargs)
            return result
        finally:
            # Always decrement critical call counter
            self._track_critical_call(priority, increment=False)
    
    def get_active_futures(self, include_volume: bool = True) -> List[Dict]:
        """Get all active futures trading pairs (perpetual swaps and quarterly futures) - USDT pairs only
        
        This is a SCANNING operation with NORMAL priority.
        Will wait for any critical trading operations to complete first.
        
        Args:
            include_volume: If True, fetch ticker data to include 24h volume (adds API call overhead)
        
        Returns:
            List of futures with symbol, info, swap, future, and optionally quoteVolume
        """
        def _fetch():
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
        
        # Execute with NORMAL priority - will wait for CRITICAL operations
        return self._execute_with_priority(_fetch, APICallPriority.NORMAL, 'get_active_futures')
    
    def get_ticker(self, symbol: str, priority: APICallPriority = APICallPriority.HIGH) -> Optional[Dict]:
        """Get ticker information for a symbol
        
        Uses WebSocket data if available, falls back to REST API.
        
        Args:
            symbol: Trading pair symbol
            priority: Priority level (HIGH for position monitoring, NORMAL for scanning)
        
        Returns:
            Ticker dict or None
        """
        # Check if client is closing (only check during shutdown, not exchange availability)
        if getattr(self, '_closing', False):
            self.logger.debug(f"Skipping get_ticker({symbol}) - client is closing")
            return None
        
        # Try WebSocket first if enabled and connected
        if self.websocket and self.websocket.is_connected():
            # Check if we're approaching subscription limit and cleanup if needed
            if self._should_use_rest_api():
                # Fall through to REST API instead of subscribing
                pass
            else:
                ticker = self.websocket.get_ticker(symbol)
                if ticker:
                    self.logger.debug(f"Retrieved ticker for {symbol} from WebSocket")
                    return ticker
                else:
                    # Subscribe to ticker if not already subscribed
                    if not self.websocket.has_ticker(symbol):
                        self.logger.debug(f"Subscribing to ticker: {symbol}")
                        self.websocket.subscribe_ticker(symbol)
                        # Wait up to 500ms for ticker data, polling every 50ms
                        timeout = 0.5
                        interval = 0.05
                        waited = 0.0
                        ticker = None
                        while waited < timeout:
                            ticker = self.websocket.get_ticker(symbol)
                            if ticker:
                                return ticker
                            time.sleep(interval)
                            waited += interval
                    # Fall through to REST API if no WebSocket data
                    self.logger.debug(f"No WebSocket data for {symbol}, using REST API")
        
        # Fallback to REST API
        def _fetch():
            def _fetch_ticker():
                ticker = self.exchange.fetch_ticker(symbol)
                return ticker
            
            # Use error handling with retries
            # Mark HIGH/CRITICAL priority calls as critical for circuit breaker bypass
            is_critical = priority <= APICallPriority.HIGH
            result = self._handle_api_error(
                _fetch_ticker,
                max_retries=3,
                exponential_backoff=True,
                operation_name=f"get_ticker({symbol})",
                is_critical=is_critical
            )
            
            return result
        
        return self._execute_with_priority(_fetch, priority, f'get_ticker({symbol})')
    
    def get_ohlcv(self, symbol: str, timeframe: str = '1h', limit: int = 100) -> List:
        """Get OHLCV data for a symbol with caching and incremental updates
        
        Uses WebSocket data if available, falls back to REST API with caching.
        Caches candles and only fetches new ones since the last timestamp,
        reducing API calls and improving performance.
        
        This is typically used for SCANNING, so uses NORMAL priority by default.
        Will wait for critical trading operations to complete first.
        
        Args:
            symbol: Trading pair symbol
            timeframe: Timeframe (1h, 4h, 1d, etc.)
            limit: Number of candles to retrieve
            
        Returns:
            List of OHLCV candles
        """
        # Check if client is closing (only check during shutdown, not exchange availability)
        if getattr(self, '_closing', False):
            self.logger.debug(f"Skipping get_ohlcv({symbol}) - client is closing")
            return []
        
        # Try WebSocket first if enabled and connected
        if self.websocket and self.websocket.is_connected():
            # Use helper to check if we should use REST API due to subscription limit
            if self._should_use_rest_api():
                # Fall through to REST API instead of subscribing
                pass
            else:
                ohlcv = self.websocket.get_ohlcv(symbol, timeframe, limit)
                if ohlcv and len(ohlcv) >= min(50, limit):  # Ensure we have enough data
                    self.logger.debug(f"Retrieved {len(ohlcv)} candles for {symbol} {timeframe} from WebSocket")
                    return ohlcv
                else:
                    # Subscribe to candles if not already subscribed
                    if not self.websocket.has_candles(symbol, timeframe):
                        self.logger.debug(f"Subscribing to candles: {symbol} {timeframe}")
                        self.websocket.subscribe_candles(symbol, timeframe)
                        # Give it a moment to receive data
                        time.sleep(0.5)
                        ohlcv = self.websocket.get_ohlcv(symbol, timeframe, limit)
                        if ohlcv and len(ohlcv) >= min(50, limit):
                            return ohlcv
                    # Fall through to REST API if insufficient WebSocket data
                    if ohlcv:
                        self.logger.debug(f"Insufficient WebSocket data for {symbol} (got {len(ohlcv)}, need {min(50, limit)}), using REST API")
                    else:
                        self.logger.debug(f"No WebSocket data for {symbol} {timeframe}, using REST API")
        
        # Fallback to REST API with caching
        cache_key = (symbol, timeframe)
        
        # Check if we have cached candles (without holding lock for too long)
        cached_candles = None
        last_timestamp = None
        
        with self._candle_cache_lock:
            if cache_key in self._candle_cache:
                cached_candles = list(self._candle_cache[cache_key])  # Make a copy
                if cached_candles and len(cached_candles) >= limit:
                    last_timestamp = cached_candles[-1][0]  # First element is timestamp
        
        # If we have enough cached candles, fetch only new ones
        if cached_candles and last_timestamp is not None:
            # Calculate how many new candles we might need (estimate)
            # This is a heuristic - we fetch a small number of recent candles
            # to catch up with any new data since last fetch
            fetch_limit = 10  # Fetch only the last 10 candles to check for updates
            
            def _fetch_new():
                def _fetch_ohlcv():
                    # Fetch only recent candles
                    ohlcv = self.exchange.fetch_ohlcv(symbol, timeframe, limit=fetch_limit)
                    if not ohlcv:
                        return []
                    
                    self.logger.debug(f"Fetched {len(ohlcv)} recent candles for {symbol} from REST API")
                    return ohlcv
                
                # Use error handling with retries
                result = self._handle_api_error(
                    _fetch_ohlcv,
                    max_retries=3,
                    exponential_backoff=True,
                    operation_name=f"get_ohlcv({symbol})"
                )
                
                return result if result is not None else []
            
            # Execute with NORMAL priority to fetch new candles (outside of lock)
            new_candles = self._execute_with_priority(_fetch_new, APICallPriority.NORMAL, f'get_ohlcv({symbol})')
            
            if new_candles:
                # Merge new candles with cached ones
                with self._candle_cache_lock:
                    updated_candles = list(cached_candles)  # Use our local copy
                    
                    for candle in new_candles:
                        candle_timestamp = candle[0]
                        # Only add candles that are newer than our last cached candle
                        # or update the last candle if it's the same timestamp
                        if candle_timestamp > last_timestamp:
                            updated_candles.append(candle)
                        elif candle_timestamp == last_timestamp:
                            # Update the last candle (it may have changed if it's still forming)
                            updated_candles[-1] = candle
                    
                    # Keep only the most recent candles up to our max limit
                    if len(updated_candles) > self._max_cached_candles:
                        updated_candles = updated_candles[-self._max_cached_candles:]
                    
                    # Update cache
                    self._candle_cache[cache_key] = updated_candles
                    
                    # Return the requested number of candles
                    result = updated_candles[-limit:] if len(updated_candles) > limit else updated_candles
                    self.logger.debug(f"Returned {len(result)} cached+updated candles for {symbol} {timeframe}")
                    return result
            else:
                # No new candles fetched, return cached data
                result = cached_candles[-limit:] if len(cached_candles) > limit else cached_candles
                self.logger.debug(f"Returned {len(result)} cached candles for {symbol} {timeframe}")
                return result
        
        # No cache or insufficient cached data - fetch full dataset
        def _fetch():
            def _fetch_ohlcv():
                ohlcv = self.exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
                if not ohlcv:
                    self.logger.warning(f"Empty OHLCV data returned for {symbol}")
                    return []
                
                self.logger.debug(f"Fetched {len(ohlcv)} candles for {symbol} from REST API")
                return ohlcv
            
            # Use error handling with retries
            result = self._handle_api_error(
                _fetch_ohlcv,
                max_retries=3,
                exponential_backoff=True,
                operation_name=f"get_ohlcv({symbol})"
            )
            
            if result:
                # Cache the fetched candles
                with self._candle_cache_lock:
                    self._candle_cache[cache_key] = result
                    self.logger.debug(f"Cached {len(result)} candles for {symbol} {timeframe}")
            
            return result if result is not None else []
        
        # Execute with NORMAL priority - will wait for CRITICAL and HIGH operations
        return self._execute_with_priority(_fetch, APICallPriority.NORMAL, f'get_ohlcv({symbol})')
    
    def get_balance(self) -> Dict:
        """Get account balance - HIGH priority for position monitoring"""
        def _fetch():
            def _fetch_balance():
                balance = self.exchange.fetch_balance()
                return balance
            
            # Use error handling with retries
            # Balance checks are critical for risk management
            result = self._handle_api_error(
                _fetch_balance,
                max_retries=3,
                exponential_backoff=True,
                operation_name="get_balance",
                is_critical=True
            )
            
            return result if result is not None else {}
        
        return self._execute_with_priority(_fetch, APICallPriority.HIGH, 'get_balance')
    
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
    
    def _predict_slippage(self, order_size: float, levels: List, reference_price: float) -> float:
        """
        Predict slippage for an order based on order book depth
        
        Args:
            order_size: Size of the order in contracts
            levels: Order book levels (list of [price, amount])
            reference_price: Current market price
        
        Returns:
            Predicted slippage as percentage
        """
        if not levels or order_size <= 0:
            return 0.0
        
        try:
            cumulative_amount = 0.0
            weighted_price = 0.0
            
            for price, amount in levels:
                price_float = float(price)
                amount_float = float(amount)
                
                # Calculate how much of this level we'd consume
                remaining = order_size - cumulative_amount
                consumed = min(remaining, amount_float)
                
                # Add to weighted average
                weighted_price += price_float * consumed
                cumulative_amount += consumed
                
                if cumulative_amount >= order_size:
                    break
            
            if cumulative_amount > 0:
                avg_fill_price = weighted_price / cumulative_amount
                slippage = abs(avg_fill_price - reference_price) / reference_price
                return slippage
            
        except Exception as e:
            self.logger.debug(f"Error predicting slippage: {e}")
        
        return 0.0
    
    def _calculate_spread(self, order_book: Dict) -> float:
        """
        Calculate bid-ask spread as percentage
        
        Args:
            order_book: Order book with bids and asks
        
        Returns:
            Spread as percentage
        """
        try:
            if not order_book or not order_book.get('bids') or not order_book.get('asks'):
                return 0.0
            
            best_bid = float(order_book['bids'][0][0])
            best_ask = float(order_book['asks'][0][0])
            
            if best_bid > 0:
                spread = (best_ask - best_bid) / best_bid
                return spread
        except Exception as e:
            self.logger.debug(f"Error calculating spread: {e}")
        
        return 0.0
    
    def calculate_required_margin(self, symbol: str, amount: float, 
                                  price: float, leverage: int) -> float:
        """Calculate margin required to open a position
        
        Args:
            symbol: Trading pair symbol
            amount: Position size in contracts
            price: Entry price
            leverage: Leverage to use
            
        Returns:
            Required margin in USDT
        """
        try:
            # For futures: required_margin = (contracts * price * contract_size) / leverage
            # Most futures have contract_size = 1
            markets = self.exchange.load_markets()
            contract_size = 1
            if symbol in markets:
                contract_size = markets[symbol].get('contractSize', 1)
            
            # SAFETY: Validate inputs before calculation
            if leverage <= 0:
                self.logger.error(f"Invalid leverage: {leverage}, using 1x")
                leverage = 1
            if amount <= 0 or price <= 0:
                self.logger.error(f"Invalid amount ({amount}) or price ({price})")
                return 0
            
            position_value = amount * price * contract_size
            required_margin = position_value / leverage
            
            return required_margin
        except Exception as e:
            self.logger.error(f"Error calculating required margin: {e}")
            # Return conservative estimate with safety checks
            if leverage <= 0:
                leverage = 1
            return (amount * price) / leverage if (amount > 0 and price > 0) else 0
    
    def check_available_margin(self, symbol: str, amount: float, 
                               price: float, leverage: int) -> tuple[bool, float, str]:
        """Check if there's enough margin available to open a position
        
        Args:
            symbol: Trading pair symbol
            amount: Position size in contracts
            price: Entry price
            leverage: Leverage to use
            
        Returns:
            Tuple of (is_sufficient, available_margin, reason)
        """
        try:
            balance = self.get_balance()
            
            # Handle case where balance fetch fails or is empty
            if not balance or 'free' not in balance or 'USDT' not in balance.get('free', {}):
                # If we can't get balance, assume sufficient margin to avoid blocking trades
                # The exchange will reject if there's actually insufficient margin
                self.logger.debug("Could not determine available margin, proceeding with order")
                return True, 0, "Unable to verify margin, proceeding"
            
            available_margin = float(balance.get('free', {}).get('USDT', 0))
            
            required_margin = self.calculate_required_margin(symbol, amount, price, leverage)
            
            # Get contract size for accurate position value display
            markets = self.exchange.load_markets()
            contract_size = 1
            if symbol in markets:
                contract_size = markets[symbol].get('contractSize', 1)
            
            # Add 5% buffer for safety and fees
            required_with_buffer = required_margin * 1.05
            
            if available_margin < required_with_buffer:
                # Calculate actual position value including contract size
                position_value = amount * price * contract_size
                reason = (
                    f"Insufficient margin: available=${available_margin:.2f}, "
                    f"required=${required_with_buffer:.2f} (position value=${position_value:.2f}, "
                    f"leverage={leverage}x)"
                )
                return False, available_margin, reason
            
            return True, available_margin, "Sufficient margin available"
            
        except Exception as e:
            self.logger.error(f"Error checking available margin: {e}")
            # If error checking, proceed with order and let exchange handle it
            return True, 0, f"Error checking margin: {e}"
    
    def is_position_viable(self, symbol: str, amount: float, price: float, leverage: int) -> tuple[bool, str]:
        """Check if a position size is viable for trading
        
        Args:
            symbol: Trading pair symbol
            amount: Position size in contracts
            price: Entry price
            leverage: Leverage to use
            
        Returns:
            Tuple of (is_viable, reason)
        """
        try:
            # Get market limits
            limits = self.get_market_limits(symbol)
            
            # Check against exchange minimum amount
            if limits and limits['amount']['min']:
                min_amount = limits['amount']['min']
                if amount < min_amount:
                    return False, f"Position size {amount:.4f} below exchange minimum {min_amount}"
            
            # Get contract size for accurate position value
            markets = self.exchange.load_markets()
            contract_size = 1
            if symbol in markets:
                contract_size = markets[symbol].get('contractSize', 1)
            
            # Calculate position value
            position_value = amount * price * contract_size
            
            # Check against exchange minimum cost
            if limits and limits['cost']['min']:
                min_cost = limits['cost']['min']
                if position_value < min_cost:
                    return False, f"Position value ${position_value:.2f} below exchange minimum ${min_cost}"
            
            # Check that position value is meaningful (at least $1)
            if position_value < 1.0:
                return False, f"Position value ${position_value:.2f} too small to be meaningful"
            
            # Check that required margin is meaningful (at least $0.10)
            required_margin = self.calculate_required_margin(symbol, amount, price, leverage)
            if required_margin < 0.10:
                return False, f"Required margin ${required_margin:.4f} too small to be meaningful"
            
            return True, "Position is viable"
            
        except Exception as e:
            self.logger.error(f"Error checking position viability: {e}")
            # If we can't check, assume it's viable and let exchange handle it
            return True, "Unable to verify viability, proceeding"
    
    def adjust_position_for_margin(self, symbol: str, amount: float, price: float, 
                                   leverage: int, available_margin: float) -> tuple[float, int]:
        """Adjust position size and/or leverage to fit available margin
        
        Args:
            symbol: Trading pair symbol
            amount: Desired position size in contracts
            price: Entry price
            leverage: Desired leverage
            available_margin: Available margin in USDT
            
        Returns:
            Tuple of (adjusted_amount, adjusted_leverage)
        """
        try:
            # Check for zero or near-zero margin early to prevent division by zero
            if available_margin <= 0.01:
                self.logger.error(
                    f"Cannot adjust position: available margin ${available_margin:.4f} is too low "
                    f"(minimum required: $0.01)"
                )
                # Return minimal viable values that will fail viability check
                return 0.0, 1
            
            # Get contract size for accurate calculations
            markets = self.exchange.load_markets()
            contract_size = 1
            if symbol in markets:
                contract_size = markets[symbol].get('contractSize', 1)
            
            # Check for zero price to prevent division by zero
            if price <= 0:
                self.logger.error(f"Cannot adjust position: invalid price {price}")
                return 0.0, 1
            
            # Reserve 10% of available margin for safety and fees
            usable_margin = available_margin * 0.90
            
            # Calculate maximum position value we can take
            max_position_value = usable_margin * leverage
            
            # Calculate adjusted amount based on available margin
            adjusted_amount = max_position_value / (price * contract_size)
            
            # If adjusted amount is still too large, also reduce leverage
            if adjusted_amount > amount:
                adjusted_amount = amount
            
            # Validate adjusted amount
            adjusted_amount = self.validate_and_cap_amount(symbol, adjusted_amount)
            
            # If we still can't fit, reduce leverage
            required_margin = self.calculate_required_margin(symbol, adjusted_amount, price, leverage)
            if required_margin > usable_margin:
                # Calculate what leverage we can actually use (must include contract_size)
                position_value = adjusted_amount * price * contract_size
                # SAFETY: Guard against division by zero
                if usable_margin <= 0:
                    self.logger.error(f"Invalid usable_margin: {usable_margin}, cannot adjust leverage")
                    return 0, 1  # Return minimal values to prevent trading
                adjusted_leverage = int(position_value / usable_margin)
                adjusted_leverage = max(1, min(adjusted_leverage, leverage))
                
                self.logger.warning(
                    f"Reducing leverage from {leverage}x to {adjusted_leverage}x to fit available margin"
                )
                return adjusted_amount, adjusted_leverage
            
            self.logger.warning(
                f"Reducing position size from {amount:.4f} to {adjusted_amount:.4f} contracts "
                f"to fit available margin (${usable_margin:.2f})"
            )
            
            return adjusted_amount, leverage
            
        except Exception as e:
            self.logger.error(f"Error adjusting position for margin: {e}")
            # Return conservative values
            return amount * 0.5, max(1, leverage // 2)
    
    def create_market_order(self, symbol: str, side: str, amount: float, 
                           leverage: int = 10, max_slippage: float = 0.01,
                           validate_depth: bool = True, reduce_only: bool = False,
                           is_critical: bool = False) -> Optional[Dict]:
        """Create a market order with leverage and slippage protection
        
        🔴 CRITICAL PRIORITY: This order operation executes BEFORE any scanning operations.
        
        Args:
            symbol: Trading pair symbol
            side: 'buy' or 'sell'
            amount: Order amount in contracts
            leverage: Leverage to use
            max_slippage: Maximum acceptable slippage (default 1%)
            validate_depth: Check order book depth before large orders
            reduce_only: If True, order only reduces position (for closing positions)
            is_critical: If True, uses more aggressive retry for critical operations
        
        Returns:
            Order dict if successful, None otherwise
        """
        def _create_order():
            nonlocal leverage
            
            # PRIORITY 1 SAFETY: Validate order locally before submitting to exchange
            is_valid, rejection_reason = self.validate_order_locally(symbol, amount, 0)  # Price check comes later
            if not is_valid:
                self.logger.error(f"🛑 Order validation failed: {rejection_reason}")
                self.orders_logger.error(
                    f"Order rejected locally | Symbol: {symbol} | Side: {side} | "
                    f"Amount: {amount:.4f} | Reason: {rejection_reason}"
                )
                return None
            
            # Get current price first for margin checks (use HIGH priority for position-related ticker)
            ticker = self.get_ticker(symbol, priority=APICallPriority.HIGH)
            if not ticker:
                self.logger.error(f"Could not get ticker for {symbol}")
                return None
                
            reference_price = ticker['last']
            self.logger.debug(f"Reference price for {symbol}: {reference_price}")
            
            # Validate and cap amount to exchange limits
            validated_amount = self.validate_and_cap_amount(symbol, amount)
            
            # Skip margin check for reduce_only orders as they close positions
            if not reduce_only:
                # Check if we have enough margin for this position (error 330008 prevention)
                has_margin, available_margin, margin_reason = self.check_available_margin(
                    symbol, validated_amount, reference_price, leverage
                )
            
                if not has_margin:
                    self.logger.warning(f"Margin check failed: {margin_reason}")
                    # Try to adjust position to fit available margin
                    adjusted_amount, adjusted_leverage = self.adjust_position_for_margin(
                        symbol, validated_amount, reference_price, leverage, available_margin
                    )
                    
                    # Check if adjusted position is viable (meets exchange minimums and meaningful size)
                    is_viable, viability_reason = self.is_position_viable(
                        symbol, adjusted_amount, reference_price, adjusted_leverage
                    )
                    if not is_viable:
                        self.logger.error(
                            f"Cannot open position: adjusted position not viable - {viability_reason} "
                            f"(adjusted: {adjusted_amount:.4f}, desired: {validated_amount:.4f})"
                        )
                        return None
                    
                    # Use adjusted values
                    validated_amount = adjusted_amount
                    leverage = adjusted_leverage
                    self.logger.info(
                        f"Adjusted position to fit margin: {adjusted_amount:.4f} contracts at {adjusted_leverage}x leverage"
                    )
            
            # For large orders, check order book depth and predict slippage
            if validate_depth and validated_amount > 100:  # Threshold for "large" order
                order_book = self.get_order_book(symbol, limit=20)
                if order_book:
                    levels = order_book['bids'] if side == 'sell' else order_book['asks']
                    total_liquidity = sum(level[1] for level in levels)
                    
                    # Predict slippage based on order book
                    predicted_slippage = self._predict_slippage(
                        validated_amount, levels, reference_price
                    )
                    
                    if predicted_slippage > max_slippage:
                        self.logger.warning(
                            f"High predicted slippage for {symbol}: {predicted_slippage:.2%} "
                            f"(max: {max_slippage:.2%}). Consider reducing size or using limit order."
                        )
                        # Optionally reduce order size to fit liquidity
                        safe_amount = min(validated_amount, total_liquidity * 0.5)
                        if safe_amount < validated_amount * 0.7:
                            self.logger.warning(
                                f"Reducing order size from {validated_amount:.4f} to {safe_amount:.4f} "
                                f"to limit slippage"
                            )
                            validated_amount = safe_amount
                    
                    if total_liquidity < validated_amount * 1.5:
                        self.logger.warning(
                            f"Low liquidity for {symbol}: order size {validated_amount} vs "
                            f"book depth {total_liquidity:.2f}. Potential high slippage."
                        )
                    
                    # Check spread for timing
                    spread = self._calculate_spread(order_book)
                    if spread > 0.005:  # >0.5% spread
                        self.logger.warning(
                            f"Wide spread detected for {symbol}: {spread:.2%}. "
                            f"Consider waiting for tighter spread."
                        )
            
            # Use error handling wrapper for the actual order placement
            def _place_order():
                # Skip leverage/margin mode setting for reduce_only orders (closing positions)
                # Setting leverage on close can fail with error 330008 if all margin is in use
                if not reduce_only:
                    # Switch to cross margin mode first (fixes error 330006)
                    self.exchange.set_margin_mode('cross', symbol)
                    
                    # Set leverage with cross margin mode
                    self.exchange.set_leverage(leverage, symbol, params={"marginMode": "cross"})
                
                # Build order parameters
                params = {"marginMode": "cross"}
                if reduce_only:
                    params["reduceOnly"] = True
                
                # Create market order
                order = self.exchange.create_order(
                    symbol=symbol,
                    type='market',
                    side=side,
                    amount=validated_amount,
                    params=params
                )
                
                return order
            
            # Execute with error handling and retry logic
            order = self._handle_api_error(
                _place_order, 
                max_retries=3,
                exponential_backoff=True,
                operation_name=f"create_market_order({symbol}, {side})",
                is_critical=is_critical or reduce_only  # Closing positions is critical
            )
            
            if not order:
                return None
            
            # Wait briefly for order to be filled and fetch updated status
            # Market orders typically fill immediately, but we need to fetch the status to get fill details
            time.sleep(0.5)  # Brief pause to allow order to be processed
            if order.get('id'):
                try:
                    filled_order = self.exchange.fetch_order(order['id'], symbol)
                    # Update order with filled details if available
                    if filled_order:
                        order.update({
                            'status': filled_order.get('status', order.get('status')),
                            'average': filled_order.get('average', order.get('average')),
                            'filled': filled_order.get('filled', order.get('filled')),
                            'cost': filled_order.get('cost', order.get('cost')),
                            'timestamp': filled_order.get('timestamp', order.get('timestamp'))
                        })
                except Exception as e:
                    # This is expected for very new orders - log at DEBUG level
                    self.logger.debug(f"Could not fetch order status immediately (order may be too new): {e}")
            
            # Log order details to main logger
            avg_price = order.get('average') or order.get('price') or reference_price
            self.logger.info(
                f"Created {side} market order for {validated_amount} {symbol} "
                f"at {leverage}x leverage (avg fill: {avg_price})"
            )
            
            # Log detailed order information to orders logger
            self.orders_logger.info("=" * 80)
            self.orders_logger.info(f"{side.upper()} ORDER EXECUTED: {symbol}")
            self.orders_logger.info("-" * 80)
            self.orders_logger.info(f"  Order ID: {order.get('id', 'N/A')}")
            self.orders_logger.info(f"  Type: MARKET")
            self.orders_logger.info(f"  Side: {side.upper()}")
            self.orders_logger.info(f"  Symbol: {symbol}")
            self.orders_logger.info(f"  Amount: {validated_amount} contracts")
            self.orders_logger.info(f"  Leverage: {leverage}x")
            self.orders_logger.info(f"  Reference Price: {reference_price}")
            self.orders_logger.info(f"  Average Fill Price: {avg_price}")
            if order.get('filled'):
                self.orders_logger.info(f"  Filled Amount: {order.get('filled')}")
            if order.get('cost'):
                self.orders_logger.info(f"  Total Cost: {order.get('cost')}")
            self.orders_logger.info(f"  Status: {order.get('status', 'N/A')}")
            # Display timestamp exactly as KuCoin returns it (in milliseconds)
            timestamp = order.get('timestamp', 'N/A')
            self.orders_logger.info(f"  Timestamp: {timestamp}")
            
            # Check actual slippage if we have both prices
            if order.get('average'):
                actual_slippage = abs(order['average'] - reference_price) / reference_price
                self.orders_logger.info(f"  Slippage: {actual_slippage:.4%}")
                if actual_slippage > max_slippage:
                    self.orders_logger.warning(f"  ⚠ High slippage detected (threshold: {max_slippage:.2%})")
                    self.logger.warning(
                        f"High slippage detected: {actual_slippage:.2%} "
                        f"(reference: {reference_price}, filled: {order['average']})"
                    )
            self.orders_logger.info("=" * 80)
            self.orders_logger.info("")  # Empty line for readability
            
            return order
        
        # Execute with CRITICAL priority - this will block scanning operations
        return self._execute_with_priority(_create_order, APICallPriority.CRITICAL, f'create_market_order({symbol}, {side})')
    
    def create_limit_order(self, symbol: str, side: str, amount: float, 
                          price: float, leverage: int = 10, post_only: bool = False,
                          reduce_only: bool = False, is_critical: bool = False) -> Optional[Dict]:
        """Create a limit order with leverage.
        
        🔴 CRITICAL PRIORITY: This order operation executes BEFORE any scanning operations.

        Cross margin mode is enforced when setting leverage.
        
        Args:
            symbol: Trading pair symbol
            side: 'buy' or 'sell'
            amount: Order amount in contracts
            price: Limit price
            leverage: Leverage to use
            post_only: If True, ensures order is a maker order (reduces fees)
            reduce_only: If True, order only reduces position (safer exits)
            is_critical: If True, uses more aggressive retry for critical operations
        """
        def _create_order():
            nonlocal leverage
            # Validate and cap amount to exchange limits
            validated_amount = self.validate_and_cap_amount(symbol, amount)
            
            # Check if we have enough margin for this position (error 330008 prevention)
            # Skip margin check for reduce_only orders as they close positions
            if not reduce_only:
                has_margin, available_margin, margin_reason = self.check_available_margin(
                    symbol, validated_amount, price, leverage
                )
                
                if not has_margin:
                    self.logger.warning(f"Margin check failed: {margin_reason}")
                    # Try to adjust position to fit available margin
                    adjusted_amount, adjusted_leverage = self.adjust_position_for_margin(
                        symbol, validated_amount, price, leverage, available_margin
                    )
                    
                    # Check if adjusted position is viable (meets exchange minimums and meaningful size)
                    is_viable, viability_reason = self.is_position_viable(
                        symbol, adjusted_amount, price, adjusted_leverage
                    )
                    if not is_viable:
                        self.logger.error(
                            f"Cannot open position: adjusted position not viable - {viability_reason} "
                            f"(adjusted: {adjusted_amount:.4f}, desired: {validated_amount:.4f})"
                        )
                        return None
                    
                    # Use adjusted values
                    validated_amount = adjusted_amount
                    leverage = adjusted_leverage
                    self.logger.info(
                        f"Adjusted limit order to fit margin: {adjusted_amount:.4f} contracts at {adjusted_leverage}x leverage"
                    )
            
            # Use error handling wrapper for the actual order placement
            def _place_order():
                # Skip leverage/margin mode setting for reduce_only orders (closing positions)
                # Setting leverage on close can fail with error 330008 if all margin is in use
                if not reduce_only:
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
                
                return order
            
            # Execute with error handling and retry logic
            order = self._handle_api_error(
                _place_order,
                max_retries=3,
                exponential_backoff=True,
                operation_name=f"create_limit_order({symbol}, {side})",
                is_critical=is_critical or reduce_only  # Closing positions is critical
            )
            
            if not order:
                return None
            
            # Log order details to main logger
            self.logger.info(
                f"Created {side} limit order for {validated_amount} {symbol} at {price} "
                f"(leverage={leverage}x, post_only={post_only}, reduce_only={reduce_only})"
            )
            
            # Log detailed order information to orders logger
            self.orders_logger.info("=" * 80)
            self.orders_logger.info(f"{side.upper()} ORDER CREATED: {symbol}")
            self.orders_logger.info("-" * 80)
            self.orders_logger.info(f"  Order ID: {order.get('id', 'N/A')}")
            self.orders_logger.info(f"  Type: LIMIT")
            self.orders_logger.info(f"  Side: {side.upper()}")
            self.orders_logger.info(f"  Symbol: {symbol}")
            self.orders_logger.info(f"  Amount: {validated_amount} contracts")
            self.orders_logger.info(f"  Limit Price: {price}")
            self.orders_logger.info(f"  Leverage: {leverage}x")
            self.orders_logger.info(f"  Post Only: {post_only}")
            self.orders_logger.info(f"  Reduce Only: {reduce_only}")
            self.orders_logger.info(f"  Status: {order.get('status', 'N/A')}")
            self.orders_logger.info(f"  Timestamp: {order.get('timestamp', 'N/A')}")
            self.orders_logger.info("=" * 80)
            self.orders_logger.info("")  # Empty line for readability
            
            return order
        
        # Execute with CRITICAL priority
        return self._execute_with_priority(_create_order, APICallPriority.CRITICAL, f'create_limit_order({symbol}, {side})')
    
    def cancel_order(self, order_id: str, symbol: str) -> bool:
        """Cancel an order - CRITICAL priority for risk management"""
        def _cancel():
            def _do_cancel():
                self.exchange.cancel_order(order_id, symbol)
                return True
            
            # Execute with error handling
            result = self._handle_api_error(
                _do_cancel,
                max_retries=3,
                exponential_backoff=True,
                operation_name=f"cancel_order({order_id}, {symbol})"
            )
            
            if result:
                self.logger.info(f"Cancelled order {order_id} for {symbol}")
                
                # Log cancellation to orders logger
                self.orders_logger.info("=" * 80)
                self.orders_logger.info(f"ORDER CANCELLED: {symbol}")
                self.orders_logger.info("-" * 80)
                self.orders_logger.info(f"  Order ID: {order_id}")
                self.orders_logger.info(f"  Symbol: {symbol}")
                self.orders_logger.info("=" * 80)
                self.orders_logger.info("")  # Empty line for readability
                
                return True
            return False
        
        # Execute with CRITICAL priority
        return self._execute_with_priority(_cancel, APICallPriority.CRITICAL, f'cancel_order({order_id})')
    
    def get_open_positions(self) -> List[Dict]:
        """Get all open positions - HIGH priority for position monitoring"""
        def _fetch():
            try:
                positions = self.exchange.fetch_positions()
                open_positions = [pos for pos in positions if float(pos.get('contracts', 0)) > 0]
                return open_positions
            except Exception as e:
                self.logger.error(f"Error fetching positions: {e}")
                return []
        
        return self._execute_with_priority(_fetch, APICallPriority.HIGH, 'get_open_positions')
    
    def close_position(self, symbol: str, use_limit: bool = False, 
                      slippage_tolerance: float = 0.002, max_close_retries: int = 5) -> bool:
        """Close a position with optional limit order for better execution
        
        This method will retry multiple times to ensure the position is closed,
        as closing positions is a critical operation that should not fail due to
        transient network issues or rate limits.
        
        Args:
            symbol: Trading pair symbol
            use_limit: If True, uses limit order instead of market order
            slippage_tolerance: Maximum acceptable slippage (default 0.2%)
            max_close_retries: Maximum number of retries for the entire close operation (default 5)
        
        Returns:
            True if position closed successfully, False otherwise
        """
        for close_attempt in range(max_close_retries):
            try:
                positions = self.get_open_positions()
                position_found = False
                
                for pos in positions:
                    if pos['symbol'] == symbol:
                        position_found = True
                        contracts = float(pos['contracts'])
                        side = 'sell' if pos['side'] == 'long' else 'buy'
                        
                        # Extract leverage from position data (multi-source)
                        # 1. Try CCXT unified 'leverage' field
                        leverage = pos.get('leverage')
                        if leverage is not None:
                            try:
                                leverage = int(leverage)
                            except (ValueError, TypeError):
                                self.logger.warning(
                                    f"Invalid leverage value '{leverage}' for {symbol}, defaulting to 10x"
                                )
                                leverage = 10
                        else:
                            # 2. Try KuCoin-specific 'realLeverage' in raw info
                            info = pos.get('info', {})
                            real_leverage = info.get('realLeverage')
                            if real_leverage is not None:
                                try:
                                    leverage = int(real_leverage)
                                except (ValueError, TypeError):
                                    self.logger.warning(
                                        f"Invalid realLeverage value '{real_leverage}' for {symbol}, defaulting to 10x"
                                    )
                                    leverage = 10
                            else:
                                # 3. Default to 10x with warning
                                leverage = 10
                                self.logger.warning(
                                    f"Leverage not found for {symbol} when closing, defaulting to 10x"
                                )
                        
                        if use_limit:
                            # Get current market price
                            ticker = self.get_ticker(symbol)
                            if not ticker:
                                self.logger.error(f"Could not get ticker for {symbol}, falling back to market order")
                                order = self.create_market_order(symbol, side, abs(contracts), leverage, reduce_only=True, is_critical=True)
                            else:
                                current_price = ticker['last']
                                # Set limit price with slippage tolerance
                                if side == 'sell':
                                    limit_price = current_price * (1 - slippage_tolerance)
                                else:
                                    limit_price = current_price * (1 + slippage_tolerance)
                                
                                order = self.create_limit_order(
                                    symbol, side, abs(contracts), limit_price, leverage,
                                    reduce_only=True, is_critical=True
                                )
                        else:
                            order = self.create_market_order(symbol, side, abs(contracts), leverage, reduce_only=True, is_critical=True)
                        
                        if order:
                            self.logger.info(f"Closed position for {symbol} with {leverage}x leverage")
                            return True
                        else:
                            self.logger.error(
                                f"Failed to create close order for {symbol} "
                                f"(attempt {close_attempt + 1}/{max_close_retries})"
                            )
                            # If order creation failed, retry the entire close operation
                            if close_attempt < max_close_retries - 1:
                                retry_delay = min(2 ** close_attempt, 10)  # Exponential backoff, capped at 10s
                                self.logger.warning(
                                    f"Retrying close_position for {symbol} in {retry_delay}s..."
                                )
                                time.sleep(retry_delay)
                            continue
                
                # If position not found, it may have already been closed
                if not position_found:
                    self.logger.info(f"Position {symbol} not found (may already be closed)")
                    return True
                    
            except Exception as e:
                self.logger.error(
                    f"Error closing position {symbol} "
                    f"(attempt {close_attempt + 1}/{max_close_retries}): {e}"
                )
                if close_attempt < max_close_retries - 1:
                    retry_delay = min(2 ** close_attempt, 10)  # Exponential backoff, capped at 10s
                    self.logger.warning(
                        f"Retrying close_position for {symbol} in {retry_delay}s..."
                    )
                    time.sleep(retry_delay)
        
        # All retries exhausted
        self.logger.error(
            f"Failed to close position {symbol} after {max_close_retries} attempts. "
            f"Position may still be open!"
        )
        return False
    
    def create_stop_limit_order(self, symbol: str, side: str, amount: float,
                               stop_price: float, limit_price: float, 
                               leverage: int = 10, reduce_only: bool = False) -> Optional[Dict]:
        """Create a stop-limit order for stop loss or take profit
        
        🔴 CRITICAL PRIORITY: This order operation executes BEFORE any scanning operations.
        
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
        def _create_order():
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
                
                # Log order details to main logger
                self.logger.info(
                    f"Created {side} stop-limit order for {validated_amount} {symbol} "
                    f"(stop={stop_price}, limit={limit_price}, reduce_only={reduce_only})"
                )
                
                # Log detailed order information to orders logger
                self.orders_logger.info("=" * 80)
                self.orders_logger.info(f"{side.upper()} ORDER CREATED: {symbol}")
                self.orders_logger.info("-" * 80)
                self.orders_logger.info(f"  Order ID: {order.get('id', 'N/A')}")
                self.orders_logger.info(f"  Type: STOP-LIMIT")
                self.orders_logger.info(f"  Side: {side.upper()}")
                self.orders_logger.info(f"  Symbol: {symbol}")
                self.orders_logger.info(f"  Amount: {validated_amount} contracts")
                self.orders_logger.info(f"  Stop Price: {stop_price}")
                self.orders_logger.info(f"  Limit Price: {limit_price}")
                self.orders_logger.info(f"  Leverage: {leverage}x")
                self.orders_logger.info(f"  Reduce Only: {reduce_only}")
                self.orders_logger.info(f"  Status: {order.get('status', 'N/A')}")
                self.orders_logger.info(f"  Timestamp: {order.get('timestamp', 'N/A')}")
                self.orders_logger.info("=" * 80)
                self.orders_logger.info("")  # Empty line for readability
                
                return order
            except Exception as e:
                self.logger.error(f"Error creating stop-limit order: {e}")
                return None
        
        # Execute with CRITICAL priority
        return self._execute_with_priority(_create_order, APICallPriority.CRITICAL, f'create_stop_limit_order({symbol}, {side})')
    
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
    
    # PRIORITY 1 SAFETY: Clock Sync and Metadata Caching
    
    def _verify_clock_sync(self) -> bool:
        """
        Verify local time vs KuCoin server time and refuse to trade if drift > threshold
        
        Returns:
            True if clock sync is OK, False if drift is too large
        """
        try:
            
            
            # Get server time
            server_time = self.exchange.fetch_time()  # milliseconds
            local_time = int(time.time() * 1000)  # milliseconds
            
            # Calculate drift
            self._server_time_offset = server_time - local_time
            drift_ms = abs(self._server_time_offset)
            
            self._last_sync_check = time.time()
            
            if drift_ms > self._max_time_drift_ms:
                self.logger.critical(
                    f"⚠️  CLOCK DRIFT TOO LARGE: {drift_ms}ms (max: {self._max_time_drift_ms}ms)"
                )
                self.logger.critical(
                    f"   Server time: {server_time}, Local time: {local_time}"
                )
                self.logger.critical(
                    "   ❌ TRADING DISABLED - Fix clock sync to prevent nonce/signature errors"
                )
                return False
            else:
                self.logger.info(
                    f"✅ Clock sync OK: drift={drift_ms}ms (threshold: {self._max_time_drift_ms}ms)"
                )
                return True
                
        except Exception as e:
            self.logger.error(f"Error checking clock sync: {e}")
            # Fail safe - allow trading but log warning
            self.logger.warning("⚠️  Could not verify clock sync, proceeding with caution")
            return True
    
    def should_check_clock_sync(self) -> bool:
        """Check if it's time for hourly clock sync verification"""
        if self._last_sync_check is None:
            return True
        return (time.time() - self._last_sync_check) > self._sync_check_interval
    
    def verify_clock_sync_if_needed(self) -> bool:
        """
        Verify clock sync if enough time has passed (hourly check)
        
        Returns:
            True if sync is OK or check not needed, False if drift too large
        """
        if self.should_check_clock_sync():
            self.logger.info("⏰ Performing hourly clock sync check...")
            return self._verify_clock_sync()
        return True  # Check not needed yet
    
    def get_cached_symbol_metadata(self, symbol: str, force_refresh: bool = False) -> Optional[Dict]:
        """
        Get cached symbol metadata (min qty, price step, contract size) with scheduled refresh
        
        PRIORITY 1: Cache and validate exchange invariants locally before placing orders
        
        Args:
            symbol: Trading pair symbol
            force_refresh: Force refresh even if cache is valid
        
        Returns:
            Dictionary with symbol metadata or None if not available
        """
        current_time = time.time()
        
        with self._metadata_lock:
            # Check if cache needs refresh
            needs_refresh = (
                force_refresh or
                self._metadata_cache_time is None or
                (current_time - self._metadata_cache_time) > self._metadata_refresh_interval or
                symbol not in self._symbol_metadata_cache
            )
            
            if needs_refresh:
                # Refresh metadata for this symbol
                try:
                    markets = self.exchange.load_markets()
                    if symbol in markets:
                        market = markets[symbol]
                        
                        # Extract key metadata for order validation
                        metadata = {
                            'symbol': symbol,
                            'min_amount': market.get('limits', {}).get('amount', {}).get('min'),
                            'max_amount': market.get('limits', {}).get('amount', {}).get('max'),
                            'min_cost': market.get('limits', {}).get('cost', {}).get('min'),
                            'max_cost': market.get('limits', {}).get('cost', {}).get('max'),
                            'price_precision': market.get('precision', {}).get('price'),
                            'amount_precision': market.get('precision', {}).get('amount'),
                            'contract_size': market.get('contractSize', 1),
                            'type': market.get('type'),
                            'active': market.get('active', False),
                            'cached_at': current_time
                        }
                        
                        self._symbol_metadata_cache[symbol] = metadata
                        
                        # Update cache time only after successful refresh
                        self._metadata_cache_time = current_time
                        
                        self.logger.debug(
                            f"Cached metadata for {symbol}: "
                            f"min={metadata['min_amount']}, max={metadata['max_amount']}, "
                            f"contract_size={metadata['contract_size']}"
                        )
                        
                        return metadata
                    else:
                        self.logger.warning(f"Symbol {symbol} not found in markets")
                        return None
                        
                except Exception as e:
                    self.logger.error(f"Error caching symbol metadata for {symbol}: {e}")
                    return None
            
            # Return cached data
            return self._symbol_metadata_cache.get(symbol)
    
    def validate_order_locally(self, symbol: str, amount: float, price: float) -> tuple[bool, str]:
        """
        Validate order against cached exchange invariants BEFORE submitting to API
        
        PRIORITY 1: Reject invalid orders locally to avoid API churn
        
        Args:
            symbol: Trading pair symbol
            amount: Order amount in contracts
            price: Order price
        
        Returns:
            Tuple of (is_valid, rejection_reason)
        """
        try:
            # Get cached metadata
            metadata = self.get_cached_symbol_metadata(symbol)
            if not metadata:
                # If we can't get metadata, allow but log warning
                self.logger.warning(f"No metadata available for {symbol}, allowing order")
                return True, "metadata_unavailable"
            
            # Check if market is active
            if not metadata.get('active', False):
                return False, f"Market {symbol} is not active"
            
            # Validate minimum amount
            min_amount = metadata.get('min_amount')
            if min_amount and amount < min_amount:
                return False, f"Amount {amount:.4f} below minimum {min_amount}"
            
            # Validate maximum amount
            max_amount = metadata.get('max_amount')
            if max_amount and amount > max_amount:
                return False, f"Amount {amount:.4f} exceeds maximum {max_amount}"
            
            # Validate minimum cost (skip for market orders where price=0)
            if price > 0:
                cost = amount * price
                min_cost = metadata.get('min_cost')
                if min_cost and cost < min_cost:
                    return False, f"Order cost ${cost:.2f} below minimum ${min_cost:.2f}"
                
                # Validate maximum cost
                max_cost = metadata.get('max_cost')
                if max_cost and cost > max_cost:
                    return False, f"Order cost ${cost:.2f} exceeds maximum ${max_cost:.2f}"
            
            # All validations passed
            return True, "valid"
            
        except Exception as e:
            self.logger.error(f"Error validating order locally: {e}")
            # Fail safe - allow order but log error
            return True, f"validation_error: {str(e)}"
    
    def clear_candle_cache(self, symbol: str = None, timeframe: str = None):
        """
        Clear cached candles for a specific symbol/timeframe or all caches
        
        Args:
            symbol: Optional symbol to clear cache for. If None, clears all.
            timeframe: Optional timeframe to clear cache for. Required if symbol is provided.
        """
        with self._candle_cache_lock:
            if symbol and timeframe:
                # Clear specific cache entry
                cache_key = (symbol, timeframe)
                if cache_key in self._candle_cache:
                    del self._candle_cache[cache_key]
                    self.logger.debug(f"Cleared candle cache for {symbol} {timeframe}")
            elif symbol:
                # Clear all timeframes for a symbol
                keys_to_delete = [key for key in self._candle_cache if key[0] == symbol]
                for key in keys_to_delete:
                    del self._candle_cache[key]
                self.logger.debug(f"Cleared all candle caches for {symbol}")
            else:
                # Clear all caches
                self._candle_cache.clear()
                self.logger.info("Cleared all candle caches")
    
    def get_cache_stats(self) -> Dict:
        """
        Get statistics about the candle cache
        
        Returns:
            Dictionary with cache statistics
        """
        with self._candle_cache_lock:
            stats = {
                'total_entries': len(self._candle_cache),
                'entries': {}
            }
            for (symbol, timeframe), candles in self._candle_cache.items():
                key = f"{symbol}:{timeframe}"
                stats['entries'][key] = {
                    'candle_count': len(candles),
                    'oldest_timestamp': candles[0][0] if candles else None,
                    'newest_timestamp': candles[-1][0] if candles else None
                }
            return stats
    
    def close(self):
        """Close connections and cleanup resources"""
        if self.websocket:
            self.logger.info("Closing WebSocket connection...")
            try:
                self.websocket.disconnect()
            except Exception as e:
                self.logger.warning(f"Error disconnecting WebSocket: {e}")
            finally:
                self.websocket = None
        
        # Mark the exchange as closed to prevent further API calls
        if hasattr(self, 'exchange'):
            self._closing = True
