#!/bin/bash

echo "🔄 重新启动所有机器人"
echo "=" * 40

# 停止所有机器人进程
echo "🛑 停止现有机器人进程..."
sudo pkill -f "submission_bot.py" 2>/dev/null
sudo pkill -f "publish_bot.py" 2>/dev/null  
sudo pkill -f "control_bot.py" 2>/dev/null
sleep 3

# 清理PID文件
echo "🧹 清理PID文件..."
sudo rm -f /root/sgr/pids/*.pid 2>/dev/null

# 创建日志目录
echo "📁 准备日志目录..."
sudo mkdir -p /root/sgr/logs /root/sgr/pids

# 启动投稿机器人
echo "🚀 启动投稿机器人..."
sudo bash -c 'cd /root/sgr && source venv/bin/activate && nohup python3 submission_bot.py > logs/submission_bot.log 2>&1 & echo $! > pids/submission_bot.pid'

# 启动发布机器人
echo "🚀 启动发布机器人..."
sudo bash -c 'cd /root/sgr && source venv/bin/activate && nohup python3 publish_bot.py > logs/publish_bot.log 2>&1 & echo $! > pids/publish_bot.pid'

# 启动控制机器人
echo "🚀 启动控制机器人..."
sudo bash -c 'cd /root/sgr && source venv/bin/activate && nohup python3 control_bot.py > logs/control_bot.log 2>&1 & echo $! > pids/control_bot.pid'

sleep 5

# 检查状态
echo ""
echo "📊 检查启动状态..."
echo "=" * 40

for bot in submission publish control; do
    if sudo pgrep -f "${bot}_bot.py" > /dev/null; then
        pid=$(sudo pgrep -f "${bot}_bot.py")
        echo "✅ ${bot}_bot 运行中 (PID: $pid)"
    else
        echo "❌ ${bot}_bot 启动失败"
    fi
done

echo ""
echo "📋 查看日志命令："
echo "sudo tail -f /root/sgr/logs/*.log"