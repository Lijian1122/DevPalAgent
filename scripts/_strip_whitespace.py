from pathlib import Path

files = [
    'devpal/core/openspec_phases/base.py',
    'devpal/core/openspec_phases/enhanced_scheduler.py',
    'devpal/core/openspec_phases/logger.py',
    'run_ai_flow.py',
    'tests/openspec/test_enhanced_scheduler_checkpoint.py',
    'tests/openspec/test_resume_phase4.py',
    'scripts/simulate_resume.py',
    'scripts/_apply_resume_logger.py',
]
for f in files:
    p = Path(f)
    if p.exists():
        text = p.read_text(encoding='utf-8')
        cleaned = '\n'.join(line.rstrip() for line in text.splitlines()) + '\n'
        p.write_text(cleaned, encoding='utf-8', newline='\n')
print('done')
