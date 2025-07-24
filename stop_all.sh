#!/bin/bash
# 停止所有电报机器人的脚本

echo "🛑 开始停止所有机器人..."

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 停止函数（更新PID文件路径）
stop_bot() {
    local bot_name=$1
    local pid_file="pids/${bot_name}.pid"
    
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if ps -p $pid > /dev/null 2>&1; then
            echo -e "${BLUE}🔄 停止 $bot_name (PID: $pid)...${NC}"
            kill $pid
            
            # 等待进程结束
            local count=0
            while ps -p $pid > /dev/null 2>&1 && [ $count -lt 10 ]; do
                sleep 1
                count=$((count + 1))
            done
            
            # 如果还没结束，强制停止
            if ps -p $pid > /dev/null 2>&1; then
                echo -e "${YELLOW}⚠️ 强制停止 $bot_name...${NC}"
                kill -9 $pid
            fi
            
            echo -e "${GREEN}✅ $bot_name 已停止${NC}"
        else
            echo -e "${YELLOW}⚠️ $bot_name 进程不存在 (PID: $pid)${NC}"
        fi
        rm -f "$pid_file"
    else
        echo -e "${YELLOW}⚠️ 找不到 $bot_name 的PID文件${NC}"
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
echo -e "${BLUE}🧹 清理临时文件...${NC}"
rm -f *.pid *.out pids/*.pid

echo -e "${GREEN}🎯 停止完成！${NC}"

# 显示最终状态
echo
echo -e "${BLUE}📊 最终状态检查：${NC}"
if pgrep -f "submission_bot.py\|publish_bot.py\|control_bot.py" > /dev/null; then
    echo -e "${YELLOW}⚠️ 仍有机器人进程在运行${NC}"
    pgrep -f "submission_bot.py\|publish_bot.py\|control_bot.py"
else
    echo -e "${GREEN}✅ 所有机器人进程已完全停止${NC}"
fi