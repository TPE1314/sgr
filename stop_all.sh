#!/bin/bash
# 停止所有电报机器人的脚本

echo "🛑 开始停止所有机器人..."

# 停止函数
stop_bot() {
    local bot_name=$1
    local pid_file="${bot_name}.pid"
    
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if ps -p $pid > /dev/null 2>&1; then
            echo "🔄 停止 $bot_name (PID: $pid)..."
            kill $pid
            
            # 等待进程结束
            local count=0
            while ps -p $pid > /dev/null 2>&1 && [ $count -lt 10 ]; do
                sleep 1
                count=$((count + 1))
            done
            
            # 如果还没结束，强制停止
            if ps -p $pid > /dev/null 2>&1; then
                echo "⚠️ 强制停止 $bot_name..."
                kill -9 $pid
            fi
            
            echo "✅ $bot_name 已停止"
        else
            echo "⚠️ $bot_name 进程不存在 (PID: $pid)"
        fi
        rm -f "$pid_file"
    else
        echo "⚠️ 找不到 $bot_name 的PID文件"
    fi
}

# 通过进程名停止
stop_by_name() {
    local script_name=$1
    local display_name=$2
    
    local pids=$(pgrep -f "$script_name")
    if [ -n "$pids" ]; then
        echo "🔄 通过进程名停止 $display_name..."
        for pid in $pids; do
            kill $pid 2>/dev/null
        done
        sleep 2
        
        # 检查是否还有进程
        local remaining_pids=$(pgrep -f "$script_name")
        if [ -n "$remaining_pids" ]; then
            echo "⚠️ 强制停止 $display_name..."
            for pid in $remaining_pids; do
                kill -9 $pid 2>/dev/null
            done
        fi
        echo "✅ $display_name 已停止"
    fi
}

# 使用PID文件停止
stop_bot "submission_bot"
stop_bot "publish_bot" 
stop_bot "control_bot"

# 通过进程名再次确认停止
stop_by_name "submission_bot.py" "投稿机器人"
stop_by_name "publish_bot.py" "发布机器人"
stop_by_name "control_bot.py" "控制机器人"

echo ""
echo "✅ 所有机器人已停止！"

# 清理临时文件
echo "🧹 清理临时文件..."
rm -f *.pid *.out

echo "🎯 停止完成！"