#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import subprocess
import asyncio
import logging
import shutil
import hashlib
import json
from typing import Dict, List, Tuple, Optional
from datetime import datetime
from database import DatabaseManager
from config_manager import ConfigManager

logger = logging.getLogger(__name__)

class UpdateService:
    def __init__(self):
        self.config = ConfigManager()
        self.db = DatabaseManager(self.config.get_db_file())
        self.backup_dir = "backups"
        self.update_log_file = "update.log"
        
    def get_current_version(self) -> str:
        """获取当前版本信息"""
        try:
            # 优先使用.version文件
            if os.path.exists('.version'):
                with open('.version', 'r', encoding='utf-8') as f:
                    version = f.read().strip()
                    if version:
                        return version
            
            # 如果没有版本文件，使用固定版本号
            return "v2.3.0"
        except Exception as e:
            logger.error(f"获取版本信息失败: {e}")
            return "v2.3.0"
    
    def set_version(self, version: str) -> bool:
        """设置版本信息"""
        try:
            with open('.version', 'w', encoding='utf-8') as f:
                f.write(version)
            return True
        except Exception as e:
            logger.error(f"设置版本信息失败: {e}")
            return False
    
    def create_backup(self) -> Tuple[bool, str]:
        """创建系统备份"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = os.path.join(self.backup_dir, f"backup_{timestamp}")
            
            # 创建备份目录
            os.makedirs(backup_path, exist_ok=True)
            
            # 需要备份的文件列表
            backup_files = [
                "*.py",
                "*.ini", 
                "*.sh",
                "*.txt",
                "*.md",
                "telegram_bot.db"
            ]
            
            backup_count = 0
            for pattern in backup_files:
                files = subprocess.run(
                    f"ls {pattern} 2>/dev/null || true", 
                    shell=True, 
                    capture_output=True, 
                    text=True
                ).stdout.strip().split('\n')
                
                for file in files:
                    if file and os.path.exists(file):
                        try:
                            shutil.copy2(file, backup_path)
                            backup_count += 1
                        except Exception as e:
                            logger.warning(f"备份文件 {file} 失败: {e}")
            
            # 记录备份信息
            backup_info = {
                "timestamp": timestamp,
                "version": self.get_current_version(),
                "files_count": backup_count,
                "backup_path": backup_path
            }
            
            with open(os.path.join(backup_path, "backup_info.json"), 'w', encoding='utf-8') as f:
                json.dump(backup_info, f, indent=2, ensure_ascii=False)
            
            logger.info(f"备份创建成功: {backup_path} ({backup_count} 个文件)")
            return True, f"备份创建成功: {backup_path}"
            
        except Exception as e:
            logger.error(f"创建备份失败: {e}")
            return False, f"创建备份失败: {str(e)}"
    
    def get_backup_list(self) -> List[Dict]:
        """获取备份列表"""
        backups = []
        try:
            if not os.path.exists(self.backup_dir):
                return backups
            
            for item in os.listdir(self.backup_dir):
                backup_path = os.path.join(self.backup_dir, item)
                if os.path.isdir(backup_path):
                    info_file = os.path.join(backup_path, "backup_info.json")
                    if os.path.exists(info_file):
                        try:
                            with open(info_file, 'r', encoding='utf-8') as f:
                                backup_info = json.load(f)
                                backup_info['name'] = item
                                backups.append(backup_info)
                        except Exception as e:
                            logger.warning(f"读取备份信息失败 {info_file}: {e}")
            
            # 按时间排序
            backups.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
            
        except Exception as e:
            logger.error(f"获取备份列表失败: {e}")
        
        return backups
    
    async def update_from_git(self, repo_url: str = None, branch: str = "main") -> Tuple[bool, str]:
        """从Git仓库更新代码"""
        try:
            # 检查是否是Git仓库
            if not os.path.exists('.git'):
                if not repo_url:
                    return False, "不是Git仓库且未提供仓库URL"
                
                # 初始化Git仓库
                result = await self._run_command(f"git clone {repo_url} temp_repo")
                if not result[0]:
                    return False, f"克隆仓库失败: {result[1]}"
                
                # 复制文件
                result = await self._run_command("cp -r temp_repo/* . && rm -rf temp_repo")
                if not result[0]:
                    return False, f"复制文件失败: {result[1]}"
                
                return True, "从Git仓库初始化成功"
            
            # 检查是否有未提交的更改
            result = await self._run_command("git status --porcelain")
            if result[0] and result[1].strip():
                # 有未提交的更改，先备份
                backup_result = self.create_backup()
                if not backup_result[0]:
                    return False, f"备份失败: {backup_result[1]}"
            
            # 清理可能冲突的临时文件（日志文件等）
            cleanup_files = [
                "*.log",
                "logs/*.log", 
                "pids/*.pid",
                "temp/*"
            ]
            for pattern in cleanup_files:
                await self._run_command(f"rm -f {pattern} 2>/dev/null || true")
            
            # 拉取最新代码
            result = await self._run_command(f"git fetch origin {branch}")
            if not result[0]:
                return False, f"拉取代码失败: {result[1]}"
            
            # 检查是否有更新
            result = await self._run_command(f"git rev-list HEAD...origin/{branch} --count")
            if result[0] and result[1].strip() == "0":
                return True, "代码已是最新版本，无需更新"
            
            # 重置未跟踪文件以避免冲突
            await self._run_command("git clean -fd")
            
            # 合并最新代码
            result = await self._run_command(f"git merge origin/{branch}")
            if not result[0]:
                # 如果还是失败，尝试强制合并
                await self._run_command("git reset --hard HEAD")
                result = await self._run_command(f"git merge origin/{branch}")
                if not result[0]:
                    return False, f"合并代码失败: {result[1]}"
            
            # 获取最新提交信息
            result = await self._run_command("git log -1 --pretty=format:'%h - %s (%an, %ar)'")
            commit_info = result[1] if result[0] else "未知"
            
            logger.info(f"Git更新成功: {commit_info}")
            return True, f"Git更新成功: {commit_info}"
            
        except Exception as e:
            logger.error(f"Git更新失败: {e}")
            return False, f"Git更新失败: {str(e)}"
    
    async def update_dependencies(self) -> Tuple[bool, str]:
        """更新Python依赖"""
        try:
            # 检查requirements.txt是否存在
            if not os.path.exists('requirements.txt'):
                return True, "requirements.txt不存在，跳过依赖更新"
            
            # 更新pip
            result = await self._run_command("python3 -m pip install --upgrade pip")
            if not result[0]:
                logger.warning(f"升级pip失败: {result[1]}")
            
            # 安装/更新依赖
            result = await self._run_command("pip3 install -r requirements.txt --upgrade")
            if not result[0]:
                return False, f"更新依赖失败: {result[1]}"
            
            logger.info("依赖更新成功")
            return True, "依赖更新成功"
            
        except Exception as e:
            logger.error(f"更新依赖失败: {e}")
            return False, f"更新依赖失败: {str(e)}"
    
    async def restart_system(self, exclude_control: bool = True) -> Tuple[bool, str]:
        """重启系统（排除控制机器人）"""
        try:
            from hot_update_service import HotUpdateService
            hot_update = HotUpdateService()
            
            results = []
            
            # 停止其他机器人
            if exclude_control:
                bots_to_restart = ['submission', 'publish']
            else:
                bots_to_restart = ['submission', 'publish', 'control']
            
            # 先停止所有机器人
            for bot_name in bots_to_restart:
                if bot_name == 'control' and exclude_control:
                    continue
                    
                success, msg = await hot_update.stop_bot(bot_name)
                results.append(f"停止{hot_update.bot_configs[bot_name]['name']}: {msg}")
            
            # 等待一下
            await asyncio.sleep(3)
            
            # 重新启动机器人
            for bot_name in bots_to_restart:
                if bot_name == 'control' and exclude_control:
                    continue
                    
                success, msg = await hot_update.start_bot(bot_name)
                results.append(f"启动{hot_update.bot_configs[bot_name]['name']}: {msg}")
                await asyncio.sleep(2)
            
            result_text = "\n".join(results)
            logger.info(f"系统重启完成:\n{result_text}")
            return True, f"系统重启完成:\n{result_text}"
            
        except Exception as e:
            logger.error(f"系统重启失败: {e}")
            return False, f"系统重启失败: {str(e)}"
    
    async def full_update(self, repo_url: str = None, branch: str = "main") -> Tuple[bool, str]:
        """完整更新流程"""
        update_steps = []
        
        try:
            # 记录更新开始
            start_time = datetime.now()
            current_version = self.get_current_version()
            
            update_steps.append(f"🔄 开始更新 (当前版本: {current_version})")
            
            # 1. 创建备份
            update_steps.append("📦 创建系统备份...")
            backup_success, backup_msg = self.create_backup()
            if not backup_success:
                update_steps.append(f"❌ 备份失败: {backup_msg}")
                return False, "\n".join(update_steps)
            update_steps.append(f"✅ {backup_msg}")
            
            # 2. 更新代码
            if repo_url or os.path.exists('.git'):
                update_steps.append("📥 更新代码...")
                git_success, git_msg = await self.update_from_git(repo_url, branch)
                if not git_success:
                    update_steps.append(f"❌ 代码更新失败: {git_msg}")
                    return False, "\n".join(update_steps)
                update_steps.append(f"✅ {git_msg}")
            else:
                update_steps.append("⏭️ 跳过代码更新 (非Git仓库)")
            
            # 3. 更新依赖
            update_steps.append("📚 更新依赖...")
            dep_success, dep_msg = await self.update_dependencies()
            if not dep_success:
                update_steps.append(f"❌ 依赖更新失败: {dep_msg}")
                return False, "\n".join(update_steps)
            update_steps.append(f"✅ {dep_msg}")
            
            # 4. 重启系统
            update_steps.append("🔄 重启系统...")
            restart_success, restart_msg = await self.restart_system()
            if not restart_success:
                update_steps.append(f"❌ 系统重启失败: {restart_msg}")
                return False, "\n".join(update_steps)
            update_steps.append(f"✅ 系统重启成功")
            
            # 5. 更新版本信息
            new_version = f"v1.0.{datetime.now().strftime('%Y%m%d_%H%M')}"
            self.set_version(new_version)
            
            # 记录更新完成
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            update_steps.append(f"🎉 更新完成! 新版本: {new_version}")
            update_steps.append(f"⏱️ 耗时: {duration:.1f}秒")
            
            # 记录到数据库
            self.db.set_config('last_update_time', end_time.isoformat(), 0)
            self.db.set_config('last_update_version', new_version, 0)
            
            # 写入更新日志
            self._write_update_log(update_steps, True)
            
            logger.info(f"完整更新成功: {new_version}")
            return True, "\n".join(update_steps)
            
        except Exception as e:
            error_msg = f"❌ 更新过程中发生错误: {str(e)}"
            update_steps.append(error_msg)
            self._write_update_log(update_steps, False)
            logger.error(f"完整更新失败: {e}")
            return False, "\n".join(update_steps)
    
    async def rollback_to_backup(self, backup_name: str) -> Tuple[bool, str]:
        """回滚到指定备份"""
        try:
            backup_path = os.path.join(self.backup_dir, backup_name)
            if not os.path.exists(backup_path):
                return False, f"备份不存在: {backup_name}"
            
            # 读取备份信息
            info_file = os.path.join(backup_path, "backup_info.json")
            if os.path.exists(info_file):
                with open(info_file, 'r', encoding='utf-8') as f:
                    backup_info = json.load(f)
                    backup_version = backup_info.get('version', 'unknown')
            else:
                backup_version = 'unknown'
            
            # 创建当前状态的备份
            current_backup = self.create_backup()
            if not current_backup[0]:
                logger.warning(f"创建当前备份失败: {current_backup[1]}")
            
            # 停止所有机器人
            from hot_update_service import HotUpdateService
            hot_update = HotUpdateService()
            await hot_update.stop_all_bots()
            
            # 复制备份文件
            result = await self._run_command(f"cp -r {backup_path}/* .")
            if not result[0]:
                return False, f"恢复文件失败: {result[1]}"
            
            # 删除备份信息文件（避免覆盖当前目录）
            if os.path.exists("backup_info.json"):
                os.remove("backup_info.json")
            
            # 设置版本信息
            self.set_version(backup_version)
            
            # 重启系统
            restart_result = await self.restart_system()
            
            logger.info(f"回滚到备份 {backup_name} 成功")
            return True, f"回滚到备份 {backup_name} 成功 (版本: {backup_version})"
            
        except Exception as e:
            logger.error(f"回滚失败: {e}")
            return False, f"回滚失败: {str(e)}"
    
    def _write_update_log(self, steps: List[str], success: bool):
        """写入更新日志"""
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            status = "SUCCESS" if success else "FAILED"
            
            log_entry = f"\n[{timestamp}] UPDATE {status}\n"
            log_entry += "\n".join(steps)
            log_entry += "\n" + "="*50 + "\n"
            
            with open(self.update_log_file, 'a', encoding='utf-8') as f:
                f.write(log_entry)
                
        except Exception as e:
            logger.error(f"写入更新日志失败: {e}")
    
    async def _run_command(self, command: str, timeout: int = 300) -> Tuple[bool, str]:
        """执行命令"""
        try:
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(
                process.communicate(), 
                timeout=timeout
            )
            
            stdout_text = stdout.decode('utf-8') if stdout else ""
            stderr_text = stderr.decode('utf-8') if stderr else ""
            
            if process.returncode == 0:
                return True, stdout_text
            else:
                return False, stderr_text or stdout_text
                
        except asyncio.TimeoutError:
            return False, f"命令执行超时 (>{timeout}秒)"
        except Exception as e:
            return False, f"命令执行失败: {str(e)}"
    
    def get_update_status(self) -> Dict:
        """获取更新状态信息"""
        try:
            status = {
                'current_version': self.get_current_version(),
                'last_update': self.db.get_config('last_update_time'),
                'last_version': self.db.get_config('last_update_version'),
                'backup_count': len(self.get_backup_list()),
                'is_git_repo': os.path.exists('.git'),
                'has_requirements': os.path.exists('requirements.txt'),
                'update_log_exists': os.path.exists(self.update_log_file)
            }
            
            # 检查是否有Git更新
            if status['is_git_repo']:
                try:
                    result = subprocess.run(
                        "git fetch && git rev-list HEAD...origin/main --count", 
                        shell=True, 
                        capture_output=True, 
                        text=True,
                        timeout=10
                    )
                    if result.returncode == 0:
                        behind_count = int(result.stdout.strip() or "0")
                        status['git_behind_count'] = behind_count
                        status['has_updates'] = behind_count > 0
                    else:
                        status['git_behind_count'] = -1
                        status['has_updates'] = False
                except:
                    status['git_behind_count'] = -1
                    status['has_updates'] = False
            else:
                status['git_behind_count'] = 0
                status['has_updates'] = False
            
            return status
            
        except Exception as e:
            logger.error(f"获取更新状态失败: {e}")
            return {}