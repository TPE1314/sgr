#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
数据库初始化测试脚本
Test script for database initialization
"""

import sys
import os

# 添加当前目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

def test_database_import():
    """测试数据库模块导入"""
    print("测试数据库模块导入...")
    try:
        from database import DatabaseManager
        print("✅ database模块导入成功")
        return True
    except ImportError as e:
        print(f"❌ database模块导入失败: {e}")
        return False
    except Exception as e:
        print(f"❌ database模块导入错误: {e}")
        return False

def test_database_creation():
    """测试数据库创建"""
    print("测试数据库创建...")
    try:
        from database import DatabaseManager
        db = DatabaseManager('test_telegram_bot.db')
        print("✅ 测试数据库创建成功")
        
        # 清理测试数据库
        if os.path.exists('test_telegram_bot.db'):
            os.remove('test_telegram_bot.db')
            print("✅ 测试数据库清理完成")
        
        return True
    except Exception as e:
        print(f"❌ 数据库创建失败: {e}")
        return False

def test_config_manager():
    """测试配置管理器"""
    print("测试配置管理器...")
    try:
        from config_manager import ConfigManager
        print("✅ config_manager模块导入成功")
        return True
    except ImportError as e:
        print(f"❌ config_manager模块导入失败: {e}")
        return False
    except Exception as e:
        print(f"❌ config_manager模块错误: {e}")
        return False

def test_optional_modules():
    """测试可选模块"""
    modules = [
        ('advertisement_manager', '广告管理模块'),
        ('performance_optimizer', '性能优化模块'),
        ('i18n_manager', '多语言模块'),
        ('real_time_notification', '实时通知模块'),
        ('media_processor', '多媒体处理模块')
    ]
    
    results = {}
    
    for module_name, display_name in modules:
        try:
            __import__(module_name)
            print(f"✅ {display_name}可用")
            results[module_name] = True
        except ImportError:
            print(f"⚠️  {display_name}未找到")
            results[module_name] = False
        except Exception as e:
            print(f"❌ {display_name}错误: {e}")
            results[module_name] = False
    
    return results

def main():
    """主测试函数"""
    print("=" * 50)
    print("🧪 数据库初始化测试")
    print("=" * 50)
    
    all_tests_passed = True
    
    # 测试必需模块
    print("\n📋 必需模块测试:")
    if not test_database_import():
        all_tests_passed = False
    
    if not test_config_manager():
        all_tests_passed = False
    
    if not test_database_creation():
        all_tests_passed = False
    
    # 测试可选模块
    print("\n📦 可选模块测试:")
    optional_results = test_optional_modules()
    
    # 总结
    print("\n" + "=" * 50)
    print("📊 测试总结:")
    print("=" * 50)
    
    if all_tests_passed:
        print("✅ 所有必需模块测试通过")
    else:
        print("❌ 部分必需模块测试失败")
    
    available_count = sum(1 for v in optional_results.values() if v)
    total_count = len(optional_results)
    print(f"📦 可选模块: {available_count}/{total_count} 可用")
    
    if all_tests_passed:
        print("\n🎉 数据库初始化环境检查通过！")
        return 0
    else:
        print("\n⚠️  发现问题，请检查Python文件是否完整")
        return 1

if __name__ == "__main__":
    sys.exit(main())