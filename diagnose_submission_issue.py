#!/usr/bin/env python3
"""
诊断投稿系统问题
检查配置、数据库、机器人状态等
"""

import os
import sqlite3
import configparser
import subprocess
import sys
from datetime import datetime

def check_config():
    """检查配置文件"""
    print("🔧 检查配置文件...")
    
    config_files = ['config.local.ini', 'config.ini']
    config = configparser.ConfigParser()
    
    config_found = False
    for config_file in config_files:
        if os.path.exists(config_file):
            config.read(config_file)
            config_found = True
            print(f"✅ 找到配置文件: {config_file}")
            break
    
    if not config_found:
        print("❌ 没有找到配置文件")
        return False
    
    # 检查token配置
    tokens = {}
    if 'telegram' in config:
        tokens['submission'] = config['telegram'].get('submission_bot_token', '')
        tokens['publish'] = config['telegram'].get('publish_bot_token', '')
        tokens['admin'] = config['telegram'].get('admin_bot_token', '')
        
        print("\n🤖 机器人Token状态:")
        for bot_type, token in tokens.items():
            if token and token != f'YOUR_{bot_type.upper()}_BOT_TOKEN':
                print(f"  ✅ {bot_type}机器人: 已配置")
            else:
                print(f"  ❌ {bot_type}机器人: 未配置")
        
        # 检查群组ID配置
        print("\n📢 群组/频道配置:")
        channel_id = config['telegram'].get('channel_id', '')
        review_group_id = config['telegram'].get('review_group_id', '')
        admin_group_id = config['telegram'].get('admin_group_id', '')
        
        if channel_id and channel_id != 'YOUR_CHANNEL_ID':
            print(f"  ✅ 发布频道: 已配置")
        else:
            print(f"  ❌ 发布频道: 未配置")
            
        if review_group_id and review_group_id != 'YOUR_REVIEW_GROUP_ID':
            print(f"  ✅ 审核群组: 已配置")
        else:
            print(f"  ❌ 审核群组: 未配置")
            
        if admin_group_id and admin_group_id != 'YOUR_ADMIN_GROUP_ID':
            print(f"  ✅ 管理群组: 已配置")
        else:
            print(f"  ❌ 管理群组: 未配置")
    
    return True

def check_database():
    """检查数据库状态"""
    print("\n💾 检查数据库...")
    
    db_file = 'telegram_bot.db'
    if not os.path.exists(db_file):
        print(f"❌ 数据库文件不存在: {db_file}")
        return False
    
    try:
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        
        # 检查表
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [table[0] for table in cursor.fetchall()]
        
        if 'submissions' in tables:
            print("✅ submissions表存在")
            
            # 检查记录数
            cursor.execute("SELECT COUNT(*) FROM submissions")
            total_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM submissions WHERE status='pending'")
            pending_count = cursor.fetchone()[0]
            
            print(f"📊 投稿统计:")
            print(f"  总投稿数: {total_count}")
            print(f"  待审核: {pending_count}")
            
            if total_count > 0:
                print("\n📝 最近5条投稿:")
                cursor.execute("""
                    SELECT id, user_id, username, content_type, status, submit_time 
                    FROM submissions 
                    ORDER BY submit_time DESC 
                    LIMIT 5
                """)
                for row in cursor.fetchall():
                    print(f"  #{row[0]} - {row[2]} ({row[3]}) - {row[4]} - {row[5]}")
        else:
            print("❌ submissions表不存在")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ 数据库检查失败: {e}")
        return False

def check_bot_processes():
    """检查机器人进程"""
    print("\n🤖 检查机器人运行状态...")
    
    bots = ['submission_bot.py', 'publish_bot.py', 'control_bot.py']
    running_bots = []
    
    try:
        result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
        processes = result.stdout
        
        for bot in bots:
            if bot in processes and 'python' in processes:
                print(f"  ✅ {bot}: 运行中")
                running_bots.append(bot)
            else:
                print(f"  ❌ {bot}: 未运行")
        
        return running_bots
        
    except Exception as e:
        print(f"❌ 进程检查失败: {e}")
        return []

