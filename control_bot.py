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
from hot_update_service import HotUpdateService
from database import DatabaseManager
from update_service import UpdateService

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
        self.db = DatabaseManager(self.config.get_db_file())
        self.hot_update = HotUpdateService()
        self.update_service = UpdateService()
        self.app = None
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理 /start 命令"""
        user_id = update.effective_user.id
        admin_level = self.config.get_admin_level(user_id)
        
        if admin_level == "none":
            await update.message.reply_text("❌ 您没有权限使用此机器人。")
            return
        
        user_name = update.effective_user.first_name or update.effective_user.username
        
        welcome_text = f"""
🎛️ **机器人控制面板**

👋 欢迎 {user_name}！ (权限: {admin_level})

🤖 **机器人管理：**
• 启动/停止/重启机器人
• 热更新配置
• 实时状态监控

👨‍💼 **管理员功能：**
• 添加/移除动态管理员
• 查看操作日志
• 系统资源监控

📋 **快速操作：**
使用下方按钮进行管理
        """
        
        # 根据权限级别显示不同的按钮
        keyboard = [
            [
                InlineKeyboardButton("📊 机器人状态", callback_data="show_status"),
                InlineKeyboardButton("💻 系统信息", callback_data="system_info")
            ],
            [
                InlineKeyboardButton("🚀 启动全部", callback_data="start_all"),
                InlineKeyboardButton("🛑 停止全部", callback_data="stop_all")
            ],
            [
                InlineKeyboardButton("🔄 重启全部", callback_data="restart_all"),
                InlineKeyboardButton("🔥 热更新", callback_data="hot_reload_all")
            ]
        ]
        
        # 超级管理员才能看到管理员管理功能
        if admin_level == "super":
            keyboard.extend([
                [
                    InlineKeyboardButton("👨‍💼 管理员列表", callback_data="admin_list"),
                    InlineKeyboardButton("➕ 添加管理员", callback_data="add_admin")
                ],
                [
                    InlineKeyboardButton("📋 操作日志", callback_data="show_logs"),
                    InlineKeyboardButton("⚙️ 系统配置", callback_data="system_config")
                ]
            ])
        else:
            keyboard.append([
                InlineKeyboardButton("📋 查看日志", callback_data="show_logs")
            ])
        
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
        elif data == "hot_reload_all":
            await self.hot_reload_all_bots(query.message)
        elif data == "admin_list":
            await self.show_admin_list(query.message)
        elif data == "add_admin":
            await self.prompt_add_admin(query.message)
        elif data == "system_config":
            await self.show_system_config(query.message)
        elif data == "one_click_update":
            await self.one_click_update(query.message)
        elif data == "show_backups":
            await self.show_backup_list(query.message)
        elif data == "update_status":
            await self.show_update_status(query.message)
        elif data.startswith("remove_admin_"):
            admin_id = int(data.split("_")[2])
            await self.remove_admin_action(query, admin_id, user_id)
        elif data.startswith("rollback_"):
            backup_name = data.replace("rollback_", "")
            await self.rollback_action(query, backup_name)
        elif data == "confirm_update":
            await self.confirm_update_action(query, user_id)
        elif data == "back_to_main":
            await self.start_command(query, None)
    
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
    
    async def hot_reload_all_bots(self, message):
        """热重载所有机器人"""
        await message.reply_text("🔥 开始热重载所有机器人...")
        
        results = []
        for bot_name in self.hot_update.bot_configs.keys():
            success, msg = await self.hot_update.hot_reload_bot(bot_name)
            status_emoji = "✅" if success else "❌"
            results.append(f"{status_emoji} {self.hot_update.bot_configs[bot_name]['name']}: {msg}")
        
        result_text = "🔥 **热重载结果**\n\n" + "\n".join(results)
        await message.reply_text(result_text, parse_mode=ParseMode.MARKDOWN)
    
    async def show_admin_list(self, message):
        """显示管理员列表"""
        # 获取配置文件中的超级管理员
        super_admins = self.config.get_admin_users()
        
        # 获取动态管理员
        dynamic_admins = self.db.get_dynamic_admins()
        
        admin_text = "👨‍💼 **管理员列表**\n\n"
        
        # 超级管理员
        admin_text += "🔑 **超级管理员 (配置文件):**\n"
        for admin_id in super_admins:
            admin_text += f"• ID: {admin_id} (权限: super)\n"
        
        # 动态管理员
        admin_text += f"\n👥 **动态管理员 ({len(dynamic_admins)} 人):**\n"
        if dynamic_admins:
            for admin in dynamic_admins:
                admin_text += f"• @{admin['username'] or 'N/A'} (ID: {admin['user_id']}, 权限: {admin['permissions']})\n"
                admin_text += f"  添加时间: {admin['added_time']}\n"
        else:
            admin_text += "暂无动态管理员\n"
        
        # 添加管理按钮
        keyboard = []
        if dynamic_admins:
            keyboard.append([InlineKeyboardButton("🗑️ 管理动态管理员", callback_data="manage_dynamic_admins")])
        
        keyboard.extend([
            [
                InlineKeyboardButton("➕ 添加管理员", callback_data="add_admin"),
                InlineKeyboardButton("🔄 刷新列表", callback_data="admin_list")
            ],
            [InlineKeyboardButton("🔙 返回主菜单", callback_data="back_to_main")]
        ])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await message.reply_text(admin_text, parse_mode=ParseMode.MARKDOWN, reply_markup=reply_markup)
    
    async def prompt_add_admin(self, message):
        """提示添加管理员"""
        help_text = """
