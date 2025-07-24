#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
数据库初始化脚本
Independent Database Initialization Script
"""

import sys
import os
import traceback
from pathlib import Path

# 添加当前目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

def print_status(message, status="INFO"):
    """打印状态信息"""
    print(f"[{status}] {message}")

def init_core_database():
    """初始化核心数据库"""
    try:
        from database import DatabaseManager
        print_status("数据库模块导入成功", "SUCCESS")
        
        # 初始化主数据库
        db = DatabaseManager('telegram_bot.db')
        print_status("主数据库初始化完成", "SUCCESS")
        return True
        
    except ImportError as e:
        print_status(f"数据库模块导入失败: {e}", "ERROR")
        return False
    except Exception as e:
        print_status(f"数据库初始化失败: {e}", "ERROR")
        print_status(f"详细错误: {traceback.format_exc()}", "DEBUG")
        return False

def init_advertisement_module():
    """初始化广告管理模块"""
    try:
        from advertisement_manager import initialize_ad_manager
        initialize_ad_manager('telegram_bot.db')
        print_status("广告管理模块初始化完成", "SUCCESS")
        return True
    except ImportError:
        print_status("广告管理模块未找到，跳过初始化", "WARNING")
        return True  # 不是致命错误
    except Exception as e:
        print_status(f"广告管理模块初始化失败: {e}", "ERROR")
        return False

def init_performance_module():
    """初始化性能优化模块"""
    try:
        from performance_optimizer import PerformanceOptimizer
        optimizer = PerformanceOptimizer('telegram_bot.db')
        print_status("性能优化模块初始化完成", "SUCCESS")
        return True
    except ImportError:
        print_status("性能优化模块未找到，跳过初始化", "WARNING")
        return True  # 不是致命错误
    except Exception as e:
        print_status(f"性能优化模块初始化失败: {e}", "ERROR")
        return False

def init_i18n_module():
    """初始化多语言模块"""
    try:
        from i18n_manager import LocaleManager
        locale_manager = LocaleManager()
        print_status("多语言模块初始化完成", "SUCCESS")
        return True
    except ImportError:
        print_status("多语言模块未找到，跳过初始化", "WARNING")
        return True  # 不是致命错误
    except Exception as e:
        print_status(f"多语言模块初始化失败: {e}", "ERROR")
        return False

def init_notification_module():
    """初始化实时通知模块"""
    try:
        import configparser
        
        # 检查配置文件
        config_file = 'config.ini'
        if not os.path.exists(config_file):
            print_status("配置文件不存在，跳过通知模块初始化", "WARNING")
            return True
        
        config = configparser.ConfigParser()
        config.read(config_file)
        
        if not config.has_option('telegram', 'admin_bot_token'):
            print_status("管理员Token未配置，跳过通知模块初始化", "WARNING")
            return True
            
        from real_time_notification import NotificationManager
        token = config.get('telegram', 'admin_bot_token')
        notification_manager = NotificationManager(token)
        print_status("实时通知模块初始化完成", "SUCCESS")
        return True
        
    except ImportError:
        print_status("实时通知模块未找到，跳过初始化", "WARNING")
        return True  # 不是致命错误
    except Exception as e:
        print_status(f"实时通知模块初始化失败: {e}", "ERROR")
        return False

def check_python_files():
    """检查必需的Python文件"""
    required_files = [
        'database.py',
        'config_manager.py'
    ]
    
    missing_files = []
    for file in required_files:
        if not os.path.exists(file):
            missing_files.append(file)
    
    if missing_files:
        print_status(f"缺少必需的Python文件: {', '.join(missing_files)}", "ERROR")
        return False
    
    print_status("所有必需的Python文件检查通过", "SUCCESS")
    return True

def main():
    """主函数"""
    print_status("开始数据库初始化过程")
    
    # 检查Python文件
    if not check_python_files():
        print_status("Python文件检查失败", "ERROR")
        sys.exit(1)
    
    # 初始化核心数据库
    if not init_core_database():
        print_status("核心数据库初始化失败", "ERROR")
        sys.exit(1)
    
    # 初始化各个模块（非致命错误）
    modules = [
        ("广告管理", init_advertisement_module),
        ("性能优化", init_performance_module),
        ("多语言", init_i18n_module),
        ("实时通知", init_notification_module)
    ]
    
    success_count = 0
    for module_name, init_func in modules:
        if init_func():
            success_count += 1
        else:
            print_status(f"{module_name}模块初始化失败，但不影响基础功能", "WARNING")
    
    print_status(f"数据库初始化完成，{success_count}/{len(modules)} 个扩展模块成功初始化")
    
    # 创建必要的目录
    directories = ['logs', 'backups', 'temp']
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
    print_status("必要目录创建完成", "SUCCESS")
    
    print_status("数据库和模块初始化过程完成", "INFO")

if __name__ == "__main__":
    main()