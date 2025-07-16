"""
Concept caching layer for external ontology API calls.

This module provides efficient caching mechanisms for external knowledge base
queries to improve performance and reduce API usage costs.
"""

import json
import logging
import sqlite3
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from contextlib import contextmanager
from dataclasses import dataclass, asdict, is_dataclass
from datetime import datetime, timedelta

from src.settings import Settings


def _serialize_value(value: Any) -> str:
    """Serialize a value for storage, handling dataclasses properly."""
    def custom_serializer(obj):
        if is_dataclass(obj):
            return {
                '__dataclass__': obj.__class__.__module__ + '.' + obj.__class__.__qualname__,
                '__data__': asdict(obj)
            }
        elif hasattr(obj, '__dict__'):
            return obj.__dict__
        return str(obj)
    
    return json.dumps(value, default=custom_serializer)


def _deserialize_value(serialized: str) -> Any:
    """Deserialize a value from storage, handling dataclasses properly."""
    def custom_deserializer(dct):
        if '__dataclass__' in dct:
            # Import the dataclass dynamically
            module_path, class_name = dct['__dataclass__'].rsplit('.', 1)
            try:
                module = __import__(module_path, fromlist=[class_name])
                cls = getattr(module, class_name)
                return cls(**dct['__data__'])
            except (ImportError, AttributeError) as e:
                # If we can't import the class, return the raw data
                return dct['__data__']
        return dct
    
    return json.loads(serialized, object_hook=custom_deserializer)


@dataclass
class CacheEntry:
    """Represents a cache entry with metadata."""
    key: str
    value: Any
    created_at: datetime
    expires_at: Optional[datetime] = None
    access_count: int = 0
    last_accessed: Optional[datetime] = None
    source: Optional[str] = None
    
    def is_expired(self) -> bool:
        """Check if the cache entry is expired."""
        if self.expires_at is None:
            return False
        return datetime.now() > self.expires_at
    
    def update_access(self):
        """Update access statistics."""
        self.access_count += 1
        self.last_accessed = datetime.now()


