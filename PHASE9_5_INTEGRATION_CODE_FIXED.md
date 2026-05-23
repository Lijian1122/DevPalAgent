# Phase 9.5 集成代码 - 正确格式版本

## 重要说明
- 使用 **4 个空格** 作为一级缩进
- `if i == 9` 这一行应该与上面的其他 `if` 语句对齐（3 级缩进 = 12 个空格）
- 整个代码块在 Phase 执行循环内部

## 插入位置

在 `enhanced_scheduler.py` 的 **line 532** 之后插入：

```python
              else:
                    print(f"[WARN] {warning_msg}")
```

在这两行**之后**插入下面的代码。

## 正确格式的集成代码

```python
            # --- Phase 9.5: Critique Phase (after Phase 9 Quality Gate) ---
          if i == 9 and result.success:
                enable_critique = self.config.get('enable_critique_phase', True)
                if enable_critique:
                try:
             if context.logger:
                  context.logger.info("Starting Phase 9.5: Critique Phase")
                   
                # Get LLM client from base_scheduler
                        llm_client = None
                   if hasattr(self.base_scheduler, 'llm_client'):
                      llm_client = self.base_scheduler.llm_client
                        
                  # Get critique config
                        critique_config = self.config.get('critique_config', {})
                     
                  # Import and execute Phase 9.5
                  from .phase9_5_critique import Phase9_5Critique
                 phase_9_5 = Phase9_5Critique(context, llm_client=llm_client, config=critique_config)
                 
                    if context.logger:
                      context.logger.phase_start(9.5, "Critique Phase")
                  
                     critique_result, critique_duration = phase_9_5.execute_with_timing()
                   
                     if context.logger:
              context.logger.phase_end(9.5, critique_result.success, critique_duration)
                   
                   # Store result
                      context.phase_results[9.5] = critique_result
                   
                      if critique_result.success:
                    if context.logger:
                         overall_score = critique_result.data.get('overall_score', 'N/A')
                        context.logger.info(f"Phase 9.5 completed: Overall Score = {overall_score}/100")
                   else:
                        # Critique Phase failure is not critical
                         if context.logger:
                         context.logger.warning(f"Phase 9.5 failed: {critique_result.message}")
                      else:
                          print(f"[WARN] Phase 9.5 Critique failed: {critique_result.message}")
                    
                    except Exception as e:
                # Critique Phase errors should not stop the workflow
          if context.logger:
                  context.logger.error(f"Phase 9.5 Critique error: {e}")
                     else:
                            print(f"[ERROR] Phase 9.5 Critique error: {e}")
                else:
                  if context.logger:
                   context.logger.info("Phase 9.5 Critique disabled, skipping")
                    else:
                     print("[INFO] Phase 9.5 Critique disabled, skipping")

```

## 插入后的代码应该看起来像这样

```python
... (前面的代码)

                else:
            warning_msg = f"Phase {i} ..."
                    if context.logger:
           context.logger.warning(warning_msg)
                    else:
                 print(f"[WARN] {warning_msg}")

            # --- Phase 9.5: Critique Phase (after Phase 9 Quality Gate) ---
            if i == 9 and result.success:
                enable_critique = self.config.get('enable_critique_phase', True)
                if enable_critique:
                 try:
                      if context.logger:
                            context.logger.info("Starting Phase 9.5: Critique Phase")
              
                      # ... (Phase 9.5 代码)
                        
                except Exception as e:
                        if context.logger:
                   context.logger.error(f"Phase 9.5 Critique error: {e}")
                 else:
                          print(f"[ERROR] Phase 9.5 Critique error: {e}")
             else:
                  if context.logger:
                  context.logger.info("Phase 9.5 Critique disabled, skipping")
                    else:
                      print("[INFO] Phase 9.5 Critique disabled, skipping")

        # ---  ---
        #
        if self.checkpoint:
            self.checkpoint.clear(archive_reason="completed")

... (后面的代码)
```

## 关键缩进规则

