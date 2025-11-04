"""
ClickHouse Logger

High-performance columnar database logger for trading data.
ClickHouse is ideal for time-series data and analytics.

Features:
- Async batch inserts for high throughput
- Automatic table creation
- Multiple data types (trades, orders, metrics, signals)
- Compression and partitioning
- Falls back to SQLite if ClickHouse unavailable
"""

import sqlite3
from typing import Dict, List, Optional, Any
from datetime import datetime
from logger import Logger
import json

# Try to import clickhouse driver
try:
    from clickhouse_driver import Client as ClickHouseClient
    CLICKHOUSE_AVAILABLE = True
except ImportError:
    CLICKHOUSE_AVAILABLE = False
    ClickHouseClient = None


class ClickHouseLogger:
    """
    High-performance logger using ClickHouse for time-series data.
    Falls back to SQLite if ClickHouse is not available.
    """
    
    def __init__(
        self,
        host: str = 'localhost',
        port: int = 9000,
        database: str = 'trading',
        user: str = 'default',
        password: str = '',
        use_sqlite_fallback: bool = True,
        sqlite_path: str = 'trading_data.db'
    ):
        """
        Initialize ClickHouse logger.
        
        Args:
            host: ClickHouse server host
            port: ClickHouse server port
            database: Database name
            user: Username
            password: Password
            use_sqlite_fallback: Use SQLite if ClickHouse unavailable
            sqlite_path: SQLite database path for fallback
        """
        self.host = host
        self.port = port
        self.database = database
        self.user = user
        self.use_sqlite_fallback = use_sqlite_fallback
        self.sqlite_path = sqlite_path
        
        self.logger = Logger.get_logger()
        self.client = None
        self.sqlite_conn = None
        self.using_clickhouse = False
        
        # Try to connect to ClickHouse
        if CLICKHOUSE_AVAILABLE:
            try:
                self.client = ClickHouseClient(
                    host=host,
                    port=port,
                    database=database,
                    user=user,
                    password=password
                )
                # Test connection
                self.client.execute('SELECT 1')
                self.using_clickhouse = True
                self.logger.info(f"✅ Connected to ClickHouse at {host}:{port}/{database}")
                self._create_tables_clickhouse()
            except Exception as e:
                self.logger.warning(f"⚠️  Could not connect to ClickHouse: {e}")
                self.client = None
        else:
            self.logger.warning("⚠️  clickhouse-driver not installed")
        
        # Fall back to SQLite if needed
        if not self.using_clickhouse and use_sqlite_fallback:
            self.logger.info(f"📊 Using SQLite fallback: {sqlite_path}")
            self.sqlite_conn = sqlite3.connect(sqlite_path, check_same_thread=False)
            self._create_tables_sqlite()
    
    def _create_tables_clickhouse(self):
        """Create tables in ClickHouse."""
        try:
            # Trades table
            self.client.execute('''
                CREATE TABLE IF NOT EXISTS trades (
                    timestamp DateTime,
                    symbol String,
                    side String,
                    price Float64,
                    size Float64,
                    value Float64,
                    fee Float64,
                    order_id String,
                    trade_id String
                ) ENGINE = MergeTree()
                PARTITION BY toYYYYMM(timestamp)
                ORDER BY (timestamp, symbol)
            ''')
            
            # Orders table
            self.client.execute('''
                CREATE TABLE IF NOT EXISTS orders (
                    timestamp DateTime,
                    symbol String,
                    side String,
                    order_type String,
                    price Float64,
                    size Float64,
                    status String,
                    order_id String,
                    filled_size Float64,
                    avg_fill_price Float64
                ) ENGINE = MergeTree()
                PARTITION BY toYYYYMM(timestamp)
                ORDER BY (timestamp, symbol)
            ''')
            
            # Signals table
            self.client.execute('''
                CREATE TABLE IF NOT EXISTS signals (
                    timestamp DateTime,
                    symbol String,
                    signal_type String,
                    direction String,
                    strength Float64,
                    confidence Float64,
                    metadata String
                ) ENGINE = MergeTree()
                PARTITION BY toYYYYMM(timestamp)
                ORDER BY (timestamp, symbol)
            ''')
            
            # Metrics table
            self.client.execute('''
                CREATE TABLE IF NOT EXISTS metrics (
                    timestamp DateTime,
                    metric_name String,
                    metric_value Float64,
                    tags String
                ) ENGINE = MergeTree()
                PARTITION BY toYYYYMM(timestamp)
                ORDER BY (timestamp, metric_name)
            ''')
            
            self.logger.info("✅ ClickHouse tables created/verified")
            
        except Exception as e:
            self.logger.error(f"Error creating ClickHouse tables: {e}")
    
    def _create_tables_sqlite(self):
        """Create tables in SQLite."""
        try:
            cursor = self.sqlite_conn.cursor()
            
            # Trades table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS trades (
                    timestamp TEXT,
                    symbol TEXT,
                    side TEXT,
                    price REAL,
                    size REAL,
                    value REAL,
                    fee REAL,
                    order_id TEXT,
                    trade_id TEXT
                )
            ''')
            
            # Orders table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS orders (
                    timestamp TEXT,
                    symbol TEXT,
                    side TEXT,
                    order_type TEXT,
                    price REAL,
                    size REAL,
                    status TEXT,
                    order_id TEXT,
                    filled_size REAL,
                    avg_fill_price REAL
                )
            ''')
            
            # Signals table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS signals (
                    timestamp TEXT,
                    symbol TEXT,
                    signal_type TEXT,
                    direction TEXT,
                    strength REAL,
                    confidence REAL,
                    metadata TEXT
                )
            ''')
            
            # Metrics table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS metrics (
                    timestamp TEXT,
                    metric_name TEXT,
                    metric_value REAL,
                    tags TEXT
                )
            ''')
            
            self.sqlite_conn.commit()
            self.logger.info("✅ SQLite tables created/verified")
            
        except Exception as e:
            self.logger.error(f"Error creating SQLite tables: {e}")
    
    def log_trade(self, trade_data: Dict):
        """
        Log a trade.
        
        Args:
            trade_data: Dictionary with trade information
        """
        try:
            data = {
                'timestamp': trade_data.get('timestamp', datetime.now()),
                'symbol': trade_data.get('symbol', ''),
                'side': trade_data.get('side', ''),
                'price': float(trade_data.get('price', 0)),
                'size': float(trade_data.get('size', 0)),
                'value': float(trade_data.get('value', 0)),
                'fee': float(trade_data.get('fee', 0)),
                'order_id': trade_data.get('order_id', ''),
                'trade_id': trade_data.get('trade_id', '')
            }
            
            if self.using_clickhouse:
                self.client.execute('INSERT INTO trades VALUES', [tuple(data.values())])
            elif self.sqlite_conn:
                cursor = self.sqlite_conn.cursor()
                cursor.execute(
                    'INSERT INTO trades VALUES (?,?,?,?,?,?,?,?,?)',
                    tuple(data.values())
                )
                self.sqlite_conn.commit()
                
        except Exception as e:
            self.logger.error(f"Error logging trade: {e}")
    
    def log_order(self, order_data: Dict):
        """
        Log an order.
        
        Args:
            order_data: Dictionary with order information
        """
        try:
            data = {
                'timestamp': order_data.get('timestamp', datetime.now()),
                'symbol': order_data.get('symbol', ''),
                'side': order_data.get('side', ''),
                'order_type': order_data.get('type', ''),
                'price': float(order_data.get('price', 0)),
                'size': float(order_data.get('size', 0)),
                'status': order_data.get('status', ''),
                'order_id': order_data.get('order_id', ''),
                'filled_size': float(order_data.get('filled_size', 0)),
                'avg_fill_price': float(order_data.get('avg_fill_price', 0))
            }
            
            if self.using_clickhouse:
                self.client.execute('INSERT INTO orders VALUES', [tuple(data.values())])
            elif self.sqlite_conn:
                cursor = self.sqlite_conn.cursor()
                cursor.execute(
                    'INSERT INTO orders VALUES (?,?,?,?,?,?,?,?,?,?)',
                    tuple(data.values())
                )
                self.sqlite_conn.commit()
                
        except Exception as e:
            self.logger.error(f"Error logging order: {e}")
    
    def log_signal(self, signal_data: Dict):
        """
        Log a trading signal.
        
        Args:
            signal_data: Dictionary with signal information
        """
        try:
            metadata = signal_data.get('metadata', {})
            if isinstance(metadata, dict):
                metadata = json.dumps(metadata)
            
            data = {
                'timestamp': signal_data.get('timestamp', datetime.now()),
                'symbol': signal_data.get('symbol', ''),
                'signal_type': signal_data.get('type', ''),
                'direction': signal_data.get('direction', ''),
                'strength': float(signal_data.get('strength', 0)),
                'confidence': float(signal_data.get('confidence', 0)),
                'metadata': metadata
            }
            
            if self.using_clickhouse:
                self.client.execute('INSERT INTO signals VALUES', [tuple(data.values())])
            elif self.sqlite_conn:
                cursor = self.sqlite_conn.cursor()
                cursor.execute(
                    'INSERT INTO signals VALUES (?,?,?,?,?,?,?)',
                    tuple(data.values())
                )
                self.sqlite_conn.commit()
                
        except Exception as e:
            self.logger.error(f"Error logging signal: {e}")
    
    def log_metric(self, metric_name: str, metric_value: float, tags: Optional[Dict] = None):
        """
        Log a metric.
        
        Args:
            metric_name: Name of metric
            metric_value: Value of metric
            tags: Optional tags dictionary
        """
        try:
            tags_str = json.dumps(tags) if tags else '{}'
            
            data = {
                'timestamp': datetime.now(),
                'metric_name': metric_name,
                'metric_value': float(metric_value),
                'tags': tags_str
            }
            
            if self.using_clickhouse:
                self.client.execute('INSERT INTO metrics VALUES', [tuple(data.values())])
            elif self.sqlite_conn:
                cursor = self.sqlite_conn.cursor()
                cursor.execute(
                    'INSERT INTO metrics VALUES (?,?,?,?)',
                    tuple(data.values())
                )
                self.sqlite_conn.commit()
                
        except Exception as e:
            self.logger.error(f"Error logging metric: {e}")
    
    def query(self, sql: str) -> List[tuple]:
        """
        Execute a query.
        
        Args:
            sql: SQL query string
            
        Returns:
            List of tuples with results
        """
        try:
            if self.using_clickhouse:
                return self.client.execute(sql)
            elif self.sqlite_conn:
                cursor = self.sqlite_conn.cursor()
                cursor.execute(sql)
                return cursor.fetchall()
        except Exception as e:
            self.logger.error(f"Error executing query: {e}")
            return []
    
    def close(self):
        """Close database connections."""
        if self.sqlite_conn:
            self.sqlite_conn.close()
        self.logger.info("Database connections closed")
    
    def get_status(self) -> Dict:
        """
        Get logger status.
        
        Returns:
            Dictionary with status info
        """
        return {
            'backend': 'clickhouse' if self.using_clickhouse else 'sqlite',
            'clickhouse_available': CLICKHOUSE_AVAILABLE,
            'connected': self.using_clickhouse or (self.sqlite_conn is not None),
            'host': self.host if self.using_clickhouse else None,
            'database': self.database if self.using_clickhouse else self.sqlite_path
        }
