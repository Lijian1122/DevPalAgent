# 技术设计文档

## 1. 系统架构概览

本项目为极简 C++17 加法计算器，采用三层结构：

- **接口层**：`include/calculator.h` 暴露 `Calculator` 类及 `add` 方法。
- **实现层**：`src/calculator.cpp` 实现加法逻辑。
- **应用层**：`src/main.cpp` 演示创建 `Calculator` 并调用 `add`。
- **测试层**：`tests/test_calculator.cpp` 验证加法功能正确性。

数据流：

```text
main/test
  -> Calculator::add(int a, int b)
  -> 返回 int 类型加法结果
```

本项目无复杂状态、无外部 I/O 依赖、无持久化存储。

## 2. 核心模块清单

- **Calculator 模块**
  - 责任：提供整数加法能力。
  - 关键类：`Calculator`
  - 关键函数：
    - `Calculator::Calculator()`
    - `Calculator::Calculator(const Calculator& other)`
    - `int Calculator::add(int a, int b) const`

- **Demo 模块**
  - 责任：提供命令行演示入口。
  - 关键函数：
    - `int main()`

- **Test 模块**
  - 责任：验证 `Calculator::add` 在正数、负数、零等场景下的行为。
  - 关键函数：
    - `TEST(CalculatorTest, AddPositiveNumbers)`
    - `TEST(CalculatorTest, AddNegativeNumbers)`
    - `TEST(CalculatorTest, AddWithZero)`
    - `TEST(CalculatorTest, AddMixedSigns)`

## 3. 关键 API 定义

```cpp
#ifndef CALCULATOR_H
#define CALCULATOR_H

class Calculator {
public:
    Calculator();
    Calculator(const Calculator& other);
    Calculator& operator=(const Calculator& other);
    ~Calculator();

    int add(int a, int b) const;
};

#endif // CALCULATOR_H
```

函数签名说明：

```cpp
Calculator::Calculator();
```

- 参数：无
- 返回值：无
- 说明：默认构造计算器对象。

```cpp
Calculator::Calculator(const Calculator& other);
```

- 参数：`const Calculator& other`
- 返回值：无
- 说明：拷贝构造，当前类无成员状态，使用默认语义即可。

```cpp
Calculator& Calculator::operator=(const Calculator& other);
```

- 参数：`const Calculator& other`
- 返回值：`Calculator&`
- 说明：赋值操作，当前类无成员状态，使用默认语义即可。

```cpp
Calculator::~Calculator();
```

- 参数：无
- 返回值：无
- 说明：析构函数，无资源释放需求。

```cpp
int Calculator::add(int a, int b) const;
```

- 参数：
  - `int a`：第一个整数
  - `int b`：第二个整数
- 返回值：`int`
- 说明：返回 `a + b`。

`src/main.cpp` 演示入口：

```cpp
int main();
```

## 4. 数据结构与持久化

### 数据结构

本项目不需要自定义复杂数据结构。

核心数据类型：

```cpp
int a;
int b;
int result;
```

`Calculator` 类设计为无状态类：

```cpp
class Calculator {
public:
    int add(int a, int b) const;
};
```

### 持久化

- 不涉及文件读写。
- 不涉及数据库。
- 不涉及缓存。
- 不保存历史计算记录。
- 每次调用 `add` 直接根据入参计算并返回结果。

### 整数溢出说明

`int add(int a, int b) const` 使用 C++ 内置 `int` 加法。若发生有符号整数溢出，行为遵循 C++ 标准，不在本需求范围内额外处理。

## 5. 安全与并发设计

### 安全设计

- 不使用动态内存分配。
- 不使用裸指针。
- 不接收外部文件路径或网络输入。
- 不使用第三方库。
- 不执行系统命令。
- 接口仅接受两个 `int` 参数，攻击面极小。

### 并发设计

`Calculator` 为无状态类，`add` 方法为 `const`，不修改任何共享数据。

因此：

- 多线程同时调用同一个 `Calculator` 实例的 `add` 是安全的。
- 不需要 `std::mutex`。
- 不需要原子变量。
- 不需要线程池。

示例：

```cpp
const Calculator calculator;
int result = calculator.add(1, 2);
```

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

- **`include/calculator.h`**
  - 声明 `Calculator` 类。
  - 使用 include guard：`CALCULATOR_H`。
  - 暴露 `int add(int a, int b) const`。

- **`src/calculator.cpp`**
  - 包含 `calculator.h`。
  - 实现 `Calculator` 构造、析构、赋值及 `add` 方法。

- **`src/main.cpp`**
  - 演示调用 `Calculator::add`。
  - 使用 `std::cout` 输出示例结果。

- **`tests/test_calculator.cpp`**
  - 使用 gtest 或 `test_base.h`。
  - 覆盖正数、负数、零、混合符号加法。

- **`CMakeLists.txt`**
  - 设置 C++17。
  - 构建静态库或目标 `calculator_lib`。
  - 构建可执行文件 `simple_calculator`。
  - 构建测试目标 `test_calculator`。

推荐 CMake 目标：

```cmake
cmake_minimum_required(VERSION 3.10)
project(simple_calculator)

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

### 单元测试范围

测试目标：`Calculator::add(int a, int b) const`

测试用例：

- **正数相加**
  - 输入：`1, 2`
  - 期望：`3`

- **负数相加**
  - 输入：`-1, -2`
  - 期望：`-3`

- **正负数相加**
  - 输入：`5, -3`
  - 期望：`2`

- **零参与计算**
  - 输入：`0, 7`
  - 期望：`7`

- **两个零相加**
  - 输入：`0, 0`
  - 期望：`0`

### gtest 示例

```cpp
#include "calculator.h"
#include <gtest/gtest.h>

TEST(CalculatorTest, AddPositiveNumbers) {
    Calculator calculator;
    EXPECT_EQ(3, calculator.add(1, 2));
}

TEST(CalculatorTest, AddNegativeNumbers) {
    Calculator calculator;
    EXPECT_EQ(-3, calculator.add(-1, -2));
}

TEST(CalculatorTest, AddMixedSigns) {
    Calculator calculator;
    EXPECT_EQ(2, calculator.add(5, -3));
}

TEST(CalculatorTest, AddWithZero) {
    Calculator calculator;
    EXPECT_EQ(7, calculator.add(0, 7));
}
```

若不使用 gtest，可在 `tests/test_calculator.cpp` 中包含自定义 `test_base.h`，用断言宏实现同等覆盖。