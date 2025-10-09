"""
PostgreSQL Database Integration for Trade History and Analytics
"""
import os
from typing import Dict, List, Optional
from datetime import datetime
from logger import Logger

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    POSTGRES_AVAILABLE = True
except ImportError:
    POSTGRES_AVAILABLE = False
    Logger.get_logger().warning("psycopg2 not available. Database features disabled.")

class TradingDatabase:
    """PostgreSQL database manager for trading bot"""
    
    def __init__(self, db_url: str = None):
        """
        Initialize database connection
        
        Args:
            db_url: PostgreSQL connection URL (postgresql://user:pass@host:port/dbname)
                   or None to use environment variable DATABASE_URL
        """
        self.logger = Logger.get_logger()
        self.db_url = db_url or os.getenv('DATABASE_URL')
        self.conn = None
        
        if not POSTGRES_AVAILABLE:
            self.logger.warning("Database features disabled (psycopg2 not installed)")
            return
        
        if not self.db_url:
            self.logger.info("No DATABASE_URL provided, database features disabled")
            return
        
        self.connect()
        self.create_tables()
    
    def connect(self):
        """Establish database connection"""
        if not POSTGRES_AVAILABLE or not self.db_url:
            return
        
        try:
            self.conn = psycopg2.connect(self.db_url)
            self.logger.info("Connected to PostgreSQL database")
        except Exception as e:
            self.logger.error(f"Error connecting to database: {e}")
            self.conn = None
    
    def create_tables(self):
        """Create necessary tables if they don't exist"""
        if not self.conn:
            return
        
        try:
            cursor = self.conn.cursor()
            
            # Trades table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS trades (
                    id SERIAL PRIMARY KEY,
                    timestamp TIMESTAMP NOT NULL,
                    symbol VARCHAR(50) NOT NULL,
                    side VARCHAR(10) NOT NULL,
                    entry_price DECIMAL(20, 8) NOT NULL,
                    exit_price DECIMAL(20, 8),
                    amount DECIMAL(20, 8) NOT NULL,
                    leverage INTEGER NOT NULL,
                    pnl DECIMAL(20, 8),
                    pnl_pct DECIMAL(10, 6),
                    duration_seconds INTEGER,
                    signal_confidence DECIMAL(5, 4),
                    indicators JSONB,
                    exit_reason VARCHAR(50),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Equity curve table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS equity_curve (
                    id SERIAL PRIMARY KEY,
                    timestamp TIMESTAMP NOT NULL,
                    balance DECIMAL(20, 8) NOT NULL,
                    equity DECIMAL(20, 8),
                    margin_used DECIMAL(20, 8),
                    unrealized_pnl DECIMAL(20, 8),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Model performance table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS model_performance (
                    id SERIAL PRIMARY KEY,
                    timestamp TIMESTAMP NOT NULL,
                    model_type VARCHAR(50) NOT NULL,
                    accuracy DECIMAL(5, 4),
                    precision_score DECIMAL(5, 4),
                    recall DECIMAL(5, 4),
                    f1_score DECIMAL(5, 4),
                    training_samples INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Market data table for backtesting
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS market_data (
                    id SERIAL PRIMARY KEY,
                    timestamp TIMESTAMP NOT NULL,
                    symbol VARCHAR(50) NOT NULL,
                    open DECIMAL(20, 8) NOT NULL,
                    high DECIMAL(20, 8) NOT NULL,
                    low DECIMAL(20, 8) NOT NULL,
                    close DECIMAL(20, 8) NOT NULL,
                    volume DECIMAL(20, 8) NOT NULL,
                    timeframe VARCHAR(10) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(symbol, timestamp, timeframe)
                )
            """)
            
            # Create indexes for better query performance
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_trades_timestamp ON trades(timestamp);
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_trades_symbol ON trades(symbol);
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_equity_timestamp ON equity_curve(timestamp);
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_market_data_symbol_timestamp ON market_data(symbol, timestamp);
            """)
            
            self.conn.commit()
            self.logger.info("Database tables created/verified successfully")
            
        except Exception as e:
            self.logger.error(f"Error creating tables: {e}")
            if self.conn:
                self.conn.rollback()
    
    def insert_trade(self, trade_data: Dict) -> bool:
        """Insert a completed trade into the database"""
        if not self.conn:
            return False
        
        try:
            cursor = self.conn.cursor()
            
            cursor.execute("""
                INSERT INTO trades (
                    timestamp, symbol, side, entry_price, exit_price, amount,
                    leverage, pnl, pnl_pct, duration_seconds, signal_confidence,
                    indicators, exit_reason
                ) VALUES (
                    %(timestamp)s, %(symbol)s, %(side)s, %(entry_price)s,
                    %(exit_price)s, %(amount)s, %(leverage)s, %(pnl)s,
                    %(pnl_pct)s, %(duration_seconds)s, %(signal_confidence)s,
                    %(indicators)s, %(exit_reason)s
                )
            """, trade_data)
            
            self.conn.commit()
            return True
            
        except Exception as e:
            self.logger.error(f"Error inserting trade: {e}")
            if self.conn:
                self.conn.rollback()
            return False
    
    def insert_equity_snapshot(self, balance: float, equity: float = None,
                              margin_used: float = None, unrealized_pnl: float = None) -> bool:
        """Insert equity curve snapshot"""
        if not self.conn:
            return False
        
        try:
            cursor = self.conn.cursor()
            
            cursor.execute("""
                INSERT INTO equity_curve (timestamp, balance, equity, margin_used, unrealized_pnl)
                VALUES (%s, %s, %s, %s, %s)
            """, (datetime.now(), balance, equity, margin_used, unrealized_pnl))
            
            self.conn.commit()
            return True
            
        except Exception as e:
            self.logger.error(f"Error inserting equity snapshot: {e}")
            if self.conn:
                self.conn.rollback()
            return False
    
    def get_trade_history(self, symbol: str = None, limit: int = 100) -> List[Dict]:
        """Retrieve trade history"""
        if not self.conn:
            return []
        
        try:
            cursor = self.conn.cursor(cursor_factory=RealDictCursor)
            
            if symbol:
                cursor.execute("""
                    SELECT * FROM trades
                    WHERE symbol = %s
                    ORDER BY timestamp DESC
                    LIMIT %s
                """, (symbol, limit))
            else:
                cursor.execute("""
                    SELECT * FROM trades
                    ORDER BY timestamp DESC
                    LIMIT %s
                """, (limit,))
            
            trades = cursor.fetchall()
            return [dict(trade) for trade in trades]
            
        except Exception as e:
            self.logger.error(f"Error retrieving trade history: {e}")
            return []
    
    def get_equity_curve(self, days: int = 30) -> List[Dict]:
        """Retrieve equity curve data"""
        if not self.conn:
            return []
        
        try:
            cursor = self.conn.cursor(cursor_factory=RealDictCursor)
            
            cursor.execute("""
                SELECT * FROM equity_curve
                WHERE timestamp >= NOW() - INTERVAL '%s days'
                ORDER BY timestamp ASC
            """, (days,))
            
            curve = cursor.fetchall()
            return [dict(point) for point in curve]
            
        except Exception as e:
            self.logger.error(f"Error retrieving equity curve: {e}")
            return []
    
    def get_performance_stats(self, days: int = 30) -> Dict:
        """Calculate performance statistics from database"""
        if not self.conn:
            return {}
        
        try:
            cursor = self.conn.cursor(cursor_factory=RealDictCursor)
            
            cursor.execute("""
                SELECT
                    COUNT(*) as total_trades,
                    SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END) as winning_trades,
                    SUM(CASE WHEN pnl < 0 THEN 1 ELSE 0 END) as losing_trades,
                    AVG(pnl) as avg_pnl,
                    AVG(pnl_pct) as avg_pnl_pct,
                    MAX(pnl) as max_profit,
                    MIN(pnl) as max_loss,
                    AVG(duration_seconds) as avg_duration_seconds
                FROM trades
                WHERE timestamp >= NOW() - INTERVAL '%s days'
            """, (days,))
            
            stats = cursor.fetchone()
            return dict(stats) if stats else {}
            
        except Exception as e:
            self.logger.error(f"Error calculating performance stats: {e}")
            return {}
    
    def insert_market_data(self, symbol: str, ohlcv: List, timeframe: str = '1h') -> bool:
        """Insert market data for backtesting"""
        if not self.conn:
            return False
        
        try:
            cursor = self.conn.cursor()
            
            for candle in ohlcv:
                timestamp = datetime.fromtimestamp(candle[0] / 1000)
                
                cursor.execute("""
                    INSERT INTO market_data (timestamp, symbol, open, high, low, close, volume, timeframe)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (symbol, timestamp, timeframe) DO UPDATE
                    SET open = EXCLUDED.open, high = EXCLUDED.high, low = EXCLUDED.low,
                        close = EXCLUDED.close, volume = EXCLUDED.volume
                """, (timestamp, symbol, candle[1], candle[2], candle[3], candle[4], candle[5], timeframe))
            
            self.conn.commit()
            return True
            
        except Exception as e:
            self.logger.error(f"Error inserting market data: {e}")
            if self.conn:
                self.conn.rollback()
            return False
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            self.logger.info("Database connection closed")
