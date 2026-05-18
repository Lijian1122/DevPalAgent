# -*- coding: utf-8 -*-
"""
Japanese (ja) message catalog
"""

MESSAGES = {
    # Common
    "common.yes": "はい",
    "common.no": "いいえ",
    "common.success": "成功",
    "common.error": "エラー",
    "common.warning": "警告",
    "common.info": "情報",

    # Installation
    "install.title": "Claude Code CLI インストールスクリプト",
    "install.checking_node": "Node.jsのインストールを確認中...",
    "install.node_found": "Node.js {version} が見つかりました",
    "install.node_not_found": "Node.jsが見つかりません。まずNode.jsをインストールしてください。",
    "install.checking_npm": "npmのインストールを確認中...",
    "install.npm_found": "npm {version} が見つかりました",
    "install.installing": "@anthropic-ai/claude-codeをインストール中...",
    "install.install_success": "インストールが正常に完了しました！",
    "install.install_failed": "インストールに失敗しました：{error}",
    "install.verifying": "インストールを検証中...",
    "install.verify_success": "Claude Code CLIの準備が整いました！",
    "install.verify_failed": "検証に失敗しました",

    # Project generation
    "project.creating": "プロジェクト構造を作成中...",
    "project.created": "プロジェクトが {path} に作成されました",
    "project.generating_code": "コードを生成中...",
    "project.code_generated": "コード生成が完了しました",
    "project.running_tests": "テストを実行中...",
    "project.tests_passed": "すべてのテストに合格しました ({count}/{total})",
    "project.tests_failed": "テストに失敗しました ({failed}/{total})",

    # Errors
    "error.file_not_found": "ファイルが見つかりません：{path}",
    "error.permission_denied": "アクセスが拒否されました：{path}",
    "error.invalid_config": "無効な設定：{message}",
    "error.network_error": "ネットワークエラー：{message}",
}
