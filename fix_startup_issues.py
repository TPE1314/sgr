#!/usr/bin/env python3
"""
修复机器人启动问题的脚本
"""

import sys
import os
import subprocess
import signal

def colored_print(message, color):
    colors = {
        'red': '\033[91m',
        'green': '\033[92m',
        'yellow': '\033[93m',
        'blue': '\033[94m',
        'cyan': '\033[96m',
        'white': '\033[97m',
        'reset': '\033[0m'
    }
    print(f"{colors.get(color, '')}{message}{colors['reset']}")

def stop_all_bots():
    """停止所有正在运行的机器人"""
    colored_print("🛑 停止所有正在运行的机器人...", "yellow")
    
    # 使用stop_all.sh
    if os.path.exists("stop_all.sh"):
        subprocess.run(["./stop_all.sh"], check=False)
    
    # 强制停止相关进程
    try:
        subprocess.run(["pkill", "-f", "submission_bot.py"], check=False)
        subprocess.run(["pkill", "-f", "publish_bot.py"], check=False) 
        subprocess.run(["pkill", "-f", "control_bot.py"], check=False)
        colored_print("✅ 所有机器人进程已停止", "green")
    except Exception as e:
        colored_print(f"⚠️ 停止进程时出现警告: {e}", "yellow")

def clean_pid_files():
    """清理PID文件"""
    colored_print("🧹 清理PID文件...", "blue")
    
    if os.path.exists("pids"):
        for file in os.listdir("pids"):
            if file.endswith(".pid"):
                try:
                    os.remove(os.path.join("pids", file))
                    colored_print(f"✅ 删除 pids/{file}", "green")
                except Exception as e:
                    colored_print(f"⚠️ 删除 pids/{file} 失败: {e}", "yellow")

def test_individual_bots():
    """单独测试每个机器人"""
    colored_print("🧪 单独测试每个机器人...", "blue")
    
    bots = [
        ("submission_bot.py", "投稿机器人"),
        ("publish_bot.py", "发布机器人"), 
        ("control_bot.py", "控制机器人")
    ]
    
    results = {}
    
    for bot_file, bot_name in bots:
        colored_print(f"测试 {bot_name}...", "cyan")
        
        # 测试语法
        result = subprocess.run([
            "python3", "-m", "py_compile", bot_file
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            colored_print(f"✅ {bot_name} 语法检查通过", "green")
            results[bot_name] = "语法正确"
        else:
            colored_print(f"❌ {bot_name} 语法错误:", "red")
            colored_print(result.stderr, "red")
            results[bot_name] = f"语法错误: {result.stderr}"
            continue
            
        # 测试导入
        test_import = f"""
import sys
import os
sys.path.insert(0, os.getcwd())
try:
    with open('{bot_file}', 'r') as f:
        code = f.read()
    # 移除直接执行的部分
    if 'if __name__' in code:
        code = code.split('if __name__')[0]
    compile(code, '{bot_file}', 'exec')
    print('IMPORT_SUCCESS')
except Exception as e:
    print(f'IMPORT_ERROR: {{e}}')
"""
        
        result = subprocess.run([
            "python3", "-c", test_import
        ], capture_output=True, text=True, timeout=10)
        
        if "IMPORT_SUCCESS" in result.stdout:
            colored_print(f"✅ {bot_name} 导入测试通过", "green")
            results[bot_name] = "测试通过"
        else:
            colored_print(f"❌ {bot_name} 导入测试失败:", "red")
            error_msg = result.stderr or result.stdout
            colored_print(error_msg, "red")
            results[bot_name] = f"导入错误: {error_msg}"
    
    return results

def show_test_results(results):
    """显示测试结果"""
    colored_print("\n📊 测试结果总结:", "blue")
    colored_print("=" * 50, "cyan")
    
    for bot_name, result in results.items():
        if "测试通过" in result:
            colored_print(f"✅ {bot_name}: {result}", "green")
        else:
            colored_print(f"❌ {bot_name}: {result}", "red")

def provide_solutions():
    """提供解决方案"""
    colored_print("\n💡 解决方案:", "yellow")
    colored_print("=" * 50, "cyan")
    
    solutions = [
        "1. 检查配置文件:",
        "   cat config.ini",
        "",
        "2. 重新激活虚拟环境:",
        "   source venv/bin/activate",
        "",
        "3. 重新安装依赖:",
        "   pip install -r requirements.txt",
        "",
        "4. 检查Token是否有效:",
        "   检查config.ini中的bot_token是否正确",
        "",
        "5. 手动启动单个机器人进行调试:",
        "   python3 submission_bot.py",
        "   python3 publish_bot.py",
        "   python3 control_bot.py",
        "",
        "6. 查看详细日志:",
        "   tail -f logs/*.log",
        "",
        "7. 重新运行一键安装:",
        "   ./quick_setup.sh",
    ]
    
    for solution in solutions:
        if solution.startswith(("   ", "       ")):
            colored_print(solution, "cyan")
        elif solution.startswith(("1.", "2.", "3.", "4.", "5.", "6.", "7.")):
            colored_print(solution, "yellow")
        else:
            print(solution)

def main():
    colored_print("🔧 机器人启动问题修复工具", "blue")
    colored_print("=" * 50, "cyan")
    
    # 步骤1: 停止所有机器人
    stop_all_bots()
    
    # 步骤2: 清理PID文件
    clean_pid_files()
    
    # 步骤3: 测试各个机器人
    results = test_individual_bots()
    
    # 步骤4: 显示结果
    show_test_results(results)
    
    # 步骤5: 提供解决方案
    provide_solutions()
    
    # 步骤6: 询问是否尝试重新启动
    colored_print("\n🚀 是否尝试重新启动机器人?", "yellow")
    choice = input("输入 y 重新启动, 或按回车跳过: ").strip().lower()
    
    if choice == 'y':
        colored_print("🚀 重新启动机器人...", "blue")
        if os.path.exists("start_all.sh"):
            subprocess.run(["./start_all.sh"])
        else:
            colored_print("❌ start_all.sh 不存在", "red")
    
    colored_print("\n🎉 修复工具执行完成！", "green")

if __name__ == "__main__":
    main()