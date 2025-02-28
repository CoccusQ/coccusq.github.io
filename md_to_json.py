import json
import re
from pathlib import Path
import blog_generator

class MarkdownConverter:
    def __init__(self):
        self.output = {
            "title": "",
            "sections": []
        }
        self.current_section = None
        self.current_subsection = None

    def convert(self, md_path, json_path):
        """主转换方法"""
        lines = Path(md_path).read_text(encoding='utf-8').split('\n')
        
        # 状态跟踪
        in_code = False
        code_lines = []
        code_lang = ""
        in_list = False
        list_items = []
        
        for line in lines:
            # 处理代码块
            if line.startswith('```'):
                if in_code:
                    # 结束代码块
                    self._add_code_block(code_lines, code_lang)
                    code_lines = []
                    code_lang = ""
                    in_code = False
                else:
                    # 开始代码块
                    code_lang = line[3:].strip()
                    in_code = True
                continue
            
            if in_code:
                code_lines.append(line)
                continue
            
            # 处理标题
            header_match = re.match(r'^(#{1,3})\s+(.+)', line)
            if header_match:
                level = len(header_match.group(1))
                text = header_match.group(2).strip()
                
                if level == 1:
                    self.output["title"] = text
                elif level == 2:
                    self._finalize_current()
                    self.current_section = {
                        "id": text,
                        "title": text,
                        "content": []
                    }
                elif level == 3:
                    self._finalize_current()
                    self.current_subsection = {
                        "id": text,
                        "title": text,
                        "content": []
                    }
                continue
            
            # 处理列表
            if re.match(r'^\s*[-*+] ', line):
                if not in_list:
                    list_items = []
                    in_list = True
                list_items.append(re.sub(r'^\s*[-*+] ', '', line).strip())
                continue
            else:
                if in_list:
                    self._add_list(list_items)
                    list_items = []
                    in_list = False
            
            # 处理普通段落
            if line.strip() and not in_list and not in_code:
                self._add_paragraph(line.strip())
        
        # 处理未关闭的状态
        self._finalize_current()
        if in_list:
            self._add_list(list_items)
        
        # 保存结果
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(self.output, f, indent=2, ensure_ascii=False)

    def _add_paragraph(self, text):
        """添加段落"""
        target = self._get_current_content()
        target.append(text)

    def _add_code_block(self, code_lines, lang):
        """添加代码块"""
        target = self._get_current_content()
        code_block = {
            "code": code_lines
        }
        if lang:
            code_block["notes"] = {
                "title": "语言说明",
                "items": [f"编程语言: {lang}"]
            }
        target.append({"code": code_lines})

    def _add_list(self, items):
        """添加列表为note"""
        target = self._get_current_content()
        target.append({
            "notes": {
                "title": "要点说明",
                "items": items
            }
        })

    def _get_current_content(self):
        """获取当前内容容器"""
        if self.current_subsection:
            return self.current_subsection.setdefault("content", [])
        elif self.current_section:
            return self.current_section.setdefault("content", [])
        elif self.output["sections"]:
            return self.output["sections"][-1].setdefault("content", [])
        else:
            new_section = {"title": "", "content": []}
            self.output["sections"].append(new_section)
            return new_section["content"]

    def _finalize_current(self):
        """结束当前层级"""
        if self.current_subsection:
            if self.current_section:
                self.current_section.setdefault("subsections", []).append(self.current_subsection)
            else:
                new_section = {"title": "", "subsections": [self.current_subsection]}
                self.output["sections"].append(new_section)
            self.current_subsection = None
        elif self.current_section:
            self.output["sections"].append(self.current_section)
            self.current_section = None

# 使用示例
if __name__ == "__main__":
    converter = MarkdownConverter()
    converter.convert("input.md", "config.json")
    blog_generator.BlogGenerator("template.html").generate("config.json", "output.html")