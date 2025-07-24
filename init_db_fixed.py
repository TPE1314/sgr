#!/usr/bin/env python3
"""
修复版数据库初始化脚本
解决ModuleNotFoundError: No module named 'database'问题
"""

import sys
import os

def setup_python_path():
    """设置Python路径"""
    # 获取当前目录
    current_dir = os.getcwd()
    
    # 可能的项目目录
    project_dirs = [
        current_dir,
        '/root/sgr',
        '.',
        os.path.abspath('.'),
        os.path.dirname(os.path.abspath(__file__))
    ]
    
    # 添加到sys.path
    for path in project_dirs:
        if path and os.path.exists(path) and path not in sys.path:
            sys.path.insert(0, path)
    
    # 设置PYTHONPATH环境变量
    pythonpath = os.environ.get('PYTHONPATH', '')
    valid_paths = [p for p in project_dirs if p and os.path.exists(p)]
    os.environ['PYTHONPATH'] = ':'.join(valid_paths + [pythonpath]).strip(':')
    
    print(f"[INFO] Python路径已设置: {sys.path[:3]}")

def init_database():
    """初始化数据库"""
    print("[INFO] 初始化数据库表...")
    
    try:
        # 设置路径
        setup_python_path()
        
        # 清理模块缓存
        for module in list(sys.modules.keys()):
            if module.startswith('database'):
                del sys.modules[module]
        
        # 导入数据库模块
        from database import DatabaseManager
        print("[SUCCESS] database模块导入成功")
        
        # 初始化数据库
        db_file = 'telegram_bot.db'
        db = DatabaseManager(db_file)
        print(f"[SUCCESS] 数据库初始化完成: {db_file}")
        
        # 创建必要的目录
        dirs = ['logs', 'pids', 'backups', 'temp']
        for dir_name in dirs:
            os.makedirs(dir_name, exist_ok=True)
        print(f"[SUCCESS] 目录创建完成: {', '.join(dirs)}")
        
        return True
        
    except ImportError as e:
        print(f"[ERROR] 模块导入失败: {e}")
        print("[INFO] 可能的解决方案:")
        print("1. 检查database.py文件是否存在")
        print("2. 确保在正确的工作目录中")
        print("3. 检查Python路径设置")
        return False
    except Exception as e:
        print(f"[ERROR] 数据库初始化失败: {e}")
        return False

if __name__ == "__main__":
    success = init_database()
    if success:
        print("🎉 数据库功能正常，问题已彻底解决!")
    else:
        print("❌ 数据库初始化失败")
    
    sys.exit(0 if success else 1)