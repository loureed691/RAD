"""
Market scanner to find the best trading pairs
"""
import time
import threading
from typing import List, Dict, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
from kucoin_client import KuCoinClient
from indicators import Indicators
from signals import SignalGenerator
from logger import Logger
from config import Config

class MarketScanner:
    """Scan market for best trading opportunities"""
    
    def __init__(self, client: KuCoinClient):
        self.client = client
        self.signal_generator = SignalGenerator()
        self.logger = Logger.get_logger()
        self.scanning_logger = Logger.get_scanning_logger()
        
        # Caching mechanism to avoid redundant scans
        # IMPORTANT: Cache is ONLY used for market scanning to identify opportunities
        # Actual trading decisions ALWAYS use fresh live data from the exchange
        # This cache stores scan results (scores, signals) as fallback, NOT trading data
        self.cache = {}
        self.cache_duration = Config.CACHE_DURATION  # Use configurable cache duration
        self.last_full_scan = None
        self.scan_results_cache = []
        
        # Thread lock for cache access to prevent race conditions
        self._cache_lock = threading.Lock()
    
    def scan_pair(self, symbol: str) -> Tuple[str, float, str, float, Dict]:
        """
        Scan a single trading pair with caching as fallback only
        
        IMPORTANT: This method is used ONLY for market scanning to identify opportunities.
        Cached data is NEVER used for actual trading decisions - only as a fallback 
        during scanning when live data fetch fails. When execute_trade() is called,
        it ALWAYS fetches fresh live data from the exchange.
        
        Returns:
            Tuple of (symbol, score, signal, confidence, reasons)
        """
        self.scanning_logger.debug(f"--- Scanning {symbol} ---")
        
        # Always try to fetch live data first
        cache_key = symbol
        
        try:
            # Get OHLCV data for multiple timeframes
            self.scanning_logger.debug(f"  Fetching OHLCV data...")
            ohlcv_1h = self.client.get_ohlcv(symbol, timeframe='1h', limit=100)
            if not ohlcv_1h:
                self.logger.warning(f"No OHLCV data for {symbol}, checking cache...")
                self.scanning_logger.warning(f"  ⚠ No OHLCV data available, checking cache...")
                # Try to use cached data as fallback
                with self._cache_lock:
                    if cache_key in self.cache:
                        cached_data, timestamp = self.cache[cache_key]
                        cache_age = time.time() - timestamp
                        if cache_age < self.cache_duration:
                            self.logger.info(f"Using cached data as fallback for {symbol} (age: {int(cache_age)}s)")
                            self.scanning_logger.info(f"  ℹ Using cached data as fallback (age: {int(cache_age)}s)")
                            return cached_data
                # No cache available, return empty result
                result = (symbol, 0.0, 'HOLD', 0.0, {'error': 'No OHLCV data'})
                with self._cache_lock:
                    self.cache[cache_key] = (result, time.time())
                return result
            
            # Check if we have enough data
            if len(ohlcv_1h) < 50:
                self.logger.warning(f"Insufficient OHLCV data for {symbol}: only {len(ohlcv_1h)} candles (need 50+), checking cache...")
                self.scanning_logger.warning(f"  ⚠ Insufficient data: {len(ohlcv_1h)} candles (need 50+), checking cache...")
                # Try to use cached data as fallback
                with self._cache_lock:
                    if cache_key in self.cache:
                        cached_data, timestamp = self.cache[cache_key]
                        cache_age = time.time() - timestamp
                        if cache_age < self.cache_duration:
                            self.logger.info(f"Using cached data as fallback for {symbol} (age: {int(cache_age)}s)")
                            self.scanning_logger.info(f"  ℹ Using cached data as fallback (age: {int(cache_age)}s)")
                            return cached_data
                # No cache available, return empty result
                result = (symbol, 0.0, 'HOLD', 0.0, {'error': f'Insufficient data: {len(ohlcv_1h)} candles'})
                with self._cache_lock:
                    self.cache[cache_key] = (result, time.time())
                return result
            
            self.scanning_logger.debug(f"  1h data: {len(ohlcv_1h)} candles")
            
            # Get higher timeframe data for confirmation
            ohlcv_4h = self.client.get_ohlcv(symbol, timeframe='4h', limit=50)
            ohlcv_1d = self.client.get_ohlcv(symbol, timeframe='1d', limit=30)
            
            self.scanning_logger.debug(f"  4h data: {len(ohlcv_4h) if ohlcv_4h else 0} candles")
            self.scanning_logger.debug(f"  1d data: {len(ohlcv_1d) if ohlcv_1d else 0} candles")
            
            # Calculate indicators
            self.scanning_logger.debug(f"  Calculating indicators...")
            df_1h = Indicators.calculate_all(ohlcv_1h)
            if df_1h.empty:
                self.logger.warning(f"Could not calculate indicators for {symbol}, checking cache...")
                self.scanning_logger.warning(f"  ⚠ Indicator calculation failed, checking cache...")
                # Try to use cached data as fallback
                with self._cache_lock:
                    if cache_key in self.cache:
                        cached_data, timestamp = self.cache[cache_key]
                        cache_age = time.time() - timestamp
                        if cache_age < self.cache_duration:
                            self.logger.info(f"Using cached data as fallback for {symbol} (age: {int(cache_age)}s)")
                            self.scanning_logger.info(f"  ℹ Using cached data as fallback (age: {int(cache_age)}s)")
                            return cached_data
                # No cache available, return empty result
                result = (symbol, 0.0, 'HOLD', 0.0, {'error': 'Indicator calculation failed'})
                with self._cache_lock:
                    self.cache[cache_key] = (result, time.time())
                return result
            
            # Calculate indicators for higher timeframes
            df_4h = Indicators.calculate_all(ohlcv_4h) if ohlcv_4h and len(ohlcv_4h) >= 20 else None
            df_1d = Indicators.calculate_all(ohlcv_1d) if ohlcv_1d and len(ohlcv_1d) >= 20 else None
            
            # Generate signal with multi-timeframe analysis
            self.scanning_logger.debug(f"  Generating trading signal...")
            signal, confidence, reasons = self.signal_generator.generate_signal(df_1h, df_4h, df_1d)
            
            # Calculate score
            score = self.signal_generator.calculate_score(df_1h)
            
            self.scanning_logger.info(f"  Result: Signal={signal}, Score={score:.2f}, Confidence={confidence:.2%}")
            if reasons:
                self.scanning_logger.debug(f"  Reasons: {', '.join([f'{k}={v}' for k, v in reasons.items()])}")
            
            result = (symbol, score, signal, confidence, reasons)
            
            # Cache the result (thread-safe)
            with self._cache_lock:
                self.cache[cache_key] = (result, time.time())
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error scanning {symbol}: {e}, checking cache...")
            self.scanning_logger.error(f"  ✗ Error: {e}, checking cache...")
            # Try to use cached data as fallback
            with self._cache_lock:
                if cache_key in self.cache:
                    cached_data, timestamp = self.cache[cache_key]
                    cache_age = time.time() - timestamp
                    if cache_age < self.cache_duration:
                        self.logger.info(f"Using cached data as fallback for {symbol} (age: {int(cache_age)}s)")
                        self.scanning_logger.info(f"  ℹ Using cached data as fallback (age: {int(cache_age)}s)")
                        return cached_data
            # No cache available, return error result
            result = (symbol, 0.0, 'HOLD', 0.0, {'error': str(e)})
            with self._cache_lock:
                self.cache[cache_key] = (result, time.time())
            return result
    
    def _filter_high_priority_pairs(self, symbols: List[str], futures_data: List[Dict]) -> List[str]:
        """
        Smart filtering to prioritize high-quality pairs
        
        Args:
            symbols: List of all symbols
            futures_data: List of futures contract data with volume info
        
        Returns:
            Filtered list of high-priority symbols
        """
        # Create a mapping of symbol to volume data
        volume_map = {}
        for f in futures_data:
            symbol = f.get('symbol')
            volume_24h = float(f.get('turnoverOf24h', 0))  # 24h volume in USDT
            volume_map[symbol] = volume_24h
        
        # Filter by minimum volume (liquidity)
        min_volume = 1_000_000  # $1M daily volume minimum
        high_volume_pairs = [s for s in symbols if volume_map.get(s, 0) >= min_volume]
        
        # Sort by volume descending
        high_volume_pairs.sort(key=lambda s: volume_map.get(s, 0), reverse=True)
        
        # Take top 100 by volume (or all if less than 100)
        priority_pairs = high_volume_pairs[:100]
        
        self.logger.info(f"Filtered {len(priority_pairs)} high-volume pairs (>{min_volume/1e6:.1f}M daily volume)")
        
        return priority_pairs
    
    def scan_all_pairs(self, max_workers: int = None, use_cache: bool = True) -> List[Dict]:
        """
        Scan all available trading pairs in parallel with smart filtering
        
        Args:
            max_workers: Number of parallel workers (defaults to Config.MAX_WORKERS)
            use_cache: Whether to use cached results as fallback if live fetch fails
        
        Returns:
            List of dicts with scan results sorted by score
        """
        # Use configured value if not specified
        if max_workers is None:
            max_workers = Config.MAX_WORKERS
        
        self.scanning_logger.info(f"\n{'='*80}")
        self.scanning_logger.info(f"FULL MARKET SCAN - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.scanning_logger.info(f"{'='*80}")
        
        self.logger.info("Starting market scan with live data...")
        
        # Get all active futures
        self.scanning_logger.info("Fetching active futures contracts...")
        futures = self.client.get_active_futures()
        if not futures:
            self.logger.warning("No active futures found, checking for cached results...")
            self.scanning_logger.warning("⚠ No active futures found, checking for cached results...")
            # Try to use cached results as fallback
            if use_cache and self.scan_results_cache and self.last_full_scan:
                time_since_scan = (datetime.now() - self.last_full_scan).total_seconds()
                if time_since_scan < self.cache_duration:
                    self.logger.info(f"Using cached market scan results as fallback ({time_since_scan:.0f}s old)")
                    self.scanning_logger.info(f"Using cached results as fallback (age: {time_since_scan:.0f}s)")
                    self.scanning_logger.info(f"{'='*80}\n")
                    return self.scan_results_cache
            # No cache available
            self.scanning_logger.info(f"{'='*80}\n")
            return []
        
        symbols = [f['symbol'] for f in futures]
        self.scanning_logger.info(f"Total futures contracts: {len(symbols)}")
        
        # Smart filtering: prioritize high-volume pairs
        self.scanning_logger.info("Filtering high-priority pairs...")
        filtered_symbols = self._filter_high_priority_pairs(symbols, futures)
        
        self.logger.info(f"Scanning {len(filtered_symbols)} high-priority pairs (filtered from {len(symbols)} total)...")
        self.scanning_logger.info(f"Filtered to {len(filtered_symbols)} high-priority pairs")
        self.scanning_logger.info(f"Max workers: {max_workers}")
        self.scanning_logger.info(f"\nScanning pairs in parallel...")
        
        results = []
        scan_count = 0
        
        # Scan pairs in parallel
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_symbol = {
                executor.submit(self.scan_pair, symbol): symbol 
                for symbol in filtered_symbols
            }
            
            for future in as_completed(future_to_symbol):
                symbol, score, signal, confidence, reasons = future.result()
                scan_count += 1
                
                # Log all scanned pairs for debugging
                self.logger.debug(f"Scanned {symbol}: Signal={signal}, Confidence={confidence:.2f}, Score={score:.2f}")
                
                if signal != 'HOLD' and score > 0:
                    results.append({
                        'symbol': symbol,
                        'score': score,
                        'signal': signal,
                        'confidence': confidence,
                        'reasons': reasons
                    })
                    self.scanning_logger.info(f"✓ Found opportunity: {symbol} - {signal} (score: {score:.2f}, confidence: {confidence:.2%})")
                else:
                    self.logger.debug(f"Skipped {symbol}: signal={signal}, score={score:.2f}")
                    self.scanning_logger.debug(f"  Skipped {symbol}: {signal} (score: {score:.2f})")
        
        # Sort by score descending
        results.sort(key=lambda x: x['score'], reverse=True)
        
        self.logger.info(f"Market scan complete. Found {len(results)} trading opportunities")
        
        self.scanning_logger.info(f"\n{'='*40}")
        self.scanning_logger.info(f"SCAN SUMMARY")
        self.scanning_logger.info(f"{'='*40}")
        self.scanning_logger.info(f"Pairs scanned: {scan_count}")
        self.scanning_logger.info(f"Opportunities found: {len(results)}")
        
        if results:
            self.scanning_logger.info(f"\nTop opportunities:")
            for i, opp in enumerate(results[:10], 1):
                self.scanning_logger.info(f"  {i}. {opp['symbol']}: {opp['signal']} (score: {opp['score']:.2f}, conf: {opp['confidence']:.2%})")
        else:
            self.scanning_logger.info("No trading opportunities found")
        
        self.scanning_logger.info(f"{'='*80}\n")
        
        # Cache the results - thread-safe update
        with self._cache_lock:
            self.scan_results_cache = results
            self.last_full_scan = datetime.now()
        
        return results
    
    def _filter_high_priority_pairs(self, symbols: List[str], futures: List[Dict]) -> List[str]:
        """
        Filter to high-priority trading pairs based on volume and liquidity with enhanced logic
        
        Returns:
            List of filtered symbols
        """
        # Create a map for quick lookup
        symbol_map = {f['symbol']: f for f in futures}
        
        # Prioritize perpetual swaps and high-volume pairs
        priority_symbols = []
        
        # Major coins that should always be included (if they're perpetual swaps)
        major_coins = ['BTC', 'ETH', 'SOL', 'BNB', 'ADA', 'XRP', 'DOGE', 'MATIC', 'AVAX', 'DOT']
        
        for symbol in symbols:
            future_info = symbol_map.get(symbol, {})
            
            # Filter by volume if available (min $1M daily volume)
            volume_24h = future_info.get('quoteVolume', 0)
            is_low_volume = volume_24h > 0 and volume_24h < 1000000
            
            # Check if it's a major coin
            is_major = any(major in symbol for major in major_coins)
            
            # Check if it's a perpetual swap
            is_swap = future_info.get('swap', False)
            
            # Skip low volume non-major coins
            if is_low_volume and not is_major:
                self.logger.debug(f"Skipping {symbol} due to low volume: ${volume_24h:.0f}")
                continue
            
            # Always include major perpetual swaps
            if is_major and is_swap:
                priority_symbols.append(symbol)
            # Include other high-volume perpetual swaps
            elif is_swap and not is_low_volume:
                priority_symbols.append(symbol)
            # Major coins even if not perpetual swap (but warn)
            elif is_major:
                self.logger.debug(f"Skipping {symbol}: major coin but not a perpetual swap")
        
        # Enhanced fallback logic
        # If we filtered too aggressively, progressively relax constraints
        if len(priority_symbols) < 5 and len(symbols) > 10:
            self.logger.warning(f"Only found {len(priority_symbols)} priority pairs, relaxing volume filter")
            priority_symbols = []
            
            # Use a lower volume threshold (500k instead of 1M)
            for symbol in symbols:
                future_info = symbol_map.get(symbol, {})
                volume_24h = future_info.get('quoteVolume', 0)
                is_major = any(major in symbol for major in major_coins)
                is_swap = future_info.get('swap', False)
                
                # Relaxed volume filter: 500k threshold
                if volume_24h > 0 and volume_24h < 500000 and not is_major:
                    continue
                
                # Include all perpetual swaps
                if is_swap:
                    priority_symbols.append(symbol)
        
        # If still not enough, include all swaps regardless of volume (last resort)
        if len(priority_symbols) < 5 and len(symbols) > 10:
            self.logger.warning(f"Still only {len(priority_symbols)} pairs, removing volume filter entirely")
            priority_symbols = []
            for symbol in symbols:
                future_info = symbol_map.get(symbol, {})
                if future_info.get('swap', False):
                    priority_symbols.append(symbol)
        
        self.logger.info(f"Filtered to {len(priority_symbols)} priority pairs from {len(symbols)} total")
        return priority_symbols
    
    def get_best_pairs(self, n: int = 3) -> List[Dict]:
        """
        Get the top N best trading pairs
        
        Args:
            n: Number of pairs to return
        
        Returns:
            List of best trading opportunities
        """
        results = self.scan_all_pairs()
        best_pairs = results[:n]
        
        for pair in best_pairs:
            self.logger.info(
                f"Best pair: {pair['symbol']} - "
                f"Score: {pair['score']:.1f}, "
                f"Signal: {pair['signal']}, "
                f"Confidence: {pair['confidence']:.2f}, "
                f"Regime: {pair['reasons'].get('market_regime', 'N/A')}"
            )
        
        return best_pairs
    
    def clear_cache(self):
        """Clear all cached data (thread-safe)"""
        with self._cache_lock:
            self.cache.clear()
            self.scan_results_cache = []
            self.last_full_scan = None
        self.logger.info("Market scanner cache cleared")
