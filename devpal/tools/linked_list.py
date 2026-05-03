# -*- coding: utf-8 -*-
"""
链表工具模块
基于抽象 FunctionCall 实现链表的创建、增删改查操作
"""
import json
import os
from typing import Any, Optional, List, Dict
from pydantic import Field
from .function_call_base import AbstractFunctionCall, FunctionCallContext, ExecutionResult
from .base import BaseTool, ToolResult


# 持久化文件路径
LINKED_LIST_STORAGE_FILE = "./data/linked_lists.json"


class ListNode:
    """链表节点"""

    def __init__(self, value: Any):
        self.value = value
        self.next: Optional["ListNode"] = None

    def __repr__(self) -> str:
        return f"ListNode({repr(self.value)})"

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "value": self.value,
            "next": id(self.next) if self.next else None
        }


class LinkedList:
    """链表数据结构 - 单链表实现"""

    def __init__(self, name: str = "default"):
        self.name = name
        self.head: Optional[ListNode] = None
        self.size: int = 0

    def is_empty(self) -> bool:
        """判断链表是否为空"""
        return self.head is None

    def __len__(self) -> int:
        """获取链表长度"""
        return self.size

    def append(self, value: Any) -> int:
        """尾部添加节点

        Returns:
            新节点的索引位置
        """
        new_node = ListNode(value)

        if self.is_empty():
            self.head = new_node
        else:
            current = self.head
            while current.next:
                current = current.next
            current.next = new_node

        self.size += 1
        return self.size - 1

    def prepend(self, value: Any) -> int:
        """头部添加节点

        Returns:
            新节点的索引位置（始终为0）
        """
        new_node = ListNode(value)
        new_node.next = self.head
        self.head = new_node
        self.size += 1
        return 0

    def insert(self, index: int, value: Any) -> bool:
        """在指定位置插入节点

        Args:
            index: 插入位置（0-based）
            value: 节点值

        Returns:
            是否插入成功
        """
        if index < 0 or index > self.size:
            return False

        if index == 0:
            self.prepend(value)
            return True

        if index == self.size:
            self.append(value)
            return True

        new_node = ListNode(value)
        current = self.head
        for _ in range(index - 1):
            current = current.next

        new_node.next = current.next
        current.next = new_node
        self.size += 1
        return True

    def delete_at(self, index: int) -> Optional[Any]:
        """删除指定位置的节点

        Args:
            index: 要删除节点的索引

        Returns:
            删除的节点值，失败返回 None
        """
        if self.is_empty() or index < 0 or index >= self.size:
            return None

        if index == 0:
            value = self.head.value
            self.head = self.head.next
            self.size -= 1
            return value

        current = self.head
        for _ in range(index - 1):
            current = current.next

        value = current.next.value
        current.next = current.next.next
        self.size -= 1
        return value

    def delete_value(self, value: Any) -> int:
        """删除第一个匹配指定值的节点

        Args:
            value: 要删除的值

        Returns:
            删除节点的索引，未找到返回 -1
        """
        if self.is_empty():
            return -1

        # 检查头节点
        if self.head.value == value:
            self.head = self.head.next
            self.size -= 1
            return 0

        current = self.head
        index = 1
        while current.next:
            if current.next.value == value:
                current.next = current.next.next
                self.size -= 1
                return index
            current = current.next
            index += 1

        return -1

    def update_at(self, index: int, new_value: Any) -> bool:
        """更新指定位置节点的值

        Args:
            index: 节点索引
            new_value: 新值

        Returns:
            是否更新成功
        """
        if index < 0 or index >= self.size:
            return False

        current = self.head
        for _ in range(index):
            current = current.next

        current.value = new_value
        return True

    def get_at(self, index: int) -> Optional[Any]:
        """获取指定位置的节点值

        Args:
            index: 节点索引

        Returns:
            节点值，不存在返回 None
        """
        if index < 0 or index >= self.size:
            return None

        current = self.head
        for _ in range(index):
            current = current.next

        return current.value

    def find(self, value: Any) -> int:
        """查找值第一次出现的索引

        Args:
            value: 要查找的值

        Returns:
            索引位置，未找到返回 -1
        """
        current = self.head
        index = 0
        while current:
            if current.value == value:
                return index
            current = current.next
            index += 1
        return -1

    def to_list(self) -> List[Any]:
        """转换为 Python 列表"""
        result = []
        current = self.head
        while current:
            result.append(current.value)
            current = current.next
        return result

    def clear(self) -> None:
        """清空链表"""
        self.head = None
        self.size = 0

    def __repr__(self) -> str:
        values = self.to_list()
        return f"LinkedList({', '.join(map(repr, values))})"

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "name": self.name,
            "size": self.size,
            "nodes": self.to_list()
        }


