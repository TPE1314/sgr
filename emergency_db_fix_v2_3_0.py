#!/usr/bin/env python3
"""
v2.3.0 紧急数据库修复脚本
专门解决 ModuleNotFoundError: No module named 'database' 问题

使用方法:
python3 emergency_db_fix_v2_3_0.py

或直接运行:
./emergency_db_fix_v2_3_0.py
"""

import sys
import os
import importlib.util

def print_header():
    """打印头部信息"""
    print("=" * 60)
    print("🔧 v2.3.0 紧急数据库修复工具")
    print("=" * 60)
    print("专门解决: ModuleNotFoundError: No module named 'database'")
    print()

def check_files():
    """检查必要文件是否存在"""
    print("📁 检查文件状态...")
    
    files_status = {}
    required_files = ['database.py', 'config_manager.py', 'config.ini']
    
    for file in required_files:
        exists = os.path.exists(file)
        files_status[file] = exists
        status = "✅" if exists else "❌"
        print(f"   {status} {file}")
    
    return files_status

def create_database_file():
    """创建database.py文件"""
    print("\n🔧 创建database.py文件...")
    
    database_content = '''import sqlite3
import datetime
import json
from typing import List, Dict, Optional

class DatabaseManager:
    def __init__(self, db_file: str):
        self.db_file = db_file
        self.conn = None
        self.init_database()
    
    def get_connection(self):
        """获取数据库连接"""
        if self.conn is None:
            self.conn = sqlite3.connect(self.db_file)
        return self.conn
    
    def init_database(self):
        """初始化数据库表"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        # 创建投稿表
        cursor.execute(\\\'\\\'\\\'
            CREATE TABLE IF NOT EXISTS submissions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                username TEXT,
                content_type TEXT NOT NULL,
                content TEXT,
                media_file_id TEXT,
                caption TEXT,
                status TEXT DEFAULT 'pending',
                submit_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                review_time TIMESTAMP,
                publish_time TIMESTAMP,
                reviewer_id INTEGER,
                reject_reason TEXT
            )
        \\\'\\\'\\\')
        
        # 创建用户表
        cursor.execute(\\\'\\\'\\\'
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                is_banned BOOLEAN DEFAULT FALSE,
                submission_count INTEGER DEFAULT 0,
                last_submission_time TIMESTAMP,
                registration_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        \\\'\\\'\\\')
        
        # 创建管理员表
        cursor.execute(\\\'\\\'\\\'
            CREATE TABLE IF NOT EXISTS admins (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                permission_level INTEGER DEFAULT 1,
                added_by INTEGER,
                added_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        \\\'\\\'\\\')
        
        # 创建配置表
        cursor.execute(\\\'\\\'\\\'
            CREATE TABLE IF NOT EXISTS config (
                key TEXT PRIMARY KEY,
                value TEXT,
                updated_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        \\\'\\\'\\\')
        
        # 创建广告表
        cursor.execute(\\\'\\\'\\\'
            CREATE TABLE IF NOT EXISTS advertisements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                ad_type TEXT DEFAULT 'text',
                position TEXT DEFAULT 'bottom',
                status TEXT DEFAULT 'active',
                created_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                click_count INTEGER DEFAULT 0
            )
        \\\'\\\'\\\')
        
        conn.commit()
        conn.close()
        print("数据库表初始化完成")
    
    def add_submission(self, user_id: int, username: str, content_type: str, 
                      content: str = None, media_file_id: str = None, caption: str = None) -> int:
        """添加投稿"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute(\\\'\\\'\\\'
            INSERT INTO submissions (user_id, username, content_type, content, media_file_id, caption)
            VALUES (?, ?, ?, ?, ?, ?)
        \\\'\\\'\\\', (user_id, username, content_type, content, media_file_id, caption))
        
        submission_id = cursor.lastrowid
        conn.commit()
        return submission_id
    
    def get_pending_submissions(self) -> List[Dict]:
        """获取待审核投稿"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute(\\\'\\\'\\\'
            SELECT * FROM submissions WHERE status = 'pending' ORDER BY submit_time ASC
        \\\'\\\'\\\')
        
        columns = [description[0] for description in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    def update_submission_status(self, submission_id: int, status: str, reviewer_id: int = None, reject_reason: str = None):
        """更新投稿状态"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if status == 'approved':
            cursor.execute(\\\'\\\'\\\'
                UPDATE submissions SET status = ?, reviewer_id = ?, review_time = CURRENT_TIMESTAMP
                WHERE id = ?
            \\\'\\\'\\\', (status, reviewer_id, submission_id))
        elif status == 'rejected':
            cursor.execute(\\\'\\\'\\\'
                UPDATE submissions SET status = ?, reviewer_id = ?, reject_reason = ?, review_time = CURRENT_TIMESTAMP
                WHERE id = ?
            \\\'\\\'\\\', (status, reviewer_id, reject_reason, submission_id))
        else:
            cursor.execute(\\\'\\\'\\\'
                UPDATE submissions SET status = ? WHERE id = ?
            \\\'\\\'\\\', (status, submission_id))
        
        conn.commit()
    
    def add_user(self, user_id: int, username: str = None, first_name: str = None, last_name: str = None):
        """添加用户"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute(\\\'\\\'\\\'
            INSERT OR REPLACE INTO users (user_id, username, first_name, last_name)
            VALUES (?, ?, ?, ?)
        \\\'\\\'\\\', (user_id, username, first_name, last_name))
        
        conn.commit()
    
    def get_config(self, key: str, default=None):
        """获取配置"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT value FROM config WHERE key = ?', (key,))
        result = cursor.fetchone()
        
        if result:
            return result[0]
        return default
    
    def set_config(self, key: str, value: str):
        """设置配置"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute(\\\'\\\'\\\'
            INSERT OR REPLACE INTO config (key, value, updated_time)
            VALUES (?, ?, CURRENT_TIMESTAMP)
        \\\'\\\'\\\', (key, value))
        
        conn.commit()
'''
    
    try:
        with open('database.py', 'w', encoding='utf-8') as f:
            f.write(database_content)
        print("✅ database.py 文件创建成功")
        return True
    except Exception as e:
        print(f"❌ database.py 文件创建失败: {e}")
        return False

