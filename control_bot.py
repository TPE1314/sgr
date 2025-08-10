#!/usr/bin/env python3
# -<i>- coding: utf-8 -</i>-

import logging
import subprocess
import os
import signal
import psutil
import asyncio
from datetime import datetime
from pathlib import Path
from typing import List, Dict
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters
from telegram.constants import ParseMode
from config_manager import ConfigManager
from hot_update_service import HotUpdateService
from database import DatabaseManager
from update_service import UpdateService
from file_update_service import FileUpdateService
from advertisement_manager import (
    get_ad_manager, initialize_ad_manager, Advertisement, AdType, 
    AdPosition, AdStatus, AdDisplayConfig
)

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
        self.file_update = FileUpdateService()
        
        # 初始化广告管理器
        try:
            self.ad_manager = initialize_ad_manager(self.config.get_db_file())
        except:
            self.ad_manager = get_ad_manager()
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
🎛️ <b>机器人控制面板</b>

👋 欢迎 {user_name}！ (权限: {admin_level})

🤖 <b>机器人管理：</b>
• 启动/停止/重启机器人
• 热更新配置
• 实时状态监控

👨‍💼 <b>管理员功能：</b>
• 添加/移除动态管理员
• 查看操作日志
• 系统资源监控

📋 <b>快速操作：</b>
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
                ],
                [
                    InlineKeyboardButton("📁 文件更新历史", callback_data="file_update_history"),
                    InlineKeyboardButton("🔄 一键更新", callback_data="one_click_update")
                ],
                [
                    InlineKeyboardButton("📢 广告管理", callback_data="ad_management"),
                    InlineKeyboardButton("📊 广告统计", callback_data="ad_statistics")
                ]
            ])
        else:
            keyboard.append([
                InlineKeyboardButton("📋 查看日志", callback_data="show_logs")
            ])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            welcome_text,
            parse_mode=ParseMode.HTML,
            reply_markup=reply_markup
        )
    
    async def status_command(self, update: Update, context:ContextTypes.DEFAULT_TYPE):
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
📊 <b>机器人状态监控</b>

🎯 <b>投稿机器人：</b> {'🟢 运行中' if submission_status['running'] else '🔴 已停止'}
{'📍 PID: ' + str(submission_status['pid']) if submission_status['pid'] else ''}
{'💾 内存: ' + submission_status['memory'] if submission_status['memory'] else ''}
{'🔄 启动时间: ' + submission_status['start_time'] if submission_status['start_time'] else ''}

