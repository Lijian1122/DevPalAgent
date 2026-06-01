# 技术设计文档

## 1. 系统架构概览

本项目为极简 C++17 加法计算器，采用三层结构：

- **接口层**：`include/calculator.h` 暴露 `Calculator` 类及 `add` 方法。
- **实现层**：`src/calculator.cpp` 实现加法逻辑。
- **应用层/测试层**：
  - `src/main.cpp` 提供命令行演示。
  - `tests/test_calculator.cpp` 验证功能正确性。

数据流：

1. 调用方创建 `Calculator` 对象。
2. 调用 `Calculator::add(int a, int b)`。
3. 方法返回 `a + b` 的整数结果。
4. `main.cpp` 输出演示结果，测试文件断言返回值。

模块依赖方向：

`main.cpp / test_calculator.cpp` → `calculator.h` → `calculator.cpp`

无动态资源、无外部依赖、无持久化存储。

## 2. 核心模块清单

- **Calculator 模块**
  - 责任：提供整数加法能力。
  - 关键类：`Calculator`
  - 关键函数：
    - `Calculator::Calculator()`
    - `Calculator::add(int a, int b) const`

- **Demo 应用模块**
  - 责任：演示 `Calculator` 的基本使用方式。
  - 关键函数：
    - `int main()`

- **测试模块**
  - 责任：验证加法功能在正数、负数、零、混合符号场景下的正确性。
  - 关键文件：
    - `tests/test_calculator.cpp`

## 3. 关键 API 定义

```cpp
// include/calculator.h
#ifndef CALCULATOR_H
#define CALCULATOR_H

class Calculator {
public:
    Calculator();
    explicit Calculator(int initial_value);

    int add(int a, int b) const;

private:
    int initial_value_;
};

#endif // CALCULATOR_H
```

```cpp
// src/calculator.cpp
#include "calculator.h"

Calculator::Calculator()
    : initial_value_(0) {}

Calculator::Calculator(int initial_value)
    : initial_value_(initial_value) {}

int Calculator::add(int a, int b) const {
    return a + b;
}
```

```cpp
// src/main.cpp
#include <iostream>
#include "calculator.h"

int main() {
    Calculator calculator;
    int result = calculator.add(1, 2);
    std::cout << "1 + 2 = " << result << std::endl;
    return 0;
}
```

核心 API 说明：

| API | 参数 | 返回值 | 说明 |
|---|---|---|---|
| `Calculator()` | 无 | 构造对象 | 默认构造函数 |
| `Calculator(int initial_value)` | `initial_value` 初始值 | 构造对象 | 参数化构造函数，满足设计规范 |
| `int add(int a, int b) const` | 两个整数 | `int` | 返回 `a + b` |

## 4. 数据结构与持久化

### 数据结构

- `Calculator`
  - `int initial_value_`
    - 默认值为 `0`
    - 当前需求中不参与加法计算，仅用于满足默认与参数化构造要求，并为后续扩展预留状态。

### 持久化

本项目无持久化需求：

- 不读写文件。
- 不访问数据库。
- 不依赖配置文件。
- 所有计算在内存中完成。
- 对象生命周期由栈对象或 RAII 自动管理。

### 整数范围

`add` 使用 C++ `int` 类型。若发生整数溢出，遵循 C++ 标准中有符号整数溢出的未定义行为。当前需求未要求溢出检测，因此不额外处理。

## 5. 安全与并发设计

### 安全设计

- 不使用裸指针。
- 不分配动态内存。
- 不使用第三方库。
- 无输入解析风险，`add` 仅接收已确定类型的 `int` 参数。
- `Calculator::add` 标记为 `const`，保证调用不修改对象状态。

### 并发设计

- `Calculator::add` 为无副作用计算函数。
- 多线程同时调用同一个 `Calculator` 实例的 `add` 方法是安全的，因为方法不修改共享状态。
- 当前项目不主动创建线程，不需要 `std::mutex`。
- 如未来加入可变状态，应使用 `std::mutex` 保护共享数据。

## 6. 文件组织

```text
include/
  calculator.h              // Calculator 类声明

src/
  calculator.cpp            // Calculator 方法实现
  main.cpp                  // 演示程序入口

tests/
  test_calculator.cpp       // Calculator 单元测试

docs/
  technical_design.md       // 本技术设计文档

CMakeLists.txt              // 顶层 CMake 构建配置
```

建议 CMake 目标：

```cmake
cmake_minimum_required(VERSION 3.10)
project(simple_calculator CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

add_library(calculator_lib src/calculator.cpp)
target_include_directories(calculator_lib PUBLIC include)

add_executable(calculator_demo src/main.cpp)
target_link_libraries(calculator_demo PRIVATE calculator_lib)

enable_testing()
add_executable(test_calculator tests/test_calculator.cpp)
target_link_libraries(test_calculator PRIVATE calculator_lib)
add_test(NAME test_calculator COMMAND test_calculator)
```

测试文件可使用 `gtest` 或项目自定义 `test_base.h`。在无第三方依赖约束下，优先使用 `test_base.h` 或简单断言。

## 7. 测试策略

### 单元测试范围

文件：`tests/test_calculator.cpp`

测试用例：

- `add(1, 2)` 返回 `3`
- `add(0, 0)` 返回 `0`
- `add(-1, -2)` 返回 `-3`
- `add(-1, 2)` 返回 `1`
- `add(100, 200)` 返回 `300`

### 示例测试代码

```cpp
#include <cassert>
#include "calculator.h"

int main() {
    Calculator calculator;

    assert(calculator.add(1, 2) == 3);
    assert(calculator.add(0, 0) == 0);
    assert(calculator.add(-1, -2) == -3);
    assert(calculator.add(-1, 2) == 1);
    assert(calculator.add(100, 200) == 300);

    return 0;
}
```

### 测试执行

```bash
cmake -S . -B build
cmake --build build
ctest --test-dir build
```

验收标准：

- 项目可在 C++17 编译器下成功构建。
- `calculator_demo` 可输出加法结果。
- `test_calculator` 全部断言通过。
- 无第三方库依赖。