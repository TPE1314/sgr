#!/bin/bash

# Git问题诊断和修复脚本

echo "🔍 Git问题诊断工具"
echo "=================================="
echo "当前时间: $(date)"
echo "当前用户: $(whoami)"
echo "当前目录: $(pwd)"
echo

# 检查当前目录Git状态
echo "📍 检查当前目录Git状态:"
if git rev-parse --git-dir > /dev/null 2>&1; then
    echo "✅ 当前目录是Git仓库"
    echo "📊 Git状态:"
    git status --short
    echo
    echo "🌿 当前分支: $(git branch --show-current)"
else
    echo "❌ 当前目录不是Git仓库"
fi

echo
echo "🔍 查找可能的Git仓库:"

# 检查常见位置
locations=(
    "/workspace"
    "/root/sgr" 
    "$HOME/sgr"
    "$(pwd)/sgr"
)

for location in "${locations[@]}"; do
    if [ -d "$location/.git" ]; then
        echo "✅ 发现Git仓库: $location"
        echo "   分支: $(cd "$location" && git branch --show-current 2>/dev/null || echo '未知')"
        echo "   状态: $(cd "$location" && git status --porcelain | wc -l) 个更改"
    else
        echo "❌ 不存在: $location"
    fi
done

echo
echo "💡 解决方案:"
echo "1. 如果要在当前目录使用Git，请运行: git init"
echo "2. 如果要进入项目目录，请运行:"

for location in "${locations[@]}"; do
    if [ -d "$location/.git" ]; then
        echo "   cd $location"
        break
    fi
done

echo "3. 如果需要克隆项目，请运行:"
echo "   git clone <repository-url>"

echo
echo "🔧 如果需要清理Git状态，在项目目录中运行:"
echo "   python3 fix_git_repository.py"

echo
echo "📋 当前环境信息:"
echo "   Shell: $SHELL"
echo "   PATH: $PATH"
echo "   Git版本: $(git --version 2>/dev/null || echo '未安装')"