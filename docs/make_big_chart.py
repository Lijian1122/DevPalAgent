# -*- coding: utf-8 -*-
"""
生成超大字体的极简流程图
"""
from PIL import Image, ImageDraw, ImageFont

# 创建高清画布 (1920x1080)
W, H = 1920, 1080
img = Image.new('RGB', (W, H), color='#ffffff')
draw = ImageDraw.Draw(img)

# 颜色定义
COLOR_BLUE = '#2196f3'
COLOR_ORANGE = '#ff9800'
COLOR_GREEN = '#4caf50'
COLOR_PURPLE = '#9c27b0'
COLOR_TEXT = '#1a1a1a'

# 大字体！
try:
    font_big = ImageFont.truetype("msyh.ttc", 48)
    font_medium = ImageFont.truetype("msyh.ttc", 32)
    font_small = ImageFont.truetype("msyh.ttc", 24)
except:
    font_big = ImageFont.load_default(size=48)
    font_medium = ImageFont.load_default(size=32)
    font_small = ImageFont.load_default(size=24)

def draw_big_box(x, y, w, h, text, color, border_color):
    """画一个大方框带文字"""
    draw.rounded_rectangle([x, y, x + w, y + h], radius=20, fill=color, outline=border_color, width=5)
    bbox = draw.textbbox((0, 0), text, font=font_big)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    draw.text((x + (w - text_w) / 2, y + (h - text_h) / 2), text, fill=COLOR_TEXT, font=font_big)

def draw_arrow(x1, y1, x2, y2, label=None):
    """画粗箭头"""
    draw.line([(x1, y1), (x2, y2)], fill='#333333', width=6)
    # 箭头头
    draw.polygon([(x2, y2), (x2 - 20, y2 - 12), (x2 - 20, y2 + 12)], fill='#333333')

    if label:
        bbox = draw.textbbox((0, 0), label, font=font_medium)
        text_w = bbox[2] - bbox[0]
        label_x = (x1 + x2) / 2 - text_w / 2
        label_y = (y1 + y2) / 2 - 35
        draw.text((label_x, label_y), label, fill='#666666', font=font_medium)

# 标题
title = "DevPal Agent Tool Calling 核心流程"
bbox = draw.textbbox((0, 0), title, font=font_big)
draw.text(((W - (bbox[2] - bbox[0])) / 2, 50), title, fill='#1976d2', font=font_big)

# 方框尺寸
box_w, box_h = 280, 120
spacing = 100
start_y = 250

# 从左到右布局
x1 = 80
x2 = x1 + box_w + spacing
x3 = x2 + box_w + spacing
x4 = x3 + box_w + spacing
x5 = x4 + box_w + spacing

# 第 1 行：线性流程
draw_big_box(x1, start_y, box_w, box_h, "用户输入", '#e3f2fd', COLOR_BLUE)
draw_big_box(x2, start_y, box_w, box_h, "大模型", '#fff3e0', COLOR_ORANGE)
draw_big_box(x3, start_y, box_w, box_h, "返回 name", '#fff9c4', '#fbc02d')
draw_big_box(x4, start_y, box_w, box_h, "匹配工具", '#e8f5e9', COLOR_GREEN)
draw_big_box(x5, start_y, box_w, box_h, "执行工具", '#f3e5f5', COLOR_PURPLE)

# 箭头（第一行）
draw_arrow(x1 + box_w, start_y + box_h/2, x2, start_y + box_h/2, "任务")
draw_arrow(x2 + box_w, start_y + box_h/2, x3, start_y + box_h/2, "tool_use")
draw_arrow(x3 + box_w, start_y + box_h/2, x4, start_y + box_h/2, "根据 name")
draw_arrow(x4 + box_w, start_y + box_h/2, x5, start_y + box_h/2, "执行")

# 第 2 行：回环
loop_y = start_y + box_h + 80
draw_big_box(x3, loop_y, box_w, box_h, "结果回传", '#e0f7fa', '#00bcd4')

# 回环箭头
draw_arrow(x5 + box_w/2, start_y + box_h, x5 + box_w/2, loop_y)
draw_arrow(x5 + box_w/2, loop_y + box_h/2, x3 + box_w/2, loop_y + box_h/2)
draw_arrow(x3 + box_w/2, loop_y, x3 + box_w/2, start_y + box_h)

# 标签
draw.text((x3 + 50, loop_y - 50), "🔄 多轮循环", fill='#e91e63', font=font_medium)

# 底部核心说明
core_text = """
核心原理：工具名称 name 是唯一契约！

  定义时：class FileTool: name = "file_writer"
      ↓
  发送时："name": "file_writer" （给大模型看）
      ↓
  返回时：block.name = "file_writer" （大模型返回）
      ↓
  执行时：registry.get("file_writer") （本地匹配）
"""
draw.text((200, loop_y + box_h + 60), core_text, fill='#333333', font=font_medium)

# 保存
img.save('docs/tool_call_big.png')
print("✅ 超大字体流程图已生成: docs/tool_call_big.png")
print(f"   分辨率: {W}x{H}")
