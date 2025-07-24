#!/bin/bash
# 查看机器人状态的脚本

echo "📊 电报机器人状态监控"
echo "=========================="

# 检查进程状态
check_process() {
    local script_name=$1
    local display_name=$2
    
    local pid=$(pgrep -f "$script_name")
    if [ -n "$pid" ]; then
        # 获取内存使用情况
        local memory=$(ps -p $pid -o rss= 2>/dev/null)
        if [ -n "$memory" ]; then
            memory=$(echo "scale=1; $memory/1024" | bc)
            echo "🟢 $display_name: 运行中 (PID: $pid, 内存: ${memory}MB)"
        else
            echo "🟢 $display_name: 运行中 (PID: $pid)"
        fi
    else
        echo "🔴 $display_name: 未运行"
    fi
}

# 检查各个机器人
check_process "submission_bot.py" "投稿机器人"
check_process "publish_bot.py" "发布机器人"
check_process "control_bot.py" "控制机器人"

echo ""
echo "📋 系统信息："
echo "================================"

# CPU使用率
if command -v top >/dev/null 2>&1; then
    cpu_usage=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1)
    echo "🖥️ CPU使用率: ${cpu_usage}%"
fi

# 内存使用情况
if command -v free >/dev/null 2>&1; then
    memory_info=$(free -h | grep "Mem:")
    total=$(echo $memory_info | awk '{print $2}')
    used=$(echo $memory_info | awk '{print $3}')
    available=$(echo $memory_info | awk '{print $7}')
    echo "💾 内存使用: $used / $total (可用: $available)"
fi

# 磁盘使用情况
if command -v df >/dev/null 2>&1; then
    disk_info=$(df -h / | tail -1)
    disk_used=$(echo $disk_info | awk '{print $3}')
    disk_total=$(echo $disk_info | awk '{print $2}')
    disk_percent=$(echo $disk_info | awk '{print $5}')
    echo "💿 磁盘使用: $disk_used / $disk_total ($disk_percent)"
fi

echo ""
echo "📁 日志文件："
echo "================================"

# 检查日志文件
for log_file in submission_bot.log publish_bot.log control_bot.log; do
    if [ -f "$log_file" ]; then
        size=$(du -h "$log_file" | cut -f1)
        lines=$(wc -l < "$log_file")
        echo "📄 $log_file: ${size} (${lines} 行)"
    else
        echo "📄 $log_file: 不存在"
    fi
done

echo ""
echo "⏰ 检查时间: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""
echo "📋 常用命令："
echo "• 启动所有: ./start_all.sh"
echo "• 停止所有: ./stop_all.sh"
echo "• 查看日志: tail -f *.log"
echo "• 实时监控: watch -n 5 ./status.sh"