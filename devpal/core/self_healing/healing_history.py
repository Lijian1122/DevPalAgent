"""
修复历史管理器

记录和管理修复历史，支持相似错误查询和统计分析。
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from .models import ErrorContext, ErrorSeverity, ErrorType, HealingRecord, StrategyType


class HealingHistory:
    """修复历史管理器"""

    def __init__(self, storage_path: Path, logger: Optional[logging.Logger] = None):
        self.storage_path = storage_path
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.logger = logger or logging.getLogger(__name__)

        # 内存缓存
        self.records: List[HealingRecord] = []
        self._load_from_disk()

    def add_record(self, record: HealingRecord) -> None:
        """添加修复记录"""
        self.records.append(record)
        self._save_to_disk(record)
        self.logger.info(
            f"[History] 记录修复: {record.record_id} (成功: {record.success})"
        )

    def find_similar_errors(
        self, error_context: ErrorContext, similarity_threshold: float = 0.7
    ) -> List[HealingRecord]:
        """查找相似错误"""
        similar_records = []

        for record in self.records:
            similarity = self._calculate_similarity(error_context, record.error_context)

            if similarity >= similarity_threshold:
                similar_records.append(record)

        # 按相似度和时间排序（最近的优先）
        similar_records.sort(
            key=lambda r: (
                self._calculate_similarity(error_context, r.error_context),
                r.timestamp,
            ),
            reverse=True,
        )

        return similar_records

    def get_statistics(self) -> Dict:
        """获取统计信息"""
        if not self.records:
            return {
                "total_records": 0,
                "success_rate": 0.0,
                "avg_execution_time": 0.0,
                "by_error_type": {},
                "by_strategy_type": {},
            }

        total = len(self.records)
        successful = sum(1 for r in self.records if r.success)

        # 按错误类型统计
        by_error_type = {}
        for record in self.records:
            error_type = record.error_context.error_type.value
            if error_type not in by_error_type:
                by_error_type[error_type] = {"total": 0, "success": 0}
                by_error_type[error_type]["total"] += 1
            if record.success:
                by_error_type[error_type]["success"] += 1

        # 按策略类型统计
        by_strategy_type = {}
        for record in self.records:
            strategy_type = record.strategy.strategy_type.value
            if strategy_type not in by_strategy_type:
                by_strategy_type[strategy_type] = {"total": 0, "success": 0}
                by_strategy_type[strategy_type]["total"] += 1
            if record.success:
                by_strategy_type[strategy_type]["success"] += 1

        return {
            "total_records": total,
            "success_rate": successful / total,
            "avg_execution_time": sum(r.execution_time for r in self.records) / total,
            "by_error_type": by_error_type,
            "by_strategy_type": by_strategy_type,
        }

    def _calculate_similarity(self, ctx1: ErrorContext, ctx2: ErrorContext) -> float:
        """计算错误相似度"""
        score = 0.0

        # 错误类型匹配 (40%)
        if ctx1.error_type == ctx2.error_type:
            score += 0.4

        # 错误消息相似度 (40%)
        msg_similarity = self._text_similarity(ctx1.error_message, ctx2.error_message)
        score += msg_similarity * 0.4

        # 文件路径相似度 (20%)
        if ctx1.file_path and ctx2.file_path:
            if ctx1.file_path == ctx2.file_path:
                score += 0.2
            elif ctx1.file_path.suffix == ctx2.file_path.suffix:
                score += 0.1

        return score

    def _text_similarity(self, text1: str, text2: str) -> float:
        """计算文本相似度（简化版）"""
        # 使用 Jaccard 相似度
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())

        if not words1 or not words2:
            return 0.0

        intersection = words1 & words2
        union = words1 | words2

        return len(intersection) / len(union)

    def _load_from_disk(self) -> None:
        """从磁盘加载历史记录"""
        history_file = self.storage_path / "healing_history.jsonl"

        if not history_file.exists():
            return

        try:
            with open(history_file, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        data = json.loads(line)
                        record = self._deserialize_record(data)
                        self.records.append(record)

            self.logger.info(f"[History] 加载 {len(self.records)} 条历史记录")
        except Exception as e:
            self.logger.error(f"[History] 加载历史记录失败: {e}")

    def _save_to_disk(self, record: HealingRecord) -> None:
        """保存记录到磁盘"""
        history_file = self.storage_path / "healing_history.jsonl"

        try:
            with open(history_file, "a", encoding="utf-8") as f:
                data = self._serialize_record(record)
                f.write(json.dumps(data, ensure_ascii=False) + "\n")
        except Exception as e:
            self.logger.error(f"[History] 保存记录失败: {e}")

    def _serialize_record(self, record: HealingRecord) -> Dict:
        """序列化记录"""
        return {
            "record_id": record.record_id,
            "error_context": {
                "error_message": record.error_context.error_message,
                "error_type": record.error_context.error_type.value,
                "severity": record.error_context.severity.value,
                "file_path": str(record.error_context.file_path)
                if record.error_context.file_path
                else None,
                "phase": record.error_context.phase,
            },
            "root_cause": {
                "root_cause_type": record.root_cause.root_cause_type,
                "confidence": record.root_cause.confidence,
            },
            "strategy": {
                "strategy_type": record.strategy.strategy_type.value,
                "confidence": record.strategy.confidence,
            },
            "success": record.success,
            "execution_time": record.execution_time,
            "timestamp": record.timestamp.isoformat(),
            "retry_count": record.retry_count,
        }

    def _deserialize_record(self, data: Dict) -> HealingRecord:
        """反序列化记录（简化版）"""
        from .models import HealingStrategy, RootCause

        # 创建简化的 ErrorContext
        error_ctx = ErrorContext(
            error_message=data["error_context"]["error_message"],
            error_type=ErrorType(data["error_context"]["error_type"]),
            severity=ErrorSeverity(data["error_context"]["severity"]),
            file_path=Path(data["error_context"]["file_path"])
            if data["error_context"]["file_path"]
            else None,
            phase=data["error_context"].get("phase"),
        )

        # 创建简化的 RootCause
        root_cause = RootCause(
            error_context=error_ctx,
            root_cause_type=data["root_cause"]["root_cause_type"],
            root_cause_description="",
            confidence=data["root_cause"]["confidence"],
        )
        # 创建简化的 Strategy
        strategy = HealingStrategy(
            strategy_type=StrategyType(data["strategy"]["strategy_type"]),
            description="",
            confidence=data["strategy"]["confidence"],
            estimated_time=0.0,
            root_cause=root_cause,
        )

        return HealingRecord(
            record_id=data["record_id"],
            error_context=error_ctx,
            root_cause=root_cause,
            strategy=strategy,
            success=data["success"],
            execution_time=data["execution_time"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            retry_count=data.get("retry_count", 0),
        )
