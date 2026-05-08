from __future__ import annotations
from typing import Any, Dict, List, Optional, Union, Tuple, Callable, TYPE_CHECKING
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import difflib
import hashlib
import re

if TYPE_CHECKING:
    pass


class DeltaOperation(Enum):
    ADDED = "added"        # 新增行为
    MODIFIED = "modified"  # 修改行为
    REMOVED = "removed"    # 弃用行为
    RENAMED = "renamed"    # 重命名


@dataclass
class DeltaHunk:
    """变更块 - 描述具体的变更内容"""
    operation: DeltaOperation
    target_path: str  # 目标路径，如 "function:my_func" or "file:src/main.cpp:class:X"
    old_content: Optional[str] = None
    new_content: Optional[str] = None
    start_line: Optional[int] = None
    end_line: Optional[int] = None
    reason: Optional[str] = None  # 变更原因


# -------------------------------------------------------------------------
# 冲突检测与解决
# -------------------------------------------------------------------------
class ConflictType(Enum):
    """冲突类型"""
    OVERLAP = "overlap"              # 变更范围重叠
    CONTENT_MISMATCH = "content_mismatch"  # 内容不匹配（预期 old_content 但实际不同）
    DEPENDENCY = "dependency"        # 依赖冲突
    THREE_WAY = "three_way"          # 三向合并冲突


class ConflictResolution(Enum):
    """冲突解决策略"""
    MANUAL = "manual"                # 需要人工解决
    OURS = "ours"                    # 保留我方变更
    THEIRS = "theirs"                # 保留对方变更
    MERGE = "merge"                  # 尝试自动合并


@dataclass
class MergeConflict:
    """合并冲突详情"""
    conflict_type: ConflictType
    message: str
    our_delta: Optional[DeltaHunk] = None
    their_delta: Optional[DeltaHunk] = None
    base_content: Optional[str] = None
    our_content: Optional[str] = None
    their_content: Optional[str] = None
    resolution: ConflictResolution = ConflictResolution.MANUAL
    resolved_content: Optional[str] = None


@dataclass
class DeltaResult:
    success: bool
    applied_deltas: List[DeltaHunk]
    conflicts: List[str]
    conflict_details: List[MergeConflict] = field(default_factory=list)
    new_content: str = ""
    diff_preview: str = ""
    merged_content: Optional[str] = None


