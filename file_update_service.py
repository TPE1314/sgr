#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import shutil
import tempfile
import zipfile
import tarfile
import logging
import hashlib
import json
from typing import Dict, List, Tuple, Optional
from datetime import datetime
from pathlib import Path
from database import DatabaseManager
from config_manager import ConfigManager
from update_service import UpdateService

logger = logging.getLogger(__name__)

class FileUpdateService:
    def __init__(self):
        self.config = ConfigManager()
        self.db = DatabaseManager(self.config.get_db_file())
        self.update_service = UpdateService()
        self.temp_dir = "temp_updates"
        self.allowed_extensions = {'.py', '.ini', '.txt', '.md', '.sh', '.json', '.yml', '.yaml'}
        self.protected_files = {'telegram_bot.db', '.version'}
        
    def validate_file(self, file_path: str, file_name: str) -> Tuple[bool, str]:
        """验证上传的文件"""
        try:
            # 检查文件扩展名
            file_ext = Path(file_name).suffix.lower()
            if file_ext not in self.allowed_extensions:
                return False, f"不支持的文件类型: {file_ext}"
            
            # 检查文件大小 (最大5MB)
            file_size = os.path.getsize(file_path)
            if file_size > 5 * 1024 * 1024:
                return False, f"文件过大: {file_size / 1024 / 1024:.1f}MB (最大5MB)"
            
            # 检查是否是受保护的文件
            if file_name in self.protected_files:
                return False, f"受保护的文件不能替换: {file_name}"
            
            # 对于Python文件，进行语法检查
            if file_ext == '.py':
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        code = f.read()
                    compile(code, file_name, 'exec')
                except SyntaxError as e:
                    return False, f"Python语法错误: {e}"
                except UnicodeDecodeError:
                    return False, "文件编码错误，请使用UTF-8编码"
            
            return True, "文件验证通过"
            
        except Exception as e:
            logger.error(f"文件验证失败: {e}")
            return False, f"文件验证失败: {str(e)}"
    
    def analyze_file_changes(self, file_path: str, target_name: str) -> Dict:
        """分析文件变更"""
        try:
            analysis = {
                'file_name': target_name,
                'file_size': os.path.getsize(file_path),
                'file_type': Path(target_name).suffix.lower(),
                'exists': os.path.exists(target_name),
                'changes': [],
                'risks': [],
                'recommendations': []
            }
            
            # 如果目标文件存在，比较差异
            if analysis['exists']:
                try:
                    # 比较文件大小
                    old_size = os.path.getsize(target_name)
                    size_diff = analysis['file_size'] - old_size
                    analysis['changes'].append(f"文件大小: {old_size} -> {analysis['file_size']} ({size_diff:+d} bytes)")
                    
                    # 比较文件哈希
                    old_hash = self._get_file_hash(target_name)
                    new_hash = self._get_file_hash(file_path)
                    
                    if old_hash == new_hash:
                        analysis['changes'].append("文件内容相同，无需更新")
                    else:
                        analysis['changes'].append("文件内容已修改")
                        
                        # 对于Python文件，检查导入和函数
                        if analysis['file_type'] == '.py':
                            self._analyze_python_changes(target_name, file_path, analysis)
                            
                except Exception as e:
                    analysis['changes'].append(f"无法比较差异: {e}")
            else:
                analysis['changes'].append("新文件")
            
            # 风险评估
            self._assess_risks(target_name, analysis)
            
            # 生成建议
            self._generate_recommendations(analysis)
            
            return analysis
            
        except Exception as e:
            logger.error(f"分析文件变更失败: {e}")
            return {'error': str(e)}
    
    def _get_file_hash(self, file_path: str) -> str:
        """获取文件哈希值"""
        hasher = hashlib.md5()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hasher.update(chunk)
        return hasher.hexdigest()
    
    def _analyze_python_changes(self, old_file: str, new_file: str, analysis: Dict):
        """分析Python文件的变更"""
        try:
            import ast
            
            def get_python_info(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    tree = ast.parse(f.read())
                
                imports = []
                functions = []
                classes = []
                
                for node in ast.walk(tree):
                    if isinstance(node, (ast.Import, ast.ImportFrom)):
                        if isinstance(node, ast.Import):
                            imports.extend([alias.name for alias in node.names])
                        else:
                            imports.append(node.module or '')
                    elif isinstance(node, ast.FunctionDef):
                        functions.append(node.name)
                    elif isinstance(node, ast.ClassDef):
                        classes.append(node.name)
                
                return imports, functions, classes
            
            old_imports, old_functions, old_classes = get_python_info(old_file)
            new_imports, new_functions, new_classes = get_python_info(new_file)
            
            # 分析导入变更
            added_imports = set(new_imports) - set(old_imports)
            removed_imports = set(old_imports) - set(new_imports)
            
            if added_imports:
                analysis['changes'].append(f"新增导入: {', '.join(added_imports)}")
            if removed_imports:
                analysis['changes'].append(f"移除导入: {', '.join(removed_imports)}")
            
            # 分析函数变更
            added_functions = set(new_functions) - set(old_functions)
            removed_functions = set(old_functions) - set(new_functions)
            
            if added_functions:
                analysis['changes'].append(f"新增函数: {', '.join(added_functions)}")
            if removed_functions:
                analysis['changes'].append(f"移除函数: {', '.join(removed_functions)}")
                analysis['risks'].append("移除函数可能影响其他模块")
            
            # 分析类变更
            added_classes = set(new_classes) - set(old_classes)
            removed_classes = set(old_classes) - set(new_classes)
            
            if added_classes:
                analysis['changes'].append(f"新增类: {', '.join(added_classes)}")
            if removed_classes:
                analysis['changes'].append(f"移除类: {', '.join(removed_classes)}")
                analysis['risks'].append("移除类可能影响其他模块")
                
        except Exception as e:
            analysis['changes'].append(f"Python代码分析失败: {e}")
    
    def _assess_risks(self, target_name: str, analysis: Dict):
        """风险评估"""
        file_name = Path(target_name).name
        
        # 核心文件风险评估
        core_files = {
            'database.py': '数据库操作文件，修改可能影响数据安全',
            'config_manager.py': '配置管理文件，修改可能影响系统稳定性',
            'submission_bot.py': '投稿机器人主文件，修改需重启生效',
            'publish_bot.py': '发布机器人主文件，修改需重启生效',
            'control_bot.py': '控制机器人主文件，修改需重启生效',
            'config.ini': '配置文件，修改需重启生效'
        }
        
        if file_name in core_files:
            analysis['risks'].append(core_files[file_name])
        
        # 文件类型风险评估
        if analysis['file_type'] == '.py':
            analysis['risks'].append("Python文件修改需要重启相关机器人")
        elif analysis['file_type'] == '.ini':
            analysis['risks'].append("配置文件修改需要重启机器人")
        elif analysis['file_type'] == '.sh':
            analysis['risks'].append("脚本文件修改可能影响系统操作")
    
    def _generate_recommendations(self, analysis: Dict):
        """生成建议"""
        file_name = Path(analysis['file_name']).name
        
        # 根据文件类型生成建议
        if analysis['file_type'] == '.py':
            analysis['recommendations'].append("建议在更新后重启相关机器人")
            analysis['recommendations'].append("建议先在测试环境验证")
        
        if file_name.endswith('_bot.py'):
            analysis['recommendations'].append("机器人文件更新后需要重启该机器人")
        
        if analysis['file_name'] == 'config.ini':
            analysis['recommendations'].append("配置文件更新后需要重启所有机器人")
        
        if not analysis['exists']:
            analysis['recommendations'].append("这是新文件，请确认文件位置正确")
        
        if analysis.get('risks'):
            analysis['recommendations'].append("存在风险，建议先创建备份")
    
    async def update_single_file(self, file_path: str, target_name: str, user_id: int) -> Tuple[bool, str]:
        """更新单个文件"""
        try:
            # 验证文件
            valid, msg = self.validate_file(file_path, target_name)
            if not valid:
                return False, msg
            
            # 创建备份
            backup_success, backup_msg = self.update_service.create_backup()
            if not backup_success:
                logger.warning(f"备份失败: {backup_msg}")
            
            # 如果目标文件存在，备份原文件
            if os.path.exists(target_name):
                backup_name = f"{target_name}.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                shutil.copy2(target_name, backup_name)
                logger.info(f"原文件已备份为: {backup_name}")
            
            # 复制新文件
            shutil.copy2(file_path, target_name)
            
            # 记录更新操作
            update_info = {
                'file_name': target_name,
                'updated_by': user_id,
                'update_time': datetime.now().isoformat(),
                'file_size': os.path.getsize(target_name),
                'file_hash': self._get_file_hash(target_name)
            }
            
            self.db.set_config(f'file_update_{target_name}', json.dumps(update_info), user_id)
            
            logger.info(f"文件更新成功: {target_name} (用户: {user_id})")
            return True, f"文件 {target_name} 更新成功"
            
        except Exception as e:
            logger.error(f"文件更新失败: {e}")
            return False, f"文件更新失败: {str(e)}"
    
    async def extract_and_update_archive(self, file_path: str, user_id: int) -> Tuple[bool, str]:
        """解压并更新压缩包中的文件"""
        try:
            # 创建临时目录
            os.makedirs(self.temp_dir, exist_ok=True)
            extract_dir = os.path.join(self.temp_dir, f"extract_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
            os.makedirs(extract_dir)
            
            # 根据文件类型解压
            if file_path.endswith('.zip'):
                with zipfile.ZipFile(file_path, 'r') as zip_ref:
                    zip_ref.extractall(extract_dir)
            elif file_path.endswith(('.tar', '.tar.gz', '.tgz')):
                with tarfile.open(file_path, 'r') as tar_ref:
                    tar_ref.extractall(extract_dir)
            else:
                return False, "不支持的压缩格式"
            
            # 创建系统备份
            backup_success, backup_msg = self.update_service.create_backup()
            if not backup_success:
                logger.warning(f"系统备份失败: {backup_msg}")
            
            # 分析并更新文件
            updated_files = []
            failed_files = []
            
            for root, dirs, files in os.walk(extract_dir):
                for file in files:
                    source_path = os.path.join(root, file)
                    relative_path = os.path.relpath(source_path, extract_dir)
                    
                    # 验证文件
                    valid, msg = self.validate_file(source_path, relative_path)
                    if not valid:
                        failed_files.append(f"{relative_path}: {msg}")
                        continue
                    
                    # 更新文件
                    success, result = await self.update_single_file(source_path, relative_path, user_id)
                    if success:
                        updated_files.append(relative_path)
                    else:
                        failed_files.append(f"{relative_path}: {result}")
            
            # 清理临时文件
            shutil.rmtree(extract_dir)
            
            # 生成结果报告
            result_msg = f"压缩包处理完成\n"
            result_msg += f"✅ 成功更新: {len(updated_files)} 个文件\n"
            result_msg += f"❌ 失败: {len(failed_files)} 个文件\n"
            
            if updated_files:
                result_msg += f"\n📝 已更新文件:\n" + "\n".join(f"• {f}" for f in updated_files)
            
            if failed_files:
                result_msg += f"\n⚠️ 失败文件:\n" + "\n".join(f"• {f}" for f in failed_files)
            
            success = len(updated_files) > 0
            return success, result_msg
            
        except Exception as e:
            logger.error(f"压缩包处理失败: {e}")
            return False, f"压缩包处理失败: {str(e)}"
        finally:
            # 确保清理临时文件
            if os.path.exists(extract_dir):
                shutil.rmtree(extract_dir, ignore_errors=True)
    
    def get_update_history(self, limit: int = 10) -> List[Dict]:
        """获取文件更新历史"""
        try:
            # 从数据库获取更新记录
            cursor = self.db.conn.cursor()
            cursor.execute("""
                SELECT config_key, config_value, updated_by, updated_time 
                FROM system_config 
                WHERE config_key LIKE 'file_update_%' 
                ORDER BY updated_time DESC 
                LIMIT ?
            """, (limit,))
            
            records = cursor.fetchall()
            history = []
            
            for record in records:
                try:
                    file_name = record[0].replace('file_update_', '')
                    update_info = json.loads(record[1])
                    update_info['file_name'] = file_name
                    update_info['updated_by'] = record[2]
                    update_info['updated_time'] = record[3]
                    history.append(update_info)
                except:
                    continue
            
            return history
            
        except Exception as e:
            logger.error(f"获取更新历史失败: {e}")
            return []
    
    def suggest_restart_bots(self, updated_files: List[str]) -> List[str]:
        """建议需要重启的机器人"""
        restart_suggestions = []
        
        bot_file_mapping = {
            'submission_bot.py': 'submission',
            'publish_bot.py': 'publish', 
            'control_bot.py': 'control',
            'database.py': ['submission', 'publish', 'control'],
            'config_manager.py': ['submission', 'publish', 'control'],
            'hot_update_service.py': 'control',
            'update_service.py': 'control',
            'file_update_service.py': 'control',
            'notification_service.py': ['submission', 'publish'],
            'config.ini': ['submission', 'publish', 'control']
        }
        
        bots_to_restart = set()
        
        for file_name in updated_files:
            base_name = Path(file_name).name
            if base_name in bot_file_mapping:
                mapping = bot_file_mapping[base_name]
                if isinstance(mapping, list):
                    bots_to_restart.update(mapping)
                else:
                    bots_to_restart.add(mapping)
        
        return list(bots_to_restart)
    
    def cleanup_temp_files(self):
        """清理临时文件"""
        try:
            if os.path.exists(self.temp_dir):
                # 删除超过1小时的临时文件
                current_time = datetime.now()
                for item in os.listdir(self.temp_dir):
                    item_path = os.path.join(self.temp_dir, item)
                    if os.path.isfile(item_path):
                        file_time = datetime.fromtimestamp(os.path.getctime(item_path))
                        if (current_time - file_time).total_seconds() > 3600:  # 1小时
                            os.remove(item_path)
                            logger.info(f"清理临时文件: {item_path}")
        except Exception as e:
            logger.error(f"清理临时文件失败: {e}")