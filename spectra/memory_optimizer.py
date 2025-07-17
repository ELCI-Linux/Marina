#!/usr/bin/env python3
"""
Memory Optimization Utility for Marina's Spectra System

This module provides memory optimization features including:
- Lazy loading of heavy dependencies
- Memory usage monitoring
- Automatic cleanup of cached data
- Resource pooling and reuse
"""

import gc
import sys
import time
import threading
import logging
from typing import Dict, Any, Optional, List, Callable, Type
from dataclasses import dataclass, field
from enum import Enum
import weakref
from functools import wraps
import psutil
import asyncio


class OptimizationLevel(Enum):
    """Memory optimization levels."""
    CONSERVATIVE = "conservative"
    MODERATE = "moderate"
    AGGRESSIVE = "aggressive"


@dataclass
class MemoryStats:
    """Memory usage statistics."""
    total_memory: float  # MB
    used_memory: float   # MB
    available_memory: float  # MB
    process_memory: float    # MB
    memory_percent: float
    cached_objects: int
    last_gc_time: float
    gc_collections: int


class LazyImport:
    """Lazy import wrapper to defer heavy module loading."""
    
    def __init__(self, module_name: str, package: Optional[str] = None):
        self.module_name = module_name
        self.package = package
        self._module = None
        self._loading = False
        self._lock = threading.Lock()
    
    def __getattr__(self, name):
        if self._module is None:
            self._load_module()
        return getattr(self._module, name)
    
    def _load_module(self):
        """Load the module on first access."""
        if self._module is not None:
            return
        
        with self._lock:
            if self._module is not None:
                return
            
            if self._loading:
                # Prevent circular imports
                raise ImportError(f"Circular import detected for {self.module_name}")
            
            self._loading = True
            try:
                if self.package:
                    module = __import__(self.module_name, fromlist=[self.package])
                else:
                    module = __import__(self.module_name)
                    
                # Handle dotted imports
                for component in self.module_name.split('.')[1:]:
                    module = getattr(module, component)
                
                self._module = module
                logging.debug(f"Lazy loaded module: {self.module_name}")
            finally:
                self._loading = False
    
    def is_loaded(self) -> bool:
        """Check if module is already loaded."""
        return self._module is not None


class ObjectPool:
    """Generic object pool for reusing expensive objects."""
    
    def __init__(self, factory: Callable, max_size: int = 10, cleanup_func: Optional[Callable] = None):
        self.factory = factory
        self.max_size = max_size
        self.cleanup_func = cleanup_func
        self._pool = []
        self._in_use = set()
        self._lock = threading.Lock()
        self._created_count = 0
    
    def get(self):
        """Get an object from the pool."""
        with self._lock:
            if self._pool:
                obj = self._pool.pop()
                self._in_use.add(id(obj))
                return obj
            
            # Create new object if pool is empty
            if self._created_count < self.max_size:
                obj = self.factory()
                self._created_count += 1
                self._in_use.add(id(obj))
                return obj
            
            # Pool is full, return None to indicate unavailable
            return None
    
    def return_object(self, obj):
        """Return an object to the pool."""
        with self._lock:
            obj_id = id(obj)
            if obj_id in self._in_use:
                self._in_use.remove(obj_id)
                
                if len(self._pool) < self.max_size:
                    # Clean up object if cleanup function provided
                    if self.cleanup_func:
                        self.cleanup_func(obj)
                    self._pool.append(obj)
                else:
                    # Pool is full, let object be garbage collected
                    self._created_count -= 1
    
    def clear(self):
        """Clear the pool."""
        with self._lock:
            for obj in self._pool:
                if self.cleanup_func:
                    self.cleanup_func(obj)
            self._pool.clear()
            self._in_use.clear()
            self._created_count = 0
    
    def stats(self) -> Dict[str, int]:
        """Get pool statistics."""
        with self._lock:
            return {
                'pool_size': len(self._pool),
                'in_use': len(self._in_use),
                'created_count': self._created_count,
                'max_size': self.max_size
            }


