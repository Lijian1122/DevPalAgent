# OpenSpec 新工作流设计 - 文档先行架构

## 设计理念

**核心思想**: 先设计后实现，文档驱动开发

传统流程问题：
- ❌ 直接生成代码，缺少架构设计阶段
- ❌ 代码生成后才发现设计问题，返工成本高
- ❌ 技术文档滞后，无法指导开发

新流程优势：
- ✅ 技术文档先行，明确架构设计
- ✅ Review 技术文档，提前发现设计问题
- ✅ 代码按照审核通过的文档实现，质量更高
- ✅ 文档和代码同步，可维护性强

---

## 新工作流 - 11 阶段（文档先行版）

### Phase 1: 解析需求文档
**输入**: requirements/xxx.md  
**输出**: 需求内容解析结果  
**工具**: file_reader

### Phase 2: 创建项目目录结构
**输入**: 项目名称  
**输出**: 标准目录结构  
```
project_name/
├── include/      # C++ 头文件
├── src/          # 源代码
├── tests/        # 测试代码
├── docs/         # 文档
│   ├── architecture.md      # 架构设计文档
│   ├── technical_design.md      # 技术设计文档 ⭐ 新增
│   ├── code_review_report.md    # 代码审查报告
│   └── test_report.md           # 测试报告
├── config/       # 配置文件
└── data/         # 数据文件
```

### Phase 3: 生成技术实现文档 ⭐ 新增阶段
**输入**: 需求文档内容  
**输出**: docs/technical_design.md  
**内容结构**:
```markdown
# 技术实现文档

## 1. 系统架构设计
- 整体架构图
- 模块划分
- 接口设计

## 2. 数据结构设计
- 核心数据结构
- 数据流图
- 存储方案

## 3. 核心算法设计
- 算法选择与理由
- 伪代码实现
- 复杂度分析

## 4. 安全机制设计
- 认证方案
- 加密算法
- 防护措施

## 5. 性能优化设计
- 性能目标
- 优化策略
- 瓶颈分析

## 6. 接口规范
- API 设计
- 参数定义
- 返回值规范

## 7. 错误处理设计
- 异常分类
- 错误码定义
- 恢复策略
```

**工具**: 新增 `technical_design_generator`

### Phase 4: Review 技术文档 ⭐ 新增阶段
**输入**: docs/technical_design.md  
**输出**: docs/technical_design_review.md  
**检查项**:
- ✅ 架构设计合理性
- ✅ 数据结构完整性
- ✅ 算法选择正确性
- ✅ 安全机制充分性
- ✅ 性能目标可达性
- ✅ 接口设计一致性

**工具**: 新增 `technical_design_reviewer`

### Phase 5: 生成核心代码
**输入**: docs/technical_design.md（审核通过的技术文档）  
**输出**: 
- C++: include/auth.h, src/auth.cpp, src/main.cpp
- Python: src/auth.py

**特点**: 严格按照技术文档实现，代码注释引用文档章节

**工具**: code_generator（增强版，支持从技术文档生成）

### Phase 6: Review 代码
**输入**: 生成的源代码  
**输出**: docs/code_review_report.md  
**检查项**:
- ✅ 代码与技术文档一致性
- ✅ 代码质量（命名、注释、结构）
- ✅ 安全漏洞检测
- ✅ 性能问题识别

**工具**: code_review（现有）

### Phase 7: 自动修复代码问题
**输入**: code_review_report.md  
**输出**: 修复后的代码  
**工具**: auto_fixer（现有）

### Phase 8: 生成测试文档
**输入**: 源代码 + 技术文档  
**输出**: docs/test_documentation.md  
**工具**: test_doc_generator（现有）

### Phase 9: 生成测试代码
**输入**: test_documentation.md  
**输出**: tests/test_auth.cpp 或 tests/test_auth.py  
**工具**: test_generator（现有）

### Phase 10: 编译并运行测试
**输入**: 测试代码  
**输出**: docs/test_execution_report.md  
**工具**: test_runner（现有）

### Phase 11: 生成验证报告
**输入**: 所有阶段结果  
**输出**: docs/openspec_verification_report.md  
**内容**:
- 需求覆盖率
- 代码质量评分
- 测试通过率
- 文档完整性
- 最终评估

**工具**: verification_reporter（现有）

---

## 新旧流程对比

### 旧流程（9 阶段）
```
Phase 1: 解析需求
Phase 2: 创建目录
Phase 3: 生成代码 ❌ 直接生成，无设计阶段
Phase 4: 代码审查
Phase 5: 自动修复
Phase 6-9: 测试流程（合并）
```

### 新流程（11 阶段 - 文档先行）
```
Phase 1: 解析需求
Phase 2: 创建目录
Phase 3: 生成技术文档 ⭐ 新增
Phase 4: Review 技术文档 ⭐ 新增
Phase 5: 生成代码（基于审核通过的文档）
Phase 6: Review 代码
Phase 7: 自动修复
Phase 8: 生成测试文档
Phase 9: 生成测试代码
Phase 10: 运行测试
Phase 11: 生成验证报告
```

---

## 关键改进点

### 1. 技术文档先行（Phase 3）
**为什么重要**:
- 提前发现架构设计问题
- 明确实现路径，减少返工
- 文档可作为代码生成的"蓝图"

