# 📋 版本管理指南

## 🎯 特殊版本递增规则

电报机器人投稿系统使用特殊的版本递增规则：
- **小更新**: 尾数递增，最多到 7
- **尾数到 7**: 中间位 +1，尾数重置为 0
- **主版本**: 主版本 +1，其他位重置为 0

## 📈 版本递增示例

```
v2.3.0  # 当前版本
v2.3.1  # 小更新 1
v2.3.2  # 小更新 2
v2.3.3  # 小更新 3
v2.3.4  # 小更新 4
v2.3.5  # 小更新 5
v2.3.6  # 小更新 6
v2.3.7  # 小更新 7 (尾数上限)
v2.4.0  # 中间位 +1，尾数重置
v2.4.1  # 继续小更新
...
v2.4.7  # 再次到达上限
v2.5.0  # 中间位继续 +1
```

## 🛠️ 版本管理工具

### 查看当前版本信息
```bash
python3 version_manager.py
```

输出示例：
```
==================================================
🎯 版本管理工具
==================================================
📋 当前版本: v2.3.0
📈 下一个小更新: v2.3.1
📊 下一个中间更新: v2.4.0
🚀 下一个主版本: v3.0.0

ℹ️ 尾数可更新 7 次到达上限
```

### 执行版本更新

#### 小更新 (Bug修复、小改进)
```bash
python3 version_manager.py patch
# v2.3.0 -> v2.3.1
```

#### 中间位更新 (新功能)
```bash
python3 version_manager.py minor
# v2.3.7 -> v2.4.0
```

#### 主版本更新 (重大更新)
```bash
python3 version_manager.py major
# v2.4.7 -> v3.0.0
```

### 其他功能

#### 设置指定版本
```bash
python3 version_manager.py set v2.5.0
```

#### 预览下一版本
```bash
python3 version_manager.py next patch
# 输出: 📋 下一个patch版本: v2.3.1
```

## ⚙️ 编程接口

### 在代码中使用
```python
from update_service import UpdateService

# 创建更新服务实例
update_service = UpdateService()

# 获取当前版本
current = update_service.get_current_version()
print(f"当前版本: {current}")

# 小更新
new_version = update_service.increment_version("patch")
print(f"新版本: {new_version}")

# 预览下一版本
next_version = update_service.get_next_version("minor")
print(f"下一个中间版本: {next_version}")
```

### 在控制机器人中集成
```python
# 版本更新命令
@dp.message_handler(commands=['update_version'])
async def update_version_command(message: types.Message):
    """版本更新命令"""
    args = message.get_args().split()
    
    if not args:
        # 显示版本信息
        current = update_service.get_current_version()
        next_patch = update_service.get_next_version("patch")
        next_minor = update_service.get_next_version("minor")
        
        text = f"""
📋 **版本信息**

📱 当前版本: `{current}`
📈 下一个小更新: `{next_patch}`
📊 下一个中间更新: `{next_minor}`

**使用方法:**
• `/update_version patch` - 小更新
• `/update_version minor` - 中间位更新
• `/update_version major` - 主版本更新
        """
        await message.reply(text, parse_mode='Markdown')
        return
    
    version_type = args[0].lower()
    
    if version_type in ['patch', 'minor', 'major']:
        old_version = update_service.get_current_version()
        new_version = update_service.increment_version(version_type)
        
        await message.reply(
            f"✅ 版本已更新\n"
            f"📱 {old_version} → {new_version}",
            parse_mode='Markdown'
        )
    else:
        await message.reply("❌ 无效的版本类型，请使用: patch, minor, major")
```

## 📊 版本类型说明

| 类型 | 命令 | 场景 | 示例 |
|------|------|------|------|
| **小更新** | `patch` | Bug修复、小改进、文档更新 | v2.3.0 → v2.3.1 |
| **中间更新** | `minor` | 新功能、重要改进 | v2.3.7 → v2.4.0 |
| **主版本** | `major` | 重大更新、架构变更 | v2.9.7 → v3.0.0 |

## 🔄 自动化工作流

### Git Hook 集成
```bash
#!/bin/bash
# .git/hooks/pre-commit
# 每次提交前自动执行小更新

echo "🔧 自动执行版本小更新..."
python3 version_manager.py patch

# 将新版本添加到提交
git add .version
```

### CI/CD 集成
```yaml
# .github/workflows/version.yml
name: Version Management

on:
  push:
    branches: [ main ]

jobs:
  update-version:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    
    - name: Auto increment version
      run: |
        python3 version_manager.py patch
        
    - name: Commit new version
      run: |
        git config --local user.email "action@github.com"
        git config --local user.name "GitHub Action"
        git add .version
        git commit -m "Auto: version update" || exit 0
        git push
```

## 🎯 最佳实践

### 1. 版本更新时机
- **每次Bug修复**: 使用 `patch`
- **添加新功能**: 使用 `minor`
- **重大更新**: 使用 `major`

### 2. 版本命名一致性
- 始终使用 `vx.x.x` 格式
- 不要手动编辑版本号
- 通过工具统一管理

### 3. 发布流程
```bash
# 1. 完成开发
git add .
git commit -m "feat: 新功能开发完成"

# 2. 更新版本
python3 version_manager.py minor

# 3. 创建发布标签
version=$(cat .version)
git tag -a $version -m "Release $version"

# 4. 推送到远程
git push origin main --tags
```

## 📞 支持与帮助

### 查看帮助
```bash
python3 version_manager.py help
```

### 常见问题

**Q: 如何跳过自动递增中间位？**
A: 不能跳过，这是设计的特殊规则。尾数到7后必须递增中间位。

**Q: 可以手动设置任意版本吗？**
A: 可以使用 `python3 version_manager.py set v2.5.0` 设置任意版本。

**Q: 版本文件在哪里？**
A: 版本信息存储在项目根目录的 `.version` 文件中。

---

**遵循版本规则，保持系统一致性！** 🚀