class MemoryCache:
    """Memory-efficient cache with automatic cleanup."""
    
    def __init__(self, max_size: int = 1000, ttl: Optional[float] = None):
        self.max_size = max_size
        self.ttl = ttl
        self._cache = {}
        self._access_times = {}
        self._creation_times = {}
        self._lock = threading.Lock()
    
    def get(self, key: str) -> Any:
        """Get value from cache."""
        with self._lock:
            if key not in self._cache:
                return None
            
            # Check TTL
            if self.ttl and time.time() - self._creation_times[key] > self.ttl:
                del self._cache[key]
                del self._access_times[key]
                del self._creation_times[key]
                return None
            
            # Update access time
            self._access_times[key] = time.time()
            return self._cache[key]
    
    def set(self, key: str, value: Any):
        """Set value in cache."""
        with self._lock:
            current_time = time.time()
            
            # Remove oldest items if cache is full
            while len(self._cache) >= self.max_size:
                oldest_key = min(self._access_times, key=self._access_times.get)
                del self._cache[oldest_key]
                del self._access_times[oldest_key]
                del self._creation_times[oldest_key]
            
            self._cache[key] = value
            self._access_times[key] = current_time
            self._creation_times[key] = current_time
    
    def remove(self, key: str):
        """Remove item from cache."""
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                del self._access_times[key]
                del self._creation_times[key]
    
    def clear(self):
        """Clear all cache entries."""
        with self._lock:
            self._cache.clear()
            self._access_times.clear()
            self._creation_times.clear()
    
    def stats(self) -> Dict[str, int]:
        """Get cache statistics."""
        with self._lock:
            return {
                'size': len(self._cache),
                'max_size': self.max_size,
                'hit_ratio': getattr(self, '_hit_count', 0) / max(getattr(self, '_access_count', 1), 1)
            }


