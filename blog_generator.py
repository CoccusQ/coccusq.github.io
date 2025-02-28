from datetime import datetime
import json
import re
from html import escape

class BlogGenerator:
    def __init__(self, template_path):
        with open(template_path, 'r', encoding='utf-8') as f:
            self.template = f.read()
        
    def generate(self, config_path, output_path):
        """主生成方法（支持独立Note）"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            if not config.get("title"):
                raise ValueError("配置文件中必须包含'title'字段")

            safe_title = escape(config["title"])
            self._process_basic_info(config, safe_title)
            
            sections_html = '\n'.join([self._build_section(s) for s in config.get("sections", [])])
            self.template = self.template.replace('<!-- sections -->', sections_html)
            
            self._process_navigation(config.get("previous_post"), config.get("next_post"))
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(self.template)
            print("博客生成成功！输出文件：", output_path)
            
        except json.JSONDecodeError:
            print("错误：配置文件格式不正确")
        except FileNotFoundError as e:
            print(f"文件未找到：{e}")
        except Exception as e:
            print(f"生成失败：{str(e)}")
    
    def _process_basic_info(self, config, title):
        """处理基础信息"""
        date_str = config.get("date") or datetime.now().strftime("%Y.%m.%d")
        replacements = {
            '<title>CoccusQ的网页模板</title>': f'<title>{title} - CoccusQ的博客</title>',
            'id="headline"></h1>': f'id="headline">{title}</h1>',
            '2025.2.28 Update': f'{date_str} Update'
        }
        for old, new in replacements.items():
            self.template = self.template.replace(old, new)

    def _build_section(self, section):
        """构建单个内容区块（修复独立Note问题）"""
        elements = [
            f'<section class="section">',
            f'<h2 class="section-title" id="{section.get("id", "")}">{escape(section["title"])}</h2>'
        ]
        
        if "content" in section:
            for item in section["content"]:
                # 处理独立Note
                if isinstance(item, dict) and "notes" in item:
                    elements.append(self._build_notes(item["notes"]))
                # 处理代码块（含关联Note）
                elif isinstance(item, dict) and "code" in item:
                    code_block = self._build_code_block(item["code"])
                    if "notes" in item:
                        code_block += self._build_notes(item["notes"])
                    elements.append(code_block)
                # 处理子章节
                elif isinstance(item, dict) and "subsection" in item:
                    elements.append(self._build_subsection(item["subsection"]))
                # 处理普通文本
                elif isinstance(item, str) and item.strip():
                    elements.append(f'<p>{self._parse_inline_code(item.strip())}</p>')
        else:
            # 兼容旧版格式
            if "paragraphs" in section:
                elements.extend([f'<p>{self._parse_inline_code(p.strip())}</p>' for p in section["paragraphs"] if p.strip()])
            if "subsections" in section:
                elements.extend([self._build_subsection(sub) for sub in section["subsections"]])
        
        elements.append('</section>')
        return '\n'.join(elements)

    def _build_code_block(self, code_content):
        """构建代码块"""
        if isinstance(code_content, list):
            code_str = '\n'.join(code_content)
        else:
            code_str = str(code_content)
        cleaned_code = escape(code_str.strip('\n'))
        return f'<pre class="language-c"><code>{cleaned_code}</code></pre>'

    def _build_notes(self, notes):
        """构建注释区块（增强稳定性）"""
        # 空值检查和默认值设置
        title = notes.get("title", "注意事项")
        items = notes.get("items", [])
        
        items_html = ''.join(f'<li>{escape(str(item))}</li>' for item in items)
        return f'''
        <div class="note">
            <strong>{escape(title)}</strong>
            <ul>{items_html}</ul>
        </div>
        '''

    def _build_subsection(self, sub):
        """构建子章节（支持嵌套Note）"""
        elements = [
            '<div class="subsection">',
            f'<h3 class="subsection-title">{escape(sub["title"])}</h3>'
        ]
        
        if "content" in sub:
            for item in sub["content"]:
                if isinstance(item, dict):
                    if "notes" in item:
                        elements.append(self._build_notes(item["notes"]))
                    elif "code" in item:
                        elements.append(self._build_code_block(item["code"]))
                    elif "subsection" in item:
                        elements.append(self._build_subsection(item["subsection"]))
                elif isinstance(item, str) and item.strip():
                    elements.append(f'<p>{self._parse_inline_code(item.strip())}</p>')
        else:
            if "code" in sub:
                elements.append(self._build_code_block(sub["code"]))
            if "notes" in sub:
                elements.append(self._build_notes(sub["notes"]))
        
        elements.append('</div>')
        return '\n'.join(elements)

    def _parse_inline_code(self, text):
        """解析行内代码"""
        return re.sub(
            r'`([^`]+?)`',
            lambda m: f'<code>{escape(m.group(1))}</code>',
            text
        )

    def _process_navigation(self, prev_post, next_post):
        """处理导航链接"""
        prev_html = self._build_nav_item(prev_post, 'left') if prev_post else ''
        next_html = self._build_nav_item(next_post, 'right') if next_post else ''
        
        nav_content = [
            '<div class="guide-grid">',
            prev_html,
            next_html,
            '</div>'
        ]
        self.template = self.template.replace(
            '<div class="guide-grid">\n        <!-- 索引部分占位符 -->\n    </div>',
            '\n'.join(nav_content)
        )

    def _build_nav_item(self, post, position):
        """构建导航项（增强安全性）"""
        if not post:
            return ''
        
        direction = {
            'left': ('« ', '上一篇'),
            'right': ('» ', '下一篇')
        }[position]
        
        return f'''
        <article class="guide-card">
            <div class="guide-card-{position}">
                <span class="guide-date">{direction[1]}</span>
                <a href="{escape(post["url"])}" class="guide-title-link">
                    <h2 class="guide-title">{direction[0]}{escape(post["title"])}</h2>
                </a>
            </div>
        </article>
        '''

if __name__ == "__main__":
    BlogGenerator("template.html").generate("config.json", "output.html")