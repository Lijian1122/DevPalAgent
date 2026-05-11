# OpenSpec 项目名称推断问题修复方案

## 🐛 问题描述

### 问题 1：硬编码的项目名称
**位置：** `devpal/core/agent_engine.py:847`

```python
# 当前代码（错误）
project_dir = Path('cpp_authentication_system')  # 硬编码！
```

**影响：**
- 无论用户请求什么需求，都会创建 `cpp_authentication_system` 目录
- 用户请求"生产者消费者模型"，却得到"认证系统"项目

### 问题 2：硬编码的代码生成
**位置：** `devpal/core/agent_engine.py:857-1500`

```python
# 当前代码（错误）
print("\n[Phase 3/11] 生成用户认证系统核心代码...")  # 硬编码！

# 然后生成的全是认证系统的代码
auth_h_content = """#ifndef AUTH_H
...
class User { ... };
class Session { ... };
class Authenticator { ... };
"""
```

**影响：**
- 无论需求是什么，都生成认证系统的代码
- 完全忽略了实际的需求内容
---

## ✅ 修复方案

### 方案 A：基于需求文件名推断（快速修复）

#### 修改 1：动态项目名称
```python
# 位置：agent_engine.py:847
# 修改前：
project_dir = Path('cpp_authentication_system')

# 修改后：
# 从需求文件名推断项目名称
req_file_path = Path(req_file)
project_name = req_file_path.stem  # 例如：login_requirements → login_requirements
if project_name.endswith('_requirements'):
    project_name = project_name.replace('_requirements', '')
if project_name.startswith('req_'):
    project_name = project_name.replace('req_', '')

# 如果是 C++ 项目，添加 cpp_ 前缀
if is_cpp and not project_name.startswith('cpp_'):
    project_name = f'cpp_{project_name}'

project_dir = Path(project_name)
print(f"  [INFO] 项目名称: {project_name}")
```
#### 修改 2：动态代码生成提示
```python
# 位置：agent_engine.py:857
# 修改前：
print("\n[Phase 3/11] 生成用户认证系统核心代码...")

# 修改后：
# 从需求内容推断项目类型
project_type = "核心代码"
if "认证" in req_content or "登录" in req_content or "authentication" in req_content.lower():
    project_type = "用户认证系统核心代码"
elif "线程池" in req_content or "生产者消费者" in req_content or "thread pool" in req_content.lower():
    project_type = "线程池核心代码"
elif "数据库" in req_content or "database" in req_content.lower():
    project_type = "数据库核心代码"

print(f"\n[Phase 3/11] 生成{project_type}...")
```

---

### 方案 B：基于需求内容动态生成（完整修复）

这需要更大的重构，将硬编码的代码生成逻辑改为基于需求内容的动态生成。

#### 架构改进
```python
class CodeGenerator:
    """根据需求内容动态生成代码"""
    
    def __init__(self, req_content: str, language: str):
        self.req_content = req_content
    self.language = language
        self.project_type = self._detect_project_type()
    
    def _detect_project_type(self) -> str:
        """检测项目类型"""
        content_lower = self.req_content.lower()
        
      if any(kw in content_lower for kw in ['认证', '登录', 'authentication', 'login']):
            return 'authentication'
        elif any(kw in content_lower for kw in ['线程池', '生产者消费者', 'thread pool', 'producer consumer']):
            return 'thread_pool'
        elif any(kw in content_lower for kw in ['数据库', 'database', 'sql']):
            return 'database'
        else:
         return 'generic'
    
    def generate_code(self, project_dir: Path):
        """根据项目类型生成代码"""
        if self.project_type == 'authentication':
            self._generate_auth_system(project_dir)
        elif self.project_type == 'thread_pool':
      self._generate_thread_pool(project_dir)
        elif self.project_type == 'database':
          self._generate_database_system(project_dir)
        else:
            self._generate_generic_project(project_dir)
    
    def _generate_thread_pool(self, project_dir: Path):
        """生成线程池/生产者消费者代码"""
        # 生成 thread_pool.h
        header_content = """#ifndef THREAD_POOL_H
#define THREAD_POOL_H

#include <vector>
#include <queue>
#include <thread>
#include <mutex>
#include <condition_variable>
#include <functional>
#include <future>

class ThreadPool {
public:
    ThreadPool(size_t num_threads);
    ~ThreadPool();
    
    template<class F, class... Args>
    auto enqueue(F&& f, Args&&... args) 
      -> std::future<typename std::result_of<F(Args...)>::type>;
    
private:
    std::vector<std::thread> workers;
    std::queue<std::function<void()>> tasks;
    
    std::mutex queue_mutex;
    std::condition_variable condition;
    bool stop;
};

#endif
"""
        (project_dir / 'include' / 'thread_pool.h').write_text(header_content)
        
        # 生成 thread_pool.cpp
        # 生成 producer_consumer.h
        # 生成 producer_consumer.cpp
        # 生成 main.cpp
        # ...
```

