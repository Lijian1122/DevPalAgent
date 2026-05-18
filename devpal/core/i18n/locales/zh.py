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
    "install.checking_node": "正在检查 Node.js 安装...",
    "install.node_found": "找到 Node.js {version}",
    "install.node_not_found": "未找到 Node.js。请先安装 Node.js。",
    "install.checking_npm": "正在检查 npm 安装...",
    "install.npm_found": "找到 npm {version}",
    "install.installing": "正在安装 @anthropic-ai/claude-code...",
    "install.install_success": "安装成功完成！",
    "install.install_failed": "安装失败：{error}",
    "install.verifying": "正在验证安装...",
    "install.verify_success": "Claude Code CLI 已准备就绪！",
    "install.verify_failed": "验证失败",

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
