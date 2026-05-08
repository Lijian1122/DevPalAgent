# -*- coding: utf-8 -*-
"""
多模态图片分析器
支持分析编译报错截图、代码截图等
"""
import base64
import json
from typing import Dict, Any, Optional, List
from pathlib import Path


class ImageAnalyzer:
    """图片分析器 - 使用多模态 LLM 分析图片内容"""

    SUPPORTED_FORMATS = {'.png', '.jpg', '.jpeg', '.gif', '.webp'}

    def __init__(self, llm_client=None):
        """
        初始化图片分析器

        Args:
            llm_client: 支持多模态的 LLM 客户端（Anthropic Claude 3）
        """
        self.client = llm_client

    def _encode_image(self, image_path: str) -> tuple[str, str]:
        """将图片编码为 base64 格式"""
        path = Path(image_path)
        if not path.exists():
            raise FileNotFoundError(f"图片文件不存在: {image_path}")

        if path.suffix.lower() not in self.SUPPORTED_FORMATS:
            raise ValueError(f"不支持的图片格式: {path.suffix}，支持: {self.SUPPORTED_FORMATS}")

        with open(image_path, "rb") as f:
            image_data = base64.b64encode(f.read()).decode()

        # 确定 media type
        media_type = f"image/{path.suffix.lower()[1:]}"
        if media_type == "image/jpg":
            media_type = "image/jpeg"

        return image_data, media_type

    def analyze_image(
        self,
        image_path: str,
        prompt: str = "请详细描述这张图片的内容"
    ) -> str:
        """
        分析图片内容

        Args:
            image_path: 图片文件路径
            prompt: 分析提示词

        Returns:
            图片分析结果
        """
        if self.client is None:
            return f"[模拟模式] 图片分析: {image_path}\n提示词: {prompt}\n请配置 LLM 客户端获取真实分析结果"

        image_data, media_type = self._encode_image(image_path)

        message = {
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": media_type,
                        "data": image_data
                    }
                }
            ]
        }

        response = self.client.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=4096,
            messages=[message]
        )

        return response.content[0].text

    def analyze_compiler_error(
        self,
        image_path: str,
        output_format: str = "text"
    ) -> Dict[str, Any]:
        """
        专门分析编译报错截图

        Args:
            image_path: 截图路径
            output_format: "text" 或 "json"

        Returns:
            编译错误分析结果
        """
        prompt = """
这是一张 C++ 编译报错的截图，请仔细分析：

1. 提取所有报错信息，包括：
   - 错误代码（如 E0020、C2065 等）
   - 文件路径
   - 行号
   - 完整的错误描述

2. 分析每个错误的根本原因

3. 给出具体的修复方案，包括：
   - 需要修改哪个文件
   - 第几行
   - 具体怎么改

4. 按照 JSON 格式输出：
{
    "errors": [
        {
            "error_code": "错误代码",
            "file": "文件路径",
            "line_number": "行号",
            "description": "错误描述",
            "cause": "根本原因",
            "fix": "修复方案"
        }
    ],
    "summary": "错误总结",
    "total_errors": 错误数量
}
"""

        result = self.analyze_image(image_path, prompt)

        if output_format == "json":
            try:
                # 尝试从文本中提取 JSON
                json_start = result.find('{')
                json_end = result.rfind('}') + 1
                if json_start >= 0 and json_end > json_start:
                    return json.loads(result[json_start:json_end])
            except Exception:
                pass

        return {
            "raw_analysis": result,
            "image_path": image_path
        }

    def analyze_code_screenshot(
        self,
        image_path: str,
        language: str = "cpp"
    ) -> Dict[str, Any]:
        """
        分析代码截图，提取代码并进行初步分析

        Args:
            image_path: 代码截图路径
            language: 编程语言

        Returns:
            代码分析结果
        """
        prompt = f"""
这是一张 {language.upper()} 代码的截图，请：

1. 准确提取截图中的所有代码，保持格式和缩进
2. 初步分析代码逻辑
3. 指出可能存在的问题或改进建议

输出格式：
```代码
[提取的代码]
```

代码分析：
[你的分析]

潜在问题：
[问题列表]
"""

        result = self.analyze_image(image_path, prompt)

        return {
            "raw_analysis": result,
            "image_path": image_path
        }

    def batch_analyze(
        self,
        image_paths: List[str],
        prompt: str
    ) -> List[Dict[str, Any]]:
        """批量分析多张图片"""
        results = []
        for path in image_paths:
            try:
                result = self.analyze_image(path, prompt)
                results.append({
                    "image_path": path,
                    "success": True,
                    "analysis": result
                })
            except Exception as e:
                results.append({
                    "image_path": path,
                    "success": False,
                    "error": str(e)
                })
        return results
