#!/usr/bin/env python3
# -<i>- coding: utf-8 -</i>-

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
        """发送投稿到审核群 - 整合为单条消息"""
        try:
            submission = self.db.get_submission_by_id(submission_id)
            if not submission:
                logger.error(f"投稿 #{submission_id} 不存在")
                return False
            
            bot = await self.get_publish_bot()
            review_group_id = self.config.get_review_group_id()
            
            # 获取用户统计信息
            user_stats = self.db.get_user_stats(submission['user_id'])
            is_banned = self.db.is_user_banned(submission['user_id'])
            
            # 构建完整的审核信息
            header_text = f"""
🔍 <b>投稿审核 #{submission['id']}</b>

👤 <b>投稿用户信息：</b>
• 用户名：{submission['username']}
• 用户ID：{submission['user_id']}
• 状态：{'🚫 已封禁' if is_banned else '✅ 正常'}

📊 <b>用户投稿统计：</b>
• 总投稿：{user_stats['total']} 条
• 待审核：{user_stats['pending']} 条
• 已发布：{user_stats['published']} 条
• 已拒绝：{user_stats['rejected']} 条
• 通过率：{(user_stats['published'] / user_stats['total'] * 100) if user_stats['total'] > 0 else 0:.1f}%

⏰ <b>投稿信息：</b>
• 投稿时间：{submission['submit_time']}
• 内容类型：{self._get_content_type_display(submission['content_type'])}
            """
            
            # 添加内容信息
            if submission['content_type'] == 'text':
                header_text += f"\n📄 <b>投稿内容：</b>\n{submission['content'][:500]}"
                if len(submission['content']) > 500:
                    header_text += "...(内容过长已截断)"
            elif submission['caption']:
                header_text += f"\n📝 <b>说明文字：</b>\n{submission['caption'][:200]}"
                if len(submission['caption']) > 200:
                    header_text += "...(说明过长已截断)"
            
            # 创建审核按钮
            keyboard = [
                [
                    InlineKeyboardButton("✅ 批准并发布", callback_data=f"approve_{submission['id']}"),
                    InlineKeyboardButton("❌ 拒绝投稿", callback_data=f"reject_{submission['id']}")
                ],
                [
                    InlineKeyboardButton("📊 详细统计", callback_data=f"user_stats_{submission['user_id']}"),
                    InlineKeyboardButton("🚫 封禁用户", callback_data=f"ban_user_{submission['user_id']}")
                ],
                [
                    InlineKeyboardButton("🔄 刷新信息", callback_data=f"refresh_{submission['id']}"),
                    InlineKeyboardButton("📋 查看原文", callback_data=f"view_full_{submission['id']}")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            # 根据内容类型发送对应的消息（包含完整审核信息）
            if submission['content_type'] == 'text':
                # 纯文字投稿
                await bot.send_message(
                    chat_id=review_group_id,
                    text=header_text,
                    parse_mode=ParseMode.HTML,
                    reply_markup=reply_markup
                )
            elif submission['content_type'] == 'photo':
                # 图片投稿 - 发送图片并附带完整审核信息
                await bot.send_photo(
                    chat_id=review_group_id,
                    photo=submission['media_file_id'],
                    caption=header_text,
                    parse_mode=ParseMode.HTML,
                    reply_markup=reply_markup
                )
            elif submission['content_type'] == 'video':
                # 视频投稿 - 发送视频并附带完整审核信息
                await bot.send_video(
                    chat_id=review_group_id,
                    video=submission['media_file_id'],
                    caption=header_text,
                    parse_mode=ParseMode.HTML,
                    reply_markup=reply_markup
                )
            elif submission['content_type'] == 'video_note':
                # 视频消息（圆形视频）
                await bot.send_video_note(
                    chat_id=review_group_id,
                    video_note=submission['media_file_id'],
                    reply_markup=reply_markup
                )
                # 视频消息无法添加caption，需要单独发送审核信息
                await bot.send_message(
                    chat_id=review_group_id,
                    text=header_text,
                    parse_mode=ParseMode.HTML
                )
            elif submission['content_type'] == 'document':
                # 文档投稿
                await bot.send_document(
                    chat_id=review_group_id,
                    document=submission['media_file_id'],
                    caption=header_text,
                    parse_mode=ParseMode.HTML,
                    reply_markup=reply_markup
                )
            elif submission['content_type'] == 'voice':
                # 语音消息
                await bot.send_voice(
                    chat_id=review_group_id,
                    voice=submission['media_file_id'],
                    caption=header_text,
                    parse_mode=ParseMode.HTML,
                    reply_markup=reply_markup
                )
            elif submission['content_type'] == 'audio':
                # 音频文件
                await bot.send_audio(
                    chat_id=review_group_id,
                    audio=submission['media_file_id'],
                    caption=header_text,
                    parse_mode=ParseMode.HTML,
                    reply_markup=reply_markup
                )
            elif submission['content_type'] == 'sticker':
                # 贴纸
                await bot.send_sticker(
                    chat_id=review_group_id,
                    sticker=submission['media_file_id'],
                    reply_markup=reply_markup
                )
                # 贴纸无法添加caption，需要单独发送审核信息
                await bot.send_message(
                    chat_id=review_group_id,
                    text=header_text,
                    parse_mode=ParseMode.HTML
                )
            elif submission['content_type'] == 'animation':
                # GIF动图
                await bot.send_animation(
                    chat_id=review_group_id,
                    animation=submission['media_file_id'],
                    caption=header_text,
                    parse_mode=ParseMode.HTML,
                    reply_markup=reply_markup
                )
            elif submission['content_type'] == 'location':
                # 位置信息
                # 位置信息需要特殊处理，因为它包含经纬度
                location_data = submission['content']  # 这里应该是经纬度信息
                await bot.send_message(
                    chat_id=review_group_id,
                    text=header_text + f"\n📍 <b>位置信息：</b>\n{location_data}",
                    parse_mode=ParseMode.HTML,
                    reply_markup=reply_markup
                )
            elif submission['content_type'] == 'contact':
                # 联系人信息
                contact_data = submission['content']  # 这里应该是联系人信息
                await bot.send_message(
                    chat_id=review_group_id,
                    text=header_text + f"\n👤 <b>联系人信息：</b>\n{contact_data}",
                    parse_mode=ParseMode.HTML,
                    reply_markup=reply_markup
                )
            else:
                # 未知类型，发送纯文本
                await bot.send_message(
                    chat_id=review_group_id,
                    text=header_text + f"\n⚠️ <b>未知内容类型：</b> {submission['content_type']}",
                    parse_mode=ParseMode.HTML,
                    reply_markup=reply_markup
                )
            
            logger.info(f"投稿 #{submission_id} 已整合发送到审核群")
            return True
            
        except Exception as e:
            logger.error(f"发送投稿 #{submission_id} 到审核群失败: {e}")
            return False
    
    def _get_content_type_display(self, content_type: str) -> str:
        """获取内容类型的中文显示名称"""
        type_map = {
            'text': '📝 文字',
            'photo': '🖼️ 图片',
            'video': '🎥 视频',
            'video_note': '🎬 视频消息',
            'document': '📎 文档',
            'voice': '🎤 语音',
            'audio': '🎵 音频',
            'sticker': '😀 贴纸',
            'animation': '🎭 动图',
            'location': '📍 位置',
            'contact': '👤 联系人'
        }
        return type_map.get(content_type, f'❓ {content_type}')
    
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