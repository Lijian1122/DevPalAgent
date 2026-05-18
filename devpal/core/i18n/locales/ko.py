# -*- coding: utf-8 -*-
"""
Korean (ko) message catalog
"""

MESSAGES = {
    # Common
    "common.yes": "예",
    "common.no": "아니오",
    "common.success": "성공",
    "common.error": "오류",
    "common.warning": "경고",
    "common.info": "정보",

    # Installation
    "install.title": "Claude Code CLI 설치 스크립트",
    "install.checking_node": "Node.js 설치 확인 중...",
    "install.node_found": "Node.js {version}을(를) 찾았습니다",
    "install.node_not_found": "Node.js를 찾을 수 없습니다. 먼저 Node.js를 설치하세요.",
    "install.checking_npm": "npm 설치 확인 중...",
    "install.npm_found": "npm {version}을(를) 찾았습니다",
    "install.installing": "@anthropic-ai/claude-code 설치 중...",
    "install.install_success": "설치가 성공적으로 완료되었습니다!",
    "install.install_failed": "설치 실패: {error}",
    "install.verifying": "설치 확인 중...",
    "install.verify_success": "Claude Code CLI가 사용 준비되었습니다!",
    "install.verify_failed": "확인 실패",

    # Project generation
    "project.creating": "프로젝트 구조 생성 중...",
    "project.created": "프로젝트가 {path}에 생성되었습니다",
    "project.generating_code": "코드 생성 중...",
    "project.code_generated": "코드 생성 완료",
    "project.running_tests": "테스트 실행 중...",
    "project.tests_passed": "모든 테스트 통과 ({count}/{total})",
    "project.tests_failed": "테스트 실패 ({failed}/{total})",

    # Errors
    "error.file_not_found": "파일을 찾을 수 없음: {path}",
    "error.permission_denied": "권한 거부됨: {path}",
    "error.invalid_config": "잘못된 구성: {message}",
    "error.network_error": "네트워크 오류: {message}",
}
