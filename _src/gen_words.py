# -*- coding: utf-8 -*-
"""
tone_verse 詞庫生成器（偷懶版「查多字詞彙」用）
- wordfreq 中文詞頻表取常用詞
- OpenCC s2t 轉繁
- 只留長度 >=2、且「每個字都在現有單字庫 chars_db.json」的詞
  （聲調／注音／聲母／韻母／字向量全部 runtime 從單字庫推）
- jieba.posseg 標詞性 → n 名詞 / v 動詞 / a 形容詞 / o 其他
輸出 words.json：[{w, p}] 物件陣列，依詞頻由高到低排序。
"""
import json, sys, io, logging
from collections import Counter
from wordfreq import top_n_list, zipf_frequency
from opencc import OpenCC
from pypinyin import pinyin, Style

logging.getLogger('jieba').setLevel(logging.ERROR)
import jieba.posseg as pseg

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

s2t = OpenCC('s2t')

# 載入單字庫，取得合法字集合（詞的每個字都必須在此集合）
with open('chars_db.json', encoding='utf-8') as fp:
    CHAR_SET = {c['c'] for c in json.load(fp)['chars']}

N_SCAN = 60000       # 掃描 wordfreq 前 N 高頻詞
ZIPF_MIN = 2.3       # 詞頻門檻

def flag_to_cat(f):
    """jieba POS flag → n/v/a/o"""
    if f.startswith('n') or f in ('t', 's', 'f'):
        return 'n'
    if f.startswith('v'):
        return 'v'
    if f.startswith('a') or f in ('b', 'z'):
        return 'a'
    return 'o'

def analyze_word(w_simplified):
    """簡體詞 → (詞性類別 n/v/a/o, 是否專有名詞)"""
    segs = list(pseg.cut(w_simplified))
    if not segs:
        return 'o', False
    cats = [flag_to_cat(s.flag) for s in segs]
    pos = Counter(cats).most_common(1)[0][0]
    pn = any(s.flag in ('nr', 'ns', 'nt', 'nrt', 'nz') for s in segs)
    return pos, pn

def get_word_tones(w_simplified):
    """用 pypinyin 詞組模式取每字聲調（比查單字主讀更準：假期→[4,1] 而非 [3,1]）"""
    py = pinyin(w_simplified, style=Style.TONE3, heteronym=False)
    if len(py) != len(w_simplified):
        return None
    tones = []
    for syllable in py:
        s = syllable[0]
        if s and s[-1].isdigit():
            tones.append(int(s[-1]))
        else:
            tones.append(5)
    return tones

seen = set()
words = []           # [(f, w0_simplified, w_traditional)]
for w0 in top_n_list('zh', N_SCAN):
    w = s2t.convert(w0)
    if len(w) < 2:           # 只要多字詞
        continue
    if w in seen:
        continue
    if any(ch not in CHAR_SET for ch in w):   # 每字須在單字庫
        continue
    f = zipf_frequency(w, 'zh')
    if f < ZIPF_MIN:
        continue
    seen.add(w)
    words.append((f, w0, w))

words.sort(key=lambda x: -x[0])

print('標詞性中（jieba）…')
word_list = []
for _, w0, w in words:
    p, pn = analyze_word(w0)
    t = get_word_tones(w0)
    entry = {'w': w, 'p': p}
    if t and len(t) == len(w):
        entry['t'] = t
    if pn:
        entry['pn'] = 1
    word_list.append(entry)

out = {
    'meta': {
        'desc': 'tone_verse 詞庫（{w,p} 物件陣列，依詞頻排序；聲調/注音 runtime 從單字庫推）',
        'pos_legend': {'n': '名詞', 'v': '動詞', 'a': '形容詞', 'o': '其他'},
        'zipf_min': ZIPF_MIN,
        'count': len(word_list),
    },
    'words': word_list,
}
with open('words.json', 'w', encoding='utf-8') as fp:
    json.dump(out, fp, ensure_ascii=False, separators=(',', ':'))

# 統計
lc = Counter(len(x['w']) for x in word_list)
pc = Counter(x['p'] for x in word_list)
print('詞數:', len(word_list))
print('各長度詞數:', dict(sorted(lc.items())))
print('各詞性詞數:', dict(sorted(pc.items())))
print('範例(高頻):', [x['w'] for x in word_list[:20]])
