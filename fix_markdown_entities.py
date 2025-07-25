#!/usr/bin/env python3
"""
修复 Telegram Markdown 实体解析错误
解决 BadRequest: Can't parse entities 问题
"""

import os
import re
import shutil
from datetime import datetime

def escape_markdown_v2(text):
    """
    为 Telegram MarkdownV2 转义特殊字符
    """
    # MarkdownV2 需要转义的字符
    escape_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    
    for char in escape_chars:
        text = text.replace(char, f'\\{char}')
    
    return text

def fix_markdown_in_file(filepath):
    """
    修复文件中的 Markdown 格式问题
    """
    if not os.path.exists(filepath):
        print(f"❌ 文件不存在: {filepath}")
        return False
    
    # 备份原文件
    backup_path = f"{filepath}.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    shutil.copy2(filepath, backup_path)
    print(f"📄 已备份文件: {backup_path}")
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 记录修改
        modifications = []
        
        # 1. 将 ParseMode.MARKDOWN 改为 ParseMode.HTML
        if 'ParseMode.MARKDOWN' in content:
            content = content.replace('ParseMode.MARKDOWN', 'ParseMode.HTML')
            modifications.append("ParseMode.MARKDOWN → ParseMode.HTML")
        
        # 2. 将 Markdown 格式转换为 HTML 格式
        # **粗体** → <b>粗体</b>
        content = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', content)
        
        # *斜体* → <i>斜体</i>
        content = re.sub(r'(?<!\*)\*([^*]+?)\*(?!\*)', r'<i>\1</i>', content)
        
        # `代码` → <code>代码</code>
        content = re.sub(r'`([^`]+?)`', r'<code>\1</code>', content)
        
        # ```代码块``` → <pre>代码块</pre>
        content = re.sub(r'```(.*?)```', r'<pre>\1</pre>', content, flags=re.DOTALL)
        
        if modifications:
            modifications.append("Markdown 格式 → HTML 格式")
        
        # 3. 修复常见的格式问题
        # 移除可能导致解析错误的特殊字符组合
        problematic_patterns = [
            (r'(\*\*[^*]*)\*([^*]*\*\*)', r'\1\\*\2'),  # 修复嵌套星号
            (r'(\[[^\]]*)\[([^\]]*\])', r'\1\\[\2'),     # 修复嵌套方括号
            (r'(\([^)]*)\(([^)]*\))', r'\1\\(\2'),       # 修复嵌套圆括号
        ]
        
        for pattern, replacement in problematic_patterns:
            if re.search(pattern, content):
                content = re.sub(pattern, replacement, content)
                modifications.append(f"修复嵌套格式: {pattern}")
        
        # 写回文件
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        if modifications:
            print(f"✅ 已修复 {filepath}:")
            for mod in modifications:
                print(f"   • {mod}")
            return True
        else:
            print(f"ℹ️  {filepath} 无需修复")
            # 删除备份文件
            os.remove(backup_path)
            return True
    
    except Exception as e:
        print(f"❌ 修复文件失败 {filepath}: {e}")
        # 恢复备份
        if os.path.exists(backup_path):
            shutil.copy2(backup_path, filepath)
            print(f"🔄 已恢复备份文件")
        return False

def main():
    """主函数"""
    print("🔧 Telegram Markdown 实体解析错误修复工具")
    print("=" * 50)
    
    # 需要修复的文件列表
    files_to_fix = [
        'submission_bot.py',
        'publish_bot.py', 
        'control_bot.py',
        'notification_service.py',
        'real_time_notification.py'
    ]
    
    success_count = 0
    total_count = 0
    
    for filename in files_to_fix:
        if os.path.exists(filename):
            total_count += 1
            if fix_markdown_in_file(filename):
                success_count += 1
        else:
            print(f"⚠️  文件不存在，跳过: {filename}")
    
    print("\n" + "=" * 50)
    print(f"📊 修复结果: {success_count}/{total_count} 个文件修复成功")
    
    if success_count > 0:
        print("\n✅ 修复完成！建议重启所有机器人以应用更改。")
        print("\n🔄 重启命令:")
        print("   sudo systemctl restart telegram-bots")
        print("   # 或者使用脚本:")
        print("   ./bot_manager.sh restart")
    
    # 额外的修复建议
    print("\n💡 额外建议:")
    print("1. 如果问题仍然存在，检查消息内容是否包含特殊的 Unicode 字符")
    print("2. 考虑使用 HTML 格式而不是 Markdown 格式")
    print("3. 在发送消息前验证文本格式的正确性")
    
    return success_count == total_count

if __name__ == "__main__":
    main()