# 技术设计文档

## 1. 系统架构概览

本项目为极简 C++17 加法计算器，采用三层结构：

- **接口层**：`include/calculator.h`  
  对外暴露 `Calculator` 类及 `add` 方法声明。
- **实现层**：`src/calculator.cpp`  
  实现整数加法逻辑。
- **应用/测试层**：
  - `src/main.cpp`：演示如何创建 `Calculator` 并调用 `add`
  - `tests/test_calculator.cpp`：验证加法功能正确性

数据流：

```text
main/test 输入整数 a, b
        ↓
Calculator::add(a, b)
        ↓
返回 a + b
        ↓
main 输出结果 / test 校验结果
```

系统无外部依赖、无持久化存储、无网络通信，核心逻辑保持纯函数式行为，便于测试和复用。

## 2. 核心模块清单

- **Calculator 模块**
  - 责任：提供基础整数加法能力
  - 关键类：`Calculator`
  - 关键函数：
    - `Calculator::Calculator()`
    - `int Calculator::add(int a, int b) const`

- **Demo 应用模块**
  - 责任：演示计算器的基本使用方式
  - 关键文件：`src/main.cpp`
  - 关键函数：
    - `int main()`

- **测试模块**
  - 责任：验证 `Calculator::add` 对正数、负数、零等输入场景的正确性
  - 关键文件：`tests/test_calculator.cpp`
  - 关键测试：
    - 正数相加
    - 负数相加
    - 正负数相加
    - 零参与相加

## 3. 关键 API 定义

### `Calculator`

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

### 构造函数

```cpp
Calculator::Calculator();
```

- 参数：无
- 返回值：无
- 说明：创建无状态计算器对象

### 加法函数

```cpp
int Calculator::add(int a, int b) const;
```

- 参数：
  - `int a`：第一个整数
  - `int b`：第二个整数
- 返回值：
  - `int`：`a + b` 的结果
- 异常：
  - 不主动抛出异常
- 备注：
  - 遵循 C++ `int` 默认溢出语义；本需求不额外处理溢出

### Demo 入口

```cpp
int main();
```

- 参数：无
- 返回值：
  - `0` 表示程序正常结束
- 说明：演示调用 `Calculator::add`

## 4. 数据结构与持久化

### 数据结构

本项目无需复杂数据结构，仅使用 C++17 基础类型：

```cpp
int a;
int b;
int result;
```

`Calculator` 类无成员变量：

```cpp
class Calculator {
public:
    Calculator();
    int add(int a, int b) const;
};
```

设计原因：

- 加法操作无状态
- 避免不必要的内存占用
- 对象可安全复用
- 易于单元测试

### 持久化

本项目不涉及持久化：

- 不读写文件
- 不访问数据库
- 不保存历史计算记录
- 不维护配置文件

如后续扩展历史记录，可增加 `CalculationRecord` 结构并使用 `std::vector<CalculationRecord>` 暂存，或通过 STL 文件流持久化到文本文件。

## 5. 安全与并发设计

### 安全设计

- 不使用裸指针
- 不进行动态内存分配
- 不使用第三方库
- 不涉及系统调用、网络、文件写入
- `Calculator::add` 不修改对象状态，声明为 `const`

整数溢出策略：

- 当前需求仅定义 `int add(int a, int b)`
- 设计遵循 C++17 对 `int` 运算的默认行为
- 测试用例不覆盖超出 `int` 表示范围的输入

### 并发设计

`Calculator` 为无状态类，`add` 方法为 `const` 方法：

```cpp
int add(int a, int b) const;
```

因此具备天然线程安全特性：

- 多线程共享同一个 `Calculator` 实例调用 `add` 不会产生数据竞争
- 不需要 `std::mutex`
- 不需要原子变量
- 不需要线程本地存储

如未来增加历史记录或统计计数，应使用 `std::mutex` 保护共享状态。

## 6. 文件组织

```text
.
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

### 文件职责

- **`include/calculator.h`**
  - 声明 `Calculator` 类
  - 使用 include guard：`CALCULATOR_H`
  - 暴露 `add` API

- **`src/calculator.cpp`**
  - 包含 `calculator.h`
  - 实现 `Calculator` 构造函数
  - 实现 `Calculator::add`

- **`src/main.cpp`**
  - 包含 `<iostream>`
  - 包含 `calculator.h`
  - 创建 `Calculator`
  - 输出示例计算结果

- **`tests/test_calculator.cpp`**
  - 包含 `calculator.h`
  - 使用 gtest 或 `test_base.h`
  - 验证加法结果

- **`CMakeLists.txt`**
  - 设置 C++17
  - 构建 calculator 静态库或对象库
  - 构建 demo 可执行程序
  - 构建测试可执行程序

### CMake 目标建议

```cmake
cmake_minimum_required(VERSION 3.10)
project(simple_calculator LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

add_library(calculator src/calculator.cpp)
target_include_directories(calculator PUBLIC include)

add_executable(simple_calculator src/main.cpp)
target_link_libraries(simple_calculator PRIVATE calculator)

add_executable(test_calculator tests/test_calculator.cpp)
target_link_libraries(test_calculator PRIVATE calculator)
```

## 7. 测试策略

测试框架采用 gtest 或项目内 `custom test_base.h`。由于需求极简，测试重点覆盖输入组合。

### 单元测试范围

- 正数 + 正数

```cpp
Calculator calculator;
EXPECT_EQ(calculator.add(2, 3), 5);
```

- 负数 + 负数

```cpp
EXPECT_EQ(calculator.add(-2, -3), -5);
```

- 正数 + 负数

```cpp
EXPECT_EQ(calculator.add(10, -4), 6);
```

- 零 + 正数

```cpp
EXPECT_EQ(calculator.add(0, 7), 7);
```

- 零 + 零

```cpp
EXPECT_EQ(calculator.add(0, 0), 0);
```

### 测试文件

```text
tests/test_calculator.cpp
```

建议测试用例命名：

```cpp
TEST(CalculatorTest, AddPositiveNumbers)
TEST(CalculatorTest, AddNegativeNumbers)
TEST(CalculatorTest, AddMixedSignNumbers)
TEST(CalculatorTest, AddZero)
```

### 验收标准

- 项目可通过 CMake 配置与构建
- `src/main.cpp` 可正常运行并输出示例结果
- `tests/test_calculator.cpp` 所有测试通过
- `Calculator::add(int a, int b)` 返回值严格等于 `a + b`
- 不引入任何第三方运行时依赖