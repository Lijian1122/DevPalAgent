# Phase 9.5 Enhanced Scheduler 集成指南

## 集成位置

在文件 `devpal/core/openspec_phases/enhanced_scheduler.py` 中：

**位置**：在 line 532 之后（`print(f"[WARN] {warning_msg}")` 这一行之后）

## 需要添加的代码

在 line 532 后面添加以下代码块：

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

## 集成步骤

1. 打开 `devpal/core/openspec_phases/enhanced_scheduler.py`
2. 找到 line 532：`print(f"[WARN] {warning_msg}")`
3. 在这一行**之后**（line 533 的空行位置）插入上面的代码
4. 确保缩进正确（使用 12 个空格作为基础缩进）
5. 保存文件

## 验证

插入后运行以下命令验证语法：

```bash
python -m py_compile devpal/core/openspec_phases/enhanced_scheduler.py
```

如果没有输出，说明语法正确！

## 注意事项

- **缩进非常重要**：确保使用空格而不是 Tab
- **基础缩进**：`if i == 9` 这一行应该与上面的 `if not result.success:` 对齐
- **代码块位置**：必须在 Phase 执行循环内部，Phase 10 执行之前

## 配置（可选）

在 `config/config.yaml` 中添加（如果需要自定义配置）：

```yaml
openspec:
  enable_critique_phase: true  # 启用/禁用 Phase 9.5
  critique_config:
    dimension_weights:
      readability: 0.25
      architecture: 0.25
    security: 0.20
      performance: 0.15
      maintainability: 0.15
    max_files_to_review: 10
    skip_test_files: true
```

## 测试

集成完成后，运行端到端测试：

```bash
python run_ai_flow.py -r requirements/simple_login.md
```

检查输出：
- `docs/critique_report.md` - Critique 报告
- `.spec/critique_metrics.json` - JSON 指标
- `docs/final_report.md` - 应包含 Critique 章节
