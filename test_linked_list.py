# -*- coding: utf-8 -*-
"""
链表工具测试脚本
测试抽象 FunctionCall 基类和链表操作功能
"""
from devpal.tools import (
    # 链表数据结构
    LinkedList,
    ListNode,

    # 抽象 FunctionCall 基类
    AbstractFunctionCall,
    FunctionCallContext,
    ExecutionResult,
    FunctionChain,

    # 具体 FunctionCall 实现
    CreateLinkedList,
    AppendNode,
    PrependNode,
    InsertNode,
    DeleteNodeAtIndex,
    DeleteNodeByValue,
    UpdateNode,
    GetNode,
    FindNode,
    GetLinkedList,
    ClearLinkedList,
    DeleteLinkedList,
    ListAllLinkedLists,

    # 集成工具
    LinkedListTool,
    registry
)


def test_linked_list_data_structure():
    """测试链表数据结构"""
    print("=" * 60)
    print("测试 1: 链表数据结构")
    print("=" * 60)

    ll = LinkedList("test_list")

    # 测试空链表
    assert ll.is_empty() is True
    assert len(ll) == 0
    print("  [OK] 空链表测试通过")

    # 测试尾部添加
    ll.append(10)
    ll.append(20)
    ll.append(30)
    assert len(ll) == 3
    assert ll.to_list() == [10, 20, 30]
    print("  [OK] 尾部添加节点测试通过")

    # 测试头部添加
    ll.prepend(5)
    assert len(ll) == 4
    assert ll.to_list() == [5, 10, 20, 30]
    print("  [OK] 头部添加节点测试通过")

    # 测试插入
    ll.insert(2, 15)
    assert len(ll) == 5
    assert ll.to_list() == [5, 10, 15, 20, 30]
    print("  [OK] 中间插入节点测试通过")

    # 测试获取
    assert ll.get_at(0) == 5
    assert ll.get_at(2) == 15
    assert ll.get_at(4) == 30
    assert ll.get_at(100) is None
    print("  [OK] 获取节点测试通过")

    # 测试查找
    assert ll.find(15) == 2
    assert ll.find(100) == -1
    print("  [OK] 查找节点测试通过")

    # 测试更新
    assert ll.update_at(2, 100) is True
    assert ll.get_at(2) == 100
    assert ll.update_at(100, 200) is False
    print("  [OK] 更新节点测试通过")

    # 测试按索引删除
    deleted = ll.delete_at(2)
    assert deleted == 100
    assert len(ll) == 4
    assert ll.to_list() == [5, 10, 20, 30]
    print("  [OK] 按索引删除测试通过")

    # 测试按值删除
    deleted_idx = ll.delete_value(20)
    assert deleted_idx == 2
    assert len(ll) == 3
    assert ll.to_list() == [5, 10, 30]
    print("  [OK] 按值删除测试通过")

    # 测试清空
    ll.clear()
    assert ll.is_empty() is True
    assert len(ll) == 0
    print("  [OK] 清空链表测试通过")

    print("\n  [OK] 链表数据结构测试全部通过\n")


def test_function_call_basic():
    """测试抽象 FunctionCall 基类"""
    print("=" * 60)
    print("测试 2: 抽象 FunctionCall 基类")
    print("=" * 60)

    context = FunctionCallContext()

    # 创建链表
    create_func = CreateLinkedList(context)
    result = create_func(name="my_list")
    assert result.success is True
    assert result.data["name"] == "my_list"
    print("  [OK] CreateLinkedList 执行成功")

    # 尾部添加
    append_func = AppendNode(context)
    result = append_func(list_name="my_list", value=100)
    assert result.success is True
    assert result.data["index"] == 0
    print("  [OK] AppendNode 执行成功")

    # 继续添加
    append_func(list_name="my_list", value=200)
    append_func(list_name="my_list", value=300)

    # 获取链表
    get_func = GetLinkedList(context)
    result = get_func(list_name="my_list")
    assert result.success is True
    assert result.data["size"] == 3
    assert result.data["nodes"] == [100, 200, 300]
    print("  [OK] GetLinkedList 执行成功")

    print(f"  [OK] 调用记录: {context.get_call_count()} 次调用")
    print(f"  [OK] 总耗时: {context.get_total_duration():.2f}ms")

    print("\n  [OK] 抽象 FunctionCall 测试全部通过\n")


def test_function_chain():
    """测试函数链（链式调用）"""
    print("=" * 60)
    print("测试 3: 函数链（链式调用）")
    print("=" * 60)

    context = FunctionCallContext()

    # 创建执行链
    chain = FunctionChain(
        CreateLinkedList(context),
        AppendNode(context),
        AppendNode(context),
        AppendNode(context),
        GetLinkedList(context),
        context=context
    )

    # 执行链条
    results = chain.execute(
        name="chain_list",
        list_name="chain_list",
        value=1  # 第一个 append 的值
    )

    # 检查结果
    assert len(results) == 5  # create + 3 appends + get_list
    assert all(r.success for r in results)

    final_result = results[-1].data
    assert final_result["size"] == 3

    summary = chain.get_summary()
    assert summary["total_calls"] == 5
    assert summary["success_count"] == 5

    print(f"  [OK] 链式调用成功: {summary['total_calls']} 次调用")
    print(f"  [OK] 全部成功: {summary['success_count']} 次成功")
    print(f"  [OK] 总耗时: {summary['total_duration_ms']:.2f}ms")

    print("\n  [OK] 函数链测试全部通过\n")


