"""
Market scanner to find the best trading pairs
"""
import time
from typing import List, Dict, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
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
    
    def scan_pair(self, symbol: str) -> Tuple[str, float, str, float, Dict]:
        """
        Scan a single trading pair
        
        Returns:
            Tuple of (symbol, score, signal, confidence, reasons)
        """
        try:
            # Get OHLCV data
            ohlcv = self.client.get_ohlcv(symbol, timeframe='1h', limit=100)
            if not ohlcv:
                self.logger.warning(f"No OHLCV data for {symbol}")
                return symbol, 0.0, 'HOLD', 0.0, {'error': 'No OHLCV data'}
            
            # Calculate indicators
            df = Indicators.calculate_all(ohlcv)
            if df.empty:
                self.logger.warning(f"Could not calculate indicators for {symbol}")
                return symbol, 0.0, 'HOLD', 0.0, {'error': 'No indicators'}
            
            # Generate signal
            signal, confidence, reasons = self.signal_generator.generate_signal(df)
            
            # Calculate score
            score = self.signal_generator.calculate_score(df)
            
            return symbol, score, signal, confidence, reasons
            
        except Exception as e:
            self.logger.error(f"Error scanning {symbol}: {e}")
            return symbol, 0.0, 'HOLD', 0.0, {}
    
    def scan_all_pairs(self, max_workers: int = 10) -> List[Dict]:
        """
        Scan all available trading pairs in parallel
        
        Returns:
            List of dicts with scan results sorted by score
        """
        self.logger.info("Starting market scan...")
        
        # Get all active futures
        futures = self.client.get_active_futures()
        if not futures:
            self.logger.warning("No active futures found")
            return []
        
        symbols = [f['symbol'] for f in futures]
        self.logger.info(f"Scanning {len(symbols)} trading pairs...")
        
        results = []
        
        # Scan pairs in parallel
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_symbol = {
                executor.submit(self.scan_pair, symbol): symbol 
                for symbol in symbols
            }
            
            for future in as_completed(future_to_symbol):
                symbol, score, signal, confidence, reasons = future.result()
                
                # Log all scanned pairs for debugging
                self.logger.info(f"Scanned {symbol}: Signal={signal}, Confidence={confidence:.2f}, Score={score:.2f}")
                
                if signal != 'HOLD' and score > 0:
                    results.append({
                        'symbol': symbol,
                        'score': score,
                        'signal': signal,
                        'confidence': confidence,
                        'reasons': reasons
                    })
                else:
                    self.logger.debug(f"Skipped {symbol}: signal={signal}, score={score:.2f}, reasons={reasons}")
        
        # Sort by score descending
        results.sort(key=lambda x: x['score'], reverse=True)
        
        self.logger.info(f"Market scan complete. Found {len(results)} trading opportunities")
        
        return results
    
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
                f"Confidence: {pair['confidence']:.2f}"
            )
        
        return best_pairs
