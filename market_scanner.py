"""
Market scanner to find the best trading pairs
"""
import time
from typing import List, Dict, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
from kucoin_client import KuCoinClient
from indicators import Indicators
from signals import SignalGenerator
from logger import Logger

class MarketScanner:
    """Scan market for best trading opportunities"""
    
    def __init__(self, client: KuCoinClient):
        self.client = client
        self.signal_generator = SignalGenerator()
        self.logger = Logger.get_logger()
        
        # Caching mechanism to avoid redundant scans
        self.cache = {}
        self.cache_duration = 300  # 5 minutes cache
        self.last_full_scan = None
        self.scan_results_cache = []
    
    def scan_pair(self, symbol: str) -> Tuple[str, float, str, float, Dict]:
        """
        Scan a single trading pair with caching and multi-timeframe analysis
        
        Returns:
            Tuple of (symbol, score, signal, confidence, reasons)
        """
        # Check cache first
        cache_key = symbol
        if cache_key in self.cache:
            cached_data, timestamp = self.cache[cache_key]
            if time.time() - timestamp < self.cache_duration:
                self.logger.debug(f"Using cached data for {symbol}")
                return cached_data
        
        try:
            # Get OHLCV data for multiple timeframes
            ohlcv_1h = self.client.get_ohlcv(symbol, timeframe='1h', limit=100)
            if not ohlcv_1h:
                self.logger.warning(f"No OHLCV data for {symbol}")
                result = (symbol, 0.0, 'HOLD', 0.0, {'error': 'No OHLCV data'})
                self.cache[cache_key] = (result, time.time())
                return result
            
            # Check if we have enough data
            if len(ohlcv_1h) < 50:
                self.logger.warning(f"Insufficient OHLCV data for {symbol}: only {len(ohlcv_1h)} candles (need 50+)")
                result = (symbol, 0.0, 'HOLD', 0.0, {'error': f'Insufficient data: {len(ohlcv_1h)} candles'})
                self.cache[cache_key] = (result, time.time())
                return result
            
            # Get higher timeframe data for confirmation
            ohlcv_4h = self.client.get_ohlcv(symbol, timeframe='4h', limit=50)
            ohlcv_1d = self.client.get_ohlcv(symbol, timeframe='1d', limit=30)
            
            # Calculate indicators
            df_1h = Indicators.calculate_all(ohlcv_1h)
            if df_1h.empty:
                self.logger.warning(f"Could not calculate indicators for {symbol}")
                result = (symbol, 0.0, 'HOLD', 0.0, {'error': 'Indicator calculation failed'})
                self.cache[cache_key] = (result, time.time())
                return result
            
            # Calculate indicators for higher timeframes
            df_4h = Indicators.calculate_all(ohlcv_4h) if ohlcv_4h and len(ohlcv_4h) >= 20 else None
            df_1d = Indicators.calculate_all(ohlcv_1d) if ohlcv_1d and len(ohlcv_1d) >= 20 else None
            
            # Generate signal with multi-timeframe analysis
            signal, confidence, reasons = self.signal_generator.generate_signal(df_1h, df_4h, df_1d)
            
            # Calculate score
            score = self.signal_generator.calculate_score(df_1h)
            
            result = (symbol, score, signal, confidence, reasons)
            
            # Cache the result
            self.cache[cache_key] = (result, time.time())
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error scanning {symbol}: {e}")
            result = (symbol, 0.0, 'HOLD', 0.0, {'error': str(e)})
            self.cache[cache_key] = (result, time.time())
            return result
    
    def scan_all_pairs(self, max_workers: int = 10, use_cache: bool = True) -> List[Dict]:
        """
        Scan all available trading pairs in parallel with smart filtering
        
        Args:
            max_workers: Number of parallel workers
            use_cache: Whether to use cached results if available
        
        Returns:
            List of dicts with scan results sorted by score
        """
        # Check if we can use cached results
        if use_cache and self.scan_results_cache and self.last_full_scan:
            time_since_scan = (datetime.now() - self.last_full_scan).total_seconds()
            if time_since_scan < self.cache_duration:
                self.logger.info(f"Using cached market scan results ({time_since_scan:.0f}s old)")
                return self.scan_results_cache
        
        self.logger.info("Starting market scan...")
        
        # Get all active futures
        futures = self.client.get_active_futures()
        if not futures:
            self.logger.warning("No active futures found")
            return []
        
        symbols = [f['symbol'] for f in futures]
        
        # Smart filtering: prioritize high-volume pairs
        filtered_symbols = self._filter_high_priority_pairs(symbols, futures)
        
        self.logger.info(f"Scanning {len(filtered_symbols)} high-priority pairs (filtered from {len(symbols)} total)...")
        
        results = []
        
        # Scan pairs in parallel
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_symbol = {
                executor.submit(self.scan_pair, symbol): symbol 
                for symbol in filtered_symbols
            }
            
            for future in as_completed(future_to_symbol):
                symbol, score, signal, confidence, reasons = future.result()
                
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
                else:
                    self.logger.debug(f"Skipped {symbol}: signal={signal}, score={score:.2f}")
        
        # Sort by score descending
        results.sort(key=lambda x: x['score'], reverse=True)
        
        self.logger.info(f"Market scan complete. Found {len(results)} trading opportunities")
        
        # Cache the results
        self.scan_results_cache = results
        self.last_full_scan = datetime.now()
        
        return results
    
    def _filter_high_priority_pairs(self, symbols: List[str], futures: List[Dict]) -> List[str]:
        """
        Filter to high-priority trading pairs based on volume and liquidity
        
        Returns:
            List of filtered symbols
        """
        # Create a map for quick lookup
        symbol_map = {f['symbol']: f for f in futures}
        
        # Prioritize perpetual swaps and high-volume pairs
        priority_symbols = []
        
        for symbol in symbols:
            future_info = symbol_map.get(symbol, {})
            
            # Always include BTC, ETH, and other major pairs
            if any(major in symbol for major in ['BTC', 'ETH', 'SOL', 'BNB', 'ADA', 'XRP', 'DOGE', 'MATIC']):
                priority_symbols.append(symbol)
            # Include perpetual swaps (typically higher volume)
            elif future_info.get('swap', False):
                priority_symbols.append(symbol)
        
        # If we filtered too aggressively, include all
        if len(priority_symbols) < 10:
            return symbols
        
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
        """Clear all cached data"""
        self.cache.clear()
        self.scan_results_cache = []
        self.last_full_scan = None
        self.logger.info("Market scanner cache cleared")