| 代码行 | 缩进级别 | 空格数 |
|--------|---------|--------|
| `# --- Phase 9.5` | 3 级 | 12 |
| `if i == 9` | 3 级 | 12 |
| `enable_critique = ...` | 4 级 | 16 |
| `if enable_critique:` | 4 级 | 16 |
| `try:` | 5 级 | 20 |
| `if context.logger:` | 6 级 | 24 |
| `context.logger.info(...)` | 7 级 | 28 |

## 验证步骤

1. 复制上面"正确格式的集成代码"部分（从 `# --- Phase 9.5` 到最后的空行）
2. 在 VS Code 中打开 `enhanced_scheduler.py`
3. 按 `Ctrl+G` 输入 `532` 跳转到 line 532
4. 在 line 532 的 `print(f"[WARN] {warning_msg}")` 后面按 Enter 创建新行
5. 粘贴代码
6. **重要**：粘贴后，选中所有粘贴的代码，按 `Shift+Tab` 一次或多次调整缩进，使 `if i == 9` 与上面的 `else:` 对齐
7. 保存文件
8. 验证：`python -m py_compile devpal/core/openspec_phases/enhanced_scheduler.py`

## 如果还是有缩进问题

使用 VS Code 的自动格式化：
1. 粘贴代码后
2. 选中所有粘贴的代码
3. 右键 → "Format Selection" 或按 `Ctrl+K Ctrl+F`
4. VS Code 会自动调整缩进

## 或者使用 Python 脚本自动插入

如果手动粘贴还是有问题，运行这个脚本：

```bash
cd c:/code/DevPalAgent && python << 'PYEOF'
# 读取文件
with open('devpal/core/openspec_phases/enhanced_scheduler.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Phase 9.5 代码（正确缩进）
phase_9_5_code = '''
            # --- Phase 9.5: Critique Phase (after Phase 9 Quality Gate) ---
            if i == 9 and result.success:
                enable_critique = self.config.get('enable_critique_phase', True)
                if enable_critique:
                    try:
             if context.logger:
                            context.logger.info("Starting Phase 9.5: Critique Phase")
                    
               # Get LLM client from base_scheduler
                llm_client = None
                        if hasattr(self.base_scheduler, 'llm_client'):
                     llm_client = self.base_scheduler.llm_client
                    
                        # Get critique config
              critique_config = self.config.get('critique_config', {})
                
                    # Import and execute Phase 9.5
                        from .phase9_5_critique import Phase9_5Critique
                 phase_9_5 = Phase9_5Critique(context, llm_client=llm_client, config=critique_config)
                     
                        if context.logger:
                       context.logger.phase_start(9.5, "Critique Phase")
             
           critique_result, critique_duration = phase_9_5.execute_with_timing()
              
                 if context.logger:
                        context.logger.phase_end(9.5, critique_result.success, critique_duration)
              
                        # Store result
                    context.phase_results[9.5] = critique_result
                     
                    if critique_result.success:
                          if context.logger:
                   overall_score = critique_result.data.get('overall_score', 'N/A')
                      context.logger.info(f"Phase 9.5 completed: Overall Score = {overall_score}/100")
                     else:
                    # Critique Phase failure is not critical
                       if context.logger:
                          context.logger.warning(f"Phase 9.5 failed: {critique_result.message}")
               else:
                          print(f"[WARN] Phase 9.5 Critique failed: {critique_result.message}")
                    
                    except Exception as e:
                # Critique Phase errors should not stop the workflow
                   if context.logger:
                            context.logger.error(f"Phase 9.5 Critique error: {e}")
                      else:
                         print(f"[ERROR] Phase 9.5 Critique error: {e}")
              else:
               if context.logger:
                  context.logger.info("Phase 9.5 Critique disabled, skipping")
                 else:
                        print("[INFO] Phase 9.5 Critique disabled, skipping")

'''

# 插入到 line 532 之后
insert_pos = 532
new_lines = lines[:insert_pos] + [phase_9_5_code] + lines[insert_pos:]

# 写回
with open('devpal/core/openspec_phases/enhanced_scheduler.py', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print("✓ Phase 9.5 代码已插入")
print("验证: python -m py_compile devpal/core/openspec_phases/enhanced_scheduler.py")
PYEOF
```

运行这个脚本会自动插入正确格式的代码！
