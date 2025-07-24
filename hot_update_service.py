#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import signal
import subprocess
import psutil
import hashlib
import asyncio
import logging
from typing import Dict, List, Optional, Tuple
from database import DatabaseManager
from config_manager import ConfigManager

logger = logging.getLogger(__name__)

class HotUpdateService:
    def __init__(self):
        self.config = ConfigManager()
        self.db = DatabaseManager(self.config.get_db_file())
        self.bot_configs = {
            'submission': {
                'script': 'submission_bot.py',
                'name': '投稿机器人',
                'description': '接收用户投稿的机器人'
            },
            'publish': {
                'script': 'publish_bot.py', 
                'name': '发布机器人',
                'description': '审核投稿并发布到频道的机器人'
            }
        }
        self.processes = {}
    
    def get_config_hash(self) -> str:
        """计算配置文件的哈希值，用于检测配置变更"""
        try:
            with open('config.ini', 'rb') as f:
                return hashlib.md5(f.read()).hexdigest()
        except Exception as e:
            logger.error(f"计算配置哈希失败: {e}")
            return ""
    
    def check_bot_process(self, bot_name: str) -> Dict:
        """检查机器人进程状态"""
        script_name = self.bot_configs[bot_name]['script']
        status = {
            'running': False,
            'pid': None,
            'memory_mb': 0,
            'cpu_percent': 0,
            'start_time': None,
            'restart_count': 0
        }
        
        try:
            # 从数据库获取重启次数
            bot_status = self.db.get_bot_status(bot_name)
            if bot_status:
                status['restart_count'] = bot_status.get('restart_count', 0)
            
            # 查找进程
            for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'memory_info', 'cpu_percent', 'create_time']):
                try:
                    cmdline = ' '.join(proc.info['cmdline']) if proc.info['cmdline'] else ''
                    if script_name in cmdline and 'python' in cmdline:
                        status['running'] = True
                        status['pid'] = proc.info['pid']
                        status['memory_mb'] = round(proc.info['memory_info'].rss / 1024 / 1024, 1)
                        status['cpu_percent'] = proc.info['cpu_percent']
                        
                        import datetime
                        status['start_time'] = datetime.datetime.fromtimestamp(
                            proc.info['create_time']
                        ).strftime("%H:%M:%S")
                        break
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue
        except Exception as e:
            logger.error(f"检查 {bot_name} 机器人进程失败: {e}")
        
        return status
    
    async def start_bot(self, bot_name: str) -> Tuple[bool, str]:
        """启动指定的机器人"""
        if bot_name not in self.bot_configs:
            return False, f"未知的机器人: {bot_name}"
        
        script_name = self.bot_configs[bot_name]['script']
        bot_display_name = self.bot_configs[bot_name]['name']
        
        # 检查是否已经运行
        status = self.check_bot_process(bot_name)
        if status['running']:
            return False, f"{bot_display_name}已经在运行中 (PID: {status['pid']})"
        
        try:
            # 启动进程
            process = subprocess.Popen(
                ['python3', script_name],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                preexec_fn=os.setsid
            )
            
            self.processes[bot_name] = process
            
            # 等待一下检查是否成功启动
            await asyncio.sleep(3)
            
            if process.poll() is None:
                # 更新数据库状态
                config_hash = self.get_config_hash()
                self.db.update_bot_status(bot_name, 'running', config_hash)
                
                logger.info(f"{bot_display_name}启动成功 (PID: {process.pid})")
                return True, f"{bot_display_name}启动成功 (PID: {process.pid})"
            else:
                # 获取错误信息
                _, stderr = process.communicate()
                error_msg = stderr.decode('utf-8')[:200] if stderr else "未知错误"
                
                logger.error(f"{bot_display_name}启动失败: {error_msg}")
                return False, f"{bot_display_name}启动失败: {error_msg}"
                
        except Exception as e:
            logger.error(f"启动 {bot_display_name} 失败: {e}")
            return False, f"启动 {bot_display_name} 失败: {str(e)}"
    
    async def stop_bot(self, bot_name: str) -> Tuple[bool, str]:
        """停止指定的机器人"""
        if bot_name not in self.bot_configs:
            return False, f"未知的机器人: {bot_name}"
        
        script_name = self.bot_configs[bot_name]['script']
        bot_display_name = self.bot_configs[bot_name]['name']
        
        try:
            stopped = False
            
            # 首先尝试停止我们启动的进程
            if bot_name in self.processes and self.processes[bot_name]:
                try:
                    process = self.processes[bot_name]
                    os.killpg(os.getpgid(process.pid), signal.SIGTERM)
                    
                    # 等待进程结束
                    try:
                        process.wait(timeout=10)
                        stopped = True
                        logger.info(f"通过进程组停止了 {bot_display_name}")
                    except subprocess.TimeoutExpired:
                        # 强制停止
                        os.killpg(os.getpgid(process.pid), signal.SIGKILL)
                        stopped = True
                        logger.info(f"强制停止了 {bot_display_name}")
                        
                except (ProcessLookupError, psutil.NoSuchProcess):
                    pass
                finally:
                    self.processes[bot_name] = None
            
            # 如果上面没有成功，通过进程名查找并停止
            if not stopped:
                for proc in psutil.process_iter(['pid', 'cmdline']):
                    try:
                        cmdline = ' '.join(proc.info['cmdline']) if proc.info['cmdline'] else ''
                        if script_name in cmdline and 'python' in cmdline:
                            proc.terminate()
                            proc.wait(timeout=5)
                            stopped = True
                            logger.info(f"通过进程查找停止了 {bot_display_name}")
                            break
                    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.TimeoutExpired):
                        continue
            
            if stopped:
                # 更新数据库状态
                self.db.update_bot_status(bot_name, 'stopped')
                return True, f"{bot_display_name}已成功停止"
            else:
                return False, f"{bot_display_name}未在运行或停止失败"
                
        except Exception as e:
            logger.error(f"停止 {bot_display_name} 失败: {e}")
            return False, f"停止 {bot_display_name} 失败: {str(e)}"
    
    async def restart_bot(self, bot_name: str) -> Tuple[bool, str]:
        """重启指定的机器人"""
        if bot_name not in self.bot_configs:
            return False, f"未知的机器人: {bot_name}"
        
        bot_display_name = self.bot_configs[bot_name]['name']
        
        # 增加重启计数
        self.db.increment_restart_count(bot_name)
        
        # 先停止
        stop_success, stop_msg = await self.stop_bot(bot_name)
        if not stop_success and "未在运行" not in stop_msg:
            return False, f"重启失败: {stop_msg}"
        
        # 等待一下
        await asyncio.sleep(2)
        
        # 再启动
        start_success, start_msg = await self.start_bot(bot_name)
        if start_success:
            return True, f"{bot_display_name}重启成功"
        else:
            return False, f"重启失败: {start_msg}"
    
    async def hot_reload_bot(self, bot_name: str) -> Tuple[bool, str]:
        """热重载机器人（检测配置变更后重启）"""
        if bot_name not in self.bot_configs:
            return False, f"未知的机器人: {bot_name}"
        
        bot_display_name = self.bot_configs[bot_name]['name']
        current_hash = self.get_config_hash()
        
        # 检查配置是否有变更
        bot_status = self.db.get_bot_status(bot_name)
        if bot_status and bot_status.get('config_hash') == current_hash:
            return True, f"{bot_display_name}配置无变更，无需重载"
        
        # 配置有变更，执行热重载
        success, msg = await self.restart_bot(bot_name)
        if success:
            # 更新配置哈希
            self.db.update_bot_status(bot_name, 'running', current_hash)
            return True, f"{bot_display_name}热重载成功 (配置已更新)"
        else:
            return False, f"{bot_display_name}热重载失败: {msg}"
    
    async def start_all_bots(self) -> Dict[str, Tuple[bool, str]]:
        """启动所有机器人"""
        results = {}
        for bot_name in self.bot_configs.keys():
            results[bot_name] = await self.start_bot(bot_name)
            await asyncio.sleep(1)  # 间隔启动
        return results
    
    async def stop_all_bots(self) -> Dict[str, Tuple[bool, str]]:
        """停止所有机器人"""
        results = {}
        for bot_name in self.bot_configs.keys():
            results[bot_name] = await self.stop_bot(bot_name)
        return results
    
    async def restart_all_bots(self) -> Dict[str, Tuple[bool, str]]:
        """重启所有机器人"""
        results = {}
        for bot_name in self.bot_configs.keys():
            results[bot_name] = await self.restart_bot(bot_name)
            await asyncio.sleep(2)  # 间隔重启
        return results
    
    def get_all_bots_status(self) -> Dict[str, Dict]:
        """获取所有机器人状态"""
        status = {}
        for bot_name in self.bot_configs.keys():
            bot_status = self.check_bot_process(bot_name)
            bot_status['display_name'] = self.bot_configs[bot_name]['name']
            bot_status['description'] = self.bot_configs[bot_name]['description']
            status[bot_name] = bot_status
        return status
    
    async def check_and_auto_restart(self) -> List[str]:
        """检查并自动重启崩溃的机器人"""
        restarted_bots = []
        
        for bot_name in self.bot_configs.keys():
            status = self.check_bot_process(bot_name)
            bot_db_status = self.db.get_bot_status(bot_name)
            
            # 如果数据库显示应该运行但实际没有运行，则自动重启
            if (bot_db_status and 
                bot_db_status.get('status') == 'running' and 
                not status['running']):
                
                logger.warning(f"检测到 {self.bot_configs[bot_name]['name']} 意外停止，正在自动重启...")
                success, msg = await self.restart_bot(bot_name)
                if success:
                    restarted_bots.append(bot_name)
                    logger.info(f"自动重启 {self.bot_configs[bot_name]['name']} 成功")
                else:
                    logger.error(f"自动重启 {self.bot_configs[bot_name]['name']} 失败: {msg}")
        
        return restarted_bots
    
    def get_system_info(self) -> Dict:
        """获取系统信息"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            load_avg = os.getloadavg()
            
            return {
                'cpu_percent': cpu_percent,
                'memory_total_gb': round(memory.total / 1024 / 1024 / 1024, 1),
                'memory_used_gb': round(memory.used / 1024 / 1024 / 1024, 1),
                'memory_percent': memory.percent,
                'disk_total_gb': round(disk.total / 1024 / 1024 / 1024, 1),
                'disk_used_gb': round(disk.used / 1024 / 1024 / 1024, 1),
                'disk_percent': round(disk.used / disk.total * 100, 1),
                'load_avg_1m': load_avg[0],
                'load_avg_5m': load_avg[1],
                'load_avg_15m': load_avg[2]
            }
        except Exception as e:
            logger.error(f"获取系统信息失败: {e}")
            return {}