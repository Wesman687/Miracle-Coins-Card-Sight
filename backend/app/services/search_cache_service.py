from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import Column, Integer, String, Text, DateTime, Float, Boolean
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime, timedelta
import json
import logging

logger = logging.getLogger(__name__)

Base = declarative_base()

class SearchCache(Base):
    __tablename__ = 'search_cache'
    
    id = Column(Integer, primary_key=True)
    query_hash = Column(String(64), unique=True, nullable=False)
    query_text = Column(Text, nullable=False)
    preset = Column(String(50), nullable=False)
    response = Column(Text, nullable=False)
    confidence_score = Column(Float, nullable=False)
    pricing_data = Column(Text)  # JSON string
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)
    hit_count = Column(Integer, default=0)
    last_hit = Column(DateTime)

class SearchCacheService:
    def __init__(self, db: Session):
        self.db = db
        self.default_ttl = 3600  # 1 hour
        self.max_cache_size = 1000
    
    async def get_cached_search(self, query: str, preset: str) -> Optional[Dict[str, Any]]:
        """Get cached search result if available and not expired"""
        
        try:
            query_hash = self._hash_query(query, preset)
            
            cached_result = self.db.query(SearchCache).filter(
                SearchCache.query_hash == query_hash,
                SearchCache.expires_at > datetime.utcnow()
            ).first()
            
            if cached_result:
                # Update hit statistics
                cached_result.hit_count += 1
                cached_result.last_hit = datetime.utcnow()
                self.db.commit()
                
                logger.info(f"Cache hit for query: {query[:50]}...")
                
                # Parse pricing data if exists
                pricing_data = None
                if cached_result.pricing_data:
                    try:
                        pricing_data = json.loads(cached_result.pricing_data)
                    except json.JSONDecodeError:
                        logger.warning(f"Failed to parse pricing data for query: {query}")
                
                return {
                    'response': cached_result.response,
                    'confidence_score': cached_result.confidence_score,
                    'pricing': pricing_data
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting cached search: {str(e)}")
            return None
    
    async def cache_search_result(
        self, 
        query: str, 
        preset: str, 
        response: str, 
        confidence_score: float,
        pricing_data: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Cache search result for future use"""
        
        try:
            query_hash = self._hash_query(query, preset)
            expires_at = datetime.utcnow() + timedelta(seconds=self.default_ttl)
            
            # Check if already exists
            existing = self.db.query(SearchCache).filter(
                SearchCache.query_hash == query_hash
            ).first()
            
            if existing:
                # Update existing entry
                existing.response = response
                existing.confidence_score = confidence_score
                existing.pricing_data = json.dumps(pricing_data) if pricing_data else None
                existing.expires_at = expires_at
                existing.hit_count = 0
                existing.last_hit = None
            else:
                # Create new entry
                cached_result = SearchCache(
                    query_hash=query_hash,
                    query_text=query,
                    preset=preset,
                    response=response,
                    confidence_score=confidence_score,
                    pricing_data=json.dumps(pricing_data) if pricing_data else None,
                    expires_at=expires_at
                )
                self.db.add(cached_result)
            
            # Clean up old entries if cache is getting too large
            await self._cleanup_cache()
            
            self.db.commit()
            logger.info(f"Cached search result for query: {query[:50]}...")
            return True
            
        except Exception as e:
            logger.error(f"Error caching search result: {str(e)}")
            self.db.rollback()
            return False
    
    async def _cleanup_cache(self):
        """Clean up expired and old cache entries"""
        
        try:
            # Remove expired entries
            expired_count = self.db.query(SearchCache).filter(
                SearchCache.expires_at < datetime.utcnow()
            ).delete()
            
            if expired_count > 0:
                logger.info(f"Removed {expired_count} expired cache entries")
            
            # Check cache size
            total_count = self.db.query(SearchCache).count()
            
            if total_count > self.max_cache_size:
                # Remove oldest entries (least recently used)
                entries_to_remove = total_count - self.max_cache_size + 100  # Remove 100 extra
                
                oldest_entries = self.db.query(SearchCache).order_by(
                    SearchCache.last_hit.asc().nullsfirst(),
                    SearchCache.created_at.asc()
                ).limit(entries_to_remove).all()
                
                for entry in oldest_entries:
                    self.db.delete(entry)
                
                logger.info(f"Removed {entries_to_remove} old cache entries")
            
            self.db.commit()
            
        except Exception as e:
            logger.error(f"Error cleaning up cache: {str(e)}")
            self.db.rollback()
    
    def _hash_query(self, query: str, preset: str) -> str:
        """Create hash for query and preset combination"""
        
        import hashlib
        
        # Normalize query (lowercase, strip whitespace)
        normalized_query = query.lower().strip()
        
        # Create hash
        hash_input = f"{normalized_query}:{preset}"
        return hashlib.sha256(hash_input.encode()).hexdigest()
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        
        try:
            total_entries = self.db.query(SearchCache).count()
            expired_entries = self.db.query(SearchCache).filter(
                SearchCache.expires_at < datetime.utcnow()
            ).count()
            
            # Get hit statistics
            total_hits = self.db.query(SearchCache).with_entities(
                SearchCache.hit_count
            ).all()
            
            total_hit_count = sum(hit[0] for hit in total_hits)
            
            # Get most popular queries
            popular_queries = self.db.query(SearchCache).order_by(
                SearchCache.hit_count.desc()
            ).limit(5).all()
            
            popular_queries_data = [
                {
                    'query': entry.query_text[:50] + '...' if len(entry.query_text) > 50 else entry.query_text,
                    'preset': entry.preset,
                    'hits': entry.hit_count,
                    'last_hit': entry.last_hit.isoformat() if entry.last_hit else None
                }
                for entry in popular_queries
            ]
            
            return {
                'total_entries': total_entries,
                'expired_entries': expired_entries,
                'active_entries': total_entries - expired_entries,
                'total_hits': total_hit_count,
                'popular_queries': popular_queries_data,
                'cache_hit_rate': total_hit_count / max(total_entries, 1)
            }
            
        except Exception as e:
            logger.error(f"Error getting cache stats: {str(e)}")
            return {
                'total_entries': 0,
                'expired_entries': 0,
                'active_entries': 0,
                'total_hits': 0,
                'popular_queries': [],
                'cache_hit_rate': 0.0
            }
    
    async def clear_cache(self, preset: Optional[str] = None) -> int:
        """Clear cache entries, optionally filtered by preset"""
        
        try:
            query = self.db.query(SearchCache)
            
            if preset:
                query = query.filter(SearchCache.preset == preset)
            
            deleted_count = query.delete()
            self.db.commit()
            
            logger.info(f"Cleared {deleted_count} cache entries")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Error clearing cache: {str(e)}")
            self.db.rollback()
            return 0

