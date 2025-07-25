#!/usr/bin/env python3
"""
测试三个机器人是否共享同一个数据库
"""

import os
import sys
import sqlite3
from datetime import datetime

# 添加当前目录到Python路径
sys.path.insert(0, os.getcwd())

def test_config_loading():
    """测试配置加载"""
    print("🔧 测试配置文件加载...")
    
    try:
        from config_manager import ConfigManager
        
        # 模拟三个机器人的配置加载
        configs = {}
        for bot_name in ['submission', 'publish', 'control']:
            config = ConfigManager()
            db_file = config.get_db_file()
            configs[bot_name] = {
                'db_file': db_file,
                'db_file_abs': os.path.abspath(db_file)
            }
            print(f"  {bot_name}_bot 数据库文件: {db_file}")
            print(f"  {bot_name}_bot 绝对路径: {os.path.abspath(db_file)}")
        
        # 检查是否都指向同一个文件
        db_files = [config['db_file_abs'] for config in configs.values()]
        if len(set(db_files)) == 1:
            print("✅ 所有机器人使用相同的数据库文件")
            return db_files[0]
        else:
            print("❌ 机器人使用不同的数据库文件!")
            for bot, config in configs.items():
                print(f"  {bot}: {config['db_file_abs']}")
            return None
            
    except Exception as e:
        print(f"❌ 配置加载失败: {e}")
        return None

def test_database_operations(db_file):
    """测试数据库操作"""
    print(f"\n💾 测试数据库操作: {db_file}")
    
    if not os.path.exists(db_file):
        print(f"❌ 数据库文件不存在: {db_file}")
        return False
    
    try:
        # 测试直接数据库连接
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        
        # 插入测试投稿
        test_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute("""
            INSERT INTO submissions (user_id, username, content_type, content, status, submit_time)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (888888, 'test_sharing', 'text', '测试数据库共享', 'pending', test_time))
        
        test_id = cursor.lastrowid
        conn.commit()
        print(f"✅ 直接插入测试投稿成功，ID: {test_id}")
        
        # 测试通过DatabaseManager查询
        try:
            from database import DatabaseManager
            db_manager = DatabaseManager(db_file)
            
            pending_submissions = db_manager.get_pending_submissions()
            print(f"✅ DatabaseManager查询成功，待审核投稿数: {len(pending_submissions)}")
            
            # 查找我们刚插入的测试数据
            found_test = False
            for submission in pending_submissions:
                if submission['id'] == test_id:
                    found_test = True
                    print(f"✅ 找到测试投稿: #{submission['id']} - {submission['username']}")
                    break
            
            if not found_test:
                print("⚠️  未找到刚插入的测试投稿")
            
        except Exception as e:
            print(f"❌ DatabaseManager测试失败: {e}")
        
        # 清理测试数据
        cursor.execute("DELETE FROM submissions WHERE id = ?", (test_id,))
        conn.commit()
        conn.close()
        print("✅ 测试数据清理完成")
        
        return True
        
    except Exception as e:
        print(f"❌ 数据库操作失败: {e}")
        return False

def test_notification_service():
    """测试通知服务"""
    print(f"\n🔔 测试通知服务...")
    
    try:
        from notification_service import NotificationService
        from config_manager import ConfigManager
        
        config = ConfigManager()
        notification = NotificationService(config)
        
        print("✅ NotificationService 实例化成功")
        
        # 检查是否有发送到审核群组的方法
        if hasattr(notification, 'send_submission_to_review_group'):
            print("✅ 找到 send_submission_to_review_group 方法")
        else:
            print("❌ 缺少 send_submission_to_review_group 方法")
        
        return True
        
    except Exception as e:
        print(f"❌ 通知服务测试失败: {e}")
        return False

def simulate_submission_process():
    """模拟完整的投稿流程"""
    print(f"\n🔄 模拟投稿流程...")
    
    try:
        from database import DatabaseManager
        from config_manager import ConfigManager
        
        config = ConfigManager()
        db = DatabaseManager(config.get_db_file())
        
        # 模拟投稿
        print("1. 模拟用户投稿...")
        submission_id = db.add_submission(
            user_id=777777,
            username='test_user_flow',
            content_type='text',
            content='模拟投稿流程测试'
        )
        print(f"✅ 投稿添加成功，ID: {submission_id}")
        
        # 检查是否在待审核列表中
        print("2. 检查待审核列表...")
        pending = db.get_pending_submissions()
        found = any(s['id'] == submission_id for s in pending)
        if found:
            print("✅ 投稿出现在待审核列表中")
        else:
            print("❌ 投稿未出现在待审核列表中")
        
        # 模拟审核通过
        print("3. 模拟审核通过...")
        success = db.approve_submission(submission_id, 123456)
        if success:
            print("✅ 投稿审核通过")
        else:
            print("❌ 投稿审核失败")
        
        # 检查状态变化
        print("4. 检查投稿状态...")
        cursor = sqlite3.connect(config.get_db_file()).cursor()
        cursor.execute("SELECT status FROM submissions WHERE id = ?", (submission_id,))
        result = cursor.fetchone()
        if result and result[0] == 'approved':
            print("✅ 投稿状态已更新为 'approved'")
        else:
            print(f"❌ 投稿状态异常: {result[0] if result else 'NOT FOUND'}")
        
        # 清理测试数据
        cursor.execute("DELETE FROM submissions WHERE id = ?", (submission_id,))
        cursor.connection.commit()
        cursor.connection.close()
        print("✅ 测试数据清理完成")
        
        return True
        
    except Exception as e:
        print(f"❌ 投稿流程模拟失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    print("🧪 数据库共享测试工具")
    print("=" * 50)
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"工作目录: {os.getcwd()}")
    print()
    
    # 测试1：配置加载
    db_file = test_config_loading()
    if not db_file:
        print("\n❌ 配置测试失败，停止后续测试")
        return
    
    # 测试2：数据库操作
    db_ok = test_database_operations(db_file)
    if not db_ok:
        print("\n❌ 数据库测试失败")
    
    # 测试3：通知服务
    notification_ok = test_notification_service()
    
    # 测试4：完整流程
    flow_ok = simulate_submission_process()
    
    # 汇总结果
    print("\n📊 测试结果汇总:")
    print("=" * 50)
    print(f"配置文件: {'✅ 正常' if db_file else '❌ 异常'}")
    print(f"数据库操作: {'✅ 正常' if db_ok else '❌ 异常'}")
    print(f"通知服务: {'✅ 正常' if notification_ok else '❌ 异常'}")
    print(f"投稿流程: {'✅ 正常' if flow_ok else '❌ 异常'}")
    
    if all([db_file, db_ok, notification_ok, flow_ok]):
        print("\n✅ 数据库共享正常，问题可能在其他地方")
        print("\n💡 建议检查:")
        print("1. 机器人是否都在运行")
        print("2. Token配置是否正确")
        print("3. 群组ID配置是否正确")
        print("4. 网络连接是否正常")
    else:
        print("\n❌ 发现数据库共享问题")
        print("\n🔧 建议修复:")
        print("1. 检查config.local.ini文件")
        print("2. 重新初始化数据库")
        print("3. 确保所有文件在同一目录")

if __name__ == "__main__":
    main()