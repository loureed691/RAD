"""
Real-time correlation matrix for multi-asset risk management
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from logger import Logger

class CorrelationMatrix:
    """Track real-time correlations between trading pairs"""
    
    def __init__(self, lookback_periods: int = 100):
        """
        Initialize correlation tracker
        
        Args:
            lookback_periods: Number of periods to use for correlation calculation
        """
        self.logger = Logger.get_logger()
        self.lookback_periods = lookback_periods
        self.price_history = {}  # symbol -> list of prices
        self.correlation_cache = {}
        self.last_update = {}
    
    def update_price(self, symbol: str, price: float, timestamp: datetime = None):
        """
        Update price history for a symbol
        
        Args:
            symbol: Trading pair symbol
            price: Current price
            timestamp: Optional timestamp (defaults to now)
        """
        if timestamp is None:
            timestamp = datetime.now()
        
        if symbol not in self.price_history:
            self.price_history[symbol] = []
        
        self.price_history[symbol].append({
            'timestamp': timestamp,
            'price': price
        })
        
        # Keep only recent history
        if len(self.price_history[symbol]) > self.lookback_periods:
            self.price_history[symbol] = self.price_history[symbol][-self.lookback_periods:]
        
        self.last_update[symbol] = timestamp
    
    def calculate_correlation(self, symbol1: str, symbol2: str) -> Optional[float]:
        """
        Calculate correlation between two symbols
        
        Args:
            symbol1: First symbol
            symbol2: Second symbol
            
        Returns:
            Correlation coefficient (-1 to 1) or None if insufficient data
        """
        if symbol1 not in self.price_history or symbol2 not in self.price_history:
            return None
        
        prices1 = [p['price'] for p in self.price_history[symbol1]]
        prices2 = [p['price'] for p in self.price_history[symbol2]]
        
        # Need matching lengths
        min_len = min(len(prices1), len(prices2))
        if min_len < 20:  # Need minimum data
            return None
        
        prices1 = prices1[-min_len:]
        prices2 = prices2[-min_len:]
        
        # Calculate returns
        returns1 = np.diff(prices1) / prices1[:-1]
        returns2 = np.diff(prices2) / prices2[:-1]
        
        # Calculate correlation
        if len(returns1) > 0 and len(returns2) > 0:
            correlation = np.corrcoef(returns1, returns2)[0, 1]
            return correlation
        
        return None
    
    def get_correlation_matrix(self, symbols: List[str]) -> pd.DataFrame:
        """
        Get full correlation matrix for list of symbols
        
        Args:
            symbols: List of symbols to calculate correlations for
            
        Returns:
            DataFrame with correlation matrix
        """
        n = len(symbols)
        matrix = np.ones((n, n))
        
        for i, sym1 in enumerate(symbols):
            for j, sym2 in enumerate(symbols):
                if i != j:
                    corr = self.calculate_correlation(sym1, sym2)
                    if corr is not None:
                        matrix[i, j] = corr
        
        df = pd.DataFrame(matrix, index=symbols, columns=symbols)
        return df
    
    def find_uncorrelated_pairs(self, symbols: List[str], 
                               threshold: float = 0.3) -> List[tuple]:
        """
        Find pairs of symbols with low correlation
        
        Args:
            symbols: List of symbols to check
            threshold: Maximum correlation to consider uncorrelated
            
        Returns:
            List of (symbol1, symbol2, correlation) tuples
        """
        uncorrelated = []
        
        for i, sym1 in enumerate(symbols):
            for j, sym2 in enumerate(symbols[i+1:], i+1):
                corr = self.calculate_correlation(sym1, sym2)
                if corr is not None and abs(corr) < threshold:
                    uncorrelated.append((sym1, sym2, corr))
        
        return sorted(uncorrelated, key=lambda x: abs(x[2]))
    
    def get_portfolio_correlation(self, positions: Dict[str, float]) -> float:
        """
        Calculate average correlation of portfolio positions
        
        Args:
            positions: Dict of symbol -> position_size
            
        Returns:
            Average correlation (0-1, lower is better)
        """
        symbols = list(positions.keys())
        if len(symbols) < 2:
            return 0.0
        
        correlations = []
        for i, sym1 in enumerate(symbols):
            for sym2 in symbols[i+1:]:
                corr = self.calculate_correlation(sym1, sym2)
                if corr is not None:
                    correlations.append(abs(corr))
        
        if correlations:
            return np.mean(correlations)
        return 0.0
    
    def get_diversification_score(self, positions: Dict[str, float]) -> float:
        """
        Calculate portfolio diversification score
        
        Args:
            positions: Dict of symbol -> position_size
            
        Returns:
            Diversification score (0-1, higher is better)
        """
        avg_correlation = self.get_portfolio_correlation(positions)
        
        # Diversification score: inverse of average correlation
        # Adjusted for number of positions
        num_positions = len(positions)
        position_bonus = min(num_positions / 10, 0.3)  # Up to 30% bonus for 10+ positions
        
        base_score = 1.0 - avg_correlation
        diversification_score = min(base_score + position_bonus, 1.0)
        
        return diversification_score
    
    def should_add_position(self, new_symbol: str, 
                           existing_positions: List[str],
                           max_correlation: float = 0.7) -> tuple[bool, str]:
        """
        Determine if adding a position would hurt diversification
        
        Args:
            new_symbol: Symbol to potentially add
            existing_positions: List of current position symbols
            max_correlation: Maximum acceptable correlation
            
        Returns:
            Tuple of (should_add, reason)
        """
        if not existing_positions:
            return True, "First position"
        
        # Check correlation with each existing position
        high_correlations = []
        for existing_sym in existing_positions:
            corr = self.calculate_correlation(new_symbol, existing_sym)
            if corr is not None and abs(corr) > max_correlation:
                high_correlations.append((existing_sym, corr))
        
        if high_correlations:
            worst = max(high_correlations, key=lambda x: abs(x[1]))
            return False, f"High correlation with {worst[0]} ({worst[1]:.2f})"
        
        return True, "Acceptable diversification"
    
    def get_best_diversifier(self, current_positions: List[str],
                            candidates: List[str]) -> Optional[str]:
        """
        Find the best symbol to add for diversification
        
        Args:
            current_positions: Current portfolio positions
            candidates: Potential symbols to add
            
        Returns:
            Best symbol for diversification or None
        """
        if not current_positions:
            return candidates[0] if candidates else None
        
        best_symbol = None
        lowest_avg_corr = float('inf')
        
        for candidate in candidates:
            correlations = []
            for pos in current_positions:
                corr = self.calculate_correlation(candidate, pos)
                if corr is not None:
                    correlations.append(abs(corr))
            
            if correlations:
                avg_corr = np.mean(correlations)
                if avg_corr < lowest_avg_corr:
                    lowest_avg_corr = avg_corr
                    best_symbol = candidate
        
        return best_symbol
    
    def calculate_dynamic_position_weights(self, symbols: List[str]) -> Dict[str, float]:
        """
        Calculate optimal position weights based on correlations
        Uses inverse correlation weighting
        
        Args:
            symbols: List of symbols to weight
            
        Returns:
            Dict of symbol -> weight (sum to 1.0)
        """
        if not symbols:
            return {}
        
        if len(symbols) == 1:
            return {symbols[0]: 1.0}
        
        # Calculate average correlation for each symbol
        avg_correlations = {}
        for sym in symbols:
            corrs = []
            for other in symbols:
                if sym != other:
                    corr = self.calculate_correlation(sym, other)
                    if corr is not None:
                        corrs.append(abs(corr))
            
            avg_correlations[sym] = np.mean(corrs) if corrs else 0.5
        
        # Weight inversely to correlation (less correlated = higher weight)
        inverse_corrs = {sym: 1.0 - corr for sym, corr in avg_correlations.items()}
        total = sum(inverse_corrs.values())
        
        if total > 0:
            weights = {sym: weight / total for sym, weight in inverse_corrs.items()}
        else:
            # Equal weights fallback
            equal_weight = 1.0 / len(symbols)
            weights = {sym: equal_weight for sym in symbols}
        
        return weights
    
    def get_correlation_report(self, symbols: List[str]) -> str:
        """
        Generate a formatted correlation report
        
        Args:
            symbols: List of symbols to report on
            
        Returns:
            Formatted string with correlation analysis
        """
        report = "\n" + "=" * 70 + "\n"
        report += "CORRELATION ANALYSIS REPORT\n"
        report += "=" * 70 + "\n"
        
        if len(symbols) < 2:
            report += "Need at least 2 symbols for correlation analysis\n"
            return report
        
        # Correlation matrix
        matrix = self.get_correlation_matrix(symbols)
        report += "\nCorrelation Matrix:\n"
        report += matrix.to_string()
        report += "\n"
        
        # Find highly correlated pairs
        high_corr = []
        for i, sym1 in enumerate(symbols):
            for sym2 in symbols[i+1:]:
                corr = self.calculate_correlation(sym1, sym2)
                if corr is not None and abs(corr) > 0.7:
                    high_corr.append((sym1, sym2, corr))
        
        if high_corr:
            report += "\n⚠️  High Correlations (>0.7):\n"
            for sym1, sym2, corr in sorted(high_corr, key=lambda x: abs(x[2]), reverse=True):
                report += f"  {sym1} - {sym2}: {corr:.2f}\n"
        else:
            report += "\n✓ No high correlations detected\n"
        
        # Portfolio diversification
        positions = {sym: 1.0 for sym in symbols}  # Equal weight for report
        div_score = self.get_diversification_score(positions)
        report += f"\nPortfolio Diversification Score: {div_score:.2f} (0-1, higher is better)\n"
        
        # Optimal weights
        weights = self.calculate_dynamic_position_weights(symbols)
        report += "\nOptimal Position Weights (correlation-adjusted):\n"
        for sym, weight in sorted(weights.items(), key=lambda x: x[1], reverse=True):
            report += f"  {sym}: {weight*100:.1f}%\n"
        
        report += "=" * 70 + "\n"
        
        return report
