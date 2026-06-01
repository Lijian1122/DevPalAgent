# 技术设计文档

## 1. 系统架构概览

本项目实现一个极简 C++17 加法计算器，采用三层结构：

- **接口层**：`include/calculator.h`，暴露 `Calculator` 类及 `add` 方法。
- **实现层**：`src/calculator.cpp`，实现整数加法逻辑。
- **应用层**：`src/main.cpp`，演示创建 `Calculator` 对象并调用 `add`。
- **测试层**：`tests/test_calculator.cpp`，验证加法功能正确性。

数据流：

1. 调用方传入两个 `int` 参数 `a`、`b`
2. `Calculator::add(int a, int b)` 执行 `a + b`
3. 返回 `int` 类型结果
4. 主程序打印结果，测试程序断言结果

模块依赖方向：

`main.cpp / test_calculator.cpp` → `calculator.h` → `calculator.cpp`

## 2. 核心模块清单

- **Calculator 模块**
  - 职责：提供基础整数加法能力。
  - 关键类：`Calculator`
  - 关键函数：
    - `Calculator::Calculator()`
    - `Calculator::add(int a, int b) const`

- **Demo 主程序模块**
  - 职责：展示计算器的基本使用方式。
  - 关键函数：
    - `int main()`

- **测试模块**
  - 职责：验证 `Calculator::add` 在正数、负数、零等输入下的行为。
  - 关键函数：
    - `TEST(CalculatorTest, AddPositiveNumbers)`
    - `TEST(CalculatorTest, AddNegativeNumbers)`
    - `TEST(CalculatorTest, AddWithZero)`
    - `TEST(CalculatorTest, AddMixedSigns)`

## 3. 关键 API 定义

```cpp
#ifndef CALCULATOR_H
#define CALCULATOR_H

namespace dev_pal {

class Calculator {
public:
    Calculator();
    explicit Calculator(bool enable_overflow_check);

    int add(int a, int b) const;

private:
    bool enable_overflow_check_;
};

} // namespace dev_pal

#endif // CALCULATOR_H
```

核心函数签名：

```cpp
dev_pal::Calculator::Calculator();

dev_pal::Calculator::Calculator(bool enable_overflow_check);

int dev_pal::Calculator::add(int a, int b) const;
```

接口说明：

- `Calculator()`
  - 默认构造函数。
  - 默认关闭溢出检查，直接返回 `a + b`。

- `Calculator(bool enable_overflow_check)`
  - 参数：
    - `enable_overflow_check`：是否启用整数溢出检查。
  - 当前需求仅要求简单加法，可保留扩展能力。

- `int add(int a, int b) const`
  - 参数：
    - `a`：第一个整数。
    - `b`：第二个整数。
  - 返回：
    - `a + b` 的整数结果。

## 4. 数据结构与持久化

### 数据结构

本项目不需要复杂数据结构，仅使用 C++17 基础类型：

```cpp
int a;
int b;
int result;
bool enable_overflow_check_;
```

### 类成员

```cpp
class Calculator {
private:
    bool enable_overflow_check_;
};
```

### 持久化设计

本项目无持久化需求：

- 不读写数据库
- 不读写配置文件
- 不保存历史计算记录
- 不维护运行时状态

所有计算均为无副作用的同步内存计算。

## 5. 安全与并发设计

### 安全设计

- 使用 C++17 标准库，不引入第三方依赖。
- `Calculator::add` 不分配动态内存，无资源泄漏风险。
- 默认实现直接使用 `int` 加法，与需求保持一致。
- 如启用 `enable_overflow_check_`，可在实现中使用边界判断：

```cpp
if ((b > 0 && a > std::numeric_limits<int>::max() - b) ||
    (b < 0 && a < std::numeric_limits<int>::min() - b)) {
    throw std::overflow_error("integer addition overflow");
}
```

需要包含：

```cpp
#include <limits>
#include <stdexcept>
```

### 并发设计

- `Calculator::add` 声明为 `const`，不修改对象状态。
- `Calculator` 仅包含只读配置成员，适合多线程并发调用。
- 无全局可变状态。
- 无静态缓存。
- 无锁设计即可满足当前需求。

## 6. 文件组织

```text
include/
  calculator.h

src/
  calculator.cpp
  main.cpp

tests/
  test_calculator.cpp
  test_base.h

docs/
  technical_design.md

CMakeLists.txt
```

### 文件职责

- `include/calculator.h`
  - 声明 `dev_pal::Calculator` 类。
  - 使用 include guard：`CALCULATOR_H`。

- `src/calculator.cpp`
  - 实现构造函数和 `Calculator::add`。

- `src/main.cpp`
  - 创建 `Calculator` 实例。
  - 调用 `add(1, 2)`。
  - 使用 `std::cout` 输出结果。

- `tests/test_calculator.cpp`
  - 包含 `calculator.h`。
  - 使用 gtest 或 `test_base.h` 编写单元测试。

- `tests/test_base.h`
  - 可选自定义轻量测试辅助头文件。
  - 如果项目环境未接入 gtest，可提供简单断言宏。

- `docs/technical_design.md`
  - 保存本文档。

- `CMakeLists.txt`
  - 配置 C++17。
  - 构建静态库或对象库 `calculator_lib`。
  - 构建演示程序 `simple_calculator`。
  - 构建测试程序 `test_calculator`。

## 7. 测试策略

### 单元测试范围

测试文件：`tests/test_calculator.cpp`

覆盖场景：

- 正数相加：

```cpp
EXPECT_EQ(calculator.add(1, 2), 3);
```

- 负数相加：

```cpp
EXPECT_EQ(calculator.add(-1, -2), -3);
```

- 正负数相加：

```cpp
EXPECT_EQ(calculator.add(5, -3), 2);
```

- 与零相加：

```cpp
EXPECT_EQ(calculator.add(0, 7), 7);
EXPECT_EQ(calculator.add(7, 0), 7);
```

- 两个零相加：

```cpp
EXPECT_EQ(calculator.add(0, 0), 0);
```

### 测试组织

- 若使用 gtest：
  - 测试入口由 gtest 提供或在测试文件中定义 `main`。
  - CMake 中启用 `enable_testing()` 和 `add_test()`。

- 若使用自定义 `test_base.h`：
  - 定义 `ASSERT_EQ(expected, actual)`。
  - `test_calculator.cpp` 返回非零表示失败。

### 构建验证

建议执行：

```bash
cmake -S . -B build
cmake --build build
ctest --test-dir build
```

验收标准：

- 项目可使用 CMake 成功构建。
- `src/main.cpp` 可运行并输出加法结果。
- `tests/test_calculator.cpp` 所有测试用例通过。
- 实现仅依赖 C++17 STL，无第三方库。