# 🚨 数据库紧急修复指南

当您遇到以下错误时使用此指南：
```
ModuleNotFoundError: No module named 'database'
```

## 🔧 快速修复

### 方法1: 使用v2.3.0紧急修复脚本 (推荐)

```bash
# 下载并运行紧急修复脚本
curl -fsSL https://raw.githubusercontent.com/TPE1314/sgr/main/emergency_db_fix_v2_3_0.py -o emergency_db_fix_v2_3_0.py
chmod +x emergency_db_fix_v2_3_0.py
python3 emergency_db_fix_v2_3_0.py
```

或者如果您已在项目目录中：
```bash
python3 emergency_db_fix_v2_3_0.py
```

### 方法2: 手动修复

1. **检查database.py文件**:
   ```bash
   ls -la database.py
   ```

2. **如果文件不存在，创建它**:
   ```bash
   curl -fsSL https://raw.githubusercontent.com/TPE1314/sgr/main/database.py -o database.py
   ```

3. **设置Python路径**:
   ```bash
   export PYTHONPATH=$PYTHONPATH:$(pwd)
   ```

4. **测试导入**:
   ```bash
   python3 -c "from database import DatabaseManager; print('成功!')"
   ```

## 🎯 修复脚本功能

`emergency_db_fix_v2_3_0.py` 脚本会自动：

- ✅ 检查必要文件状态
- ✅ 创建缺失的 `database.py` 文件
- ✅ 创建缺失的 `config_manager.py` 文件
- ✅ 设置正确的Python环境路径
- ✅ 清理模块缓存
- ✅ 测试数据库导入和创建
- ✅ 创建必要的目录结构
- ✅ 验证修复结果

## 📊 修复过程示例

```bash
$ python3 emergency_db_fix_v2_3_0.py

============================================================
🔧 v2.3.0 紧急数据库修复工具
============================================================
专门解决: ModuleNotFoundError: No module named 'database'

📁 检查文件状态...
   ❌ database.py
   ❌ config_manager.py
   ✅ config.ini

🔧 创建database.py文件...
✅ database.py 文件创建成功

🔧 创建config_manager.py文件...
✅ config_manager.py 文件创建成功

🐍 设置Python环境...
✅ Python路径已设置: 6 个路径
✅ 已清理 0 个模块缓存

🧪 测试数据库导入...
✅ 标准导入成功

🗄️ 测试数据库创建...
📝 创建数据库实例...
数据库表初始化完成
✅ 数据库创建成功
🧪 测试基本数据库操作...
✅ 数据库读写测试通过

📁 创建必要目录...
✅ logs/
✅ pids/
✅ backups/
✅ temp/

============================================================
📊 修复结果总结
============================================================
📄 文件状态:
   ✅ database.py
   ✅ config_manager.py

📁 目录状态:
   ✅ logs/
   ✅ pids/
   ✅ backups/
   ✅ temp/

🗄️ 数据库状态:
   ✅ telegram_bot.db

🎉 数据库问题修复完成！

💡 现在可以重新运行安装脚本或启动机器人
   python3 submission_bot.py
   python3 publish_bot.py
   python3 control_bot.py
```

## 🚀 修复完成后

修复完成后，您可以：

1. **重新运行一键安装脚本**:
   ```bash
   ./quick_setup.sh
   ```

2. **直接启动机器人**:
   ```bash
   python3 submission_bot.py
   python3 publish_bot.py
   python3 control_bot.py
   ```

3. **使用管理脚本**:
   ```bash
   ./start_all.sh
   ./status.sh
   ```

## ❓ 常见问题

### Q: 脚本运行后仍然报错？
A: 检查Python版本和虚拟环境：
```bash
python3 --version
which python3
source venv/bin/activate  # 如果有虚拟环境
```

### Q: 权限错误？
A: 给脚本添加执行权限：
```bash
chmod +x emergency_db_fix_v2_3_0.py
```

### Q: 网络问题无法下载？
A: 使用离线模式，脚本会创建基础的database.py文件。

## 📞 获取帮助

如果紧急修复脚本无法解决问题：

1. 查看详细错误信息
2. 检查Python环境
3. 重新下载完整项目：
   ```bash
   git clone https://github.com/TPE1314/sgr.git
   cd sgr
   ./quick_setup.sh
   ```

---

**v2.3.0 = 智能修复 + 零手动干预！** 🚀