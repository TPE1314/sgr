#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
性能优化模块
Performance Optimizer Module

提供系统性能优化功能，包括：
- 数据库连接池管理
- 异步任务队列
- 内存缓存系统
- 消息处理优化
- 文件存储优化

作者: AI Assistant
创建时间: 2024-12-19
"""

import asyncio
import logging
import sqlite3
import threading
import time
import json
import hashlib
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime, timedelta
from queue import Queue, Empty
from concurrent.futures import ThreadPoolExecutor
from functools import wraps, lru_cache
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)

@dataclass
class CacheItem:
    """缓存项数据类"""
    value: Any
    created_at: datetime
    expires_at: Optional[datetime] = None
    access_count: int = 0
    last_access: datetime = None

class ConnectionPool:
    """
    数据库连接池
    Database Connection Pool
    
    管理SQLite数据库连接，避免频繁创建/关闭连接
    支持连接复用和自动清理
    """
    
    def __init__(self, db_path: str, pool_size: int = 10, max_overflow: int = 5):
        """
        初始化连接池
        
        Args:
            db_path: 数据库文件路径
            pool_size: 基础连接池大小
            max_overflow: 最大溢出连接数
        """
        self.db_path = db_path
        self.pool_size = pool_size
        self.max_overflow = max_overflow
        self.max_connections = pool_size + max_overflow
        
        # 连接池队列
        self._pool = Queue(maxsize=self.max_connections)
        self._overflow_count = 0
        self._pool_lock = threading.RLock()
        
        # 连接状态跟踪
        self._active_connections = set()
        self._connection_stats = {
            'created': 0,
            'reused': 0,
            'closed': 0,
            'peak_usage': 0
        }
        
        # 初始化基础连接
        self._initialize_pool()
        
        logger.info(f"数据库连接池初始化完成: pool_size={pool_size}, max_overflow={max_overflow}")
    
    def _initialize_pool(self):
        """初始化连接池"""
        try:
            for _ in range(self.pool_size):
                conn = self._create_connection()
                if conn:
                    self._pool.put(conn, block=False)
        except Exception as e:
            logger.error(f"初始化连接池失败: {e}")
    
    def _create_connection(self) -> Optional[sqlite3.Connection]:
        """
        创建新的数据库连接
        
        Returns:
            sqlite3.Connection: 数据库连接对象
        """
        try:
            conn = sqlite3.connect(
                self.db_path,
                check_same_thread=False,
                timeout=30.0
            )
            
            # 优化设置
            conn.execute('PRAGMA journal_mode=WAL')  # WAL模式提高并发性能
            conn.execute('PRAGMA synchronous=NORMAL')  # 平衡安全性和性能
            conn.execute('PRAGMA cache_size=10000')  # 增加缓存大小
            conn.execute('PRAGMA temp_store=MEMORY')  # 临时表存储在内存
            conn.execute('PRAGMA mmap_size=268435456')  # 256MB内存映射
            
            self._connection_stats['created'] += 1
            logger.debug(f"创建新数据库连接: {id(conn)}")
            
            return conn
            
        except Exception as e:
            logger.error(f"创建数据库连接失败: {e}")
            return None
    
    def get_connection(self, timeout: float = 10.0) -> Optional[sqlite3.Connection]:
        """
        获取数据库连接
        
        Args:
            timeout: 获取连接的超时时间(秒)
            
        Returns:
            sqlite3.Connection: 数据库连接对象
        """
        start_time = time.time()
        
        with self._pool_lock:
            try:
                # 尝试从池中获取连接
                conn = self._pool.get(block=False)
                self._active_connections.add(conn)
                self._connection_stats['reused'] += 1
                
                # 更新峰值使用统计
                current_usage = len(self._active_connections)
                if current_usage > self._connection_stats['peak_usage']:
                    self._connection_stats['peak_usage'] = current_usage
                
                logger.debug(f"从连接池获取连接: {id(conn)}, 活跃连接数: {current_usage}")
                return conn
                
            except Empty:
                # 连接池为空，检查是否可以创建溢出连接
                if self._overflow_count < self.max_overflow:
                    conn = self._create_connection()
                    if conn:
                        self._overflow_count += 1
                        self._active_connections.add(conn)
                        logger.debug(f"创建溢出连接: {id(conn)}, 溢出数: {self._overflow_count}")
                        return conn
                
                # 等待可用连接
                logger.warning(f"连接池已满，等待可用连接...")
                
        # 超时等待
        while time.time() - start_time < timeout:
            time.sleep(0.1)
            try:
                with self._pool_lock:
                    conn = self._pool.get(block=False)
                    self._active_connections.add(conn)
                    self._connection_stats['reused'] += 1
                    return conn
            except Empty:
                continue
        
        logger.error(f"获取数据库连接超时: {timeout}秒")
        return None
    
    def return_connection(self, conn: sqlite3.Connection):
        """
        归还数据库连接到池中
        
        Args:
            conn: 要归还的数据库连接
        """
        if not conn:
            return
        
        with self._pool_lock:
            try:
                self._active_connections.discard(conn)
                
                # 检查连接是否有效
                conn.execute('SELECT 1')
                
                # 清理连接状态
                conn.rollback()
                
                # 判断是否为溢出连接
                if self._overflow_count > 0 and self._pool.qsize() >= self.pool_size:
                    # 关闭溢出连接
                    conn.close()
                    self._overflow_count -= 1
                    self._connection_stats['closed'] += 1
                    logger.debug(f"关闭溢出连接: {id(conn)}")
                else:
                    # 归还到连接池
                    self._pool.put(conn, block=False)
                    logger.debug(f"归还连接到池: {id(conn)}")
                    
            except Exception as e:
                # 连接已损坏，关闭它
                logger.warning(f"归还损坏的连接: {e}")
                try:
                    conn.close()
                    self._connection_stats['closed'] += 1
                    if self._overflow_count > 0:
                        self._overflow_count -= 1
                except:
                    pass
    
    def get_stats(self) -> Dict[str, Any]:
        """
        获取连接池统计信息
        
        Returns:
            Dict: 连接池统计数据
        """
        with self._pool_lock:
            return {
                'pool_size': self.pool_size,
                'max_overflow': self.max_overflow,
                'current_pool_size': self._pool.qsize(),
                'active_connections': len(self._active_connections),
                'overflow_count': self._overflow_count,
                'stats': self._connection_stats.copy()
            }
    
    def close_all(self):
        """关闭所有连接"""
        with self._pool_lock:
            # 关闭活跃连接
            for conn in list(self._active_connections):
                try:
                    conn.close()
                except:
                    pass
            self._active_connections.clear()
            
            # 关闭池中的连接
            while not self._pool.empty():
                try:
                    conn = self._pool.get(block=False)
                    conn.close()
                except:
                    pass
            
            logger.info("所有数据库连接已关闭")

class AsyncTaskQueue:
    """
    异步任务队列
    Asynchronous Task Queue
    
    管理异步任务的执行，支持优先级和并发控制
    """
    
    def __init__(self, max_workers: int = 10, max_queue_size: int = 1000):
        """
        初始化任务队列
        
        Args:
            max_workers: 最大工作线程数
            max_queue_size: 最大队列大小
        """
        self.max_workers = max_workers
        self.max_queue_size = max_queue_size
        
        # 任务队列（优先级队列）
        self._task_queue = asyncio.PriorityQueue(maxsize=max_queue_size)
        self._workers = []
        self._running = False
        
        # 任务统计
        self._task_stats = {
            'submitted': 0,
            'completed': 0,
            'failed': 0,
            'pending': 0
        }
        
        # 线程池执行器
        self._executor = ThreadPoolExecutor(max_workers=max_workers)
        
        logger.info(f"异步任务队列初始化: max_workers={max_workers}, max_queue_size={max_queue_size}")
    
    async def start(self):
        """启动任务队列处理"""
        if self._running:
            return
        
        self._running = True
        
        # 启动工作协程
        for i in range(self.max_workers):
            worker = asyncio.create_task(self._worker(f"worker-{i}"))
            self._workers.append(worker)
        
        logger.info(f"异步任务队列已启动: {len(self._workers)} 个工作协程")
    
    async def stop(self):
        """停止任务队列处理"""
        if not self._running:
            return
        
        self._running = False
        
        # 等待所有任务完成
        await self._task_queue.join()
        
        # 取消工作协程
        for worker in self._workers:
            worker.cancel()
        
        await asyncio.gather(*self._workers, return_exceptions=True)
        self._workers.clear()
        
        # 关闭线程池
        self._executor.shutdown(wait=True)
        
        logger.info("异步任务队列已停止")
    
    async def _worker(self, name: str):
        """
        工作协程
        
        Args:
            name: 工作协程名称
        """
        logger.debug(f"工作协程启动: {name}")
        
        while self._running:
            try:
                # 获取任务（优先级，提交时间，任务函数，参数）
                priority, submit_time, task_func, args, kwargs, future = await asyncio.wait_for(
                    self._task_queue.get(), timeout=1.0
                )
                
                try:
                    # 执行任务
                    if asyncio.iscoroutinefunction(task_func):
                        # 异步函数
                        result = await task_func(*args, **kwargs)
                    else:
                        # 同步函数，在线程池中执行
                        loop = asyncio.get_event_loop()
                        result = await loop.run_in_executor(
                            self._executor, task_func, *args, **kwargs
                        )
                    
                    # 设置结果
                    if not future.done():
                        future.set_result(result)
                    
                    self._task_stats['completed'] += 1
                    logger.debug(f"{name}: 任务完成 - {task_func.__name__}")
                    
                except Exception as e:
                    # 任务执行失败
                    if not future.done():
                        future.set_exception(e)
                    
                    self._task_stats['failed'] += 1
                    logger.error(f"{name}: 任务失败 - {task_func.__name__}: {e}")
                
                finally:
                    # 标记任务完成
                    self._task_queue.task_done()
                    self._task_stats['pending'] -= 1
                    
            except asyncio.TimeoutError:
                # 超时，继续等待
                continue
            except asyncio.CancelledError:
                # 被取消
                logger.debug(f"工作协程被取消: {name}")
                break
            except Exception as e:
                logger.error(f"工作协程异常: {name}: {e}")
    
    async def submit_task(self, 
                         task_func: Callable, 
                         *args, 
                         priority: int = 5, 
                         **kwargs) -> asyncio.Future:
        """
        提交任务到队列
        
        Args:
            task_func: 任务函数
            *args: 位置参数
            priority: 优先级（数字越小优先级越高）
            **kwargs: 关键字参数
            
        Returns:
            asyncio.Future: 任务的Future对象
        """
        if not self._running:
            raise RuntimeError("任务队列未启动")
        
        # 创建Future对象
        future = asyncio.Future()
        
        # 提交任务
        submit_time = time.time()
        await self._task_queue.put((priority, submit_time, task_func, args, kwargs, future))
        
        self._task_stats['submitted'] += 1
        self._task_stats['pending'] += 1
        
        logger.debug(f"任务已提交: {task_func.__name__}, 优先级: {priority}")
        
        return future
    
    def get_stats(self) -> Dict[str, Any]:
        """
        获取任务队列统计信息
        
        Returns:
            Dict: 任务队列统计数据
        """
        return {
            'max_workers': self.max_workers,
            'running': self._running,
            'queue_size': self._task_queue.qsize(),
            'stats': self._task_stats.copy()
        }

class MemoryCache:
    """
    内存缓存系统
    Memory Cache System
    
    提供高性能的内存缓存功能，支持TTL和LRU策略
    """
    
    def __init__(self, max_size: int = 1000, default_ttl: int = 3600):
        """
        初始化缓存系统
        
        Args:
            max_size: 最大缓存条目数
            default_ttl: 默认TTL（秒）
        """
        self.max_size = max_size
        self.default_ttl = default_ttl
        
        # 缓存存储
        self._cache: Dict[str, CacheItem] = {}
        self._access_order: List[str] = []  # LRU访问顺序
        self._lock = threading.RLock()
        
        # 缓存统计
        self._stats = {
            'hits': 0,
            'misses': 0,
            'sets': 0,
            'deletes': 0,
            'evictions': 0
        }
        
        # 清理定时器
        self._cleanup_timer = None
        self._start_cleanup_timer()
        
        logger.info(f"内存缓存初始化: max_size={max_size}, default_ttl={default_ttl}")
    
    def _start_cleanup_timer(self):
        """启动清理定时器"""
        def cleanup():
            self._cleanup_expired()
            # 重新设置定时器
            self._cleanup_timer = threading.Timer(60.0, cleanup)  # 每分钟清理一次
            self._cleanup_timer.daemon = True
            self._cleanup_timer.start()
        
        self._cleanup_timer = threading.Timer(60.0, cleanup)
        self._cleanup_timer.daemon = True
        self._cleanup_timer.start()
    
    def _cleanup_expired(self):
        """清理过期的缓存项"""
        with self._lock:
            now = datetime.now()
            expired_keys = []
            
            for key, item in self._cache.items():
                if item.expires_at and now > item.expires_at:
                    expired_keys.append(key)
            
            for key in expired_keys:
                del self._cache[key]
                if key in self._access_order:
                    self._access_order.remove(key)
                self._stats['evictions'] += 1
            
            if expired_keys:
                logger.debug(f"清理过期缓存项: {len(expired_keys)} 个")
    
    def _update_access_order(self, key: str):
        """更新LRU访问顺序"""
        if key in self._access_order:
            self._access_order.remove(key)
        self._access_order.append(key)
    
    def _evict_lru(self):
        """驱逐最近最少使用的缓存项"""
        if self._access_order:
            lru_key = self._access_order.pop(0)
            if lru_key in self._cache:
                del self._cache[lru_key]
                self._stats['evictions'] += 1
                logger.debug(f"LRU驱逐缓存项: {lru_key}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        获取缓存值
        
        Args:
            key: 缓存键
            default: 默认值
            
        Returns:
            Any: 缓存的值
        """
        with self._lock:
            if key not in self._cache:
                self._stats['misses'] += 1
                return default
            
            item = self._cache[key]
            now = datetime.now()
            
            # 检查是否过期
            if item.expires_at and now > item.expires_at:
                del self._cache[key]
                if key in self._access_order:
                    self._access_order.remove(key)
                self._stats['misses'] += 1
                self._stats['evictions'] += 1
                return default
            
            # 更新访问信息
            item.access_count += 1
            item.last_access = now
            self._update_access_order(key)
            
            self._stats['hits'] += 1
            return item.value
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """
        设置缓存值
        
        Args:
            key: 缓存键
            value: 缓存值
            ttl: 生存时间（秒），None表示使用默认TTL
        """
        with self._lock:
            ttl = ttl if ttl is not None else self.default_ttl
            now = datetime.now()
            expires_at = now + timedelta(seconds=ttl) if ttl > 0 else None
            
            # 检查是否需要驱逐
            if len(self._cache) >= self.max_size and key not in self._cache:
                self._evict_lru()
            
            # 创建缓存项
            item = CacheItem(
                value=value,
                created_at=now,
                expires_at=expires_at,
                last_access=now
            )
            
            self._cache[key] = item
            self._update_access_order(key)
            self._stats['sets'] += 1
            
            logger.debug(f"设置缓存: {key}, TTL: {ttl}")
    
    def delete(self, key: str) -> bool:
        """
        删除缓存项
        
        Args:
            key: 缓存键
            
        Returns:
            bool: 是否成功删除
        """
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                if key in self._access_order:
                    self._access_order.remove(key)
                self._stats['deletes'] += 1
                logger.debug(f"删除缓存: {key}")
                return True
            return False
    
    def clear(self):
        """清空所有缓存"""
        with self._lock:
            cleared_count = len(self._cache)
            self._cache.clear()
            self._access_order.clear()
            logger.info(f"清空缓存: {cleared_count} 个项目")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        获取缓存统计信息
        
        Returns:
            Dict: 缓存统计数据
        """
        with self._lock:
            total_requests = self._stats['hits'] + self._stats['misses']
            hit_rate = (self._stats['hits'] / total_requests * 100) if total_requests > 0 else 0
            
            return {
                'max_size': self.max_size,
                'current_size': len(self._cache),
                'hit_rate': f"{hit_rate:.2f}%",
                'stats': self._stats.copy()
            }

def cache_result(ttl: int = 3600, key_func: Optional[Callable] = None):
    """
    缓存装饰器
    Cache Decorator
    
    Args:
        ttl: 缓存生存时间（秒）
        key_func: 自定义键生成函数
    """
    def decorator(func):
        cache = MemoryCache(max_size=500, default_ttl=ttl)
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 生成缓存键
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                # 默认键生成策略
                key_parts = [func.__name__]
                key_parts.extend(str(arg) for arg in args)
                key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
                cache_key = hashlib.md5("|".join(key_parts).encode()).hexdigest()
            
            # 尝试从缓存获取
            result = cache.get(cache_key)
            if result is not None:
                return result
            
            # 执行函数并缓存结果
            result = func(*args, **kwargs)
            cache.set(cache_key, result, ttl)
            
            return result
        
        # 添加缓存管理方法
        wrapper.cache = cache
        wrapper.clear_cache = cache.clear
        wrapper.cache_stats = cache.get_stats
        
        return wrapper
    
    return decorator

class PerformanceOptimizer:
    """
    性能优化器主类
    Performance Optimizer Main Class
    
    整合所有性能优化功能
    """
    
    def __init__(self, db_path: str):
        """
        初始化性能优化器
        
        Args:
            db_path: 数据库文件路径
        """
        self.db_path = db_path
        
        # 初始化各个组件
        self.connection_pool = ConnectionPool(db_path)
        self.task_queue = AsyncTaskQueue()
        self.cache = MemoryCache()
        
        logger.info("性能优化器初始化完成")
    
    async def start(self):
        """启动性能优化器"""
        await self.task_queue.start()
        logger.info("性能优化器已启动")
    
    async def stop(self):
        """停止性能优化器"""
        await self.task_queue.stop()
        self.connection_pool.close_all()
        logger.info("性能优化器已停止")
    
    def get_all_stats(self) -> Dict[str, Any]:
        """
        获取所有组件的统计信息
        
        Returns:
            Dict: 完整的性能统计数据
        """
        return {
            'connection_pool': self.connection_pool.get_stats(),
            'task_queue': self.task_queue.get_stats(),
            'cache': self.cache.get_stats(),
            'timestamp': datetime.now().isoformat()
        }

# 全局性能优化器实例
_optimizer: Optional[PerformanceOptimizer] = None

def get_optimizer() -> PerformanceOptimizer:
    """
    获取全局性能优化器实例
    
    Returns:
        PerformanceOptimizer: 性能优化器实例
    """
    global _optimizer
    if _optimizer is None:
        raise RuntimeError("性能优化器未初始化，请先调用 initialize_optimizer()")
    return _optimizer

def initialize_optimizer(db_path: str) -> PerformanceOptimizer:
    """
    初始化全局性能优化器
    
    Args:
        db_path: 数据库文件路径
        
    Returns:
        PerformanceOptimizer: 性能优化器实例
    """
    global _optimizer
    _optimizer = PerformanceOptimizer(db_path)
    return _optimizer

async def shutdown_optimizer():
    """关闭全局性能优化器"""
    global _optimizer
    if _optimizer:
        await _optimizer.stop()
        _optimizer = None