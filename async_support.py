"""
Asyncio Support Module

Provides async wrappers for concurrent operations in the trading bot.

Features:
- Concurrent market data fetching
- Parallel order placement
- Async event handling
- Non-blocking I/O operations
"""

import asyncio
from typing import Dict, List, Optional, Callable, Any
from concurrent.futures import ThreadPoolExecutor
from functools import partial
from collections import deque
import time
from logger import Logger


class AsyncTrading:
    """
    Async wrapper for trading operations.
    
    Enables concurrent execution of I/O-bound operations like:
    - Fetching prices from multiple symbols
    - Placing multiple orders simultaneously
    - Monitoring multiple positions
    """
    
    def __init__(self, max_workers: int = 10):
        """
        Initialize async trading wrapper.
        
        Args:
            max_workers: Maximum number of concurrent workers
        """
        self.max_workers = max_workers
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.logger = Logger.get_logger()
        
        self.logger.info(f"⚡ Async Trading initialized with {max_workers} workers")
    
    async def fetch_prices_concurrent(
        self,
        client: Any,
        symbols: List[str]
    ) -> Dict[str, Optional[float]]:
        """
        Fetch prices for multiple symbols concurrently.
        
        Args:
            client: Trading client with get_price method
            symbols: List of symbols to fetch
            
        Returns:
            Dictionary of symbol -> price
        """
        loop = asyncio.get_event_loop()
        
        async def fetch_one(symbol: str) -> tuple:
            try:
                # Run synchronous get_price in executor
                price = await loop.run_in_executor(
                    self.executor,
                    client.get_price,
                    symbol
                )
                return symbol, price
            except Exception as e:
                self.logger.error(f"Error fetching price for {symbol}: {e}")
                return symbol, None
        
        # Fetch all prices concurrently
        tasks = [fetch_one(symbol) for symbol in symbols]
        results = await asyncio.gather(*tasks)
        
        return dict(results)
    
    async def fetch_orderbooks_concurrent(
        self,
        client: Any,
        symbols: List[str]
    ) -> Dict[str, Optional[Dict]]:
        """
        Fetch order books for multiple symbols concurrently.
        
        Args:
            client: Trading client with get_orderbook method
            symbols: List of symbols to fetch
            
        Returns:
            Dictionary of symbol -> orderbook
        """
        loop = asyncio.get_event_loop()
        
        async def fetch_one(symbol: str) -> tuple:
            try:
                orderbook = await loop.run_in_executor(
                    self.executor,
                    client.get_orderbook,
                    symbol
                )
                return symbol, orderbook
            except Exception as e:
                self.logger.error(f"Error fetching orderbook for {symbol}: {e}")
                return symbol, None
        
        tasks = [fetch_one(symbol) for symbol in symbols]
        results = await asyncio.gather(*tasks)
        
        return dict(results)
    
    async def place_orders_concurrent(
        self,
        client: Any,
        orders: List[Dict]
    ) -> List[Dict]:
        """
        Place multiple orders concurrently.
        
        Args:
            client: Trading client with place_order method
            orders: List of order dictionaries
            
        Returns:
            List of order results
        """
        loop = asyncio.get_event_loop()
        
        async def place_one(order: Dict) -> Dict:
            try:
                result = await loop.run_in_executor(
                    self.executor,
                    partial(
                        client.place_order,
                        symbol=order['symbol'],
                        side=order['side'],
                        size=order['size'],
                        order_type=order.get('type', 'market'),
                        price=order.get('price')
                    )
                )
                return result
            except Exception as e:
                self.logger.error(f"Error placing order: {e}")
                return {'success': False, 'error': str(e)}
        
        tasks = [place_one(order) for order in orders]
        results = await asyncio.gather(*tasks)
        
        return results
    
    async def run_concurrent_tasks(
        self,
        tasks: List[Callable],
        timeout: Optional[float] = None
    ) -> List[Any]:
        """
        Run multiple synchronous tasks concurrently.
        
        Args:
            tasks: List of callable functions to execute
            timeout: Optional timeout in seconds
            
        Returns:
            List of results
        """
        loop = asyncio.get_event_loop()
        
        async def run_one(task: Callable) -> Any:
            try:
                return await loop.run_in_executor(self.executor, task)
            except Exception as e:
                self.logger.error(f"Error running task: {e}")
                return None
        
        task_coroutines = [run_one(task) for task in tasks]
        
        if timeout:
            results = await asyncio.wait_for(
                asyncio.gather(*task_coroutines),
                timeout=timeout
            )
        else:
            results = await asyncio.gather(*task_coroutines)
        
        return results
    
    async def monitor_positions_async(
        self,
        position_manager: Any,
        symbols: List[str],
        check_interval: float = 1.0,
        callback: Optional[Callable] = None
    ):
        """
        Monitor positions asynchronously with periodic checks.
        
        Args:
            position_manager: Position manager instance
            symbols: Symbols to monitor
            check_interval: Time between checks in seconds
            callback: Optional callback for position updates
        """
        while True:
            try:
                loop = asyncio.get_event_loop()
                
                # Get positions concurrently
                async def get_one(symbol: str):
                    return await loop.run_in_executor(
                        self.executor,
                        position_manager.get_position,
                        symbol
                    )
                
                tasks = [get_one(symbol) for symbol in symbols]
                positions = await asyncio.gather(*tasks)
                
                # Call callback if provided
                if callback:
                    await loop.run_in_executor(
                        self.executor,
                        callback,
                        dict(zip(symbols, positions))
                    )
                
                await asyncio.sleep(check_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error monitoring positions: {e}")
                await asyncio.sleep(check_interval)
    
    def close(self):
        """Shutdown executor."""
        self.executor.shutdown(wait=True)
        self.logger.info("Async trading executor shutdown")


class AsyncEventBus:
    """
    Async event bus for pub/sub pattern.
    
    Allows components to subscribe to events and be notified asynchronously.
    """
    
    def __init__(self):
        """Initialize event bus."""
        self.subscribers = {}  # event_name -> list of callbacks
        self.logger = Logger.get_logger()
        
        self.logger.info("📡 Async Event Bus initialized")
    
    def subscribe(self, event_name: str, callback: Callable):
        """
        Subscribe to an event.
        
        Args:
            event_name: Name of event to subscribe to
            callback: Callback function (can be sync or async)
        """
        if event_name not in self.subscribers:
            self.subscribers[event_name] = []
        
        self.subscribers[event_name].append(callback)
        self.logger.debug(f"Subscribed to event: {event_name}")
    
    def unsubscribe(self, event_name: str, callback: Callable):
        """
        Unsubscribe from an event.
        
        Args:
            event_name: Event name
            callback: Callback to remove
        """
        if event_name in self.subscribers:
            self.subscribers[event_name].remove(callback)
    
    async def publish(self, event_name: str, data: Any):
        """
        Publish an event to all subscribers.
        
        Args:
            event_name: Event name
            data: Event data
        """
        if event_name not in self.subscribers:
            return
        
        callbacks = self.subscribers[event_name]
        
        for callback in callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(data)
                else:
                    callback(data)
            except Exception as e:
                self.logger.error(f"Error in event callback for {event_name}: {e}")
    
    def get_subscribers(self, event_name: str) -> int:
        """Get number of subscribers for an event."""
        return len(self.subscribers.get(event_name, []))


class RateLimiter:
    """
    Async rate limiter for API calls.
    
    Prevents exceeding rate limits by throttling requests.
    """
    
    def __init__(self, max_calls: int, period: float):
        """
        Initialize rate limiter.
        
        Args:
            max_calls: Maximum number of calls allowed
            period: Time period in seconds
        """
        self.max_calls = max_calls
        self.period = period
        self.calls = deque()  # Using deque for O(1) popleft operations
        self.lock = asyncio.Lock()
        self.logger = Logger.get_logger()
    
    async def acquire(self):
        """
        Acquire permission to make a call.
        
        Blocks if rate limit would be exceeded.
        """
        async with self.lock:
            now = time.time()
            
            # Remove old calls outside the time window using deque for O(1) popleft
            while self.calls and now - self.calls[0] >= self.period:
                self.calls.popleft()
            
            # Check if we need to wait
            if len(self.calls) >= self.max_calls:
                # Calculate wait time until oldest call expires
                oldest_call = self.calls[0]
                wait_time = self.period - (now - oldest_call)
                
                if wait_time > 0:
                    self.logger.debug(f"Rate limit: waiting {wait_time:.2f}s")
                    await asyncio.sleep(wait_time)
                    # Recurse to try again
                    return await self.acquire()
            
            # Record this call
            self.calls.append(time.time())
    
    async def __aenter__(self):
        """Context manager entry."""
        await self.acquire()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        pass


# Example usage functions

async def example_concurrent_price_fetch(client, symbols: List[str]):
    """
    Example: Fetch prices concurrently.
    
    Args:
        client: Trading client
        symbols: List of symbols
    """
    async_trading = AsyncTrading()
    
    start = time.time()
    prices = await async_trading.fetch_prices_concurrent(client, symbols)
    elapsed = time.time() - start
    
    print(f"Fetched {len(symbols)} prices in {elapsed:.2f}s")
    return prices


async def example_event_driven_trading():
    """Example: Event-driven trading with async event bus."""
    event_bus = AsyncEventBus()
    
    # Define event handlers
    async def on_price_update(data):
        print(f"Price updated: {data}")
    
    def on_order_fill(data):
        print(f"Order filled: {data}")
    
    # Subscribe to events
    event_bus.subscribe('price_update', on_price_update)
    event_bus.subscribe('order_fill', on_order_fill)
    
    # Publish events
    await event_bus.publish('price_update', {'symbol': 'BTCUSDT', 'price': 50000})
    await event_bus.publish('order_fill', {'order_id': '123', 'size': 1.0})


async def example_rate_limited_calls(client):
    """Example: Rate-limited API calls."""
    # Allow 10 calls per second
    rate_limiter = RateLimiter(max_calls=10, period=1.0)
    
    for i in range(50):
        async with rate_limiter:
            # Make API call
            print(f"Call {i}")
            # await client.get_price('BTCUSDT')


if __name__ == '__main__':
    # Example: Run event-driven trading
    asyncio.run(example_event_driven_trading())
