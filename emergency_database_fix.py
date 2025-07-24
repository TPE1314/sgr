#!/usr/bin/env python3
"""
紧急数据库修复脚本
专门解决 "ModuleNotFoundError: No module named 'database'" 问题
"""

import sys
import os
import subprocess

def colored_print(message, color):
    colors = {
        'red': '\033[91m',
        'green': '\033[92m',
        'yellow': '\033[93m',
        'blue': '\033[94m',
        'cyan': '\033[96m',
        'white': '\033[97m',
        'reset': '\033[0m'
    }
    print(f"{colors.get(color, '')}{message}{colors['reset']}")

def emergency_fix():
    colored_print("🚨 紧急数据库修复工具", "red")
    colored_print("=" * 50, "cyan")
    
    # 1. 检查当前目录
    current_dir = os.getcwd()
    colored_print(f"📁 当前工作目录: {current_dir}", "blue")
    
    # 2. 检查database.py文件
    database_py = os.path.join(current_dir, 'database.py')
    if not os.path.exists(database_py):
        colored_print("❌ database.py 文件不存在！", "red")
        colored_print("请确保在项目根目录中运行此脚本", "yellow")
        return False
    
    colored_print("✅ database.py 文件存在", "green")
    
    # 3. 强制设置Python路径
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)
        colored_print(f"✅ 已添加 {current_dir} 到 sys.path", "green")
    
    # 4. 设置环境变量
    os.environ['PYTHONPATH'] = f"{os.environ.get('PYTHONPATH', '')}:{current_dir}"
    colored_print("✅ 已设置 PYTHONPATH 环境变量", "green")
    
    # 5. 测试模块导入
    colored_print("🔍 测试数据库模块导入...", "yellow")
    try:
        # 清除已加载的模块缓存
        if 'database' in sys.modules:
            del sys.modules['database']
        
        # 重新导入
        import importlib.util
        spec = importlib.util.spec_from_file_location("database", database_py)
        database_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(database_module)
        
        # 测试DatabaseManager类
        DatabaseManager = database_module.DatabaseManager
        test_db = DatabaseManager(':memory:')
        
        colored_print("✅ 数据库模块导入成功", "green")
        return True
        
    except Exception as e:
        colored_print(f"❌ 数据库模块导入失败: {e}", "red")
        return False

def run_database_initialization():
    colored_print("🔧 开始数据库初始化...", "yellow")
    
    try:
        # 确保当前目录在Python路径中
        current_dir = os.getcwd()
        if current_dir not in sys.path:
            sys.path.insert(0, current_dir)
        
        # 导入并初始化数据库
        from database import DatabaseManager
        
        colored_print("[INFO] 初 始 化 数 据 库 表 ...", "cyan")
        
        # 创建数据库实例
        db = DatabaseManager('telegram_bot.db')
        colored_print("✅ 主数据库初始化完成", "green")
        
        # 创建必要目录
        directories = ['logs', 'pids', 'backups', 'temp']
        for directory in directories:
            os.makedirs(directory, exist_ok=True)
        colored_print("✅ 必要目录创建完成", "green")
        
        colored_print("🎉 数据库初始化完全成功！", "green")
        return True
        
    except ImportError as e:
        colored_print(f"❌ 导入错误: {e}", "red")
        colored_print("🔧 尝试替代修复方案...", "yellow")
        return alternative_fix()
    except Exception as e:
        colored_print(f"❌ 初始化错误: {e}", "red")
        return False

def alternative_fix():
    """替代修复方案"""
    colored_print("🔄 执行替代修复方案...", "yellow")
    
    try:
        # 方案1: 使用subprocess执行
        cmd = [
            sys.executable, '-c',
            '''
import sys
import os
sys.path.insert(0, os.getcwd())
from database import DatabaseManager
print("[INFO] 初 始 化 数 据 库 表 ...")
db = DatabaseManager("telegram_bot.db")
print("[SUCCESS] 数据库初始化完成")
'''
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=os.getcwd())
        
        if result.returncode == 0:
            colored_print("✅ 替代方案成功", "green")
            colored_print(result.stdout, "cyan")
            return True
        else:
            colored_print(f"❌ 替代方案失败: {result.stderr}", "red")
            return False
            
    except Exception as e:
        colored_print(f"❌ 替代方案执行错误: {e}", "red")
        return False

def provide_manual_solutions():
    """提供手动解决方案"""
    colored_print("🛠️ 手动解决方案:", "yellow")
    colored_print("=" * 50, "cyan")
    
    current_dir = os.getcwd()
    
    solutions = [
        "1. 手动设置Python路径:",
        f"   export PYTHONPATH=$PYTHONPATH:{current_dir}",
        "",
        "2. 使用完整路径运行:",
        f"   cd {current_dir}",
        "   python3 -c \"import sys; sys.path.insert(0, '.'); from database import DatabaseManager; db = DatabaseManager('telegram_bot.db')\"",
        "",
        "3. 检查Python版本:",
        "   python3 --version",
        "   which python3",
        "",
        "4. 重新下载项目:",
        "   git clone https://github.com/TPE1314/sgr.git",
        "   cd sgr",
        "",
        "5. 创建虚拟环境:",
        "   python3 -m venv venv",
        "   source venv/bin/activate",
        "   pip install python-telegram-bot",
        "",
        "6. 直接运行修复工具:",
        "   ./quick_fix_database.sh",
        "",
        "7. 一键修复命令:",
        f"   cd {current_dir} && export PYTHONPATH=$PYTHONPATH:$(pwd) && python3 -c \"from database import DatabaseManager; print('修复成功!')\"",
    ]
    
    for solution in solutions:
        if solution.startswith("   "):
            colored_print(solution, "cyan")
        elif solution.startswith(("1.", "2.", "3.", "4.", "5.", "6.", "7.")):
            colored_print(solution, "yellow")
        else:
            print(solution)

def main():
    colored_print("🚨 紧急数据库问题修复", "red")
    colored_print("专门解决: ModuleNotFoundError: No module named 'database'", "yellow")
    print()
    
    # 步骤1: 紧急修复
    if emergency_fix():
        colored_print("✅ 紧急修复成功", "green")
        print()
        
        # 步骤2: 数据库初始化
        if run_database_initialization():
            colored_print("🎉 问题完全解决！", "green")
            colored_print("现在可以正常使用数据库功能", "cyan")
            return
    
    # 如果自动修复失败，提供手动方案
    colored_print("❌ 自动修复失败", "red")
    print()
    provide_manual_solutions()

if __name__ == "__main__":
    main()