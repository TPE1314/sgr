#!/usr/bin/env python3
# -<i>- coding: utf-8 -</i>-

"""
实时通知系统
Real-time Notification System

提供全面的实时通知功能，包括：
- 跨机器人事件通知
- 系统状态监控告警
- 用户活动通知
- 定时报告推送
- 自定义通知规则
- 通知优先级管理

作者: AI Assistant
创建时间: 2024-12-19
"""

import asyncio
import logging
import json
import time
from typing import Dict, List, Optional, Any, Callable, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import threading
from queue import Queue, Empty
import weakref

# 尝试导入Telegram相关库
try:
    from telegram import Bot
    from telegram.constants import ParseMode
    TELEGRAM_AVAILABLE = True
except ImportError:
    TELEGRAM_AVAILABLE = False

logger = logging.getLogger(__name__)

class NotificationLevel(Enum):
    """通知级别枚举"""
    DEBUG = 1      # 调试信息
    INFO = 2       # 一般信息  
    WARNING = 3    # 警告
    ERROR = 4      # 错误
    CRITICAL = 5   # 严重错误

class NotificationType(Enum):
    """通知类型枚举"""
    SYSTEM_STATUS = "system_status"        # 系统状态
    BOT_STATUS = "bot_status"              # 机器人状态
    USER_ACTIVITY = "user_activity"        # 用户活动
    SUBMISSION = "submission"              # 投稿相关
    FILE_OPERATION = "file_operation"      # 文件操作
    ADMIN_ACTION = "admin_action"          # 管理员操作
    SECURITY = "security"                  # 安全事件
    PERFORMANCE = "performance"            # 性能监控
    MAINTENANCE = "maintenance"            # 维护通知
    CUSTOM = "custom"                      # 自定义通知

@dataclass
class NotificationEvent:
    """通知事件数据类"""
    id: str                              # 事件ID
    type: NotificationType               # 通知类型
    level: NotificationLevel             # 通知级别
    title: str                           # 标题
    message: str                         # 消息内容
    timestamp: datetime                  # 时间戳
    source: str                          # 来源
    target_users: List[int] = None       # 目标用户列表
    target_groups: List[int] = None      # 目标群组列表
    data: Dict[str, Any] = None          # 附加数据
    retry_count: int = 0                 # 重试次数
    max_retries: int = 3                 # 最大重试次数
    expires_at: Optional[datetime] = None # 过期时间

@dataclass 
class NotificationRule:
    """通知规则数据类"""
    id: str                              # 规则ID
    name: str                            # 规则名称
    event_types: List[NotificationType]  # 监听的事件类型
    conditions: Dict[str, Any]           # 触发条件
    target_users: List[int]              # 目标用户
    target_groups: List[int] = None      # 目标群组
    min_level: NotificationLevel = NotificationLevel.INFO  # 最小级别
    enabled: bool = True                 # 是否启用
    cooldown: int = 0                    # 冷却时间(秒)
    last_triggered: Optional[datetime] = None  # 上次触发时间

