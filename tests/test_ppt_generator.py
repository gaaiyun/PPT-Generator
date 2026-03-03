"""
PPT Generator 单元测试
测试覆盖率目标：> 70%
"""

import unittest
import os
import sys
import pandas as pd
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from ppt_generator import PPTGenerator, create_sample_outline


class TestPPTGenerator(unittest.TestCase):
    """PPTGenerator 测试类"""
    
    def setUp(self):
        """测试前准备"""
        self.test_output_dir = project_root / "test_output"
        self.test_output_dir.mkdir(exist_ok=True)
        self.generator = PPTGenerator()
    
    def tearDown(self):
        """测试后清理"""
        # 清理测试文件
        for file in self.test_output_dir.glob("*.pptx"):
            file.unlink()
    
    def test_init(self):
        """测试初始化"""
        generator = PPTGenerator()
        self.assertIsNotNone(generator.prs)
        self.assertEqual(len(generator.prs.slides), 0)
    
    def test_init_with_template(self):
        """测试带模板初始化"""
        # 创建一个临时模板
        temp_template = self.test_output_dir / "temp_template.pptx"
        temp_generator = PPTGenerator()
        temp_generator.add_title_slide("Template", "Test")
        temp_generator.save(str(temp_template))
        
        # 使用模板初始化
        generator = PPTGenerator(str(temp_template))
        self.assertIsNotNone(generator.prs)
        
        # 清理
        temp_template.unlink()
    
    def test_set_color_scheme(self):
        """测试设置配色方案"""
        schemes = ['professional', 'vibrant', 'minimal', 'dark']
        
        for scheme in schemes:
            self.generator.set_color_scheme(scheme)
            self.assertIn('primary', self.generator.color_scheme)
            self.assertIn('secondary', self.generator.color_scheme)
            self.assertIn('accent', self.generator.color_scheme)
    
    def test_set_color_scheme_invalid(self):
        """测试设置无效配色方案"""
        with self.assertRaises(ValueError):
            self.generator.set_color_scheme('invalid_scheme')
    
    def test_add_title_slide(self):
        """测试添加标题幻灯片"""
        self.generator.add_title_slide("Test Title", "Test Subtitle")
        
        self.assertEqual(len(self.generator.prs.slides), 1)
        slide = self.generator.prs.slides[0]
        
        # 验证标题
        title_shape = slide.shapes.title
        self.assertEqual(title_shape.text, "Test Title")
        
        # 验证副标题
        subtitle_shape = slide.placeholders[1]
        self.assertEqual(subtitle_shape.text, "Test Subtitle")
    
    def test_add_content_slide(self):
        """测试添加内容幻灯片"""
        content = ["Point 1", "Point 2", "Point 3"]
        self.generator.add_content_slide("Content Title", content)
        
        self.assertEqual(len(self.generator.prs.slides), 1)
        slide = self.generator.prs.slides[0]
        
        # 验证标题
        title_shape = slide.shapes.title
        self.assertEqual(title_shape.text, "Content Title")
        
        # 验证内容
        content_shape = slide.placeholders[1]
        self.assertIn("Point 1", content_shape.text)
    
    def test_add_content_slide_empty(self):
        """测试添加空内容幻灯片"""
        self.generator.add_content_slide("Empty Title", [])
        
        self.assertEqual(len(self.generator.prs.slides), 1)
    
    def test_add_chart_slide_bar(self):
        """测试添加柱状图幻灯片"""
        df = pd.DataFrame({
            'Category': ['A', 'B', 'C'],
            'Value1': [10, 20, 30],
            'Value2': [15, 25, 35]
        })
        
        self.generator.add_chart_slide(
            "Chart Title",
            'bar',
            df,
            'Category',
            ['Value1', 'Value2']
        )
        
        self.assertEqual(len(self.generator.prs.slides), 1)
    
    def test_add_chart_slide_line(self):
        """测试添加折线图幻灯片"""
        df = pd.DataFrame({
            'Month': ['Jan', 'Feb', 'Mar'],
            'Sales': [100, 150, 200]
        })
        
        self.generator.add_chart_slide(
            "Sales Trend",
            'line',
            df,
            'Month',
            ['Sales']
        )
        
        self.assertEqual(len(self.generator.prs.slides), 1)
    
    def test_add_chart_slide_pie(self):
        """测试添加饼图幻灯片"""
        df = pd.DataFrame({
            'Product': ['A', 'B', 'C'],
            'Market Share': [40, 35, 25]
        })
        
        self.generator.add_chart_slide(
            "Market Share",
            'pie',
            df,
            'Product',
            ['Market Share']
        )
        
        self.assertEqual(len(self.generator.prs.slides), 1)
    
    def test_add_chart_slide_area(self):
        """测试添加面积图幻灯片"""
        df = pd.DataFrame({
            'Quarter': ['Q1', 'Q2', 'Q3', 'Q4'],
            'Revenue': [100, 120, 110, 140]
        })
        
        self.generator.add_chart_slide(
            "Quarterly Revenue",
            'area',
            df,
            'Quarter',
            ['Revenue']
        )
        
        self.assertEqual(len(self.generator.prs.slides), 1)
    
    def test_add_chart_slide_invalid_type(self):
        """测试添加无效图表类型"""
        df = pd.DataFrame({
            'X': ['A', 'B'],
            'Y': [1, 2]
        })
        
        with self.assertRaises(ValueError):
            self.generator.add_chart_slide(
                "Invalid Chart",
                'invalid_type',
                df,
                'X',
                ['Y']
            )
    
    def test_add_section_header(self):
        """测试添加章节标题页"""
        self.generator.add_section_header("Section 1")
        
        self.assertEqual(len(self.generator.prs.slides), 1)
    
    def test_generate_from_outline(self):
        """测试从大纲生成完整 PPT"""
        outline = create_sample_outline()
        self.generator.generate_from_outline(outline)
        
        # 应该包含：封面 + 2 个章节标题 + 3 个内容页
        self.assertGreater(len(self.generator.prs.slides), 0)
    
    def test_generate_from_outline_empty(self):
        """测试从空大纲生成"""
        outline = {
            'title': 'Empty Presentation',
            'subtitle': '',
            'sections': []
        }
        
        self.generator.generate_from_outline(outline)
        self.assertEqual(len(self.generator.prs.slides), 1)  # 只有封面
    
    def test_save(self):
        """测试保存 PPTX 文件"""
        self.generator.add_title_slide("Test", "Save Test")
        
        output_path = self.test_output_dir / "test_save.pptx"
        self.generator.save(str(output_path))
        
        self.assertTrue(output_path.exists())
        self.assertGreater(output_path.stat().st_size, 0)
    
    def test_get_slide_count(self):
        """测试获取幻灯片数量"""
        self.assertEqual(self.generator.get_slide_count(), 0)
        
        self.generator.add_title_slide("Title", "Subtitle")
        self.assertEqual(self.generator.get_slide_count(), 1)
        
        self.generator.add_content_slide("Content", ["Point 1"])
        self.assertEqual(self.generator.get_slide_count(), 2)
    
    def test_multiple_slides(self):
        """测试添加多个幻灯片"""
        for i in range(10):
            self.generator.add_content_slide(f"Slide {i}", [f"Point {i}"])
        
        self.assertEqual(self.generator.get_slide_count(), 10)
    
    def test_color_scheme_application(self):
        """测试配色方案应用"""
        self.generator.set_color_scheme('professional')
        self.generator.add_title_slide("Title", "Subtitle")
        
        # 验证标题颜色
        title_shape = self.generator.prs.slides[0].shapes.title
        title_color = title_shape.text_frame.paragraphs[0].font.color.rgb
        
        # 专业蓝色的主色是 RGB(41, 128, 185)
        self.assertEqual(title_color, self.generator.color_scheme['primary'])


