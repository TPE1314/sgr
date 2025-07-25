#!/usr/bin/env python3
"""
系统状态检查脚本
快速诊断电报机器人投稿系统的健康状态
"""

import os
import sys
import sqlite3
import subprocess
import configparser
import psutil
from datetime import datetime

def print_header(title):
    print(f"\n{'='*60}")
    print(f"🔍 {title}")
    print('='*60)

def print_success(msg):
    print(f"✅ {msg}")

def print_warning(msg):
    print(f"⚠️  {msg}")

def print_error(msg):
    print(f"❌ {msg}")

def print_info(msg):
    print(f"ℹ️  {msg}")

def check_environment():
    """检查运行环境"""
    print_header("运行环境检查")
    
    # Python版本
    python_version = sys.version.split()[0]
    print_success(f"Python版本: {python_version}")
    
    # 当前目录
    current_dir = os.getcwd()
    print_info(f"工作目录: {current_dir}")
    
    # 磁盘空间
    disk_usage = psutil.disk_usage('.')
    free_gb = disk_usage.free / (1024**3)
    total_gb = disk_usage.total / (1024**3)
    print_info(f"磁盘空间: {free_gb:.1f}GB / {total_gb:.1f}GB 可用")
    
    # 内存使用
    memory = psutil.virtual_memory()
    memory_gb = memory.available / (1024**3)
    total_memory_gb = memory.total / (1024**3)
    print_info(f"可用内存: {memory_gb:.1f}GB / {total_memory_gb:.1f}GB")

def check_files():
    """检查关键文件"""
    print_header("关键文件检查")
    
    required_files = [
        'submission_bot.py',
        'publish_bot.py', 
        'control_bot.py',
        'database.py',
        'config_manager.py'
    ]
    
    missing_files = []
    
    for file in required_files:
        if os.path.exists(file):
            print_success(f"{file}")
        else:
            print_error(f"{file} - 缺失")
            missing_files.append(file)
    
    # 检查配置文件
    if os.path.exists('config.local.ini'):
        print_success("config.local.ini")
    elif os.path.exists('config.ini'):
        print_warning("config.ini (建议创建config.local.ini)")
    else:
        print_error("配置文件缺失")
        missing_files.append('config.ini/config.local.ini')
    
    # 检查数据库
    if os.path.exists('telegram_bot.db'):
        print_success("telegram_bot.db")
    else:
        print_warning("telegram_bot.db (首次运行时会自动创建)")
    
    return missing_files

def check_configuration():
    """检查配置文件"""
    print_header("配置文件检查")
    
    config_file = None
    if os.path.exists('config.local.ini'):
        config_file = 'config.local.ini'
    elif os.path.exists('config.ini'):
        config_file = 'config.ini'
    else:
        print_error("找不到配置文件")
        return False
    
    try:
        config = configparser.ConfigParser()
        config.read(config_file)
        
        # 检查必需的配置节
        required_sections = ['telegram', 'database']
        for section in required_sections:
            if section in config:
                print_success(f"[{section}] 节存在")
            else:
                print_error(f"[{section}] 节缺失")
        
        # 检查机器人Token
        if 'telegram' in config:
            tokens = [
                ('submission_bot_token', '投稿机器人Token'),
                ('publish_bot_token', '发布机器人Token'),
                ('admin_bot_token', '控制机器人Token')
            ]
            
            for token_key, token_name in tokens:
                token = config.get('telegram', token_key, fallback='')
                if token and not token.startswith('YOUR_'):
                    print_success(f"{token_name}: 已配置")
                else:
                    print_warning(f"{token_name}: 未配置或使用占位符")
        
        # 检查频道和群组ID
        if 'telegram' in config:
            ids = [
                ('channel_id', '发布频道ID'),
                ('review_group_id', '审核群组ID'),
                ('admin_group_id', '管理群组ID')
            ]
            
            for id_key, id_name in ids:
                id_value = config.get('telegram', id_key, fallback='')
                if id_value and not id_value.startswith('YOUR_') and id_value != '-1001234567890':
                    print_success(f"{id_name}: 已配置")
                else:
                    print_warning(f"{id_name}: 未配置或使用占位符")
        
        return True
        
    except Exception as e:
        print_error(f"配置文件读取失败: {e}")
        return False

def check_database():
    """检查数据库状态"""
    print_header("数据库状态检查")
    
    if not os.path.exists('telegram_bot.db'):
        print_warning("数据库文件不存在")
        return False
    
    try:
        conn = sqlite3.connect('telegram_bot.db')
        cursor = conn.cursor()
        
        # 检查表
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        required_tables = ['submissions', 'users', 'admin_logs']
        for table in required_tables:
            if table in tables:
                print_success(f"表 {table} 存在")
            else:
                print_warning(f"表 {table} 不存在")
        
        # 检查数据
        if 'submissions' in tables:
            cursor.execute("SELECT COUNT(*) FROM submissions")
            total_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM submissions WHERE status='pending'")
            pending_count = cursor.fetchone()[0]
            
            print_info(f"总投稿数: {total_count}")
            print_info(f"待审核投稿: {pending_count}")
        
        conn.close()
        print_success("数据库连接正常")
        return True
        
    except Exception as e:
        print_error(f"数据库检查失败: {e}")
        return False