def create_config_manager():
    """创建config_manager.py文件"""
    print("\n🔧 创建config_manager.py文件...")
    
    config_content = '''import configparser
import os
import sys
from typing import List

def fix_import_paths():
    """修复模块导入路径问题"""
    current_dir = os.getcwd()
    project_dirs = [current_dir, '.', os.path.abspath('.')]
    
    for path in project_dirs:
        if path and os.path.exists(path) and path not in sys.path:
            sys.path.insert(0, path)
    
    # 设置PYTHONPATH
    pythonpath = os.environ.get('PYTHONPATH', '')
    new_paths = [p for p in project_dirs if p and os.path.exists(p)]
    os.environ['PYTHONPATH'] = ':'.join(new_paths + [pythonpath]).strip(':')

# 调用修复函数
fix_import_paths()

class ConfigManager:
    def __init__(self, config_file: str = "config.ini"):
        self.config_file = config_file
        self.config = configparser.ConfigParser()
        self.load_config()
    
    def load_config(self):
        """加载配置文件，优先使用本地配置"""
        local_config = "config.local.ini"
        if os.path.exists(local_config):
            self.config.read(local_config, encoding='utf-8')
            print(f"✅ 已加载本地配置文件: {local_config}")
        elif os.path.exists(self.config_file):
            self.config.read(self.config_file, encoding='utf-8')
            print(f"✅ 已加载配置文件: {self.config_file}")
        else:
            raise FileNotFoundError(f"配置文件 {self.config_file} 和 {local_config} 都不存在")
    
    def get(self, section: str, key: str, fallback: str = None) -> str:
        """获取配置值"""
        return self.config.get(section, key, fallback=fallback)
    
    def get_list(self, section: str, key: str, fallback: List[str] = None) -> List[str]:
        """获取列表配置值"""
        value = self.get(section, key)
        if value:
            return [item.strip() for item in value.split(',')]
        return fallback or []
    
    def get_int(self, section: str, key: str, fallback: int = 0) -> int:
        """获取整数配置值"""
        try:
            return self.config.getint(section, key)
        except (ValueError, configparser.NoOptionError, configparser.NoSectionError):
            return fallback
    
    def get_bool(self, section: str, key: str, fallback: bool = False) -> bool:
        """获取布尔配置值"""
        try:
            return self.config.getboolean(section, key)
        except (ValueError, configparser.NoOptionError, configparser.NoSectionError):
            return fallback
    
    def get_db_file(self) -> str:
        """获取数据库文件路径"""
        return self.get('database', 'db_file', 'telegram_bot.db')
'''
    
    try:
        with open('config_manager.py', 'w', encoding='utf-8') as f:
            f.write(config_content)
        print("✅ config_manager.py 文件创建成功")
        return True
    except Exception as e:
        print(f"❌ config_manager.py 文件创建失败: {e}")
        return False

def setup_python_environment():
    """设置Python环境"""
    print("\n🐍 设置Python环境...")
    
    current_dir = os.getcwd()
    paths = [current_dir, '.', os.path.abspath('.')]
    
    for path in paths:
        if path and os.path.exists(path) and path not in sys.path:
            sys.path.insert(0, path)
    
    # 设置PYTHONPATH
    os.environ['PYTHONPATH'] = ':'.join(paths + [os.environ.get('PYTHONPATH', '')]).strip(':')
    
    # 清理模块缓存
    modules_to_clear = []
    for module_name in list(sys.modules.keys()):
        if any(name in module_name for name in ['database', 'config']):
            modules_to_clear.append(module_name)
    
    for module_name in modules_to_clear:
        del sys.modules[module_name]
    
    print(f"✅ Python路径已设置: {len(sys.path)} 个路径")
    if modules_to_clear:
        print(f"✅ 已清理 {len(modules_to_clear)} 个模块缓存")

