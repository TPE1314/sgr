#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.constants import ParseMode
from database import DatabaseManager
from config_manager import ConfigManager
from notification_service import NotificationService

# 配置日志
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler('submission_bot.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class SubmissionBot:
    def __init__(self):
        self.config = ConfigManager()
        self.db = DatabaseManager(self.config.get_db_file())
        self.notification_service = NotificationService()
        self.app = None
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理 /start 命令"""
        user = update.effective_user
        welcome_text = f"""
🎯 欢迎使用投稿机器人！

👋 你好 {user.first_name}！

📝 **如何投稿：**
• 直接发送文字、图片、视频、文档等内容
• 支持带说明文字的媒体文件
• 发送后会自动提交到审核队列

📊 **查看投稿状态：**
• 使用 /status 查看你的投稿统计
• 使用 /my_submissions 查看投稿历史

ℹ️ **注意事项：**
• 请确保内容符合社区规范
• 投稿需要管理员审核后才会发布
• 请勿发送违规内容

开始投稿吧！直接发送内容即可。
        """
        
        await update.message.reply_text(
            welcome_text,
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """查看用户投稿统计"""
        user_id = update.effective_user.id
        
        # 检查用户是否被封禁
        if self.db.is_user_banned(user_id):
            await update.message.reply_text("❌ 您已被封禁，无法查看状态。")
            return
        
        stats = self.db.get_user_stats(user_id)
        
        stats_text = f"""
📊 **您的投稿统计**

📝 总投稿数：{stats['total']}
⏳ 待审核：{stats['pending']}
✅ 已通过：{stats['approved']}
📢 已发布：{stats['published']}
❌ 已拒绝：{stats['rejected']}

继续加油投稿吧！ 💪
        """
        
        await update.message.reply_text(
            stats_text,
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """帮助命令"""
        help_text = """
🤖 **投稿机器人帮助**

📋 **可用命令：**
/start - 开始使用机器人
/status - 查看投稿统计
/help - 显示此帮助信息

📝 **投稿方式：**
• 文字消息：直接发送文字内容
• 图片：发送图片，可带说明文字
• 视频：发送视频，可带说明文字
• 文档：发送文档文件
• 音频：发送音频文件

✨ **小贴士：**
• 所有投稿都会进入审核队列
• 审核通过后会自动发布到频道
• 保持内容质量，提高通过率

如有问题，请联系管理员。
        """
        
        await update.message.reply_text(
            help_text,
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def handle_text_submission(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理文字投稿"""
        user = update.effective_user
        
        # 检查用户是否被封禁
        if self.db.is_user_banned(user.id):
            await update.message.reply_text("❌ 您已被封禁，无法投稿。")
            return
        
        content = update.message.text
        
        # 添加到数据库
        submission_id = self.db.add_submission(
            user_id=user.id,
            username=user.username or user.first_name,
            content_type='text',
            content=content
        )
        
        success_text = f"""
✅ **投稿提交成功！**

📄 投稿ID：{submission_id}
📝 类型：文字
⏳ 状态：待审核

您的投稿已进入审核队列，请耐心等待管理员审核。
        """
        
        await update.message.reply_text(
            success_text,
            parse_mode=ParseMode.MARKDOWN
        )
        
        # 发送到审核群
        await self.notification_service.send_submission_to_review_group(submission_id)
        
        logger.info(f"用户 {user.id} ({user.username}) 提交了文字投稿 #{submission_id}")
    
    async def handle_photo_submission(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理图片投稿"""
        user = update.effective_user
        
        # 检查用户是否被封禁
        if self.db.is_user_banned(user.id):
            await update.message.reply_text("❌ 您已被封禁，无法投稿。")
            return
        
        photo = update.message.photo[-1]  # 获取最高质量的图片
        caption = update.message.caption or ""
        
        # 添加到数据库
        submission_id = self.db.add_submission(
            user_id=user.id,
            username=user.username or user.first_name,
            content_type='photo',
            media_file_id=photo.file_id,
            caption=caption
        )
        
        success_text = f"""
✅ **投稿提交成功！**

📄 投稿ID：{submission_id}
🖼️ 类型：图片
📝 说明：{caption[:50] + "..." if len(caption) > 50 else caption}
⏳ 状态：待审核

您的投稿已进入审核队列，请耐心等待管理员审核。
        """
        
        await update.message.reply_text(
            success_text,
            parse_mode=ParseMode.MARKDOWN
        )
        
        # 发送到审核群
        await self.notification_service.send_submission_to_review_group(submission_id)
        
        logger.info(f"用户 {user.id} ({user.username}) 提交了图片投稿 #{submission_id}")
    
    async def handle_video_submission(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理视频投稿"""
        user = update.effective_user
        
        # 检查用户是否被封禁
        if self.db.is_user_banned(user.id):
            await update.message.reply_text("❌ 您已被封禁，无法投稿。")
            return
        
        video = update.message.video
        caption = update.message.caption or ""
        
        # 添加到数据库
        submission_id = self.db.add_submission(
            user_id=user.id,
            username=user.username or user.first_name,
            content_type='video',
            media_file_id=video.file_id,
            caption=caption
        )
        
        success_text = f"""
✅ **投稿提交成功！**

📄 投稿ID：{submission_id}
🎥 类型：视频
📝 说明：{caption[:50] + "..." if len(caption) > 50 else caption}
⏳ 状态：待审核

您的投稿已进入审核队列，请耐心等待管理员审核。
        """
        
        await update.message.reply_text(
            success_text,
            parse_mode=ParseMode.MARKDOWN
        )
        
        # 发送到审核群
        await self.notification_service.send_submission_to_review_group(submission_id)
        
        logger.info(f"用户 {user.id} ({user.username}) 提交了视频投稿 #{submission_id}")
    
    async def handle_document_submission(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理文档投稿"""
        user = update.effective_user
        
        # 检查用户是否被封禁
        if self.db.is_user_banned(user.id):
            await update.message.reply_text("❌ 您已被封禁，无法投稿。")
            return
        
        document = update.message.document
        caption = update.message.caption or ""
        
        # 添加到数据库
        submission_id = self.db.add_submission(
            user_id=user.id,
            username=user.username or user.first_name,
            content_type='document',
            media_file_id=document.file_id,
            caption=caption
        )
        
        success_text = f"""
✅ **投稿提交成功！**

📄 投稿ID：{submission_id}
📎 类型：文档
📝 文件名：{document.file_name or "未知"}
📝 说明：{caption[:50] + "..." if len(caption) > 50 else caption}
⏳ 状态：待审核

您的投稿已进入审核队列，请耐心等待管理员审核。
        """
        
        await update.message.reply_text(
            success_text,
            parse_mode=ParseMode.MARKDOWN
        )
        
        # 发送到审核群
        await self.notification_service.send_submission_to_review_group(submission_id)
        
        logger.info(f"用户 {user.id} ({user.username}) 提交了文档投稿 #{submission_id}")
    
    async def handle_audio_submission(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理音频投稿"""
        user = update.effective_user
        
        # 检查用户是否被封禁
        if self.db.is_user_banned(user.id):
            await update.message.reply_text("❌ 您已被封禁，无法投稿。")
            return
        
        audio = update.message.audio or update.message.voice
        caption = update.message.caption or ""
        content_type = 'voice' if update.message.voice else 'audio'
        
        # 添加到数据库
        submission_id = self.db.add_submission(
            user_id=user.id,
            username=user.username or user.first_name,
            content_type=content_type,
            media_file_id=audio.file_id,
            caption=caption
        )
        
        success_text = f"""
✅ **投稿提交成功！**

📄 投稿ID：{submission_id}
🎵 类型：{"语音" if content_type == 'voice' else "音频"}
📝 说明：{caption[:50] + "..." if len(caption) > 50 else caption}
⏳ 状态：待审核

您的投稿已进入审核队列，请耐心等待管理员审核。
        """
        
        await update.message.reply_text(
            success_text,
            parse_mode=ParseMode.MARKDOWN
        )
        
        # 发送到审核群
        await self.notification_service.send_submission_to_review_group(submission_id)
        
        logger.info(f"用户 {user.id} ({user.username}) 提交了{content_type}投稿 #{submission_id}")
    
    def run(self):
        """启动机器人"""
        # 创建应用
        self.app = Application.builder().token(self.config.get_submission_bot_token()).build()
        
        # 添加处理器
        self.app.add_handler(CommandHandler("start", self.start_command))
        self.app.add_handler(CommandHandler("status", self.status_command))
        self.app.add_handler(CommandHandler("help", self.help_command))
        
        # 消息处理器
        self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_text_submission))
        self.app.add_handler(MessageHandler(filters.PHOTO, self.handle_photo_submission))
        self.app.add_handler(MessageHandler(filters.VIDEO, self.handle_video_submission))
        self.app.add_handler(MessageHandler(filters.DOCUMENT, self.handle_document_submission))
        self.app.add_handler(MessageHandler(filters.AUDIO | filters.VOICE, self.handle_audio_submission))
        
        logger.info("投稿机器人启动中...")
        
        # 启动机器人
        self.app.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    bot = SubmissionBot()
    bot.run()