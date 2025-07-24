#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import subprocess
import os
import signal
import psutil
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from telegram.constants import ParseMode
from config_manager import ConfigManager

# 配置日志
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler('control_bot.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ControlBot:
    def __init__(self):
        self.config = ConfigManager()
        self.app = None
        self.bot_processes = {
            'submission': None,
            'publish': None
        }
        self.bot_pids = {}
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理 /start 命令"""
        user_id = update.effective_user.id
        
        if not self.config.is_admin(user_id):
            await update.message.reply_text("❌ 您没有权限使用此机器人。")
            return
        
        welcome_text = """
🎛️ **机器人控制面板**

欢迎使用控制机器人！您可以管理投稿机器人和发布机器人。

📋 **可用命令：**
/status - 查看机器人状态
/start_bots - 启动所有机器人
/stop_bots - 停止所有机器人
/restart_bots - 重启所有机器人
/logs - 查看日志
/system - 系统信息
/help - 显示帮助信息

🎮 **快捷控制：**
使用下方按钮进行快速操作
        """
        
        keyboard = [
            [
                InlineKeyboardButton("📊 状态", callback_data="show_status"),
                InlineKeyboardButton("🚀 启动", callback_data="start_all")
            ],
            [
                InlineKeyboardButton("🛑 停止", callback_data="stop_all"),
                InlineKeyboardButton("🔄 重启", callback_data="restart_all")
            ],
            [
                InlineKeyboardButton("📋 日志", callback_data="show_logs"),
                InlineKeyboardButton("💻 系统", callback_data="system_info")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            welcome_text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=reply_markup
        )
    
    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """查看机器人状态"""
        user_id = update.effective_user.id
        
        if not self.config.is_admin(user_id):
            await update.message.reply_text("❌ 您没有权限执行此操作。")
            return
        
        await self.show_bot_status(update.message)
    
    async def show_bot_status(self, message):
        """显示机器人状态"""
        submission_status = self.check_bot_status('submission_bot.py')
        publish_status = self.check_bot_status('publish_bot.py')
        
        status_text = f"""
📊 **机器人状态监控**

🎯 **投稿机器人：** {'🟢 运行中' if submission_status['running'] else '🔴 已停止'}
{'📍 PID: ' + str(submission_status['pid']) if submission_status['pid'] else ''}
{'💾 内存: ' + submission_status['memory'] if submission_status['memory'] else ''}
{'🔄 启动时间: ' + submission_status['start_time'] if submission_status['start_time'] else ''}

📢 **发布机器人：** {'🟢 运行中' if publish_status['running'] else '🔴 已停止'}
{'📍 PID: ' + str(publish_status['pid']) if publish_status['pid'] else ''}
{'💾 内存: ' + publish_status['memory'] if publish_status['memory'] else ''}
{'🔄 启动时间: ' + publish_status['start_time'] if publish_status['start_time'] else ''}

⏰ 更新时间：{self.get_current_time()}
        """
        
        keyboard = [
            [
                InlineKeyboardButton("🔄 刷新", callback_data="show_status"),
                InlineKeyboardButton("📋 详细日志", callback_data="show_logs")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await message.reply_text(
            status_text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=reply_markup
        )
    
    def check_bot_status(self, bot_filename):
        """检查机器人状态"""
        status = {
            'running': False,
            'pid': None,
            'memory': None,
            'start_time': None
        }
        
        try:
            # 查找进程
            for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'memory_info', 'create_time']):
                try:
                    cmdline = ' '.join(proc.info['cmdline']) if proc.info['cmdline'] else ''
                    if bot_filename in cmdline and 'python' in cmdline:
                        status['running'] = True
                        status['pid'] = proc.info['pid']
                        
                        # 获取内存使用情况
                        memory_mb = proc.info['memory_info'].rss / 1024 / 1024
                        status['memory'] = f"{memory_mb:.1f}MB"
                        
                        # 获取启动时间
                        import datetime
                        start_time = datetime.datetime.fromtimestamp(proc.info['create_time'])
                        status['start_time'] = start_time.strftime("%H:%M:%S")
                        break
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue
        except Exception as e:
            logger.error(f"检查进程状态失败: {e}")
        
        return status
    
    async def start_bots_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """启动所有机器人"""
        user_id = update.effective_user.id
        
        if not self.config.is_admin(user_id):
            await update.message.reply_text("❌ 您没有权限执行此操作。")
            return
        
        await self.start_all_bots(update.message)
    
    async def start_all_bots(self, message):
        """启动所有机器人"""
        await message.reply_text("🚀 正在启动机器人...")
        
        results = []
        
        # 启动投稿机器人
        submission_result = await self.start_bot('submission', 'submission_bot.py')
        results.append(f"🎯 投稿机器人: {'✅ 启动成功' if submission_result else '❌ 启动失败'}")
        
        # 启动发布机器人
        publish_result = await self.start_bot('publish', 'publish_bot.py')
        results.append(f"📢 发布机器人: {'✅ 启动成功' if publish_result else '❌ 启动失败'}")
        
        result_text = "🚀 **启动结果**\n\n" + "\n".join(results)
        
        await message.reply_text(result_text, parse_mode=ParseMode.MARKDOWN)
    
    async def start_bot(self, bot_name, bot_file):
        """启动单个机器人"""
        try:
            # 检查是否已经运行
            if self.check_bot_status(bot_file)['running']:
                logger.info(f"{bot_name} 机器人已经在运行")
                return True
            
            # 启动机器人进程
            process = subprocess.Popen(
                ['python3', bot_file],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                preexec_fn=os.setsid  # 创建新的进程组
            )
            
            self.bot_processes[bot_name] = process
            self.bot_pids[bot_name] = process.pid
            
            # 等待一下检查是否成功启动
            await asyncio.sleep(2)
            
            if process.poll() is None:  # 进程还在运行
                logger.info(f"{bot_name} 机器人启动成功，PID: {process.pid}")
                return True
            else:
                logger.error(f"{bot_name} 机器人启动失败")
                return False
                
        except Exception as e:
            logger.error(f"启动 {bot_name} 机器人失败: {e}")
            return False
    
    async def stop_bots_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """停止所有机器人"""
        user_id = update.effective_user.id
        
        if not self.config.is_admin(user_id):
            await update.message.reply_text("❌ 您没有权限执行此操作。")
            return
        
        await self.stop_all_bots(update.message)
    
    async def stop_all_bots(self, message):
        """停止所有机器人"""
        await message.reply_text("🛑 正在停止机器人...")
        
        results = []
        
        # 停止投稿机器人
        submission_result = self.stop_bot('submission', 'submission_bot.py')
        results.append(f"🎯 投稿机器人: {'✅ 停止成功' if submission_result else '❌ 停止失败'}")
        
        # 停止发布机器人
        publish_result = self.stop_bot('publish', 'publish_bot.py')
        results.append(f"📢 发布机器人: {'✅ 停止成功' if publish_result else '❌ 停止失败'}")
        
        result_text = "🛑 **停止结果**\n\n" + "\n".join(results)
        
        await message.reply_text(result_text, parse_mode=ParseMode.MARKDOWN)
    
    def stop_bot(self, bot_name, bot_file):
        """停止单个机器人"""
        try:
            stopped = False
            
            # 首先尝试停止我们启动的进程
            if bot_name in self.bot_processes and self.bot_processes[bot_name]:
                try:
                    # 发送SIGTERM信号
                    os.killpg(os.getpgid(self.bot_processes[bot_name].pid), signal.SIGTERM)
                    self.bot_processes[bot_name].wait(timeout=5)
                    stopped = True
                    logger.info(f"通过进程组停止了 {bot_name} 机器人")
                except (subprocess.TimeoutExpired, ProcessLookupError):
                    # 如果SIGTERM不行，使用SIGKILL
                    try:
                        os.killpg(os.getpgid(self.bot_processes[bot_name].pid), signal.SIGKILL)
                        stopped = True
                        logger.info(f"强制停止了 {bot_name} 机器人")
                    except ProcessLookupError:
                        pass
                finally:
                    self.bot_processes[bot_name] = None
            
            # 如果上面没有成功，尝试通过进程名查找并停止
            if not stopped:
                for proc in psutil.process_iter(['pid', 'cmdline']):
                    try:
                        cmdline = ' '.join(proc.info['cmdline']) if proc.info['cmdline'] else ''
                        if bot_file in cmdline and 'python' in cmdline:
                            proc.terminate()
                            proc.wait(timeout=5)
                            stopped = True
                            logger.info(f"通过进程查找停止了 {bot_name} 机器人")
                            break
                    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.TimeoutExpired):
                        continue
            
            return stopped
            
        except Exception as e:
            logger.error(f"停止 {bot_name} 机器人失败: {e}")
            return False
    
    async def restart_bots_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """重启所有机器人"""
        user_id = update.effective_user.id
        
        if not self.config.is_admin(user_id):
            await update.message.reply_text("❌ 您没有权限执行此操作。")
            return
        
        await update.message.reply_text("🔄 正在重启机器人...")
        
        # 先停止所有机器人
        await self.stop_all_bots(update.message)
        
        # 等待一下
        await asyncio.sleep(3)
        
        # 再启动所有机器人
        await self.start_all_bots(update.message)
    
    async def logs_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """查看日志"""
        user_id = update.effective_user.id
        
        if not self.config.is_admin(user_id):
            await update.message.reply_text("❌ 您没有权限执行此操作。")
            return
        
        await self.show_logs(update.message)
    
    async def show_logs(self, message):
        """显示日志"""
        log_files = [
            ('submission_bot.log', '🎯 投稿机器人'),
            ('publish_bot.log', '📢 发布机器人'),
            ('control_bot.log', '🎛️ 控制机器人')
        ]
        
        logs_text = "📋 **最近日志记录**\n\n"
        
        for log_file, bot_name in log_files:
            try:
                if os.path.exists(log_file):
                    with open(log_file, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                        recent_lines = lines[-5:] if len(lines) >= 5 else lines
                        
                    logs_text += f"**{bot_name}:**\n"
                    for line in recent_lines:
                        if line.strip():
                            logs_text += f"`{line.strip()[:100]}...`\n"
                    logs_text += "\n"
                else:
                    logs_text += f"**{bot_name}:** 日志文件不存在\n\n"
            except Exception as e:
                logs_text += f"**{bot_name}:** 读取日志失败 - {e}\n\n"
        
        if len(logs_text) > 4096:  # Telegram消息长度限制
            logs_text = logs_text[:4000] + "...\n\n日志过长，已截断"
        
        await message.reply_text(logs_text, parse_mode=ParseMode.MARKDOWN)
    
    async def system_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """系统信息"""
        user_id = update.effective_user.id
        
        if not self.config.is_admin(user_id):
            await update.message.reply_text("❌ 您没有权限执行此操作。")
            return
        
        await self.show_system_info(update.message)
    
    async def show_system_info(self, message):
        """显示系统信息"""
        try:
            # 获取系统信息
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # 获取系统负载
            load_avg = os.getloadavg()
            
            system_text = f"""
💻 **系统状态监控**

🖥️ **CPU使用率：** {cpu_percent:.1f}%
📊 **系统负载：** {load_avg[0]:.2f}, {load_avg[1]:.2f}, {load_avg[2]:.2f}

💾 **内存使用：**
• 总计: {memory.total / 1024 / 1024 / 1024:.1f}GB
• 已用: {memory.used / 1024 / 1024 / 1024:.1f}GB ({memory.percent:.1f}%)
• 可用: {memory.available / 1024 / 1024 / 1024:.1f}GB

💿 **磁盘使用：**
• 总计: {disk.total / 1024 / 1024 / 1024:.1f}GB
• 已用: {disk.used / 1024 / 1024 / 1024:.1f}GB ({disk.used / disk.total * 100:.1f}%)
• 可用: {disk.free / 1024 / 1024 / 1024:.1f}GB

⏰ 更新时间：{self.get_current_time()}
            """
            
            await message.reply_text(system_text, parse_mode=ParseMode.MARKDOWN)
            
        except Exception as e:
            await message.reply_text(f"❌ 获取系统信息失败: {e}")
    
    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理回调按钮"""
        query = update.callback_query
        user_id = update.effective_user.id
        
        if not self.config.is_admin(user_id):
            await query.answer("❌ 您没有权限执行此操作。")
            return
        
        await query.answer()
        data = query.data
        
        if data == "show_status":
            await self.show_bot_status(query.message)
        elif data == "start_all":
            await self.start_all_bots(query.message)
        elif data == "stop_all":
            await self.stop_all_bots(query.message)
        elif data == "restart_all":
            await query.message.reply_text("🔄 正在重启机器人...")
            await self.stop_all_bots(query.message)
            await asyncio.sleep(3)
            await self.start_all_bots(query.message)
        elif data == "show_logs":
            await self.show_logs(query.message)
        elif data == "system_info":
            await self.show_system_info(query.message)
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """帮助命令"""
        user_id = update.effective_user.id
        
        if not self.config.is_admin(user_id):
            await update.message.reply_text("❌ 您没有权限使用此机器人。")
            return
        
        help_text = """
🎛️ **控制机器人帮助**

📋 **命令列表：**
/start - 显示控制面板
/status - 查看机器人状态
/start_bots - 启动所有机器人
/stop_bots - 停止所有机器人
/restart_bots - 重启所有机器人
/logs - 查看日志文件
/system - 系统状态监控
/help - 显示此帮助

🎮 **使用说明：**
• 使用控制面板可以快速管理机器人
• 所有操作都会记录日志
• 支持查看系统资源使用情况
• 仅管理员可以使用此机器人

⚠️ **注意事项：**
• 重启操作可能需要几秒钟时间
• 确保配置文件正确后再启动机器人
• 定期检查日志以确保正常运行

如有问题，请联系系统管理员。
        """
        
        await update.message.reply_text(
            help_text,
            parse_mode=ParseMode.MARKDOWN
        )
    
    def get_current_time(self):
        """获取当前时间字符串"""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    def run(self):
        """启动机器人"""
        # 创建应用
        self.app = Application.builder().token(self.config.get_admin_bot_token()).build()
        
        # 添加处理器
        self.app.add_handler(CommandHandler("start", self.start_command))
        self.app.add_handler(CommandHandler("status", self.status_command))
        self.app.add_handler(CommandHandler("start_bots", self.start_bots_command))
        self.app.add_handler(CommandHandler("stop_bots", self.stop_bots_command))
        self.app.add_handler(CommandHandler("restart_bots", self.restart_bots_command))
        self.app.add_handler(CommandHandler("logs", self.logs_command))
        self.app.add_handler(CommandHandler("system", self.system_command))
        self.app.add_handler(CommandHandler("help", self.help_command))
        
        # 回调处理器
        self.app.add_handler(CallbackQueryHandler(self.handle_callback))
        
        logger.info("控制机器人启动中...")
        
        # 启动机器人
        self.app.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    bot = ControlBot()
    bot.run()