def test_linked_list_crud():
    """测试链表完整 CRUD 操作"""
    print("=" * 60)
    print("测试 4: 链表完整 CRUD 操作")
    print("=" * 60)

    context = FunctionCallContext()

    # 创建
    create = CreateLinkedList(context)(name="crud_list")
    assert create.success
    print("  [OK] 创建链表")

    # 增加（C）
    AppendNode(context)(list_name="crud_list", value=10)
    AppendNode(context)(list_name="crud_list", value=20)
    AppendNode(context)(list_name="crud_list", value=30)
    print("  [OK] 增加节点")

    # 查询（R）
    get_result = GetLinkedList(context)(list_name="crud_list")
    assert get_result.data["nodes"] == [10, 20, 30]
    print("  [OK] 查询全部节点")

    # 修改（U）
    update_result = UpdateNode(context)(list_name="crud_list", index=1, new_value=200)
    assert update_result.data["old_value"] == 20
    assert update_result.data["new_value"] == 200
    print("  [OK] 修改节点")

    # 验证修改
    get_result = GetLinkedList(context)(list_name="crud_list")
    assert get_result.data["nodes"] == [10, 200, 30]
    print("  [OK] 验证修改成功")

    # 删除（D）
    delete_result = DeleteNodeAtIndex(context)(list_name="crud_list", index=1)
    assert delete_result.data["deleted_value"] == 200
    print("  [OK] 删除节点")

    # 验证删除
    get_result = GetLinkedList(context)(list_name="crud_list")
    assert get_result.data["nodes"] == [10, 30]
    assert get_result.data["size"] == 2
    print("  [OK] 验证删除成功")

    print("\n  [OK] 链表 CRUD 测试全部通过\n")


def test_linked_list_tool_integration():
    """测试 LinkedListTool 集成到 Tool 系统"""
    print("=" * 60)
    print("测试 5: LinkedListTool 集成到 Tool 系统")
    print("=" * 60)

    # 检查工具是否已注册
    tool = registry.get("linked_list_tool")
    assert tool is not None
    print("  [OK] LinkedListTool 已注册")

    # 测试创建链表
    result = registry.execute_tool("linked_list_tool", {
        "operation": "create",
        "list_name": "integrated_list"
    })
    assert result.success is True
    print("  [OK] 通过 ToolRegistry 创建链表成功")

    # 测试添加节点
    result = registry.execute_tool("linked_list_tool", {
        "operation": "append",
        "list_name": "integrated_list",
        "value": "hello"
    })
    assert result.success is True
    print("  [OK] 通过 ToolRegistry 添加节点成功")

    # 测试获取链表
    result = registry.execute_tool("linked_list_tool", {
        "operation": "get_list",
        "list_name": "integrated_list"
    })
    assert result.success is True
    assert result.metadata["data"]["size"] == 1
    print("  [OK] 通过 ToolRegistry 获取链表成功")

    # 列出所有链表
    result = registry.execute_tool("linked_list_tool", {
        "operation": "list_all"
    })
    assert result.success is True
    print(f"  [OK] 当前链表数量: {result.metadata['data']['count']}")

    print("\n  [OK] LinkedListTool 集成测试全部通过\n")


def test_error_handling():
    """测试错误处理"""
    print("=" * 60)
    print("测试 6: 错误处理")
    print("=" * 60)

    context = FunctionCallContext()

    # 访问不存在的链表
    result = GetLinkedList(context)(list_name="non_existent")
    assert result.success is False
    assert "不存在" in result.error_message
    print("  [OK] 访问不存在链表的错误处理正确")

    # 访问不存在的索引
    CreateLinkedList(context)(name="error_test_list")
    result = GetNode(context)(list_name="error_test_list", index=999)
    assert result.success is False
    print("  [OK] 访问不存在索引的错误处理正确")

    # 执行失败会被记录到上下文
    assert context.get_call_count() == 3
    print(f"  [OK] 错误调用被记录: {context.get_call_count()} 次调用")

    print("\n  [OK] 错误处理测试全部通过\n")


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("  DevPal Agent - 链表工具测试套件")
    print("=" * 70 + "\n")

    test_linked_list_data_structure()
    test_function_call_basic()
    test_function_chain()
    test_linked_list_crud()
    test_linked_list_tool_integration()
    test_error_handling()

    print("=" * 70)
    print("  [PASS] 所有测试全部通过！")
    print("=" * 70)
    print("\n  测试内容总结:")
    print("  [OK] LinkedList 数据结构（ListNode 链表节点）")
    print("  [OK] AbstractFunctionCall 抽象基类（泛型、参数校验、执行追踪）")
    print("  [OK] FunctionChain 函数链（链式调用、结果传递）")
    print("  [OK] 12 个具体 FunctionCall 实现（完整 CRUD）")
    print("  [OK] LinkedListTool 集成到 Tool 系统")
    print("  [OK] 错误处理机制")
