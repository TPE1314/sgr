#!/usr/bin/env python3
"""
版本管理工具
支持特殊的版本递增规则：尾数最多到7，然后中间位+1
支持Git提交哈希值版本格式：x.x.提交哈希值
"""

import sys
import os
import subprocess
from typing import Tuple, Optional

class VersionManager:
    def __init__(self, version_file: str = ".version"):
        self.version_file = version_file
    
    def get_git_commit_hash(self, short: bool = True) -> Optional[str]:
        """获取Git提交哈希值"""
        try:
            cmd = ["git", "rev-parse", "--short", "HEAD"] if short else ["git", "rev-parse", "HEAD"]
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=os.getcwd())
            if result.returncode == 0:
                return result.stdout.strip()
            return None
        except Exception:
            return None
    
    def get_current_version(self) -> str:
        """获取当前版本"""
        try:
            if os.path.exists(self.version_file):
                with open(self.version_file, 'r', encoding='utf-8') as f:
                    version = f.read().strip()
                    if version:
                        return version
            return "v2.3.0"
        except Exception as e:
            print(f"获取版本失败: {e}")
            return "v2.3.0"
    
    def set_version(self, version: str) -> bool:
        """设置版本"""
        try:
            with open(self.version_file, 'w', encoding='utf-8') as f:
                f.write(version)
            print(f"✅ 版本已更新为: {version}")
            return True
        except Exception as e:
            print(f"❌ 设置版本失败: {e}")
            return False
    
    def generate_git_hash_version(self, major: int = 2, minor: int = 3) -> str:
        """生成基于Git提交哈希值的版本号"""
        commit_hash = self.get_git_commit_hash(short=True)
        if commit_hash:
            return f"v{major}.{minor}.{commit_hash}"
        else:
            print("⚠️ 无法获取Git提交哈希值，使用默认版本")
            return f"v{major}.{minor}.0"
    
    def update_to_git_hash_version(self, major: int = 2, minor: int = 3) -> str:
        """更新版本为Git提交哈希值格式"""
        new_version = self.generate_git_hash_version(major, minor)
        self.set_version(new_version)
        return new_version
    
    def parse_version(self, version: str) -> Tuple[int, int, int]:
        """解析版本号"""
        if version.startswith('v'):
            version = version[1:]
        
        parts = version.split('.')
        if len(parts) != 3:
            raise ValueError(f"版本格式错误: {version}")
        
        # 如果第三部分是数字，直接转换；如果是哈希值，返回0
        try:
            patch = int(parts[2])
        except ValueError:
            # 第三部分不是数字，可能是哈希值
            patch = 0
        
        return (int(parts[0]), int(parts[1]), patch)
    
    def format_version(self, major: int, minor: int, patch: int) -> str:
        """格式化版本号"""
        return f"v{major}.{minor}.{patch}"
    
    def increment_patch(self) -> str:
        """小更新：尾数+1，最多到7"""
        current = self.get_current_version()
        major, minor, patch = self.parse_version(current)
        
        if patch < 7:
            patch += 1
        else:
            # 尾数到7了，中间位+1，尾数重置为0
            minor += 1
            patch = 0
            print(f"⚠️ 尾数已达上限(7)，中间位自动递增")
        
        new_version = self.format_version(major, minor, patch)
        self.set_version(new_version)
        return new_version
    
    def increment_minor(self) -> str:
        """中间位更新：中间位+1，尾数重置为0"""
        current = self.get_current_version()
        major, minor, patch = self.parse_version(current)
        
        minor += 1
        patch = 0
        
        new_version = self.format_version(major, minor, patch)
        self.set_version(new_version)
        return new_version
    
    def increment_major(self) -> str:
        """主版本更新：主版本+1，其他重置为0"""
        current = self.get_current_version()
        major, minor, patch = self.parse_version(current)
        
        major += 1
        minor = 0
        patch = 0
        
        new_version = self.format_version(major, minor, patch)
        self.set_version(new_version)
        return new_version
    
    def get_next_version(self, version_type: str = "patch") -> str:
        """预览下一个版本（不保存）"""
        current = self.get_current_version()
        major, minor, patch = self.parse_version(current)
        
        if version_type == "major":
            return self.format_version(major + 1, 0, 0)
        elif version_type == "minor":
            return self.format_version(major, minor + 1, 0)
        else:  # patch
            if patch < 7:
                return self.format_version(major, minor, patch + 1)
            else:
                return self.format_version(major, minor + 1, 0)
    
    def show_version_info(self):
        """显示版本信息"""
        current_version = self.get_current_version()
        commit_hash = self.get_git_commit_hash(short=True)
        full_hash = self.get_git_commit_hash(short=False)
        
        print(f"📋 版本信息:")
        print(f"   当前版本: {current_version}")
        if commit_hash:
            print(f"   Git提交: {commit_hash}")
            print(f"   完整哈希: {full_hash}")
        else:
            print(f"   Git提交: 无法获取")
        
        # 检查是否为Git哈希版本
        if commit_hash and commit_hash in current_version:
            print(f"   ✅ 当前使用Git哈希版本格式")
        else:
            print(f"   ℹ️ 当前使用传统版本格式")
            print(f"   建议: 使用 'git-hash' 命令更新为Git哈希版本格式")

