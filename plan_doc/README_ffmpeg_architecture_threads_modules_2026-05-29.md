# FFmpeg 基本架构：线程模型与模块模型详解

> **日期**: 2026-05-29  
> **主题**: FFmpeg 架构、线程模型、模块模型、数据流、工程理解  
> **适用场景**: 音视频工程入门、FFmpeg 源码阅读、面试准备、Agent/多媒体项目架构参考

---

## 目录

1. [一句话理解 FFmpeg](#1-一句话理解-ffmpeg)
2. [整体架构总览](#2-整体架构总览)
3. [核心模块模型](#3-核心模块模型)
4. [典型处理链路](#4-典型处理链路)
5. [线程模型总览](#5-线程模型总览)
6. [转码命令中的线程协作](#6-转码命令中的线程协作)
7. [解码线程模型](#7-解码线程模型)
8. [编码线程模型](#8-编码线程模型)
9. [FilterGraph 线程模型](#9-filtergraph-线程模型)
10. [Mux/Demux 与 I/O 线程关系](#10-muxdemux-与-io-线程关系)
11. [FFmpeg CLI 的任务调度模型](#11-ffmpeg-cli-的任务调度模型)
12. [模块之间的数据结构关系](#12-模块之间的数据结构关系)
13. [常见命令背后的执行流程](#13-常见命令背后的执行流程)
14. [性能调优视角](#14-性能调优视角)
15. [源码阅读路线](#15-源码阅读路线)
16. [源码级端到端调用链](#16-源码级端到端调用链)
17. [队列、缓冲与背压模型](#17-队列缓冲与背压模型)
18. [线程安全、生命周期与引用计数](#18-线程安全生命周期与引用计数)
19. [时间戳、同步与音视频对齐](#19-时间戳同步与音视频对齐)
20. [多输入、多输出与复杂 FilterGraph](#20-多输入多输出与复杂-filtergraph)
21. [实战排障与性能分析清单](#21-实战排障与性能分析清单)
22. [面试总结版](#22-面试总结版)
23. [总结](#23-总结)

---

## 1. 一句话理解 FFmpeg

FFmpeg 是一个完整的音视频处理框架，它把音视频处理拆成几类核心问题：

```text
输入读取 -> 解封装 -> 解码 -> 过滤处理 -> 编码 -> 封装 -> 输出写入
```

对应到模块就是：

```text
AVFormat  ->  AVCodec  ->  AVFilter  ->  AVCodec  ->  AVFormat
解封装        解码          滤镜          编码          封装
```

从工程角度看，FFmpeg 不是一个单纯的播放器、转码器或编解码库，而是一套完整的媒体处理基础设施。

---

## 2. 整体架构总览

FFmpeg 可以分成三层：

```text
┌──────────────────────────────────────────────┐
│               应用层 / 工具层                 │
│ ffmpeg / ffplay / ffprobe                    │
└──────────────────────────────────────────────┘
                    │
┌──────────────────────────────────────────────┐
│              框架层 / 媒体处理层              │
│ libavformat / libavcodec / libavfilter       │
│ libavutil / libswscale / libswresample       │
└──────────────────────────────────────────────┘
                    │
┌──────────────────────────────────────────────┐
│              编解码器 / 协议 / 硬件层          │
│ H.264 / H.265 / AAC / MP4 / RTMP / CUDA 等    │
└──────────────────────────────────────────────┘
```

### 2.1 工具层

| 工具 | 作用 |
|---|---|
| ffmpeg | 转码、剪辑、过滤、推流、录制，是最常用的命令行工具 |
| ffplay | 简易播放器，用于播放和调试音视频 |
| ffprobe | 媒体信息分析工具，用于查看封装、流、帧、编码参数 |

### 2.2 库层

| 库 | 作用 |
|---|---|
| libavformat | 封装、解封装、协议 I/O，比如 MP4、FLV、MKV、RTMP、HLS |
| libavcodec | 音视频编解码，比如 H.264、HEVC、AAC、Opus |
| libavfilter | 滤镜图，比如 scale、crop、overlay、aresample、volume |
| libavutil | 基础工具库，比如 AVFrame、AVPacket、内存、时间戳、日志、字典 |
| libswscale | 视频像素格式转换和缩放 |
| libswresample | 音频采样率、声道布局、采样格式转换 |
| libavdevice | 摄像头、麦克风、屏幕采集等设备输入输出 |

---

## 3. 核心模块模型

FFmpeg 的模块模型本质上是“插件注册 + 上下文对象 + 数据包/帧流转”。

### 3.1 AVFormat：封装与解封装模块

AVFormat 处理的是“容器格式”和“协议 I/O”。

常见容器格式：

```text
MP4 / FLV / MKV / TS / AVI / MOV / WAV
```

常见协议：

```text
file / http / https / rtmp / rtsp / udp / tcp / hls
```

核心职责：

1. 打开输入或输出 URL。
2. 识别容器格式。
3. 读取媒体流信息。
4. 从容器中读出压缩数据包 AVPacket。
5. 把编码后的 AVPacket 写入目标容器。

核心对象：

| 对象 | 含义 |
|---|---|
| AVFormatContext | 输入或输出容器上下文 |
| AVInputFormat | 输入格式实现 |
| AVOutputFormat | 输出格式实现 |
| AVStream | 容器中的一条媒体流 |
| AVIOContext | I/O 抽象层 |

### 3.2 AVCodec：编解码模块

AVCodec 处理的是“压缩数据”和“原始帧”之间的转换。

```text
解码：AVPacket -> AVFrame
编码：AVFrame  -> AVPacket
```

核心对象：

| 对象 | 含义 |
|---|---|
| AVCodec | 编码器或解码器实现 |
| AVCodecContext | 编解码上下文，保存参数和运行状态 |
| AVPacket | 压缩后的数据包 |
| AVFrame | 解码后的音视频原始帧 |

### 3.3 AVFilter：滤镜模块

AVFilter 处理的是“原始帧级别”的媒体加工。

视频滤镜示例：

```text
scale / crop / overlay / fps / transpose / drawtext
```

音频滤镜示例：

```text
volume / aresample / atempo / anull / amix
```

核心对象：

| 对象 | 含义 |
|---|---|
| AVFilterGraph | 滤镜图 |
| AVFilterContext | 单个滤镜节点上下文 |
| AVFilterLink | 滤镜节点之间的连接 |
| buffersrc | 滤镜图输入节点 |
| buffersink | 滤镜图输出节点 |

滤镜图可以理解为一张 DAG：

```text
输入帧 -> scale -> fps -> overlay -> 输出帧
```

### 3.4 AVUtil：基础设施模块

AVUtil 是整个 FFmpeg 的公共基础层，提供：

- 内存分配。
- 日志系统。
- 字典参数。
- 时间戳计算。
- 像素格式定义。
- 采样格式定义。
- AVFrame / AVPacket 的基础生命周期。

### 3.5 swscale 与 swresample

这两个库常被滤镜或应用层使用。

| 库 | 作用 |
|---|---|
| libswscale | 视频缩放、像素格式转换，例如 YUV420P 转 RGB24 |
| libswresample | 音频重采样，例如 44100Hz 转 48000Hz，stereo 转 mono |

### 3.6 模块注册与插件化机制

FFmpeg 的扩展能力来自大量格式、协议、编解码器、滤镜的注册表。

可以理解为：

```text
编译期：选择启用哪些 demuxer / muxer / codec / filter / protocol
运行期：根据输入、参数、探测结果，从注册表中选择具体实现
```

典型注册对象：

| 类型 | 示例 | 选择时机 |
|---|---|---|
| AVInputFormat | mov, matroska, flv, mpegts | 打开输入、探测容器时 |
| AVOutputFormat | mp4, flv, hls, matroska | 创建输出上下文时 |
| AVCodec | h264, hevc, aac, libx264 | 打开解码器或编码器时 |
| AVFilter | scale, overlay, fps, aresample | 解析 filter graph 时 |
| URLProtocol | file, http, tcp, udp, rtmp | 打开 URL 时 |

这也是为什么 FFmpeg 命令里的参数大多不是硬编码逻辑，而是在运行时映射到具体模块：

```bash
-f flv       -> 选择 FLV muxer 或 demuxer
-c:v libx264 -> 选择 libx264 encoder
-vf scale    -> 选择 scale video filter
-i http://   -> 选择 http protocol
```

### 3.7 上下文对象是模块边界

FFmpeg 很少直接把全局变量暴露给用户，而是用 context 保存状态。

```text
AVFormatContext：一次输入/输出容器会话
AVCodecContext：一次编解码器会话
AVFilterGraph：一张滤镜图会话
AVIOContext：一次 I/O 会话
SwsContext：一次视频格式转换会话
SwrContext：一次音频重采样会话
```

这种设计的好处：

1. 多个输入文件可以各有自己的 AVFormatContext。
2. 多路视频流可以各有自己的 AVCodecContext。
3. 多个输出可以各有自己的 AVFormatContext。
4. 一张复杂滤镜图可以独立维护节点状态。
5. 状态隔离后，才有可能在不同流、不同任务之间做并发。

### 3.8 模块边界上的数据所有权

FFmpeg 的模块边界不是简单传裸指针，而是围绕 AVPacket / AVFrame 的引用、拷贝和释放。

```text
Demuxer 产生 AVPacket
Decoder 消费 AVPacket，产生 AVFrame
FilterGraph 消费 AVFrame，产生新的 AVFrame 或引用同一块数据
Encoder 消费 AVFrame，产生 AVPacket
Muxer 消费 AVPacket
```

重点是：

- AVPacket / AVFrame 本身是结构体壳。
- 真正的大块媒体数据通常挂在 AVBufferRef 上。
- 引用计数允许模块之间零拷贝传递。
- 一旦涉及跨线程，引用计数和生命周期就变得非常关键。

---

## 4. 典型处理链路

### 4.1 解封装 + 解码

```text
输入文件 input.mp4
    │
    ▼
avformat_open_input
    │
    ▼
avformat_find_stream_info
    │
    ▼
av_read_frame
    │  输出 AVPacket
    ▼
avcodec_send_packet
    │
    ▼
avcodec_receive_frame
       输出 AVFrame
```

### 4.2 编码 + 封装

```text
输入 AVFrame
    │
    ▼
avcodec_send_frame
    │
    ▼
avcodec_receive_packet
    │  输出 AVPacket
    ▼
av_interleaved_write_frame
    │
    ▼
输出文件 output.mp4
```

### 4.3 完整转码

```text
input.mp4
  │
  ▼
Demuxer 解封装
  │ AVPacket
  ▼
Decoder 解码
  │ AVFrame
  ▼
FilterGraph 滤镜处理
  │ AVFrame
  ▼
Encoder 编码
  │ AVPacket
  ▼
Muxer 封装
  │
  ▼
output.mp4
```

### 4.4 带状态机的处理链路

实际 FFmpeg 处理不是每读一个 packet 就立刻得到一个 frame，也不是每送一个 frame 就立刻得到一个 packet。

更准确的模型是 send/receive 状态机：

```text
Demuxer
  └─ av_read_frame()
       └─ 得到 AVPacket
            └─ avcodec_send_packet(decoder)
                 ├─ 可能返回 EAGAIN：需要先 receive frame
                 ├─ 可能缓存 packet：暂时没有 frame 输出
                 └─ 可能触发解码线程工作

Decoder
  └─ avcodec_receive_frame()
       ├─ 得到 AVFrame
       ├─ 返回 EAGAIN：需要继续 send packet
       └─ 返回 EOF：解码器已 flush 完成
```

编码端类似：

```text
FilterGraph 输出 AVFrame
  └─ avcodec_send_frame(encoder)
       ├─ 可能进入编码器缓存
       ├─ 可能触发 lookahead / B-frame 重排
       └─ 可能暂时没有 packet 输出

Encoder
  └─ avcodec_receive_packet()
       ├─ 得到 AVPacket
       ├─ 返回 EAGAIN：需要继续 send frame
       └─ 返回 EOF：编码器已 flush 完成
```

所以完整链路更接近：

```text
while 输入未结束:
    读 packet
    send packet 到 decoder
    while decoder 能吐 frame:
        frame 送入 filter
        while filter 能吐 filtered_frame:
            send frame 到 encoder
            while encoder 能吐 packet:
                写 packet 到 muxer

flush decoder
flush filter
flush encoder
写 trailer
```

这解释了几个常见现象：

1. 有些命令刚开始没有输出，因为解码器、滤镜或编码器在缓存帧。
2. B 帧编码需要重排，输出 packet 的顺序可能滞后于输入 frame。
3. EOF 时必须 flush，否则最后几帧可能丢失。
4. 低延迟场景要减少内部缓存、B 帧和 lookahead。

---

## 5. 线程模型总览

FFmpeg 的线程模型不是单一模型，而是多层线程模型叠加：

```text
┌──────────────────────────────────────────┐
│ ffmpeg CLI 调度层                         │
│ 输入读取、输出写入、转码任务调度            │
└──────────────────────────────────────────┘
                    │
┌──────────────────────────────────────────┐
│ 编解码线程层                              │
│ frame threading / slice threading         │
└──────────────────────────────────────────┘
                    │
┌──────────────────────────────────────────┐
│ FilterGraph 线程层                        │
│ 滤镜图内部并行、滤镜节点执行               │
└──────────────────────────────────────────┘
                    │
┌──────────────────────────────────────────┐
│ I/O 与协议层                              │
│ 网络读写、文件读写、缓冲                   │
└──────────────────────────────────────────┘
```

可以概括为：

1. FFmpeg CLI 负责整体转码任务调度。
2. 编码器和解码器内部可以开线程。
3. FilterGraph 内部可以并行执行。
4. I/O 通常由主处理链路驱动，但网络协议和设备输入可能引入缓冲或异步行为。
5. 多输入、多输出、多流场景下，调度复杂度会明显上升。

### 5.1 三类线程不要混淆

| 线程类型 | 谁创建 | 作用 | 用户参数 |
|---|---|---|---|
| CLI 调度线程 | ffmpeg 工具层 | 驱动输入、输出、转码任务 | 通常不直接暴露 |
| Codec worker 线程 | libavcodec 或外部 codec 库 | 解码、编码内部并行 | -threads |
| Filter worker 线程 | libavfilter | 滤镜图执行并行 | -filter_threads / -filter_complex_threads |
| 外部库线程 | libx264、libx265、硬件 SDK | 编码器私有并行 | codec 私有参数 |

很多性能问题来自把这些线程混在一起理解。例如：

```bash
ffmpeg -threads 8 -filter_threads 8 -filter_complex_threads 8 ...
```

这不代表总共只有 8 个线程，而可能代表：

```text
解码器线程 + 编码器线程 + 滤镜线程 + 外部库线程 + 主调度线程 + I/O 阻塞线程
```

### 5.2 并行粒度

FFmpeg 常见并行粒度：

| 粒度 | 示例 | 特点 |
|---|---|---|
| 文件级 | 多个 ffmpeg 进程并行处理多个文件 | 最简单、隔离性最好 |
| 流级 | 视频流和音频流各自处理 | 需要最终 mux 同步 |
| 帧级 | frame threading | 吞吐高，延迟更高 |
| slice/tile 级 | slice threading、tile 编码 | 单帧内部并行 |
| 滤镜节点级 | overlay 两个输入链可部分并行 | 受图拓扑限制 |
| SIMD 级 | 像素处理、DCT、运动估计 | 由底层实现控制 |

### 5.3 线程模型的核心约束

FFmpeg 不能随意把所有阶段完全并行化，主要受这些约束影响：

1. 解码依赖：P/B 帧依赖参考帧。
2. 显示顺序：PTS 顺序和 DTS 顺序可能不同。
3. 滤镜依赖：fps、overlay、trim、concat 等滤镜需要缓存和对齐。
4. 封装约束：muxer 需要按时间戳交错写入。
5. 内存约束：帧数据很大，多线程会扩大缓冲占用。
6. I/O 约束：网络和磁盘不一定跟得上编码速度。

---

## 6. 转码命令中的线程协作

以命令为例：

```bash
ffmpeg -i input.mp4 -vf scale=1280:720 -c:v libx264 -c:a aac output.mp4
```

逻辑执行链路：

```text
主线程
  │
  ├─ 打开输入文件
  ├─ 分析流信息
  ├─ 创建解码器
  ├─ 创建 FilterGraph
  ├─ 创建编码器
  ├─ 创建输出文件
  │
  └─ 进入转码循环
        │
        ├─ av_read_frame 读取 AVPacket
        ├─ 送入对应 Decoder
        ├─ Decoder 内部可能多线程解码
        ├─ 输出 AVFrame
        ├─ 送入 FilterGraph
        ├─ FilterGraph 可能并行处理
        ├─ 输出处理后的 AVFrame
        ├─ 送入 Encoder
        ├─ Encoder 内部可能多线程编码
        ├─ 输出 AVPacket
        └─ Muxer 写入 output.mp4
```

从用户视角看是一条命令；从运行时看，是主调度循环驱动多个模块，每个模块内部根据参数和能力决定是否并行。

---

## 7. 解码线程模型

解码线程主要有两种：

```text
Frame Threading：按帧并行
Slice Threading：按片并行
```

### 7.1 Frame Threading

Frame threading 是按帧级别并行。

```text
Thread 1 解码 Frame N
Thread 2 解码 Frame N+1
Thread 3 解码 Frame N+2
```

优点：

- 并行度较高。
- 对多核 CPU 利用较好。
- 常用于 H.264/H.265 等复杂视频解码。

缺点：

- 会增加解码延迟。
- 对帧间依赖敏感。
- B 帧、参考帧越复杂，调度越复杂。

### 7.2 Slice Threading

Slice threading 是把一帧拆成多个 slice 并行处理。

```text
Frame N
  ├─ Slice 1 -> Thread 1
  ├─ Slice 2 -> Thread 2
  └─ Slice 3 -> Thread 3
```

优点：

- 单帧内部并行。
- 延迟比 frame threading 低。

缺点：

- 依赖码流本身是否有 slice 切分。
- 并行度通常不如 frame threading 稳定。
- 压缩效率和 slice 划分相关。

### 7.3 解码线程参数

常见参数：

```bash
-threads N
```

含义：

- 控制编解码器使用的线程数。
- N 为 0 时通常表示自动选择。
- 实际是否生效取决于具体 codec 实现。

示例：

```bash
ffmpeg -threads 8 -i input.mp4 output.mp4
```

注意：

- 并不是所有解码器都支持多线程。
- 支持多线程也不代表一定线性加速。
- 线程太多可能带来调度开销和缓存压力。

### 7.4 解码线程内部的输入输出关系

解码器表面 API 是：

```text
avcodec_send_packet()
avcodec_receive_frame()
```

但内部通常包含：

```text
Packet Queue -> Parser -> Decode Context -> Worker Threads -> Frame Reorder Buffer -> Output Frame
```

更细一点：

```text
AVPacket
  │
  ▼
Parser / bitstream reader
  │
  ▼
Entropy decode / motion compensation / inverse transform
  │
  ├─ worker thread 1
  ├─ worker thread 2
  └─ worker thread 3
  │
  ▼
Decoded picture buffer
  │
  ▼
Reorder by PTS
  │
  ▼
AVFrame
```

其中 Decoded Picture Buffer 很关键，它保存参考帧，解决 P/B 帧依赖。

### 7.5 DTS、PTS 与解码重排

视频编码中常见三种顺序：

| 顺序 | 含义 |
|---|---|
| 文件存储顺序 | packet 在容器里的顺序 |
| 解码顺序 DTS | 解码器必须按这个顺序处理 |
| 显示顺序 PTS | 用户最终看到的帧顺序 |

例如 GOP：

```text
显示顺序：I0 B1 B2 P3
解码顺序：I0 P3 B1 B2
```

这意味着：

1. demuxer 读出的 packet 顺序通常更接近 DTS。
2. decoder 输出 frame 时要按 PTS 显示顺序重排。
3. frame threading 会进一步增加内部缓存和延迟。
4. 直播低延迟场景通常要减少 B 帧。

### 7.6 Flush 解码器

输入结束后还要 flush 解码器：

```text
avcodec_send_packet(decoder, NULL)
while avcodec_receive_frame(decoder) 能拿到 frame:
    继续送 filter / encoder
```

原因是解码器内部可能还有：

- 尚未输出的 B 帧。
- frame threading worker 正在处理的帧。
- reorder buffer 中等待输出的帧。
- parser 缓存的残余数据。

---

## 8. 编码线程模型

编码器的线程模型与具体编码器强相关。

### 8.1 libx264 编码线程

libx264 常见并行方式包括：

1. 帧级并行。
2. slice 并行。
3. lookahead 线程。
4. rate control 相关内部调度。

典型命令：

```bash
ffmpeg -i input.mp4 -c:v libx264 -threads 8 output.mp4
```

### 8.2 编码并行的影响

编码并行会影响：

| 影响项 | 说明 |
|---|---|
| 吞吐 | 线程越多通常越快，但不一定线性提升 |
| 延迟 | 帧级并行和 lookahead 会增加延迟 |
| 码率控制 | 多线程可能影响码率分配细节 |
| 压缩效率 | 某些并行方式可能略微影响压缩效率 |
| 内存占用 | 更多线程意味着更多缓冲和状态 |

### 8.3 低延迟编码场景

低延迟场景通常需要减少帧缓存和前瞻：

```bash
ffmpeg -i input.mp4 -c:v libx264 -preset veryfast -tune zerolatency output.mp4
```

`tune=zerolatency` 通常会减少 B 帧、lookahead 等会增加延迟的机制。

### 8.4 编码器内部流水线

编码器表面 API 是：

```text
avcodec_send_frame()
avcodec_receive_packet()
```

内部更接近：

```text
Input Frame Queue
  │
  ▼
Lookahead / Scene Cut / B-frame Decision
  │
  ▼
Frame Reorder
  │
  ▼
Motion Estimation / Mode Decision / Transform / Quant
  │
  ├─ worker thread 1
  ├─ worker thread 2
  └─ worker thread 3
  │
  ▼
Entropy Coding
  │
  ▼
Rate Control
  │
  ▼
AVPacket
```

编码器为了压缩率，通常会“看未来帧”：

```text
Frame N 到达时，不一定立刻输出 Packet N
编码器可能等待 N+1、N+2、N+3 用来做 B 帧决策和码率控制
```

这就是为什么高压缩率编码会增加延迟。

### 8.5 x264/x265 常见线程来源

使用 libx264/libx265 时，线程不只来自 FFmpeg 的 `-threads`，还来自编码器内部策略。

| 线程来源 | 说明 |
|---|---|
| frame threads | 多帧并行编码 |
| slice threads | 单帧多 slice 并行 |
| lookahead thread | 提前分析未来帧 |
| worker pool | 运动估计、变换、量化等内部任务 |

低延迟场景通常希望：

```text
减少 B 帧
减少 lookahead
降低 reference frame 数量
使用更快 preset
控制 VBV buffer
```

### 8.6 编码参数的工程取舍

| 目标 | 常见方向 | 代价 |
|---|---|---|
| 更快 | preset 更快、线程更多、硬编 | 压缩率下降或画质下降 |
| 更小文件 | preset 更慢、CRF 更低质量损失更小 | CPU 更高、耗时更长 |
| 更低延迟 | zerolatency、少 B 帧、低 buffer | 压缩效率下降 |
| 更稳定码率 | CBR/VBV | 复杂场景画质波动 |
| 更高画质 | CRF 调低、慢 preset | 文件更大或速度更慢 |

---

## 9. FilterGraph 线程模型

FilterGraph 是 FFmpeg 中非常重要的模块，因为它处理的是原始帧加工。

### 9.1 滤镜图模型

简单滤镜：

```bash
-vf scale=1280:720
```

复杂滤镜：

```bash
-filter_complex "[0:v]scale=1280:720[v0];[v0]fps=30[out]"
```

抽象成图：

```text
Input -> scale -> fps -> Output
```

更复杂的图：

```text
Input A -> scale ─┐
                  ├-> overlay -> Output
Input B -> scale ─┘
```

### 9.2 滤镜图并行

FilterGraph 的并行主要来自：

1. 不同滤镜链之间的并行。
2. 单个滤镜内部的并行。
3. FFmpeg filter threading 对滤镜执行的调度。

相关参数：

```bash
-filter_threads N
-filter_complex_threads N
```

含义：

| 参数 | 说明 |
|---|---|
| -filter_threads | 设置简单滤镜图线程数 |
| -filter_complex_threads | 设置复杂滤镜图线程数 |

示例：

```bash
ffmpeg -i input.mp4 -filter_threads 4 -vf scale=1280:720 output.mp4
```

### 9.3 FilterGraph 的工程特点

FilterGraph 的核心特点：

- 它是基于帧流动的 DAG。
- 每个节点可以消费和产生帧。
- 节点之间通过 link 连接。
- 某些滤镜需要缓存多帧，比如 fps、setpts、overlay、trim。
- 音频滤镜和视频滤镜的数据节奏不同。

所以 FilterGraph 的线程调度不只是“开几个线程”这么简单，还要考虑帧依赖、时间戳、缓存和图拓扑。

### 9.4 FilterGraph 的拉取模型

FilterGraph 很多时候不是简单 push 模型，而是带有 request/pull 语义。

可以理解为：

```text
应用层向 buffersink 要一帧
  │
  ▼
buffersink 发现没有可输出帧
  │
  ▼
向上游 filter 请求帧
  │
  ▼
上游继续向更上游请求帧
  │
  ▼
buffersrc 提供输入帧
  │
  ▼
中间 filter 逐级处理
  │
  ▼
buffersink 返回输出帧
```

这意味着复杂滤镜图里，某个节点卡住会影响整张图。

### 9.5 多输入滤镜的同步问题

以 overlay 为例：

```text
main video  ─────┐
                 ├─ overlay -> output
logo/video  ─────┘
```

overlay 需要同时考虑两个输入的时间戳：

```text
main frame pts = 10.000s
logo frame pts = 10.000s
才能合成这一时刻的输出帧
```

如果一个输入慢，另一个输入就可能被缓存。

典型问题：

1. 一个输入先结束，overlay 如何处理后续主画面。
2. 两路输入 time_base 不同，需要统一换算。
3. 两路输入帧率不同，需要选择相近时间戳帧。
4. 缓存太多会增加内存，缓存太少会丢帧或阻塞。

### 9.6 音频滤镜与视频滤镜差异

视频通常以“帧”为单位：

```text
一帧 1920x1080 YUV420P
```

音频通常以“样本块”为单位：

```text
一帧音频可能包含 1024 samples
```

音频滤镜常见问题：

| 问题 | 示例 |
|---|---|
| 样本数不固定 | AAC 常见 1024 samples，重采样后可能变化 |
| 声道布局变化 | stereo -> mono |
| 采样格式变化 | s16 -> fltp |
| 采样率变化 | 44100 -> 48000 |
| 时间戳累积误差 | 长音频中可能出现 drift |

因此音视频同步不能只看“第几帧”，必须看 PTS 和 time_base。

---

## 10. Mux/Demux 与 I/O 线程关系

### 10.1 Demuxer 解封装

Demuxer 的职责是从输入容器中读出 AVPacket。

```text
文件 / 网络输入
    │
    ▼
AVIOContext
    │
    ▼
Demuxer
    │
    ▼
AVPacket
```

通常情况下，`av_read_frame()` 由主转码循环调用。它本身不一定创建独立线程，但底层协议可能有缓冲、阻塞读、网络超时等行为。

### 10.2 Muxer 封装

Muxer 的职责是把编码后的 AVPacket 写入输出容器。

```text
AVPacket
    │
    ▼
Muxer
    │
    ▼
AVIOContext
    │
    ▼
文件 / 网络输出
```

封装时要处理：

- 包交错写入。
- 时间戳排序。
- 容器头和尾。
- 网络输出阻塞。
- 写入失败和重试。

### 10.3 为什么 I/O 经常成为瓶颈

I/O 可能成为瓶颈的原因：

1. 网络直播流不稳定。
2. 磁盘吞吐不足。
3. 输出协议有阻塞。
4. 多路输入输出竞争资源。
5. 容器需要按时间戳交错写入，不能完全自由并行。

### 10.4 Demuxer 的探测流程

打开输入时通常不是直接知道格式，而是探测：

```text
URLProtocol 打开 URL
  │
  ▼
读取一小段 probe data
  │
  ▼
遍历 AVInputFormat probe 函数
  │
  ▼
选择分数最高的 demuxer
  │
  ▼
读取 header
  │
  ▼
建立 AVStream 列表
  │
  ▼
查找 codec parameters
```

相关参数：

| 参数 | 说明 |
|---|---|
| -probesize | 探测读取的数据量上限 |
| -analyzeduration | 分析流信息的时长上限 |
| -fflags nobuffer | 减少输入缓冲，常用于低延迟 |

探测不足可能导致：

- 识别不出音频流或字幕流。
- 码率、帧率估计不准。
- time_base 或 extradata 不完整。
- 直播流启动快但后续容易异常。

### 10.5 Muxer 的交错写入

多流输出时，muxer 不能随便先写完视频再写音频。

它需要类似这样交错：

```text
video packet pts=0.000
 audio packet pts=0.000
 audio packet pts=0.023
video packet pts=0.040
 audio packet pts=0.046
video packet pts=0.080
```

如果某一路流迟迟没有 packet，muxer 可能：

1. 等待该流。
2. 缓存其他流 packet。
3. 超过 interleave delta 后强制写出。
4. 在直播输出中表现为卡顿或延迟增加。

### 10.6 网络 I/O 与实时流

实时流和本地文件最大区别是：

```text
本地文件：数据通常随取随有
实时流：数据按时间到达，可能抖动、丢包、阻塞
```

常见低延迟参数方向：

```bash
-fflags nobuffer
-flags low_delay
-probesize 32
-analyzeduration 0
```

但这些参数有副作用：

| 优化 | 代价 |
|---|---|
| 减少 probe | 流信息更可能识别不完整 |
| 减少 buffer | 抗网络抖动能力下降 |
| 降低 analyzeduration | 帧率/码率估计可能不准 |
| 禁用缓冲 | 更容易卡顿或丢帧 |

---

## 11. FFmpeg CLI 的任务调度模型

FFmpeg CLI 内部不是简单的一行命令直接顺序执行，而是会根据输入、输出、流映射和滤镜图构建一套转码任务。

### 11.1 关键抽象

可以把 CLI 层抽象为：

```text
InputFile
  └─ InputStream
       └─ Decoder
            └─ FilterGraph
                 └─ Encoder
                      └─ OutputStream
                           └─ OutputFile
```

### 11.2 多流场景

一个 MP4 文件可能有：

```text
Stream 0: video h264
Stream 1: audio aac
Stream 2: subtitle mov_text
```

转码时，视频和音频通常走不同链路：

```text
Video Packet -> Video Decoder -> Video Filter -> Video Encoder -> Video Mux
Audio Packet -> Audio Decoder -> Audio Filter -> Audio Encoder -> Audio Mux
```

它们最终在 Muxer 处按时间戳交错写入。

### 11.3 Stream Copy 场景

如果使用 `-c copy`：

```bash
ffmpeg -i input.mp4 -c copy output.mkv
```

则链路变成：

```text
Demuxer -> AVPacket -> Muxer
```

此时不会解码，也不会编码，速度通常非常快，CPU 消耗低。

### 11.4 ffmpeg CLI 的执行阶段

从 CLI 角度看，一次命令大致分为：

```text
参数解析
  │
  ▼
创建输入文件和输入流
  │
  ▼
创建输出文件和输出流
  │
  ▼
建立 stream mapping
  │
  ▼
初始化 decoder / filter / encoder / muxer
  │
  ▼
启动调度循环
  │
  ▼
flush 所有链路
  │
  ▼
写 trailer，释放资源
```

### 11.5 Stream Mapping 是连接层

例如：

```bash
ffmpeg -i input.mp4 -map 0:v:0 -map 0:a:0 -c:v libx264 -c:a aac output.mp4
```

stream mapping 决定：

```text
哪个 InputStream 连接到哪个 OutputStream
哪个流需要 decoder
哪个流需要 filter
哪个流需要 encoder
哪个流可以 stream copy
```

如果不显式写 `-map`，FFmpeg 会自动选择默认流，但复杂输入下容易和预期不一致。

### 11.6 多输出任务

一个输入可以同时输出多个文件：

```bash
ffmpeg -i input.mp4 \
  -map 0:v -c:v libx264 out.mp4 \
  -map 0:v -c:v libx265 out.hevc.mp4
```

抽象链路：

```text
Input Video Stream
  │
  ▼
Decoder
  │ AVFrame
  ├─ Encoder libx264 -> Muxer MP4 -> out.mp4
  └─ Encoder libx265 -> Muxer MP4 -> out.hevc.mp4
```

这里会出现资源竞争：

- 一个 decoder 的输出可能喂多个输出链。
- 每个 encoder 有自己的线程池。
- 输出 muxer 各自写文件。
- 最慢的输出链可能拖累整体调度。

---

## 12. 模块之间的数据结构关系

FFmpeg 最重要的两个数据结构是：

```text
AVPacket：压缩数据
AVFrame：原始帧数据
```

### 12.1 AVPacket

AVPacket 表示编码后的压缩数据，常见于：

- Demuxer 输出。
- Decoder 输入。
- Encoder 输出。
- Muxer 输入。

```text
Demuxer -> AVPacket -> Decoder
Encoder -> AVPacket -> Muxer
```

关键字段概念：

| 字段 | 含义 |
|---|---|
| data | 压缩数据指针 |
| size | 数据大小 |
| pts | 显示时间戳 |
| dts | 解码时间戳 |
| stream_index | 属于哪一条流 |
| duration | 持续时长 |

### 12.2 AVFrame

AVFrame 表示解码后的原始音视频数据，常见于：

- Decoder 输出。
- FilterGraph 输入输出。
- Encoder 输入。

```text
Decoder -> AVFrame -> FilterGraph -> AVFrame -> Encoder
```

视频 AVFrame 关心：

- width / height。
- format。
- data / linesize。
- pts。

音频 AVFrame 关心：

- sample_rate。
- channel layout。
- sample format。
- nb_samples。
- pts。

### 12.3 时间戳模型

FFmpeg 中时间戳非常关键。

核心概念：

| 概念 | 含义 |
|---|---|
| PTS | Presentation Timestamp，显示时间 |
| DTS | Decoding Timestamp，解码时间 |
| time_base | 时间戳单位 |
| duration | 持续时长 |

简化理解：

```text
真实时间 = timestamp × time_base
```

示例：

```text
pts = 90000
time_base = 1/90000
真实时间 = 1 秒
```

### 12.4 AVBufferRef 与零拷贝

AVPacket 和 AVFrame 往往不直接拥有大块数据，而是引用 AVBufferRef。

```text
AVFrame
  ├─ data[0] -> AVBufferRef -> Y plane
  ├─ data[1] -> AVBufferRef -> U plane
  └─ data[2] -> AVBufferRef -> V plane
```

引用计数带来的好处：

1. 模块之间传帧不一定拷贝大块内存。
2. 滤镜可以复用输入帧数据。
3. 编码器可以安全持有输入帧引用。
4. 多线程下可以避免过早释放。

常见操作语义：

| 操作 | 语义 |
|---|---|
| av_frame_ref | 增加引用，共享底层 buffer |
| av_frame_clone | 创建新的 frame 壳并引用底层 buffer |
| av_frame_unref | 释放当前 frame 引用 |
| av_frame_make_writable | 如果共享则拷贝，确保可写 |
| av_packet_ref | 增加 packet 引用 |
| av_packet_unref | 释放 packet 引用 |

### 12.5 side data 与 extradata

除了主数据，FFmpeg 还有两类常见附加数据。

| 类型 | 所属 | 例子 |
|---|---|---|
| extradata | codec parameters / codec context | H.264 SPS/PPS，AAC AudioSpecificConfig |
| side data | packet / frame | HDR metadata，display matrix，skip samples |

它们很容易被忽略，但在实际工程中很重要：

- MP4 转 Annex B H.264 时经常要处理 SPS/PPS。
- 旋转信息可能在 display matrix 里，而不在像素数据里。
- HDR 视频需要保留 mastering display metadata。
- AAC 裁剪和 gapless playback 依赖 skip samples。

---

## 13. 常见命令背后的执行流程

### 13.1 查看媒体信息

```bash
ffprobe input.mp4
```

执行重点：

```text
打开输入 -> 探测格式 -> 读取流信息 -> 打印 metadata / stream / codec 参数
```

### 13.2 转封装

```bash
ffmpeg -i input.mp4 -c copy output.mkv
```

执行链路：

```text
MP4 Demuxer -> AVPacket -> MKV Muxer
```

特点：

- 不解码。
- 不编码。
- 速度快。
- 画质无损。
- 只改变容器格式。

### 13.3 转码

```bash
ffmpeg -i input.mp4 -c:v libx264 -c:a aac output.mp4
```

执行链路：

```text
Demux -> Decode -> Encode -> Mux
```

特点：

- 会消耗大量 CPU/GPU。
- 可能损失画质。
- 可以改变编码格式、码率、分辨率等。

### 13.4 加滤镜转码

```bash
ffmpeg -i input.mp4 -vf scale=1280:720 -c:v libx264 output.mp4
```

执行链路：

```text
Demux -> Decode -> Filter(scale) -> Encode -> Mux
```

特点：

- 必须解码到 AVFrame。
- 经过滤镜处理后再编码。
- 不能纯 `-c copy`。

### 13.5 推流

```bash
ffmpeg -re -i input.mp4 -c copy -f flv rtmp://server/live/stream
```

执行链路：

```text
File Demux -> Packet -> FLV Mux -> RTMP Output
```

特点：

- `-re` 按真实时间速度读取。
- 输出端可能受网络波动影响。
- 推流失败通常与 I/O、协议、时间戳有关。

---

## 14. 性能调优视角

### 14.1 线程数不是越多越好

常见误区：

```bash
ffmpeg -threads 64 ...
```

线程数过多可能导致：

- 上下文切换增加。
- CPU cache 命中率下降。
- 内存占用增加。
- 编码器内部调度成本上升。
- I/O 或滤镜成为瓶颈时，继续增加编解码线程没有意义。

### 14.2 定位瓶颈的方法

可以从链路上逐段排查：

```text
Demux I/O -> Decode -> Filter -> Encode -> Mux I/O
```

| 瓶颈位置 | 现象 | 优化方向 |
|---|---|---|
| 输入 I/O | 读取慢、网络抖动 | 本地化输入、增大缓冲、检查协议 |
| 解码 | CPU 高、解码慢 | 增加解码线程、硬件解码 |
| 滤镜 | scale/overlay 慢 | 简化滤镜、GPU 滤镜、调整 filter_threads |
| 编码 | CPU 高、速度慢 | 调 preset、线程数、硬件编码 |
| 输出 I/O | 写入阻塞、推流卡顿 | 检查网络、降低码率、调整封装参数 |

### 14.3 常用调优参数

| 参数 | 说明 |
|---|---|
| -threads N | 编解码线程数 |
| -filter_threads N | 简单滤镜线程数 |
| -filter_complex_threads N | 复杂滤镜线程数 |
| -preset | 编码速度与压缩率平衡，常用于 x264/x265 |
| -tune zerolatency | 低延迟编码调优 |
| -hwaccel | 启用硬件加速解码 |
| -c:v h264_nvenc | 使用 NVIDIA 硬件编码 |

### 14.4 硬件加速与线程模型

硬件加速会改变瓶颈位置。

```text
CPU 解码/编码瓶颈 -> GPU 解码/编码瓶颈 -> PCIe 拷贝/显存/滤镜瓶颈
```

典型命令：

```bash
ffmpeg -hwaccel cuda -i input.mp4 -c:v h264_nvenc output.mp4
```

需要注意：

- 硬解和硬编不是一定更快，短视频、小分辨率时初始化成本明显。
- CPU/GPU 之间的数据拷贝可能成为瓶颈。
- 如果滤镜在 CPU 上执行，硬件帧可能需要下载回系统内存。

---

## 15. 源码阅读路线

如果要读 FFmpeg 源码，建议按“数据流”而不是按目录硬读。

### 15.1 第一阶段：理解 CLI 主流程

重点文件方向：

```text
fftools/ffmpeg.c
fftools/ffmpeg_demux.c
fftools/ffmpeg_dec.c
fftools/ffmpeg_filter.c
fftools/ffmpeg_enc.c
fftools/ffmpeg_mux.c
```

阅读目标：

- 命令行参数如何解析。
- 输入输出文件如何初始化。
- stream mapping 如何建立。
- 转码循环如何驱动。

### 15.2 第二阶段：理解 libavformat

重点方向：

```text
libavformat/avformat.c
libavformat/demux.c
libavformat/mux.c
libavformat/avio.c
```

阅读目标：

- `avformat_open_input()` 如何打开输入。
- `avformat_find_stream_info()` 如何探测流信息。
- `av_read_frame()` 如何返回 AVPacket。
- `av_interleaved_write_frame()` 如何写入包。

### 15.3 第三阶段：理解 libavcodec

重点方向：

```text
libavcodec/avcodec.c
libavcodec/decode.c
libavcodec/encode.c
libavcodec/pthread_frame.c
libavcodec/pthread_slice.c
```

阅读目标：

- send/receive API 如何工作。
- 解码器如何管理 packet/frame。
- frame threading 如何调度。
- slice threading 如何调度。

### 15.4 第四阶段：理解 libavfilter

重点方向：

```text
libavfilter/avfiltergraph.c
libavfilter/buffersrc.c
libavfilter/buffersink.c
libavfilter/vf_scale.c
libavfilter/af_aresample.c
```

阅读目标：

- FilterGraph 如何解析。
- buffersrc / buffersink 如何连接应用层。
- 滤镜节点之间如何传递 AVFrame。
- 滤镜图如何调度执行。

---

## 16. 源码级端到端调用链

这一节从源码调用关系理解 FFmpeg，而不是只看抽象模块。

### 16.1 解封装调用链

典型 API：

```c
avformat_open_input(&fmt_ctx, url, NULL, &options);
avformat_find_stream_info(fmt_ctx, NULL);
av_read_frame(fmt_ctx, pkt);
```

抽象调用链：

```text
avformat_open_input
  │
  ├─ init_input
  │    ├─ ffio_open_whitelist / avio_open2
  │    ├─ av_probe_input_buffer2
  │    └─ 选择 AVInputFormat
  │
  ├─ s->iformat->read_header
  │    └─ 读取容器头，创建 AVStream
  │
  └─ 返回 AVFormatContext

avformat_find_stream_info
  │
  ├─ 循环 av_read_frame
  ├─ 尝试解析 codec parameters
  ├─ 估算 fps / duration / bitrate
  └─ 必要时临时打开 decoder 辅助探测

av_read_frame
  │
  ├─ read_frame_internal
  ├─ demuxer->read_packet
  ├─ parser 处理 packet 边界
  └─ 返回 AVPacket
```

关键点：

1. `avformat_open_input` 主要解决“输入是什么”。
2. `avformat_find_stream_info` 主要解决“里面有哪些流、参数是什么”。
3. `av_read_frame` 主要解决“按 demuxer 逻辑吐出一个 packet”。
4. 容器格式不同，`read_header` 和 `read_packet` 的具体实现完全不同。

### 16.2 解码调用链

典型 API：

```c
avcodec_find_decoder(codec_id);
avcodec_alloc_context3(codec);
avcodec_parameters_to_context(codec_ctx, stream->codecpar);
avcodec_open2(codec_ctx, codec, &options);
avcodec_send_packet(codec_ctx, pkt);
avcodec_receive_frame(codec_ctx, frame);
```

抽象调用链：

```text
avcodec_open2
  │
  ├─ 校验 codec 参数
  ├─ 初始化 codec 私有上下文
  ├─ 初始化线程模型
  │    ├─ frame threading
  │    └─ slice threading
  └─ codec->init

avcodec_send_packet
  │
  ├─ 输入 packet 入队或保存
  ├─ parser / bitstream filter 相关处理
  ├─ 触发 decode receive 侧状态变化
  └─ 可能唤醒 worker thread

avcodec_receive_frame
  │
  ├─ 从内部队列取 decoded frame
  ├─ 如果没有则驱动 decode
  ├─ 处理 reorder / delay
  └─ 返回 AVFrame 或 EAGAIN / EOF
```

### 16.3 滤镜调用链

典型 API：

```c
avfilter_graph_alloc();
avfilter_graph_parse_ptr(graph, filter_desc, &inputs, &outputs, NULL);
avfilter_graph_config(graph, NULL);
av_buffersrc_add_frame_flags(src_ctx, frame, flags);
av_buffersink_get_frame(sink_ctx, filt_frame);
```

抽象调用链：

```text
avfilter_graph_parse_ptr
  │
  ├─ 解析 filter 字符串
  ├─ 创建 AVFilterContext 节点
  ├─ 创建 AVFilterLink 边
  └─ 建立 DAG

avfilter_graph_config
  │
  ├─ 格式协商
  ├─ time_base 协商
  ├─ width/height/sample_rate/channel_layout 协商
  └─ 初始化各 filter

av_buffersrc_add_frame_flags
  │
  └─ 输入 AVFrame 到 graph

av_buffersink_get_frame
  │
  ├─ 从 sink 拉取 frame
  ├─ 触发上游 request_frame
  ├─ 执行 filter chain
  └─ 返回处理后的 AVFrame
```

格式协商非常重要。例如 `scale` 前后像素格式不匹配时，FFmpeg 可能自动插入 format/scale 类转换节点。

### 16.4 编码调用链

典型 API：

```c
avcodec_find_encoder(codec_id);
avcodec_alloc_context3(codec);
avcodec_open2(codec_ctx, codec, &options);
avcodec_send_frame(codec_ctx, frame);
avcodec_receive_packet(codec_ctx, pkt);
```

抽象调用链：

```text
avcodec_open2
  │
  ├─ 初始化 encoder 参数
  ├─ 初始化线程模型
  ├─ 初始化外部编码库，例如 libx264
  └─ codec->init

avcodec_send_frame
  │
  ├─ 输入 frame 入队
  ├─ 可能触发 lookahead
  ├─ 可能触发 frame reorder
  └─ 可能唤醒 worker thread

avcodec_receive_packet
  │
  ├─ 从编码器内部取 packet
  ├─ 写入 pts/dts/duration
  ├─ 附加 side data
  └─ 返回 AVPacket 或 EAGAIN / EOF
```

### 16.5 封装调用链

典型 API：

```c
avformat_alloc_output_context2(&out_ctx, NULL, NULL, filename);
avformat_new_stream(out_ctx, codec);
avcodec_parameters_from_context(out_stream->codecpar, enc_ctx);
avio_open(&out_ctx->pb, filename, AVIO_FLAG_WRITE);
avformat_write_header(out_ctx, &options);
av_interleaved_write_frame(out_ctx, pkt);
av_write_trailer(out_ctx);
```

抽象调用链：

```text
avformat_write_header
  │
  ├─ muxer->write_header
  ├─ 写容器头
  └─ 写全局 metadata / extradata

av_interleaved_write_frame
  │
  ├─ 检查 packet stream_index
  ├─ rescale timestamp 到 output stream time_base
  ├─ 根据 dts/pts 做 interleave
  ├─ muxer->write_packet
  └─ AVIOContext 写到底层协议

av_write_trailer
  │
  ├─ flush interleave queue
  ├─ muxer->write_trailer
  └─ 写索引、duration、moov 等尾部信息
```

MP4 这类容器在 trailer 阶段很关键，因为索引、duration、moov 等信息可能要最后写入或回填。

---

## 17. 队列、缓冲与背压模型

FFmpeg 的运行效率和延迟，很大程度取决于每个阶段的队列和缓冲。

### 17.1 简化队列图

完整转码可以抽象为：

```text
Input I/O
  │
  ▼
Demux Packet Queue
  │
  ▼
Decoder Input Queue
  │
  ▼
Decoder Reorder Buffer
  │
  ▼
Filter Frame Queue
  │
  ▼
Encoder Input Queue
  │
  ▼
Encoder Lookahead / Reorder Buffer
  │
  ▼
Mux Interleave Queue
  │
  ▼
Output I/O
```

任何一个队列变长，都会带来：

- 内存增加。
- 延迟增加。
- flush 时间增加。
- 实时流更容易越积越慢。

### 17.2 背压如何产生

背压是下游处理慢导致上游无法继续推进。

```text
Output I/O 慢
  -> muxer 写阻塞
  -> encoder packet 无法及时写出
  -> encoder receive 变慢
  -> filter 输出 frame 堵住
  -> decoder 输出 frame 堵住
  -> demuxer 读包变慢
```

这就是为什么推流时网络慢，会表现为整个 FFmpeg 处理链变慢，而不是只有最后一步慢。

### 17.3 常见缓冲来源

| 位置 | 缓冲内容 | 常见原因 |
|---|---|---|
| demuxer | AVPacket | 网络 jitter、容器探测、parser |
| decoder | AVFrame / reference frame | B 帧、frame threading、DPB |
| filter | AVFrame | 多输入同步、fps、overlay、concat |
| encoder | AVFrame / AVPacket | lookahead、B 帧、rate control |
| muxer | AVPacket | 多流 interleave、输出阻塞 |
| protocol | bytes | socket buffer、文件系统缓存 |

### 17.4 低延迟链路设计原则

低延迟不是只加一个参数，而是整条链路都要减少缓存：

```text
输入少 probe
解码少 reorder
滤镜少缓存
编码少 B 帧和 lookahead
mux 少 interleave 等待
输出协议少缓冲
```

典型方向：

```bash
-fflags nobuffer
-flags low_delay
-tune zerolatency
-g 较小
-bf 0
-probesize 较小
-analyzeduration 较小
```

但越低延迟，抗抖动能力和压缩效率通常越差。

---

## 18. 线程安全、生命周期与引用计数

### 18.1 哪些对象不能随便跨线程共享

一般原则：

| 对象 | 是否适合多线程共享 | 说明 |
|---|---|---|
| AVFormatContext | 不建议并发读写 | demux/mux 状态复杂 |
| AVCodecContext | 不建议外部多线程同时调用 send/receive | 内部线程由 codec 自己管理 |
| AVFilterGraph | 不建议多个外部线程同时驱动同一 graph | 图状态和缓存复杂 |
| AVPacket / AVFrame | 可以通过引用计数传递 | 要管理 ref/unref |
| AVBufferRef | 可引用计数共享 | 写前要确保 writable |

工程上更稳的模型是：

```text
一个 context 由一个调度线程驱动
模块内部自己开 worker threads
跨线程只传 ref-counted AVPacket / AVFrame
```

### 18.2 AVFrame 生命周期

常见生命周期：

```text
av_frame_alloc
  │
  ▼
decoder receive 填充 frame
  │
  ▼
送入 filter 或 encoder
  │
  ▼
av_frame_unref 复用 frame 壳
  │
  ▼
av_frame_free
```

如果编码器或滤镜需要保留 frame，它会增加引用或内部拷贝。用户代码不要在没有明确所有权的情况下直接修改 frame 数据。

### 18.3 可写性问题

共享 buffer 时，直接写可能破坏其他引用者看到的数据。

典型安全流程：

```text
if frame not writable:
    av_frame_make_writable(frame)
modify frame data
```

这类问题在自定义滤镜、自定义转码代码中很常见。

### 18.4 Packet 生命周期

Packet 通常循环复用：

```text
pkt = av_packet_alloc()
while av_read_frame(fmt, pkt) >= 0:
    send pkt
    av_packet_unref(pkt)
av_packet_free(&pkt)
```

`av_packet_unref` 释放的是当前引用，不一定立即释放底层数据，因为其他模块可能还持有引用。

---

## 19. 时间戳、同步与音视频对齐

时间戳是 FFmpeg 中最容易出错的部分。

### 19.1 time_base 转换

不同模块 time_base 可能不同：

```text
Input stream time_base: 1/90000
Decoder frame time_base: 1/25
Encoder time_base: 1/25
Output stream time_base: 1/12800
```

跨模块传递时经常需要 rescale：

```text
av_packet_rescale_ts(pkt, in_stream->time_base, out_stream->time_base)
```

如果忘记转换，会出现：

- 音视频不同步。
- 输出时长错误。
- 播放速度异常。
- muxer 报 non-monotonous DTS。

### 19.2 PTS 和 DTS 的工程规则

| 场景 | 关注点 |
|---|---|
| 解码输入 | DTS 顺序通常更重要 |
| 显示输出 | PTS 顺序更重要 |
| 编码输出 | 编码器可能重新生成 PTS/DTS |
| mux 写入 | DTS 必须单调递增，PTS 要合理 |

常见错误：

```text
Application provided invalid, non monotonically increasing dts
```

常见原因：

1. packet 没有正确 rescale time_base。
2. 多路流交错写入顺序不对。
3. B 帧重排后 DTS 处理错误。
4. 手动改 PTS 但没有同步调整 duration。
5. concat 多段视频时起始时间没有归零或连续化。

### 19.3 音视频同步模型

播放器最终同步的是时间，而不是帧号：

```text
video frame pts = 10.000s
audio samples 覆盖 9.984s ~ 10.007s
subtitle event 覆盖 9.500s ~ 11.000s
```

所以同步关键是：

1. 每条流的 PTS 都要落在统一时间轴上。
2. time_base 必须正确换算。
3. 音频重采样后 sample 数变化要反映到 PTS。
4. 视频变帧率时不能假设固定帧间隔。

### 19.4 VFR 与 CFR

| 类型 | 含义 | 特点 |
|---|---|---|
| CFR | Constant Frame Rate | 每帧间隔固定 |
| VFR | Variable Frame Rate | 每帧间隔可能不同 |

很多屏幕录制、手机视频是 VFR。处理 VFR 时，如果强行按固定 FPS 理解，容易出现音画不同步。

常见处理方向：

```bash
-vsync cfr
-vsync vfr
-fps_mode cfr
-fps_mode vfr
```

---

## 20. 多输入、多输出与复杂 FilterGraph

### 20.1 多输入合成

例如画中画：

```bash
ffmpeg -i main.mp4 -i pip.mp4 \
  -filter_complex "[1:v]scale=320:180[pip];[0:v][pip]overlay=10:10[out]" \
  -map "[out]" -map 0:a -c:v libx264 output.mp4
```

架构图：

```text
main.mp4 video -> decoder -> [0:v] ───────────┐
                                               ├─ overlay -> encoder -> mux
pip.mp4 video  -> decoder -> scale -> [pip] ──┘
main.mp4 audio -> demux/copy or decode/encode ────────────────┘
```

关键点：

- 两个输入各有 demuxer。
- 两个视频流各有 decoder。
- filter_complex 把两条视频链合成一条。
- 音频可以从主视频复制或重新编码。
- overlay 的输出节奏受两个输入时间戳影响。

### 20.2 一进多出转码

例如同时输出 1080p、720p、480p：

```bash
ffmpeg -i input.mp4 \
  -filter_complex "[0:v]split=3[v1][v2][v3];[v1]scale=1920:1080[o1];[v2]scale=1280:720[o2];[v3]scale=854:480[o3]" \
  -map "[o1]" -c:v:0 libx264 out_1080p.mp4 \
  -map "[o2]" -c:v:1 libx264 out_720p.mp4 \
  -map "[o3]" -c:v:2 libx264 out_480p.mp4
```

架构图：

```text
Decoder
  │
  ▼
split
  ├─ scale 1080p -> encoder 1 -> mux 1
  ├─ scale 720p  -> encoder 2 -> mux 2
  └─ scale 480p  -> encoder 3 -> mux 3
```

瓶颈可能出现在：

- 单个 decoder 输出供应不足。
- split 后 frame 引用增多，生命周期变长。
- 多个 scale 同时占 CPU。
- 多个 encoder 同时抢 CPU。
- 某一个 muxer 慢导致整体背压。

### 20.3 concat 的两种模式

| 模式 | 说明 |
|---|---|
| concat demuxer | 输入参数一致时更高效，packet 级拼接 |
| concat filter | 可以处理参数不同的输入，但需要解码和重新编码 |

packet 级 concat：

```text
Demux A packet -> Mux
Demux B packet -> Mux
```

filter 级 concat：

```text
Decode A -> Frame
Decode B -> Frame
concat filter -> Encode -> Mux
```

如果输入视频参数不同，直接 packet concat 很容易出现时间戳、分辨率、编码参数不一致问题。

---

## 21. 实战排障与性能分析清单

### 21.1 先判断是哪类任务

| 任务 | 是否解码 | 是否编码 | 主要瓶颈 |
|---|---:|---:|---|
| 转封装 `-c copy` | 否 | 否 | I/O、容器兼容、时间戳 |
| 普通转码 | 是 | 是 | 编码器通常最重 |
| 加滤镜转码 | 是 | 是 | 滤镜和编码器 |
| 推流 | 视情况 | 视情况 | 网络、时间戳、实时性 |
| 多码率输出 | 是 | 多个编码 | CPU/GPU、内存、背压 |

### 21.2 看日志的重点

建议加：

```bash
-loglevel verbose
```

更深入可以用：

```bash
-loglevel debug
```

重点看：

- 输入格式是否识别正确。
- 每条 stream 的 codecpar 是否完整。
- filter graph 是否自动插入了 scale/format/aresample。
- encoder 实际使用了多少线程。
- time_base、fps、sample_rate 是否符合预期。
- 是否有 non-monotonous DTS、queue blocking、buffer underflow。

### 21.3 常见问题定位

| 现象 | 可能原因 | 排查方向 |
|---|---|---|
| 转码很慢 | 编码 preset 慢、滤镜重、没用硬件加速 | 看 CPU/GPU、换 preset、拆掉滤镜测试 |
| 推流延迟越来越大 | 输出网络慢、buffer 积压、编码太慢 | 降码率、减少缓冲、检查实时速度 |
| 音画不同步 | time_base 错、VFR、重采样 PTS 错 | ffprobe 看 packet/frame PTS |
| 最后几帧丢失 | 没 flush decoder/encoder/filter | 检查 EOF 流程 |
| MP4 播放不了 | trailer 没写、moov 异常、编码参数缺失 | 确认 av_write_trailer 成功 |
| 画面旋转不对 | display matrix side data 被丢 | 检查 metadata/side data |
| HDR 丢失 | side data 没传递 | 检查 mastering display metadata |
| 内存持续上涨 | 下游背压、frame 引用未释放 | 检查 unref/free 和队列长度 |

### 21.4 性能定位实验法

不要一上来调所有参数，应该拆链路。

第一步，只测读取和解封装：

```bash
ffmpeg -i input.mp4 -c copy -f null -
```

第二步，测解码：

```bash
ffmpeg -i input.mp4 -f null -
```

第三步，测滤镜：

```bash
ffmpeg -i input.mp4 -vf scale=1280:720 -f null -
```

第四步，测编码：

```bash
ffmpeg -i input.mp4 -vf scale=1280:720 -c:v libx264 -f null -
```

第五步，测实际输出：

```bash
ffmpeg -i input.mp4 -vf scale=1280:720 -c:v libx264 output.mp4
```

这样可以判断瓶颈是在 I/O、解码、滤镜、编码还是 mux。

### 21.5 ffprobe 辅助分析

查看容器和流：

```bash
ffprobe -hide_banner -show_format -show_streams input.mp4
```

查看 packet 时间戳：

```bash
ffprobe -select_streams v:0 -show_packets -show_entries packet=pts_time,dts_time,duration_time,flags input.mp4
```

查看 frame 时间戳：

```bash
ffprobe -select_streams v:0 -show_frames -show_entries frame=pts_time,pkt_dts_time,pict_type input.mp4
```

这些信息能帮助定位：

- 是否有 B 帧。
- DTS 是否单调。
- 是否 VFR。
- 关键帧分布是否合理。
- duration 是否异常。

---

## 22. 面试总结版

如果面试中被问“FFmpeg 架构是什么”，可以这样回答：

> FFmpeg 的核心架构是一条媒体处理流水线：输入协议和容器由 libavformat 负责，解封装后得到 AVPacket；AVPacket 进入 libavcodec 解码成 AVFrame；AVFrame 可以进入 libavfilter 做缩放、裁剪、混流、重采样等处理；处理后的 AVFrame 再由 libavcodec 编码成 AVPacket；最后由 libavformat 封装并写入输出。底层公共能力由 libavutil、libswscale、libswresample 等库提供。

如果继续问“线程模型是什么”，可以这样回答：

> FFmpeg 的线程模型是分层的。CLI 层有整体转码调度循环，负责驱动输入、解码、滤镜、编码和输出；编解码器内部可以通过 frame threading 或 slice threading 做并行；FilterGraph 也有自己的 filter_threads 和 filter_complex_threads；I/O 层通常由主流程驱动，但网络和设备输入可能带来阻塞、缓冲或异步行为。所以 FFmpeg 不是一个简单的全局线程池模型，而是不同模块内部各自具备并行能力，由上层转码流程串起来。

如果问“AVPacket 和 AVFrame 的区别”，可以这样回答：

> AVPacket 是压缩后的编码数据，主要在 Demuxer、Decoder、Encoder、Muxer 之间流动；AVFrame 是解码后的原始音视频帧，主要在 Decoder、FilterGraph 和 Encoder 之间流动。简单说，Packet 是压缩态，Frame 是原始态。

如果问“转封装和转码有什么区别”，可以这样回答：

> 转封装是 Demuxer 读出 AVPacket 后直接交给 Muxer 写入新容器，不经过解码和编码，所以速度快、画质无损；转码则需要解码成 AVFrame，再重新编码成 AVPacket，能改变编码格式、分辨率、码率，但成本更高，也可能损失质量。

---

## 23. 总结

FFmpeg 可以用三个关键词概括：

```text
Pipeline：媒体处理流水线
Module：格式、编解码、滤镜、工具库解耦
Threading：编解码、滤镜、调度多层并行
```

核心心智模型：

```text
AVPacket 是压缩数据，AVFrame 是原始帧。
libavformat 管容器，libavcodec 管编解码，libavfilter 管帧处理。
线程模型不是一个全局统一线程池，而是 CLI 调度 + codec 内部线程 + filter 图线程 + I/O 行为共同组成。
```

掌握这条主线后，再去看具体命令、源码、性能调优和音视频工程问题，都会清晰很多。
