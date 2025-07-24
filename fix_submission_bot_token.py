#!/usr/bin/env python3
"""
投稿机器人Token修复工具
快速修复投稿机器人的Token配置问题
"""

import configparser
import os
import sys

def main():
    print("🔧 投稿机器人Token修复工具")
    print("=" * 50)
    
    # 检查配置文件
    config_file = "config.ini"
    if not os.path.exists(config_file):
        print(f"❌ 找不到配置文件: {config_file}")
        return False
    
    # 读取当前配置
    config = configparser.ConfigParser()
    config.read(config_file)
    
    current_token = config.get('telegram', 'submission_bot_token', fallback='未设置')
    print(f"📋 当前投稿机器人Token: {current_token}")
    
    if current_token == 'YOUR_SUBMISSION_BOT_TOKEN':
        print("⚠️  检测到投稿机器人Token为占位符，需要更新")
        print("\n请提供您的投稿机器人Token:")
        print("格式示例: 1234567890:ABCdefGhIJKlmNoPQRsTuVwXyZ")
        
        new_token = input("请输入投稿机器人Token: ").strip()
        
        if new_token and ':' in new_token and len(new_token) > 20:
            # 更新配置
            config.set('telegram', 'submission_bot_token', new_token)
            
            # 保存配置
            with open(config_file, 'w') as f:
                config.write(f)
            
            print(f"✅ 投稿机器人Token已更新: {new_token[:10]}...")
            print("\n现在您可以重新启动投稿机器人:")
            print("source venv/bin/activate && python3 submission_bot.py")
            return True
        else:
            print("❌ Token格式不正确，请检查后重试")
            return False
    else:
        print("✅ 投稿机器人Token看起来正常")
        
        # 测试Token格式
        if ':' in current_token and len(current_token) > 20:
            print("✅ Token格式检查通过")
        else:
            print("⚠️  Token格式可能有问题")
        
        return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)