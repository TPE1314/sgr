#!/usr/bin/env python3
"""
投稿系统全面修复脚本
解决Token冲突、数据库共享、机器人启动等问题
"""

import os
import sys
import sqlite3
import subprocess
import time
import signal
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

def kill_conflicting_processes():
    """终止所有可能冲突的机器人进程"""
    print_header("终止冲突进程")
    
    try:
        # 查找所有Python机器人进程
        result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
        processes = result.stdout.split('\n')
        
        killed_processes = []
        for line in processes:
            if 'python' in line and any(bot in line for bot in ['submission_bot', 'publish_bot', 'control_bot']):
                # 提取进程ID
                parts = line.split()
                if len(parts) > 1:
                    pid = parts[1]
                    try:
                        # 获取进程详细信息
                        process_info = ' '.join(parts[10:])
                        print_step(f"发现进程: PID {pid} - {process_info}")
                        
                        # 温和终止
                        os.kill(int(pid), signal.SIGTERM)
                        time.sleep(2)
                        
                        # 检查是否已终止
                        try:
                            os.kill(int(pid), 0)  # 检查进程是否存在
                            print_warning(f"进程 {pid} 未响应SIGTERM，使用SIGKILL")
                            os.kill(int(pid), signal.SIGKILL)
                        except ProcessLookupError:
                            pass
                        
                        killed_processes.append(pid)
                        print_success(f"已终止进程 {pid}")
                        
                    except (ValueError, ProcessLookupError) as e:
                        print_warning(f"无法终止进程 {pid}: {e}")
        
        if killed_processes:
            print_success(f"共终止 {len(killed_processes)} 个冲突进程")
            time.sleep(3)  # 等待进程完全清理
        else:
            print_success("没有发现冲突进程")
            
    except Exception as e:
        print_error(f"进程清理失败: {e}")

def check_and_fix_config():
    """检查并修复配置文件"""
    print_header("检查配置文件")
    
    config_file = 'config.local.ini'
    if not os.path.exists(config_file):
        config_file = 'config.ini'
    
    if not os.path.exists(config_file):
        print_error("找不到配置文件")
        return False
    
    config = configparser.ConfigParser()
    config.read(config_file)
    
    print_step(f"使用配置文件: {config_file}")
    
    # 检查必要的配置
    required_configs = {
        'submission_bot_token': config.get('telegram', 'submission_bot_token', fallback=''),
        'publish_bot_token': config.get('telegram', 'publish_bot_token', fallback=''),
        'admin_bot_token': config.get('telegram', 'admin_bot_token', fallback=''),
        'channel_id': config.get('telegram', 'channel_id', fallback=''),
        'review_group_id': config.get('telegram', 'review_group_id', fallback=''),
    }
    
    missing_configs = []
    for key, value in required_configs.items():
        if not value or value.startswith('YOUR_'):
            missing_configs.append(key)
        else:
            print_success(f"{key}: 已配置")
    
    if missing_configs:
        print_warning("以下配置项缺失或未正确配置:")
        for config_name in missing_configs:
            print(f"  - {config_name}")
        print("\n💡 你需要:")
        print("1. 从 @BotFather 获取机器人Token")
        print("2. 创建频道和群组，获取ID")
        print("3. 更新 config.local.ini 文件")
        return False
    
    print_success("配置文件检查通过")
    return True