---

## 🔧 快速修复代码

### 文件：`devpal/core/agent_engine.py`

#### 修改位置 1：第 847 行
```python
# 替换这一行：
# project_dir = Path('cpp_authentication_system')

# 为：
req_file_path = Path(req_file)
project_name = req_file_path.stem
if project_name.endswith('_requirements'):
    project_name = project_name.replace('_requirements', '')
if project_name.startswith('req_'):
    project_name = project_name.replace('req_', '')
if is_cpp and not project_name.startswith('cpp_'):
    project_name = f'cpp_{project_name}'
project_dir = Path(project_name)
print(f"  [INFO] 推断项目名称: {project_name}")
```

#### 修改位置 2：第 857 行
```python
# 替换这一行：
# print("\n[Phase 3/11] 生成用户认证系统核心代码...")

# 为：
project_type_desc = "核心代码"
if "认证" in req_content or "登录" in req_content:
    project_type_desc = "用户认证系统核心代码"
elif "线程池" in req_content or "生产者消费者" in req_content:
    project_type_desc = "线程池/生产者消费者核心代码"
elif "数据库" in req_content:
    project_type_desc = "数据库系统核心代码"

print(f"\n[Phase 3/11] 生成{project_type_desc}...")
```
---

## 📋 测试用例

### 测试 1：认证系统
```
输入：完整实现 requirements/login_requirements.md
预期项目名：cpp_login 或 cpp_authentication
预期代码：认证系统相关代码
```

### 测试 2：线程池
```
输入：完成用C++实现一个生产者消费者模型的需求 需要用线程池模型
预期项目名：cpp_producer_consumer 或 cpp_thread_pool
预期代码：线程池和生产者消费者相关代码
```

### 测试 3：数据库
```
输入：实现 requirements/database_requirements.md
预期项目名：cpp_database
预期代码：数据库相关代码
```
---

## ⚠️ 当前限制

即使修复了项目名称推断，**代码生成逻辑仍然是硬编码的**。

当前代码生成（第 860-1500 行）全部是认证系统的代码：
- `auth.h` - 认证头文件
- `auth.cpp` - 认证实现
- `User` 类
- `Session` 类
- `Authenticator` 类

**要真正支持不同类型的项目，需要：**
1. 创建代码生成器抽象层
2. 为每种项目类型实现专门的生成器
3. 根据需求内容选择合适的生成器

---

## 🎯 推荐实施步骤

### 短期（立即修复）
1. ✅ 修复项目名称推断（第 847 行）
2. ✅ 修复代码生成提示（第 857 行）
3. ⚠️ 添加警告：当需求不是认证系统时，提示用户当前只支持认证系统

### 中期（1-2周）
1. 实现 `CodeGenerator` 抽象类
2. 实现 `ThreadPoolGenerator`
3. 实现 `DatabaseGenerator`
4. 根据需求内容自动选择生成器

### 长期（1-2月）
1. 使用 AI 根据需求文档动态生成代码
2. 支持任意类型的项目
3. 完全消除硬编码

---

## 📝 临时解决方案

在完全修复之前，可以：

1. **创建专门的需求文件**
   ```bash
   # 为线程池创建专门的需求文档
   cp requirements/login_requirements.md requirements/thread_pool_requirements.md
   # 编辑内容为线程池需求
   ```

2. **创建专门的生成脚本**
   ```python
   # scripts/generate_thread_pool.py
   # 专门用于生成线程池项目
   ```

3. **手动指定项目类型**
   ```python
   # 添加命令行参数
   --project-type thread_pool
   ```

---

**创建日期：** 2026-05-10  
**优先级：** 🔴 高（影响核心功能）  
**状态：** 待修复