def test_database_import():
    """测试数据库导入"""
    print("\n🧪 测试数据库导入...")
    
    try:
        # 方法1: 标准导入
        from database import DatabaseManager
        print("✅ 标准导入成功")
        return DatabaseManager
    except ImportError as e:
        print(f"❌ 标准导入失败: {e}")
        
        # 方法2: 文件路径导入
        try:
            print("🔄 尝试文件路径导入...")
            db_path = os.path.join(os.getcwd(), 'database.py')
            if not os.path.exists(db_path):
                raise ImportError(f"database.py文件不存在: {db_path}")
            
            spec = importlib.util.spec_from_file_location("database", db_path)
            database_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(database_module)
            
            print("✅ 文件路径导入成功")
            return database_module.DatabaseManager
        except Exception as e:
            print(f"❌ 文件路径导入失败: {e}")
            return None

def test_database_creation():
    """测试数据库创建"""
    print("\n🗄️ 测试数据库创建...")
    
    try:
        DatabaseManager = test_database_import()
        if not DatabaseManager:
            return False
        
        print("📝 创建数据库实例...")
        db = DatabaseManager('telegram_bot.db')
        print("✅ 数据库创建成功")
        
        # 测试基本操作
        print("🧪 测试基本数据库操作...")
        db.set_config('test_key', 'test_value')
        value = db.get_config('test_key')
        
        if value == 'test_value':
            print("✅ 数据库读写测试通过")
            return True
        else:
            print("❌ 数据库读写测试失败")
            return False
            
    except Exception as e:
        print(f"❌ 数据库测试失败: {e}")
        return False

def create_directories():
    """创建必要的目录"""
    print("\n📁 创建必要目录...")
    
    dirs = ['logs', 'pids', 'backups', 'temp']
    created = []
    
    for dir_name in dirs:
        try:
            os.makedirs(dir_name, exist_ok=True)
            created.append(dir_name)
            print(f"✅ {dir_name}/")
        except Exception as e:
            print(f"❌ {dir_name}/ - {e}")
    
    return len(created) == len(dirs)

def show_final_status():
    """显示最终状态"""
    print("\n" + "=" * 60)
    print("📊 修复结果总结")
    print("=" * 60)
    
    # 检查文件
    files_ok = True
    required_files = ['database.py', 'config_manager.py']
    
    print("📄 文件状态:")
    for file in required_files:
        if os.path.exists(file):
            print(f"   ✅ {file}")
        else:
            print(f"   ❌ {file}")
            files_ok = False
    
    # 检查目录
    print("\n📁 目录状态:")
    dirs = ['logs', 'pids', 'backups', 'temp']
    for dir_name in dirs:
        if os.path.exists(dir_name):
            print(f"   ✅ {dir_name}/")
        else:
            print(f"   ❌ {dir_name}/")
    
    # 检查数据库
    print("\n🗄️ 数据库状态:")
    if os.path.exists('telegram_bot.db'):
        print("   ✅ telegram_bot.db")
    else:
        print("   ❌ telegram_bot.db")
    
    return files_ok

def main():
    """主函数"""
    print_header()
    
    # 1. 检查当前状态
    files_status = check_files()
    
    # 2. 创建缺失的文件
    if not files_status.get('database.py', False):
        if not create_database_file():
            print("❌ 数据库文件创建失败，无法继续")
            return False
    else:
        print("✅ database.py 已存在")
    
    if not files_status.get('config_manager.py', False):
        if not create_config_manager():
            print("❌ 配置管理文件创建失败，无法继续")
            return False
    else:
        print("✅ config_manager.py 已存在")
    
    # 3. 设置Python环境
    setup_python_environment()
    
    # 4. 测试数据库
    if not test_database_creation():
        print("❌ 数据库测试失败")
        return False
    
    # 5. 创建目录
    create_directories()
    
    # 6. 显示最终状态
    success = show_final_status()
    
    if success:
        print("\n🎉 数据库问题修复完成！")
        print("\n💡 现在可以重新运行安装脚本或启动机器人")
        print("   python3 submission_bot.py")
        print("   python3 publish_bot.py")
        print("   python3 control_bot.py")
    else:
        print("\n❌ 修复过程中遇到问题")
        print("💡 建议重新下载完整项目:")
        print("   git clone https://github.com/TPE1314/sgr.git")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)