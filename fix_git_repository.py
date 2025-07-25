#!/usr/bin/env python3
"""
修复Git仓库问题的脚本
解决Git状态异常、未跟踪文件等问题
"""

import os
import sys
import subprocess
import shutil
from datetime import datetime

def print_header(title):
    print(f"\n{'='*60}")
    print(f"🔧 {title}")
    print('='*60)

def print_success(msg):
    print(f"✅ {msg}")

def print_warning(msg):
    print(f"⚠️  {msg}")

def print_error(msg):
    print(f"❌ {msg}")

def print_info(msg):
    print(f"ℹ️  {msg}")

def run_command(cmd, capture_output=True, shell=True):
    """运行命令并返回结果"""
    try:
        result = subprocess.run(cmd, shell=shell, capture_output=capture_output, text=True)
        return result.returncode == 0, result.stdout.strip(), result.stderr.strip()
    except Exception as e:
        return False, "", str(e)

def check_git_repository():
    """检查是否在Git仓库中"""
    print_header("检查Git仓库状态")
    
    success, stdout, stderr = run_command("git rev-parse --is-inside-work-tree")
    
    if success and stdout == "true":
        print_success("当前目录是有效的Git仓库")
        return True
    else:
        print_error("当前目录不是Git仓库或Git仓库损坏")
        print_info(f"错误信息: {stderr}")
        return False

def get_git_status():
    """获取Git状态"""
    print_header("获取Git状态信息")
    
    # 获取分支信息
    success, branch, _ = run_command("git branch --show-current")
    if success:
        print_info(f"当前分支: {branch}")
    
    # 获取远程状态
    success, status, _ = run_command("git status --porcelain")
    if success:
        if status:
            lines = status.split('\n')
            modified_files = [line for line in lines if line.startswith(' M') or line.startswith('M ')]
            untracked_files = [line for line in lines if line.startswith('??')]
            
            print_info(f"修改的文件: {len(modified_files)} 个")
            print_info(f"未跟踪的文件: {len(untracked_files)} 个")
            
            return {
                'clean': False,
                'modified': len(modified_files),
                'untracked': len(untracked_files),
                'modified_files': modified_files,
                'untracked_files': untracked_files
            }
        else:
            print_success("工作目录干净")
            return {'clean': True}
    else:
        print_error("无法获取Git状态")
        return None

def clean_untracked_files(status_info):
    """清理未跟踪的文件"""
    if not status_info or status_info.get('clean', False):
        return True
        
    print_header("清理未跟踪文件")
    
    untracked_files = status_info.get('untracked_files', [])
    if not untracked_files:
        print_success("没有未跟踪的文件需要清理")
        return True
    
    # 定义应该保留的文件模式
    keep_patterns = [
        'config.local.ini',
        'telegram_bot.db',
        '*.log',
        'pids/',
        'backups/',
        'logs/',
        'venv/',
        '__pycache__/'
    ]
    
    # 定义应该删除的文件模式
    delete_patterns = [
        '*.pyc',
        '__pycache__/',
        '*.tmp',
        '*.temp',
        '.DS_Store',
        'Thumbs.db'
    ]
    
    files_to_delete = []
    files_to_keep = []
    
    for file_line in untracked_files:
        file_path = file_line[3:]  # 去掉 "?? " 前缀
        
        should_delete = False
        should_keep = False
        
        # 检查是否应该删除
        for pattern in delete_patterns:
            if pattern.endswith('/') and file_path.startswith(pattern):
                should_delete = True
                break
            elif pattern.replace('*', '') in file_path:
                should_delete = True
                break
        
        # 检查是否应该保留
        for pattern in keep_patterns:
            if pattern.endswith('/') and file_path.startswith(pattern):
                should_keep = True
                break
            elif pattern.replace('*', '') in file_path:
                should_keep = True
                break
        
        if should_delete and not should_keep:
            files_to_delete.append(file_path)
        else:
            files_to_keep.append(file_path)
    
    # 显示清理计划
    if files_to_delete:
        print_info("准备删除的文件:")
        for file_path in files_to_delete[:10]:  # 只显示前10个
            print(f"  🗑️  {file_path}")
        if len(files_to_delete) > 10:
            print(f"  ... 还有 {len(files_to_delete) - 10} 个文件")
    
    if files_to_keep:
        print_info("将保留的文件:")
        for file_path in files_to_keep[:5]:  # 只显示前5个
            print(f"  📁 {file_path}")
        if len(files_to_keep) > 5:
            print(f"  ... 还有 {len(files_to_keep) - 5} 个文件")
    
    # 执行清理
    deleted_count = 0
    for file_path in files_to_delete:
        try:
            if os.path.isdir(file_path):
                shutil.rmtree(file_path)
                print_success(f"删除目录: {file_path}")
            else:
                os.remove(file_path)
                print_success(f"删除文件: {file_path}")
            deleted_count += 1
        except Exception as e:
            print_warning(f"删除失败 {file_path}: {e}")
    
    print_success(f"清理完成，删除了 {deleted_count} 个文件/目录")
    return True

