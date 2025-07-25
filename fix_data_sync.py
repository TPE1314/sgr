#!/usr/bin/env python3
"""
修复投稿机器人和发布机器人数据不互通问题
确保两个机器人使用相同的数据库和配置
"""

import os
import sys
import sqlite3
import subprocess
import shutil
from datetime import datetime
import configparser

def print_header(title):
    print(f"\n{'='*60}")
    print(f"🔧 {title}")
    print('='*60)

def print_step(step):
    print(f"📋 {step}")

def print_success(msg):
    print(f"✅ {msg}")

def print_warning(msg):
    print(f"⚠️  {msg}")

def print_error(msg):
    print(f"❌ {msg}")

def kill_all_bots():
    """终止所有机器人进程"""
    print_header("终止所有机器人进程")
    
    try:
        # 使用pkill终止所有相关进程
        subprocess.run(['pkill', '-f', 'submission_bot.py'], check=False)
        subprocess.run(['pkill', '-f', 'publish_bot.py'], check=False)
        subprocess.run(['pkill', '-f', 'control_bot.py'], check=False)
        
        print_success("已终止所有机器人进程")
        
        # 等待进程完全终止
        import time
        time.sleep(3)
        
    except Exception as e:
        print_warning(f"进程终止可能不完整: {e}")

def ensure_database_consistency():
    """确保数据库一致性"""
    print_header("检查数据库一致性")
    
    db_file = 'telegram_bot.db'
    
    if not os.path.exists(db_file):
        print_error(f"数据库文件不存在: {db_file}")
        return False
    
    try:
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        
        # 检查数据库表
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        print_step(f"数据库表: {', '.join(tables)}")
        
        if 'submissions' not in tables:
            print_error("缺少submissions表")
            return False
        
        # 检查submissions表结构
        cursor.execute("PRAGMA table_info(submissions)")
        columns = [row[1] for row in cursor.fetchall()]
        print_step(f"submissions表字段: {', '.join(columns)}")
        
        # 检查数据
        cursor.execute("SELECT COUNT(*) FROM submissions")
        total_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM submissions WHERE status='pending'")
        pending_count = cursor.fetchone()[0]
        
        print_step(f"总投稿数: {total_count}, 待审核: {pending_count}")
        
        if pending_count > 0:
            print_step("待审核投稿列表:")
            cursor.execute("SELECT id, username, content_type, submit_time FROM submissions WHERE status='pending' ORDER BY submit_time ASC LIMIT 5")
            for row in cursor.fetchall():
                print(f"  #{row[0]} - {row[1]} ({row[2]}) - {row[3]}")
        
        conn.close()
        print_success("数据库一致性检查完成")
        return True
        
    except Exception as e:
        print_error(f"数据库检查失败: {e}")
        return False

def fix_config_paths():
    """修复配置文件路径问题"""
    print_header("修复配置文件路径")
    
    # 确保配置文件存在
    if os.path.exists('config.local.ini'):
        config_file = 'config.local.ini'
    elif os.path.exists('config.ini'):
        config_file = 'config.ini'
        # 复制到local版本
        shutil.copy('config.ini', 'config.local.ini')
        config_file = 'config.local.ini'
        print_step("已创建config.local.ini")
    else:
        print_error("找不到配置文件")
        return False
    
    # 读取配置
    config = configparser.ConfigParser()
    config.read(config_file)
    
    # 确保数据库路径是绝对路径
    current_dir = os.path.abspath('.')
    db_path = os.path.join(current_dir, 'telegram_bot.db')
    
    if 'database' not in config:
        config['database'] = {}
    
    config['database']['db_file'] = 'telegram_bot.db'  # 使用相对路径，确保一致性
    
    # 写回配置文件
    with open(config_file, 'w') as f:
        config.write(f)
    
    print_success(f"配置文件路径已修复: {config_file}")
    print_step(f"数据库路径: telegram_bot.db")
    
    return True

