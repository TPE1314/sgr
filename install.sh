#!/bin/bash
# Ubuntu系统电报机器人自动安装脚本

echo "🚀 电报机器人系统安装脚本"
echo "========================="
echo "适用于: Ubuntu 18.04+ 系统"
echo ""

# 检查是否为root用户
if [ "$EUID" -eq 0 ]; then
    echo "⚠️ 建议不要使用root用户运行此脚本"
    read -p "是否继续? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# 更新系统包
echo "📦 更新系统包列表..."
sudo apt update

# 安装Python3和pip
echo "🐍 安装Python3和相关工具..."
sudo apt install -y python3 python3-pip python3-venv

# 安装系统依赖
echo "🔧 安装系统依赖..."
sudo apt install -y git curl wget bc htop

# 检查Python版本
python_version=$(python3 --version | cut -d' ' -f2)
echo "✅ Python版本: $python_version"

# 创建虚拟环境（可选）
read -p "🤔 是否创建Python虚拟环境? (推荐) (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "📁 创建虚拟环境..."
    python3 -m venv telegram_bot_env
    echo "🔄 激活虚拟环境..."
    source telegram_bot_env/bin/activate
    echo "✅ 虚拟环境已创建并激活"
    echo "💡 提示: 以后使用前请运行: source telegram_bot_env/bin/activate"
fi

# 升级pip
echo "⬆️ 升级pip..."
pip3 install --upgrade pip

# 安装Python依赖
echo "📚 安装Python依赖包..."
pip3 install -r requirements.txt

# 检查依赖安装
echo "🔍 检查依赖安装..."
python3 -c "
try:
    import telegram
    import sqlite3
    import psutil
    import asyncio
    import configparser
    print('✅ 所有依赖包安装成功')
except ImportError as e:
    print(f'❌ 依赖包安装失败: {e}')
    exit(1)
"

# 设置脚本权限
echo "🔐 设置脚本执行权限..."
chmod +x *.sh

# 创建日志目录（如果需要）
echo "📁 准备日志目录..."
mkdir -p logs

# 检查配置文件
echo "⚙️ 检查配置文件..."
if [ ! -f "config.ini" ]; then
    echo "⚠️ 配置文件不存在，请按照以下步骤配置:"
    echo ""
    echo "1. 创建电报机器人:"
    echo "   - 联系 @BotFather 创建三个机器人"
    echo "   - 获取三个机器人的token"
    echo ""
    echo "2. 获取频道和群组ID:"
    echo "   - 创建频道和审核群组"
    echo "   - 添加机器人为管理员"
    echo "   - 获取频道和群组的ID"
    echo ""
    echo "3. 编辑config.ini文件:"
    echo "   - 填入所有token和ID"
    echo "   - 设置管理员用户ID"
    echo ""
    echo "📝 配置文件模板已存在，请编辑后重新运行"
else
    echo "✅ 配置文件已存在"
fi

echo ""
echo "🎯 安装完成！"
echo "============="
echo ""
echo "📋 下一步操作:"
echo "1. 编辑 config.ini 文件，填入您的机器人配置"
echo "2. 运行 ./start_all.sh 启动所有机器人"
echo "3. 运行 ./status.sh 查看运行状态"
echo ""
echo "🔧 常用命令:"
echo "• 启动: ./start_all.sh"
echo "• 停止: ./stop_all.sh"
echo "• 状态: ./status.sh"
echo "• 日志: tail -f *.log"
echo ""
echo "📚 文件说明:"
echo "• submission_bot.py - 投稿机器人"
echo "• publish_bot.py - 发布机器人(含审核功能)"
echo "• control_bot.py - 控制机器人"
echo "• config.ini - 配置文件"
echo ""
echo "⚠️ 重要提醒:"
echo "• 请妥善保管config.ini文件，包含敏感信息"
echo "• 定期备份数据库文件 telegram_bot.db"
echo "• 监控日志文件以确保正常运行"
echo ""
echo "🎉 祝您使用愉快！"