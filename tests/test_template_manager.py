"""
Template Manager 单元测试
测试覆盖率目标：> 70%
"""

import unittest
import os
import sys
import json
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from template_manager import TemplateManager, get_available_templates


class TestTemplateManager(unittest.TestCase):
    """TemplateManager 测试类"""
    
    def setUp(self):
        """测试前准备"""
        self.test_template_dir = project_root / "test_templates"
        self.test_template_dir.mkdir(exist_ok=True)
        self.manager = TemplateManager(str(self.test_template_dir))
    
    def tearDown(self):
        """测试后清理"""
        # 清理测试文件
        for file in self.test_template_dir.glob("*.pptx"):
            file.unlink()
        for file in self.test_template_dir.glob("*.json"):
            file.unlink()
        self.test_template_dir.rmdir()
    
    def test_init(self):
        """测试初始化"""
        manager = TemplateManager(str(self.test_template_dir))
        self.assertIsNotNone(manager.template_dir)
        self.assertIsInstance(manager.templates, dict)
    
    def test_init_creates_default_templates(self):
        """测试初始化时创建默认模板"""
        # 默认应该创建 4 个模板
        self.assertGreaterEqual(len(self.manager.templates), 4)
    
    def test_load_templates(self):
        """测试加载模板"""
        # 创建测试模板文件
        test_template = self.test_template_dir / "test_template.pptx"
        test_template.touch()
        
        # 重新加载
        self.manager.load_templates()
        
        self.assertIn('test_template', self.manager.templates)
    
    def test_get_template_list(self):
        """测试获取模板列表"""
        templates = self.manager.get_template_list()
        
        self.assertIsInstance(templates, list)
        self.assertGreater(len(templates), 0)
        
        # 验证模板结构
        for template in templates:
            self.assertIn('id', template)
            self.assertIn('name', template)
            self.assertIn('description', template)
            self.assertIn('path', template)
    
    def test_get_template(self):
        """测试获取模板路径"""
        templates = self.manager.get_template_list()
        
        if templates:
            template_id = templates[0]['id']
            template_path = self.manager.get_template(template_id)
            
            self.assertIsNotNone(template_path)
            self.assertTrue(os.path.exists(template_path))
    
    def test_get_template_not_found(self):
        """测试获取不存在的模板"""
        template_path = self.manager.get_template('non_existent_template')
        self.assertIsNone(template_path)
    
    def test_apply_template(self):
        """测试应用模板"""
        templates = self.manager.get_template_list()
        
        if templates:
            template_id = templates[0]['id']
            prs = self.manager.apply_template(template_id)
            
            self.assertIsNotNone(prs)
    
    def test_apply_template_not_found(self):
        """测试应用不存在的模板"""
        prs = self.manager.apply_template('non_existent_template')
        self.assertIsNone(prs)
    
    def test_preview_template(self):
        """测试预览模板"""
        templates = self.manager.get_template_list()
        
        if templates:
            template_id = templates[0]['id']
            preview = self.manager.preview_template(template_id)
            
            self.assertNotIn('error', preview)
            self.assertIn('name', preview)
            self.assertIn('slide_count', preview)
            self.assertIn('slide_layouts', preview)
    
    def test_preview_template_not_found(self):
        """测试预览不存在的模板"""
        preview = self.manager.preview_template('non_existent_template')
        
        self.assertIn('error', preview)
    
    def test_delete_template(self):
        """测试删除模板"""
        # 创建测试模板
        test_template = self.test_template_dir / "to_delete.pptx"
        test_template.touch()
        
        test_metadata = self.test_template_dir / "to_delete.json"
        with open(test_metadata, 'w') as f:
            json.dump({'name': 'to_delete'}, f)
        
        # 重新加载
        self.manager.load_templates()
        
        # 删除
        result = self.manager.delete_template('to_delete')
        
        self.assertTrue(result)
        self.assertNotIn('to_delete', self.manager.templates)
    
    def test_delete_template_not_found(self):
        """测试删除不存在的模板"""
        result = self.manager.delete_template('non_existent_template')
        self.assertFalse(result)
    
    def test_create_custom_template(self):
        """测试创建自定义模板"""
        color_scheme = {
            'primary': '#FF0000',
            'secondary': '#00FF00',
            'accent': '#0000FF',
            'background': '#FFFFFF'
        }
        
        template_path = self.manager.create_custom_template(
            name='custom_test',
            color_scheme=color_scheme,
            description='Test custom template'
        )
        
        self.assertTrue(os.path.exists(template_path))
        self.assertIn('custom_test', self.manager.templates)
        
        # 验证元数据
        metadata_path = self.test_template_dir / "custom_test.json"
        self.assertTrue(os.path.exists(metadata_path))
    
    def test_create_custom_template_with_rgb(self):
        """测试使用 RGB 值创建自定义模板"""
        from pptx.dml.color import RGBColor
        
        color_scheme = {
            'primary': RGBColor(255, 0, 0),
            'secondary': RGBColor(0, 255, 0),
            'accent': RGBColor(0, 0, 255),
            'background': RGBColor(255, 255, 255)
        }
        
        template_path = self.manager.create_custom_template(
            name='custom_rgb',
            color_scheme=color_scheme,
            description='RGB custom template'
        )
        
        self.assertTrue(os.path.exists(template_path))
    
    def test_template_metadata_structure(self):
        """测试模板元数据结构"""
        templates = self.manager.get_template_list()
        
        for template in templates:
            self.assertIn('name', template)
            self.assertIn('description', template)
            self.assertIn('style', template)
            self.assertIn('id', template)
            self.assertIn('path', template)
    
    def test_default_templates_exist(self):
        """测试默认模板存在"""
        expected_templates = ['professional', 'vibrant', 'minimal', 'dark']
        
        templates = self.manager.get_template_list()
        template_ids = [t['id'] for t in templates]
        
        for expected in expected_templates:
            self.assertIn(expected, template_ids)


