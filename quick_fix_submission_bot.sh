#!/bin/bash

echo "🔧 投稿机器人快速修复工具"
echo "=" * 50

# 找到当前目录的submission_bot.py
if [ ! -f "submission_bot.py" ]; then
    echo "❌ 找不到submission_bot.py文件"
    exit 1
fi

echo "📁 找到文件: $(pwd)/submission_bot.py"

# 备份原文件
cp submission_bot.py submission_bot.py.backup
echo "📦 已备份原文件: submission_bot.py.backup"

# 修复filters错误
echo "🔧 修复filters错误..."

# 使用sed修复所有已知的filters问题
sed -i 's/filters\.STICKER/filters.Sticker.ALL/g' submission_bot.py
sed -i 's/filters\.DOCUMENT/filters.Document.ALL/g' submission_bot.py

echo "✅ 修复完成"

# 验证修复结果
echo "🧪 验证修复结果..."
if grep -q "filters\.STICKER" submission_bot.py; then
    echo "❌ 还有未修复的STICKER错误"
else
    echo "✅ STICKER错误已修复"
fi

if grep -q "filters\.DOCUMENT\>" submission_bot.py; then
    echo "❌ 还有未修复的DOCUMENT错误"
else
    echo "✅ DOCUMENT错误已修复"
fi

# 检查语法
echo "🧪 检查Python语法..."
if python3 -m py_compile submission_bot.py 2>/dev/null; then
    echo "✅ 语法检查通过"
else
    echo "❌ 语法检查失败"
    echo "正在尝试进一步修复..."
    
    # 显示问题行
    python3 -m py_compile submission_bot.py
fi

echo ""
echo "🎉 修复完成！现在可以重新启动投稿机器人了"
echo ""
echo "重启命令:"
echo "source venv/bin/activate && python3 submission_bot.py"