#!/usr/bin/env python3
"""
版本管理工具
支持特殊的版本递增规则：尾数最多到7，然后中间位+1
"""

import sys
import os
from typing import Tuple

class VersionManager:
    def __init__(self, version_file: str = ".version"):
        self.version_file = version_file
    
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
    
    def parse_version(self, version: str) -> Tuple[int, int, int]:
        """解析版本号"""
        if version.startswith('v'):
            version = version[1:]
        
        parts = version.split('.')
        if len(parts) != 3:
            raise ValueError(f"版本格式错误: {version}")
        
        return tuple(map(int, parts))
    
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
        
        if version_type == "patch":
            if patch < 7:
                patch += 1
            else:
                minor += 1
                patch = 0
        elif version_type == "minor":
            minor += 1
            patch = 0
        elif version_type == "major":
            major += 1
            minor = 0
            patch = 0
        
        return self.format_version(major, minor, patch)
    
    def show_version_info(self):
        """显示版本信息"""
        current = self.get_current_version()
        
        print("=" * 50)
        print("🎯 版本管理工具")
        print("=" * 50)
        print(f"📋 当前版本: {current}")
        print(f"📈 下一个小更新: {self.get_next_version('patch')}")
        print(f"📊 下一个中间更新: {self.get_next_version('minor')}")
        print(f"🚀 下一个主版本: {self.get_next_version('major')}")
        print()
        
        # 显示规则
        try:
            major, minor, patch = self.parse_version(current)
            if patch == 7:
                print("⚠️ 尾数已达上限(7)，下次小更新将自动递增中间位")
            else:
                print(f"ℹ️ 尾数可更新 {7-patch} 次到达上限")
        except:
            pass

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

⚙️ 其他功能:
  python3 version_manager.py set v2.5.0    # 设置指定版本
  python3 version_manager.py next patch    # 预览下一版本

📈 版本递增规则:
  • 小更新: 尾数递增，最多到7
  • 到达7后: 中间位+1，尾数重置为0
  • 主版本: 主版本+1，其他重置为0

示例: v2.3.0 -> v2.3.1 -> ... -> v2.3.7 -> v2.4.0
    """)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n❌ 操作已取消")
    except Exception as e:
        print(f"❌ 错误: {e}")
        print_usage()