class TestGetAvailableTemplates(unittest.TestCase):
    """get_available_templates 函数测试"""
    
    def test_get_available_templates(self):
        """测试获取可用模板"""
        templates = get_available_templates()
        
        self.assertIsInstance(templates, list)
        self.assertGreater(len(templates), 0)


class TestTemplateManagerIntegration(unittest.TestCase):
    """TemplateManager 集成测试"""
    
    def setUp(self):
        """测试前准备"""
        self.test_template_dir = project_root / "test_templates_integration"
        self.test_template_dir.mkdir(exist_ok=True)
    
    def tearDown(self):
        """测试后清理"""
        for file in self.test_template_dir.glob("*.pptx"):
            file.unlink()
        for file in self.test_template_dir.glob("*.json"):
            file.unlink()
        self.test_template_dir.rmdir()
    
    def test_full_workflow(self):
        """测试完整工作流程"""
        # 创建管理器
        manager = TemplateManager(str(self.test_template_dir))
        
        # 获取模板列表
        templates = manager.get_template_list()
        self.assertGreater(len(templates), 0)
        
        # 创建自定义模板
        custom_path = manager.create_custom_template(
            name='workflow_test',
            color_scheme={
                'primary': '#123456',
                'secondary': '#654321',
                'accent': '#ABCDEF'
            },
            description='Workflow test template'
        )
        
        # 验证创建
        self.assertTrue(os.path.exists(custom_path))
        
        # 预览模板
        preview = manager.preview_template('workflow_test')
        self.assertNotIn('error', preview)
        
        # 应用模板
        prs = manager.apply_template('workflow_test')
        self.assertIsNotNone(prs)
        
        # 删除模板
        result = manager.delete_template('workflow_test')
        self.assertTrue(result)
        
        # 验证删除
        self.assertFalse(os.path.exists(custom_path))


if __name__ == '__main__':
    # 运行测试
    unittest.main(verbosity=2)
