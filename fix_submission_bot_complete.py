#!/usr/bin/env python3
"""
完整修复投稿机器人脚本
解决所有已知问题：Token配置、Filters错误、依赖安装
"""

import os
import sys
import subprocess
import configparser

def install_dependencies():
    """安装依赖"""
    print("🔧 检查并安装依赖...")
    
    # 检查虚拟环境
    venv_path = None
    possible_venvs = ['venv', './venv', '/root/sgr/venv']
    
    for path in possible_venvs:
        if os.path.exists(os.path.join(path, 'bin', 'activate')):
            venv_path = path
            break
    
    if venv_path:
        print(f"✅ 找到虚拟环境: {venv_path}")
        pip_cmd = f"{venv_path}/bin/pip"
    else:
        print("⚠️  未找到虚拟环境，使用系统pip")
        pip_cmd = "pip3"
    
    # 安装依赖
    try:
        result = subprocess.run(
            [pip_cmd, "install", "python-telegram-bot", "psutil"], 
            capture_output=True, text=True, check=True
        )
        print("✅ 依赖安装成功")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ 依赖安装失败: {e}")
        return False

def fix_filters_issues():
    """修复filters相关错误"""
    print("🔧 修复filters错误...")
    
    # 查找submission_bot.py文件
    possible_files = [
        'submission_bot.py',
        './submission_bot.py',
        '/root/sgr/submission_bot.py'
    ]
    
    target_file = None
    for file_path in possible_files:
        if os.path.exists(file_path):
            target_file = file_path
            break
    
    if not target_file:
        print("❌ 找不到submission_bot.py文件")
        return False
    
    print(f"📁 找到文件: {target_file}")
    
    # 读取文件内容
    try:
        with open(target_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 修复已知的filters错误
        fixes = [
            ('filters.DOCUMENT', 'filters.Document.ALL'),
            ('filters.STICKER', 'filters.Sticker.ALL'),
            ('filters.ANIMATION', 'filters.ANIMATION'),
            ('filters.LOCATION', 'filters.LOCATION'),
            ('filters.CONTACT', 'filters.CONTACT'),
        ]
        
        changed = False
        for old, new in fixes:
            if old in content:
                content = content.replace(old, new)
                changed = True
                print(f"✅ 修复: {old} -> {new}")
        
        if changed:
            # 备份原文件
            backup_file = target_file + '.backup'
            with open(backup_file, 'w', encoding='utf-8') as f:
                with open(target_file, 'r', encoding='utf-8') as orig:
                    f.write(orig.read())
            print(f"📦 已备份原文件: {backup_file}")
            
            # 写入修复后的内容
            with open(target_file, 'w', encoding='utf-8') as f:
                f.write(content)
            print("✅ filters错误修复完成")
        else:
            print("✅ 未发现filters错误")
        
        return True
        
    except Exception as e:
        print(f"❌ 修复filters错误失败: {e}")
        return False

def fix_token_config():
    """修复Token配置"""
    print("🔧 检查Token配置...")
    
    # 查找配置文件
    config_files = [
        'config.local.ini',
        'config.ini',
        './config.local.ini',
        './config.ini',
        '/root/sgr/config.local.ini',
        '/root/sgr/config.ini'
    ]
    
    config_file = None
    for file_path in config_files:
        if os.path.exists(file_path):
            config_file = file_path
            break
    
    if not config_file:
        print("❌ 找不到配置文件")
        return False
    
    print(f"📁 找到配置文件: {config_file}")
    
    # 检查配置
    try:
        config = configparser.ConfigParser()
        config.read(config_file, encoding='utf-8')
        
        token = config.get('telegram', 'submission_bot_token', fallback='')
        
        if token == 'YOUR_SUBMISSION_BOT_TOKEN' or not token:
            print("⚠️  投稿机器人Token未配置")
            print("请手动配置config.local.ini中的submission_bot_token")
            return False
        elif ':' in token and len(token) > 20:
            print("✅ Token配置正常")
            return True
        else:
            print("⚠️  Token格式可能有问题")
            return False
            
    except Exception as e:
        print(f"❌ 检查Token配置失败: {e}")
        return False

def test_bot():
    """测试机器人启动"""
    print("🧪 测试机器人启动...")
    
    # 查找submission_bot.py
    possible_files = [
        'submission_bot.py',
        './submission_bot.py',
        '/root/sgr/submission_bot.py'
    ]
    
    target_file = None
    for file_path in possible_files:
        if os.path.exists(file_path):
            target_file = file_path
            break
    
    if not target_file:
        print("❌ 找不到submission_bot.py文件")
        return False
    
    # 检查虚拟环境
    venv_path = None
    possible_venvs = ['venv', './venv', '/root/sgr/venv']
    
    for path in possible_venvs:
        if os.path.exists(os.path.join(path, 'bin', 'python')):
            venv_path = path
            break
    
    if venv_path:
        python_cmd = f"{venv_path}/bin/python"
    else:
        python_cmd = "python3"
    
    # 测试语法
    try:
        result = subprocess.run(
            [python_cmd, "-m", "py_compile", target_file],
            capture_output=True, text=True, check=True
        )
        print("✅ 语法检查通过")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ 语法检查失败: {e.stderr}")
        return False

def main():
    print("🔧 投稿机器人完整修复工具")
    print("=" * 50)
    
    steps = [
        ("修复filters错误", fix_filters_issues),
        ("检查Token配置", fix_token_config),
        ("安装依赖", install_dependencies),
        ("测试机器人", test_bot),
    ]
    
    success_count = 0
    for step_name, step_func in steps:
        print(f"\n🔄 {step_name}...")
        if step_func():
            success_count += 1
        else:
            print(f"❌ {step_name}失败")
    
    print(f"\n📊 修复结果: {success_count}/{len(steps)} 项成功")
    
    if success_count == len(steps):
        print("🎉 所有问题已修复，投稿机器人应该可以正常启动了！")
        print("\n启动命令:")
        print("source venv/bin/activate && python3 submission_bot.py")
    else:
        print("⚠️  还有问题需要手动处理")
    
    return success_count == len(steps)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)