def main():
    """主函数"""
    vm = VersionManager()
    
    if len(sys.argv) == 1:
        vm.show_version_info()
        return
    
    command = sys.argv[1].lower()
    
    if command in ['patch', 'p', 'small', '小']:
        print("🔧 执行小更新...")
        new_version = vm.increment_patch()
        print(f"🎉 版本已更新为: {new_version}")
        
    elif command in ['minor', 'm', 'middle', '中']:
        print("📊 执行中间位更新...")
        new_version = vm.increment_minor()
        print(f"🎉 版本已更新为: {new_version}")
        
    elif command in ['major', 'M', 'big', '大']:
        print("🚀 执行主版本更新...")
        new_version = vm.increment_major()
        print(f"🎉 版本已更新为: {new_version}")
        
    elif command in ['show', 's', 'info', '显示']:
        vm.show_version_info()
        
    elif command in ['set', '设置']:
        if len(sys.argv) < 3:
            print("❌ 请提供版本号，例如: python3 version_manager.py set v2.4.0")
            return
        
        version = sys.argv[2]
        if not version.startswith('v'):
            version = f"v{version}"
        
        vm.set_version(version)
        
    elif command in ['next', 'preview', '预览']:
        version_type = sys.argv[2] if len(sys.argv) > 2 else "patch"
        next_ver = vm.get_next_version(version_type)
        print(f"📋 下一个{version_type}版本: {next_ver}")
        
    elif command in ['git-hash', 'gh', 'git']:
        print("🔗 更新为Git提交哈希值版本格式...")
        if len(sys.argv) > 2:
            try:
                major = int(sys.argv[2])
                minor = int(sys.argv[3]) if len(sys.argv) > 3 else 3
                new_version = vm.update_to_git_hash_version(major, minor)
            except (ValueError, IndexError):
                print("❌ 参数格式错误，使用默认值 v2.3.{hash}")
                new_version = vm.update_to_git_hash_version()
        else:
            new_version = vm.update_to_git_hash_version()
        print(f"🎉 版本已更新为Git哈希格式: {new_version}")
        
    else:
        print("❌ 未知命令")
        print_usage()

def print_usage():
    """显示使用说明"""
    print("""
🎯 版本管理工具 - 使用说明

📋 查看版本信息:
  python3 version_manager.py
  python3 version_manager.py show

🔧 版本更新:
  python3 version_manager.py patch    # 小更新 (v2.3.0 -> v2.3.1)
  python3 version_manager.py minor    # 中间位更新 (v2.3.7 -> v2.4.0)
  python3 version_manager.py major    # 主版本更新 (v2.4.7 -> v3.0.0)

🔗 Git哈希版本:
  python3 version_manager.py git-hash        # 更新为 v2.3.{commit_hash}
  python3 version_manager.py git-hash 3 1   # 更新为 v3.1.{commit_hash}

⚙️ 其他功能:
  python3 version_manager.py set v2.5.0    # 设置指定版本
  python3 version_manager.py next patch    # 预览下一版本

📈 版本递增规则:
  • 小更新: 尾数递增，最多到7
  • 到达7后: 中间位+1，尾数重置为0
  • 主版本: 主版本+1，其他重置为0
  • Git哈希版本: x.x.{commit_hash} 格式

示例: v2.3.0 -> v2.3.1 -> ... -> v2.3.7 -> v2.4.0
Git哈希版本示例: v2.3.35396e8
    """)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n❌ 操作已取消")
    except Exception as e:
        print(f"❌ 错误: {e}")
        print_usage()