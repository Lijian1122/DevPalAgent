# -*- coding: utf-8 -*-
"""
Chinese (zh) message catalog
"""

MESSAGES = {
    # Common
    "common.yes": "是",
    "common.no": "否",
    "common.success": "成功",
    "common.error": "错误",
    "common.warning": "警告",
    "common.info": "信息",

    # Installation
    "install.title": "Claude Code CLI 安装脚本",
    "install.welcome": "欢迎使用 Claude Code CLI 一键安装脚本",
    "install.checking_node": "正在检查 Node.js 安装...",
    "install.node_found": "找到 Node.js {version}",
    "install.node_not_found": "未找到 Node.js。请先安装 Node.js。",
    "install.node_version_low": "Node.js 版本过低（需要 >= {min_version}）",
    "install.checking_npm": "正在检查 npm 安装...",
    "install.npm_found": "找到 npm {version}",
    "install.npm_missing": "未找到 npm",
    "install.installing": "正在安装 @anthropic-ai/claude-code...",
    "install.install_success": "安装成功完成！",
    "install.install_failed": "安装失败：{error}",
    "install.verifying": "正在验证安装...",
    "install.verify_success": "Claude Code CLI 已准备就绪！",
    "install.verify_failed": "验证失败",
    "install.config_api_key_prompt": "是否现在配置 API Key？(y/n)",
    "install.enter_api_key": "请输入您的 Anthropic API Key",
    "install.api_key_saved": "API Key 已保存到环境变量",
    "install.done": "安装完成！运行 'claude' 开始使用",
    "install.download_node": "正在打开 Node.js 下载页面...",
    "install.manual_install": "请手动安装 Node.js 后重新运行此脚本",
    "install.permission_denied": "权限不足，请使用管理员权限运行",
    "install.network_error": "网络错误，请检查网络连接",
    "install.already_installed": "Claude CLI 已安装：{version}",
  "install.upgrade_prompt": "发现新版本 ({new_version})，是否升级？(y/n)",
    "install.usage": "用法：{script_name} [--lang=zh|en]",

    # Project generation
    "project.creating": "正在创建项目结构...",
    "project.created": "项目已创建于 {path}",
    "project.generating_code": "正在生成代码...",
    "project.code_generated": "代码生成完成",
    "project.running_tests": "正在运行测试...",
    "project.tests_passed": "所有测试通过 ({count}/{total})",
    "project.tests_failed": "测试失败 ({failed}/{total})",

    # Errors
    "error.file_not_found": "文件未找到：{path}",
    "error.permission_denied": "权限被拒绝：{path}",
    "error.invalid_config": "无效的配置：{message}",
    "error.network_error": "网络错误：{message}",
}
