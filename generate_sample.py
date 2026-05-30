"""
生成示例 PPT - 用于演示和测试
"""

import sys
import io
from pathlib import Path

# 设置控制台编码
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from ppt_generator import PPTGenerator, create_sample_outline


def main():
    """生成示例 PPT"""
    print("Generating sample PPT...")
    
    # 创建生成器
    generator = PPTGenerator()
    generator.set_color_scheme('professional')
    
    # 使用示例大纲生成
    outline = create_sample_outline()
    generator.generate_from_outline(outline)
    
    # 保存文件
    output_dir = project_root / "output"
    output_dir.mkdir(exist_ok=True)
    
    output_path = output_dir / "sample_presentation.pptx"
    generator.save(str(output_path))
    
    print(f"Success! PPT generated.")
    print(f"File location: {output_path}")
    print(f"Slide count: {generator.get_slide_count()}")
    
    return str(output_path)


if __name__ == "__main__":
    main()
