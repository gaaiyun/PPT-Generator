"""
PPT Generator Dashboard - Streamlit 主界面
功能：提供用户友好的 PPT 生成界面
"""

import streamlit as st
import pandas as pd
import os
import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from ppt_generator import PPTGenerator, create_sample_outline
from template_manager import TemplateManager


# 页面配置
st.set_page_config(
    page_title="PPT 演示文稿生成器 ✨",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定义 CSS 样式
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #2980B9;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #7F8C8D;
        text-align: center;
        margin-bottom: 2rem;
    }
    .stButton>button {
        background-color: #2980B9;
        color: white;
        border: none;
        padding: 0.5rem 1rem;
        border-radius: 5px;
    }
    .stButton>button:hover {
        background-color: #3498DB;
    }
</style>
""", unsafe_allow_html=True)


def initialize_session_state():
    """初始化会话状态"""
    if 'outline' not in st.session_state:
        st.session_state.outline = {
            'title': '',
            'subtitle': '',
            'sections': []
        }
    if 'generated_file' not in st.session_state:
        st.session_state.generated_file = None
    if 'template_selected' not in st.session_state:
        st.session_state.template_selected = 'professional'


def render_header():
    """渲染页面头部"""
    st.markdown('<h1 class="main-header">📊 PPT 演示文稿生成器</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">根据大纲自动生成专业幻灯片 ✨</p>', unsafe_allow_html=True)


def render_sidebar():
    """渲染侧边栏"""
    with st.sidebar:
        st.header("⚙️ 设置")
        
        # 模板选择
        st.subheader("选择模板")
        template_manager = TemplateManager()
        templates = template_manager.get_template_list()
        
        template_options = {t['name']: t['id'] for t in templates}
        selected_template = st.selectbox(
            "模板风格",
            options=list(template_options.keys()),
            index=0
        )
        
        st.session_state.template_selected = template_options[selected_template]
        
        # 配色方案
        st.subheader("配色方案")
        color_schemes = {
            'professional': '专业蓝色',
            'vibrant': '活力红色',
            'minimal': '极简黑白',
            'dark': '深色模式'
        }
        
        selected_scheme = st.selectbox(
            "配色",
            options=list(color_schemes.keys()),
            index=0
        )
        
        # 导出选项
        st.subheader("导出格式")
        export_format = st.radio(
            "格式",
            options=['PPTX', 'PDF'],
            index=0
        )
        
        return {
            'template': st.session_state.template_selected,
            'color_scheme': selected_scheme,
            'export_format': export_format
        }


def render_title_section():
    """渲染标题部分"""
    st.header("📝 基本信息")
    
    col1, col2 = st.columns(2)
    
    with col1:
        title = st.text_input("演示文稿标题", 
                             placeholder="例如：2024 年度业务报告",
                             value=st.session_state.outline.get('title', ''))
    
    with col2:
        subtitle = st.text_input("副标题",
                                placeholder="例如：业绩总结与展望",
                                value=st.session_state.outline.get('subtitle', ''))
    
    st.session_state.outline['title'] = title
    st.session_state.outline['subtitle'] = subtitle


def render_section_editor():
    """渲染章节编辑器"""
    st.header("📋 大纲编辑")
    
    # 添加新章节
    if st.button("➕ 添加新章节"):
        if 'sections' not in st.session_state.outline:
            st.session_state.outline['sections'] = []
        
        st.session_state.outline['sections'].append({
            'title': f'第{len(st.session_state.outline["sections"]) + 1}部分',
            'slides': []
        })
        st.rerun()
    
    # 编辑现有章节
    if 'sections' in st.session_state.outline and st.session_state.outline['sections']:
        for i, section in enumerate(st.session_state.outline['sections']):
            with st.expander(f"📁 {section.get('title', f'部分{i+1}')}", expanded=True):
                # 章节标题编辑
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    section_title = st.text_input(
                        "章节标题",
                        value=section.get('title', ''),
                        key=f"section_title_{i}"
                    )
                    st.session_state.outline['sections'][i]['title'] = section_title
                
                with col2:
                    if st.button("🗑️ 删除章节", key=f"delete_section_{i}"):
                        st.session_state.outline['sections'].pop(i)
                        st.rerun()
                
                # 添加幻灯片
                if st.button("➕ 添加幻灯片", key=f"add_slide_{i}"):
                    if 'slides' not in section:
                        section['slides'] = []
                    
                    section['slides'].append({
                        'type': 'content',
                        'title': f'新幻灯片',
                        'content': ['要点 1', '要点 2']
                    })
                    st.rerun()
                
                # 编辑幻灯片
                if 'slides' in section and section['slides']:
                    for j, slide in enumerate(section['slides']):
                        with st.container():
                            st.markdown(f"**幻灯片 {j+1}**")
                            
                            # 幻灯片类型
                            slide_type = st.selectbox(
                                "类型",
                                options=['content', 'chart', 'image'],
                                index=['content', 'chart', 'image'].index(slide.get('type', 'content')),
                                key=f"slide_type_{i}_{j}"
                            )
                            st.session_state.outline['sections'][i]['slides'][j]['type'] = slide_type
                            
                            # 幻灯片标题
                            slide_title = st.text_input(
                                "标题",
                                value=slide.get('title', ''),
                                key=f"slide_title_{i}_{j}"
                            )
                            st.session_state.outline['sections'][i]['slides'][j]['title'] = slide_title
                            
                            # 根据类型显示不同编辑器
                            if slide_type == 'content':
                                content_text = st.text_area(
                                    "内容（每行一个要点）",
                                    value='\n'.join(slide.get('content', [])),
                                    key=f"slide_content_{i}_{j}"
                                )
                                st.session_state.outline['sections'][i]['slides'][j]['content'] = content_text.split('\n')
                            
                            elif slide_type == 'chart':
                                chart_col1, chart_col2 = st.columns(2)
                                
                                with chart_col1:
                                    chart_type = st.selectbox(
                                        "图表类型",
                                        options=['bar', 'line', 'pie', 'area'],
                                        index=0,
                                        key=f"chart_type_{i}_{j}"
                                    )
                                    st.session_state.outline['sections'][i]['slides'][j]['chart_type'] = chart_type
                                
                                with chart_col2:
                                    st.info("图表数据将在下一步配置")
                            
                            elif slide_type == 'image':
                                image_path = st.text_input(
                                    "图片路径",
                                    value=slide.get('image_path', ''),
                                    key=f"image_path_{i}_{j}"
                                )
                                st.session_state.outline['sections'][i]['slides'][j]['image_path'] = image_path
                                
                                caption = st.text_input(
                                    "图片说明",
                                    value=slide.get('caption', ''),
                                    key=f"image_caption_{i}_{j}"
                                )
                                st.session_state.outline['sections'][i]['slides'][j]['caption'] = caption
                            
                            # 删除幻灯片按钮
                            if st.button("🗑️ 删除", key=f"delete_slide_{i}_{j}"):
                                section['slides'].pop(j)
                                st.rerun()
                            
                            st.divider()
    
    # 使用示例大纲
    if st.button("📖 加载示例大纲"):
        st.session_state.outline = create_sample_outline()
        st.rerun()


def render_chart_data_editor():
    """渲染图表数据编辑器"""
    st.header("📊 图表数据配置")
    
    if 'sections' in st.session_state.outline:
        for i, section in enumerate(st.session_state.outline['sections']):
            if 'slides' in section:
                for j, slide in enumerate(section['slides']):
                    if slide.get('type') == 'chart':
                        with st.expander(f"📈 {slide.get('title', f'图表{i}-{j}')}"):
                            # 创建示例数据
                            default_data = pd.DataFrame({
                                '类别': ['A', 'B', 'C', 'D'],
                                '数值 1': [10, 20, 15, 25],
                                '数值 2': [8, 15, 12, 20]
                            })
                            
                            edited_df = st.data_editor(
                                default_data,
                                num_rows="dynamic",
                                key=f"chart_data_{i}_{j}"
                            )
                            
                            # 保存数据到 outline
                            st.session_state.outline['sections'][i]['slides'][j]['data'] = edited_df
                            st.session_state.outline['sections'][i]['slides'][j]['x_column'] = edited_df.columns[0]
                            st.session_state.outline['sections'][i]['slides'][j]['y_columns'] = edited_df.columns[1:].tolist()


def generate_ppt(settings):
    """生成 PPT"""
    try:
        # 创建生成器
        template_path = None
        if settings['template']:
            template_manager = TemplateManager()
            template_path = template_manager.get_template(settings['template'])
        
        generator = PPTGenerator(template_path)
        generator.set_color_scheme(settings['color_scheme'])
        
        # 从大纲生成
        generator.generate_from_outline(st.session_state.outline)
        
        # 保存文件
        output_dir = project_root / "output"
        output_dir.mkdir(exist_ok=True)
        
        filename = st.session_state.outline.get('title', 'presentation').replace('/', '_').replace('\\', '_')
        
        if settings['export_format'] == 'PDF':
            output_path = output_dir / f"{filename}.pdf"
            generator.save_as_pdf(str(output_path))
        else:
            output_path = output_dir / f"{filename}.pptx"
            generator.save(str(output_path))
        
        return str(output_path), generator.get_slide_count()
    
    except Exception as e:
        st.error(f"生成失败：{str(e)}")
        return None, 0


def render_generation_section():
    """渲染生成部分"""
    st.header("🎨 生成演示文稿")
    
    col1, col2, col3 = st.columns([2, 1, 2])
    
    with col2:
        if st.button("✨ 生成 PPT", type="primary", use_container_width=True):
            with st.spinner("派蒙正在生成 PPT..."):
                settings = {
                    'template': st.session_state.template_selected,
                    'color_scheme': 'professional',  # 从侧边栏获取
                    'export_format': 'PPTX'  # 从侧边栏获取
                }
                
                # 从侧边栏获取实际值（需要重新设计状态管理）
                output_path, slide_count = generate_ppt(settings)
                
                if output_path:
                    st.session_state.generated_file = output_path
                    st.success(f"✅ 生成成功！共 {slide_count} 张幻灯片")
    
    # 显示生成的文件
    if st.session_state.generated_file:
        st.success(f"📁 文件已保存至：{st.session_state.generated_file}")
        
        # 下载按钮
        with open(st.session_state.generated_file, "rb") as file:
            st.download_button(
                label="📥 下载 PPT 文件",
                data=file,
                file_name=os.path.basename(st.session_state.generated_file),
                mime="application/vnd.openxmlformats-officedocument.presentationml.presentation"
            )


def render_preview():
    """渲染预览部分"""
    st.header("👁️ 预览")
    
    if st.session_state.outline.get('title'):
        st.info(f"**标题**: {st.session_state.outline['title']}")
        
        if st.session_state.outline.get('subtitle'):
            st.info(f"**副标题**: {st.session_state.outline['subtitle']}")
        
        if 'sections' in st.session_state.outline:
            total_slides = 0
            for section in st.session_state.outline['sections']:
                slide_count = len(section.get('slides', []))
                total_slides += slide_count
                st.write(f"📁 **{section.get('title', '未命名')}**: {slide_count} 张幻灯片")
            
            st.success(f"📊 总计：{total_slides + 1} 张幻灯片（含封面）")
    else:
        st.warning("请先填写演示文稿标题")


def main():
    """主函数"""
    # 初始化
    initialize_session_state()
    
    # 渲染页面
    render_header()
    
    # 侧边栏设置
    settings = render_sidebar()
    
    # 主要内容区
    render_title_section()
    
    st.divider()
    
    render_section_editor()
    
    st.divider()
    
    render_chart_data_editor()
    
    st.divider()
    
    render_generation_section()
    
    st.divider()
    
    render_preview()
    
    # 页脚
    st.divider()
    st.markdown("""
    <div style='text-align: center; color: #7F8C8D; padding: 1rem;'>
        <p>Created with ❤️ by Paimon | Powered by Streamlit & python-pptx</p>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
