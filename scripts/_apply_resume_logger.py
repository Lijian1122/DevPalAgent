from pathlib import Path

p = Path('devpal/core/openspec_phases/enhanced_scheduler.py')
text = p.read_text(encoding='utf-8')
lines = text.splitlines(keepends=True)

print_idx = None
else_idx = None
for idx, line in enumerate(lines):
    if '[RESUME]  Phase {start_phase}' in line and print_idx is None:
        print_idx = idx
    if 'checkpoint missing or incompatible' in line and else_idx is None:
        else_idx = idx

assert print_idx is not None and else_idx is not None
inserted_call = '             self._ensure_logger_for_resume(start_phase)\n'
lines.insert(print_idx + 1, inserted_call)
else_idx += 1

# Find blank line after `return self._run_phases_with_enhancements(start_phase)`
return_idx = None
for idx in range(else_idx, len(lines)):
    if 'return self._run_phases_with_enhancements(start_phase)' in lines[idx]:
      return_idx = idx
      break
assert return_idx is not None

helper = (
    '\n'
    '    def _ensure_logger_for_resume(self, start_phase: int) -> None:\n'
    '        context = self.context\n'
    '        if context.logger or not context.project_dir or not context.project_name:\n'
    '            return\n'
    '        try:\n'
    '            from .logger import OpenSpecLogger\n'
    '         context.project_dir.mkdir(parents=True, exist_ok=True)\n'
    '            context.logger = OpenSpecLogger(context.project_name, context.project_dir)\n'
    '       context.log_file = context.logger.log_file\n'
    '            print(f"[INFO] resume log: {context.log_file}")\n'
    '            context.logger.info(f"[RESUME] start_phase={start_phase}")\n'
    '            backfill_through = min(start_phase - 1, 11)\n'
    '            if backfill_through >= 1:\n'
    '          self._backfill_pre_logger_phases(\n'
    '                 context,\n'
    '                 current_phase=backfill_through + 1,\n'
    '                  current_duration=0.0,\n'
  '                )\n'
    '        except Exception as exc:\n'
    '         print(f"[WARN] failed to init resume logger: {exc}")\n'
)
lines.insert(return_idx + 2, helper)

p.write_text(''.join(lines), encoding='utf-8')
print('done')