class MemoryOptimizer:
    """Main memory optimization coordinator."""
    
    def __init__(self, optimization_level: OptimizationLevel = OptimizationLevel.MODERATE):
        self.optimization_level = optimization_level
        self.logger = logging.getLogger(__name__)
        
        # Configuration based on optimization level
        self.config = self._get_config(optimization_level)
        
        # Memory monitoring
        self._memory_stats = MemoryStats(0, 0, 0, 0, 0, 0, 0, 0)
        self._monitoring_active = False
        self._monitoring_thread = None
        self._shutdown_event = threading.Event()
        
        # Cache and pool management
        self._caches: Dict[str, MemoryCache] = {}
        self._pools: Dict[str, ObjectPool] = {}
        self._lazy_imports: Dict[str, LazyImport] = {}
        
        # Cleanup callbacks
        self._cleanup_callbacks: List[Callable] = []
        
        # Initialize lazy imports for heavy dependencies
        self._setup_lazy_imports()
    
    def _get_config(self, level: OptimizationLevel) -> Dict[str, Any]:
        """Get configuration based on optimization level."""
        configs = {
            OptimizationLevel.CONSERVATIVE: {
                'gc_threshold': 0.8,
                'cleanup_interval': 300,
                'max_cache_size': 1000,
                'max_pool_size': 10,
                'enable_aggressive_gc': False
            },
            OptimizationLevel.MODERATE: {
                'gc_threshold': 0.7,
                'cleanup_interval': 180,
                'max_cache_size': 500,
                'max_pool_size': 5,
                'enable_aggressive_gc': True
            },
            OptimizationLevel.AGGRESSIVE: {
                'gc_threshold': 0.6,
                'cleanup_interval': 60,
                'max_cache_size': 100,
                'max_pool_size': 3,
                'enable_aggressive_gc': True
            }
        }
        return configs[level]
    
    def _setup_lazy_imports(self):
        """Setup lazy imports for heavy dependencies."""
        heavy_modules = [
            'torch',
            'transformers',
            'spacy',
            'cv2',
            'scikit-learn',
            'librosa',
            'whisper',
            'face_recognition',
            'easyocr'
        ]
        
        for module in heavy_modules:
            self._lazy_imports[module] = LazyImport(module)
    
    def get_lazy_import(self, module_name: str) -> LazyImport:
        """Get lazy import for a module."""
        if module_name not in self._lazy_imports:
            self._lazy_imports[module_name] = LazyImport(module_name)
        return self._lazy_imports[module_name]
    
    def create_cache(self, name: str, max_size: int = None, ttl: Optional[float] = None) -> MemoryCache:
        """Create a memory cache."""
        if max_size is None:
            max_size = self.config['max_cache_size']
        
        cache = MemoryCache(max_size, ttl)
        self._caches[name] = cache
        return cache
    
    def create_pool(self, name: str, factory: Callable, max_size: int = None, 
                   cleanup_func: Optional[Callable] = None) -> ObjectPool:
        """Create an object pool."""
        if max_size is None:
            max_size = self.config['max_pool_size']
        
        pool = ObjectPool(factory, max_size, cleanup_func)
        self._pools[name] = pool
        return pool
    
    def get_memory_stats(self) -> MemoryStats:
        """Get current memory statistics."""
        try:
            # System memory
            memory = psutil.virtual_memory()
            
            # Process memory
            process = psutil.Process()
            process_memory = process.memory_info().rss / (1024 * 1024)  # MB
            
            # Cache statistics
            cached_objects = sum(cache.stats()['size'] for cache in self._caches.values())
            
            self._memory_stats = MemoryStats(
                total_memory=memory.total / (1024 * 1024),
                used_memory=memory.used / (1024 * 1024),
                available_memory=memory.available / (1024 * 1024),
                process_memory=process_memory,
                memory_percent=memory.percent,
                cached_objects=cached_objects,
                last_gc_time=time.time(),
                gc_collections=sum(gc.get_stats())
            )
            
            return self._memory_stats
        except Exception as e:
            self.logger.error(f"Failed to get memory stats: {e}")
            return self._memory_stats
    
    def start_monitoring(self):
        """Start memory monitoring."""
        if self._monitoring_active:
            return
        
        self._monitoring_active = True
        self._monitoring_thread = threading.Thread(target=self._monitor_memory)
        self._monitoring_thread.daemon = True
        self._monitoring_thread.start()
        
        self.logger.info("Memory monitoring started")
    
    def stop_monitoring(self):
        """Stop memory monitoring."""
        if not self._monitoring_active:
            return
        
        self._monitoring_active = False
        self._shutdown_event.set()
        
        if self._monitoring_thread:
            self._monitoring_thread.join(timeout=5)
        
        self.logger.info("Memory monitoring stopped")
    
    def _monitor_memory(self):
        """Background memory monitoring."""
        while self._monitoring_active and not self._shutdown_event.wait(self.config['cleanup_interval']):
            try:
                stats = self.get_memory_stats()
                
                # Check if memory usage is high
                if stats.memory_percent > self.config['gc_threshold'] * 100:
                    self.logger.warning(f"High memory usage: {stats.memory_percent:.1f}%")
                    self.force_cleanup()
                
                # Log memory stats
                self.logger.debug(f"Memory stats: {stats.process_memory:.1f}MB process, "
                                f"{stats.memory_percent:.1f}% system, "
                                f"{stats.cached_objects} cached objects")
                
            except Exception as e:
                self.logger.error(f"Memory monitoring error: {e}")
    
    def force_cleanup(self):
        """Force cleanup of all caches and pools."""
        self.logger.info("Forcing memory cleanup...")
        
        # Clear all caches
        for name, cache in self._caches.items():
            cache.clear()
            self.logger.debug(f"Cleared cache: {name}")
        
        # Clear all pools
        for name, pool in self._pools.items():
            pool.clear()
            self.logger.debug(f"Cleared pool: {name}")
        
        # Run cleanup callbacks
        for callback in self._cleanup_callbacks:
            try:
                callback()
            except Exception as e:
                self.logger.error(f"Cleanup callback failed: {e}")
        
        # Force garbage collection
        if self.config['enable_aggressive_gc']:
            collected = gc.collect()
            self.logger.debug(f"Garbage collection freed {collected} objects")
    
    def register_cleanup_callback(self, callback: Callable):
        """Register a cleanup callback."""
        self._cleanup_callbacks.append(callback)
    
    def memory_limit_decorator(self, max_memory_mb: float):
        """Decorator to limit memory usage of a function."""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                # Check memory before execution
                stats = self.get_memory_stats()
                if stats.process_memory > max_memory_mb:
                    self.force_cleanup()
                    
                    # Check again after cleanup
                    stats = self.get_memory_stats()
                    if stats.process_memory > max_memory_mb:
                        raise MemoryError(f"Memory usage ({stats.process_memory:.1f}MB) exceeds limit ({max_memory_mb}MB)")
                
                return func(*args, **kwargs)
            return wrapper
        return decorator
    
    def get_optimization_report(self) -> Dict[str, Any]:
        """Get optimization report."""
        stats = self.get_memory_stats()
        
        # Calculate cache efficiency
        cache_stats = {}
        for name, cache in self._caches.items():
            cache_stats[name] = cache.stats()
        
        # Calculate pool efficiency
        pool_stats = {}
        for name, pool in self._pools.items():
            pool_stats[name] = pool.stats()
        
        # Check loaded modules
        loaded_modules = []
        for name, lazy_import in self._lazy_imports.items():
            if lazy_import.is_loaded():
                loaded_modules.append(name)
        
        return {
            'optimization_level': self.optimization_level.value,
            'memory_stats': {
                'process_memory_mb': stats.process_memory,
                'system_memory_percent': stats.memory_percent,
                'cached_objects': stats.cached_objects
            },
            'cache_stats': cache_stats,
            'pool_stats': pool_stats,
            'loaded_modules': loaded_modules,
            'recommendations': self._get_recommendations(stats)
        }
    
    def _get_recommendations(self, stats: MemoryStats) -> List[str]:
        """Get optimization recommendations."""
        recommendations = []
        
        if stats.memory_percent > 80:
            recommendations.append("Consider using more aggressive optimization level")
        
        if stats.cached_objects > 1000:
            recommendations.append("Consider reducing cache sizes")
        
        if len([li for li in self._lazy_imports.values() if li.is_loaded()]) > 5:
            recommendations.append("Many heavy modules loaded - consider lazy loading")
        
        return recommendations
    
    def __del__(self):
        """Cleanup on destruction."""
        self.stop_monitoring()


# Global memory optimizer instance
_global_optimizer: Optional[MemoryOptimizer] = None


def get_memory_optimizer() -> MemoryOptimizer:
    """Get global memory optimizer instance."""
    global _global_optimizer
    if _global_optimizer is None:
        _global_optimizer = MemoryOptimizer()
    return _global_optimizer


def lazy_import(module_name: str) -> LazyImport:
    """Convenience function for lazy imports."""
    return get_memory_optimizer().get_lazy_import(module_name)


def memory_limit(max_memory_mb: float):
    """Decorator to limit memory usage."""
    return get_memory_optimizer().memory_limit_decorator(max_memory_mb)


# Example usage
if __name__ == "__main__":
    # Initialize optimizer
    optimizer = MemoryOptimizer(OptimizationLevel.MODERATE)
    optimizer.start_monitoring()
    
    # Create cache
    cache = optimizer.create_cache("test_cache", max_size=100)
    
    # Test cache
    cache.set("key1", "value1")
    print(f"Cache value: {cache.get('key1')}")
    
    # Get optimization report
    report = optimizer.get_optimization_report()
    print(f"Optimization report: {report}")
    
    # Stop monitoring
    optimizer.stop_monitoring()