# 全局链表注册表 - 支持持久化
_linked_lists: Dict[str, LinkedList] = {}


def _ensure_storage_dir():
    """确保存储目录存在"""
    os.makedirs(os.path.dirname(LINKED_LIST_STORAGE_FILE), exist_ok=True)


def _save_linked_lists():
    """将所有链表保存到文件"""
    _ensure_storage_dir()
    data = {}
    for name, ll in _linked_lists.items():
        data[name] = ll.to_list()
    with open(LINKED_LIST_STORAGE_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False)


def _load_linked_lists():
    """从文件加载所有链表"""
    if os.path.exists(LINKED_LIST_STORAGE_FILE):
        try:
            with open(LINKED_LIST_STORAGE_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
            for name, values in data.items():
                ll = LinkedList(name)
                for v in values:
                    ll.append(v)
                _linked_lists[name] = ll
        except Exception:
            pass


# 初始化时加载已保存的链表
_load_linked_lists()


def get_linked_list(name: str) -> Optional[LinkedList]:
    """获取指定名称的链表"""
    # 每次操作前尝试加载，支持跨进程共享
    _load_linked_lists()
    return _linked_lists.get(name)


def create_linked_list(name: str) -> LinkedList:
    """创建或获取链表"""
    _load_linked_lists()
    if name not in _linked_lists:
        _linked_lists[name] = LinkedList(name)
    _save_linked_lists()
    return _linked_lists[name]


def delete_linked_list(name: str) -> bool:
    """删除链表"""
    _load_linked_lists()
    if name in _linked_lists:
        del _linked_lists[name]
        _save_linked_lists()
        return True
    return False


def get_all_linked_lists() -> List[str]:
    """获取所有链表名称"""
    _load_linked_lists()
    return list(_linked_lists.keys())


# ==================== 具体 FunctionCall 实现 ====================

class CreateLinkedList(AbstractFunctionCall):
    """创建链表函数"""

    class Parameters(BaseTool.Parameters):
        name: str = Field(description="链表名称")

    name = "create_linked_list"
    description = "创建一个新的链表，如果已存在则返回现有链表"

    def do_call(self, params: Parameters) -> Dict[str, Any]:
        ll = create_linked_list(params.name)
        return {
            "name": params.name,
            "size": ll.size,
            "created": ll.size == 0
        }


class AppendNode(AbstractFunctionCall):
    """尾部添加节点函数"""

    class Parameters(BaseTool.Parameters):
        list_name: str = Field(description="链表名称")
        value: Any = Field(description="要添加的值")

    name = "append_node"
    description = "在链表尾部添加节点"

    def do_call(self, params: Parameters) -> Dict[str, Any]:
        ll = get_linked_list(params.list_name)
        if ll is None:
            raise ValueError(f"链表 '{params.list_name}' 不存在")

        # Handle batch append when value is a list
        if isinstance(params.value, list):
            for v in params.value:
                ll.append(v)
            last_index = ll.size - 1
            _save_linked_lists()
            return {
                "list_name": params.list_name,
                "index": last_index,
                "value": params.value,
                "size": ll.size,
                "batch_count": len(params.value)
            }

        index = ll.append(params.value)
        _save_linked_lists()
        return {
            "list_name": params.list_name,
            "index": index,
            "value": params.value,
            "size": ll.size
        }


class PrependNode(AbstractFunctionCall):
    """头部添加节点函数"""

    class Parameters(BaseTool.Parameters):
        list_name: str = Field(description="链表名称")
        value: Any = Field(description="要添加的值")

    name = "prepend_node"
    description = "在链表头部添加节点"

    def do_call(self, params: Parameters) -> Dict[str, Any]:
        ll = get_linked_list(params.list_name)
        if ll is None:
            raise ValueError(f"链表 '{params.list_name}' 不存在")

        index = ll.prepend(params.value)
        _save_linked_lists()
        return {
            "list_name": params.list_name,
            "index": index,
            "value": params.value,
            "size": ll.size
        }


class InsertNode(AbstractFunctionCall):
    """插入节点函数"""

    class Parameters(BaseTool.Parameters):
        list_name: str = Field(description="链表名称")
        index: int = Field(description="插入位置（0-based）")
        value: Any = Field(description="要插入的值")

    name = "insert_node"
    description = "在链表指定位置插入节点"

    def do_call(self, params: Parameters) -> Dict[str, Any]:
        ll = get_linked_list(params.list_name)
        if ll is None:
            raise ValueError(f"链表 '{params.list_name}' 不存在")

        success = ll.insert(params.index, params.value)
        if not success:
            raise ValueError(f"插入失败: 索引 {params.index} 超出范围 [0, {ll.size}]")
        _save_linked_lists()

        return {
            "list_name": params.list_name,
            "index": params.index,
            "value": params.value,
            "size": ll.size
        }


class DeleteNodeAtIndex(AbstractFunctionCall):
    """删除指定位置节点函数"""

    class Parameters(BaseTool.Parameters):
        list_name: str = Field(description="链表名称")
        index: int = Field(description="要删除节点的索引")

    name = "delete_node_at_index"
    description = "删除链表中指定索引位置的节点"

    def do_call(self, params: Parameters) -> Dict[str, Any]:
        ll = get_linked_list(params.list_name)
        if ll is None:
            raise ValueError(f"链表 '{params.list_name}' 不存在")

        deleted_value = ll.delete_at(params.index)
        if deleted_value is None:
            raise ValueError(f"删除失败: 索引 {params.index} 超出范围")
        _save_linked_lists()

        return {
            "list_name": params.list_name,
            "deleted_index": params.index,
            "deleted_value": deleted_value,
            "size": ll.size
        }


class DeleteNodeByValue(AbstractFunctionCall):
    """删除指定值节点函数"""

    class Parameters(BaseTool.Parameters):
        list_name: str = Field(description="链表名称")
        value: Any = Field(description="要删除的值")

    name = "delete_node_by_value"
    description = "删除链表中第一个匹配指定值的节点"

    def do_call(self, params: Parameters) -> Dict[str, Any]:
        ll = get_linked_list(params.list_name)
        if ll is None:
            raise ValueError(f"链表 '{params.list_name}' 不存在")

        index = ll.delete_value(params.value)
        if index == -1:
            raise ValueError(f"删除失败: 链表中不存在值 '{params.value}'")
        _save_linked_lists()

        return {
            "list_name": params.list_name,
            "deleted_index": index,
            "deleted_value": params.value,
            "size": ll.size
        }


class UpdateNode(AbstractFunctionCall):
    """更新节点值函数"""

    class Parameters(BaseTool.Parameters):
        list_name: str = Field(description="链表名称")
        index: int = Field(description="节点索引")
        new_value: Any = Field(description="新的值")

    name = "update_node"
    description = "更新链表中指定索引位置的节点值"

    def do_call(self, params: Parameters) -> Dict[str, Any]:
        ll = get_linked_list(params.list_name)
        if ll is None:
            raise ValueError(f"链表 '{params.list_name}' 不存在")

        old_value = ll.get_at(params.index)
        if old_value is None:
            raise ValueError(f"更新失败: 索引 {params.index} 超出范围")

        success = ll.update_at(params.index, params.new_value)
        if not success:
            raise ValueError(f"更新失败: 索引 {params.index}")
        _save_linked_lists()

        return {
            "list_name": params.list_name,
            "index": params.index,
            "old_value": old_value,
            "new_value": params.new_value
        }


class GetNode(AbstractFunctionCall):
    """获取节点值函数"""

    class Parameters(BaseTool.Parameters):
        list_name: str = Field(description="链表名称")
        index: int = Field(description="节点索引")

    name = "get_node"
    description = "获取链表中指定索引位置的节点值"

    def do_call(self, params: Parameters) -> Dict[str, Any]:
        ll = get_linked_list(params.list_name)
        if ll is None:
            raise ValueError(f"链表 '{params.list_name}' 不存在")

        value = ll.get_at(params.index)
        if value is None:
            raise ValueError(f"获取失败: 索引 {params.index} 超出范围")

        return {
            "list_name": params.list_name,
            "index": params.index,
            "value": value
        }


class FindNode(AbstractFunctionCall):
    """查找节点函数"""

    class Parameters(BaseTool.Parameters):
        list_name: str = Field(description="链表名称")
        value: Any = Field(description="要查找的值")

    name = "find_node"
    description = "查找链表中第一个匹配指定值的节点索引"

    def do_call(self, params: Parameters) -> Dict[str, Any]:
        ll = get_linked_list(params.list_name)
        if ll is None:
            raise ValueError(f"链表 '{params.list_name}' 不存在")

        index = ll.find(params.value)
        if index == -1:
            raise ValueError(f"未找到值 '{params.value}'")

        return {
            "list_name": params.list_name,
            "index": index,
            "value": params.value,
            "found": True
        }


class GetLinkedList(AbstractFunctionCall):
    """获取链表完整信息函数"""

    class Parameters(BaseTool.Parameters):
        list_name: str = Field(description="链表名称")

    name = "get_linked_list"
    description = "获取链表的完整信息（大小、所有节点值）"

    def do_call(self, params: Parameters) -> Dict[str, Any]:
        ll = get_linked_list(params.list_name)
        if ll is None:
            raise ValueError(f"链表 '{params.list_name}' 不存在")

        return ll.to_dict()


class ClearLinkedList(AbstractFunctionCall):
    """清空链表函数"""

    class Parameters(BaseTool.Parameters):
        list_name: str = Field(description="链表名称")

    name = "clear_linked_list"
    description = "清空链表中的所有节点"

    def do_call(self, params: Parameters) -> Dict[str, Any]:
        ll = get_linked_list(params.list_name)
        if ll is None:
            raise ValueError(f"链表 '{params.list_name}' 不存在")

        old_size = ll.size
        ll.clear()
        _save_linked_lists()

        return {
            "list_name": params.list_name,
            "cleared_nodes": old_size,
            "size": 0
        }


class DeleteLinkedList(AbstractFunctionCall):
    """删除链表函数"""

    class Parameters(BaseTool.Parameters):
        list_name: str = Field(description="链表名称")

    name = "delete_linked_list"
    description = "删除整个链表"

    def do_call(self, params: Parameters) -> Dict[str, Any]:
        success = delete_linked_list(params.list_name)
        if not success:
            raise ValueError(f"链表 '{params.list_name}' 不存在")

        return {
            "list_name": params.list_name,
            "deleted": True
        }


class ListAllLinkedLists(AbstractFunctionCall):
    """列出所有链表函数"""

    class Parameters(BaseTool.Parameters):
        pass

    name = "list_all_linked_lists"
    description = "列出所有已创建的链表名称和大小"

    def do_call(self, params: Parameters) -> Dict[str, Any]:
        lists_info = []
        for name in get_all_linked_lists():
            ll = get_linked_list(name)
            lists_info.append({
                "name": name,
                "size": ll.size if ll else 0
            })

        return {
            "count": len(lists_info),
            "linked_lists": lists_info
        }


# ==================== 集成到 Tool 系统的封装 ====================

class LinkedListTool(BaseTool):
    """链表操作工具 - 集成到 Tool 系统"""

    name = "linked_list_tool"
    description = "链表创建、增删改查操作工具"

    class Parameters(BaseTool.Parameters):
        operation: str = Field(description="操作类型: create|append|prepend|insert|delete_at|delete_value|update|get|find|get_list|clear|delete_list|list_all")
        list_name: str = Field(default="default", description="链表名称")
        index: Optional[int] = Field(default=None, description="节点索引（insert, delete_at, update, get 需要）")
        value: Optional[Any] = Field(default=None, description="节点值（append, prepend, insert, delete_value, update, find 需要）")
        new_value: Optional[Any] = Field(default=None, description="新值（update 需要）")

    def _execute(self, params: Parameters) -> ToolResult:
        """执行链表操作"""
        try:
            context = FunctionCallContext()

            # 根据操作类型选择对应的 FunctionCall
            func_map = {
                "create": CreateLinkedList(context),
                "append": AppendNode(context),
                "prepend": PrependNode(context),
                "insert": InsertNode(context),
                "delete_at": DeleteNodeAtIndex(context),
                "delete_value": DeleteNodeByValue(context),
                "update": UpdateNode(context),
                "get": GetNode(context),
                "find": FindNode(context),
                "get_list": GetLinkedList(context),
                "clear": ClearLinkedList(context),
                "delete_list": DeleteLinkedList(context),
                "list_all": ListAllLinkedLists(context),
            }

            func = func_map.get(params.operation)
            if func is None:
                return ToolResult.error(
                    f"未知操作类型: {params.operation}，支持的操作: {', '.join(func_map.keys())}"
                )

            # 构建参数字典
            func_params = {"name": params.list_name} if params.operation == "create" else {}
            if params.list_name and params.operation != "list_all":
                func_params["list_name" if params.operation != "create" else "name"] = params.list_name
            if params.index is not None:
                func_params["index"] = params.index
            if params.value is not None:
                func_params["value"] = params.value
            if params.new_value is not None:
                func_params["new_value"] = params.new_value

            # 自动创建链表（如果操作需要链表但链表不存在）
            auto_create_ops = ["append", "prepend", "insert", "get_list", "get", "find", "clear", "update"]
            if params.operation in auto_create_ops:
                from devpal.tools.linked_list import _linked_lists
                if params.list_name not in _linked_lists:
                    create_func = CreateLinkedList(context)
                    create_result = create_func(name=params.list_name)
                    if not create_result.success:
                        return ToolResult.error(
                            f"自动创建链表失败: {create_result.error_message}",
                            execution_id=create_result.execution_id
                        )

            # 智能批量追加：当 append 的 value 是列表时，批量追加所有值
            if params.operation == "append" and isinstance(params.value, (list, tuple)):
                results = []
                for val in params.value:
                    single_params = {**func_params, "value": val}
                    result = AppendNode(context)(**single_params)
                    if not result.success:
                        return ToolResult.error(
                            f"批量追加失败: {result.error_message}",
                            data={"failed_at": val, "successful": results}
                        )
                    results.append(result.data)
                return ToolResult.ok(
                    f"批量追加 {len(results)} 个节点成功",
                    data={"count": len(results), "nodes": params.value}
                )

            # 普通执行
            result = func(**func_params)

            if result.success:
                return ToolResult.ok(
                    f"操作 {params.operation} 成功",
                    data=result.data,
                    execution_id=result.execution_id,
                    duration_ms=result.duration_ms
                )
            else:
                return ToolResult.error(
                    result.error_message or "操作失败",
                    execution_id=result.execution_id
                )

        except Exception as e:
            return ToolResult.error(f"链表操作异常: {str(e)}")