def check_log_files():
    """检查日志文件"""
    print("\n📋 检查日志文件...")
    
    log_files = ['submission_bot.log', 'publish_bot.log', 'control_bot.log']
    
    for log_file in log_files:
        if os.path.exists(log_file):
            size = os.path.getsize(log_file)
            print(f"  ✅ {log_file}: {size} bytes")
            
            # 检查最新错误
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    error_lines = [line for line in lines[-20:] if 'ERROR' in line or 'Exception' in line]
                    if error_lines:
                        print(f"    ⚠️  最近错误: {len(error_lines)}条")
                        for error in error_lines[-2:]:  # 显示最后2条错误
                            print(f"      {error.strip()}")
            except:
                pass
        else:
            print(f"  ❌ {log_file}: 不存在")

def test_database_connection():
    """测试数据库连接和操作"""
    print("\n🧪 测试数据库操作...")
    
    try:
        # 测试添加一条测试投稿
        conn = sqlite3.connect('telegram_bot.db')
        cursor = conn.cursor()
        
        # 插入测试数据
        test_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute("""
            INSERT INTO submissions (user_id, username, content_type, content, status, submit_time)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (999999, 'test_user', 'text', '测试投稿内容', 'pending', test_time))
        
        test_id = cursor.lastrowid
        print(f"✅ 测试投稿插入成功，ID: {test_id}")
        
        # 检查是否能查询到
        cursor.execute("SELECT * FROM submissions WHERE id = ?", (test_id,))
        result = cursor.fetchone()
        
        if result:
            print("✅ 测试投稿查询成功")
        else:
            print("❌ 测试投稿查询失败")
        
        # 删除测试数据
        cursor.execute("DELETE FROM submissions WHERE id = ?", (test_id,))
        print("✅ 测试数据清理完成")
        
        conn.commit()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ 数据库测试失败: {e}")
        return False

def provide_solutions():
    """提供解决方案"""
    print("\n💡 问题解决方案:")
    print("=" * 50)
    
    print("1. 🔧 配置问题解决:")
    print("   - 确保所有机器人token都已正确配置")
    print("   - 确保频道ID和群组ID都已配置")
    print("   - 检查config.local.ini文件权限")
    
    print("\n2. 🤖 机器人启动:")
    print("   - 启动发布机器人: python3 publish_bot.py &")
    print("   - 启动控制机器人: python3 control_bot.py &")
    print("   - 重启投稿机器人: pkill -f submission_bot.py && python3 submission_bot.py &")
    
    print("\n3. 📊 数据同步问题:")
    print("   - 检查所有机器人是否使用同一个数据库文件")
    print("   - 确保数据库文件权限正确")
    print("   - 检查notification_service是否正常工作")
    
    print("\n4. 🔍 进一步诊断:")
    print("   - 查看详细日志: tail -f submission_bot.log")
    print("   - 测试投稿: 向投稿机器人发送测试消息")
    print("   - 检查网络连接: ping api.telegram.org")

def main():
    """主函数"""
    print("🔍 电报机器人投稿系统诊断工具")
    print("=" * 50)
    print(f"诊断时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # 执行各项检查
    config_ok = check_config()
    database_ok = check_database()
    running_bots = check_bot_processes()
    check_log_files()
    db_test_ok = test_database_connection()
    
    print("\n📊 诊断结果汇总:")
    print("=" * 50)
    print(f"配置文件: {'✅ 正常' if config_ok else '❌ 异常'}")
    print(f"数据库: {'✅ 正常' if database_ok else '❌ 异常'}")
    print(f"数据库测试: {'✅ 正常' if db_test_ok else '❌ 异常'}")
    print(f"运行中的机器人: {len(running_bots)}/3")
    
    # 分析问题
    if len(running_bots) < 3:
        print("\n⚠️  主要问题: 部分机器人未运行")
        print("这是导致投稿无法被审核的主要原因！")
    
    if not config_ok:
        print("\n⚠️  配置问题: 需要完善配置文件")
    
    provide_solutions()

if __name__ == "__main__":
    main()