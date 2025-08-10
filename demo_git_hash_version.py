#!/usr/bin/env python3
"""
Git哈希版本功能演示脚本
展示如何使用新的版本管理功能
"""

from version_manager import VersionManager

def main():
    print("🚀 Git哈希版本功能演示")
    print("=" * 50)
    
    vm = VersionManager()
    
    # 显示当前版本信息
    print("\n📋 当前版本信息:")
    vm.show_version_info()
    
    # 演示Git哈希版本功能
    print("\n🔗 演示Git哈希版本功能:")
    
    # 获取当前Git提交哈希
    commit_hash = vm.get_git_commit_hash(short=True)
    full_hash = vm.get_git_commit_hash(short=False)
    
    print(f"   当前Git提交: {commit_hash}")
    print(f"   完整哈希值: {full_hash}")
    
    # 生成不同格式的Git哈希版本
    print("\n📝 可用的Git哈希版本格式:")
    print(f"   v2.3.{commit_hash}  (默认格式)")
    print(f"   v3.1.{commit_hash}  (自定义主次版本)")
    print(f"   v1.0.{commit_hash}  (自定义主次版本)")
    
    # 询问用户是否要更新版本
    print("\n❓ 是否要更新为Git哈希版本格式? (y/n): ", end="")
    try:
        choice = input().strip().lower()
        if choice in ['y', 'yes', '是', '要']:
            print("\n🔧 更新版本...")
            new_version = vm.update_to_git_hash_version()
            print(f"✅ 版本已更新为: {new_version}")
            
            print("\n📋 更新后的版本信息:")
            vm.show_version_info()
        else:
            print("ℹ️ 保持当前版本不变")
    except KeyboardInterrupt:
        print("\n\n⚠️ 操作被中断")
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")

if __name__ == "__main__":
    main()