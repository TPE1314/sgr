#!/bin/bash
# 查看机器人状态的脚本

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${CYAN}📊 电报机器人状态监控${NC}"
echo "=========================="

# 检查进程状态（使用PID文件）
check_process_by_pid() {
    local bot_name=$1
    local display_name=$2
    local emoji=$3
    
    local pid_file="pids/${bot_name}.pid"
    
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if kill -0 "$pid" 2>/dev/null; then
            # 获取内存使用情况
            local memory=$(ps -p $pid -o rss= 2>/dev/null)
            local cpu=$(ps -p $pid -o %cpu= 2>/dev/null)
            local start_time=$(ps -p $pid -o lstart= 2>/dev/null)
            
            if [ -n "$memory" ]; then
                memory=$(echo "scale=1; $memory/1024" | bc 2>/dev/null || echo "N/A")
                cpu=$(echo "$cpu" | xargs)
                echo -e "${GREEN}${emoji} $display_name: 运行中${NC} (PID: $pid, 内存: ${memory}MB, CPU: ${cpu}%)"
            else
                echo -e "${GREEN}${emoji} $display_name: 运行中${NC} (PID: $pid)"
            fi
        else
            echo -e "${RED}${emoji} $display_name: 进程已停止${NC} (PID文件存在但进程不存在)"
            # 清理无效的PID文件
            rm -f "$pid_file"
        fi
    else
        # 备用方法：通过进程名查找
        local pid=$(pgrep -f "${bot_name}.py")
        if [ -n "$pid" ]; then
            echo -e "${YELLOW}${emoji} $display_name: 运行中${NC} (PID: $pid, 无PID文件)"
        else
            echo -e "${RED}${emoji} $display_name: 未运行${NC}"
        fi
    fi
}

# 检查日志文件最后更新时间
check_log_activity() {
    local bot_name=$1
    local log_file="logs/${bot_name}.log"
    
    if [ -f "$log_file" ]; then
        local last_modified=$(stat -c %Y "$log_file" 2>/dev/null || stat -f %m "$log_file" 2>/dev/null)
        local current_time=$(date +%s)
        local diff=$((current_time - last_modified))
        
        if [ $diff -lt 300 ]; then  # 5分钟内有活动
            echo -e "  ${GREEN}📝 日志活跃${NC} (最后更新: $((diff/60))分钟前)"
        elif [ $diff -lt 3600 ]; then  # 1小时内有活动
            echo -e "  ${YELLOW}📝 日志较旧${NC} (最后更新: $((diff/60))分钟前)"
        else
            echo -e "  ${RED}📝 日志很旧${NC} (最后更新: $((diff/3600))小时前)"
        fi
    else
        echo -e "  ${RED}📝 无日志文件${NC}"
    fi
}

# 检查各个机器人
echo -e "${BLUE}🤖 机器人状态：${NC}"
echo "--------------------"
check_process_by_pid "submission_bot" "投稿机器人" "📝"
check_log_activity "submission_bot"

check_process_by_pid "publish_bot" "发布机器人" "📢"
check_log_activity "publish_bot"

check_process_by_pid "control_bot" "控制机器人" "🎛️"
check_log_activity "control_bot"

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
echo -e "${PURPLE}📁 日志文件：${NC}"
echo "================================"

# 检查日志文件
for bot_name in submission_bot publish_bot control_bot; do
    log_file="logs/${bot_name}.log"
    if [ -f "$log_file" ]; then
        size=$(du -h "$log_file" | cut -f1)
        lines=$(wc -l < "$log_file")
        echo -e "${GREEN}📄${NC} $log_file: ${size} (${lines} 行)"
    else
        echo -e "${RED}📄${NC} $log_file: 不存在"
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