**生成内容示例**:
```markdown
## 3. 核心算法设计

### 3.1 密码哈希算法
**选择**: SHA-256 + Salt
**理由**: 
- SHA-256 是 NIST 推荐的安全哈希算法
- 加盐可防止彩虹表攻击
- 性能开销可接受（~1ms/次）

**伪代码**:
```
function hash_password(password, salt):
    combined = password + salt
    hash = SHA256(combined)
    return hex(hash)
```

**实现要点**:
- Salt 长度: 16 bytes (128 bits)
- 使用 std::random_device 生成随机 salt
- 常量时间比较防止时序攻击
```

### 2. 技术文档 Review（Phase 4）
**为什么重要**:
- 在代码实现前发现设计缺陷
- 成本低：修改文档 << 修改代码
- 提高代码质量：按照审核通过的设计实现

**Review 检查点**:
```yaml
architecture_review:
  - 模块划分是否合理
  - 接口设计是否清晰
  - 依赖关系是否简洁

security_review:
  - 认证机制是否安全
  - 加密算法是否合规
  - 输入验证是否完整

performance_review:
  - 算法复杂度是否可接受
  - 是否存在性能瓶颈
  - 资源使用是否合理
```

### 3. 代码生成基于文档（Phase 5）
**改进**:
- 旧方式: 直接从需求生成代码（容易偏离设计）
- 新方式: 从技术文档生成代码（严格遵循设计）

**代码注释引用文档**:
```cpp
// 实现: 技术文档 3.1 节 - 密码哈希算法
std::string hash_password(const std::string& password, const std::string& salt) {
    // 按照文档设计: SHA-256 + Salt
    std::string combined = password + salt;
    return sha256(combined);
}
```

---

## 实施计划

### Step 1: 新增工具（1-2 天）

#### 1.1 TechnicalDesignGenerator
```python
class TechnicalDesignGeneratorTool(BaseTool):
    """技术设计文档生成器"""
    name = "technical_design_generator"
    
    class Parameters(BaseModel):
    requirements_content: str
      output_file: str
        language: str = "C++"
    
    def _execute(self, params):
        # 从需求生成技术设计文档
        # 包含: 架构、数据结构、算法、安全、性能、接口
        pass
```

#### 1.2 TechnicalDesignReviewer
```python
class TechnicalDesignReviewerTool(BaseTool):
    """技术设计文档审查器"""
    name = "technical_design_reviewer"
    
    class Parameters(BaseModel):
      design_doc_path: str
        output_file: str
    
    def _execute(self, params):
        # 审查技术文档
        # 检查: 架构合理性、安全性、性能、完整性
        pass
```

### Step 2: 升级 openspec_workflow.py（1 天）

修改 Phase 3-5:
```python
# Phase 3: 生成技术实现文档
print("[Phase 3/11] 生成技术实现文档...")
result = self.registry.execute_tool('technical_design_generator', {
    'requirements_content': req_content,
    'output_file': str(self.project_dir / 'docs' / 'technical_design.md'),
    'language': language
})

# Phase 4: Review 技术文档
print("[Phase 4/11] Review 技术文档...")
result = self.registry.execute_tool('technical_design_reviewer', {
    'design_doc_path': str(self.project_dir / 'docs' / 'technical_design.md'),
    'output_file': str(self.project_dir / 'docs' / 'technical_design_review.md')
})

# Phase 5: 生成核心代码（基于技术文档）
print("[Phase 5/11] 生成核心代码（基于技术文档）...")
if is_cpp:
    self._generate_cpp_auth_system_from_design(
        design_doc=self.project_dir / 'docs' / 'technical_design.md'
    )
else:
    self._generate_python_auth_system_from_design(
      design_doc=self.project_dir / 'docs' / 'technical_design.md'
    )
```

### Step 3: 测试验证（1 天）

测试用例:
```bash
# 测试 1: C++ 认证系统
python test_new_workflow.py requirements/cpp_authentication_system.md

# 验证生成文件:
# - docs/technical_design.md (技术文档)
# - docs/technical_design_review.md (技术文档审查)
# - docs/code_review_report.md (代码审查)
# - 所有代码文件

# 测试 2: Python 登录系统
python test_new_workflow.py requirements/login_requirements.md
```

---

## 预期收益

### 1. 代码质量提升
- **设计阶段发现问题**: 减少 50% 的代码返工
- **文档驱动实现**: 代码与设计一致性 > 95%
- **Review 覆盖**: 技术文档 + 代码双重审查

### 2. 开发效率提升
- **减少返工**: 设计阶段修改成本 < 代码阶段 10 倍
- **并行开发**: 技术文档可作为多人协作的契约
- **知识传承**: 完整的技术文档便于维护

### 3. 文档完整性
- **技术文档**: 架构、算法、安全、性能全覆盖
- **审查报告**: 设计审查 + 代码审查
- **测试文档**: 测试策略 + 执行报告
- **验证报告**: 需求覆盖率 + 质量评估

---

## 总结

### 核心变化
1. **Phase 3**: 生成代码 → 生成技术文档
2. **Phase 4**: 代码审查 → Review 技术文档
3. **Phase 5**: 自动修复 → 生成代码（基于文档）
4. **Phase 6**: 测试流程 → Review 代码
5. **Phase 7-11**: 拆分测试流程为独立阶段

### 设计哲学
> "先设计后实现，文档驱动开发"

- 技术文档是代码的"蓝图"
- Review 技术文档比 Review 代码更高效
- 代码严格按照审核通过的文档实现
- 文档和代码同步，可维护性强

---

**下一步**: 实施 Step 1 - 创建新工具
