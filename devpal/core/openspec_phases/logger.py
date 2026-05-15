# -*- coding: utf-8 -*-
"""
OpenSpec 日志系统

提供结构化日志功能，同时输出到控制台和文件。
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Optional


class OpenSpecLogger:
    """OpenSpec 日志记录器

    功能：
    - 双输出：控制台（简洁）+ 文件（详细）
    - 日志级别：DEBUG, INFO, WARN, ERROR, CRITICAL
    - 自动记录阶段开始、结束、耗时
    - 异常堆栈跟踪
    """

    def __init__(self, project_name: str, project_dir: Path):
        """初始化日志系统

        Args:
            project_name: 项目名称
         project_dir: 项目目录
        """
        # 生成日志文件名：项目名_YYYYMMDD_HHMMSS.log
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = project_dir / f"{project_name}_{timestamp}.log"

        # 创建 logger
        self.logger = logging.getLogger(f"OpenSpec_{project_name}")
        self.logger.setLevel(logging.DEBUG)

        # 清除已有的 handlers（避免重复）
        self.logger.handlers.clear()

    # 文件处理器 - 记录所有级别的详细日志
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            '%(asctime)s [%(levelname)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)

        # 控制台处理器 - 只显示 INFO 及以上级别
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter('[%(levelname)s] %(message)s')
        console_handler.setFormatter(console_formatter)

        # 添加处理器
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)

        # 保存日志文件路径
        self.log_file = log_file

        # 记录日志系统初始化
        self.logger.info("=" * 70)
        self.logger.info(f"OpenSpec 日志系统已初始化")
        self.logger.info(f"项目名称: {project_name}")
        self.logger.info(f"日志文件: {log_file}")
        self.logger.info("=" * 70)

    def phase_start(self, phase_num: int, phase_name: str) -> None:
        """记录阶段开始

        Args:
            phase_num: 阶段编号 (1-11)
            phase_name: 阶段名称
      """
        self.logger.info("")
        self.logger.info("=" * 70)
        self.logger.info(f"Phase {phase_num}/11 开始: {phase_name}")
        self.logger.info("=" * 70)

    def phase_end(self, phase_num: int, success: bool, duration: float) -> None:
        """记录阶段结束

        Args:
            phase_num: 阶段编号 (1-11)
            success: 是否成功
            duration: 耗时（秒）
        """
        status = "[成功]" if success else "[失败]"
        self.logger.info(f"Phase {phase_num}/11 结束: {status} (耗时: {duration:.2f}s)")
        self.logger.info("=" * 70)

    def error(self, message: str, exc: Optional[Exception] = None) -> None:
        """记录错误

        Args:
         message: 错误消息
            exc: 异常对象（可选）
        """
        self.logger.error(message)
        if exc:
            self.logger.exception(exc)

    def debug(self, message: str) -> None:
        """记录调试信息"""
        self.logger.debug(message)

    def info(self, message: str) -> None:
        """记录一般信息"""
        self.logger.info(message)

    def warning(self, message: str) -> None:
        """记录警告"""
        self.logger.warning(message)

    def critical(self, message: str) -> None:
        """记录严重错误"""
        self.logger.critical(message)
