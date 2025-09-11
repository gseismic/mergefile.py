import sys
import os
import argparse
from xml.sax.saxutils import escape

def merge_files(input_files, output_file, header=None, format_type='xml'):
    """
    将多个文件合并到一个输出文件中
    :param input_files: 输入文件路径列表
    :param output_file: 输出文件路径
    :param header: 自定义头部注释
    :param format_type: 输出格式 ('xml' 或 'markdown')
    """
    try:
        with open(output_file, 'w', encoding='utf-8') as out_f:
            if format_type == 'xml':
                _write_xml_format(out_f, input_files, header)
            else:  # markdown
                _write_markdown_format(out_f, input_files, header)
        
        print(f"成功合并 {len(input_files)} 个文件到 {output_file} (格式: {format_type})")
    except Exception as e:
        print(f"写入输出文件时出错: {str(e)}")

def _write_xml_format(out_f, input_files, header):
    """写入XML格式"""
    # 写入XML头部
    out_f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
    out_f.write('<file_documentation>\n')
    
    # 添加自定义头部
    if header:
        out_f.write(f'  <description>\n')
        out_f.write(f'    {escape(header)}\n')
        out_f.write(f'  </description>\n\n')
    
    # 添加文件列表
    out_f.write('  <file_list>\n')
    for i, file_path in enumerate(input_files, 1):
        out_f.write(f'    <item index="{i}" path="{escape(file_path)}" name="{escape(os.path.basename(file_path))}" />\n')
    out_f.write('  </file_list>\n\n')
    
    # 处理每个输入文件内容
    out_f.write('  <file_contents>\n')
    for file_path in input_files:
        file_name = os.path.basename(file_path)
        out_f.write(f'    <file name="{escape(file_name)}" path="{escape(file_path)}">\n')
        
        try:
            with open(file_path, 'r', encoding='utf-8') as in_f:
                content = in_f.read()
                # 使用CDATA包裹内容，避免XML解析问题 
                out_f.write('      <![CDATA[\n') 
                out_f.write(content) 
                if not content.endswith('\n'):
                    out_f.write('\n')
                out_f.write('      ]]>\n')
        except FileNotFoundError:
            print(f"警告: 文件 {file_path} 不存在，已跳过")
            out_f.write('      <error>文件不存在</error>\n')
        except UnicodeDecodeError:
            print(f"错误: 文件 {file_path} 解码失败，请检查编码格式")
            out_f.write('      <error>编码错误</error>\n')
        
        out_f.write('    </file>\n')
    out_f.write('  </file_contents>\n')
    
    out_f.write('</file_documentation>')

def _write_markdown_format(out_f, input_files, header):
    """写入Markdown格式"""
    out_f.write('# 文件说明\n\n')
    
    # 添加自定义头部
    if header:
        out_f.write(f'{header}\n\n')
    
    out_f.write('## 文件列表\n\n')
    out_f.write('文件列表如下:\n\n')
    for i, file_path in enumerate(input_files, 1):
        out_f.write(f'{i}. `{file_path}`\n')
    out_f.write('\n## 文件内容\n\n')
    out_f.write('各文件内容详见下方:\n\n')
    out_f.write('---\n\n')
    
    # 处理每个输入文件
    for file_path in input_files:
        file_name = os.path.basename(file_path)
        out_f.write(f'### {file_name}\n\n')
        out_f.write(f'文件路径: `{file_path}`\n\n')
        
        try:
            with open(file_path, 'r', encoding='utf-8') as in_f:
                content = in_f.read()
                # 根据文件扩展名确定代码块语言
                _, ext = os.path.splitext(file_name)
                lang = _get_language_by_extension(ext)
                out_f.write(f'```{lang}\n')
                out_f.write(content)
                if not content.endswith('\n'):
                    out_f.write('\n')
                out_f.write('```\n\n')
        except FileNotFoundError:
            print(f"警告: 文件 {file_path} 不存在，已跳过")
            out_f.write('文件不存在\n\n')
        except UnicodeDecodeError:
            print(f"错误: 文件 {file_path} 解码失败，请检查编码格式")
            out_f.write('编码错误\n\n')

def _get_language_by_extension(ext):
    """根据文件扩展名返回代码块语言标识"""
    language_map = {
        '.py': 'python',
        '.js': 'javascript', 
        '.ts': 'typescript',
        '.java': 'java',
        '.cpp': 'cpp',
        '.c': 'c',
        '.h': 'c',
        '.cs': 'csharp',
        '.php': 'php',
        '.rb': 'ruby',
        '.go': 'go',
        '.rs': 'rust',
        '.swift': 'swift',
        '.kt': 'kotlin',
        '.scala': 'scala',
        '.r': 'r',
        '.sql': 'sql',
        '.html': 'html',
        '.css': 'css',
        '.scss': 'scss',
        '.sass': 'sass',
        '.xml': 'xml',
        '.json': 'json',
        '.yaml': 'yaml',
        '.yml': 'yaml',
        '.toml': 'toml',
        '.ini': 'ini',
        '.cfg': 'ini',
        '.conf': 'ini',
        '.sh': 'bash',
        '.bash': 'bash',
        '.zsh': 'zsh',
        '.fish': 'fish',
        '.ps1': 'powershell',
        '.bat': 'batch',
        '.cmd': 'batch',
        '.dockerfile': 'dockerfile',
        '.md': 'markdown',
        '.tex': 'latex',
        '.csv': 'csv',
        '.tsv': 'csv',
    }
    return language_map.get(ext.lower(), 'text')

def main():
    parser = argparse.ArgumentParser(
        description='合并多个文件到XML格式，适合提供给大模型阅读',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  mergefile 1.py 2.csv data/xx.py output.xml
  mergefile --header "这是我的项目代码" src/*.py merged.xml
  mergefile --header "数据文件合并" data.csv config.json result.xml
        """
    )
    parser.add_argument('files', nargs='+', help='输入文件列表，最后一个参数是输出文件')
    parser.add_argument('--header', help='添加自定义头部注释')
    parser.add_argument('--format', choices=['xml', 'markdown'], default='markdown', 
                       help='输出格式 (默认: markdown)')
    
    args = parser.parse_args()
    
    if len(args.files) < 2:
        parser.error("至少需要一个输入文件和一个输出文件")
    
    # 最后一个参数是输出文件，其余是输入文件
    input_files = args.files[:-1]
    output_file = args.files[-1]
    
    merge_files(input_files, output_file, args.header, args.format)

if __name__ == "__main__":
    main()