➕ **添加动态管理员**

请使用以下命令添加管理员：
`/add_admin <用户ID> <权限级别> [用户名]`

**参数说明：**
• 用户ID: 必需，数字格式
• 权限级别: basic 或 advanced
• 用户名: 可选，便于识别

**示例：**
`/add_admin 123456789 basic @username`
`/add_admin 987654321 advanced`

**权限说明：**
• basic: 基础权限，可以查看状态和日志
• advanced: 高级权限，可以管理机器人但不能管理其他管理员
        """
        
        await message.reply_text(help_text, parse_mode=ParseMode.MARKDOWN)
    
    async def show_system_config(self, message):
        """显示系统配置"""
        try:
            # 获取更新状态
            update_status = self.update_service.get_update_status()
            
            config_text = f"""
⚙️ **系统配置信息**

📱 **当前版本:** {update_status.get('current_version', 'unknown')}
🔄 **最后更新:** {update_status.get('last_update', '从未更新')[:19] if update_status.get('last_update') else '从未更新'}

🗂️ **Git状态:**
• Git仓库: {'✅' if update_status.get('is_git_repo') else '❌'}
• 有可用更新: {'✅' if update_status.get('has_updates') else '❌'}
• 落后提交: {update_status.get('git_behind_count', 0)} 个

📦 **备份信息:**
• 备份数量: {update_status.get('backup_count', 0)} 个
• 依赖文件: {'✅' if update_status.get('has_requirements') else '❌'}

🤖 **机器人状态:**
            """
            
            # 获取机器人状态
            bots_status = self.hot_update.get_all_bots_status()
            for bot_name, status in bots_status.items():
                status_emoji = "🟢" if status['running'] else "🔴"
                config_text += f"• {status['display_name']}: {status_emoji}\n"
            
            # 添加操作按钮
            keyboard = [
                [
                    InlineKeyboardButton("🔄 一键更新", callback_data="one_click_update"),
                    InlineKeyboardButton("📦 查看备份", callback_data="show_backups")
                ],
                [
                    InlineKeyboardButton("📊 更新状态", callback_data="update_status"),
                    InlineKeyboardButton("🔙 返回", callback_data="back_to_main")
                ]
            ]
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            await message.reply_text(config_text, parse_mode=ParseMode.MARKDOWN, reply_markup=reply_markup)
            
        except Exception as e:
            await message.reply_text(f"❌ 获取系统配置失败: {e}")
    
    async def one_click_update(self, message):
        """一键更新系统"""
        user_id = message.chat.id
        admin_level = self.config.get_admin_level(user_id)
        
        if admin_level != "super":
            await message.reply_text("❌ 只有超级管理员才能执行系统更新操作。")
            return
        
        # 显示更新确认
        update_status = self.update_service.get_update_status()
        
        confirm_text = f"""
🔄 **系统更新确认**

📱 当前版本: {update_status.get('current_version', 'unknown')}
🔄 是否有更新: {'✅ 是' if update_status.get('has_updates') else '❌ 否'}

⚠️ **更新内容:**
• 📥 从Git拉取最新代码
• 📚 更新Python依赖包
• 🔄 重启所有机器人 (除控制机器人)
• 📦 自动创建备份

