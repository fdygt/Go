from typing import Optional, Dict, List, Any, Union
from datetime import datetime, UTC, timedelta
import logging
import json
import sqlite3
import redis
from redis.lock import Lock

logger = logging.getLogger(__name__)

class DatabaseService:
    _instance = None
    _conn = None
    _redis = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DatabaseService, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not self._conn:
            self.startup_time = datetime.now(UTC)
            logger.info(f"""
            DatabaseService initialized:
            Time: 2025-05-30 15:09:00
            User: fdygg
            """)
            
            # Init SQLite
            self._init_sqlite()
            
            # Init Redis
            self._init_redis()

    def _init_sqlite(self):
        """Initialize SQLite connection"""
        try:
            self._conn = sqlite3.connect('shop.db', check_same_thread=False)
            self._conn.row_factory = sqlite3.Row
            cursor = self._conn.cursor()
            cursor.execute("PRAGMA foreign_keys = ON")
            cursor.execute("PRAGMA journal_mode = WAL")
            logger.info("SQLite initialized successfully")
        except Exception as e:
            logger.error(f"SQLite initialization error: {str(e)}")
            raise

    def _init_redis(self):
        """Initialize Redis connection"""
        try:
            self._redis = redis.Redis(
                host='localhost',
                port=6379,
                db=0,
                decode_responses=True
            )
            self._redis.ping()
            logger.info("Redis initialized successfully") 
        except Exception as e:
            logger.error(f"Redis initialization error: {str(e)}")
            raise

    def get_connection(self) -> sqlite3.Connection:
        """Get SQLite connection"""
        if not self._conn:
            self._init_sqlite()
        return self._conn

    def get_redis(self) -> redis.Redis:
        """Get Redis connection"""
        if not self._redis:
            self._init_redis()
        return self._redis

    async def execute_query(
        self,
        query: str,
        params: tuple = None,
        fetch: bool = True
    ) -> Optional[List[Dict]]:
        """Execute SQL query"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(query, params or ())
            if fetch:
                result = [dict(row) for row in cursor.fetchall()]
                return result
            conn.commit()
            return None
        except sqlite3.Error as e:
            logger.error(f"Query execution failed: {str(e)}")
            conn.rollback()
            raise

    async def cache_get(
        self,
        key: str,
        default: Any = None
    ) -> Any:
        """Get value from cache"""
        try:
            data = self._redis.get(key)
            if data:
                return json.loads(data)
            return default
        except Exception as e:
            logger.error(f"Cache get error: {str(e)}")
            return default

    async def cache_set(
        self,
        key: str,  
        value: Any,
        expire: int = 3600
    ) -> bool:
        """Set value in cache"""
        try:
            data = json.dumps(value)
            return self._redis.setex(key, expire, data)
        except Exception as e:
            logger.error(f"Cache set error: {str(e)}")
            return False

    async def cache_delete(
        self,
        key: str
    ) -> bool:
        """Delete value from cache"""
        try:
            return bool(self._redis.delete(key))
        except Exception as e:
            logger.error(f"Cache delete error: {str(e)}")
            return False

    async def cache_clear(
        self,
        pattern: str = "*"
    ) -> bool:
        """Clear cache entries matching pattern"""
        try:
            keys = self._redis.keys(pattern)
            if keys:
                return bool(self._redis.delete(*keys))
            return True
        except Exception as e:
            logger.error(f"Cache clear error: {str(e)}")
            return False

    async def acquire_lock(
        self,
        key: str,
        timeout: int = 10
    ) -> Optional[Lock]:
        """Acquire distributed lock"""
        try:
            lock = self._redis.lock(
                f"lock:{key}",
                timeout=timeout
            )
            if lock.acquire(blocking=True):
                return lock
            return None
        except Exception as e:
            logger.error(f"Lock acquisition error: {str(e)}")
            return None
