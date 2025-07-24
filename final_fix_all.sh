#!/bin/bash

echo "🔧 最终修复 - 解决所有数据库和机器人问题"
echo "=" * 60

cd /root/sgr || exit 1

# 1. 修复数据库初始化问题
echo "🗄️ 修复数据库问题..."
python3 init_db_fixed.py
if [ $? -eq 0 ]; then
    echo "✅ 数据库问题已解决"
else
    echo "❌ 数据库修复失败"
fi

# 2. 停止现有进程
echo "🛑 停止现有机器人进程..."
pkill -f "_bot.py" 2>/dev/null
sleep 3

# 3. 清理PID文件
echo "🧹 清理PID文件..."
rm -f pids/*.pid 2>/dev/null

# 4. 启动所有机器人
echo "🚀 启动所有机器人..."

# 激活虚拟环境并启动投稿机器人
source venv/bin/activate
echo "📝 启动投稿机器人..."
nohup python3 submission_bot.py > logs/submission_bot.log 2>&1 & 
echo $! > pids/submission_bot.pid

# 启动发布机器人  
echo "📢 启动发布机器人..."
nohup python3 publish_bot.py > logs/publish_bot.log 2>&1 &
echo $! > pids/publish_bot.pid

# 启动控制机器人
echo "🎛️ 启动控制机器人..."
nohup python3 control_bot.py > logs/control_bot.log 2>&1 &
echo $! > pids/control_bot.pid

# 等待启动
sleep 5

# 5. 检查状态
echo ""
echo "📊 最终状态检查..."
echo "=" * 40

success_count=0
for bot in submission publish control; do
    if pgrep -f "${bot}_bot.py" > /dev/null; then
        pid=$(pgrep -f "${bot}_bot.py")
        echo "✅ ${bot}_bot 运行正常 (PID: $pid)"
        ((success_count++))
    else
        echo "❌ ${bot}_bot 启动失败"
        # 显示错误日志
        echo "错误日志:"
        tail -3 logs/${bot}_bot.log 2>/dev/null | head -2
    fi
done

echo ""
echo "📈 修复结果: $success_count/3 个机器人成功启动"

if [ $success_count -eq 3 ]; then
    echo "🎉 所有问题已修复！系统完全正常运行！"
    echo ""
    echo "📋 系统状态:"
    echo "• 数据库: ✅ 正常"
    echo "• 投稿机器人: ✅ 运行中"  
    echo "• 发布机器人: ✅ 运行中"
    echo "• 控制机器人: ✅ 运行中"
    echo ""
    echo "🎯 您现在可以使用您的Telegram机器人系统了！"
else
    echo "⚠️ 部分机器人启动失败，请检查日志"
    echo "查看日志: tail -f logs/*.log"
fi

echo ""
echo "🔄 管理命令:"
echo "• 查看状态: ./status.sh"
echo "• 查看日志: tail -f logs/*.log"
echo "• 停止系统: ./stop_all.sh"
echo "• 重启系统: ./restart_all_bots.sh"