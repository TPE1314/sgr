#!/usr/bin/env python3
"""
修复数据库模块导入问题
"""

import sys
import os

def fix_database_import():
    """修复数据库导入问题"""
    print("🔧 修复数据库模块导入问题")
    
    # 添加当前目录到Python路径
    current_dir = os.getcwd()
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)
    
    # 添加项目根目录到Python路径
    project_dirs = ['/root/sgr', '.', os.path.abspath('.')]
    for path in project_dirs:
        if path and os.path.exists(path) and path not in sys.path:
            sys.path.insert(0, path)
    
    # 设置PYTHONPATH环境变量
    pythonpath = os.environ.get('PYTHONPATH', '')
    new_paths = [current_dir] + [p for p in project_dirs if p and os.path.exists(p)]
    os.environ['PYTHONPATH'] = ':'.join(new_paths + [pythonpath]).strip(':')
    
    # 清理模块缓存
    for module in list(sys.modules.keys()):
        if module.startswith('database'):
            del sys.modules[module]
    
    print(f"✅ Python路径已添加: {sys.path[:3]}")
    print(f"✅ PYTHONPATH已设置: {os.environ.get('PYTHONPATH', '')[:100]}...")
    
    # 测试导入数据库模块
    try:
        from database import DatabaseManager
        print("✅ database模块导入成功")
        
        # 测试数据库初始化
        db = DatabaseManager('telegram_bot.db')
        print("✅ 数据库初始化成功")
        
        return True
    except Exception as e:
        print(f"❌ 数据库模块导入失败: {e}")
        return False

if __name__ == "__main__":
    success = fix_database_import()
    if success:
        print("🎉 数据库模块问题已修复！")
    else:
        print("❌ 修复失败，需要手动处理")
    sys.exit(0 if success else 1)