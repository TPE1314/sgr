#!/bin/bash

echo "🔧 直接修复 /root/sgr 目录中的投稿机器人"
echo "=" * 50

# 检查是否在正确的目录
if [ ! -f "submission_bot.py" ]; then
    echo "❌ 当前目录没有 submission_bot.py 文件"
    echo "请确保您在 /root/sgr 目录中运行此脚本"
    exit 1
fi

echo "📁 找到文件: $(pwd)/submission_bot.py"

# 备份原文件
cp submission_bot.py submission_bot.py.backup.$(date +%Y%m%d_%H%M%S)
echo "📦 已备份原文件"

# 直接修复所有已知的filters错误
echo "🔧 修复filters错误..."

# 使用sed修复filters.STICKER
sed -i 's/filters\.STICKER/filters.Sticker.ALL/g' submission_bot.py
echo "✅ 修复 filters.STICKER -> filters.Sticker.ALL"

# 修复filters.DOCUMENT
sed -i 's/filters\.DOCUMENT/filters.Document.ALL/g' submission_bot.py
echo "✅ 修复 filters.DOCUMENT -> filters.Document.ALL"

# 验证修复结果
echo ""
echo "🧪 验证修复结果..."

if grep -q "filters\.STICKER" submission_bot.py; then
    echo "❌ 还有未修复的 STICKER 错误"
    grep -n "filters\.STICKER" submission_bot.py
else
    echo "✅ STICKER 错误已全部修复"
fi

if grep -q "filters\.DOCUMENT[^.]" submission_bot.py; then
    echo "❌ 还有未修复的 DOCUMENT 错误"
    grep -n "filters\.DOCUMENT[^.]" submission_bot.py
else
    echo "✅ DOCUMENT 错误已全部修复"
fi

# 检查Python语法
echo ""
echo "🧪 检查Python语法..."
if python3 -m py_compile submission_bot.py 2>/dev/null; then
    echo "✅ Python语法检查通过"
else
    echo "❌ Python语法检查失败："
    python3 -m py_compile submission_bot.py
fi

# 检查Token配置
echo ""
echo "🔧 检查Token配置..."
if [ -f "config.local.ini" ]; then
    echo "✅ 找到本地配置文件 config.local.ini"
    if grep -q "YOUR_SUBMISSION_BOT_TOKEN" config.local.ini; then
        echo "⚠️  投稿机器人Token还是占位符，需要配置真实Token"
    else
        echo "✅ Token配置看起来正常"
    fi
elif [ -f "config.ini" ]; then
    echo "⚠️  只找到 config.ini，建议创建 config.local.ini"
    if grep -q "YOUR_SUBMISSION_BOT_TOKEN" config.ini; then
        echo "⚠️  需要配置真实的投稿机器人Token"
    fi
else
    echo "❌ 找不到配置文件"
fi

echo ""
echo "🎉 修复完成！"
echo ""
echo "🚀 启动投稿机器人："
echo "source venv/bin/activate"
echo "python3 submission_bot.py"
echo ""
echo "🔄 后台启动："
echo "source venv/bin/activate"
echo "nohup python3 submission_bot.py > logs/submission_bot.log 2>&1 &"