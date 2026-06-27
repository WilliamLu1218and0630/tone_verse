# -*- coding: utf-8 -*-
"""
tone_verse 聲調字庫生成器
- 掃 CJK 基本區，用 wordfreq 取字頻（Zipf），保留真實常用字
- OpenCC 過濾：只留繁體/共用字（丟純簡化字）
- pypinyin BOPOMOFO + heteronym 取注音（含破音字全讀音）
- 解析每個讀音的聲調(t)與韻母(y, 去聲母去調號)
輸出 chars_db.json，依字頻由高到低排序。
"""
import json, sys, io
from pypinyin import pinyin, Style
from wordfreq import zipf_frequency
from opencc import OpenCC

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

s2t = OpenCC('s2t')

SHENGMU = set('ㄅㄆㄇㄈㄉㄊㄋㄌㄍㄎㄏㄐㄑㄒㄓㄔㄕㄖㄗㄘㄙ')
TONE_MARK = {'ˊ': 2, 'ˇ': 3, 'ˋ': 4, '˙': 5}  # 無調號 = 1聲

def parse_reading(zy):
    """注音字串 -> (純注音, tone, 聲母, 韻母)。tone: 1~4 + 5(輕聲)。"""
    tone = 1
    core = zy
    for mk, tv in TONE_MARK.items():
        if mk in zy:
            tone = tv
            core = zy.replace(mk, '')
            break
    # 去聲母得韻母；空韻(ㄓㄔㄕㄖㄗㄘㄙ單獨)記為 '帀'
    sm = ''
    rime = core
    if core and core[0] in SHENGMU:
        sm = core[0]
        rime = core[1:]
    if rime == '':
        rime = '帀'
    return zy, tone, sm, rime

def in_big5(ch):
    """Big5 可編碼 = 真實繁體常用字。粵字/部首/罕字會落選 -> 乾淨過濾。"""
    try:
        ch.encode('big5')
        return True
    except UnicodeEncodeError:
        return False

ZIPF_MIN = 2.0   # 字頻門檻：保留稍冷僻的詩用字，又不收進雜訊
chars = []
for cp in range(0x4E00, 0xA000):
    ch = chr(cp)
    f = zipf_frequency(ch, 'zh')
    if f < ZIPF_MIN:
        continue
    # 乾淨過濾：Big5 可編碼(真實繁體常用) + 非純簡化字
    if not in_big5(ch):
        continue
    if s2t.convert(ch) != ch:
        continue
    # 主讀音(最常見)
    readings = pinyin(ch, heteronym=False, style=Style.BOPOMOFO)
    if not readings or not readings[0]:
        continue
    zy = readings[0][0]
    if not zy or (zy[0] not in SHENGMU and zy[0] not in 'ㄚㄛㄜㄝㄞㄟㄠㄡㄢㄣㄤㄥㄦㄧㄨㄩ'):
        continue
    z, t, sm, y = parse_reading(zy)
    entry = {'c': ch, 'f': round(f, 2), 'z': z, 't': t, 'sm': sm, 'y': y}
    # 破音字：heteronym 取前 3 筆，只留聲調不同的 alt（Zipf < 3.5 的罕字不收）
    if f >= 3.5:
        het = pinyin(ch, heteronym=True, style=Style.BOPOMOFO)
        if het and het[0] and len(het[0]) > 1:
            seen = {t}
            alts = []
            for r in het[0][1:3]:
                az, at, asm, ay = parse_reading(r)
                if at not in seen:
                    seen.add(at)
                    alts.append({'z': az, 't': at, 'sm': asm, 'y': ay})
            if alts:
                entry['alts'] = alts
    chars.append(entry)

chars.sort(key=lambda x: -x['f'])
out = {
    'meta': {
        'desc': 'tone_verse 聲調字庫',
        'tone_legend': {'1': '一聲(陰平,無調號)', '2': '二聲ˊ', '3': '三聲ˇ', '4': '四聲ˋ', '5': '輕聲˙'},
        'zipf_min': ZIPF_MIN,
        'count': len(chars),
    },
    'chars': chars,
}
with open('chars_db.json', 'w', encoding='utf-8') as fp:
    json.dump(out, fp, ensure_ascii=False, separators=(',', ':'))

# 統計
from collections import Counter
tc = Counter(c['t'] for c in chars)
print('字數:', len(chars))
print('各聲調字數:', dict(sorted(tc.items())))
print('範例(高頻):', [c['c'] for c in chars[:20]])
print('輕聲池(驗雜訊):', [c['c'] for c in chars if c['t'] == 5])
print('帶聲母範例:', [(c['c'], c['sm'], c['y']) for c in chars[:6]])
poly = [c for c in chars if 'alts' in c]
print(f'破音字: {len(poly)} 字, 總alt {sum(len(c["alts"]) for c in poly)} 條')
print('破音字範例:', [(c['c'], c['t'], [(a['t'],a['z']) for a in c['alts']]) for c in poly[:10]])
