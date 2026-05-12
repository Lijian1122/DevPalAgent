# -*- coding: utf-8 -*-
"""
Phase 4: 生成核心实现代码 - 使用通用模板系统
"""

from pathlib import Path
from .base import PhaseInterface, PhaseResult, OpenSpecContext
from ..compiledb import CompileDB
from ..templates import registry, TemplateContext


class Phase4GenerateCode(PhaseInterface):
    """Phase 4: 生成核心实现代码 - 使用通用模板系统"""

    def __init__(self, context: OpenSpecContext, tool_registry):
        super().__init__(context)
        self.phase_number = 4
        self.phase_name = "生成核心实现代码"
        self.tool_registry = tool_registry
        self.compiledb = CompileDB()

    def execute(self) -> PhaseResult:
        """执行 Phase 4"""
        self.log("开始生成核心代码 (使用通用模板系统)...")

        project_dir = self.context.project_dir
        project_name = self.context.project_name or "MyProject"

        # 1. 索引现有项目（增量模式）
        if project_dir.exists():
            self.compiledb.index_project(project_dir)
            self.log(f"  索引现有项目: {len(self.compiledb.get_all_files())} 个文件")

        # 2. 准备模板上下文
        template_ctx = TemplateContext(
            project_name=project_name,
            language=self.context.language,
            features=self._detect_features(),
            existing_files=self.compiledb.get_all_files(),
            existing_symbols=[s.name for s in self.compiledb.get_all_symbols()]
        )

        # 3. 获取匹配的模板
        matching_templates = registry.get_matching_templates(template_ctx)
        self.log(f"  匹配到 {len(matching_templates)} 个模板")
        for t in matching_templates:
            self.log(f"    - {t.name}")

        # 4. 生成所有模板文件
        generated_files = []
        errors = []

        all_files = registry.generate_all(template_ctx)
        for gen_file in all_files:
            file_path = project_dir / gen_file.path

            # 增量检查：如果文件已存在，检查是否需要更新
            if file_path.exists():
                file_symbols = self.compiledb.get_file_symbols(str(file_path))
                if file_symbols:
                    self.log(f"  [SKIP] {gen_file.path} 已存在 (含 {len(file_symbols)} 个符号)")
                    continue

            # 确保目录存在
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(gen_file.content, encoding='utf-8')
            generated_files.append(file_path)
            self.log(f"  [OK] {gen_file.path}")

        self.context.generated_files.extend(generated_files)
        self.log(f"[OK] 核心代码生成完成: {len(generated_files)} 个文件")

        # 重新索引项目，确保 CompileDB 缓存包含新生成的文件
        if generated_files:
            self.compiledb.index_project(project_dir, use_cache=False)
            # 显式保存缓存（use_cache=False 时不会自动保存）
            self.compiledb.save_cache(project_dir)
            self.log(f"  [OK] 重新索引项目: {len(self.compiledb.get_all_files())} 个文件")

        if errors:
            return PhaseResult.fail(
                "核心代码生成存在部分错误",
                errors=errors
            )

        return PhaseResult.ok(
            "核心代码生成成功",
            generated_count=len(generated_files),
            files=[str(f.name) for f in generated_files],
            templates_used=[t.name for t in matching_templates]
        )

    def _detect_features(self) -> list:
        """从需求内容检测功能特性"""
        content = self.context.requirements_content.lower()
        features = ['auth']  # 默认包含认证

        feature_keywords = {
            'database': ['数据库', 'database', 'db', 'sql'],
            'api': ['api', '接口', 'http', 'rest'],
            'web': ['web', '网页', '前端'],
            'cli': ['cli', '命令行', 'cmd'],
            'test': ['测试', 'test', '单元测试'],
            'docs': ['文档', 'doc', 'readme'],
        }

        for feature, keywords in feature_keywords.items():
            for kw in keywords:
                if kw in content:
                    features.append(feature)
                    break

        return list(set(features))
