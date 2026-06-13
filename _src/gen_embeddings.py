# -*- coding: utf-8 -*-
"""
語意字向量生成器（model2vec 靜態詞向量，純 numpy 推論，不需 torch）
- 讀 chars_db.json 的字（順序固定）
- model2vec 嵌入 -> L2 normalize -> int8 量化
- 輸出 embeddings.json：{dim, count, b64(int8, count*dim row-major)}
JS 端解 base64 成 Int8Array，cosine≈int8 內積（已正規化）。
"""
import json, base64, io, sys
import numpy as np
from model2vec import StaticModel

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

db = json.load(open('chars_db.json', encoding='utf-8'))
chars = [e['c'] for e in db['chars']]

m = StaticModel.from_pretrained("minishlab/M2V_multilingual_output")
V = m.encode(chars)                      # (N, dim) float32
V = V / (np.linalg.norm(V, axis=1, keepdims=True) + 1e-9)
q = np.clip(np.round(V * 127), -127, 127).astype(np.int8)   # int8 量化

b64 = base64.b64encode(q.tobytes()).decode('ascii')
out = {'dim': int(q.shape[1]), 'count': int(q.shape[0]), 'b64': b64}
json.dump(out, open('embeddings.json', 'w', encoding='utf-8'), separators=(',', ':'))

# sanity
def vec(ch):
    i = chars.index(ch); v = q[i].astype(np.float32); return v/ (np.linalg.norm(v)+1e-9)
def sim(a,b): return float(vec(a) @ vec(b))
print('dim', out['dim'], 'count', out['count'])
print('int8 size KB', round(len(q.tobytes())/1024,1), 'b64 KB', round(len(b64)/1024,1))
for a,b in [('愛','戀'),('愛','石'),('喜','悲'),('山','水'),('日','月'),('寒','暖')]:
    if a in chars and b in chars: print(a,b,round(sim(a,b),3))
