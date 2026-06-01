# 技术设计文档

## 1. 系统架构概览

本项目实现一个基于 C++17 STL 的极简整数加法计算器，采用三层结构：

- **接口层**：`include/calculator.h`，声明 `Calculator` 类及 `add` 方法。
- **实现层**：`src/calculator.cpp`，实现加法逻辑。
- **应用层**：`src/main.cpp`，演示创建计算器并调用加法功能。
- **测试层**：`tests/test_calculator.cpp`，使用 gtest 或自定义 `test_base.h` 验证功能正确性。

数据流：

1. 用户或测试代码传入两个 `int` 参数 `a`、`b`。
2. `Calculator::add(int a, int b)` 执行 `a + b`。
3. 返回整数结果给调用方。
4. 测试模块断言返回值是否符合预期。

## 2. 核心模块清单

- **Calculator 模块**
  - 责任：提供整数加法能力。
  - 关键类：`Calculator`
  - 关键函数：`int add(int a, int b) const`

- **Demo 应用模块**
  - 责任：演示计算器调用方式。
  - 关键函数：`int main()`
  - 行为：实例化 `Calculator`，调用 `add`，输出结果。

- **测试模块**
  - 责任：验证 `Calculator::add` 的正确性。
  - 关键测试：正数相加、负数相加、正负数相加、零值相加。

## 3. 关键 API 定义

```cpp
// include/calculator.h
#ifndef CALCULATOR_H
#define CALCULATOR_H

namespace simple_calculator {

class Calculator {
public:
    Calculator();
    Calculator(const Calculator& other) = default;
    Calculator& operator=(const Calculator& other) = default;
    ~Calculator() = default;

    int add(int a, int b) const;
};

} // namespace simple_calculator

#endif // CALCULATOR_H
```

```cpp
// src/calculator.cpp
#include "calculator.h"

namespace simple_calculator {

Calculator::Calculator() = default;

int Calculator::add(int a, int b) const {
    return a + b;
}

} // namespace simple_calculator
```

```cpp
// src/main.cpp
#include <iostream>
#include "calculator.h"

int main() {
    simple_calculator::Calculator calculator;
    int result = calculator.add(1, 2);
    std::cout << "1 + 2 = " << result << std::endl;
    return 0;
}
```

## 4. 数据结构与持久化

- **核心数据结构**
  - 不需要自定义复杂数据结构。
  - 输入参数使用 C++ 基础类型 `int`。
  - 返回值使用 `int`。

- **对象状态**
  - `Calculator` 为无状态类。
  - 不保存历史计算结果。
  - 不维护成员变量。

- **持久化**
  - 本项目无持久化需求。
  - 不读写数据库、配置文件或业务数据文件。

- **整数范围**
  - 使用标准 C++17 `int`。
  - 若发生整数溢出，行为遵循 C++ 标准整数运算规则；当前需求不额外处理溢出。

## 5. 安全与并发设计

- **安全设计**
  - 不使用裸指针。
  - 不进行动态内存分配。
  - 不访问外部资源。
  - 不引入第三方库。
  - 接口参数为值类型，避免悬空引用风险。

- **异常设计**
  - `Calculator::add` 不主动抛出异常。
  - 无文件、网络、内存资源申请逻辑，异常面极小。

- **并发设计**
  - `Calculator` 无内部状态。
  - `add` 方法声明为 `const`。
  - 多线程共享同一个 `Calculator` 实例调用 `add` 是线程安全的。
  - 不需要互斥锁、原子变量或线程同步机制。

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

- `include/calculator.h`
  - 声明 `simple_calculator::Calculator` 类。
  - 使用 include guard：`CALCULATOR_H`。

- `src/calculator.cpp`
  - 实现 `Calculator` 构造函数和 `add` 方法。

- `src/main.cpp`
  - 提供命令行演示入口。
  - 输出简单加法结果。

- `tests/test_calculator.cpp`
  - 包含加法功能单元测试。

- `CMakeLists.txt`
  - 配置 C++17 标准。
  - 构建静态库或对象库 `calculator_lib`。
  - 构建演示程序 `simple_calculator`。
  - 构建测试程序 `test_calculator`。

推荐 CMake 目标：

```cmake
cmake_minimum_required(VERSION 3.10)
project(simple_calculator LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

add_library(calculator_lib src/calculator.cpp)
target_include_directories(calculator_lib PUBLIC include)

add_executable(simple_calculator src/main.cpp)
target_link_libraries(simple_calculator PRIVATE calculator_lib)

add_executable(test_calculator tests/test_calculator.cpp)
target_link_libraries(test_calculator PRIVATE calculator_lib)
```

## 7. 测试策略

- **测试框架**
  - 优先使用 gtest。
  - 若环境未提供 gtest，则使用自定义 `test_base.h` 或简单断言方式。

- **测试文件**
  - `tests/test_calculator.cpp`

- **测试用例**
  - `add(1, 2)` 返回 `3`
  - `add(0, 0)` 返回 `0`
  - `add(-1, -2)` 返回 `-3`
  - `add(-5, 3)` 返回 `-2`
  - `add(100, 200)` 返回 `300`

- **示例测试代码**

```cpp
#include "calculator.h"
#include <cassert>
#include <iostream>

int main() {
    simple_calculator::Calculator calculator;

    assert(calculator.add(1, 2) == 3);
    assert(calculator.add(0, 0) == 0);
    assert(calculator.add(-1, -2) == -3);
    assert(calculator.add(-5, 3) == -2);
    assert(calculator.add(100, 200) == 300);

    std::cout << "All calculator tests passed." << std::endl;
    return 0;
}
```

- **通过标准**
  - 所有单元测试通过。
  - `simple_calculator` 可正常编译运行。
  - 代码仅依赖 C++17 标准库。
  - 头文件、源文件、测试文件路径符合需求约束。