def reset_modified_files():
    """重置修改的文件（谨慎操作）"""
    print_header("处理修改的文件")
    
    # 获取修改的文件
    success, status, _ = run_command("git status --porcelain")
    if not success:
        print_error("无法获取文件状态")
        return False
    
    if not status:
        print_success("没有修改的文件")
        return True
    
    lines = status.split('\n')
    modified_files = []
    
    for line in lines:
        if line.startswith(' M') or line.startswith('M '):
            file_path = line[3:]
            modified_files.append(file_path)
    
    if not modified_files:
        print_success("没有需要重置的修改文件")
        return True
    
    # 显示修改的文件
    print_info("修改的文件列表:")
    important_files = []
    log_files = []
    cache_files = []
    
    for file_path in modified_files:
        if any(ext in file_path for ext in ['.log', 'log']):
            log_files.append(file_path)
        elif any(ext in file_path for ext in ['.pyc', '__pycache__', '.db']):
            cache_files.append(file_path)
        else:
            important_files.append(file_path)
            print(f"  📄 {file_path}")
    
    # 自动重置日志和缓存文件
    if log_files or cache_files:
        files_to_reset = log_files + cache_files
        print_info(f"自动重置 {len(files_to_reset)} 个日志/缓存文件...")
        
        for file_path in files_to_reset:
            success, _, _ = run_command(f"git checkout -- \"{file_path}\"")
            if success:
                print_success(f"重置: {file_path}")
            else:
                print_warning(f"重置失败: {file_path}")
    
    # 对于重要文件，询问用户
    if important_files:
        print_warning(f"发现 {len(important_files)} 个重要文件被修改")
        print_info("这些文件包含重要更改，建议手动检查")
        
        # 创建备份
        backup_dir = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        os.makedirs(backup_dir, exist_ok=True)
        
        for file_path in important_files:
            try:
                backup_path = os.path.join(backup_dir, os.path.basename(file_path))
                shutil.copy2(file_path, backup_path)
                print_success(f"备份: {file_path} -> {backup_path}")
            except Exception as e:
                print_warning(f"备份失败 {file_path}: {e}")
        
        print_info(f"重要文件已备份到: {backup_dir}")
    
    return True

def check_remote_connection():
    """检查远程仓库连接"""
    print_header("检查远程仓库连接")
    
    # 获取远程仓库信息
    success, remotes, _ = run_command("git remote -v")
    if success and remotes:
        print_info("远程仓库:")
        for line in remotes.split('\n'):
            print(f"  🔗 {line}")
    else:
        print_warning("没有配置远程仓库")
        return False
    
    # 测试连接
    print_info("测试远程连接...")
    success, _, error = run_command("git fetch --dry-run")
    
    if success:
        print_success("远程仓库连接正常")
        return True
    else:
        print_warning(f"远程仓库连接有问题: {error}")
        return False

def fix_git_config():
    """修复Git配置"""
    print_header("检查和修复Git配置")
    
    # 检查用户配置
    success, name, _ = run_command("git config user.name")
    if not success or not name:
        print_info("设置Git用户名...")
        run_command("git config user.name 'System User'")
        print_success("Git用户名已设置")
    else:
        print_success(f"Git用户名: {name}")
    
    success, email, _ = run_command("git config user.email")
    if not success or not email:
        print_info("设置Git邮箱...")
        run_command("git config user.email 'system@example.com'")
        print_success("Git邮箱已设置")
    else:
        print_success(f"Git邮箱: {email}")
    
    return True

def main():
    """主修复流程"""
    print("🔧 Git仓库修复工具")
    print("="*60)
    print(f"修复时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"当前目录: {os.getcwd()}")
    
    # 检查Git仓库
    if not check_git_repository():
        print_error("请在Git仓库中运行此脚本")
        return
    
    # 修复Git配置
    fix_git_config()
    
    # 获取当前状态
    status_info = get_git_status()
    if status_info is None:
        print_error("无法获取Git状态，退出")
        return
    
    if status_info.get('clean', False):
        print_success("Git仓库状态良好，无需修复")
    else:
        # 清理未跟踪文件
        clean_untracked_files(status_info)
        
        # 处理修改的文件
        reset_modified_files()
    
    # 检查远程连接
    check_remote_connection()
    
    # 最终状态检查
    print_header("最终状态检查")
    final_status = get_git_status()
    
    if final_status and final_status.get('clean', False):
        print_success("🎉 Git仓库修复完成！仓库状态正常")
    else:
        print_warning("仓库状态已改善，但可能还需要手动处理一些文件")
    
    print_info("修复完成")

if __name__ == "__main__":
    main()