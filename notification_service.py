#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import logging
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from config_manager import ConfigManager
from database import DatabaseManager

logger = logging.getLogger(__name__)

class NotificationService:
    def __init__(self):
        self.config = ConfigManager()
        self.db = DatabaseManager(self.config.get_db_file())
        self.publish_bot = None
    
    async def get_publish_bot(self):
        """获取发布机器人实例"""
        if not self.publish_bot:
            self.publish_bot = Bot(token=self.config.get_publish_bot_token())
        return self.publish_bot
    
    async def send_submission_to_review_group(self, submission_id: int):
        """发送投稿到审核群"""
        try:
            submission = self.db.get_submission_by_id(submission_id)
            if not submission:
                logger.error(f"投稿 #{submission_id} 不存在")
                return False
            
            bot = await self.get_publish_bot()
            review_group_id = self.config.get_review_group_id()
            
            # 构建审核信息
            user_info = f"👤 投稿用户：{submission['username']} (ID: {submission['user_id']})"
            time_info = f"⏰ 投稿时间：{submission['submit_time']}"
            type_info = f"📝 内容类型：{submission['content_type']}"
            
            header_text = f"""
📋 **新投稿待审核 #{submission['id']}**

{user_info}
{time_info}
{type_info}
            """
            
            # 创建审核按钮
            keyboard = [
                [
                    InlineKeyboardButton("✅ 批准", callback_data=f"approve_{submission['id']}"),
                    InlineKeyboardButton("❌ 拒绝", callback_data=f"reject_{submission['id']}")
                ],
                [
                    InlineKeyboardButton("📊 用户统计", callback_data=f"user_stats_{submission['user_id']}"),
                    InlineKeyboardButton("🚫 封禁用户", callback_data=f"ban_user_{submission['user_id']}")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            # 根据内容类型发送对应的消息
            if submission['content_type'] == 'text':
                full_text = header_text + f"\n📄 **内容：**\n{submission['content']}"
                await bot.send_message(
                    chat_id=review_group_id,
                    text=full_text,
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=reply_markup
                )
            elif submission['content_type'] == 'photo':
                caption_text = header_text
                if submission['caption']:
                    caption_text += f"\n📝 **图片说明：**\n{submission['caption']}"
                
                await bot.send_photo(
                    chat_id=review_group_id,
                    photo=submission['media_file_id'],
                    caption=caption_text,
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=reply_markup
                )
            elif submission['content_type'] == 'video':
                caption_text = header_text
                if submission['caption']:
                    caption_text += f"\n📝 **视频说明：**\n{submission['caption']}"
                
                await bot.send_video(
                    chat_id=review_group_id,
                    video=submission['media_file_id'],
                    caption=caption_text,
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=reply_markup
                )
            elif submission['content_type'] == 'document':
                caption_text = header_text
                if submission['caption']:
                    caption_text += f"\n📝 **文档说明：**\n{submission['caption']}"
                
                await bot.send_document(
                    chat_id=review_group_id,
                    document=submission['media_file_id'],
                    caption=caption_text,
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=reply_markup
                )
            elif submission['content_type'] == 'voice':
                await bot.send_voice(
                    chat_id=review_group_id,
                    voice=submission['media_file_id'],
                    caption=header_text,
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=reply_markup
                )
            elif submission['content_type'] == 'audio':
                caption_text = header_text
                if submission['caption']:
                    caption_text += f"\n📝 **音频说明：**\n{submission['caption']}"
                
                await bot.send_audio(
                    chat_id=review_group_id,
                    audio=submission['media_file_id'],
                    caption=caption_text,
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=reply_markup
                )
            
            logger.info(f"投稿 #{submission_id} 已发送到审核群")
            return True
            
        except Exception as e:
            logger.error(f"发送投稿 #{submission_id} 到审核群失败: {e}")
            return False
    
    async def notify_approval_result(self, submission_id: int, approved: bool, reviewer_name: str):
        """通知审核结果给投稿用户"""
        try:
            submission = self.db.get_submission_by_id(submission_id)
            if not submission:
                return False
            
            # 这里可以通过投稿机器人发送通知给用户
            # 由于需要跨机器人通信，可以通过数据库或其他方式实现
            logger.info(f"投稿 #{submission_id} 审核结果: {'批准' if approved else '拒绝'} (审核员: {reviewer_name})")
            return True
            
        except Exception as e:
            logger.error(f"通知审核结果失败: {e}")
            return False