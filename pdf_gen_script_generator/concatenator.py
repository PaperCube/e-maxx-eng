import os
import shutil
import re
import typing
from os import path
from typing import *


def _remove_suffix(s: str, part: str) -> str:
    if s.endswith(part):
        return s[:-len(part)]
    return s


def add_script_command(file_name):
    global script
    pdf_file_name = _remove_suffix(file_name, '.md') + '.pdf'
    script.write(f'echo Writing {file_name}\n')
    script.write(f'pandoc {file_name} -o Output\\{pdf_file_name} {args}\n')


def extract_links(catalog):
    try:
        catalog = open(catalog, 'r', encoding='utf-8')
        yield 'index.md'
        for ln in catalog:
            for pattern in re.findall(r'\./(.*?).html', ln):
                yield pattern + ".md"
    finally:
        catalog.close()


def save_extracted_links(catalog, output_file):
    with open(output_file, 'w', encoding='utf-8') as output_file:
        for pattern in extract_links(catalog):
            output_file.write(pattern)
            output_file.write('\n')


def enumerate_entries(path_to_catalog):
    def replace_url_safe(s: str):
        return re.sub(r'[/\\]', '_', s)

    entry_ctr = 0
    with open(path_to_catalog, 'r', encoding='utf-8') as catalog:
        for entry in catalog:
            entry = entry.strip()
            entry_id_string = '%.03d' % entry_ctr
            yield entry, entry_id_string + "_" + replace_url_safe(entry)
            entry_ctr += 1


def read_file_content(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()


def fixup_latex_content(content: str) -> str:
    rc = re.compile
    # Attention! Use backslash for replacement designator instead of dollar sign
    replaces: List[Tuple[Pattern, str]] = [
        (rc(r'\\begin\{(align|eqnarray)}'), r'\\begin{aligned}'),
        (rc(r'\\end\{(align|eqnarray)}'), r'\\end{aligned}'),
        (rc(r'\\(left|right)\\\\'), r'\\\1\\'),
        (rc(r'\\lt'), r'\\leqslant'),
        (rc(r'\\gt'), r'\\geqslant'),
        (rc(r'\\\\#'), r'\\#'),
        (rc(r'\\\\\$'), r'\\$'),
        (rc(r'(```\w*) .*?((\r)?\n)'), r'\1\2')
    ]
    for pattern, replacement in replaces:
        content = re.sub(pattern, replacement, content)
    return content


def _to_int_or_else(s: str, otherwise: int) -> int:
    if s.isnumeric():
        return int(s)
    return otherwise


def main():
    try:
        os.mkdir(out)
    except IOError:
        pass
    # for f in os.listdir(out):
    #     if path.isfile(f):
    #         os.remove(f)
    skip_count = _to_int_or_else(input("skip...? "), 0)
    script.write('@echo off\n')

    for file_path, output_file_name in list(enumerate_entries(catalog_path))[skip_count:]:
        content = read_file_content(path.join(src, file_path))
        content = fixup_latex_content(content)
        with open(path.join(out, output_file_name), 'w', encoding='utf-8') as output_file:
            output_file.write(content)
            add_script_command(output_file_name)

    write_script_everything(skip_count)


def write_script_everything(skip_count):
    with open(path.join(out, 'script-all.bat'), 'w') as script_everything:
        script_everything.write('@echo off\n')
        script_everything.write('pandoc ')
        for file_path, output_file_name in list(enumerate_entries(catalog_path))[skip_count:]:
            script_everything.write(output_file_name + ' ')
        script_everything.write(f'-o Output\\_Merged.pdf {args}')


if __name__ == '__main__':
    base_dir = r'../'
    src = path.join(base_dir, 'src')
    out = path.join(base_dir, 'out-sequence')
    catalog_path = path.join(base_dir, 'catalog.txt')

    utf_encoding = {'encoding': 'utf-8'}

    args = '-s --toc --toc-depth=1 -V geometry:margin=0.8in'
    script = open(path.join(out, 'script.bat'), 'w')

    main()
