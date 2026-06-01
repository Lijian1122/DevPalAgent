# 技术设计文档

## 1. 系统架构概览

本项目为极简 C++17 加法计算器，采用轻量分层结构：

- **接口层**：`include/calculator.h`，声明 `Calculator` 类及 `add` 方法。
- **实现层**：`src/calculator.cpp`，实现加法逻辑。
- **演示层**：`src/main.cpp`，展示 `Calculator::add` 的基本调用。
- **测试层**：`tests/test_calculator.cpp`，验证加法功能正确性。
- **构建层**：`CMakeLists.txt`，定义库、可执行程序和测试目标。

数据流：

1. 调用方创建 `Calculator` 对象。
2. 调用 `add(int a, int b)`。
3. `Calculator` 返回 `a + b` 的整数结果。
4. 演示程序输出结果，测试程序断言返回值。

## 2. 核心模块清单

- **Calculator 模块**
  - 职责：提供整数加法能力。
  - 关键类：`Calculator`
  - 关键函数：`int add(int a, int b) const`

- **Demo 模块**
  - 职责：提供命令行演示入口。
  - 关键函数：`int main()`

- **Test 模块**
  - 职责：验证 `Calculator::add` 在正数、负数、零值场景下的行为。
  - 关键测试：`testPositiveAddition`、`testNegativeAddition`、`testZeroAddition`

- **Build 模块**
  - 职责：使用 CMake 管理编译目标。
  - 关键目标：`calculator_lib`、`simple_calculator`、`test_calculator`

## 3. 关键 API 定义

```cpp
// include/calculator.h
#ifndef CALCULATOR_H
#define CALCULATOR_H

class Calculator {
public:
    Calculator();
    ~Calculator() = default;

    int add(int a, int b) const;
};

#endif // CALCULATOR_H
```

```cpp
// src/calculator.cpp
#include "calculator.h"

Calculator::Calculator() = default;

int Calculator::add(int a, int b) const;
```

```cpp
// src/main.cpp
int main();
```

测试接口建议：

```cpp
// tests/test_calculator.cpp
void testPositiveAddition();
void testNegativeAddition();
void testZeroAddition();
int main();
```

若使用 gtest：

```cpp
TEST(CalculatorTest, AddPositiveNumbers);
TEST(CalculatorTest, AddNegativeNumbers);
TEST(CalculatorTest, AddWithZero);
```

## 4. 数据结构与持久化

- **主要数据结构**
  - `Calculator`：无成员变量、无内部状态。
  - 输入参数：`int a`、`int b`
  - 返回值：`int`

- **状态管理**
  - `Calculator` 为无状态类，可安全重复使用。
  - 不维护缓存、历史记录或全局状态。

- **持久化**
  - 本项目不需要文件、数据库或网络持久化。
  - 所有计算均在内存和调用栈中完成。

- **整数溢出**
  - `int` 加法遵循 C++ 标准行为。
  - 需求未要求溢出检测，因此 `add` 不额外处理溢出。
  - 若后续扩展，可增加 `bool tryAdd(int a, int b, int& result)`。

## 5. 安全与并发设计

- **安全性**
  - 不使用裸指针，不涉及动态内存分配。
  - 不处理外部输入解析，避免输入注入风险。
  - 不使用第三方库，完全基于 C++17 STL 和语言特性。

- **异常安全**
  - `Calculator::add` 不分配资源、不抛出业务异常。
  - 可声明为简单确定性函数。

- **并发设计**
  - `Calculator` 无共享可变状态。
  - 多线程中可安全并发调用同一个 `Calculator` 实例的 `add` 方法。
  - 不需要互斥锁、原子变量或线程池。

- **资源管理**
  - 使用 RAII 默认对象生命周期。
  - 无手动资源释放逻辑。

## 6. 文件组织

```text
simple_calculator/
├── CMakeLists.txt
├── include/
│   └── calculator.h
├── src/
│   ├── calculator.cpp
│   └── main.cpp
├── tests/
│   └── test_calculator.cpp
└── docs/
    └── technical_design.md
```

文件职责：

- `include/calculator.h`
  - 声明 `Calculator` 类。
  - 使用 include guard：`CALCULATOR_H`。

- `src/calculator.cpp`
  - 实现 `Calculator` 构造函数和 `add` 方法。

- `src/main.cpp`
  - 创建 `Calculator` 对象。
  - 调用 `add(1, 2)`。
  - 使用 `std::cout` 输出结果。

- `tests/test_calculator.cpp`
  - 测试 `add(1, 2) == 3`
  - 测试 `add(-1, -2) == -3`
  - 测试 `add(-1, 1) == 0`
  - 测试 `add(0, 0) == 0`

- `CMakeLists.txt`
  - 设置 `CMAKE_CXX_STANDARD 17`
  - 添加静态库目标 `calculator_lib`
  - 添加演示可执行目标 `simple_calculator`
  - 添加测试目标 `test_calculator`

## 7. 测试策略

- **单元测试范围**
  - 正整数加法：`1 + 2 = 3`
  - 负整数加法：`-1 + -2 = -3`
  - 正负抵消：`-1 + 1 = 0`
  - 零值加法：`0 + 0 = 0`
  - 边界值可选：`INT_MAX + 0 = INT_MAX`、`INT_MIN + 0 = INT_MIN`

- **测试框架**
  - 优先使用 `gtest`。
  - 若环境未配置 gtest，可使用自定义 `test_base.h` 或简单 `assert` 实现。

- **示例测试目标**
  - `CalculatorTest.AddPositiveNumbers`
  - `CalculatorTest.AddNegativeNumbers`
  - `CalculatorTest.AddMixedSignNumbers`
  - `CalculatorTest.AddZeroNumbers`

- **构建与运行**
  - 使用 CMake 构建：
    ```bash
    cmake -S . -B build
    cmake --build build
    ctest --test-dir build
    ```

- **验收标准**
  - 项目可在 C++17 下成功编译。
  - `src/main.cpp` 可正常运行并输出加法结果。
  - `tests/test_calculator.cpp` 全部测试通过。
  - 不引入任何第三方运行时依赖。