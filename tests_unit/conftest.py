"""
Shared fixtures for unit tests
"""
import pytest
import numpy as np
import pandas as pd


@pytest.fixture
def sample_ohlcv_data():
    """Generate sample OHLCV data for testing indicators"""
    np.random.seed(42)  # Deterministic
    
    periods = 100
    dates = pd.date_range('2025-01-01', periods=periods, freq='1h')
    
    # Generate realistic price data
    base_price = 50000
    returns = np.random.normal(0.0001, 0.01, periods)
    prices = base_price * np.exp(np.cumsum(returns))
    
    df = pd.DataFrame({
        'timestamp': dates,
        'open': prices * (1 + np.random.uniform(-0.001, 0.001, periods)),
        'high': prices * (1 + np.random.uniform(0, 0.01, periods)),
        'low': prices * (1 - np.random.uniform(0, 0.01, periods)),
        'close': prices,
        'volume': np.random.uniform(100, 1000, periods)
    })
    
    return df


@pytest.fixture
def testnet_config():
    """Dummy testnet configuration for testing"""
    return {
        'api_key': 'dummy_test_key',
        'api_secret': 'dummy_test_secret',
        'api_passphrase': 'dummy_test_passphrase',
        'base_url': 'https://api-sandbox-futures.kucoin.com',
        'use_testnet': True,
        'enable_websocket': False
    }
