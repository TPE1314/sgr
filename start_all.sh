#!/bin/bash
# 启动所有电报机器人的脚本

# 检查配置文件是否存在
if [ ! -f "config.ini" ]; then
    echo "❌ 配置文件 config.ini 不存在，请先配置"
    exit 1
fi

# 检查Python依赖
echo "🔍 检查Python依赖..."
python3 -c "import telegram, sqlite3, psutil" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "❌ Python依赖检查失败，请运行: pip3 install -r requirements.txt"
    exit 1
fi

echo "🚀 开始启动所有机器人..."

# 启动投稿机器人
echo "📝 启动投稿机器人..."
nohup python3 submission_bot.py > submission_bot.out 2>&1 &
SUBMISSION_PID=$!
echo "投稿机器人 PID: $SUBMISSION_PID"

# 等待一下
sleep 2

# 启动发布机器人
echo "📢 启动发布机器人..."
nohup python3 publish_bot.py > publish_bot.out 2>&1 &
PUBLISH_PID=$!
echo "发布机器人 PID: $PUBLISH_PID"

# 等待一下
sleep 2

# 启动控制机器人
echo "🎛️ 启动控制机器人..."
nohup python3 control_bot.py > control_bot.out 2>&1 &
CONTROL_PID=$!
echo "控制机器人 PID: $CONTROL_PID"

# 保存PID到文件
echo $SUBMISSION_PID > submission_bot.pid
echo $PUBLISH_PID > publish_bot.pid
echo $CONTROL_PID > control_bot.pid

echo ""
echo "✅ 所有机器人启动完成！"
echo ""
echo "📊 状态检查："
echo "投稿机器人 PID: $SUBMISSION_PID"
echo "发布机器人 PID: $PUBLISH_PID"
echo "控制机器人 PID: $CONTROL_PID"
echo ""
echo "📋 使用方法："
echo "• 查看状态: ./status.sh"
echo "• 停止所有: ./stop_all.sh"
echo "• 查看日志: tail -f *.log"
echo ""
echo "🎯 现在可以开始使用您的电报机器人了！"