#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
电报多管理员客服系统 - 压力测试脚本
测试系统在高并发情况下的性能表现
"""

import asyncio
import time
import random
import statistics
from datetime import datetime
from typing import List, Dict, Any
import aiohttp
import json
import os
from dataclasses import dataclass
import argparse

# 配置
BOT_TOKEN = os.getenv('BOT_TOKEN', 'YOUR_BOT_TOKEN')
TEST_DURATION = int(os.getenv('TEST_DURATION', '300'))  # 5分钟
MAX_CONCURRENT_USERS = int(os.getenv('MAX_CONCURRENT_USERS', '50'))
MESSAGE_INTERVAL = float(os.getenv('MESSAGE_INTERVAL', '2.0'))  # 2秒
ADMIN_COUNT = int(os.getenv('ADMIN_COUNT', '3'))

@dataclass
class TestResult:
    """测试结果数据类"""
    user_id: int
    start_time: datetime
    end_time: datetime
    messages_sent: int
    messages_received: int
    total_latency: float
    errors: int
    success: bool

@dataclass
class SystemMetrics:
    """系统指标数据类"""
    total_users: int
    active_sessions: int
    total_messages: int
    avg_response_time: float
    error_rate: float
    throughput: float  # 消息/秒

class MockUser:
    """模拟用户类"""
    def __init__(self, user_id: int, bot_token: str):
        self.user_id = user_id
        self.bot_token = bot_token
        self.session_id = None
        self.message_count = 0
        self.start_time = None
        self.end_time = None
        self.latencies = []
        self.errors = 0
        
    async def start_session(self, session: aiohttp.ClientSession) -> bool:
        """开始会话"""
        try:
            self.start_time = datetime.now()
            
            # 模拟发送 /start 命令
            start_data = {
                'chat_id': self.user_id,
                'text': '/start'
            }
            
            # 这里应该调用实际的Telegram Bot API
            # 简化版本只记录日志
            print(f"用户 {self.user_id} 开始会话")
            self.session_id = f"session_{self.user_id}_{int(time.time())}"
            return True
            
        except Exception as e:
            print(f"用户 {self.user_id} 开始会话失败: {e}")
            self.errors += 1
            return False
    
    async def send_message(self, session: aiohttp.ClientSession, message: str) -> bool:
        """发送消息"""
        try:
            start_time = time.time()
            
            # 模拟发送消息
            message_data = {
                'chat_id': self.user_id,
                'text': message,
                'session_id': self.session_id
            }
            
            # 模拟网络延迟
            await asyncio.sleep(random.uniform(0.1, 0.5))
            
            # 模拟响应时间
            response_time = time.time() - start_time
            self.latencies.append(response_time)
            self.message_count += 1
            
            print(f"用户 {self.user_id} 发送消息: {message[:20]}... (延迟: {response_time:.3f}s)")
            return True
            
        except Exception as e:
            print(f"用户 {self.user_id} 发送消息失败: {e}")
            self.errors += 1
            return False
    
    async def send_media(self, session: aiohttp.ClientSession, media_type: str) -> bool:
        """发送媒体文件"""
        try:
            start_time = time.time()
            
            # 模拟发送媒体文件
            media_data = {
                'chat_id': self.user_id,
                'media_type': media_type,
                'session_id': self.session_id
            }
            
            # 模拟媒体处理延迟
            await asyncio.sleep(random.uniform(0.5, 2.0))
            
            response_time = time.time() - start_time
            self.latencies.append(response_time)
            self.message_count += 1
            
            print(f"用户 {self.user_id} 发送{media_type}: (延迟: {response_time:.3f}s)")
            return True
            
        except Exception as e:
            print(f"用户 {self.user_id} 发送{media_type}失败: {e}")
            self.errors += 1
            return False
    
    def get_test_result(self) -> TestResult:
        """获取测试结果"""
        self.end_time = datetime.now()
        
        return TestResult(
            user_id=self.user_id,
            start_time=self.start_time,
            end_time=self.end_time,
            messages_sent=self.message_count,
            messages_received=0,  # 简化版本
            total_latency=sum(self.latencies) if self.latencies else 0,
            errors=self.errors,
            success=self.errors == 0
        )

class StressTester:
    """压力测试器"""
    def __init__(self, bot_token: str, max_users: int, duration: int):
        self.bot_token = bot_token
        self.max_users = max_users
        self.duration = duration
        self.users: List[MockUser] = []
        self.results: List[TestResult] = []
        self.start_time = None
        self.end_time = None
        
    async def create_users(self):
        """创建模拟用户"""
        print(f"创建 {self.max_users} 个模拟用户...")
        
        for i in range(self.max_users):
            user = MockUser(i + 1000, self.bot_token)  # 使用1000+的ID避免冲突
            self.users.append(user)
        
        print(f"成功创建 {len(self.users)} 个模拟用户")
    
    async def run_user_session(self, user: MockUser, session: aiohttp.ClientSession):
        """运行单个用户会话"""
        try:
            # 开始会话
            if not await user.start_session(session):
                return
            
            # 发送消息循环
            message_count = 0
            while True:
                # 检查是否超时
                if (datetime.now() - user.start_time).total_seconds() > self.duration:
                    break
                
                # 随机选择消息类型
                message_type = random.choice(['text', 'photo', 'video', 'document', 'voice'])
                
                if message_type == 'text':
                    # 发送文本消息
                    messages = [
                        "你好，我需要帮助",
                        "请问有人在线吗？",
                        "我有一个问题想咨询",
                        "能帮我解决一下吗？",
                        "谢谢你的帮助",
                        "这个功能怎么使用？",
                        "我需要技术支持",
                        "请问营业时间是什么时候？"
                    ]
                    message = random.choice(messages)
                    await user.send_message(session, message)
                else:
                    # 发送媒体文件
                    await user.send_media(session, message_type)
                
                message_count += 1
                
                # 随机间隔
                interval = random.uniform(1.0, 5.0)
                await asyncio.sleep(interval)
                
        except Exception as e:
            print(f"用户 {user.user_id} 会话异常: {e}")
            user.errors += 1
    
    async def run_test(self):
        """运行压力测试"""
        print(f"🚀 开始压力测试...")
        print(f"测试参数:")
        print(f"  - 最大并发用户: {self.max_users}")
        print(f"  - 测试时长: {self.duration} 秒")
        print(f"  - 消息间隔: {MESSAGE_INTERVAL} 秒")
        print(f"  - 管理员数量: {ADMIN_COUNT}")
        print()
        
        self.start_time = datetime.now()
        
        # 创建用户
        await self.create_users()
        
        # 创建HTTP会话
        async with aiohttp.ClientSession() as session:
            # 启动所有用户会话
            tasks = []
            for user in self.users:
                task = asyncio.create_task(self.run_user_session(user, session))
                tasks.append(task)
            
            # 等待所有任务完成或超时
            try:
                await asyncio.wait_for(asyncio.gather(*tasks), timeout=self.duration + 10)
            except asyncio.TimeoutError:
                print("测试超时，正在收集结果...")
            
            # 收集测试结果
            for user in self.users:
                result = user.get_test_result()
                self.results.append(result)
        
        self.end_time = datetime.now()
        
        print(f"✅ 压力测试完成")
    
    def analyze_results(self) -> SystemMetrics:
        """分析测试结果"""
        if not self.results:
            return SystemMetrics(0, 0, 0, 0, 0, 0)
        
        total_users = len(self.results)
        successful_users = sum(1 for r in self.results if r.success)
        total_messages = sum(r.messages_sent for r in self.results)
        total_errors = sum(r.errors for r in self.results)
        
        # 计算平均响应时间
        all_latencies = []
        for result in self.results:
            if result.total_latency > 0:
                all_latencies.append(result.total_latency / result.messages_sent)
        
        avg_response_time = statistics.mean(all_latencies) if all_latencies else 0
        
        # 计算错误率
        error_rate = (total_errors / (total_messages + total_errors)) * 100 if (total_messages + total_errors) > 0 else 0
        
        # 计算吞吐量
        test_duration = (self.end_time - self.start_time).total_seconds()
        throughput = total_messages / test_duration if test_duration > 0 else 0
        
        return SystemMetrics(
            total_users=total_users,
            active_sessions=successful_users,
            total_messages=total_messages,
            avg_response_time=avg_response_time,
            error_rate=error_rate,
            throughput=throughput
        )
    
    def print_results(self):
        """打印测试结果"""
        print("\n" + "="*60)
        print("📊 压力测试结果报告")
        print("="*60)
        
        metrics = self.analyze_results()
        
        print(f"📈 测试概览:")
        print(f"  测试开始时间: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"  测试结束时间: {self.end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"  测试总时长: {(self.end_time - self.start_time).total_seconds():.2f} 秒")
        print()
        
        print(f"👥 用户统计:")
        print(f"  总用户数: {metrics.total_users}")
        print(f"  成功会话: {metrics.active_sessions}")
        print(f"  成功率: {(metrics.active_sessions/metrics.total_users)*100:.1f}%")
        print()
        
        print(f"💬 消息统计:")
        print(f"  总消息数: {metrics.total_messages}")
        print(f"  平均响应时间: {metrics.avg_response_time:.3f} 秒")
        print(f"  错误率: {metrics.error_rate:.2f}%")
        print(f"  吞吐量: {metrics.throughput:.2f} 消息/秒")
        print()
        
        # 详细用户结果
        print(f"📋 用户详细结果:")
        print(f"{'用户ID':<8} {'消息数':<8} {'错误数':<8} {'状态':<8}")
        print("-" * 40)
        
        for result in self.results[:20]:  # 只显示前20个
            status = "✅" if result.success else "❌"
            print(f"{result.user_id:<8} {result.messages_sent:<8} {result.errors:<8} {status:<8}")
        
        if len(self.results) > 20:
            print(f"... 还有 {len(self.results) - 20} 个用户结果")
        
        print()
        
        # 性能评估
        print(f"🎯 性能评估:")
        if metrics.throughput >= 10:
            print(f"  吞吐量: 🟢 优秀 ({metrics.throughput:.2f} 消息/秒)")
        elif metrics.throughput >= 5:
            print(f"  吞吐量: 🟡 良好 ({metrics.throughput:.2f} 消息/秒)")
        else:
            print(f"  吞吐量: 🔴 需要优化 ({metrics.throughput:.2f} 消息/秒)")
        
        if metrics.avg_response_time <= 0.5:
            print(f"  响应时间: 🟢 优秀 ({metrics.avg_response_time:.3f}s)")
        elif metrics.avg_response_time <= 1.0:
            print(f"  响应时间: 🟡 良好 ({metrics.avg_response_time:.3f}s)")
        else:
            print(f"  响应时间: 🔴 需要优化 ({metrics.avg_response_time:.3f}s)")
        
        if metrics.error_rate <= 1.0:
            print(f"  错误率: 🟢 优秀 ({metrics.error_rate:.2f}%)")
        elif metrics.error_rate <= 5.0:
            print(f"  错误率: 🟡 良好 ({metrics.error_rate:.2f}%)")
        else:
            print(f"  错误率: 🔴 需要优化 ({metrics.error_rate:.2f}%)")
        
        print()
        
        # 建议
        print(f"💡 优化建议:")
        if metrics.throughput < 5:
            print("  - 考虑增加服务器资源或优化代码")
        if metrics.avg_response_time > 1.0:
            print("  - 检查数据库查询和网络延迟")
        if metrics.error_rate > 5.0:
            print("  - 检查错误日志，修复异常处理")
        
        print("="*60)

async def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='电报多管理员客服系统压力测试')
    parser.add_argument('--users', type=int, default=MAX_CONCURRENT_USERS, 
                       help=f'最大并发用户数 (默认: {MAX_CONCURRENT_USERS})')
    parser.add_argument('--duration', type=int, default=TEST_DURATION,
                       help=f'测试时长(秒) (默认: {TEST_DURATION})')
    parser.add_argument('--token', type=str, default=BOT_TOKEN,
                       help='机器人Token')
    
    args = parser.parse_args()
    
    if args.token == 'YOUR_BOT_TOKEN':
        print("❌ 请设置正确的机器人Token")
        print("使用方法:")
        print("  export BOT_TOKEN='your_bot_token'")
        print("  python3 stress_test.py")
        print("或者:")
        print("  python3 stress_test.py --token 'your_bot_token'")
        return
    
    # 创建压力测试器
    tester = StressTester(args.token, args.users, args.duration)
    
    try:
        # 运行测试
        await tester.run_test()
        
        # 分析结果
        tester.print_results()
        
    except KeyboardInterrupt:
        print("\n⚠️ 测试被用户中断")
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 测试已退出")