class DeltaSpec:
    """Delta 增量变更规范 - 描述"什么在变化"，而不是重写整个文件"""

    def __init__(self, target_file: Union[str, Path]):
        self.target_file = Path(target_file)
        self.deltas: List[DeltaHunk] = []
        self._original_content: Optional[str] = None

    def load_original(self):
        """加载原始文件内容"""
        if self.target_file.exists():
            self._original_content = self.target_file.read_text(encoding='utf-8')
        else:
            self._original_content = ""

    @property
    def original_content(self) -> Optional[str]:
        """获取原始内容"""
        return self._original_content

    def add_delta(self, delta: DeltaHunk):
        """添加一个变更"""
        self.deltas.append(delta)

    def create_delta_from_diff(self, new_content: str, reason: str = "") -> List[DeltaHunk]:
        """从内容 diff 自动生成 Delta 列表"""
        if self._original_content is None:
            self.load_original()

        deltas = []
        old_lines = self._original_content.splitlines(keepends=True)
        new_lines = new_content.splitlines(keepends=True)

        matcher = difflib.SequenceMatcher(None, old_lines, new_lines)

        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == 'equal':
                continue
            elif tag == 'insert':
                deltas.append(DeltaHunk(
                    DeltaOperation.ADDED,
                    target_path=f"file:{self.target_file}:lines:{i1+1}",
                    new_content=''.join(new_lines[j1:j2]),
                    start_line=i1 + 1,
                    reason=reason
                ))
            elif tag == 'delete':
                deltas.append(DeltaHunk(
                    DeltaOperation.REMOVED,
                    target_path=f"file:{self.target_file}:lines:{i1+1}-{i2}",
                    old_content=''.join(old_lines[i1:i2]),
                    start_line=i1 + 1,
                    end_line=i2,
                    reason=reason
                ))
            elif tag == 'replace':
                deltas.append(DeltaHunk(
                    DeltaOperation.MODIFIED,
                    target_path=f"file:{self.target_file}:lines:{i1+1}-{i2}",
                    old_content=''.join(old_lines[i1:i2]),
                    new_content=''.join(new_lines[j1:j2]),
                    start_line=i1 + 1,
                    end_line=i2,
                    reason=reason
                ))

        return deltas

    def dry_run(self) -> DeltaResult:
        """Dry-Run 模式: 预览变更效果，不修改原文件

        执行:
        1. 检测冲突（重叠范围、内容不匹配）
        2. 模拟应用所有 Delta
        3. 生成 diff 预览
        4. 返回预览结果，不写入文件

        Returns:
            DeltaResult: 预览结果
        """
        if self._original_content is None:
            self.load_original()

        # 1. 预检测冲突
        conflicts = []
        conflicts.extend([c.message for c in self.detect_overlaps()])
        conflicts.extend([c.message for c in self.validate_content_match()])

        # 2. 模拟应用 Delta
        content = self._original_content
        applied = []

        # 按逆序应用 Delta (避免行号偏移问题)
        sorted_deltas = sorted(
            self.deltas,
            key=lambda d: d.start_line if d.start_line else 0,
            reverse=True
        )

        for delta in sorted_deltas:
            try:
                content = self._apply_delta(content, delta)
                applied.append(delta)
            except Exception as e:
                conflicts.append(f"Delta {delta.target_path} 模拟应用失败: {e}")

        # 3. 生成预览 diff
        diff_preview = self._generate_diff(self._original_content, content)

        # 4. 返回预览结果（不写入文件）
        success = len(conflicts) == 0
        return DeltaResult(success, applied, conflicts, content, diff_preview)

    def apply(self, validate: bool = True, dry_run: bool = False) -> DeltaResult:
        """应用所有 Delta 变更

        Args:
            validate: 是否执行验证
            dry_run: 是否仅预览（不写入文件）
        """
        if dry_run:
            return self.dry_run()

        if self._original_content is None:
            self.load_original()

        content = self._original_content
        conflicts = []
        applied = []

        # 按逆序应用 Delta (避免行号偏移问题)
        sorted_deltas = sorted(
            self.deltas,
            key=lambda d: d.start_line if d.start_line else 0,
            reverse=True
        )

        for delta in sorted_deltas:
            try:
                content = self._apply_delta(content, delta)
                applied.append(delta)
            except Exception as e:
                conflicts.append(f"Delta {delta.target_path} 应用失败: {e}")

        # 生成预览 diff
        diff_preview = self._generate_diff(self._original_content, content)

        success = len(conflicts) == 0
        return DeltaResult(success, applied, conflicts, content, diff_preview)

    def _apply_delta(self, content: str, delta: DeltaHunk) -> str:
        """应用单个 Delta"""
        lines = content.splitlines(keepends=True)

        if delta.operation == DeltaOperation.ADDED:
            # 在指定位置插入
            pos = (delta.start_line or len(lines)) - 1
            new_lines = delta.new_content.splitlines(keepends=True) if delta.new_content else []
            lines[pos:pos] = new_lines
        elif delta.operation == DeltaOperation.MODIFIED:
            # 替换指定行范围
            start = (delta.start_line or 1) - 1
            end = delta.end_line or len(lines)
            new_lines = delta.new_content.splitlines(keepends=True) if delta.new_content else []
            lines[start:end] = new_lines
        elif delta.operation == DeltaOperation.REMOVED:
            # 删除指定行
            start = (delta.start_line or 1) - 1
            end = delta.end_line or len(lines)
            del lines[start:end]
        elif delta.operation == DeltaOperation.RENAMED:
            # 重命名 - 处理标识符替换
            if delta.old_content and delta.new_content:
                content_str = ''.join(lines)
                content_str = content_str.replace(delta.old_content, delta.new_content)
                lines = content_str.splitlines(keepends=True)

        return ''.join(lines)

    def _generate_diff(self, old: str, new: str) -> str:
        """生成统一格式 diff"""
        diff = difflib.unified_diff(
            old.splitlines(),
            new.splitlines(),
            fromfile=str(self.target_file),
            tofile=str(self.target_file),
            lineterm=''
        )
        return '\n'.join(diff)

    def to_dict(self) -> Dict[str, Any]:
        """序列化 DeltaSpec"""
        return {
            'target_file': str(self.target_file),
            'content_hash': hashlib.md5((self._original_content or "").encode()).hexdigest(),
            'deltas': [
                {
                    'operation': d.operation.value,
                    'target_path': d.target_path,
                    'start_line': d.start_line,
                    'end_line': d.end_line,
                    'reason': d.reason,
                }
                for d in self.deltas
            ]
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DeltaSpec':
        """从字典反序列化"""
        spec = cls(data['target_file'])
        for d in data['deltas']:
            spec.add_delta(DeltaHunk(
                operation=DeltaOperation(d['operation']),
                target_path=d['target_path'],
                start_line=d.get('start_line'),
                end_line=d.get('end_line'),
                reason=d.get('reason')
            ))
        return spec

    def apply_and_save(self, backup: bool = True) -> DeltaResult:
        """应用 Delta 并保存到文件"""
        result = self.apply()
        if result.success:
            if backup and self.target_file.exists():
                backup_path = self.target_file.with_suffix(f'.bak{self.target_file.suffix}')
                backup_path.write_text(self._original_content, encoding='utf-8')
            self.target_file.write_text(result.new_content, encoding='utf-8')
        return result

    # =========================================================================
    # 冲突检测与三向合并 (新增 P0 功能)
    # =========================================================================

    def detect_overlaps(self) -> List[MergeConflict]:
        """检测 Delta 之间的重叠冲突

        Returns:
            重叠冲突列表
        """
        conflicts = []
        deltas_with_lines = [
            (i, d) for i, d in enumerate(self.deltas)
            if d.start_line is not None
        ]

        # 检查每对 Delta 是否有重叠
        for i in range(len(deltas_with_lines)):
            idx1, d1 = deltas_with_lines[i]
            end1 = d1.end_line if d1.end_line else d1.start_line

            for j in range(i + 1, len(deltas_with_lines)):
                idx2, d2 = deltas_with_lines[j]
                end2 = d2.end_line if d2.end_line else d2.start_line

                # 检查行范围是否有重叠
                if not (end1 < d2.start_line or end2 < d1.start_line):
                    conflicts.append(MergeConflict(
                        conflict_type=ConflictType.OVERLAP,
                        message=f"Delta 重叠: 第 {d1.start_line}-{end1} 行 与 第 {d2.start_line}-{end2} 行",
                        our_delta=d1,
                        their_delta=d2
                    ))

        return conflicts

    def validate_content_match(self) -> List[MergeConflict]:
        """验证 Delta 的 old_content 与实际内容是否匹配

        Returns:
            内容不匹配冲突列表
        """
        conflicts = []
        if self._original_content is None:
            return conflicts

        original_lines = self._original_content.splitlines(keepends=True)

        for delta in self.deltas:
            if delta.operation in [DeltaOperation.MODIFIED, DeltaOperation.REMOVED]:
                if delta.old_content and delta.start_line is not None:
                    end_line = delta.end_line or delta.start_line
                    actual_lines = ''.join(original_lines[delta.start_line - 1:end_line])

                    # 规范化换行符进行比较
                    actual_normalized = re.sub(r'\r\n|\r|\n', '\n', actual_lines)
                    expected_normalized = re.sub(r'\r\n|\r|\n', '\n', delta.old_content)

                    if actual_normalized != expected_normalized:
                        conflicts.append(MergeConflict(
                            conflict_type=ConflictType.CONTENT_MISMATCH,
                            message=f"内容不匹配: Delta 预期的第 {delta.start_line}-{end_line} 行内容与实际文件不符",
                            our_delta=delta,
                            base_content=actual_lines,
                            our_content=delta.old_content
                        ))

        return conflicts

    @classmethod
    def three_way_merge(cls, base_content: str, our_content: str, their_content: str,
                        target_file: Union[str, Path] = "merged") -> Tuple[DeltaResult, 'ThreeWayMerger']:
        """三向合并算法

        Args:
            base_content: 共同祖先版本内容
            our_content: 我们的变更（本地变更）
            their_content: 他们的变更（远程变更）
            target_file: 目标文件路径

        Returns:
            (合并结果, 合并器实例)
        """
        merger = ThreeWayMerger(base_content, our_content, their_content, target_file)
        result = merger.merge()
        return result, merger


class ThreeWayMerger:
    """三向合并器 - 实现完整的 diff3 风格合并

    算法原理:
    1. 基于 base 版本分别计算 ours 和 theirs 的 diff
    2. 识别不重叠的变更：直接应用
    3. 识别重叠的变更：尝试智能合并，失败则标记冲突
    """

    def __init__(self, base: str, ours: str, theirs: str, target_file: Union[str, Path]):
        self.base = base
        self.ours = ours
        self.theirs = theirs
        self.target_file = Path(target_file)
        self.conflicts: List[MergeConflict] = []

    def _compute_diff(self, old: str, new: str) -> List[Tuple[str, int, int, List[str]]]:
        """计算两个文本的差异，返回变更块列表

        Returns:
            [(tag, start_line, end_line, content_lines), ...]
            tag: 'equal', 'insert', 'delete', 'replace'
        """
        old_lines = old.splitlines(keepends=True)
        new_lines = new.splitlines(keepends=True)

        matcher = difflib.SequenceMatcher(None, old_lines, new_lines)
        changes = []

        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == 'equal':
                continue
            content = new_lines[j1:j2] if tag in ['insert', 'replace'] else old_lines[i1:i2]
            content_clean = [re.sub(r'\r\n|\r|\n', '\n', line) for line in content]
            changes.append((tag, i1, i2, content_clean))

        return changes

    def _hunks_overlap(self, hunk1: Tuple, hunk2: Tuple) -> bool:
        """检查两个变更块是否重叠"""
        tag1, start1, end1, _ = hunk1
        tag2, start2, end2, _ = hunk2

        # insert 变更在相同位置也算重叠
        if tag1 == 'insert' and tag2 == 'insert' and start1 == start2:
            return True

        # 对于 delete/replace，检查行范围重叠
        return not (end1 <= start2 or end2 <= start1)

    def _merge_overlapping_hunks(self, hunk1: Tuple, hunk2: Tuple,
                                  base_lines: List[str]) -> Tuple[Optional[List[str]], MergeConflict]:
        """尝试合并重叠的变更块

        策略:
        1. 如果两边变更完全相同 → 保留一份
        2. 如果是相邻行的变更 → 尝试合并
        3. 否则 → 标记冲突
        """
        tag1, _, _, content1 = hunk1
        tag2, _, _, content2 = hunk2

        # 情况1: 两边变更完全相同
        if content1 == content2:
            return content1, None

        # 情况2: 尝试智能合并 (简单的行级合并)
        merged = []
        lines1_set = set(content1)
        lines2_set = set(content2)

        # 合并共同的行
        all_lines = []
        seen = set()
        for line in content1 + content2:
            if line not in seen:
                seen.add(line)
                all_lines.append(line)

        # 简单策略：如果两边没有矛盾的行，使用并集
        if len(all_lines) == len(lines1_set | lines2_set):
            return all_lines, None

        # 情况3: 无法自动合并 → 标记冲突
        conflict = MergeConflict(
            conflict_type=ConflictType.THREE_WAY,
            message="三向合并冲突：无法自动合并重叠变更",
            our_content=''.join(content1),
            their_content=''.join(content2),
            base_content=None
        )
        return None, conflict

    def merge(self, conflict_marker: bool = True) -> DeltaResult:
        """执行三向合并

        Args:
            conflict_marker: 是否在输出中包含冲突标记 (<<<<<<< ======= >>>>>>>)

        Returns:
            DeltaResult 合并结果
        """
        base_lines = self.base.splitlines(keepends=True)

        # 分别计算两边相对于 base 的 diff
        our_changes = self._compute_diff(self.base, self.ours)
        their_changes = self._compute_diff(self.base, self.theirs)

        # 检测冲突
        all_changes = our_changes + their_changes
        applied_changes = []
        self.conflicts = []

        # 简单的非重叠变更合并策略
        # 按变更位置排序
        all_changes_sorted = sorted(all_changes, key=lambda x: x[1])

        # 检查并解决冲突
        i = 0
        while i < len(all_changes_sorted):
            current = all_changes_sorted[i]

            # 查找与当前变更重叠的所有变更
            overlapping = [current]
            j = i + 1
            while j < len(all_changes_sorted):
                if self._hunks_overlap(current, all_changes_sorted[j]):
                    overlapping.append(all_changes_sorted[j])
                    j += 1
                else:
                    break

            if len(overlapping) == 1:
                # 无重叠，直接应用
                applied_changes.append(overlapping[0])
            else:
                # 有重叠，尝试合并
                merged_content, conflict = self._merge_overlapping_hunks(
                    overlapping[0], overlapping[1], base_lines
                )
                if conflict:
                    self.conflicts.append(conflict)
                    # 如果冲突，保留 ours 和 theirs 的标记
                    if conflict_marker:
                        # 创建冲突标记块
                        _, start, end, _ = overlapping[0]
                        conflict_lines = ['<<<<<<< OURS\n']
                        conflict_lines.extend([l.rstrip('\n') + '\n' for l in overlapping[0][3]])
                        conflict_lines.append('=======\n')
                        conflict_lines.extend([l.rstrip('\n') + '\n' for l in overlapping[1][3]])
                        conflict_lines.append('>>>>>>> THEIRS\n')
                        applied_changes.append(('conflict', start, end, conflict_lines))
                else:
                    applied_changes.append(('merged', overlapping[0][1], overlapping[0][2], merged_content))

            i = j

        # 应用所有变更（按逆序）
        result_lines = list(base_lines)

        # 按位置逆序应用
        for change in sorted(applied_changes, key=lambda x: x[1], reverse=True):
            tag, start, end, content = change
            if tag == 'delete':
                del result_lines[start:end]
            elif tag in ['insert', 'replace', 'merged', 'conflict']:
                result_lines[start:end] = content

        merged_content = ''.join(result_lines)

        # 生成 diff 预览
        diff_preview = difflib.unified_diff(
            self.base.splitlines(),
            merged_content.splitlines(),
            fromfile='base',
            tofile='merged',
            lineterm=''
        )

        success = len(self.conflicts) == 0

        return DeltaResult(
            success=success,
            applied_deltas=[],
            conflicts=[c.message for c in self.conflicts],
            conflict_details=self.conflicts,
            new_content=merged_content,
            merged_content=merged_content,
            diff_preview='\n'.join(diff_preview)
        )

    def resolve_conflict(self, index: int, strategy: ConflictResolution,
                         custom_content: Optional[str] = None) -> bool:
        """解决指定位置的冲突

        Args:
            index: 冲突索引
            strategy: 解决策略
            custom_content: 使用 MERGE 策略时的自定义内容

        Returns:
            是否成功解决
        """
        if index >= len(self.conflicts):
            return False

        conflict = self.conflicts[index]
        conflict.resolution = strategy

        if strategy == ConflictResolution.OURS:
            conflict.resolved_content = conflict.our_content
        elif strategy == ConflictResolution.THEIRS:
            conflict.resolved_content = conflict.their_content
        elif strategy == ConflictResolution.MERGE and custom_content:
            conflict.resolved_content = custom_content
        else:  # MANUAL
            return False

        return True
