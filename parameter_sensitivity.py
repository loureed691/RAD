"""
Parameter Sensitivity Analysis for Trading Strategies

This module performs Monte Carlo simulation to identify fragile parameters
that can significantly impact strategy performance.

AUDIT FIX: HIGH-3 - Parameter sensitivity analysis
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Callable, Any
from dataclasses import dataclass
from concurrent.futures import ProcessPoolExecutor, as_completed
import json
from datetime import datetime


@dataclass
class ParameterSpec:
    """Specification for a parameter to test"""
    name: str
    base_value: Any
    param_type: str  # 'float', 'int', 'bool'
    min_value: Any = None
    max_value: Any = None
    variation_pct: float = 0.20  # ±20% by default

    def get_variations(self, num_samples: int = 10) -> List[Any]:
        """Generate parameter variations for sensitivity analysis"""
        variations = [self.base_value]  # Include base value

        if self.param_type == 'bool':
            return [True, False]

        elif self.param_type in ['int', 'float']:
            # Calculate variation range
            if self.min_value is not None and self.max_value is not None:
                # Use explicit bounds
                min_val = self.min_value
                max_val = self.max_value
            else:
                # Use percentage variation
                if self.base_value == 0:
                    min_val = -1
                    max_val = 1
                else:
                    range_size = abs(self.base_value * self.variation_pct)
                    min_val = self.base_value - range_size
                    max_val = self.base_value + range_size

            # Generate samples
            if self.param_type == 'int':
                samples = np.linspace(min_val, max_val, num_samples, dtype=int)
                variations.extend(np.unique(samples))
            else:
                samples = np.linspace(min_val, max_val, num_samples)
                variations.extend(samples)

        return list(set(variations))  # Remove duplicates


class ParameterSensitivityAnalyzer:
    """Analyze parameter sensitivity through Monte Carlo simulation"""

    def __init__(self, backtest_func: Callable, metric_name: str = 'sharpe_ratio'):
        """
        Initialize sensitivity analyzer

        Args:
            backtest_func: Function that takes params dict and returns results dict
            metric_name: Name of metric to analyze (e.g., 'sharpe_ratio', 'total_pnl')
        """
        self.backtest_func = backtest_func
        self.metric_name = metric_name
        self.results = []

    def analyze_single_parameter(self,
                                param_spec: ParameterSpec,
                                base_params: Dict[str, Any],
                                num_samples: int = 10) -> Dict:
        """
        Analyze sensitivity to a single parameter

        Args:
            param_spec: Parameter specification
            base_params: Base parameter dictionary
            num_samples: Number of samples to test

        Returns:
            Dict with sensitivity analysis results
        """
        variations = param_spec.get_variations(num_samples)

        results = []
        for value in variations:
            # Create params with variation
            test_params = base_params.copy()
            test_params[param_spec.name] = value

            # Run backtest
            try:
                backtest_results = self.backtest_func(test_params)
                metric_value = backtest_results.get(self.metric_name, 0)

                results.append({
                    'param_value': value,
                    'metric_value': metric_value,
                    'backtest_results': backtest_results
                })
            except Exception as e:
                print(f"Error testing {param_spec.name}={value}: {e}")
                results.append({
                    'param_value': value,
                    'metric_value': None,
                    'error': str(e)
                })

        # Calculate sensitivity metrics
        valid_results = [r for r in results if r['metric_value'] is not None]

        if len(valid_results) < 2:
            return {
                'parameter': param_spec.name,
                'base_value': param_spec.base_value,
                'sensitivity_score': 0,
                'stability': 'UNKNOWN',
                'results': results
            }

        # Calculate coefficient of variation (CV) as sensitivity measure
        metric_values = [r['metric_value'] for r in valid_results]
        mean_metric = np.mean(metric_values)
        std_metric = np.std(metric_values)
        cv = (std_metric / abs(mean_metric)) if mean_metric != 0 else float('inf')

        # Calculate range
        metric_range = max(metric_values) - min(metric_values)

        # Classify stability
        if cv < 0.1:
            stability = 'ROBUST'  # Low sensitivity
        elif cv < 0.3:
            stability = 'MODERATE'  # Medium sensitivity
        elif cv < 0.5:
            stability = 'FRAGILE'  # High sensitivity
        else:
            stability = 'CRITICAL'  # Very high sensitivity

        return {
            'parameter': param_spec.name,
            'base_value': param_spec.base_value,
            'num_samples': len(valid_results),
            'mean_metric': mean_metric,
            'std_metric': std_metric,
            'cv': cv,  # Coefficient of variation
            'metric_range': metric_range,
            'min_metric': min(metric_values),
            'max_metric': max(metric_values),
            'sensitivity_score': cv * 100,  # As percentage
            'stability': stability,
            'results': results
        }

    def analyze_all_parameters(self,
                              parameter_specs: List[ParameterSpec],
                              base_params: Dict[str, Any],
                              num_samples: int = 10,
                              parallel: bool = False) -> List[Dict]:
        """
        Analyze sensitivity for all parameters

        Args:
            parameter_specs: List of parameter specifications
            base_params: Base parameter dictionary
            num_samples: Number of samples per parameter
            parallel: Whether to use parallel processing

        Returns:
            List of sensitivity analysis results, sorted by sensitivity score
        """
        all_results = []

        if parallel:
            # Parallel processing (faster but more resource-intensive)
            with ProcessPoolExecutor() as executor:
                futures = {
                    executor.submit(
                        self.analyze_single_parameter,
                        spec,
                        base_params,
                        num_samples
                    ): spec for spec in parameter_specs
                }

                for future in as_completed(futures):
                    try:
                        result = future.result()
                        all_results.append(result)
                    except Exception as e:
                        spec = futures[future]
                        print(f"Error analyzing {spec.name}: {e}")
        else:
            # Sequential processing
            for spec in parameter_specs:
                print(f"Analyzing parameter: {spec.name}")
                result = self.analyze_single_parameter(spec, base_params, num_samples)
                all_results.append(result)

        # Sort by sensitivity score (highest first)
        all_results.sort(key=lambda x: x['sensitivity_score'], reverse=True)

        return all_results

    def generate_report(self, results: List[Dict]) -> str:
        """Generate human-readable sensitivity analysis report"""
        lines = [
            "=" * 80,
            "PARAMETER SENSITIVITY ANALYSIS REPORT",
            "=" * 80,
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"Metric Analyzed: {self.metric_name}",
            f"Parameters Tested: {len(results)}",
            "",
        ]

        # Summary by stability
        stability_counts = {}
        for result in results:
            stability = result['stability']
            stability_counts[stability] = stability_counts.get(stability, 0) + 1

        lines.append("STABILITY SUMMARY")
        lines.append("-" * 80)
        for stability in ['CRITICAL', 'FRAGILE', 'MODERATE', 'ROBUST', 'UNKNOWN']:
            count = stability_counts.get(stability, 0)
            if count > 0:
                lines.append(f"  {stability:10s}: {count} parameters")
        lines.append("")

        # Detailed results
        lines.append("DETAILED SENSITIVITY RESULTS")
        lines.append("=" * 80)
        lines.append(f"{'Parameter':<25} {'Base Value':<15} {'CV':<10} {'Range':<15} {'Stability':<12}")
        lines.append("-" * 80)

        for result in results:
            param = result['parameter']
            base_val = result['base_value']
            cv = result['cv']
            metric_range = result['metric_range']
            stability = result['stability']

            # Format values
            if isinstance(base_val, float):
                base_str = f"{base_val:.4f}"
            else:
                base_str = str(base_val)

            cv_str = f"{cv:.3f}" if cv != float('inf') else "∞"
            range_str = f"{metric_range:.4f}"

            lines.append(f"{param:<25} {base_str:<15} {cv_str:<10} {range_str:<15} {stability:<12}")

        lines.append("")
        lines.append("=" * 80)
        lines.append("RECOMMENDATIONS")
        lines.append("=" * 80)

        # Recommendations for critical and fragile parameters
        critical_params = [r for r in results if r['stability'] in ['CRITICAL', 'FRAGILE']]

        if critical_params:
            lines.append("\n⚠️  WARNING: The following parameters are highly sensitive:")
            lines.append("These parameters require careful tuning and robust defaults.\n")

            for result in critical_params:
                lines.append(f"  • {result['parameter']} (CV: {result['cv']:.2f}, Stability: {result['stability']})")
                lines.append(f"    Base: {result['base_value']}, "
                           f"Range: {result['min_metric']:.4f} to {result['max_metric']:.4f}")
                lines.append(f"    Recommendation: Use robust optimization and test extensively")
                lines.append("")
        else:
            lines.append("\n✅ All parameters show good stability (CV < 0.5)")
            lines.append("Strategy is robust to parameter variations.")

        lines.append("=" * 80)
        lines.append("END OF SENSITIVITY ANALYSIS")
        lines.append("=" * 80)

        return "\n".join(lines)

    def save_results(self, results: List[Dict], filename: str = "sensitivity_analysis.json"):
        """Save results to JSON file"""

        def convert_to_json_serializable(obj):
            """Convert numpy types to Python native types"""
            if isinstance(obj, (np.integer, np.int64)):
                return int(obj)
            elif isinstance(obj, (np.floating, np.float64)):
                return float(obj)
            elif isinstance(obj, np.ndarray):
                return obj.tolist()
            elif isinstance(obj, dict):
                return {k: convert_to_json_serializable(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_to_json_serializable(item) for item in obj]
            elif obj is None or isinstance(obj, (str, int, float, bool)):
                return obj
            else:
                return str(obj)

        # Convert results to serializable format
        serializable_results = []
        for result in results:
            clean_result = convert_to_json_serializable(result)
            # Remove backtest_results to keep file size manageable
            if 'results' in clean_result:
                clean_result['results'] = [
                    {k: v for k, v in r.items() if k != 'backtest_results'}
                    for r in clean_result['results']
                ]
            serializable_results.append(clean_result)

        with open(filename, 'w') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'metric': self.metric_name,
                'results': serializable_results
            }, f, indent=2)

        print(f"Results saved to {filename}")


def example_usage():
    """Example usage of parameter sensitivity analysis"""

    # Define a mock backtest function
    def mock_backtest(params: Dict) -> Dict:
        # Simulate backtest results based on parameters
        leverage = params.get('leverage', 10)
        risk = params.get('risk_per_trade', 0.02)

        # Mock Sharpe ratio calculation (higher leverage + risk = higher variance)
        base_sharpe = 1.5
        volatility_impact = (leverage * risk) * 0.5
        sharpe = base_sharpe - volatility_impact + np.random.normal(0, 0.1)

        return {
            'sharpe_ratio': sharpe,
            'total_pnl': sharpe * 1000,
            'win_rate': 0.6
        }

    # Define parameters to test
    param_specs = [
        ParameterSpec('leverage', base_value=10, param_type='int', min_value=5, max_value=20),
        ParameterSpec('risk_per_trade', base_value=0.02, param_type='float', min_value=0.01, max_value=0.05),
        ParameterSpec('trailing_stop', base_value=0.02, param_type='float', min_value=0.01, max_value=0.05),
    ]

    base_params = {
        'leverage': 10,
        'risk_per_trade': 0.02,
        'trailing_stop': 0.02
    }

    # Run analysis
    analyzer = ParameterSensitivityAnalyzer(mock_backtest, metric_name='sharpe_ratio')
    results = analyzer.analyze_all_parameters(param_specs, base_params, num_samples=10)

    # Generate report
    report = analyzer.generate_report(results)
    print(report)

    # Save results
    analyzer.save_results(results)


if __name__ == "__main__":
    example_usage()