class ConceptCache:
    """
    High-performance caching layer for external ontology concepts.
    
    Features:
    - SQLite-based persistent storage
    - TTL (Time To Live) support
    - LRU (Least Recently Used) eviction
    - Cache statistics and monitoring
    - Configurable cache size limits
    """
    
    def __init__(self, settings: Settings):
        """Initialize the concept cache."""
        self.settings = settings
        self.logger = logging.getLogger(__name__)
        
        # Cache configuration
        self.cache_dir = Path(getattr(settings, 'cache_dir', './data/cache'))
        self.cache_file = self.cache_dir / 'concept_cache.db'
        self.max_cache_size = getattr(settings, 'max_cache_size', 10000)
        self.default_ttl = getattr(settings, 'cache_ttl_hours', 24 * 7)  # 1 week default
        
        # Create cache directory
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize database
        self._init_database()
        
        # Cache statistics
        self.stats = {
            'hits': 0,
            'misses': 0,
            'evictions': 0,
            'total_requests': 0
        }
    
    def _init_database(self):
        """Initialize the SQLite database for caching."""
        with self._get_connection() as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS cache_entries (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    created_at TIMESTAMP NOT NULL,
                    expires_at TIMESTAMP,
                    access_count INTEGER DEFAULT 0,
                    last_accessed TIMESTAMP,
                    source TEXT,
                    size INTEGER DEFAULT 0
                )
            ''')
            
            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_expires_at ON cache_entries(expires_at)
            ''')
            
            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_last_accessed ON cache_entries(last_accessed)
            ''')
            
            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_source ON cache_entries(source)
            ''')
            
            conn.commit()
    
    @contextmanager
    def _get_connection(self):
        """Get a database connection with proper error handling."""
        conn = sqlite3.connect(self.cache_file, timeout=30.0)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()
    
    def get(self, key: str) -> Optional[Any]:
        """Get a value from the cache."""
        self.stats['total_requests'] += 1
        
        try:
            with self._get_connection() as conn:
                cursor = conn.execute(
                    'SELECT value, expires_at, access_count FROM cache_entries WHERE key = ?',
                    (key,)
                )
                row = cursor.fetchone()
                
                if row is None:
                    self.stats['misses'] += 1
                    return None
                
                # Check if expired
                if row['expires_at']:
                    expires_at = datetime.fromisoformat(row['expires_at'])
                    if datetime.now() > expires_at:
                        self._delete_key(key)
                        self.stats['misses'] += 1
                        return None
                
                # Update access statistics
                conn.execute(
                    'UPDATE cache_entries SET access_count = ?, last_accessed = ? WHERE key = ?',
                    (row['access_count'] + 1, datetime.now().isoformat(), key)
                )
                conn.commit()
                
                self.stats['hits'] += 1
                try:
                    deserialized_value = _deserialize_value(row['value'])
                    # Additional validation for ExternalConceptData objects
                    if hasattr(deserialized_value, '__class__') and 'ExternalConceptData' in str(type(deserialized_value)):
                        # Ensure it has required attributes
                        if not hasattr(deserialized_value, 'external_id') or not hasattr(deserialized_value, 'source'):
                            self.logger.warning(f"Invalid ExternalConceptData in cache for key '{key}', removing")
                            self._delete_key(key)
                            self.stats['misses'] += 1
                            return None
                    return deserialized_value
                except (json.JSONDecodeError, TypeError, AttributeError) as e:
                    self.logger.warning(f"Failed to deserialize cached value for key '{key}': {e}, removing from cache")
                    self._delete_key(key)
                    self.stats['misses'] += 1
                    return None
                
        except Exception as e:
            self.logger.error(f"Cache get error for key '{key}': {e}")
            self.stats['misses'] += 1
            return None
    
    def set(self, key: str, value: Any, ttl_hours: Optional[int] = None, source: Optional[str] = None):
        """Set a value in the cache."""
        try:
            # Serialize value
            serialized_value = _serialize_value(value)
            size = len(serialized_value.encode('utf-8'))
            
            # Calculate expiration
            expires_at = None
            if ttl_hours is not None:
                expires_at = datetime.now() + timedelta(hours=ttl_hours)
            elif self.default_ttl > 0:
                expires_at = datetime.now() + timedelta(hours=self.default_ttl)
            
            # Insert or update cache entry
            with self._get_connection() as conn:
                conn.execute('''
                    INSERT OR REPLACE INTO cache_entries 
                    (key, value, created_at, expires_at, access_count, last_accessed, source, size)
                    VALUES (?, ?, ?, ?, 0, ?, ?, ?)
                ''', (
                    key,
                    serialized_value,
                    datetime.now().isoformat(),
                    expires_at.isoformat() if expires_at else None,
                    datetime.now().isoformat(),
                    source,
                    size
                ))
                conn.commit()
            
            # Check cache size and evict if necessary
            self._evict_if_necessary()
            
        except Exception as e:
            self.logger.error(f"Cache set error for key '{key}': {e}")
    
    def delete(self, key: str) -> bool:
        """Delete a specific key from the cache."""
        return self._delete_key(key)
    
    def _delete_key(self, key: str) -> bool:
        """Internal method to delete a key."""
        try:
            with self._get_connection() as conn:
                cursor = conn.execute('DELETE FROM cache_entries WHERE key = ?', (key,))
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            self.logger.error(f"Cache delete error for key '{key}': {e}")
            return False
    
    def clear(self, source: Optional[str] = None):
        """Clear the cache, optionally filtered by source."""
        try:
            with self._get_connection() as conn:
                if source:
                    conn.execute('DELETE FROM cache_entries WHERE source = ?', (source,))
                else:
                    conn.execute('DELETE FROM cache_entries')
                conn.commit()
            
            self.logger.info(f"Cache cleared{' for source: ' + source if source else ''}")
            
        except Exception as e:
            self.logger.error(f"Cache clear error: {e}")
    
    def _evict_if_necessary(self):
        """Evict entries if cache size exceeds limits."""
        try:
            with self._get_connection() as conn:
                # Count current entries
                cursor = conn.execute('SELECT COUNT(*) FROM cache_entries')
                current_size = cursor.fetchone()[0]
                
                if current_size <= self.max_cache_size:
                    return
                
                # Calculate how many entries to evict
                evict_count = current_size - self.max_cache_size + (self.max_cache_size // 10)  # Evict 10% extra
                
                # Evict least recently used entries
                conn.execute('''
                    DELETE FROM cache_entries 
                    WHERE key IN (
                        SELECT key FROM cache_entries 
                        ORDER BY last_accessed ASC, created_at ASC 
                        LIMIT ?
                    )
                ''', (evict_count,))
                
                conn.commit()
                self.stats['evictions'] += evict_count
                
                self.logger.info(f"Evicted {evict_count} cache entries")
                
        except Exception as e:
            self.logger.error(f"Cache eviction error: {e}")
    
    def cleanup_expired(self):
        """Remove expired cache entries."""
        try:
            with self._get_connection() as conn:
                cursor = conn.execute(
                    'DELETE FROM cache_entries WHERE expires_at IS NOT NULL AND expires_at < ?',
                    (datetime.now().isoformat(),)
                )
                conn.commit()
                
                if cursor.rowcount > 0:
                    self.logger.info(f"Cleaned up {cursor.rowcount} expired cache entries")
                    
        except Exception as e:
            self.logger.error(f"Cache cleanup error: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        try:
            with self._get_connection() as conn:
                # Get database stats
                cursor = conn.execute('SELECT COUNT(*), SUM(size) FROM cache_entries')
                row = cursor.fetchone()
                db_count = row[0] or 0
                db_size = row[1] or 0
                
                # Get source distribution
                cursor = conn.execute('''
                    SELECT source, COUNT(*) as count 
                    FROM cache_entries 
                    GROUP BY source
                ''')
                source_distribution = {row[0] or 'unknown': row[1] for row in cursor.fetchall()}
                
                # Calculate hit rate
                hit_rate = 0.0
                if self.stats['total_requests'] > 0:
                    hit_rate = self.stats['hits'] / self.stats['total_requests']
                
                return {
                    'total_entries': db_count,
                    'total_size_bytes': db_size,
                    'hit_rate': hit_rate,
                    'hits': self.stats['hits'],
                    'misses': self.stats['misses'],
                    'evictions': self.stats['evictions'],
                    'total_requests': self.stats['total_requests'],
                    'source_distribution': source_distribution,
                    'max_cache_size': self.max_cache_size,
                    'cache_file': str(self.cache_file)
                }
                
        except Exception as e:
            self.logger.error(f"Error getting cache stats: {e}")
            return {'error': str(e)}
    
    def get_entries_by_source(self, source: str) -> List[Dict[str, Any]]:
        """Get cache entries filtered by source."""
        try:
            with self._get_connection() as conn:
                cursor = conn.execute('''
                    SELECT key, created_at, expires_at, access_count, last_accessed, size
                    FROM cache_entries 
                    WHERE source = ?
                    ORDER BY last_accessed DESC
                ''', (source,))
                
                entries = []
                for row in cursor.fetchall():
                    entries.append({
                        'key': row['key'],
                        'created_at': row['created_at'],
                        'expires_at': row['expires_at'],
                        'access_count': row['access_count'],
                        'last_accessed': row['last_accessed'],
                        'size': row['size']
                    })
                
                return entries
                
        except Exception as e:
            self.logger.error(f"Error getting entries by source '{source}': {e}")
            return []
    
    def validate_and_clean_cache(self):
        """Validate cache entries and remove corrupted ones."""
        corrupted_keys = []
        
        try:
            with self._get_connection() as conn:
                cursor = conn.execute('SELECT key, value FROM cache_entries')
                
                for row in cursor.fetchall():
                    try:
                        _deserialize_value(row['value'])
                    except Exception:
                        corrupted_keys.append(row['key'])
                
                # Remove corrupted entries
                if corrupted_keys:
                    placeholders = ','.join('?' * len(corrupted_keys))
                    conn.execute(f'DELETE FROM cache_entries WHERE key IN ({placeholders})', corrupted_keys)
                    conn.commit()
                    
                    self.logger.info(f"Removed {len(corrupted_keys)} corrupted cache entries")
                    
        except Exception as e:
            self.logger.error(f"Error validating cache: {e}")
        
        return len(corrupted_keys)
    
    def close(self):
        """Close the cache and clean up resources."""
        self.cleanup_expired()
        self.logger.info("Concept cache closed")


def get_concept_cache(settings: Settings) -> ConceptCache:
    """Factory function to create a concept cache."""
    return ConceptCache(settings)