def check_processes():
    """检查运行进程"""
    print_header("进程状态检查")
    
    bot_processes = {
        'submission_bot.py': '投稿机器人',
        'publish_bot.py': '发布机器人', 
        'control_bot.py': '控制机器人'
    }
    
    running_count = 0
    
    for script, name in bot_processes.items():
        try:
            # 检查进程是否运行
            result = subprocess.run(['pgrep', '-f', script], 
                                  capture_output=True, text=True)
            
            if result.returncode == 0:
                pids = result.stdout.strip().split('\n')
                print_success(f"{name}: 运行中 (PID: {', '.join(pids)})")
                running_count += 1
            else:
                print_warning(f"{name}: 未运行")
                
        except Exception as e:
            print_error(f"检查 {name} 失败: {e}")
    
    print_info(f"运行中的机器人: {running_count}/3")
    return running_count

def check_logs():
    """检查日志文件"""
    print_header("日志文件检查")
    
    log_files = [
        'submission_bot.log',
        'publish_bot.log',
        'control_bot.log'
    ]
    
    for log_file in log_files:
        if os.path.exists(log_file):
            size = os.path.getsize(log_file)
            size_mb = size / (1024 * 1024)
            
            if size_mb < 10:
                print_success(f"{log_file}: {size_mb:.1f}MB")
            else:
                print_warning(f"{log_file}: {size_mb:.1f}MB (较大)")
        else:
            print_info(f"{log_file}: 不存在")

def check_network():
    """检查网络连接"""
    print_header("网络连接检查")
    
    try:
        # 检查GitHub连接
        result = subprocess.run(['ping', '-c', '1', 'github.com'], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            print_success("GitHub连接正常")
        else:
            print_warning("GitHub连接异常")
    except:
        print_warning("无法检查GitHub连接")
    
    try:
        # 检查Telegram API连接
        result = subprocess.run(['ping', '-c', '1', 'api.telegram.org'], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            print_success("Telegram API连接正常")
        else:
            print_warning("Telegram API连接异常")
    except:
        print_warning("无法检查Telegram API连接")

def generate_summary():
    """生成系统总结"""
    print_header("系统健康状态总结")
    
    # 重新检查关键指标
    missing_files = check_files() if not globals().get('missing_files_checked') else []
    config_ok = check_configuration() if not globals().get('config_checked') else True
    db_ok = check_database() if not globals().get('db_checked') else True
    running_count = check_processes() if not globals().get('processes_checked') else 0
    
    # 计算健康度
    health_score = 0
    max_score = 4
    
    if not missing_files:
        health_score += 1
        print_success("✅ 关键文件完整")
    else:
        print_error(f"❌ 缺失 {len(missing_files)} 个关键文件")
    
    if config_ok:
        health_score += 1
        print_success("✅ 配置文件正常")
    else:
        print_error("❌ 配置文件有问题")
    
    if db_ok:
        health_score += 1
        print_success("✅ 数据库状态正常")
    else:
        print_error("❌ 数据库有问题")
    
    if running_count >= 2:
        health_score += 1
        print_success(f"✅ 大部分机器人运行正常 ({running_count}/3)")
    else:
        print_error(f"❌ 多数机器人未运行 ({running_count}/3)")
    
    # 健康度评级
    health_percentage = (health_score / max_score) * 100
    
    print(f"\n🏥 系统健康度: {health_percentage:.0f}% ({health_score}/{max_score})")
    
    if health_percentage >= 90:
        print("🟢 系统状态优秀")
    elif health_percentage >= 70:
        print("🟡 系统状态良好，有轻微问题")
    elif health_percentage >= 50:
        print("🟠 系统状态一般，需要关注")
    else:
        print("🔴 系统状态较差，需要立即处理")

def show_recommendations():
    """显示建议"""
    print_header("改进建议")
    
    print("🔧 常用命令:")
    print("  查看详细日志: tail -f *.log")
    print("  手动启动机器人: python3 submission_bot.py &")
    print("  运行数据修复: python3 fix_data_sync.py")
    print("  一键更新系统: ./one_click_update.sh")
    
    print("\n📚 相关文档:")
    print("  使用指南: BOT_USAGE_GUIDE.md")
    print("  更新教程: ONE_CLICK_UPDATE_GUIDE.md")
    print("  快速参考: QUICK_REFERENCE.md")

def main():
    """主函数"""
    print("🔍 电报机器人投稿系统 - 状态检查工具")
    print("="*60)
    print(f"检查时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 执行所有检查
    check_environment()
    
    missing_files = check_files()
    globals()['missing_files_checked'] = True
    
    config_ok = check_configuration()
    globals()['config_checked'] = True
    
    db_ok = check_database()
    globals()['db_checked'] = True
    
    running_count = check_processes()
    globals()['processes_checked'] = True
    
    check_logs()
    check_network()
    
    # 生成总结和建议
    generate_summary()
    show_recommendations()
    
    print(f"\n📅 检查完成于: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()