class TestCreateSampleOutline(unittest.TestCase):
    """create_sample_outline 函数测试"""
    
    def test_create_sample_outline(self):
        """测试创建示例大纲"""
        outline = create_sample_outline()
        
        self.assertIn('title', outline)
        self.assertIn('subtitle', outline)
        self.assertIn('sections', outline)
        
        self.assertEqual(outline['title'], '2024 年度业务报告')
        self.assertEqual(outline['subtitle'], '业绩总结与展望')
        self.assertGreater(len(outline['sections']), 0)
    
    def test_sample_outline_structure(self):
        """测试示例大纲结构"""
        outline = create_sample_outline()
        
        for section in outline['sections']:
            self.assertIn('title', section)
            self.assertIn('slides', section)
            
            for slide in section['slides']:
                self.assertIn('type', slide)
                self.assertIn('title', slide)


class TestIntegration(unittest.TestCase):
    """集成测试"""
    
    def setUp(self):
        """测试前准备"""
        self.test_output_dir = project_root / "test_output"
        self.test_output_dir.mkdir(exist_ok=True)
    
    def tearDown(self):
        """测试后清理"""
        for file in self.test_output_dir.glob("*.pptx"):
            file.unlink()
    
    def test_full_workflow(self):
        """测试完整工作流程"""
        # 创建生成器
        generator = PPTGenerator()
        generator.set_color_scheme('professional')
        
        # 添加各种类型的幻灯片
        generator.add_title_slide("Integration Test", "Full Workflow")
        generator.add_content_slide("Content", ["Point 1", "Point 2"])
        generator.add_section_header("Section 1")
        
        # 添加图表
        df = pd.DataFrame({
            'Category': ['A', 'B', 'C'],
            'Value': [10, 20, 30]
        })
        generator.add_chart_slide("Chart", 'bar', df, 'Category', ['Value'])
        
        # 保存
        output_path = self.test_output_dir / "integration_test.pptx"
        generator.save(str(output_path))
        
        # 验证
        self.assertTrue(output_path.exists())
        self.assertEqual(generator.get_slide_count(), 4)
    
    def test_outline_generation_and_save(self):
        """测试大纲生成并保存"""
        generator = PPTGenerator()
        outline = create_sample_outline()
        
        generator.generate_from_outline(outline)
        
        output_path = self.test_output_dir / "outline_test.pptx"
        generator.save(str(output_path))
        
        self.assertTrue(output_path.exists())
        self.assertGreater(generator.get_slide_count(), 0)


if __name__ == '__main__':
    # 运行测试
    unittest.main(verbosity=2)
