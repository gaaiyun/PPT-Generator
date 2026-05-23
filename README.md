# 📊 PPT 演示文稿生成器

根据大纲自动生成专业 PowerPoint 演示文稿的自动化工具 ✨

## ✨ 功能特性

### 1. 模板选择
- 🎨 **多种预设模板**：专业蓝色、活力红色、极简黑白、深色模式
- 🎯 **自定义模板**：支持创建和保存自定义模板
- 📋 **模板预览**：实时预览模板效果

### 2. 内容生成
- 📝 **大纲驱动**：根据结构化大纲自动生成幻灯片
- 🎯 **智能布局**：自动调整内容布局和格式
- 📄 **多种版式**：标题页、内容页、章节页、图片页

### 3. 图表插入
- 📊 **丰富图表**：柱状图、折线图、饼图、面积图
- 📈 **数据驱动**：支持 pandas DataFrame 数据
- 🎨 **自动美化**：智能配色和样式调整

### 4. 样式美化
- 🎨 **配色方案**：4 种预设配色方案
- 📐 **自动排版**：智能调整字体大小和间距
- 🌈 **一致性**：保持整体风格统一

### 5. 导出格式
- 📄 **PPTX**：标准 PowerPoint 格式
- 📕 **PDF**：可直接分享的 PDF 格式

## 🚀 快速开始

### 安装依赖

```bash
cd ppt-generator
pip install -r requirements.txt
```

### 运行应用

```bash
streamlit run dashboard.py
```

浏览器会自动打开 http://localhost:8501

### 使用示例

1. **选择模板**：在侧边栏选择喜欢的模板风格
2. **填写标题**：输入演示文稿标题和副标题
3. **编辑大纲**：添加章节和幻灯片内容
4. **配置图表**：为图表幻灯片编辑数据
5. **生成 PPT**：点击生成按钮，下载文件

## 📁 项目结构

```
ppt-generator/
├── dashboard.py          # Streamlit 主界面
├── ppt_generator.py      # PPT 生成核心模块
├── template_manager.py   # 模板管理模块
├── requirements.txt      # 依赖列表
├── README.md            # 说明文档
├── templates/           # 模板文件目录
│   ├── professional.pptx
│   ├── vibrant.pptx
│   ├── minimal.pptx
│   └── dark.pptx
├── output/              # 生成的文件输出目录
└── tests/               # 单元测试目录
    ├── test_ppt_generator.py
    └── test_template_manager.py
```

## 💻 编程接口

### 基本使用

```python
from ppt_generator import PPTGenerator, create_sample_outline

# 创建生成器
generator = PPTGenerator()

# 设置配色方案
generator.set_color_scheme('professional')

# 使用示例大纲生成
outline = create_sample_outline()
generator.generate_from_outline(outline)

# 保存文件
generator.save('output.pptx')
```

### 自定义大纲

```python
import pandas as pd

outline = {
    'title': '我的演示文稿',
    'subtitle': '副标题',
    'sections': [
        {
            'title': '第一部分',
            'slides': [
                {
                    'type': 'content',
                    'title': '内容页',
                    'content': ['要点 1', '要点 2', '要点 3']
                },
                {
                    'type': 'chart',
                    'title': '数据图表',
                    'chart_type': 'bar',
                    'data': pd.DataFrame({...}),
                    'x_column': '类别',
                    'y_columns': ['数值 1', '数值 2']
                }
            ]
        }
    ]
}
```

### 模板管理

```python
from template_manager import TemplateManager

manager = TemplateManager()

# 获取所有模板
templates = manager.get_template_list()

# 应用模板
prs = manager.apply_template('professional')

# 创建自定义模板
manager.create_custom_template(
    name='my_template',
    color_scheme={
        'primary': '#FF0000',
        'secondary': '#00FF00',
        'accent': '#0000FF'
    },
    description='我的自定义模板'
)
```

## 🧪 测试

### 运行单元测试

```bash
cd ppt-generator
pytest tests/ -v --cov=. --cov-report=html
```

### 测试覆盖率

```bash
pytest tests/ --cov=. --cov-report=term-missing
```

目标：测试覆盖率 > 70%

### 手动测试

1. 运行 `streamlit run dashboard.py`
2. 测试所有 UI 功能
3. 生成测试 PPT 验证功能
4. 检查导出文件质量

## 🎨 配色方案

| 方案名称 | 主色 | 辅色 | 强调色 | 适用场景 |
|---------|------|------|--------|---------|
| professional | #2980B9 | #34495E | #E67E22 | 商务报告 |
| vibrant | #E74C3C | #3498DB | #F1C40F | 产品发布 |
| minimal | #000000 | #808080 | #008080 | 学术报告 |
| dark | #3498DB | #9B59B6 | #F1C40F | 科技演示 |

## 📊 图表类型支持

- ✅ 柱状图 (bar)
- ✅ 折线图 (line)
- ✅ 饼图 (pie)
- ✅ 面积图 (area)

## 🔧 技术栈

- **前端界面**: Streamlit
- **PPT 生成**: python-pptx
- **数据处理**: pandas
- **图表绘制**: plotly
- **PDF 导出**: comtypes (Windows)

## 📝 待开发功能

- [ ] 更多图表类型（散点图、雷达图等）
- [ ] 动画效果支持
- [ ] 批量生成
- [ ] 云端模板库
- [ ] AI 辅助内容生成
- [ ] 主题导出/导入
- [ ] 协作编辑

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

MIT License

## 👾 关于

Created with ❤️ by Paimon ✨

---

**派蒙提示**: 如有问题或建议，随时联系派蒙哦~ 🌟
