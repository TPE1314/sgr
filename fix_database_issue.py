#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
数据库问题诊断和修复工具
Database Issue Diagnosis and Fix Tool
"""

import sys
import os
import subprocess
import importlib.util
from pathlib import Path

def print_header(title):
    """打印标题"""
    print("=" * 60)
    print(f"🔧 {title}")
    print("=" * 60)

def print_step(message):
    """打印步骤"""
    print(f"\n📋 {message}")
    print("-" * 40)

def print_success(message):
    """打印成功信息"""
    print(f"✅ {message}")

def print_error(message):
    """打印错误信息"""
    print(f"❌ {message}")

def print_warning(message):
    """打印警告信息"""
    print(f"⚠️  {message}")

def print_info(message):
    """打印信息"""
    print(f"💡 {message}")

def check_environment():
    """检查环境"""
    print_step("环境检查")
    
    # 检查Python版本
    python_version = sys.version_info
    print(f"🐍 Python版本: {python_version.major}.{python_version.minor}.{python_version.micro}")
    
    if python_version < (3, 8):
        print_error("Python版本过低，需要3.8+")
        return False
    else:
        print_success("Python版本符合要求")
    
    # 检查当前工作目录
    current_dir = os.getcwd()
    print(f"📁 当前目录: {current_dir}")
    
    # 检查Python路径
    print(f"🔍 Python路径: {sys.executable}")
    print(f"📦 Python模块路径: {sys.path[:3]}...")  # 只显示前3个
    
    return True

def check_required_files():
    """检查必需文件"""
    print_step("检查必需文件")
    
    required_files = [
        'database.py',
        'config_manager.py',
        'submission_bot.py',
        'publish_bot.py',
        'control_bot.py'
    ]
    
    missing_files = []
    
    for file in required_files:
        if os.path.exists(file):
            print_success(f"{file} 存在")
        else:
            print_error(f"{file} 缺失")
            missing_files.append(file)
    
    if missing_files:
        print_error(f"缺少必需文件: {', '.join(missing_files)}")
        print_info("请确保在正确的项目目录中运行，或重新下载完整项目")
        return False
    
    print_success("所有必需文件检查通过")
    return True

def test_module_import():
    """测试模块导入"""
    print_step("测试模块导入")
    
    # 添加当前目录到Python路径
    current_dir = os.path.abspath('.')
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)
        print_info(f"已添加当前目录到Python路径: {current_dir}")
    
    # 测试导入database模块
    try:
        import database
        print_success("database模块导入成功")
        
        # 测试DatabaseManager类
        try:
            db_manager = database.DatabaseManager(':memory:')
            print_success("DatabaseManager类实例化成功")
            return True
        except Exception as e:
            print_error(f"DatabaseManager类实例化失败: {e}")
            return False
            
    except ImportError as e:
        print_error(f"database模块导入失败: {e}")
        return False
    except Exception as e:
        print_error(f"database模块测试失败: {e}")
        return False

def check_virtual_environment():
    """检查虚拟环境"""
    print_step("虚拟环境检查")
    
    # 检查是否在虚拟环境中
    in_venv = hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)
    
    if in_venv:
        print_success("当前在虚拟环境中")
        print_info(f"虚拟环境路径: {sys.prefix}")
    else:
        print_warning("当前不在虚拟环境中")
        
        # 检查是否存在venv目录
        if os.path.exists('venv'):
            print_info("发现venv目录，建议激活虚拟环境:")
            print("  source venv/bin/activate  # Linux/Mac")
            print("  venv\\Scripts\\activate     # Windows")
        else:
            print_info("建议创建虚拟环境:")
            print("  python3 -m venv venv")
            print("  source venv/bin/activate")
    
    return True

def check_dependencies():
    """检查依赖包"""
    print_step("依赖包检查")
    
    required_packages = [
        'telegram',
        'sqlite3',
        'configparser',
        'psutil'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            if package == 'sqlite3':
                import sqlite3
            elif package == 'configparser':
                import configparser
            elif package == 'telegram':
                import telegram
            elif package == 'psutil':
                import psutil
            
            print_success(f"{package} 可用")
        except ImportError:
            print_error(f"{package} 不可用")
            missing_packages.append(package)
    
    if missing_packages:
        print_error(f"缺少依赖包: {', '.join(missing_packages)}")
        print_info("请安装缺少的依赖包:")
        print("  pip install -r requirements.txt")
        return False
    
    print_success("所有依赖包检查通过")
    return True

def create_simple_test():
    """创建简单测试"""
    print_step("创建简单数据库测试")
    
    try:
        # 添加当前目录到路径
        sys.path.insert(0, os.getcwd())
        
        # 导入并测试
        from database import DatabaseManager
        
        # 创建测试数据库
        test_db = DatabaseManager('test_fix.db')
        print_success("测试数据库创建成功")
        
        # 清理测试文件
        if os.path.exists('test_fix.db'):
            os.remove('test_fix.db')
            print_success("测试文件清理完成")
        
        return True
        
    except Exception as e:
        print_error(f"数据库测试失败: {e}")
        import traceback
        print(traceback.format_exc())
        return False

def provide_solutions():
    """提供解决方案"""
    print_step("解决方案建议")
    
    print("🔧 如果遇到 'No module named database' 错误，请尝试:")
    print()
    print("1. 检查工作目录:")
    print("   pwd  # 确保在项目根目录")
    print("   ls   # 应该看到 database.py 文件")
    print()
    print("2. 激活虚拟环境 (如果使用):")
    print("   source venv/bin/activate")
    print()
    print("3. 使用修复过的脚本:")
    print("   python3 init_database.py")
    print("   # 或")
    print("   python3 test_database_init.py")
    print()
    print("4. 手动设置Python路径:")
    print("   export PYTHONPATH=$PYTHONPATH:$(pwd)")
    print("   python3 -c \"from database import DatabaseManager; print('成功!')\"")
    print()
    print("5. 重新运行一键安装:")
    print("   ./quick_setup.sh")
    print()
    print("6. 如果问题持续，请提供以下信息:")
    print("   - 操作系统版本")
    print("   - Python版本")
    print("   - 错误的完整输出")
    print("   - 当前目录内容 (ls -la)")

def main():
    """主函数"""
    print_header("数据库问题诊断和修复工具")
    
    print("这个工具将帮助诊断和修复 'No module named database' 错误")
    print()
    
    # 执行检查
    checks = [
        ("环境检查", check_environment),
        ("虚拟环境检查", check_virtual_environment), 
        ("必需文件检查", check_required_files),
        ("依赖包检查", check_dependencies),
        ("模块导入测试", test_module_import),
        ("简单数据库测试", create_simple_test)
    ]
    
    results = []
    
    for check_name, check_func in checks:
        try:
            result = check_func()
            results.append((check_name, result))
        except Exception as e:
            print_error(f"{check_name}执行失败: {e}")
            results.append((check_name, False))
    
    # 总结
    print_header("诊断总结")
    
    passed = 0
    total = len(results)
    
    for check_name, result in results:
        if result:
            print_success(f"{check_name}: 通过")
            passed += 1
        else:
            print_error(f"{check_name}: 失败")
    
    print()
    print(f"📊 总体结果: {passed}/{total} 项检查通过")
    
    if passed == total:
        print_success("🎉 所有检查通过！数据库环境正常")
        print_info("如果仍有问题，请尝试重新运行一键安装脚本")
    else:
        print_error("❌ 发现问题，请查看上面的详细信息")
        provide_solutions()

if __name__ == "__main__":
    main()