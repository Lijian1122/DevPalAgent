# 平台安装脚本生成器测试

## 项目概述

这是一个安装脚本项目，用于生成 Claude Code CLI 的平台安装脚本。

本项目是安装脚本类型，不需要 C++ 编译、CMake 配置和测试。

## 功能需求

### REQ-001: 生成平台安装脚本
- 为 macOS/Linux 生成 `install_claude_cli.sh` shell 脚本
- 为 Windows 生成 `install_claude_cli.bat` 批处理脚本
- 不生成 Python 安装脚本
- 支持基本环境检查：Claude Code CLI、Node.js、npm
- 当 Claude Code CLI 已安装时输出版本并成功退出
- 如果 Node.js 未安装，下载指定 LTS 版本 Node.js 到当前目录的 `.nodejs/` 并使用本地 Node.js 继续后续流程，默认版本为 `v24.15.0`，可通过 `NODE_VERSION` 覆盖
- 未安装 Claude Code CLI 时执行 `npm install -g @anthropic-ai/claude-code`
- 如果 npm 安装失败、超时或处于国内网络环境，自动使用淘宝/npmmirror 镜像 `https://registry.npmmirror.com` 重试
- 安装后验证 `claude` 命令可用
- 失败时返回非零退出码
- 这是一个安装工具项目

## 验收标准

- [ ] 生成 macOS/Linux shell 安装脚本文件
- [ ] 生成 Windows bat 安装脚本文件
- [ ] 不生成 Python 安装脚本文件
- [ ] 脚本包含 Claude Code CLI、Node.js、npm 环境检查
- [ ] Node.js 缺失时脚本能够下载指定 LTS 版本 Node.js 到当前目录并继续安装
- [ ] npm 默认安装失败或超时时脚本能够使用淘宝/npmmirror 镜像重试
- [ ] 脚本能够执行安装命令并验证结果
- [ ] 安装脚本项目跳过 C++ 编译、CMake 配置和测试阶段
