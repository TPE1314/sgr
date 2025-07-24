#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, Bot
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from telegram.constants import ParseMode
from database import DatabaseManager
from config_manager import ConfigManager

# 配置日志
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler('publish_bot.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class PublishBot:
    def __init__(self):
        self.config = ConfigManager()
        self.db = DatabaseManager(self.config.get_db_file())
        self.app = None
        self.publisher_bot = None  # 用于发布到频道的独立bot实例
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理 /start 命令"""
        user_id = update.effective_user.id
        
        if not self.config.is_admin(user_id):
            await update.message.reply_text("❌ 您没有权限使用此机器人。")
            return
        
        welcome_text = """
🤖 **发布机器人管理界面**

欢迎使用发布机器人！您可以审核投稿并管理发布。

📋 **可用命令：**
/pending - 查看待审核投稿
/stats - 查看统计信息
/ban - 封禁用户
/unban - 解封用户
/help - 显示帮助信息

开始管理投稿吧！
        """
        
        await update.message.reply_text(
            welcome_text,
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def pending_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """查看待审核投稿"""
        user_id = update.effective_user.id
        
        if not self.config.is_admin(user_id):
            await update.message.reply_text("❌ 您没有权限执行此操作。")
            return
        
        pending_submissions = self.db.get_pending_submissions()
        
        if not pending_submissions:
            await update.message.reply_text("✅ 暂无待审核投稿。")
            return
        
        # 发送第一个待审核投稿
        await self.send_submission_for_review(update, pending_submissions[0])
    
    async def send_submission_for_review(self, update, submission):
        """发送投稿供审核"""
        user_info = f"👤 投稿用户：{submission['username']} (ID: {submission['user_id']})"
        time_info = f"⏰ 投稿时间：{submission['submit_time']}"
        type_info = f"📝 内容类型：{submission['content_type']}"
        
        header_text = f"""
📋 **投稿审核 #{submission['id']}**

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
                InlineKeyboardButton("⏭️ 下一个", callback_data="next_submission"),
                InlineKeyboardButton("📊 统计", callback_data="show_stats")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # 根据内容类型发送对应的消息
        if submission['content_type'] == 'text':
            full_text = header_text + f"\n📄 **内容：**\n{submission['content']}"
            await update.effective_chat.send_message(
                text=full_text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=reply_markup
            )
        elif submission['content_type'] == 'photo':
            caption_text = header_text
            if submission['caption']:
                caption_text += f"\n📝 **图片说明：**\n{submission['caption']}"
            
            await update.effective_chat.send_photo(
                photo=submission['media_file_id'],
                caption=caption_text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=reply_markup
            )
        elif submission['content_type'] == 'video':
            caption_text = header_text
            if submission['caption']:
                caption_text += f"\n📝 **视频说明：**\n{submission['caption']}"
            
            await update.effective_chat.send_video(
                video=submission['media_file_id'],
                caption=caption_text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=reply_markup
            )
        elif submission['content_type'] == 'document':
            caption_text = header_text
            if submission['caption']:
                caption_text += f"\n📝 **文档说明：**\n{submission['caption']}"
            
            await update.effective_chat.send_document(
                document=submission['media_file_id'],
                caption=caption_text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=reply_markup
            )
        elif submission['content_type'] in ['audio', 'voice']:
            caption_text = header_text
            if submission['caption']:
                caption_text += f"\n📝 **音频说明：**\n{submission['caption']}"
            
            if submission['content_type'] == 'voice':
                await update.effective_chat.send_voice(
                    voice=submission['media_file_id'],
                    caption=caption_text,
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=reply_markup
                )
            else:
                await update.effective_chat.send_audio(
                    audio=submission['media_file_id'],
                    caption=caption_text,
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=reply_markup
                )
    
    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理回调按钮"""
        query = update.callback_query
        user_id = update.effective_user.id
        user_name = update.effective_user.first_name or update.effective_user.username or "管理员"
        
        if not self.config.is_admin(user_id):
            await query.answer("❌ 您没有权限执行此操作。")
            return
        
        await query.answer()
        data = query.data
        
        if data.startswith("approve_"):
            submission_id = int(data.split("_")[1])
            await self.approve_submission_in_group(query, submission_id, user_id, user_name)
        
        elif data.startswith("reject_"):
            submission_id = int(data.split("_")[1])
            await self.reject_submission_in_group(query, submission_id, user_id, user_name)
        
        elif data.startswith("user_stats_"):
            user_target_id = int(data.split("_")[2])
            await self.show_user_stats(query, user_target_id)
        
        elif data.startswith("ban_user_"):
            user_target_id = int(data.split("_")[2])
            await self.ban_user_action(query, user_target_id, user_id)
        
        elif data == "next_submission":
            await self.show_next_submission(query)
        
        elif data == "show_stats":
            await self.show_stats(query)
    
    async def approve_submission(self, query, submission_id, reviewer_id):
        """批准投稿"""
        submission = self.db.get_submission_by_id(submission_id)
        if not submission:
            await query.edit_message_text("❌ 投稿不存在或已被处理。")
            return
        
        if submission['status'] != 'pending':
            await query.edit_message_text(f"❌ 投稿状态已变更：{submission['status']}")
            return
        
        # 批准投稿
        success = self.db.approve_submission(submission_id, reviewer_id)
        if not success:
            await query.edit_message_text("❌ 批准失败，请重试。")
            return
        
        # 发布到频道
        await self.publish_to_channel(submission)
        
        # 标记为已发布
        self.db.mark_published(submission_id)
        
        success_text = f"""
✅ **投稿已批准并发布**

📄 投稿ID：{submission_id}
👤 投稿用户：{submission['username']}
📢 状态：已发布到频道

投稿已成功发布到频道。
        """
        
        await query.edit_message_text(
            success_text,
            parse_mode=ParseMode.MARKDOWN
        )
        
        # 显示下一个待审核投稿
        await asyncio.sleep(1)
        await self.show_next_submission_inline(query)
        
        logger.info(f"管理员 {reviewer_id} 批准了投稿 #{submission_id}")
    
    async def reject_submission(self, query, submission_id, reviewer_id):
        """拒绝投稿"""
        submission = self.db.get_submission_by_id(submission_id)
        if not submission:
            await query.edit_message_text("❌ 投稿不存在或已被处理。")
            return
        
        if submission['status'] != 'pending':
            await query.edit_message_text(f"❌ 投稿状态已变更：{submission['status']}")
            return
        
        # 拒绝投稿
        success = self.db.reject_submission(submission_id, reviewer_id, "管理员拒绝")
        if not success:
            await query.edit_message_text("❌ 拒绝失败，请重试。")
            return
        
        success_text = f"""
❌ **投稿已拒绝**

📄 投稿ID：{submission_id}
👤 投稿用户：{submission['username']}
📢 状态：已拒绝

投稿已被拒绝。
        """
        
        await query.edit_message_text(
            success_text,
            parse_mode=ParseMode.MARKDOWN
        )
        
        # 显示下一个待审核投稿
        await asyncio.sleep(1)
        await self.show_next_submission_inline(query)
        
        logger.info(f"管理员 {reviewer_id} 拒绝了投稿 #{submission_id}")
    
    async def approve_submission_in_group(self, query, submission_id, reviewer_id, reviewer_name):
        """在审核群中批准投稿"""
        submission = self.db.get_submission_by_id(submission_id)
        if not submission:
            await query.edit_message_text("❌ 投稿不存在或已被处理。")
            return
        
        if submission['status'] != 'pending':
            await query.edit_message_text(f"❌ 投稿状态已变更：{submission['status']}")
            return
        
        # 批准投稿
        success = self.db.approve_submission(submission_id, reviewer_id)
        if not success:
            await query.edit_message_text("❌ 批准失败，请重试。")
            return
        
        # 发布到频道
        try:
            await self.publish_to_channel(submission)
            # 标记为已发布
            self.db.mark_published(submission_id)
            
            # 更新消息显示审核结果
            success_text = f"""
✅ **投稿已批准并发布**

📄 投稿ID：{submission_id}
👤 投稿用户：{submission['username']}
👨‍💼 审核员：{reviewer_name}
📢 状态：已发布到频道
⏰ 处理时间：{self.get_current_time()}

投稿已成功发布到频道。
            """
            
            await query.edit_message_text(
                success_text,
                parse_mode=ParseMode.MARKDOWN
            )
            
            logger.info(f"管理员 {reviewer_id} ({reviewer_name}) 在审核群中批准了投稿 #{submission_id}")
            
        except Exception as e:
            logger.error(f"发布投稿 #{submission_id} 失败: {e}")
            await query.edit_message_text(f"❌ 发布失败: {str(e)}")
    
    async def reject_submission_in_group(self, query, submission_id, reviewer_id, reviewer_name):
        """在审核群中拒绝投稿"""
        submission = self.db.get_submission_by_id(submission_id)
        if not submission:
            await query.edit_message_text("❌ 投稿不存在或已被处理。")
            return
        
        if submission['status'] != 'pending':
            await query.edit_message_text(f"❌ 投稿状态已变更：{submission['status']}")
            return
        
        # 拒绝投稿
        success = self.db.reject_submission(submission_id, reviewer_id, "管理员拒绝")
        if not success:
            await query.edit_message_text("❌ 拒绝失败，请重试。")
            return
        
        # 更新消息显示审核结果
        success_text = f"""
❌ **投稿已拒绝**

📄 投稿ID：{submission_id}
👤 投稿用户：{submission['username']}
👨‍💼 审核员：{reviewer_name}
📢 状态：已拒绝
⏰ 处理时间：{self.get_current_time()}

投稿已被拒绝。
        """
        
        await query.edit_message_text(
            success_text,
            parse_mode=ParseMode.MARKDOWN
        )
        
        logger.info(f"管理员 {reviewer_id} ({reviewer_name}) 在审核群中拒绝了投稿 #{submission_id}")
    
    async def show_user_stats(self, query, user_id):
        """显示用户统计信息"""
        stats = self.db.get_user_stats(user_id)
        is_banned = self.db.is_user_banned(user_id)
        
        stats_text = f"""
👤 **用户统计信息**

🆔 用户ID：{user_id}
🚫 状态：{'已封禁' if is_banned else '正常'}

📊 **投稿统计：**
📝 总投稿数：{stats['total']}
⏳ 待审核：{stats['pending']}
✅ 已通过：{stats['approved']}
📢 已发布：{stats['published']}
❌ 已拒绝：{stats['rejected']}

通过率：{(stats['published'] / stats['total'] * 100) if stats['total'] > 0 else 0:.1f}%
        """
        
        await query.message.reply_text(
            stats_text,
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def ban_user_action(self, query, user_target_id, admin_id):
        """封禁用户操作"""
        if self.db.is_user_banned(user_target_id):
            await query.message.reply_text(f"⚠️ 用户 {user_target_id} 已经被封禁。")
            return
        
        success = self.db.ban_user(user_target_id, admin_id)
        if success:
            await query.message.reply_text(f"🚫 用户 {user_target_id} 已被封禁。")
        else:
            await query.message.reply_text(f"❌ 封禁用户 {user_target_id} 失败。")
    
    def get_current_time(self):
        """获取当前时间字符串"""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    async def publish_to_channel(self, submission):
        """发布到频道"""
        if not self.publisher_bot:
            self.publisher_bot = Bot(token=self.config.get_publish_bot_token())
        
        channel_id = self.config.get_channel_id()
        
        try:
            if submission['content_type'] == 'text':
                await self.publisher_bot.send_message(
                    chat_id=channel_id,
                    text=submission['content'],
                    parse_mode=ParseMode.MARKDOWN
                )
            elif submission['content_type'] == 'photo':
                await self.publisher_bot.send_photo(
                    chat_id=channel_id,
                    photo=submission['media_file_id'],
                    caption=submission['caption'],
                    parse_mode=ParseMode.MARKDOWN
                )
            elif submission['content_type'] == 'video':
                await self.publisher_bot.send_video(
                    chat_id=channel_id,
                    video=submission['media_file_id'],
                    caption=submission['caption'],
                    parse_mode=ParseMode.MARKDOWN
                )
            elif submission['content_type'] == 'document':
                await self.publisher_bot.send_document(
                    chat_id=channel_id,
                    document=submission['media_file_id'],
                    caption=submission['caption'],
                    parse_mode=ParseMode.MARKDOWN
                )
            elif submission['content_type'] == 'voice':
                await self.publisher_bot.send_voice(
                    chat_id=channel_id,
                    voice=submission['media_file_id'],
                    caption=submission['caption']
                )
            elif submission['content_type'] == 'audio':
                await self.publisher_bot.send_audio(
                    chat_id=channel_id,
                    audio=submission['media_file_id'],
                    caption=submission['caption']
                )
            
            logger.info(f"投稿 #{submission['id']} 已发布到频道")
            
        except Exception as e:
            logger.error(f"发布投稿 #{submission['id']} 到频道失败: {e}")
            raise e
    
    async def show_next_submission(self, query):
        """显示下一个待审核投稿"""
        pending_submissions = self.db.get_pending_submissions()
        
        if not pending_submissions:
            await query.edit_message_text("✅ 暂无待审核投稿。")
            return
        
        await self.send_submission_for_review(query, pending_submissions[0])
    
    async def show_next_submission_inline(self, query):
        """内联显示下一个待审核投稿"""
        pending_submissions = self.db.get_pending_submissions()
        
        if not pending_submissions:
            await query.message.reply_text("✅ 暂无更多待审核投稿。")
            return
        
        await self.send_submission_for_review(query, pending_submissions[0])
    
    async def show_stats(self, query):
        """显示统计信息"""
        # 这里可以添加统计信息的实现
        stats_text = """
📊 **系统统计**

正在开发中...
        """
        
        await query.message.reply_text(
            stats_text,
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """统计信息命令"""
        user_id = update.effective_user.id
        
        if not self.config.is_admin(user_id):
            await update.message.reply_text("❌ 您没有权限执行此操作。")
            return
        
        # 获取各种统计数据
        import sqlite3
        conn = sqlite3.connect(self.config.get_db_file())
        cursor = conn.cursor()
        
        # 获取投稿统计
        cursor.execute('''
            SELECT 
                COUNT(*) as total,
                COUNT(CASE WHEN status = 'pending' THEN 1 END) as pending,
                COUNT(CASE WHEN status = 'approved' THEN 1 END) as approved,
                COUNT(CASE WHEN status = 'published' THEN 1 END) as published,
                COUNT(CASE WHEN status = 'rejected' THEN 1 END) as rejected
            FROM submissions
        ''')
        
        stats = cursor.fetchone()
        
        # 获取今日投稿数
        cursor.execute('''
            SELECT COUNT(*) FROM submissions 
            WHERE DATE(submit_time) = DATE('now')
        ''')
        today_submissions = cursor.fetchone()[0]
        
        # 获取活跃用户数
        cursor.execute('SELECT COUNT(DISTINCT user_id) FROM submissions')
        unique_users = cursor.fetchone()[0]
        
        conn.close()
        
        stats_text = f"""
📊 **系统统计信息**

📝 **投稿统计：**
• 总投稿数：{stats[0]}
• 待审核：{stats[1]}
• 已批准：{stats[2]}
• 已发布：{stats[3]}
• 已拒绝：{stats[4]}

📅 **今日数据：**
• 今日投稿：{today_submissions}

👥 **用户统计：**
• 投稿用户数：{unique_users}

系统运行正常 ✅
        """
        
        await update.message.reply_text(
            stats_text,
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """帮助命令"""
        user_id = update.effective_user.id
        
        if not self.config.is_admin(user_id):
            await update.message.reply_text("❌ 您没有权限使用此机器人。")
            return
        
        help_text = """
🤖 **发布机器人帮助**

📋 **可用命令：**
/start - 启动机器人
/pending - 查看待审核投稿
/stats - 查看统计信息
/help - 显示此帮助信息

🔧 **审核操作：**
• 使用 /pending 命令查看待审核投稿
• 点击 ✅ 批准按钮批准投稿并自动发布
• 点击 ❌ 拒绝按钮拒绝投稿
• 点击 ⏭️ 下一个按钮查看下一个投稿

📢 **发布机制：**
• 批准的投稿会自动发布到配置的频道
• 发布成功后会标记为已发布状态
• 所有操作都会记录日志

如有问题，请联系系统管理员。
        """
        
        await update.message.reply_text(
            help_text,
            parse_mode=ParseMode.MARKDOWN
        )
    
    def run(self):
        """启动机器人"""
        # 创建应用
        self.app = Application.builder().token(self.config.get_publish_bot_token()).build()
        
        # 添加处理器
        self.app.add_handler(CommandHandler("start", self.start_command))
        self.app.add_handler(CommandHandler("pending", self.pending_command))
        self.app.add_handler(CommandHandler("stats", self.stats_command))
        self.app.add_handler(CommandHandler("help", self.help_command))
        
        # 回调处理器
        self.app.add_handler(CallbackQueryHandler(self.handle_callback))
        
        logger.info("发布机器人启动中...")
        
        # 启动机器人
        self.app.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    bot = PublishBot()
    bot.run()