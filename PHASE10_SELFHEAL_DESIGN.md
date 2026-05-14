# Phase 10 Self-Heal Design

## 当前问题
1. 测试文档路径写死 - 应该动态发现
2. 测试失败后没有自愈机制

## 改进方案

### 1. 动态发现测试文档
```python
# 在 Phase 5 中已经设置了 ctx.test_docs
# Phase 10 直接使用即可，无需写死路径
```

### 2. 自愈流程设计

```
for each test_file:
    attempt = 0
    max_attempts = 3
    
    while attempt < max_attempts:
      # 编译
        compile_result = compile_test(test_file)
    
        if not compile_result.success:
            if attempt < max_attempts - 1:
           # AI 修复编译错误
              fix_compile_error(test_file, compile_result.error)
                attempt += 1
                continue
            else:
                break  # 放弃
        
        # 运行测试
        test_result = run_test(exe_path)
        
        if test_result.all_passed:
            break  # 成功
        
        if attempt < max_attempts - 1:
            # AI 修复测试失败
        fix_test_failure(test_file, test_result.failures)
            attempt += 1
        else:
            break  # 放弃
```

### 3. AI 修复函数

```python
def _ai_fix_compile_error(self, test_file, error_output):
    """使用 AI 修复编译错误"""
    # 1. 读取测试文件和相关源文件
    # 2. 构造 prompt：错误信息 + 代码
    # 3. 调用 LLM 生成修复
    # 4. 写回文件
    # 5. 更新 self.context.self_heal_attempts
    
def _ai_fix_test_failure(self, test_file, test_output, failures):
    """使用 AI 修复测试失败"""
    # 1. 分析测试输出，找出失败的测试用例
    # 2. 读取被测试的源文件
    # 3. 构造 prompt：测试代码 + 源代码 + 失败信息
    # 4. 调用 LLM 生成修复
    # 5. 写回源文件
    # 6. 更新 self.context.self_heal_attempts
```

### 4. 实现要点

- 每个测试文件最多尝试 3 次（可配置）
- 每次修复后强制重新编译（force_rebuild=True）
- 记录每次自愈尝试的详情
- 自愈失败后继续处理下一个测试文件
- 最终报告中显示自愈次数和成功率

### 5. 需要的工具

- LLMClient（已有）
- write_file tool（已有）
- 代码分析工具（可选）

## 实现优先级

1. **高优先级**：动态发现测试文档（简单，立即可做）
2. **中优先级**：基础自愈框架（循环重试）
3. **低优先级**：智能 AI 修复（复杂，需要精心设计 prompt）