📢 <b>发布机器人：</b> {'🟢 运行中' if publish_status['running'] else '🔴 已停止'}
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
            parse_mode=ParseMode.HTML,
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
        
        result_text = "🚀 <b>启动结果</b>\n\n" + "\n".join(results)
        
        await message.reply_text(result_text, parse_mode=ParseMode.HTML)
    
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
        
        result_text = "🛑 <b>停止结果</b>\n\n" + "\n".join(results)
        
        await message.reply_text(result_text, parse_mode=ParseMode.HTML)
    
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
        
        logs_text = "📋 <b>最近日志记录</b>\n\n"
        
        for log_file, bot_name in log_files:
            try:
                if os.path.exists(log_file):
                    with open(log_file, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                        recent_lines = lines[-5:] if len(lines) >= 5 else lines
                        
                    logs_text += f"<b>{bot_name}:</b>\n"
                    for line in recent_lines:
                        if line.strip():
                            logs_text += f"<code>{line.strip()[:100]}...</code>\n"
                    logs_text += "\n"
                else:
                    logs_text += f"<b>{bot_name}:</b> 日志文件不存在\n\n"
            except Exception as e:
                logs_text += f"<b>{bot_name}:</b> 读取日志失败 - {e}\n\n"
        
        if len(logs_text) > 4096:  # Telegram消息长度限制
            logs_text = logs_text[:4000] + "...\n\n日志过长，已截断"
        
        await message.reply_text(logs_text, parse_mode=ParseMode.HTML)
    
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
💻 <b>系统状态监控</b>

🖥️ <b>CPU使用率：</b> {cpu_percent:.1f}%
📊 <b>系统负载：</b> {load_avg[0]:.2f}, {load_avg[1]:.2f}, {load_avg[2]:.2f}

💾 <b>内存使用：</b>
• 总计: {memory.total / 1024 / 1024 / 1024:.1f}GB
• 已用: {memory.used / 1024 / 1024 / 1024:.1f}GB ({memory.percent:.1f}%)
• 可用: {memory.available / 1024 / 1024 / 1024:.1f}GB

💿 <b>磁盘使用：</b>
• 总计: {disk.total / 1024 / 1024 / 1024:.1f}GB
• 已用: {disk.used / 1024 / 1024 / 1024:.1f}GB ({disk.used / disk.total <i> 100:.1f}%)
• 可用: {disk.free / 1024 / 1024 / 1024:.1f}GB

⏰ 更新时间：{self.get_current_time()}
            """
            
            await message.reply_text(system_text, parse_mode=ParseMode.HTML)
            
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
        elif data.startswith("confirm_file_update_"):
            file_info = data.replace("confirm_file_update_", "")
            await self.confirm_file_update(query, file_info, user_id)
        elif data == "file_update_history":
            await self.show_file_update_history(query.message)
        elif data.startswith("restart_bots_"):
            bot_names = data.replace("restart_bots_", "").split(",")
            await self.restart_suggested_bots(query, bot_names)
        elif data == "ad_management":
            await self.show_ad_management(query)
        elif data == "ad_statistics":
            await self.show_ad_statistics(query)
        elif data == "create_ad":
            await self.prompt_create_ad(query)
        elif data == "ad_list":
            await self.show_ad_list(query)
        elif data == "ad_config":
            await self.show_ad_config(query)
        elif data.startswith("edit_ad_"):
            ad_id = int(data.replace("edit_ad_", ""))
            await self.show_edit_ad(query, ad_id)
        elif data.startswith("delete_ad_"):
            ad_id = int(data.replace("delete_ad_", ""))
            await self.confirm_delete_ad(query, ad_id)
        elif data.startswith("confirm_delete_ad_"):
            ad_id = int(data.replace("confirm_delete_ad_", ""))
            await self.delete_ad_action(query, ad_id)
        elif data.startswith("toggle_ad_"):
            ad_id = int(data.replace("toggle_ad_", ""))
            await self.toggle_ad_status(query, ad_id)
        elif data == "toggle_ad_system":
            await self.toggle_ad_system(query)
        elif data == "back_to_main":
            await self.start_command_from_callback(query)
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """帮助命令"""
        user_id = update.effective_user.id
        
        if not self.config.is_admin(user_id):
            await update.message.reply_text("❌ 您没有权限使用此机器人。")
            return
        
        help_text = """
🎛️ <b>控制机器人帮助</b>

📋 <b>基础命令：</b>
/start - 显示控制面板
/status - 查看机器人状态
/logs - 查看日志文件
/system - 系统状态监控
/help - 显示此帮助

🔄 <b>更新功能：</b>
/update - 执行系统更新
/add_admin <用户ID> <权限> - 添加管理员
/remove_admin <用户ID> - 移除管理员

📢 <b>广告管理：</b>
/ads - 广告管理面板
/create_ad <类型> <参数> - 创建广告

<b>广告类型：</b>
• text - 文本广告
• link - 链接广告  
• button - 按钮广告

📁 <b>文件更新 (直接发送文件)：</b>
• 📄 <b>单文件更新</b> - 发送 .py/.ini/.txt/.md/.sh 等文件
• 📦 <b>批量更新</b> - 发送 .zip/.tar.gz 压缩包
• 🔍 <b>智能分析</b> - 自动分析文件变更和风险
• 🛡️ <b>安全验证</b> - Python语法检查和权限验证
• 🔄 <b>自动重启</b> - 更新后智能建议重启相关机器人

<b>支持格式：</b>
• Python代码: .py
• 配置文件: .ini, .json, .yml
• 文档文件: .txt, .md
• 脚本文件: .sh
• 压缩包: .zip, .tar.gz, .tgz

🎮 <b>使用说明：</b>
• 使用控制面板可以快速管理机器人
• 直接向机器人发送文件即可开始更新流程
• 所有操作都会记录日志和备份
• 仅管理员可以使用此机器人

⚠️ <b>注意事项：</b>
• 重启操作可能需要几秒钟时间
• 确保配置文件正确后再启动机器人
• 定期检查日志以确保正常运行

如有问题，请联系系统管理员。
        """
        
        await update.message.reply_text(
            help_text,
            parse_mode=ParseMode.HTML
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
        
        result_text = "🔥 <b>热重载结果</b>\n\n" + "\n".join(results)
        await message.reply_text(result_text, parse_mode=ParseMode.HTML)
    
    async def show_admin_list(self, message):
        """显示管理员列表"""
        # 获取配置文件中的超级管理员
        super_admins = self.config.get_admin_users()
        
        # 获取动态管理员
        dynamic_admins = self.db.get_dynamic_admins()
        
        admin_text = "👨‍💼 <b>管理员列表</b>\n\n"
        
        # 超级管理员
        admin_text += "🔑 <b>超级管理员 (配置文件):</b>\n"
        for admin_id in super_admins:
            admin_text += f"• ID: {admin_id} (权限: super)\n"
        
        # 动态管理员
        admin_text += f"\n👥 <b>动态管理员 ({len(dynamic_admins)} 人):</b>\n"
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
        await message.reply_text(admin_text, parse_mode=ParseMode.HTML, reply_markup=reply_markup)
    
    async def prompt_add_admin(self, message):
        """提示添加管理员"""
        help_text = """
➕ <b>添加动态管理员</b>

请使用以下命令添加管理员：
<code>/add_admin <用户ID> <权限级别> [用户名]</code>

<b>参数说明：</b>
• 用户ID: 必需，数字格式
• 权限级别: basic 或 advanced
• 用户名: 可选，便于识别

<b>示例：</b>
<code>/add_admin 123456789 basic @username</code>
<code>/add_admin 987654321 advanced</code>

<b>权限说明：</b>
• basic: 基础权限，可以查看状态和日志
• advanced: 高级权限，可以管理机器人但不能管理其他管理员
        """
        
        await message.reply_text(help_text, parse_mode=ParseMode.HTML)
    
    async def show_system_config(self, message):
        """显示系统配置"""
        try:
            # 获取更新状态
            update_status = self.update_service.get_update_status()
            
            config_text = f"""
⚙️ <b>系统配置信息</b>

📱 <b>当前版本:</b> {update_status.get('current_version', 'unknown')}
🔄 <b>最后更新:</b> {update_status.get('last_update', '从未更新')[:19] if update_status.get('last_update') else '从未更新'}

🗂️ <b>Git状态:</b>
• Git仓库: {'✅' if update_status.get('is_git_repo') else '❌'}
• 有可用更新: {'✅' if update_status.get('has_updates') else '❌'}
• 落后提交: {update_status.get('git_behind_count', 0)} 个

📦 <b>备份信息:</b>
• 备份数量: {update_status.get('backup_count', 0)} 个
• 依赖文件: {'✅' if update_status.get('has_requirements') else '❌'}

🤖 <b>机器人状态:</b>
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
            await message.reply_text(config_text, parse_mode=ParseMode.HTML, reply_markup=reply_markup)
            
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
🔄 <b>系统更新确认</b>

📱 当前版本: {update_status.get('current_version', 'unknown')}
🔄 是否有更新: {'✅ 是' if update_status.get('has_updates') else '❌ 否'}

⚠️ <b>更新内容:</b>
• 📥 从Git拉取最新代码
• 📚 更新Python依赖包
• 🔄 重启所有机器人 (除控制机器人)
• 📦 自动创建备份

<b>确定要开始更新吗？</b>
        """
        
        keyboard = [
            [
                InlineKeyboardButton("✅ 确认更新", callback_data="confirm_update"),
                InlineKeyboardButton("❌ 取消", callback_data="system_config")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await message.reply_text(confirm_text, parse_mode=ParseMode.HTML, reply_markup=reply_markup)
    
    async def show_backup_list(self, message):
        """显示备份列表"""
        backups = self.update_service.get_backup_list()
        
        if not backups:
            await message.reply_text("📦 暂无系统备份")
            return
        
        backup_text = "📦 <b>系统备份列表</b>\n\n"
        
        for i, backup in enumerate(backups[:10]):  # 只显示最近10个备份
            backup_text += f"<b>{i+1}. {backup['name']}</b>\n"
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
        await message.reply_text(backup_text, parse_mode=ParseMode.HTML, reply_markup=reply_markup)
    
    async def show_update_status(self, message):
        """显示详细更新状态"""
        update_status = self.update_service.get_update_status()
        
        status_text = f"""
📊 <b>详细更新状态</b>

📱 <b>版本信息:</b>
• 当前版本: {update_status.get('current_version', 'unknown')}
• 最后更新版本: {update_status.get('last_version', '未知')}
• 最后更新时间: {update_status.get('last_update', '从未更新')[:19] if update_status.get('last_update') else '从未更新'}

🔄 <b>Git状态:</b>
• 是否Git仓库: {'✅' if update_status.get('is_git_repo') else '❌'}
• 落后提交数: {update_status.get('git_behind_count', 0)}
• 有可用更新: {'✅' if update_status.get('has_updates') else '❌'}

📦 <b>系统信息:</b>
• 备份数量: {update_status.get('backup_count', 0)}
• Requirements文件: {'✅' if update_status.get('has_requirements') else '❌'}
• 更新日志: {'✅' if update_status.get('update_log_exists') else '❌'}

🤖 <b>机器人状态:</b>
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
        
        await message.reply_text(status_text, parse_mode=ParseMode.HTML, reply_markup=reply_markup)
    
    async def add_admin_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """添加管理员命令"""
        user_id = update.effective_user.id
        
        if not self.config.is_super_admin(user_id):
            await update.message.reply_text("❌ 只有超级管理员才能添加管理员。")
            return
        
        if len(context.args) < 2:
            await update.message.reply_text(
                "❌ 用法: <code>/add_admin <用户ID> <权限级别> [用户名]</code>\n"
                "权限级别: basic, advanced",
                parse_mode=ParseMode.HTML
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
                "❌ 用法: <code>/remove_admin <用户ID></code>",
                parse_mode=ParseMode.HTML
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
            await update.message.reply_text(f"✅ <b>系统更新成功</b>\n\n{result}", parse_mode=ParseMode.HTML)
        else:
                         await update.message.reply_text(f"❌ <b>系统更新失败</b>\n\n{result}", parse_mode=ParseMode.HTML)
    
    async def confirm_update_action(self, query, user_id):
        """确认更新操作"""
        await query.edit_message_text("🔄 开始系统更新，请稍候...")
        
        # 执行完整更新
        success, result = await self.update_service.full_update()
        
        if success:
            await query.edit_message_text(f"✅ <b>系统更新成功</b>\n\n{result}", parse_mode=ParseMode.HTML)
        else:
            await query.edit_message_text(f"❌ <b>系统更新失败</b>\n\n{result}", parse_mode=ParseMode.HTML)
    
    async def rollback_action(self, query, backup_name):
        """回滚操作"""
        await query.edit_message_text(f"↩️ 开始回滚到备份 {backup_name}...")
        
        success, result = await self.update_service.rollback_to_backup(backup_name)
        
        if success:
            await query.edit_message_text(f"✅ <b>回滚成功</b>\n\n{result}", parse_mode=ParseMode.HTML)
        else:
            await query.edit_message_text(f"❌ <b>回滚失败</b>\n\n{result}", parse_mode=ParseMode.HTML)
    
    async def remove_admin_action(self, query, admin_id, removed_by):
        """移除管理员操作"""
        success = self.db.remove_dynamic_admin(admin_id, removed_by)
        
        if success:
            await query.edit_message_text(f"✅ 已移除管理员 (ID: {admin_id})")
        else:
            await query.edit_message_text(f"❌ 移除管理员失败 (ID: {admin_id})")
    
    async def handle_document(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理文档文件"""
        user_id = update.effective_user.id
        
        if not self.config.is_admin(user_id):
            await update.message.reply_text("❌ 您没有权限上传文件。")
            return
        
        document = update.message.document
        file_name = document.file_name
        file_size = document.file_size
        
        # 基础验证
        if file_size > 5 * 1024 * 1024:  # 5MB
            await update.message.reply_text(f"❌ 文件过大: {file_size / 1024 / 1024:.1f}MB (最大5MB)")
            return
        
        # 检查文件类型
        file_ext = Path(file_name).suffix.lower()
        
        # 压缩包处理
        if file_ext in ['.zip', '.tar', '.tar.gz', '.tgz']:
            await self.handle_archive_update(update, document)
            return
        
        # 单文件处理
        if file_ext not in self.file_update.allowed_extensions:
            await update.message.reply_text(f"❌ 不支持的文件类型: {file_ext}")
            return
        
        await update.message.reply_text("📥 正在下载文件...")
        
        try:
            # 下载文件
            file = await context.bot.get_file(document.file_id)
            
            # 创建临时目录
            os.makedirs(self.file_update.temp_dir, exist_ok=True)
            temp_file_path = os.path.join(
                self.file_update.temp_dir, 
                f"upload_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file_name}"
            )
            
            await file.download_to_drive(temp_file_path)
            
            # 分析文件
            analysis = self.file_update.analyze_file_changes(temp_file_path, file_name)
            
            if 'error' in analysis:
                await update.message.reply_text(f"❌ 文件分析失败: {analysis['error']}")
                os.remove(temp_file_path)
                return
            
            # 显示分析结果
            await self.show_file_analysis(update.message, analysis, temp_file_path, user_id)
            
        except Exception as e:
            await update.message.reply_text(f"❌ 文件处理失败: {e}")
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)
    
    async def handle_archive_update(self, update: Update, document):
        """处理压缩包更新"""
        user_id = update.effective_user.id
        
        if not self.config.is_super_admin(user_id):
            await update.message.reply_text("❌ 只有超级管理员才能上传压缩包进行批量更新。")
            return
        
        await update.message.reply_text("📦 正在处理压缩包...")
        
        try:
            # 下载压缩包
            file = await update.bot.get_file(document.file_id)
            
            os.makedirs(self.file_update.temp_dir, exist_ok=True)
            temp_file_path = os.path.join(
                self.file_update.temp_dir,
                f"archive_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{document.file_name}"
            )
            
            await file.download_to_drive(temp_file_path)
            
            # 处理压缩包
            success, result = await self.file_update.extract_and_update_archive(temp_file_path, user_id)
            
            # 清理临时文件
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)
            
            if success:
                await update.message.reply_text(f"✅ <b>压缩包更新成功</b>\n\n{result}", parse_mode=ParseMode.HTML)
                
                # 建议重启相关机器人
                lines = result.split('\n')
                updated_files = [line.replace('• ', '') for line in lines if line.startswith('• ') and '已更新文件:' in result]
                if updated_files:
                    restart_bots = self.file_update.suggest_restart_bots(updated_files)
                    if restart_bots:
                        await self.suggest_bot_restart(update.message, restart_bots)
            else:
                await update.message.reply_text(f"❌ <b>压缩包更新失败</b>\n\n{result}", parse_mode=ParseMode.HTML)
                
        except Exception as e:
            await update.message.reply_text(f"❌ 压缩包处理失败: {e}")
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)
    
    async def show_file_analysis(self, message, analysis: Dict, temp_file_path: str, user_id: int):
        """显示文件分析结果"""
        analysis_text = f"""
📋 <b>文件分析报告</b>

📁 <b>文件信息:</b>
• 文件名: {analysis['file_name']}
• 文件大小: {analysis['file_size']} bytes
• 文件类型: {analysis['file_type']}
• 目标存在: {'✅' if analysis['exists'] else '❌'}

🔄 <b>变更内容:</b>
        """
        
        for change in analysis['changes']:
            analysis_text += f"• {change}\n"
        
        if analysis['risks']:
            analysis_text += f"\n⚠️ <b>风险评估:</b>\n"
            for risk in analysis['risks']:
                analysis_text += f"• {risk}\n"
        
        if analysis['recommendations']:
            analysis_text += f"\n💡 <b>建议:</b>\n"
            for rec in analysis['recommendations']:
                analysis_text += f"• {rec}\n"
        
        # 创建确认按钮
        import base64
        file_info = base64.b64encode(f"{temp_file_path}|{analysis['file_name']}".encode()).decode()
        
        keyboard = [
            [
                InlineKeyboardButton("✅ 确认更新", callback_data=f"confirm_file_update_{file_info}"),
                InlineKeyboardButton("❌ 取消", callback_data="cancel_file_update")
            ],
            [InlineKeyboardButton("📋 查看更新历史", callback_data="file_update_history")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await message.reply_text(analysis_text, parse_mode=ParseMode.HTML, reply_markup=reply_markup)
    
    async def confirm_file_update(self, query, file_info: str, user_id: int):
        """确认文件更新"""
        try:
            import base64
            decoded_info = base64.b64decode(file_info.encode()).decode()
            temp_file_path, target_name = decoded_info.split('|')
            
            if not os.path.exists(temp_file_path):
                await query.edit_message_text("❌ 临时文件不存在，请重新上传")
                return
            
            await query.edit_message_text("🔄 正在更新文件...")
            
            # 执行文件更新
            success, result = await self.file_update.update_single_file(temp_file_path, target_name, user_id)
            
            # 清理临时文件
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)
            
            if success:
                await query.edit_message_text(f"✅ {result}")
                
                # 建议重启相关机器人
                restart_bots = self.file_update.suggest_restart_bots([target_name])
                if restart_bots:
                    await self.suggest_bot_restart(query.message, restart_bots)
            else:
                await query.edit_message_text(f"❌ {result}")
                
        except Exception as e:
            await query.edit_message_text(f"❌ 更新失败: {e}")
    
    async def suggest_bot_restart(self, message, bot_names: List[str]):
        """建议重启机器人"""
        if not bot_names:
            return
        
        bot_display = []
        for bot_name in bot_names:
            if bot_name in self.hot_update.bot_configs:
                bot_display.append(self.hot_update.bot_configs[bot_name]['name'])
            else:
                bot_display.append(bot_name)
        
        suggest_text = f"""
🔄 <b>建议重启机器人</b>

由于文件更新，建议重启以下机器人以使更改生效：
{chr(10).join(f'• {name}' for name in bot_display)}

是否立即重启这些机器人？
        """
        
        keyboard = [
            [
                InlineKeyboardButton("🔄 立即重启", callback_data=f"restart_bots_{','.join(bot_names)}"),
                InlineKeyboardButton("⏭️ 稍后手动", callback_data="back_to_main")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await message.reply_text(suggest_text, parse_mode=ParseMode.HTML, reply_markup=reply_markup)
    
    async def restart_suggested_bots(self, query, bot_names: List[str]):
        """重启建议的机器人"""
        await query.edit_message_text("🔄 正在重启机器人...")
        
        results = []
        for bot_name in bot_names:
            if bot_name in self.hot_update.bot_configs:
                success, msg = await self.hot_update.restart_bot(bot_name)
                status_emoji = "✅" if success else "❌"
                results.append(f"{status_emoji} {self.hot_update.bot_configs[bot_name]['name']}: {msg}")
        
        result_text = "🔄 <b>机器人重启结果</b>\n\n" + "\n".join(results)
        await query.edit_message_text(result_text, parse_mode=ParseMode.HTML)
    
    async def show_file_update_history(self, message):
        """显示文件更新历史"""
        history = self.file_update.get_update_history(15)
        
        if not history:
            await message.reply_text("📋 暂无文件更新历史")
            return
        
        history_text = "📋 <b>文件更新历史</b>\n\n"
        
        for i, record in enumerate(history, 1):
            history_text += f"<b>{i}. {record['file_name']}</b>\n"
            history_text += f"• 更新时间: {record['updated_time'][:19]}\n"
            history_text += f"• 更新用户: {record['updated_by']}\n"
            history_text += f"• 文件大小: {record['file_size']} bytes\n\n"
        
        keyboard = [
            [
                InlineKeyboardButton("🔄 刷新历史", callback_data="file_update_history"),
                InlineKeyboardButton("🔙 返回", callback_data="back_to_main")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await message.reply_text(history_text, parse_mode=ParseMode.HTML, reply_markup=reply_markup)
    
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
        self.app.add_handler(CommandHandler("create_ad", self.create_ad_command))
        self.app.add_handler(CommandHandler("ads", self.ads_command))
        
        # 文件处理器
        self.app.add_handler(MessageHandler(filters.Document.ALL, self.handle_document))
        
        # 回调处理器
        self.app.add_handler(CallbackQueryHandler(self.handle_callback))
        
        logger.info("控制机器人启动中...")
        
        # 启动机器人
        self.app.run_polling(drop_pending_updates=True)
    
    # ==================== 广告管理功能 ====================
    
    async def show_ad_management(self, query):
        """显示广告管理主菜单"""
        user_id = query.from_user.id
        
        if not self.config.is_admin(user_id):
            await query.answer("❌ 权限不足", show_alert=True)
            return
        
        # 获取广告统计
        stats = self.ad_manager.get_ad_statistics()
        config = self.ad_manager.config
        
        text = f"""
📢 <b>广告管理系统</b>

📊 <b>系统状态:</b>
• 广告系统: {'🟢 启用' if config.enabled else '🔴 禁用'}
• 总广告数: {stats.get('total_ads', 0)}
• 活跃广告: {stats.get('active_ads', 0)}
• 总展示数: {stats.get('total_displays', 0)}

⚙️ <b>配置信息:</b>
• 每篇最大广告数: {config.max_ads_per_post}
• 显示广告标签: {'是' if config.show_ad_label else '否'}
• 随机选择: {'是' if config.random_selection else '否'}
        """
        
        keyboard = [
            [
                InlineKeyboardButton("➕ 创建广告", callback_data="create_ad"),
                InlineKeyboardButton("📋 广告列表", callback_data="ad_list")
            ],
            [
                InlineKeyboardButton("⚙️ 系统配置", callback_data="ad_config"),
                InlineKeyboardButton("📊 统计报告", callback_data="ad_statistics")
            ],
            [
                InlineKeyboardButton(
                    f"{'🔴 禁用' if config.enabled else '🟢 启用'}广告系统",
                    callback_data="toggle_ad_system"
                )
            ],
            [InlineKeyboardButton("🔙 返回主菜单", callback_data="back_to_main")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        try:
            await query.edit_message_text(text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
        except:
            await query.message.reply_text(text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
    
    async def show_ad_statistics(self, query):
        """显示广告统计信息"""
        user_id = query.from_user.id
        
        if not self.config.is_admin(user_id):
            await query.answer("❌ 权限不足", show_alert=True)
            return
        
        # 获取总体统计
        overall_stats = self.ad_manager.get_ad_statistics()
        
        # 获取所有广告
        all_ads = self.ad_manager.get_advertisements()
        
        text = f"""
📊 <b>广告统计报告</b>

📈 <b>总体数据:</b>
• 总广告数: {overall_stats.get('total_ads', 0)}
• 活跃广告: {overall_stats.get('active_ads', 0)}
• 总展示次数: {overall_stats.get('total_displays', 0):,}
• 总点击次数: {overall_stats.get('total_clicks', 0):,}
• 整体点击率: {overall_stats.get('overall_ctr', 0):.2f}%

📋 <b>按状态分类:</b>
        """
        
        # 按状态统计
        status_counts = {}
        for ad in all_ads:
            status = ad.status.value
            status_counts[status] = status_counts.get(status, 0) + 1
        
        status_names = {
            'active': '🟢 活跃',
            'paused': '🟡 暂停',
            'expired': '🔴 过期',
            'draft': '📝 草稿'
        }
        
        for status, count in status_counts.items():
            name = status_names.get(status, status)
            text += f"• {name}: {count}\n"
        
        # 按位置统计
        position_counts = {}
        for ad in all_ads:
            pos = ad.position.value
            position_counts[pos] = position_counts.get(pos, 0) + 1
        
        text += f"\n📍 <b>按位置分类:</b>\n"
        position_names = {
            'before_content': '📤 内容前',
            'after_content': '📥 内容后',
            'middle_content': '🔄 内容中'
        }
        
        for pos, count in position_counts.items():
            name = position_names.get(pos, pos)
            text += f"• {name}: {count}\n"
        
        # Top 5 表现最佳的广告
        active_ads = [ad for ad in all_ads if ad.status == AdStatus.ACTIVE]
        if active_ads:
            # 按点击率排序
            sorted_ads = sorted(active_ads, 
                              key=lambda x: (x.click_count / max(x.display_count, 1)), 
                              reverse=True)[:5]
            
            text += f"\n🏆 <b>表现最佳广告:</b>\n"
            for i, ad in enumerate(sorted_ads, 1):
                ctr = (ad.click_count / max(ad.display_count, 1)) * 100
                text += f"{i}. {ad.name} - CTR: {ctr:.1f}%\n"
        
        keyboard = [
            [InlineKeyboardButton("🔄 刷新数据", callback_data="ad_statistics")],
            [InlineKeyboardButton("🔙 返回广告管理", callback_data="ad_management")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        try:
            await query.edit_message_text(text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
        except:
            await query.message.reply_text(text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
    
    async def show_ad_list(self, query):
        """显示广告列表"""
        user_id = query.from_user.id
        
        if not self.config.is_admin(user_id):
            await query.answer("❌ 权限不足", show_alert=True)
            return
        
        ads = self.ad_manager.get_advertisements()
        
        if not ads:
            text = "📝 <b>广告列表</b>\n\n暂无广告，点击下方按钮创建第一个广告。"
            keyboard = [
                [InlineKeyboardButton("➕ 创建广告", callback_data="create_ad")],
                [InlineKeyboardButton("🔙 返回广告管理", callback_data="ad_management")]
            ]
        else:
            text = f"📝 <b>广告列表</b> (共 {len(ads)} 个)\n\n"
            
            keyboard = []
            for ad in ads[:10]:  # 显示前10个广告
                # 状态图标
                status_icons = {
                    AdStatus.ACTIVE: '🟢',
                    AdStatus.PAUSED: '🟡',
                    AdStatus.EXPIRED: '🔴',
                    AdStatus.DRAFT: '📝'
                }
                status_icon = status_icons.get(ad.status, '❓')
                
                # 类型图标
                type_icons = {
                    AdType.TEXT: '📝',
                    AdType.LINK: '🔗',
                    AdType.IMAGE: '🖼️',
                    AdType.VIDEO: '🎬',
                    AdType.BUTTON: '🔘'
                }
                type_icon = type_icons.get(ad.type, '❓')
                
                text += f"{status_icon} {type_icon} <b>{ad.name}</b>\n"
                text += f"   展示: {ad.display_count} | 点击: {ad.click_count}\n\n"
                
                keyboard.append([
                    InlineKeyboardButton(f"✏️ {ad.name}", callback_data=f"edit_ad_{ad.id}"),
                    InlineKeyboardButton(
                        "🔴 暂停" if ad.status == AdStatus.ACTIVE else "🟢 启用",
                        callback_data=f"toggle_ad_{ad.id}"
                    )
                ])
            
            if len(ads) > 10:
                text += f"... 还有 {len(ads) - 10} 个广告"
            
            keyboard.extend([
                [InlineKeyboardButton("➕ 创建新广告", callback_data="create_ad")],
                [InlineKeyboardButton("🔙 返回广告管理", callback_data="ad_management")]
            ])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        try:
            await query.edit_message_text(text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
        except:
            await query.message.reply_text(text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
    
    async def prompt_create_ad(self, query):
        """提示创建广告"""
        user_id = query.from_user.id
        
        if not self.config.is_admin(user_id):
            await query.answer("❌ 权限不足", show_alert=True)
            return
        
        text = """
➕ <b>创建新广告</b>

请使用以下命令创建广告：

<b>文本广告:</b>
<code>/create_ad text <广告名称>
<广告内容></code>

<b>链接广告:</b>
<code>/create_ad link <广告名称> <链接地址>
<广告内容></code>

<b>按钮广告:</b>
<code>/create_ad button <广告名称> <链接地址> <按钮文字>
<广告内容></code>

<b>示例:</b>
``<code>
/create_ad text 欢迎广告
🎉 欢迎来到我们的频道！
订阅获取更多精彩内容。
</code>`<code>

</code>`<code>
/create_ad link 官网推广 https://example.com
🌐 访问我们的官方网站
获取更多信息和服务。
</code>`<code>

<b>说明:</b>
• 广告默认位置为内容后
• 广告默认状态为草稿，需要手动启用
• 支持Markdown格式
        """
        
        keyboard = [
            [InlineKeyboardButton("🔙 返回广告管理", callback_data="ad_management")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        try:
            await query.edit_message_text(text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
        except:
            await query.message.reply_text(text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
    
    async def show_ad_config(self, query):
        """显示广告系统配置"""
        user_id = query.from_user.id
        
        if not self.config.is_admin(user_id):
            await query.answer("❌ 权限不足", show_alert=True)
            return
        
        config = self.ad_manager.config
        
        text = f"""
⚙️ <b>广告系统配置</b>

🔧 <b>当前设置:</b>
• 系统状态: {'🟢 启用' if config.enabled else '🔴 禁用'}
• 每篇最大广告数: {config.max_ads_per_post}
• 每篇最小广告数: {config.min_ads_per_post}
• 显示广告标签: {'✅ 是' if config.show_ad_label else '❌ 否'}
• 随机选择广告: {'✅ 是' if config.random_selection else '❌ 否'}

📝 <b>广告分隔符:</b>
</code>`<code>
{config.ad_separator.replace(chr(10), chr(92) + 'n')}
</code>`<code>

💡 <b>说明:</b>
• 广告标签会在广告内容前显示 "📢 广告"
• 随机选择会根据权重随机选择广告
• 分隔符用于分隔多个广告
        """
        
        keyboard = [
            [
                InlineKeyboardButton(
                    f"{'🔴 禁用' if config.enabled else '🟢 启用'}广告系统",
                    callback_data="toggle_ad_system"
                )
            ],
            [InlineKeyboardButton("🔙 返回广告管理", callback_data="ad_management")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        try:
            await query.edit_message_text(text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
        except:
            await query.message.reply_text(text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
    
    async def toggle_ad_system(self, query):
        """切换广告系统启用状态"""
        user_id = query.from_user.id
        
        if not self.config.is_super_admin(user_id):
            await query.answer("❌ 需要超级管理员权限", show_alert=True)
            return
        
        config = self.ad_manager.config
        config.enabled = not config.enabled
        
        if self.ad_manager.update_config(config):
            status = "启用" if config.enabled else "禁用"
            await query.answer(f"✅ 广告系统已{status}", show_alert=True)
            await self.show_ad_config(query)
        else:
            await query.answer("❌ 配置更新失败", show_alert=True)
    
    async def show_edit_ad(self, query, ad_id: int):
        """显示广告编辑界面"""
        user_id = query.from_user.id
        
        if not self.config.is_admin(user_id):
            await query.answer("❌ 权限不足", show_alert=True)
            return
        
        ad = self.ad_manager.get_advertisement(ad_id)
        if not ad:
            await query.answer("❌ 广告不存在", show_alert=True)
            return
        
        # 状态和类型显示
        status_names = {
            AdStatus.ACTIVE: '🟢 活跃',
            AdStatus.PAUSED: '🟡 暂停',
            AdStatus.EXPIRED: '🔴 过期',
            AdStatus.DRAFT: '📝 草稿'
        }
        
        type_names = {
            AdType.TEXT: '📝 文本',
            AdType.LINK: '🔗 链接',
            AdType.IMAGE: '🖼️ 图片',
            AdType.VIDEO: '🎬 视频',
            AdType.BUTTON: '🔘 按钮'
        }
        
        position_names = {
            AdPosition.BEFORE_CONTENT: '📤 内容前',
            AdPosition.AFTER_CONTENT: '📥 内容后',
            AdPosition.MIDDLE_CONTENT: '🔄 内容中'
        }
        
        text = f"""
✏️ <b>编辑广告: {ad.name}</b>

📋 <b>基本信息:</b>
• ID: {ad.id}
• 名称: {ad.name}
• 类型: {type_names.get(ad.type, ad.type.value)}
• 状态: {status_names.get(ad.status, ad.status.value)}
• 位置: {position_names.get(ad.position, ad.position.value)}

📊 <b>统计数据:</b>
• 展示次数: {ad.display_count:,}
• 点击次数: {ad.click_count:,}
• 点击率: {(ad.click_count / max(ad.display_count, 1) * 100):.2f}%
• 优先级: {ad.priority}
• 权重: {ad.weight}

📄 <b>内容预览:</b>
{ad.content[:200]}{'...' if len(ad.content) > 200 else ''}
        """
        
        if ad.url:
            text += f"\n🔗 <b>链接:</b> {ad.url}"
        
        if ad.button_text:
            text += f"\n🔘 <b>按钮文字:</b> {ad.button_text}"
        
        keyboard = [
            [
                InlineKeyboardButton(
                    "🔴 暂停" if ad.status == AdStatus.ACTIVE else "🟢 启用",
                    callback_data=f"toggle_ad_{ad.id}"
                ),
                InlineKeyboardButton("🗑️ 删除", callback_data=f"delete_ad_{ad.id}")
            ],
            [InlineKeyboardButton("🔙 返回列表", callback_data="ad_list")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        try:
            await query.edit_message_text(text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
        except:
            await query.message.reply_text(text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
    
    async def toggle_ad_status(self, query, ad_id: int):
        """切换广告状态"""
        user_id = query.from_user.id
        
        if not self.config.is_admin(user_id):
            await query.answer("❌ 权限不足", show_alert=True)
            return
        
        ad = self.ad_manager.get_advertisement(ad_id)
        if not ad:
            await query.answer("❌ 广告不存在", show_alert=True)
            return
        
        # 切换状态
        new_status = AdStatus.PAUSED if ad.status == AdStatus.ACTIVE else AdStatus.ACTIVE
        
        if self.ad_manager.update_advertisement(ad_id, {'status': new_status.value}):
            status_name = "启用" if new_status == AdStatus.ACTIVE else "暂停"
            await query.answer(f"✅ 广告已{status_name}", show_alert=True)
            await self.show_edit_ad(query, ad_id)
        else:
            await query.answer("❌ 更新失败", show_alert=True)
    
    async def confirm_delete_ad(self, query, ad_id: int):
        """确认删除广告"""
        user_id = query.from_user.id
        
        if not self.config.is_admin(user_id):
            await query.answer("❌ 权限不足", show_alert=True)
            return
        
        ad = self.ad_manager.get_advertisement(ad_id)
        if not ad:
            await query.answer("❌ 广告不存在", show_alert=True)
            return
        
        text = f"""
🗑️ <b>确认删除广告</b>

<b>广告信息:</b>
• 名称: {ad.name}
• 展示次数: {ad.display_count:,}
• 点击次数: {ad.click_count:,}

⚠️ <b>警告:</b> 删除操作不可恢复！
        """
        
        keyboard = [
            [
                InlineKeyboardButton("✅ 确认删除", callback_data=f"confirm_delete_ad_{ad_id}"),
                InlineKeyboardButton("❌ 取消", callback_data=f"edit_ad_{ad_id}")
            ]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        try:
            await query.edit_message_text(text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
        except:
            await query.message.reply_text(text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
    
    async def delete_ad_action(self, query, ad_id: int):
        """执行删除广告"""
        user_id = query.from_user.id
        
        if not self.config.is_admin(user_id):
            await query.answer("❌ 权限不足", show_alert=True)
            return
        
        if self.ad_manager.delete_advertisement(ad_id):
            await query.answer("✅ 广告已删除", show_alert=True)
            await self.show_ad_list(query)
        else:
            await query.answer("❌ 删除失败", show_alert=True)
    
    async def create_ad_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """创建广告命令"""
        user_id = update.effective_user.id
        
        if not self.config.is_admin(user_id):
            await update.message.reply_text("❌ 您没有权限使用此命令。")
            return
        
        if not context.args:
            await update.message.reply_text("""
❌ <b>使用方法:</b>

<b>文本广告:</b>
</code>/create_ad text <广告名称>
<广告内容><code>

<b>链接广告:</b>
</code>/create_ad link <广告名称> <链接地址>
<广告内容><code>

<b>按钮广告:</b>
</code>/create_ad button <广告名称> <链接地址> <按钮文字>
<广告内容><code>
            """, parse_mode=ParseMode.HTML)
            return
        
        ad_type_str = context.args[0].lower()
        
        try:
            if ad_type_str == 'text':
                if len(context.args) < 2:
                    await update.message.reply_text("❌ 请提供广告名称和内容")
                    return
                
                # 解析参数
                message_text = update.message.text
                lines = message_text.split('\n', 2)
                if len(lines) < 3:
                    await update.message.reply_text("❌ 请在新行提供广告内容")
                    return
                
                ad_name = context.args[1]
                ad_content = lines[2]
                
                ad = Advertisement(
                    id=0,  # 将由数据库自动分配
                    name=ad_name,
                    type=AdType.TEXT,
                    position=AdPosition.AFTER_CONTENT,
                    content=ad_content,
                    created_by=user_id,
                    status=AdStatus.DRAFT
                )
                
            elif ad_type_str == 'link':
                if len(context.args) < 3:
                    await update.message.reply_text("❌ 请提供广告名称、链接地址和内容")
                    return
                
                message_text = update.message.text
                lines = message_text.split('\n', 2)
                if len(lines) < 3:
                    await update.message.reply_text("❌ 请在新行提供广告内容")
                    return
                
                ad_name = context.args[1]
                ad_url = context.args[2]
                ad_content = lines[2]
                
                ad = Advertisement(
                    id=0,
                    name=ad_name,
                    type=AdType.LINK,
                    position=AdPosition.AFTER_CONTENT,
                    content=ad_content,
                    url=ad_url,
                    created_by=user_id,
                    status=AdStatus.DRAFT
                )
                
            elif ad_type_str == 'button':
                if len(context.args) < 4:
                    await update.message.reply_text("❌ 请提供广告名称、链接地址、按钮文字和内容")
                    return
                
                message_text = update.message.text
                lines = message_text.split('\n', 2)
                if len(lines) < 3:
                    await update.message.reply_text("❌ 请在新行提供广告内容")
                    return
                
                ad_name = context.args[1]
                ad_url = context.args[2]
                button_text = context.args[3]
                ad_content = lines[2]
                
                ad = Advertisement(
                    id=0,
                    name=ad_name,
                    type=AdType.BUTTON,
                    position=AdPosition.AFTER_CONTENT,
                    content=ad_content,
                    url=ad_url,
                    button_text=button_text,
                    created_by=user_id,
                    status=AdStatus.DRAFT
                )
                
            else:
                await update.message.reply_text("❌ 不支持的广告类型。支持: text, link, button")
                return
            
            # 创建广告
            ad_id = self.ad_manager.create_advertisement(ad)
            
            await update.message.reply_text(f"""
✅ <b>广告创建成功！</b>

• 广告ID: {ad_id}
• 名称: {ad.name}
• 类型: {ad.type.value}
• 状态: 草稿 (需要手动启用)

使用 </code>/ads` 命令管理您的广告。
            """, parse_mode=ParseMode.HTML)
            
        except Exception as e:
            logger.error(f"创建广告失败: {e}")
            await update.message.reply_text(f"❌ 创建广告失败: {e}")
    
    async def ads_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """广告管理命令"""
        user_id = update.effective_user.id
        
        if not self.config.is_admin(user_id):
            await update.message.reply_text("❌ 您没有权限使用此命令。")
            return
        
        # 创建一个虚拟的query对象来复用现有方法
        class MockQuery:
            def __init__(self, message):
                self.message = message
                self.from_user = message.from_user
        
        mock_query = MockQuery(update.message)
        await self.show_ad_management(mock_query)
    
    async def start_command_from_callback(self, query):
        """从回调显示开始菜单"""
        user_id = query.from_user.id
        admin_level = self.config.get_admin_level(user_id)
        
        if admin_level == "none":
            await query.answer("❌ 您没有权限使用此机器人。", show_alert=True)
            return
        
        user_name = query.from_user.first_name or query.from_user.username
        
        welcome_text = f"""
🎛️ <b>机器人控制面板</b>

👋 欢迎 {user_name}！ (权限: {admin_level})

🤖 <b>机器人管理：</b>
• 启动/停止/重启机器人
• 热更新配置
• 实时状态监控

👨‍💼 <b>管理员功能：</b>
• 添加/移除动态管理员
• 查看操作日志
• 系统资源监控

📋 <b>快速操作：</b>
使用下方按钮进行管理
        """
        
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
        
        if admin_level == "super":
            keyboard.extend([
                [
                    InlineKeyboardButton("👨‍💼 管理员列表", callback_data="admin_list"),
                    InlineKeyboardButton("➕ 添加管理员", callback_data="add_admin")
                ],
                [
                    InlineKeyboardButton("📋 操作日志", callback_data="show_logs"),
                    InlineKeyboardButton("⚙️ 系统配置", callback_data="system_config")
                ],
                [
                    InlineKeyboardButton("📁 文件更新历史", callback_data="file_update_history"),
                    InlineKeyboardButton("🔄 一键更新", callback_data="one_click_update")
                ],
                [
                    InlineKeyboardButton("📢 广告管理", callback_data="ad_management"),
                    InlineKeyboardButton("📊 广告统计", callback_data="ad_statistics")
                ]
            ])
        else:
            keyboard.append([
                InlineKeyboardButton("📋 查看日志", callback_data="show_logs")
            ])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        try:
            await query.edit_message_text(
                welcome_text,
                parse_mode=ParseMode.HTML,
                reply_markup=reply_markup
            )
        except:
            await query.message.reply_text(
                welcome_text,
                parse_mode=ParseMode.HTML,
                reply_markup=reply_markup
            )

if __name__ == '__main__':
    bot = ControlBot()
    bot.run()