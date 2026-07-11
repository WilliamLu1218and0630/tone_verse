# -*- coding: utf-8 -*-
"""Build index.html from template.html + JSON data files."""
import pathlib

SRC = pathlib.Path(__file__).parent
ROOT = SRC.parent

template = (SRC / 'template.html').read_text(encoding='utf-8')

replacements = {
    '/*__DB__*/':    (SRC / 'chars_db.json').read_text(encoding='utf-8').strip(),
    '/*__EMB__*/':   (SRC / 'embeddings.json').read_text(encoding='utf-8').strip(),
    '/*__ANTO__*/':  (SRC / 'antonyms.json').read_text(encoding='utf-8').strip(),
    '/*__WORDS__*/': (SRC / 'words.json').read_text(encoding='utf-8').strip(),
}

html = template
for placeholder, data in replacements.items():
    html = html.replace(placeholder, data)

(ROOT / 'index.html').write_text(html, encoding='utf-8')
print('Built index.html')
