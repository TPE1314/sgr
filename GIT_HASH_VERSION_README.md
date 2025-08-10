# Git哈希版本功能说明

## 概述

本项目现在支持基于Git提交哈希值的版本号格式：`x.x.{commit_hash}`

## 版本格式

### 传统版本格式
- `v2.3.0` - 主版本.次版本.补丁版本
- `v2.3.1` - 小更新
- `v2.4.0` - 次版本更新

### Git哈希版本格式
- `v2.3.35396e8` - 主版本.次版本.Git提交哈希值
- `v3.1.35396e8` - 自定义主次版本的Git哈希版本

## 使用方法

### 1. 查看当前版本
```bash
python3 version_manager.py
# 或
python3 version_manager.py show
```

### 2. 更新为Git哈希版本
```bash
# 使用默认主次版本 (v2.3.{hash})
python3 version_manager.py git-hash

# 自定义主次版本 (v3.1.{hash})
python3 version_manager.py git-hash 3 1

# 自定义主次版本 (v1.0.{hash})
python3 version_manager.py git-hash 1 0
```

### 3. 传统版本管理
```bash
# 小更新
python3 version_manager.py patch

# 次版本更新
python3 version_manager.py minor

# 主版本更新
python3 version_manager.py major

# 设置指定版本
python3 version_manager.py set v2.5.0

# 预览下一版本
python3 version_manager.py next patch
```

## 功能特点

1. **自动获取Git提交哈希值** - 无需手动输入
2. **支持自定义主次版本号** - 可以指定任意的主版本和次版本
3. **向后兼容** - 传统版本管理功能完全保留
4. **智能版本解析** - 自动识别Git哈希版本和传统版本
5. **实时Git状态显示** - 显示当前Git提交信息和版本状态

## 示例

### 当前状态
```
📋 版本信息:
   当前版本: v2.3.0
   Git提交: 35396e8
   完整哈希: 35396e8c93c6b9ab29331d9eebda4dc47130293f
   ℹ️ 当前使用传统版本格式
   建议: 使用 'git-hash' 命令更新为Git哈希版本格式
```

### 更新为Git哈希版本
```bash
python3 version_manager.py git-hash
```

### 更新后的状态
```
📋 版本信息:
   当前版本: v2.3.35396e8
   Git提交: 35396e8
   完整哈希: 35396e8c93c6b9ab29331d9eebda4dc47130293f
   ✅ 当前使用Git哈希版本格式
```

## 优势

1. **精确追踪** - 版本号直接对应Git提交，便于代码追踪
2. **自动化** - 无需手动维护版本号，减少人为错误
3. **开发友好** - 开发者可以快速识别代码版本对应的Git提交
4. **部署便利** - 部署时可以精确知道代码版本
5. **调试支持** - 问题报告时可以精确定位到具体的代码版本

## 注意事项

1. **Git仓库要求** - 必须在Git仓库中使用此功能
2. **哈希值长度** - 默认使用短哈希值（7位），可通过代码修改为长哈希值
3. **版本文件** - 版本信息保存在 `.version` 文件中
4. **向后兼容** - 可以随时在传统版本和Git哈希版本之间切换

## 演示脚本

运行演示脚本来体验新功能：
```bash
python3 demo_git_hash_version.py
```

## 技术实现

- 使用 `subprocess.run()` 调用Git命令获取提交哈希值
- 支持短哈希值（7位）和长哈希值（40位）
- 智能版本解析，兼容传统版本格式
- 完整的错误处理和用户反馈