**确定要开始更新吗？**
        """
        
        keyboard = [
            [
                InlineKeyboardButton("✅ 确认更新", callback_data="confirm_update"),
                InlineKeyboardButton("❌ 取消", callback_data="system_config")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await message.reply_text(confirm_text, parse_mode=ParseMode.MARKDOWN, reply_markup=reply_markup)
    
    async def show_backup_list(self, message):
        """显示备份列表"""
        backups = self.update_service.get_backup_list()
        
        if not backups:
            await message.reply_text("📦 暂无系统备份")
            return
        
        backup_text = "📦 **系统备份列表**\n\n"
        
        for i, backup in enumerate(backups[:10]):  # 只显示最近10个备份
            backup_text += f"**{i+1}. {backup['name']}**\n"
            backup_text += f"• 时间: {backup['timestamp']}\n"
            backup_text += f"• 版本: {backup.get('version', 'unknown')}\n"
            backup_text += f"• 文件数: {backup['files_count']}\n\n"
        
        if len(backups) > 10:
            backup_text += f"... 还有 {len(backups) - 10} 个备份\n"
        
        # 添加操作按钮
        keyboard = []
        for i, backup in enumerate(backups[:5]):  # 前5个备份添加回滚按钮
            keyboard.append([
                InlineKeyboardButton(
                    f"↩️ 回滚到 {backup['name'][:15]}...", 
                    callback_data=f"rollback_{backup['name']}"
                )
            ])
        
        keyboard.append([
            InlineKeyboardButton("🔄 刷新列表", callback_data="show_backups"),
            InlineKeyboardButton("🔙 返回", callback_data="system_config")
        ])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await message.reply_text(backup_text, parse_mode=ParseMode.MARKDOWN, reply_markup=reply_markup)
    
    async def show_update_status(self, message):
        """显示详细更新状态"""
        update_status = self.update_service.get_update_status()
        
        status_text = f"""
📊 **详细更新状态**

📱 **版本信息:**
• 当前版本: {update_status.get('current_version', 'unknown')}
• 最后更新版本: {update_status.get('last_version', '未知')}
• 最后更新时间: {update_status.get('last_update', '从未更新')[:19] if update_status.get('last_update') else '从未更新'}

🔄 **Git状态:**
• 是否Git仓库: {'✅' if update_status.get('is_git_repo') else '❌'}
• 落后提交数: {update_status.get('git_behind_count', 0)}
• 有可用更新: {'✅' if update_status.get('has_updates') else '❌'}

📦 **系统信息:**
• 备份数量: {update_status.get('backup_count', 0)}
• Requirements文件: {'✅' if update_status.get('has_requirements') else '❌'}
• 更新日志: {'✅' if update_status.get('update_log_exists') else '❌'}

