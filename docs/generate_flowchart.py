# -*- coding: utf-8 -*-
"""
生成 Tool Calling 流程图 PNG
"""
from PIL import Image, ImageDraw, ImageFont

# 创建画布
W, H = 1000, 800
img = Image.new('RGB', (W, H), color='#ffffff')
draw = ImageDraw.Draw(img)

# 颜色定义
COLOR_BOX = '#e3f2fd'
COLOR_BOX_BORDER = '#2196f3'
COLOR_ARROW = '#333333'
COLOR_TEXT = '#1a1a1a'
COLOR_HIGHLIGHT = '#fff3e0'
COLOR_HIGHLIGHT_BORDER = '#ff9800'

# 字体设置（兼容 Windows）
try:
    font_title = ImageFont.truetype("msyh.ttc", 24)
    font_box = ImageFont.truetype("msyh.ttc", 14)
    font_small = ImageFont.truetype("msyh.ttc", 12)
except:
    font_title = ImageFont.load_default(size=24)
    font_box = ImageFont.load_default(size=14)
    font_small = ImageFont.load_default(size=12)

def draw_box(x, y, w, h, text, is_highlight=False, lines=None):
    """画一个方框"""
    fill_color = COLOR_HIGHLIGHT if is_highlight else COLOR_BOX
    border_color = COLOR_HIGHLIGHT_BORDER if is_highlight else COLOR_BOX_BORDER
    draw.rounded_rectangle([x, y, x + w, y + h], radius=8, fill=fill_color, outline=border_color, width=2)

    if lines:
        # 多行文本
        line_height = 20
        total_height = len(lines) * line_height
        start_y = y + (h - total_height) / 2
        for i, line in enumerate(lines):
            bbox = draw.textbbox((0, 0), line, font=font_box)
            text_w = bbox[2] - bbox[0]
            draw.text((x + (w - text_w) / 2, start_y + i * line_height), line, fill=COLOR_TEXT, font=font_box)
    else:
        # 单行文本
        bbox = draw.textbbox((0, 0), text, font=font_box)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]
        draw.text((x + (w - text_w) / 2, y + (h - text_h) / 2), text, fill=COLOR_TEXT, font=font_box)

def draw_arrow(x1, y1, x2, y2, label=None):
    """画箭头"""
    draw.line([(x1, y1), (x2, y2)], fill=COLOR_ARROW, width=2)
    # 箭头头
    draw.polygon([(x2, y2), (x2 - 8, y2 - 5), (x2 - 8, y2 + 5)], fill=COLOR_ARROW)

    if label:
        bbox = draw.textbbox((0, 0), label, font=font_small)
        text_w = bbox[2] - bbox[0]
        label_x = (x1 + x2) / 2 - text_w / 2
        label_y = (y1 + y2) / 2 - 15
        draw.text((label_x, label_y), label, fill=COLOR_ARROW, font=font_small)

# 标题
title = "DevPal Agent Tool Calling 完整流程"
bbox = draw.textbbox((0, 0), title, font=font_title)
draw.text(((W - (bbox[2] - bbox[0])) / 2, 30), title, fill='#1976d2', font=font_title)

# 流程节点 - 纵向布局
box_w, box_h = 200, 60
start_x = W / 2 - box_w / 2
y_start = 100
y_step = 100

# 1. 用户输入
draw_box(start_x, y_start, box_w, box_h, "1. 用户输入任务")
draw_arrow(W/2, y_start + box_h, W/2, y_start + y_step - 10)

# 2. 获取工具描述
y = y_start + y_step
draw_box(start_x, y, box_w, box_h, "2. 获取所有工具描述")
draw_arrow(W/2, y + box_h, W/2, y + y_step - 10, "registry.get_tool_descriptions()")

# 3. 发给大模型
y = y_start + y_step * 2
draw_box(start_x, y, box_w, box_h, "3. 发给大模型 API", True)
draw.text((start_x + 10, y + box_h + 5), "client.messages.create(tools=tools)", fill='#f57c00', font=font_small)
draw_arrow(W/2, y + box_h + 25, W/2, y + y_step - 10 + 25)

# 4. 大模型决策
y = y_start + y_step * 3 + 25
draw_box(start_x, y, box_w, box_h, "4. 大模型返回 tool_use")
draw.text((start_x + 10, y + box_h + 5), "block.name='file_writer'", fill='#388e3c', font=font_small)
draw_arrow(W/2, y + box_h + 25, W/2, y + y_step - 10 + 25)

# 5. 匹配工具
y = y_start + y_step * 4 + 50
draw_box(start_x, y, box_w, box_h, "5. 根据 name 匹配工具")
draw_arrow(W/2, y + box_h, W/2, y + y_step - 10, "registry.get('file_writer')")

# 6. 执行工具
y = y_start + y_step * 5 + 50
draw_box(start_x, y, box_w, box_h, "6. 执行工具逻辑")
draw_arrow(W/2, y + box_h, W/2, y + y_step - 10)

# 7. 结果回传
y = y_start + y_step * 6 + 50
draw_box(start_x, y, box_w, box_h, "7. 结果回传给大模型")
draw_arrow(W/2, y + box_h, W/2, y + y_step - 10)

# 8. 最终回答
y = y_start + y_step * 7 + 50
draw_box(start_x, y, box_w, box_h, "8. 输出最终回答")

# 侧边说明
draw_box(30, 350, 180, 120, "核心契约", True, ["工具名称是唯一ID", "file_writer", "大模型严格返回", "相同的名称"])
draw_box(790, 350, 180, 120, "关键代码", True, ["registry.execute_tool", "block.name", "Pydantic参数校验", "messages.append()"])

# 图例
draw.rounded_rectangle([30, 720, 200, 770], radius=5, fill='#f5f5f5', outline='#999')
draw.text((40, 730), "普通流程步骤", fill='#333', font=font_small)
draw.rounded_rectangle([40, 750, 55, 765], radius=3, fill=COLOR_BOX, outline=COLOR_BOX_BORDER)
draw.text((65, 748), "关键步骤", fill='#333', font=font_small)
draw.rounded_rectangle([120, 750, 135, 765], radius=3, fill=COLOR_HIGHLIGHT, outline=COLOR_HIGHLIGHT_BORDER)

# 保存
img.save('docs/tool_call_flow.png')
print("✅ 流程图已生成: docs/tool_call_flow.png")
