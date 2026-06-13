# -*- coding: utf-8 -*-
"""
tone_verse 詞庫生成器（偷懶版「查多字詞彙」用）
- wordfreq 中文詞頻表取常用詞
- OpenCC s2t 轉繁
- 只留長度 >=2、且「每個字都在現有單字庫 chars_db.json」的詞
  （聲調／注音／聲母／韻母／字向量全部 runtime 從單字庫推）
輸出 words.json：純詞字串陣列，依詞頻由高到低排序（陣列順序即頻序，不另存 f）。
"""
import json, sys, io
from wordfreq import top_n_list, zipf_frequency
from opencc import OpenCC

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

s2t = OpenCC('s2t')

# 載入單字庫，取得合法字集合（詞的每個字都必須在此集合）
with open('chars_db.json', encoding='utf-8') as fp:
    CHAR_SET = {c['c'] for c in json.load(fp)['chars']}

N_SCAN = 60000       # 掃描 wordfreq 前 N 高頻詞
ZIPF_MIN = 2.3       # 詞頻門檻

seen = set()
words = []           # [(f, w)]，最後排序後只輸出 w
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
    words.append((f, w))

words.sort(key=lambda x: -x[0])
word_list = [w for _, w in words]
out = {
    'meta': {
        'desc': 'tone_verse 詞庫（陣列順序即頻序；聲調/注音 runtime 從單字庫推）',
        'zipf_min': ZIPF_MIN,
        'count': len(word_list),
    },
    'words': word_list,
}
with open('words.json', 'w', encoding='utf-8') as fp:
    json.dump(out, fp, ensure_ascii=False, separators=(',', ':'))

# 統計
from collections import Counter
lc = Counter(len(w) for w in word_list)
print('詞數:', len(word_list))
print('各長度詞數:', dict(sorted(lc.items())))
print('範例(高頻):', word_list[:20])