class EventBus:
    """
    事件总线
    Event Bus
    
    管理事件的发布和订阅
    """
    
    def __init__(self):
        """初始化事件总线"""
        self._subscribers: Dict[NotificationType, List[weakref.WeakMethod]] = {}
        self._lock = threading.RLock()
        
        logger.info("事件总线初始化完成")
    
    def subscribe(self, event_type: NotificationType, callback: Callable):
        """
        订阅事件
        
        Args:
            event_type: 事件类型
            callback: 回调函数
        """
        with self._lock:
            if event_type not in self._subscribers:
                self._subscribers[event_type] = []
            
            # 使用弱引用避免内存泄漏
            try:
                weak_callback = weakref.WeakMethod(callback)
                self._subscribers[event_type].append(weak_callback)
                logger.debug(f"订阅事件: {event_type.value}")
            except TypeError:
                # 普通函数使用WeakKeyDictionary不行，直接存储
                logger.warning(f"无法为函数创建弱引用: {callback}")
    
    def unsubscribe(self, event_type: NotificationType, callback: Callable):
        """
        取消订阅事件
        
        Args:
            event_type: 事件类型
            callback: 回调函数
        """
        with self._lock:
            if event_type in self._subscribers:
                # 清理失效的弱引用
                self._clean_dead_refs(event_type)
                logger.debug(f"取消订阅事件: {event_type.value}")
    
    def publish(self, event: NotificationEvent):
        """
        发布事件
        
        Args:
            event: 通知事件
        """
        with self._lock:
            if event.type in self._subscribers:
                # 清理失效的弱引用
                self._clean_dead_refs(event.type)
                
                # 通知所有订阅者
                for weak_callback in self._subscribers[event.type]:
                    callback = weak_callback()
                    if callback:
                        try:
                            # 异步调用回调函数
                            if asyncio.iscoroutinefunction(callback):
                                asyncio.create_task(callback(event))
                            else:
                                callback(event)
                        except Exception as e:
                            logger.error(f"事件回调执行失败: {e}")
                
                logger.debug(f"发布事件: {event.type.value} - {event.title}")
    
    def _clean_dead_refs(self, event_type: NotificationType):
        """清理失效的弱引用"""
        if event_type in self._subscribers:
            self._subscribers[event_type] = [
                ref for ref in self._subscribers[event_type] 
                if ref() is not None
            ]

