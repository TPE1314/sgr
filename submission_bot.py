#!/usr/bin/env python3
# -<i>- coding: utf-8 -</i>-

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
    format='%\(asctime)s - %(name)s - %(levelname)s - %(message)s',
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
        self.db = DatabaseManager(self.config.get_db_file\())
        self.notification_service = NotificationService()
        self.app = None
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理 /start 命令"""
        user = update.effective_user
        welcome_text = f"""
🎯 欢迎使用投稿机器人！

👋 你好 {user.first_name}！

📝 <b>如何投稿：</b>
• 直接在<b>私聊中</b>发送文字、图片、视频、文档等内容
• 支持带说明文字的媒体文件
• 发送后会自动提交到审核队列

🚫 <b>重要提醒：</b>
• <b>只接收私聊投稿</b>，群组中无法投稿
• 这样可以保护您的隐私，避免群组干扰

📊 <b>查看投稿状态：</b>
• 使用 /status 查看你的投稿统计
• 使用 /help 查看帮助信息

ℹ️ <b>注意事项：</b>
• 请确保内容符合社区规范
• 投稿需要管理员审核后才会发布
• 请勿发送违规内容

开始投稿吧！直接在私聊中发送内容即可。
        """
        
        await update.message.reply_text(
            welcome_text,
            parse_mode=ParseMode.HTML
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
📊 <b>您的投稿统计</b>

📝 总投稿数：{stats['total']}
⏳ 待审核：{stats['pending']}
✅ 已通过：{stats['approved']}
📢 已发布：{stats['published']}
❌ 已拒绝：{stats['rejected']}

继续加油投稿吧！ 💪
        """
        
        await update.message.reply_text(
            stats_text,
            parse_mode=ParseMode.HTML
        )
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """帮助命令"""
        help_text = """
🤖 <b>投稿机器人帮助</b>

📋 <b>可用命令：</b>
/start - 开始使用机器人
/status - 查看投稿统计
/help - 显示此帮助信息

🚫 <b>重要说明：</b>
• <b>只接收私聊投稿</b>，群组中无法投稿
• 请在与机器人的私聊中发送内容

📝 <b>支持的投稿类型：</b>
• 文字消息：直接发送文字内容
• 图片：发送图片，可带说明文字
• 视频：发送视频，可带说明文字
• 文档：发送文档文件
• 音频：发送音频文件
• 动图/贴纸：发送动图或贴纸
• 位置信息：发送位置
• 联系人：发送联系人信息

✨ <b>投稿流程：</b>
1. 在私聊中发送内容
2. 内容自动进入审核队列
3. 管理员审核后发布到频道

💡 <b>提高通过率的技巧：</b>
• 保持内容质量和原创性
• 确保内容符合社区规范
• 添加适当的说明文字

如有问题，请联系管理员。
        """
        
        await update.message.reply_text(
            help_text,
            parse_mode=ParseMode.HTML
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
✅ <b>投稿提交成功！</b>

📄 投稿ID：{submission_id}
📝 类型：文字
⏳ 状态：待审核

您的投稿已进入审核队列，请耐心等待管理员审核。
        """
        
        await update.message.reply_text(
            success_text,
            parse_mode=ParseMode.HTML
        )
        
        # 发送到审核群
        await self.notification_service.send_submission_to_review_group(submission_id)
        
        logger.info(f"用户 {user.id} \({user.username}) 提交了文字投稿 #{submission_id}")
    
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
✅ <b>投稿提交成功！</b>

📄 投稿ID：{submission_id}
🖼️ 类型：图片
📝 说明：{caption[:50] + "..." if len(caption) > 50 else caption}
⏳ 状态：待审核

您的投稿已进入审核队列，请耐心等待管理员审核。
        """
        
        await update.message.reply_text(
            success_text,
            parse_mode=ParseMode.HTML
        )
        
        # 发送到审核群
        await self.notification_service.send_submission_to_review_group(submission_id)
        
        logger.info(f"用户 {user.id} \({user.username}) 提交了图片投稿 #{submission_id}")
    
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
✅ <b>投稿提交成功！</b>

📄 投稿ID：{submission_id}
🎥 类型：视频
📝 说明：{caption[:50] + "..." if len(caption) > 50 else caption}
⏳ 状态：待审核

您的投稿已进入审核队列，请耐心等待管理员审核。
        """
        
        await update.message.reply_text(
            success_text,
            parse_mode=ParseMode.HTML
        )
        
        # 发送到审核群
        await self.notification_service.send_submission_to_review_group(submission_id)
        
        logger.info(f"用户 {user.id} \({user.username}) 提交了视频投稿 #{submission_id}")
    
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
✅ <b>投稿提交成功！</b>

📄 投稿ID：{submission_id}
📎 类型：文档
📝 文件名：{document.file_name or "未知"}
📝 说明：{caption[:50] + "..." if len(caption) > 50 else caption}
⏳ 状态：待审核

您的投稿已进入审核队列，请耐心等待管理员审核。
        """
        
        await update.message.reply_text(
            success_text,
            parse_mode=ParseMode.HTML
        )
        
        # 发送到审核群
        await self.notification_service.send_submission_to_review_group(submission_id)
        
        logger.info(f"用户 {user.id} \({user.username}) 提交了文档投稿 #{submission_id}")
    
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
✅ <b>投稿提交成功！</b>

📄 投稿ID：{submission_id}
🎵 类型：{"语音" if content_type == 'voice' else "音频"}
📝 说明：{caption[:50] + "..." if len(caption) > 50 else caption}
⏳ 状态：待审核

您的投稿已进入审核队列，请耐心等待管理员审核。
        """
        
        await update.message.reply_text(
            success_text,
            parse_mode=ParseMode.HTML
        )
        
        # 发送到审核群
        await self.notification_service.send_submission_to_review_group(submission_id)
        
        logger.info(f"用户 {user.id} \({user.username}) 提交了{content_type}投稿 #{submission_id}")
    
    async def handle_video_note_submission(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理视频消息投稿（圆形视频）"""
        user = update.effective_user
        
        if self.db.is_user_banned(user.id):
            await update.message.reply_text("❌ 您已被封禁，无法投稿。")
            return
        
        video_note = update.message.video_note
        
        submission_id = self.db.add_submission(
            user_id=user.id,
            username=user.username or user.first_name,
            content_type='video_note',
            media_file_id=video_note.file_id
        )
        
        success_text = f"""
✅ <b>投稿提交成功！</b>

📄 投稿ID：{submission_id}
🎬 类型：视频消息
⏳ 状态：待审核

您的投稿已进入审核队列，请耐心等待管理员审核。
        """
        
        await update.message.reply_text(success_text, parse_mode=ParseMode.HTML)
        await self.notification_service.send_submission_to_review_group(submission_id)
        logger.info(f"用户 {user.id} \({user.username}) 提交了视频消息投稿 #{submission_id}")
    
    async def handle_voice_submission(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理语音投稿"""
        user = update.effective_user
        
        if self.db.is_user_banned(user.id):
            await update.message.reply_text("❌ 您已被封禁，无法投稿。")
            return
        
        voice = update.message.voice
        
        submission_id = self.db.add_submission(
            user_id=user.id,
            username=user.username or user.first_name,
            content_type='voice',
            media_file_id=voice.file_id
        )
        
        success_text = f"""
✅ <b>投稿提交成功！</b>

📄 投稿ID：{submission_id}
🎤 类型：语音
⏳ 状态：待审核

您的投稿已进入审核队列，请耐心等待管理员审核。
        """
        
        await update.message.reply_text(success_text, parse_mode=ParseMode.HTML)
        await self.notification_service.send_submission_to_review_group(submission_id)
        logger.info(f"用户 {user.id} \({user.username}) 提交了语音投稿 #{submission_id}")
    
    async def handle_sticker_submission(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理贴纸投稿"""
        user = update.effective_user
        
        if self.db.is_user_banned(user.id):
            await update.message.reply_text("❌ 您已被封禁，无法投稿。")
            return
        
        sticker = update.message.sticker
        
        submission_id = self.db.add_submission(
            user_id=user.id,
            username=user.username or user.first_name,
            content_type='sticker',
            media_file_id=sticker.file_id
        )
        
        success_text = f"""
✅ <b>投稿提交成功！</b>

📄 投稿ID：{submission_id}
😀 类型：贴纸
⏳ 状态：待审核

您的投稿已进入审核队列，请耐心等待管理员审核。
        """
        
        await update.message.reply_text(success_text, parse_mode=ParseMode.HTML)
        await self.notification_service.send_submission_to_review_group(submission_id)
        logger.info(f"用户 {user.id} \({user.username}) 提交了贴纸投稿 #{submission_id}")
    
    async def handle_animation_submission(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理动图投稿（GIF）"""
        user = update.effective_user
        
        if self.db.is_user_banned(user.id):
            await update.message.reply_text("❌ 您已被封禁，无法投稿。")
            return
        
        animation = update.message.animation
        caption = update.message.caption or ""
        
        submission_id = self.db.add_submission(
            user_id=user.id,
            username=user.username or user.first_name,
            content_type='animation',
            media_file_id=animation.file_id,
            caption=caption
        )
        
        success_text = f"""
✅ <b>投稿提交成功！</b>

📄 投稿ID：{submission_id}
🎭 类型：动图
📝 说明：{caption[:50] + "..." if len(caption) > 50 else caption}
⏳ 状态：待审核

您的投稿已进入审核队列，请耐心等待管理员审核。
        """
        
        await update.message.reply_text(success_text, parse_mode=ParseMode.HTML)
        await self.notification_service.send_submission_to_review_group(submission_id)
        logger.info(f"用户 {user.id} \({user.username}) 提交了动图投稿 #{submission_id}")
    
    async def handle_location_submission(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理位置投稿"""
        user = update.effective_user
        
        if self.db.is_user_banned(user.id):
            await update.message.reply_text("❌ 您已被封禁，无法投稿。")
            return
        
        location = update.message.location
        location_text = f"纬度: {location.latitude}, 经度: {location.longitude}"
        if location.live_period:
            location_text += f", 实时位置: {location.live_period}秒"
        
        submission_id = self.db.add_submission(
            user_id=user.id,
            username=user.username or user.first_name,
            content_type='location',
            content=location_text
        )
        
        success_text = f"""
✅ <b>投稿提交成功！</b>

📄 投稿ID：{submission_id}
📍 类型：位置信息
📝 位置：{location_text}
⏳ 状态：待审核

您的投稿已进入审核队列，请耐心等待管理员审核。
        """
        
        await update.message.reply_text(success_text, parse_mode=ParseMode.HTML)
        await self.notification_service.send_submission_to_review_group(submission_id)
        logger.info(f"用户 {user.id} \({user.username}) 提交了位置投稿 #{submission_id}")
    
    async def handle_contact_submission(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理联系人投稿"""
        user = update.effective_user
        
        if self.db.is_user_banned(user.id):
            await update.message.reply_text("❌ 您已被封禁，无法投稿。")
            return
        
        contact = update.message.contact
        contact_text = f"姓名: {contact.first_name}"
        if contact.last_name:
            contact_text += f" {contact.last_name}"
        if contact.phone_number:
            contact_text += f", 电话: {contact.phone_number}"
        if contact.user_id:
            contact_text += f", 用户ID: {contact.user_id}"
        
        submission_id = self.db.add_submission(
            user_id=user.id,
            username=user.username or user.first_name,
            content_type='contact',
            content=contact_text
        )
        
        success_text = f"""
✅ <b>投稿提交成功！</b>

📄 投稿ID：{submission_id}
👤 类型：联系人
📝 信息：{contact_text}
⏳ 状态：待审核

您的投稿已进入审核队列，请耐心等待管理员审核。
        """
        
        await update.message.reply_text(success_text, parse_mode=ParseMode.HTML)
        await self.notification_service.send_submission_to_review_group(submission_id)
        logger.info(f"用户 {user.id} \({user.username}) 提交了联系人投稿 #{submission_id}")
    

    def run(self):
        """启动机器人"""
        # 创建应用
        self.app = Application.builder().token(self.config.get_submission_bot_token\()).build()
        
        # 添加处理器 - 只在私聊中响应命令
        self.app.add_handler(CommandHandler\("start", self.start_command, filters=filters.ChatType.PRIVATE))
        self.app.add_handler(CommandHandler\("status", self.status_command, filters=filters.ChatType.PRIVATE))
        self.app.add_handler(CommandHandler\("help", self.help_command, filters=filters.ChatType.PRIVATE))
        
        # 消息处理器 - 只接收私聊消息
        self.app.add_handler(MessageHandler\(filters.TEXT & ~filters.COMMAND & filters.ChatType.PRIVATE, self.handle_text_submission))
        self.app.add_handler(MessageHandler\(filters.PHOTO & filters.ChatType.PRIVATE, self.handle_photo_submission))
        self.app.add_handler(MessageHandler\(filters.VIDEO & filters.ChatType.PRIVATE, self.handle_video_submission))
        self.app.add_handler(MessageHandler\(filters.VIDEO_NOTE & filters.ChatType.PRIVATE, self.handle_video_note_submission))
        self.app.add_handler(MessageHandler\(filters.Document.ALL & filters.ChatType.PRIVATE, self.handle_document_submission))
        self.app.add_handler(MessageHandler\(filters.AUDIO & filters.ChatType.PRIVATE, self.handle_audio_submission))
        self.app.add_handler(MessageHandler\(filters.VOICE & filters.ChatType.PRIVATE, self.handle_voice_submission))
        self.app.add_handler(MessageHandler\(filters.Sticker.ALL & filters.ChatType.PRIVATE, self.handle_sticker_submission))
        self.app.add_handler(MessageHandler\(filters.ANIMATION & filters.ChatType.PRIVATE, self.handle_animation_submission))
        self.app.add_handler(MessageHandler\(filters.LOCATION & filters.ChatType.PRIVATE, self.handle_location_submission))
        self.app.add_handler(MessageHandler\(filters.CONTACT & filters.ChatType.PRIVATE, self.handle_contact_submission))
        
        logger.info("投稿机器人启动中...")
        
        # 启动机器人
        self.app.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    bot = SubmissionBot()
    bot.run()