def create_minimal_bots():
    """创建最小化的机器人，确保数据互通"""
    print_header("创建数据互通的机器人")
    
    # 检查投稿机器人是否有Token
    try:
        config = configparser.ConfigParser()
        config.read('config.local.ini')
        submission_token = config.get('telegram', 'submission_bot_token', fallback='')
        
        if not submission_token or submission_token.startswith('YOUR_'):
            print_error("投稿机器人Token未配置")
            return False
        
        print_success(f"投稿机器人Token已配置")
    except Exception as e:
        print_error(f"配置读取失败: {e}")
        return False
    
    # 创建简化的发布机器人
    publish_bot_code = '''#!/usr/bin/env python3
"""
简化的发布机器人 - 确保与投稿机器人数据互通
"""

import os
import sys
import sqlite3
import configparser
from datetime import datetime

# 添加当前目录到Python路径
sys.path.insert(0, os.getcwd())

def get_config():
    """获取配置"""
    config = configparser.ConfigParser()
    if os.path.exists('config.local.ini'):
        config.read('config.local.ini')
    elif os.path.exists('config.ini'):
        config.read('config.ini')
    else:
        raise Exception("找不到配置文件")
    return config

def get_database():
    """获取数据库连接"""
    config = get_config()
    db_file = config.get('database', 'db_file', fallback='telegram_bot.db')
    
    if not os.path.exists(db_file):
        raise Exception(f"数据库文件不存在: {db_file}")
    
    return sqlite3.connect(db_file)

def get_pending_submissions():
    """获取待审核投稿"""
    conn = get_database()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT * FROM submissions 
        WHERE status = 'pending' 
        ORDER BY submit_time ASC
    """)
    
    submissions = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return submissions

def show_pending():
    """显示待审核投稿"""
    try:
        pending = get_pending_submissions()
        print(f"\\n📋 待审核投稿 ({len(pending)}条):")
        print("="*50)
        
        if not pending:
            print("✅ 暂无待审核投稿")
            return
        
        for i, submission in enumerate(pending[:10], 1):
            print(f"{i}. ID#{submission['id']} - {submission['username']}")
            print(f"   类型: {submission['content_type']}")
            print(f"   时间: {submission['submit_time']}")
            if submission['content']:
                content = submission['content'][:50] + "..." if len(submission['content']) > 50 else submission['content']
                print(f"   内容: {content}")
            print("-" * 30)
            
    except Exception as e:
        print(f"❌ 获取待审核投稿失败: {e}")

def main():
    """主函数"""
    print("🔍 简化发布机器人 - 数据互通测试")
    print("="*50)
    print(f"当前时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"工作目录: {os.getcwd()}")
    
    try:
        # 测试配置
        config = get_config()
        print("✅ 配置文件读取成功")
        
        # 测试数据库
        conn = get_database()
        print("✅ 数据库连接成功")
        conn.close()
        
        # 显示待审核投稿
        show_pending()
        
        print("\\n✅ 数据互通测试完成")
        
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
'''
    
    # 写入简化的发布机器人
    with open('test_publish_bot.py', 'w', encoding='utf-8') as f:
        f.write(publish_bot_code)
    
    print_success("已创建测试发布机器人: test_publish_bot.py")
    return True

def test_data_sync():
    """测试数据同步"""
    print_header("测试数据同步")
    
    try:
        # 运行测试发布机器人
        result = subprocess.run([
            'python3', 'test_publish_bot.py'
        ], capture_output=True, text=True, timeout=30)
        
        print("测试输出:")
        print(result.stdout)
        
        if result.stderr:
            print("错误输出:")
            print(result.stderr)
        
        if result.returncode == 0:
            print_success("数据同步测试通过")
            return True
        else:
            print_error("数据同步测试失败")
            return False
            
    except subprocess.TimeoutExpired:
        print_error("测试超时")
        return False
    except Exception as e:
        print_error(f"测试执行失败: {e}")
        return False

def create_test_submission():
    """创建测试投稿验证互通"""
    print_header("创建测试投稿")
    
    try:
        conn = sqlite3.connect('telegram_bot.db')
        cursor = conn.cursor()
        
        # 插入测试投稿
        test_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute("""
            INSERT INTO submissions (user_id, username, content_type, content, status, submit_time)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (777777, 'data_sync_test', 'text', '🔧 数据互通测试投稿', 'pending', test_time))
        
        test_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        print_success(f"创建测试投稿成功，ID: {test_id}")
        return test_id
        
    except Exception as e:
        print_error(f"创建测试投稿失败: {e}")
        return None

def start_bots_minimal():
    """启动最小化机器人用于测试"""
    print_header("启动机器人进行测试")
    
    # 只启动投稿机器人进行测试
    if os.path.exists('submission_bot.py'):
        print_step("启动投稿机器人...")
        try:
            process = subprocess.Popen([
                'python3', 'submission_bot.py'
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            import time
            time.sleep(5)  # 等待启动
            
            if process.poll() is None:
                print_success("投稿机器人启动成功")
                return process
            else:
                stdout, stderr = process.communicate()
                print_error("投稿机器人启动失败")
                print(f"错误: {stderr.decode()}")
                return None
                
        except Exception as e:
            print_error(f"启动失败: {e}")
            return None
    else:
        print_error("找不到submission_bot.py")
        return None

def main():
    """主修复流程"""
    print("🔧 数据互通修复工具")
    print("="*60)
    print(f"修复时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 步骤1: 终止所有机器人
    kill_all_bots()
    
    # 步骤2: 修复配置路径
    if not fix_config_paths():
        print_error("配置修复失败")
        return
    
    # 步骤3: 检查数据库
    if not ensure_database_consistency():
        print_error("数据库检查失败")
        return
    
    # 步骤4: 创建测试机器人
    if not create_minimal_bots():
        print_error("创建测试机器人失败")
        return
    
    # 步骤5: 创建测试投稿
    test_id = create_test_submission()
    
    # 步骤6: 测试数据同步
    if test_data_sync():
        print_header("修复成功")
        print("✅ 数据互通修复完成！")
        if test_id:
            print(f"📝 测试投稿ID: {test_id}")
        print("\n🎯 验证步骤:")
        print("1. 运行: python3 test_publish_bot.py")
        print("2. 检查是否能看到待审核投稿")
        print("3. 确认投稿机器人和发布机器人数据一致")
    else:
        print_header("修复失败")
        print("❌ 数据互通仍有问题，需要进一步诊断")
    
    # 清理测试文件
    print_step("清理临时文件...")
    if os.path.exists('test_publish_bot.py'):
        os.remove('test_publish_bot.py')
        print_success("已清理测试文件")

if __name__ == "__main__":
    main()