🤖 **机器人状态:**
        """
        
        # 添加机器人状态
        bots_status = self.hot_update.get_all_bots_status()
        for bot_name, status in bots_status.items():
            status_emoji = "🟢" if status['running'] else "🔴"
            status_text += f"• {status['display_name']}: {status_emoji}"
            if status['running']:
                status_text += f" (PID: {status['pid']}, 内存: {status['memory_mb']}MB)"
            status_text += "\n"
        
        keyboard = [
            [
                InlineKeyboardButton("🔄 刷新状态", callback_data="update_status"),
                InlineKeyboardButton("🔙 返回", callback_data="system_config")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await message.reply_text(status_text, parse_mode=ParseMode.MARKDOWN, reply_markup=reply_markup)
    
    async def add_admin_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """添加管理员命令"""
        user_id = update.effective_user.id
        
        if not self.config.is_super_admin(user_id):
            await update.message.reply_text("❌ 只有超级管理员才能添加管理员。")
            return
        
        if len(context.args) < 2:
            await update.message.reply_text(
                "❌ 用法: `/add_admin <用户ID> <权限级别> [用户名]`\n"
                "权限级别: basic, advanced",
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        try:
            target_user_id = int(context.args[0])
            permissions = context.args[1].lower()
            username = context.args[2] if len(context.args) > 2 else None
            
            if permissions not in ['basic', 'advanced']:
                await update.message.reply_text("❌ 权限级别必须是 basic 或 advanced")
                return
            
            # 检查用户是否已经是管理员
            if self.config.is_admin(target_user_id):
                await update.message.reply_text("⚠️ 该用户已经是管理员")
                return
            
            # 添加动态管理员
            success = self.db.add_dynamic_admin(target_user_id, username, permissions, user_id)
            
            if success:
                await update.message.reply_text(
                    f"✅ 成功添加管理员\n"
                    f"用户ID: {target_user_id}\n"
                    f"权限: {permissions}\n"
                    f"用户名: {username or '未知'}"
                )
            else:
                await update.message.reply_text("❌ 添加管理员失败")
                
        except ValueError:
            await update.message.reply_text("❌ 用户ID必须是数字")
        except Exception as e:
            await update.message.reply_text(f"❌ 添加管理员失败: {e}")
    
    async def remove_admin_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """移除管理员命令"""
        user_id = update.effective_user.id
        
        if not self.config.is_super_admin(user_id):
            await update.message.reply_text("❌ 只有超级管理员才能移除管理员。")
            return
        
        if len(context.args) < 1:
            await update.message.reply_text(
                "❌ 用法: `/remove_admin <用户ID>`",
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        try:
            target_user_id = int(context.args[0])
            
            # 检查是否是动态管理员
            if not self.db.is_dynamic_admin(target_user_id):
                await update.message.reply_text("❌ 该用户不是动态管理员")
                return
            
            # 移除动态管理员
            success = self.db.remove_dynamic_admin(target_user_id, user_id)
            
            if success:
                await update.message.reply_text(f"✅ 成功移除管理员 (ID: {target_user_id})")
            else:
                await update.message.reply_text("❌ 移除管理员失败")
                
        except ValueError:
            await update.message.reply_text("❌ 用户ID必须是数字")
        except Exception as e:
            await update.message.reply_text(f"❌ 移除管理员失败: {e}")
    
    async def update_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """系统更新命令"""
        user_id = update.effective_user.id
        
        if not self.config.is_super_admin(user_id):
            await update.message.reply_text("❌ 只有超级管理员才能执行系统更新。")
            return
        
        await update.message.reply_text("🔄 开始系统更新...")
        
        # 执行完整更新
        success, result = await self.update_service.full_update()
        
        if success:
            await update.message.reply_text(f"✅ **系统更新成功**\n\n{result}", parse_mode=ParseMode.MARKDOWN)
        else:
                         await update.message.reply_text(f"❌ **系统更新失败**\n\n{result}", parse_mode=ParseMode.MARKDOWN)
    
    async def confirm_update_action(self, query, user_id):
        """确认更新操作"""
        await query.edit_message_text("🔄 开始系统更新，请稍候...")
        
        # 执行完整更新
        success, result = await self.update_service.full_update()
        
        if success:
            await query.edit_message_text(f"✅ **系统更新成功**\n\n{result}", parse_mode=ParseMode.MARKDOWN)
        else:
            await query.edit_message_text(f"❌ **系统更新失败**\n\n{result}", parse_mode=ParseMode.MARKDOWN)
    
    async def rollback_action(self, query, backup_name):
        """回滚操作"""
        await query.edit_message_text(f"↩️ 开始回滚到备份 {backup_name}...")
        
        success, result = await self.update_service.rollback_to_backup(backup_name)
        
        if success:
            await query.edit_message_text(f"✅ **回滚成功**\n\n{result}", parse_mode=ParseMode.MARKDOWN)
        else:
            await query.edit_message_text(f"❌ **回滚失败**\n\n{result}", parse_mode=ParseMode.MARKDOWN)
    
    async def remove_admin_action(self, query, admin_id, removed_by):
        """移除管理员操作"""
        success = self.db.remove_dynamic_admin(admin_id, removed_by)
        
        if success:
            await query.edit_message_text(f"✅ 已移除管理员 (ID: {admin_id})")
        else:
            await query.edit_message_text(f"❌ 移除管理员失败 (ID: {admin_id})")
    
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
        self.app.add_handler(CommandHandler("add_admin", self.add_admin_command))
        self.app.add_handler(CommandHandler("remove_admin", self.remove_admin_command))
        self.app.add_handler(CommandHandler("update", self.update_command))
        
        # 回调处理器
        self.app.add_handler(CallbackQueryHandler(self.handle_callback))
        
        logger.info("控制机器人启动中...")
        
        # 启动机器人
        self.app.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    bot = ControlBot()
    bot.run()