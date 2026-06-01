# 技术设计文档

## 1. 系统架构概览

本项目为极简 C++17 加法计算器，采用三层结构：

- **接口层**：`include/calculator.h`  
  对外暴露 `Calculator` 类及 `add` 方法声明。
- **实现层**：`src/calculator.cpp`  
  实现整数加法逻辑。
- **应用层**：`src/main.cpp`  
  演示如何创建 `Calculator` 对象并调用 `add`。
- **测试层**：`tests/test_calculator.cpp`  
  使用 gtest 或自定义 `test_base.h` 对加法功能进行验证。

数据流：

1. 调用方传入两个 `int` 参数 `a` 和 `b`
2. `Calculator::add(a, b)` 执行 `a + b`
3. 返回整数结果给调用方
4. 测试模块验证返回值是否符合预期

## 2. 核心模块清单

- **Calculator 模块**
  - 责任：提供整数加法能力
  - 关键类：`Calculator`
  - 关键函数：
    - `Calculator()`
    - `int add(int a, int b) const`

- **Demo Main 模块**
  - 责任：展示计算器基本使用方式
  - 关键函数：
    - `int main()`

- **Test Calculator 模块**
  - 责任：验证 `Calculator::add` 在正常、负数、零值等场景下的行为
  - 关键测试：
    - 正整数相加
    - 负整数相加
    - 正负整数相加
    - 与零相加

## 3. 关键 API 定义

```cpp
#ifndef CALCULATOR_H
#define CALCULATOR_H

class Calculator {
public:
    Calculator();
    int add(int a, int b) const;
};

#endif // CALCULATOR_H
```

核心函数签名：

```cpp
Calculator::Calculator();
int Calculator::add(int a, int b) const;
```

示例调用：

```cpp
Calculator calculator;
int result = calculator.add(1, 2);
```

预期结果：

```cpp
result == 3
```

## 4. 数据结构与持久化

本项目不需要复杂数据结构和持久化存储。

- 输入数据：
  - `int a`
  - `int b`
- 输出数据：
  - `int result`
- 内部状态：
  - `Calculator` 为无状态类，不保存成员变量
- 持久化：
  - 不涉及文件、数据库或网络存储
- 溢出策略：
  - 使用 C++17 `int` 默认行为
  - 不额外实现溢出检测
  - 测试用例避免依赖有符号整数溢出行为

## 5. 安全与并发设计

- **安全设计**
  - 不使用裸指针
  - 不进行动态内存分配
  - 不访问外部资源
  - 不使用第三方库
  - `Calculator` 无内部状态，避免状态污染
  - 对有符号整数溢出不做额外处理，调用方应保证输入范围合理

- **并发设计**
  - `Calculator` 类无成员变量，为无状态对象
  - `add` 方法声明为 `const`
  - 多线程环境下多个线程可安全调用同一个 `Calculator` 实例的 `add` 方法
  - 不需要互斥锁、原子变量或线程同步机制

## 6. 文件组织

```text
CMakeLists.txt
include/
  calculator.h
src/
  calculator.cpp
  main.cpp
tests/
  test_calculator.cpp
docs/
  technical_design.md
```

文件映射：

- `include/calculator.h`
  - 声明 `Calculator` 类
  - 使用 include guard：`CALCULATOR_H`

- `src/calculator.cpp`
  - 包含 `calculator.h`
  - 实现 `Calculator::Calculator`
  - 实现 `Calculator::add`

- `src/main.cpp`
  - 包含 `calculator.h`
  - 创建 `Calculator` 对象
  - 调用 `add`
  - 使用 `std::cout` 输出演示结果

- `tests/test_calculator.cpp`
  - 包含 `calculator.h`
  - 包含 gtest 头文件或自定义 `test_base.h`
  - 编写 `TEST` 或等价断言测试

- `docs/technical_design.md`
  - 保存本技术设计文档

建议 CMake 目标：

```cmake
cmake_minimum_required(VERSION 3.10)
project(simple_calculator LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

add_library(calculator src/calculator.cpp)
target_include_directories(calculator PUBLIC include)

add_executable(calculator_demo src/main.cpp)
target_link_libraries(calculator_demo PRIVATE calculator)

add_executable(test_calculator tests/test_calculator.cpp)
target_link_libraries(test_calculator PRIVATE calculator)
```

## 7. 测试策略

测试文件：`tests/test_calculator.cpp`

测试范围：

- **正整数相加**
  - 输入：`1, 2`
  - 期望：`3`

- **零值相加**
  - 输入：`0, 0`
  - 期望：`0`

- **正数与零相加**
  - 输入：`5, 0`
  - 期望：`5`

- **负整数相加**
  - 输入：`-2, -3`
  - 期望：`-5`

- **正负整数相加**
  - 输入：`10, -4`
  - 期望：`6`

示例测试结构：

```cpp
#include "calculator.h"
#include "test_base.h"

TEST(CalculatorTest, AddPositiveNumbers) {
    Calculator calculator;
    EXPECT_EQ(3, calculator.add(1, 2));
}

TEST(CalculatorTest, AddNegativeNumbers) {
    Calculator calculator;
    EXPECT_EQ(-5, calculator.add(-2, -3));
}

TEST(CalculatorTest, AddMixedNumbers) {
    Calculator calculator;
    EXPECT_EQ(6, calculator.add(10, -4));
}

TEST(CalculatorTest, AddZero) {
    Calculator calculator;
    EXPECT_EQ(0, calculator.add(0, 0));
}
```

测试执行：

```bash
cmake -S . -B build
cmake --build build
./build/test_calculator
```