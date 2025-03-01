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
        lines = Path(md_path).read_text(encoding='utf-8').split('\n')
        
        in_code = False
        code_lines = []
        code_lang = ""
        in_list = False
        list_items = []
        in_table = False
        table_headers = []
        table_align = []
        table_rows = []

        for line in lines:
            if line.startswith('```'):
                if in_code:
                    self._add_code_block(code_lines, code_lang)
                    code_lines = []
                    code_lang = ""
                    in_code = False
                else:
                    code_lang = line[3:].strip()
                    in_code = True
                continue
            
            if in_code:
                code_lines.append(line)
                continue
            
            if re.match(r'^\|.+\|$', line) and not in_code:
                if not in_table:
                    in_table = True
                    table_headers = []
                    table_align = []
                    table_rows = []
                
                if re.match(r'^\|[-: ]+[-|: ]+\|$', line):
                    cells = [c.strip() for c in line[1:-1].split('|')]
                    for cell in cells:
                        if re.match(r'^:-+:$', cell):
                            table_align.append('center')
                        elif re.match(r'^-+:$', cell):
                            table_align.append('right')
                        else:
                            table_align.append('left')
                    continue
                
                cells = [self._clean_table_cell(c) for c in line[1:-1].split('|')]
                if not table_headers:
                    table_headers = cells
                else:
                    table_rows.append(cells)
                continue
            else:
                if in_table:
                    self._add_table(table_headers, table_align, table_rows)
                    in_table = False
            
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
            
            if line.strip() and not in_list and not in_code and not in_table:
                self._add_paragraph(line.strip())
        
        self._finalize_current()
        if in_list:
            self._add_list(list_items)
        if in_table:
            self._add_table(table_headers, table_align, table_rows)
        
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(self.output, f, indent=2, ensure_ascii=False)

    def _clean_table_cell(self, text):
        return re.sub(r'\s+', ' ', text).strip()

    def _add_table(self, headers, align, rows):
        if headers and rows:
            target = self._get_current_content()
            target.append({
                "table": {
                    "headers": headers,
                    "align": align or ['left'] * len(headers),
                    "rows": rows
                }
            })

    def _add_paragraph(self, text):
        target = self._get_current_content()
        target.append(text)

    def _add_code_block(self, code_lines, lang):
        target = self._get_current_content()
        code_block = {
            "code": code_lines,
            "lang": lang
        }
        target.append(code_block)

    def _add_list(self, items):
        target = self._get_current_content()
        target.append({
            "notes": {
                "title": "💡",
                "items": items
            }
        })

    def _get_current_content(self):
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

if __name__ == "__main__":
    converter = MarkdownConverter()
    converter.convert("input.md", "config.json")
    blog_generator.BlogGenerator("template.html").generate("config.json", "output.html")