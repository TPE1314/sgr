#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
电报多管理员客服系统 - 主程序
支持多用户同时与单管理员实时对话，富媒体处理，智能路由
"""

import asyncio
import logging
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum
import sqlite3
import redis
from aiogram import Bot, Dispatcher, types, F
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import Command
from aiogram.types import FSInputFile, InlineKeyboardMarkup, InlineKeyboardButton
import aiofiles
import aiofiles.os
from pathlib import Path
import hashlib
import mimetypes
import os

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('telebot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 配置
BOT_TOKEN = os.getenv('BOT_TOKEN', 'YOUR_BOT_TOKEN')
REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379')
MAX_SESSIONS_PER_ADMIN = int(os.getenv('MAX_SESSIONS_PER_ADMIN', '50'))
SESSION_TIMEOUT = int(os.getenv('SESSION_TIMEOUT', '1800'))  # 30分钟

# 状态枚举
class SessionStatus(Enum):
    WAITING = "waiting"
    ACTIVE = "active"
    CLOSED = "closed"
    TRANSFERRED = "transferred"

class MessageType(Enum):
    TEXT = "text"
    PHOTO = "photo"
    VIDEO = "video"
    DOCUMENT = "document"
    VOICE = "voice"
    AUDIO = "audio"

# 数据类
@dataclass
class Admin:
    id: int
    name: str
    username: str
    max_sessions: int
    active_sessions: int = 0
    avg_response_time: float = 0.0
    is_online: bool = True
    last_active: datetime = None

@dataclass
class Conversation:
    id: str
    user_id: int
    admin_id: Optional[int]
    status: SessionStatus
    created_at: datetime
    last_active: datetime
    user_name: str
    user_username: str

@dataclass
class Message:
    id: str
    conv_id: str
    content: str
    media_url: Optional[str]
    msg_type: MessageType
    timestamp: datetime
    sender_id: int
    is_from_user: bool

# 数据库管理器
class DatabaseManager:
    def __init__(self, db_file: str = "telebot.db"):
        self.db_file = db_file
        self.init_database()
    
    def init_database(self):
        """初始化数据库表"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        # 管理员表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS admins (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                username TEXT,
                max_sessions INTEGER DEFAULT 50,
                avg_response_time REAL DEFAULT 0.0,
                is_online BOOLEAN DEFAULT 1,
                last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 会话表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS conversations (
                id TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL,
                admin_id INTEGER,
                status TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                user_name TEXT,
                user_username TEXT
            )
        ''')
        
        # 消息表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                id TEXT PRIMARY KEY,
                conv_id TEXT NOT NULL,
                content TEXT,
                media_url TEXT,
                msg_type TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                sender_id INTEGER NOT NULL,
                is_from_user BOOLEAN NOT NULL,
                FOREIGN KEY (conv_id) REFERENCES conversations (id)
            )
        ''')
        
        conn.commit()
        conn.close()
        logger.info("数据库初始化完成")
    
    def add_admin(self, admin: Admin):
        """添加管理员"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO admins 
            (id, name, username, max_sessions, avg_response_time, is_online, last_active)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (admin.id, admin.name, admin.username, admin.max_sessions, 
              admin.avg_response_time, admin.is_online, admin.last_active))
        conn.commit()
        conn.close()
    
    def get_available_admin(self) -> Optional[Admin]:
        """获取可用的管理员"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, name, username, max_sessions, active_sessions, 
                   avg_response_time, is_online, last_active
            FROM admins 
            WHERE is_online = 1 AND active_sessions < max_sessions
            ORDER BY active_sessions ASC, avg_response_time ASC
            LIMIT 1
        ''')
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return Admin(
                id=row[0], name=row[1], username=row[2], 
                max_sessions=row[3], active_sessions=row[4],
                avg_response_time=row[5], is_online=bool(row[6]),
                last_active=datetime.fromisoformat(row[7]) if row[7] else None
            )
        return None
    
    def create_conversation(self, conv: Conversation):
        """创建会话"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO conversations 
            (id, user_id, admin_id, status, created_at, last_active, user_name, user_username)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (conv.id, conv.user_id, conv.admin_id, conv.status.value,
              conv.created_at, conv.last_active, conv.user_name, conv.user_username))
        conn.commit()
        conn.close()
    
    def update_conversation_status(self, conv_id: str, status: SessionStatus, admin_id: Optional[int] = None):
        """更新会话状态"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        if admin_id is not None:
            cursor.execute('''
                UPDATE conversations 
                SET status = ?, admin_id = ?, last_active = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (status.value, admin_id, conv_id))
        else:
            cursor.execute('''
                UPDATE conversations 
                SET status = ?, last_active = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (status.value, conv_id))
        conn.commit()
        conn.close()
    
    def add_message(self, msg: Message):
        """添加消息"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO messages 
            (id, conv_id, content, media_url, msg_type, timestamp, sender_id, is_from_user)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (msg.id, msg.conv_id, msg.content, msg.media_url,
              msg.msg_type.value, msg.timestamp, msg.sender_id, msg.is_from_user))
        conn.commit()
        conn.close()

# Redis缓存管理器
class RedisManager:
    def __init__(self, redis_url: str):
        self.redis = redis.from_url(redis_url)
    
    async def set_session_data(self, conv_id: str, data: dict):
        """设置会话数据到Redis"""
        await asyncio.to_thread(
            self.redis.setex, 
            f"session:{conv_id}", 
            SESSION_TIMEOUT, 
            json.dumps(data)
        )
    
    async def get_session_data(self, conv_id: str) -> Optional[dict]:
        """从Redis获取会话数据"""
        data = await asyncio.to_thread(self.redis.get, f"session:{conv_id}")
        return json.loads(data) if data else None
    
    async def increment_admin_sessions(self, admin_id: int):
        """增加管理员活跃会话数"""
        await asyncio.to_thread(
            self.redis.incr, 
            f"admin_sessions:{admin_id}"
        )
    
    async def decrement_admin_sessions(self, admin_id: int):
        """减少管理员活跃会话数"""
        await asyncio.to_thread(
            self.redis.decr, 
            f"admin_sessions:{admin_id}"
        )

# 会话路由器
class SessionRouter:
    def __init__(self, db: DatabaseManager, redis: RedisManager):
        self.db = db
        self.redis = redis
        self.active_conversations: Dict[str, Conversation] = {}
    
    async def create_user_session(self, user_id: int, user_name: str, user_username: str) -> Conversation:
        """为用户创建新会话"""
        conv_id = f"conv_{user_id}_{int(time.time())}"
        
        # 获取可用管理员
        admin = self.db.get_available_admin()
        
        conv = Conversation(
            id=conv_id,
            user_id=user_id,
            admin_id=admin.id if admin else None,
            status=SessionStatus.WAITING if admin else SessionStatus.WAITING,
            created_at=datetime.now(),
            last_active=datetime.now(),
            user_name=user_name,
            user_username=user_username
        )
        
        # 保存到数据库
        self.db.create_conversation(conv)
        
        # 保存到内存
        self.active_conversations[conv_id] = conv
        
        # 如果分配了管理员，更新Redis计数
        if admin:
            await self.redis.increment_admin_sessions(admin.id)
        
        logger.info(f"创建会话 {conv_id} 用户: {user_name} 管理员: {admin.name if admin else '等待中'}")
        return conv
    
    async def assign_admin_to_session(self, conv_id: str) -> Optional[Admin]:
        """为会话分配管理员"""
        admin = self.db.get_available_admin()
        if admin:
            self.db.update_conversation_status(conv_id, SessionStatus.ACTIVE, admin.id)
            await self.redis.increment_admin_sessions(admin.id)
            
            # 更新内存中的会话
            if conv_id in self.active_conversations:
                self.active_conversations[conv_id].admin_id = admin.id
                self.active_conversations[conv_id].status = SessionStatus.ACTIVE
            
            logger.info(f"会话 {conv_id} 分配给管理员 {admin.name}")
            return admin
        return None
    
    def get_conversation(self, conv_id: str) -> Optional[Conversation]:
        """获取会话信息"""
        return self.active_conversations.get(conv_id)
    
    async def close_session(self, conv_id: str):
        """关闭会话"""
        if conv_id in self.active_conversations:
            conv = self.active_conversations[conv_id]
            if conv.admin_id:
                await self.redis.decrement_admin_sessions(conv.admin_id)
            
            self.db.update_conversation_status(conv_id, SessionStatus.CLOSED)
            del self.active_conversations[conv_id]
            logger.info(f"会话 {conv_id} 已关闭")

# 媒体处理器
class MediaProcessor:
    def __init__(self, upload_dir: str = "uploads"):
        self.upload_dir = Path(upload_dir)
        self.upload_dir.mkdir(exist_ok=True)
    
    async def process_photo(self, photo: types.PhotoSize) -> str:
        """处理图片"""
        file_id = photo.file_id
        file_path = self.upload_dir / f"photo_{file_id}.jpg"
        
        # 这里可以添加图片压缩、水印、OCR等功能
        # 简化版本直接返回文件ID
        return file_id
    
    async def process_video(self, video: types.Video) -> str:
        """处理视频"""
        file_id = video.file_id
        # 这里可以添加视频转码、关键帧提取等功能
        return file_id
    
    async def process_document(self, document: types.Document) -> str:
        """处理文档"""
        file_id = document.file_id
        # 这里可以添加病毒扫描、类型过滤等功能
        return file_id
    
    async def process_voice(self, voice: types.Voice) -> str:
        """处理语音"""
        file_id = voice.file_id
        # 这里可以添加语音转文字、情感分析等功能
        return file_id

# 主机器人类
class TeleBot:
    def __init__(self):
        self.bot = Bot(token=BOT_TOKEN)
        self.dp = Dispatcher(storage=MemoryStorage())
        self.db = DatabaseManager()
        self.redis = RedisManager(REDIS_URL)
        self.router = SessionRouter(self.db, self.redis)
        self.media_processor = MediaProcessor()
        
        # 注册处理器
        self.register_handlers()
        
        # 初始化默认管理员
        self.init_default_admins()
    
    def init_default_admins(self):
        """初始化默认管理员"""
        # 这里应该从配置文件读取管理员信息
        default_admin = Admin(
            id=123456789,  # 替换为实际的管理员ID
            name="客服A",
            username="support_a",
            max_sessions=MAX_SESSIONS_PER_ADMIN
        )
        self.db.add_admin(default_admin)
        logger.info("默认管理员已初始化")
    
    def register_handlers(self):
        """注册消息处理器"""
        # 开始命令
        @self.dp.message(Command("start"))
        async def cmd_start(message: types.Message):
            await self.handle_start(message)
        
        # 处理文本消息
        @self.dp.message(F.text)
        async def handle_text(message: types.Message):
            await self.handle_message(message)
        
        # 处理图片
        @self.dp.message(F.photo)
        async def handle_photo(message: types.Message):
            await self.handle_media(message, MessageType.PHOTO)
        
        # 处理视频
        @self.dp.message(F.video)
        async def handle_video(message: types.Message):
            await self.handle_media(message, MessageType.VIDEO)
        
        # 处理文档
        @self.dp.message(F.document)
        async def handle_document(message: types.Message):
            await self.handle_media(message, MessageType.DOCUMENT)
        
        # 处理语音
        @self.dp.message(F.voice)
        async def handle_voice(message: types.Message):
            await self.handle_media(message, MessageType.VOICE)
    
    async def handle_start(self, message: types.Message):
        """处理开始命令"""
        user_id = message.from_user.id
        user_name = message.from_user.full_name
        user_username = message.from_user.username or ""
        
        # 创建新会话
        conv = await self.router.create_user_session(user_id, user_name, user_username)
        
        # 发送欢迎消息
        welcome_text = f"""
👋 欢迎使用客服系统！

🆔 会话ID: {conv.id}
👤 用户: {user_name}
⏰ 创建时间: {conv.created_at.strftime('%H:%M:%S')}

正在为您分配客服人员，请稍候...
        """
        
        await message.answer(welcome_text)
        
        # 尝试分配管理员
        admin = await self.router.assign_admin_to_session(conv.id)
        if admin:
            await message.answer(f"✅ 已为您分配客服: {admin.name}")
        else:
            await message.answer("⏳ 当前客服繁忙，请稍候...")
    
    async def handle_message(self, message: types.Message):
        """处理文本消息"""
        user_id = message.from_user.id
        
        # 查找用户的活跃会话
        conv = None
        for c in self.router.active_conversations.values():
            if c.user_id == user_id and c.status == SessionStatus.ACTIVE:
                conv = c
                break
        
        if not conv:
            await message.answer("❌ 请先使用 /start 开始会话")
            return
        
        # 保存消息到数据库
        msg = Message(
            id=f"msg_{int(time.time())}_{user_id}",
            conv_id=conv.id,
            content=message.text,
            media_url=None,
            msg_type=MessageType.TEXT,
            timestamp=datetime.now(),
            sender_id=user_id,
            is_from_user=True
        )
        self.db.add_message(msg)
        
        # 更新会话活跃时间
        conv.last_active = datetime.now()
        
        # 转发给管理员
        if conv.admin_id:
            await self.forward_to_admin(conv, msg)
            await message.answer("✅ 消息已发送给客服")
        else:
            await message.answer("⏳ 正在为您分配客服，请稍候...")
    
    async def handle_media(self, message: types.Message, msg_type: MessageType):
        """处理媒体消息"""
        user_id = message.from_user.id
        
        # 查找用户的活跃会话
        conv = None
        for c in self.router.active_conversations.values():
            if c.user_id == user_id and c.status == SessionStatus.ACTIVE:
                conv = c
                break
        
        if not conv:
            await message.answer("❌ 请先使用 /start 开始会话")
            return
        
        # 处理媒体文件
        media_url = ""
        if msg_type == MessageType.PHOTO:
            media_url = await self.media_processor.process_photo(message.photo[-1])
        elif msg_type == MessageType.VIDEO:
            media_url = await self.media_processor.process_video(message.video)
        elif msg_type == MessageType.DOCUMENT:
            media_url = await self.media_processor.process_document(message.document)
        elif msg_type == MessageType.VOICE:
            media_url = await self.media_processor.process_voice(message.voice)
        
        # 保存消息到数据库
        msg = Message(
            id=f"msg_{int(time.time())}_{user_id}",
            conv_id=conv.id,
            content=f"媒体消息 ({msg_type.value})",
            media_url=media_url,
            msg_type=msg_type,
            timestamp=datetime.now(),
            sender_id=user_id,
            is_from_user=True
        )
        self.db.add_message(msg)
        
        # 更新会话活跃时间
        conv.last_active = datetime.now()
        
        # 转发给管理员
        if conv.admin_id:
            await self.forward_to_admin(conv, msg)
            await message.answer(f"✅ {msg_type.value} 已发送给客服")
        else:
            await message.answer("⏳ 正在为您分配客服，请稍候...")
    
    async def forward_to_admin(self, conv: Conversation, msg: Message):
        """转发消息给管理员"""
        try:
            # 这里应该实现实际的消息转发逻辑
            # 简化版本只记录日志
            logger.info(f"转发消息到管理员 {conv.admin_id}: {msg.content}")
            
            # 可以在这里实现：
            # 1. 发送Telegram消息给管理员
            # 2. 更新Web界面
            # 3. 发送推送通知
            
        except Exception as e:
            logger.error(f"转发消息失败: {e}")
    
    async def start(self):
        """启动机器人"""
        logger.info("启动电报多管理员客服系统...")
        await self.dp.start_polling(self.bot)

# 主函数
async def main():
    """主函数"""
    bot = TeleBot()
    await bot.start()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("机器人已停止")
    except Exception as e:
        logger.error(f"启动失败: {e}")