class NotificationQueue:
    """
    通知队列
    Notification Queue
    
    管理通知的排队和批量处理
    """
    
    def __init__(self, max_size: int = 10000):
        """
        初始化通知队列
        
        Args:
            max_size: 最大队列大小
        """
        self.max_size = max_size
        self._queue: asyncio.Queue = asyncio.Queue(maxsize=max_size)
        self._workers: List[asyncio.Task] = []
        self._running = False
        
        # 统计信息
        self._stats = {
            'total_processed': 0,
            'successful': 0,
            'failed': 0,
            'retries': 0,
            'dropped': 0
        }
        
        logger.info(f"通知队列初始化完成: max_size={max_size}")
    
    async def start(self, num_workers: int = 3):
        """
        启动队列处理器
        
        Args:
            num_workers: 工作协程数量
        """
        if self._running:
            return
        
        self._running = True
        
        # 启动工作协程
        for i in range(num_workers):
            worker = asyncio.create_task(self._worker(f"notification-worker-{i}"))
            self._workers.append(worker)
        
        logger.info(f"通知队列已启动: {num_workers} 个工作协程")
    
    async def stop(self):
        """停止队列处理器"""
        if not self._running:
            return
        
        self._running = False
        
        # 等待队列清空
        await self._queue.join()
        
        # 取消所有工作协程
        for worker in self._workers:
            worker.cancel()
        
        await asyncio.gather(*self._workers, return_exceptions=True)
        self._workers.clear()
        
        logger.info("通知队列已停止")
    
    async def enqueue(self, event: NotificationEvent) -> bool:
        """
        添加通知到队列
        
        Args:
            event: 通知事件
            
        Returns:
            bool: 是否成功入队
        """
        try:
            # 检查过期时间
            if event.expires_at and datetime.now() > event.expires_at:
                logger.debug(f"通知已过期，丢弃: {event.id}")
                self._stats['dropped'] += 1
                return False
            
            # 尝试入队
            if self._queue.full():
                logger.warning("通知队列已满，丢弃最旧的通知")
                try:
                    self._queue.get_nowait()
                    self._stats['dropped'] += 1
                except:
                    pass
            
            await self._queue.put(event)
            logger.debug(f"通知入队: {event.id}")
            return True
            
        except Exception as e:
            logger.error(f"通知入队失败: {e}")
            self._stats['failed'] += 1
            return False
    
    async def _worker(self, name: str):
        """
        工作协程
        
        Args:
            name: 工作协程名称
        """
        logger.debug(f"通知工作协程启动: {name}")
        
        while self._running:
            try:
                # 获取通知事件
                event = await asyncio.wait_for(self._queue.get(), timeout=1.0)
                
                try:
                    # 处理通知
                    success = await self._process_notification(event)
                    
                    if success:
                        self._stats['successful'] += 1
                    else:
                        # 重试逻辑
                        if event.retry_count < event.max_retries:
                            event.retry_count += 1
                            await asyncio.sleep(min(2 ** event.retry_count, 60))  # 指数退避
                            await self._queue.put(event)
                            self._stats['retries'] += 1
                            logger.debug(f"通知重试: {event.id} (第{event.retry_count}次)")
                        else:
                            self._stats['failed'] += 1
                            logger.error(f"通知处理失败，达到最大重试次数: {event.id}")
                    
                    self._stats['total_processed'] += 1
                    
                except Exception as e:
                    logger.error(f"处理通知时发生异常: {event.id}: {e}")
                    self._stats['failed'] += 1
                
                finally:
                    # 标记任务完成
                    self._queue.task_done()
                    
            except asyncio.TimeoutError:
                # 超时，继续等待
                continue
            except asyncio.CancelledError:
                # 被取消
                logger.debug(f"通知工作协程被取消: {name}")
                break
            except Exception as e:
                logger.error(f"通知工作协程异常: {name}: {e}")
    
    async def _process_notification(self, event: NotificationEvent) -> bool:
        """
        处理单个通知
        
        Args:
            event: 通知事件
            
        Returns:
            bool: 是否处理成功
        """
        try:
            # 这里应该调用实际的通知发送逻辑
            # 例如发送Telegram消息、邮件等
            
            logger.info(f"处理通知: {event.type.value} - {event.title}")
            
            # 模拟处理延迟
            await asyncio.sleep(0.1)
            
            return True
            
        except Exception as e:
            logger.error(f"通知处理失败: {event.id}: {e}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """
        获取队列统计信息
        
        Returns:
            Dict: 统计信息
        """
        return {
            'queue_size': self._queue.qsize(),
            'max_size': self.max_size,
            'running': self._running,
            'workers': len(self._workers),
            'stats': self._stats.copy()
        }

class TelegramNotifier:
    """
    Telegram通知发送器
    Telegram Notifier
    
    通过Telegram发送通知消息
    """
    
    def __init__(self, bot_token: str = None):
        """
        初始化Telegram通知器
        
        Args:
            bot_token: 机器人Token
        """
        self.bot_token = bot_token
        self.bot: Optional[Bot] = None
        
        if TELEGRAM_AVAILABLE and bot_token:
            try:
                self.bot = Bot(token=bot_token)
                logger.info("Telegram通知器初始化完成")
            except Exception as e:
                logger.error(f"Telegram Bot初始化失败: {e}")
        else:
            logger.warning("Telegram库不可用或未提供Token")
    
    async def send_notification(self, event: NotificationEvent) -> bool:
        """
        发送Telegram通知
        
        Args:
            event: 通知事件
            
        Returns:
            bool: 是否发送成功
        """
        if not self.bot:
            logger.debug("Telegram Bot未初始化，跳过发送")
            return False
        
        try:
            # 格式化消息
            message = self._format_message(event)
            
            # 发送给目标用户
            if event.target_users:
                for user_id in event.target_users:
                    try:
                        await self.bot.send_message(
                            chat_id=user_id,
                            text=message,
                            parse_mode=ParseMode.HTML
                        )
                        logger.debug(f"通知已发送给用户: {user_id}")
                    except Exception as e:
                        logger.error(f"发送通知给用户失败: {user_id}: {e}")
                        return False
            
            # 发送给目标群组
            if event.target_groups:
                for group_id in event.target_groups:
                    try:
                        await self.bot.send_message(
                            chat_id=group_id,
                            text=message,
                            parse_mode=ParseMode.HTML
                        )
                        logger.debug(f"通知已发送给群组: {group_id}")
                    except Exception as e:
                        logger.error(f"发送通知给群组失败: {group_id}: {e}")
                        return False
            
            return True
            
        except Exception as e:
            logger.error(f"发送Telegram通知失败: {e}")
            return False
    
    def _format_message(self, event: NotificationEvent) -> str:
        """
        格式化通知消息
        
        Args:
            event: 通知事件
            
        Returns:
            str: 格式化后的消息
        """
        # 级别图标
        level_icons = {
            NotificationLevel.DEBUG: "🔍",
            NotificationLevel.INFO: "ℹ️",
            NotificationLevel.WARNING: "⚠️", 
            NotificationLevel.ERROR: "❌",
            NotificationLevel.CRITICAL: "🚨"
        }
        
        # 类型图标
        type_icons = {
            NotificationType.SYSTEM_STATUS: "🖥️",
            NotificationType.BOT_STATUS: "🤖",
            NotificationType.USER_ACTIVITY: "👤",
            NotificationType.SUBMISSION: "📝",
            NotificationType.FILE_OPERATION: "📁",
            NotificationType.ADMIN_ACTION: "👨‍💼",
            NotificationType.SECURITY: "🔐",
            NotificationType.PERFORMANCE: "📊",
            NotificationType.MAINTENANCE: "🔧",
            NotificationType.CUSTOM: "📢"
        }
        
        level_icon = level_icons.get(event.level, "📢")
        type_icon = type_icons.get(event.type, "📢")
        
        # 格式化时间
        time_str = event.timestamp.strftime("%Y-%m-%d %H:%M:%S")
        
        message = f"{level_icon} <b>{event.title}</b>\n\n"
        message += f"{type_icon} <b>类型:</b> {event.type.value}\n"
        message += f"🕐 <b>时间:</b> {time_str}\n"
        message += f"📍 <b>来源:</b> {event.source}\n\n"
        message += f"📄 <b>详情:</b>\n{event.message}"
        
        # 添加附加数据
        if event.data:
            message += f"\n\n📋 <b>附加信息:</b>\n"
            for key, value in event.data.items():
                message += f"• {key}: {value}\n"
        
        return message

class NotificationManager:
    """
    通知管理器主类
    Notification Manager Main Class
    
    整合所有通知功能
    """
    
    def __init__(self, bot_token: str = None):
        """
        初始化通知管理器
        
        Args:
            bot_token: Telegram机器人Token
        """
        # 初始化组件
        self.event_bus = EventBus()
        self.notification_queue = NotificationQueue()
        self.telegram_notifier = TelegramNotifier(bot_token)
        
        # 通知规则
        self.rules: Dict[str, NotificationRule] = {}
        
        # 订阅所有事件类型
        for event_type in NotificationType:
            self.event_bus.subscribe(event_type, self._handle_event)
        
        logger.info("通知管理器初始化完成")
    
    async def start(self):
        """启动通知管理器"""
        await self.notification_queue.start()
        logger.info("通知管理器已启动")
    
    async def stop(self):
        """停止通知管理器"""
        await self.notification_queue.stop()
        logger.info("通知管理器已停止")
    
    def add_rule(self, rule: NotificationRule):
        """
        添加通知规则
        
        Args:
            rule: 通知规则
        """
        self.rules[rule.id] = rule
        logger.info(f"添加通知规则: {rule.name}")
    
    def remove_rule(self, rule_id: str) -> bool:
        """
        移除通知规则
        
        Args:
            rule_id: 规则ID
            
        Returns:
            bool: 是否成功移除
        """
        if rule_id in self.rules:
            del self.rules[rule_id]
            logger.info(f"移除通知规则: {rule_id}")
            return True
        return False
    
    def get_rule(self, rule_id: str) -> Optional[NotificationRule]:
        """
        获取通知规则
        
        Args:
            rule_id: 规则ID
            
        Returns:
            NotificationRule: 通知规则
        """
        return self.rules.get(rule_id)
    
    async def send_notification(self, 
                               type: NotificationType,
                               level: NotificationLevel,
                               title: str,
                               message: str,
                               source: str = "system",
                               target_users: List[int] = None,
                               target_groups: List[int] = None,
                               data: Dict[str, Any] = None) -> str:
        """
        发送通知
        
        Args:
            type: 通知类型
            level: 通知级别
            title: 标题
            message: 消息内容
            source: 来源
            target_users: 目标用户列表
            target_groups: 目标群组列表
            data: 附加数据
            
        Returns:
            str: 通知事件ID
        """
        # 创建通知事件
        event_id = f"{type.value}_{int(time.time() * 1000)}"
        event = NotificationEvent(
            id=event_id,
            type=type,
            level=level,
            title=title,
            message=message,
            timestamp=datetime.now(),
            source=source,
            target_users=target_users or [],
            target_groups=target_groups or [],
            data=data or {}
        )
        
        # 发布事件
        self.event_bus.publish(event)
        
        return event_id
    
    async def _handle_event(self, event: NotificationEvent):
        """
        处理事件
        
        Args:
            event: 通知事件
        """
        # 应用通知规则
        for rule in self.rules.values():
            if self._should_notify(event, rule):
                # 检查冷却时间
                if self._check_cooldown(rule):
                    # 创建针对规则的通知事件
                    rule_event = NotificationEvent(
                        id=f"{event.id}_{rule.id}",
                        type=event.type,
                        level=event.level,
                        title=event.title,
                        message=event.message,
                        timestamp=event.timestamp,
                        source=event.source,
                        target_users=rule.target_users,
                        target_groups=rule.target_groups or [],
                        data=event.data
                    )
                    
                    # 加入通知队列
                    await self.notification_queue.enqueue(rule_event)
                    
                    # 更新规则触发时间
                    rule.last_triggered = datetime.now()
    
    def _should_notify(self, event: NotificationEvent, rule: NotificationRule) -> bool:
        """
        判断是否应该发送通知
        
        Args:
            event: 通知事件
            rule: 通知规则
            
        Returns:
            bool: 是否应该通知
        """
        # 检查规则是否启用
        if not rule.enabled:
            return False
        
        # 检查事件类型
        if event.type not in rule.event_types:
            return False
        
        # 检查通知级别
        if event.level.value < rule.min_level.value:
            return False
        
        # 检查条件
        if rule.conditions:
            for key, expected_value in rule.conditions.items():
                if key in event.data:
                    if event.data[key] != expected_value:
                        return False
                else:
                    return False
        
        return True
    
    def _check_cooldown(self, rule: NotificationRule) -> bool:
        """
        检查冷却时间
        
        Args:
            rule: 通知规则
            
        Returns:
            bool: 是否可以触发
        """
        if rule.cooldown <= 0:
            return True
        
        if rule.last_triggered is None:
            return True
        
        elapsed = (datetime.now() - rule.last_triggered).total_seconds()
        return elapsed >= rule.cooldown
    
    def get_stats(self) -> Dict[str, Any]:
        """
        获取通知管理器统计信息
        
        Returns:
            Dict: 统计信息
        """
        return {
            'rules_count': len(self.rules),
            'active_rules': len([r for r in self.rules.values() if r.enabled]),
            'queue_stats': self.notification_queue.get_stats(),
            'telegram_available': self.telegram_notifier.bot is not None
        }

# 全局通知管理器实例
_notification_manager: Optional[NotificationManager] = None

def get_notification_manager() -> NotificationManager:
    """
    获取全局通知管理器实例
    
    Returns:
        NotificationManager: 通知管理器实例
    """
    global _notification_manager
    if _notification_manager is None:
        raise RuntimeError("通知管理器未初始化，请先调用 initialize_notification_manager\()")
    return _notification_manager

def initialize_notification_manager(bot_token: str = None) -> NotificationManager:
    """
    初始化全局通知管理器
    
    Args:
        bot_token: Telegram机器人Token
        
    Returns:
        NotificationManager: 通知管理器实例
    """
    global _notification_manager
    _notification_manager = NotificationManager(bot_token)
    return _notification_manager

async def notify(type: NotificationType,
                level: NotificationLevel, 
                title: str,
                message: str,
                **kwargs) -> str:
    """
    快捷通知发送函数
    
    Args:
        type: 通知类型
        level: 通知级别
        title: 标题
        message: 消息内容
        **kwargs: 其他参数
        
    Returns:
        str: 通知事件ID
    """
    return await get_notification_manager().send_notification(
        type=type,
        level=level,
        title=title,
        message=message,
        **kwargs
    )