def test_database():
    """测试数据库连接和操作"""
    print_header("测试数据库")
    
    db_file = 'telegram_bot.db'
    if not os.path.exists(db_file):
        print_error(f"数据库文件不存在: {db_file}")
        return False
    
    try:
        # 测试基本连接
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        
        # 检查表结构
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [table[0] for table in cursor.fetchall()]
        
        required_tables = ['submissions', 'users', 'admin_logs']
        missing_tables = [table for table in required_tables if table not in tables]
        
        if missing_tables:
            print_error(f"缺失数据库表: {missing_tables}")
            conn.close()
            return False
        
        print_success("数据库表结构正常")
        
        # 测试投稿操作
        test_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute("""
            INSERT INTO submissions (user_id, username, content_type, content, status, submit_time)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (999999, 'test_fix', 'text', '修复测试投稿', 'pending', test_time))
        
        test_id = cursor.lastrowid
        conn.commit()
        
        # 测试查询
        cursor.execute("SELECT * FROM submissions WHERE id = ?", (test_id,))
        result = cursor.fetchone()
        
        if result:
            print_success("数据库读写操作正常")
        else:
            print_error("数据库读写操作失败")
            conn.close()
            return False
        
        # 清理测试数据
        cursor.execute("DELETE FROM submissions WHERE id = ?", (test_id,))
        conn.commit()
        conn.close()
        
        print_success("数据库测试完成")
        return True
        
    except Exception as e:
        print_error(f"数据库测试失败: {e}")
        return False

def start_bots_in_sequence():
    """按顺序启动机器人"""
    print_header("启动机器人")
    
    bots = [
        ('submission_bot.py', '投稿机器人'),
        ('publish_bot.py', '发布机器人'),
        ('control_bot.py', '控制机器人')
    ]
    
    started_bots = []
    
    for bot_file, bot_name in bots:
        if not os.path.exists(bot_file):
            print_warning(f"{bot_name} 文件不存在: {bot_file}")
            continue
        
        print_step(f"启动 {bot_name}...")
        
        try:
            # 使用nohup在后台启动
            process = subprocess.Popen([
                'nohup', 'python3', bot_file
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, 
               preexec_fn=os.setsid)
            
            time.sleep(3)  # 等待启动
            
            # 检查进程是否还在运行
            if process.poll() is None:
                print_success(f"{bot_name} 启动成功 (PID: {process.pid})")
                started_bots.append((bot_name, process.pid))
            else:
                print_error(f"{bot_name} 启动失败")
                
        except Exception as e:
            print_error(f"{bot_name} 启动异常: {e}")
    
    return started_bots

def verify_system():
    """验证系统运行状态"""
    print_header("系统验证")
    
    # 检查进程
    try:
        result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
        processes = result.stdout
        
        running_bots = []
        for line in processes.split('\n'):
            if 'python3' in line:
                if 'submission_bot.py' in line:
                    running_bots.append('投稿机器人')
                elif 'publish_bot.py' in line:
                    running_bots.append('发布机器人')
                elif 'control_bot.py' in line:
                    running_bots.append('控制机器人')
        
        print_step(f"运行中的机器人: {len(running_bots)}/3")
        for bot in running_bots:
            print_success(f"  ✓ {bot}")
        
        if len(running_bots) == 3:
            print_success("所有机器人正常运行")
        else:
            missing = 3 - len(running_bots)
            print_warning(f"有 {missing} 个机器人未运行")
        
    except Exception as e:
        print_error(f"进程检查失败: {e}")

def create_test_submission():
    """创建测试投稿来验证系统"""
    print_header("创建测试投稿")
    
    try:
        from database import DatabaseManager
        from config_manager import ConfigManager
        
        config = ConfigManager()
        db = DatabaseManager(config.get_db_file())
        
        # 创建测试投稿
        submission_id = db.add_submission(
            user_id=888888,
            username='system_test',
            content_type='text',
            content='🧪 系统修复测试投稿\n\n这是一条测试投稿，用于验证系统是否正常工作。'
        )
        
        print_success(f"创建测试投稿成功，ID: {submission_id}")
        
        # 检查是否出现在待审核列表
        pending = db.get_pending_submissions()
        test_found = any(s['id'] == submission_id for s in pending)
        
        if test_found:
            print_success("测试投稿已进入待审核队列")
            print("💡 现在可以:")
            print("1. 通过发布机器人查看待审核投稿")
            print("2. 在审核群组中进行审核")
            print("3. 验证审核和发布流程")
        else:
            print_warning("测试投稿未出现在待审核队列中")
        
        return submission_id
        
    except Exception as e:
        print_error(f"创建测试投稿失败: {e}")
        return None

def show_next_steps():
    """显示下一步操作指导"""
    print_header("下一步操作指导")
    
    print("🎯 验证投稿系统:")
    print("1. 向投稿机器人发送测试消息")
    print("2. 检查发布机器人是否收到待审核投稿")
    print("3. 在审核群组中进行审核操作")
    print("4. 验证投稿是否正确发布到频道")
    
    print("\n🔍 如果仍有问题:")
    print("1. 检查机器人日志: tail -f submission_bot.log")
    print("2. 检查配置文件是否正确")
    print("3. 确认所有Token和ID都已正确配置")
    print("4. 验证机器人是否已添加到对应的群组/频道")
    
    print("\n📱 机器人命令:")
    print("- 投稿机器人: /start, /status, /help")
    print("- 发布机器人: /pending, /stats")
    print("- 控制机器人: /status, /config, /restart")

def main():
    """主修复流程"""
    print("🔧 投稿系统全面修复工具")
    print("=" * 60)
    print(f"修复时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 步骤1: 终止冲突进程
    kill_conflicting_processes()
    
    # 步骤2: 检查配置
    if not check_and_fix_config():
        print_error("配置文件问题需要先解决")
        return
    
    # 步骤3: 测试数据库
    if not test_database():
        print_error("数据库问题需要先解决")
        return
    
    # 步骤4: 启动机器人
    started_bots = start_bots_in_sequence()
    
    # 步骤5: 等待启动完成
    print_step("等待机器人完全启动...")
    time.sleep(10)
    
    # 步骤6: 验证系统
    verify_system()
    
    # 步骤7: 创建测试投稿
    test_id = create_test_submission()
    
    # 步骤8: 显示指导
    show_next_steps()
    
    print_header("修复完成")
    print("✅ 投稿系统修复完成！")
    if test_id:
        print(f"📝 测试投稿ID: {test_id}")
    print("现在可以测试完整的投稿流程。")

if __name__ == "__main__":
    main()