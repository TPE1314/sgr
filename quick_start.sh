#!/bin/bash

# 电报多管理员客服系统 - 快速启动脚本
# 用于开发和测试环境

set -e

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🚀 电报多管理员客服系统 - 快速启动${NC}"
echo "=========================================="

# 检查Python版本
echo -e "${YELLOW}检查Python环境...${NC}"
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python3未安装${NC}"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
echo -e "${GREEN}✅ Python版本: $PYTHON_VERSION${NC}"

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}创建虚拟环境...${NC}"
    python3 -m venv venv
    echo -e "${GREEN}✅ 虚拟环境创建完成${NC}"
fi

# 激活虚拟环境
echo -e "${YELLOW}激活虚拟环境...${NC}"
source venv/bin/activate
echo -e "${GREEN}✅ 虚拟环境已激活${NC}"

# 安装依赖
echo -e "${YELLOW}安装Python依赖...${NC}"
pip install --upgrade pip
pip install -r requirements.txt
echo -e "${GREEN}✅ 依赖安装完成${NC}"

# 检查配置文件
if [ ! -f "config.ini" ]; then
    echo -e "${RED}❌ 配置文件config.ini不存在${NC}"
    echo -e "${YELLOW}请先创建配置文件或复制config.ini.example${NC}"
    exit 1
fi

# 检查机器人Token
BOT_TOKEN=$(grep "^token" config.ini | cut -d'=' -f2 | tr -d ' ')
if [ "$BOT_TOKEN" = "YOUR_BOT_TOKEN_HERE" ]; then
    echo -e "${RED}❌ 请在config.ini中设置正确的机器人Token${NC}"
    echo -e "${YELLOW}获取Token: 在Telegram中联系@BotFather${NC}"
    exit 1
fi

echo -e "${GREEN}✅ 机器人Token已配置${NC}"

# 创建必要的目录
echo -e "${YELLOW}创建必要目录...${NC}"
mkdir -p uploads logs backups
echo -e "${GREEN}✅ 目录创建完成${NC}"

# 检查Redis
echo -e "${YELLOW}检查Redis服务...${NC}"
if ! command -v redis-cli &> /dev/null; then
    echo -e "${YELLOW}⚠️  Redis未安装，将使用内存存储（不推荐生产环境）${NC}"
    echo -e "${YELLOW}建议安装Redis: sudo apt install redis-server${NC}"
else
    if redis-cli ping &> /dev/null; then
        echo -e "${GREEN}✅ Redis服务运行正常${NC}"
    else
        echo -e "${YELLOW}⚠️  Redis服务未运行，尝试启动...${NC}"
        sudo systemctl start redis-server || echo -e "${YELLOW}无法启动Redis，将使用内存存储${NC}"
    fi
fi

# 启动机器人
echo -e "${GREEN}🎯 启动机器人...${NC}"
echo -e "${BLUE}按Ctrl+C停止机器人${NC}"
echo ""

python3 bot.py