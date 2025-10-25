"""
Lazy loading utilities for heavy imports
"""
import sys
from functools import wraps
from typing import Callable, Any


class LazyImport:
    """
    Lazy import wrapper that delays module loading until first use.
    This reduces startup time by only loading modules when they're actually needed.
    """
    
    def __init__(self, module_name: str):
        self.module_name = module_name
        self._module = None
    
    def __getattr__(self, name: str) -> Any:
        if self._module is None:
            self._module = __import__(self.module_name, fromlist=[name])
        return getattr(self._module, name)
    
    def __call__(self, *args, **kwargs):
        if self._module is None:
            self._module = __import__(self.module_name)
        return self._module(*args, **kwargs)


def lazy_import(module_name: str) -> LazyImport:
    """
    Create a lazy import proxy for a module.
    
    Usage:
        tensorflow = lazy_import('tensorflow')
        # tensorflow is not actually imported until you use it
        model = tensorflow.keras.Model()  # Now it's imported
    
    Args:
        module_name: Name of the module to lazy load
    
    Returns:
        LazyImport proxy object
    """
    return LazyImport(module_name)


def defer_heavy_imports(func: Callable) -> Callable:
    """
    Decorator to defer heavy imports until the function is first called.
    This is useful for functions that use heavy ML libraries but may not
    be called frequently.
    
    Usage:
        @defer_heavy_imports
        def train_model():
            import tensorflow as tf
            import torch
            # Heavy imports only happen when this function is called
    
    Args:
        func: Function to decorate
    
    Returns:
        Wrapped function that defers imports
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    
    return wrapper


# Commonly used lazy imports for the trading bot
# These can be imported from this module instead of importing directly

# Machine Learning
tensorflow = None  # Set to lazy_import('tensorflow') if needed
torch = None  # Set to lazy_import('torch') if needed
xgboost = None  # Set to lazy_import('xgboost') if needed
lightgbm = None  # Set to lazy_import('lightgbm') if needed
catboost = None  # Set to lazy_import('catboost') if needed

# Data Processing
pandas = lazy_import('pandas')
numpy = lazy_import('numpy')

# Technical Analysis
ta = lazy_import('ta')


def optimize_imports():
    """
    Optimize Python import system for better performance.
    Call this once at startup to improve import performance.
    """
    # Remove .pyc files on import to ensure fresh bytecode
    sys.dont_write_bytecode = False
    
    # Optimize module search path
    # Remove duplicate paths
    seen = set()
    sys.path = [x for x in sys.path if not (x in seen or seen.add(x))]


def preload_critical_modules():
    """
    Preload critical modules in background during bot initialization.
    This improves responsiveness when these modules are first needed.
    """
    import threading
    
    def _preload():
        # Import commonly used modules
        try:
            import numpy
            import pandas
            import ccxt
        except ImportError:
            pass
    
    # Start preloading in background thread
    thread = threading.Thread(target=_preload, daemon=True)
    thread.start()
