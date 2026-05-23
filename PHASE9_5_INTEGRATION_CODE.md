# Phase 9.5 集成代码 - 直接复制粘贴版本

## 说明
将以下代码复制并粘贴到 `enhanced_scheduler.py` 的 line 532 之后

## 代码（已格式化，可直接复制）

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

## 插入位置示意

```python
... (前面的代码)

           else:
                    warning_msg = f"Phase {i} ..."
                    if context.logger:
                 context.logger.warning(warning_msg)
                 else:
                  print(f"[WARN] {warning_msg}")

         # ← 在这里插入 Phase 9.5 代码（line 533）

        # ---  ---
        #
        if self.checkpoint:
            self.checkpoint.clear(archive_reason="completed")

... (后面的代码)
```

## 验证步骤

1. 复制上面的代码块（从 `# --- Phase 9.5` 开始到最后的空行）
2. 在 VS Code 中打开 `enhanced_scheduler.py`
3. 定位到 line 532（`print(f"[WARN] {warning_msg}")`）
4. 在这一行后面按 Enter 创建新行
5. 粘贴代码
6. 保存文件
7. 运行验证：`python -m py_compile devpal/core/openspec_phases/enhanced_scheduler.py`

## 注意
- 代码使用 **12 个空格** 作为基础缩进（3 级缩进，每级 4 个空格）
- 确保粘贴后缩进对齐
- 如果有缩进错误，使用 VS Code 的 "Format Document" 功能
