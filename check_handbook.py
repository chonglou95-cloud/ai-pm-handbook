#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AI产品经理面试手册.html 的自检脚本。改完页面跑一遍：python3 check_handbook.py"""
import io, os, re, sys
from html.parser import HTMLParser

FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "AI产品经理面试手册.html")
VOID = {'area','base','br','col','embed','hr','img','input','link','meta','source','track','wbr',
        'path','rect','line','circle','polygon','polyline','use','stop','ellipse'}

ok, bad = [], []
def check(name, passed, detail=""):
    (ok if passed else bad).append((name, detail))

if not os.path.exists(FILE):
    print("找不到 %s" % FILE); sys.exit(1)
s = io.open(FILE, encoding="utf-8").read()

# 1 标签闭合
class P(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True); self.stack=[]; self.err=[]
    def handle_starttag(self, t, a):
        if t not in VOID: self.stack.append((t, self.getpos()))
    def handle_endtag(self, t):
        if t in VOID: return
        if not self.stack: self.err.append("多余的 </%s> @%s" % (t, self.getpos())); return
        if self.stack[-1][0] != t:
            self.err.append("</%s> @%s 对不上未闭合的 <%s> @%s" % (t, self.getpos(), self.stack[-1][0], self.stack[-1][1]))
            for i in range(len(self.stack)-1, -1, -1):
                if self.stack[i][0] == t: del self.stack[i:]; break
        else: self.stack.pop()
p = P(); p.feed(s)
check("标签闭合", not p.stack and not p.err,
      "; ".join(p.err[:3] + ["未闭合 <%s> @%s" % (t, pos) for t, pos in p.stack[:3]]))

# 2 三套主题块
themes = [("浅色 :root", bool(re.search(r'^:root\{', s, re.M))),
          ("系统深色 @media", 'prefers-color-scheme:dark' in s and ':root:not([data-theme="light"])' in s),
          ("显式深色 [data-theme]", ':root[data-theme="dark"]' in s)]
check("三套主题块齐全", all(v for _, v in themes),
      "缺少: " + ", ".join(n for n, v in themes if not v))

# 3 组件里写死色值
decl = set(re.findall(r'--[\w-]+:\s*(#[0-9A-Fa-f]{3,8})', s))
allc = set(re.findall(r'(?<![\w-])#[0-9A-Fa-f]{6}\b', s))
hard = sorted(allc - decl)
check("没有写死的色值", not hard, "组件里出现了非 token 色值: " + ", ".join(hard[:6]))

# 4 三套主题的变量名一致
def vars_in(block): return set(re.findall(r'(--[\w-]+):', block))
m_light = re.search(r'^:root\{(.*?)\}', s, re.S | re.M)
m_media = re.search(r':root:not\(\[data-theme="light"\]\)\{(.*?)\}', s, re.S)
m_dark  = re.search(r':root\[data-theme="dark"\]\{(.*?)\}', s, re.S)
if m_light and m_media and m_dark:
    L, M, D = vars_in(m_light.group(1)), vars_in(m_media.group(1)), vars_in(m_dark.group(1))
    check("深色两块变量名一致", M == D, "只在其中一块出现: " + ", ".join(sorted(M ^ D)))
    check("深色变量都在浅色里有定义", M <= L, "浅色缺少: " + ", ".join(sorted(M - L)))
else:
    check("能解析出三个主题块", False, "正则没匹配到，检查 CSS 是否被重排过")

# 5 术语卡结构
terms = re.findall(r'<article class="term">(.*?)</article>', s, re.S)
check("术语卡数量", len(terms) == 59, "找到 %d 张，期望 59 张（新增术语时请同步改本脚本）" % len(terms))
no_reveal = [i+1 for i, t in enumerate(terms) if t.count('<div class="reveal">') != 1]
check("每张卡恰好一个 .reveal", not no_reveal, "第 %s 张不对（背诵模式会失效）" % no_reveal[:5])
no_def = [i+1 for i, t in enumerate(terms) if '<p class="def">' not in t]
check("每张卡都有 .def 定义", not no_def, "第 %s 张缺少面试口径" % no_def[:5])

# 6 编号连续
nos = re.findall(r'<div class="term-no">(\d+)</div>', s)
expect = ["%02d" % i for i in range(1, len(nos)+1)]
first_bad = next((i for i, (a, b) in enumerate(zip(nos, expect)) if a != b), None)
check("术语编号连续", nos == expect,
      "第 %d 个编号是 %s，应为 %s" % (first_bad+1, nos[first_bad], expect[first_bad]) if first_bad is not None else "个数对不上")

# 7 SVG marker
ids = re.findall(r'<marker id="([^"]+)"', s)
refs = set(re.findall(r'url\(#([^)]+)\)', s))
check("marker id 唯一", len(ids) == len(set(ids)), "重复: " + ", ".join(sorted({i for i in ids if ids.count(i) > 1})))
check("marker 引用都存在", refs <= set(ids), "引用了不存在的: " + ", ".join(sorted(refs - set(ids))))

# 8 SVG 文字估宽（粗略，只抓明显撑破的）
FS = {'cn': 13.0, 'sm': 11.0, 'en': 10.5, 'lb': 10.0}
def width_of(txt, cls):
    fs = next((v for k, v in FS.items() if k in cls.split()), 12.0)
    w = 0.0
    for ch in txt:
        w += fs if ord(ch) > 0x2E80 else fs * 0.56
    return w
overflow, collide = [], []
for si, sv in enumerate(re.findall(r'<svg class="dg[^"]*" viewBox="([^"]+)"(.*?)</svg>', s, re.S), 1):
    vbW = float(sv[0].split()[2])
    spans = []
    for m in re.finditer(r'<text class="([^"]*)"([^>]*)>([^<]*)</text>', sv[1]):
        cls, attrs, txt = m.group(1), m.group(2), m.group(3)
        xm = re.search(r'\bx="([-\d.]+)"', attrs); ym = re.search(r'\by="([-\d.]+)"', attrs)
        if not (xm and ym) or not txt.strip(): continue
        x, y, w = float(xm.group(1)), float(ym.group(1)), width_of(txt, cls)
        fs = next((v for k, v in FS.items() if k in cls.split()), 12.0)
        anchor = 'middle' if 'middle' in attrs else 'start'
        l = x - w/2 if anchor == 'middle' else x
        if l + w > vbW + 4 or l < -4:
            overflow.append("图%d 「%s」占 %d–%d，画布 0–%d" % (si, txt[:14], l, l+w, vbW))
        spans.append((l, l+w, y, fs, txt))
    # 同一水平带上的文字互相压字
    for i in range(len(spans)):
        for j in range(i+1, len(spans)):
            a, b = spans[i], spans[j]
            if abs(a[2] - b[2]) >= min(a[3], b[3]) * 0.9: continue   # 不在同一行
            ov = min(a[1], b[1]) - max(a[0], b[0])
            if ov > 2:
                collide.append("图%d 「%s」压住「%s」约 %dpx" % (si, a[4][:12], b[4][:12], ov))
check("SVG 文字未超出画布(估算)", not overflow, " / ".join(overflow[:3]))
check("SVG 文字未互相压字(估算)", not collide, " / ".join(collide[:3]))

# 9 外链
links = re.findall(r'(?:href|src)="(https?://[^"]+)"', s)
foreign = [u for u in links if 'fonts.googleapis.com' not in u and 'fonts.gstatic.com' not in u]
check("没有 Google Fonts 之外的外链", not foreign, "发现: " + ", ".join(foreign[:3]))

# 10 移动端与字符集
check("有 viewport meta", 'name="viewport"' in s)
check("有 charset meta", 'charset=' in s)
check("宽内容有横向滚动容器", 'overflow-x:auto' in s)

print("\n\033[1mAI产品经理面试手册.html 自检\033[0m  (%d 行 / %.1f KB)\n" % (s.count("\n")+1, len(s.encode('utf-8'))/1024))
for n, _ in ok:   print("  \033[32m✓\033[0m %s" % n)
for n, d in bad:  print("  \033[31m✗\033[0m %s%s" % (n, ("  → " + d) if d else ""))
print("\n%d 项通过，%d 项失败\n" % (len(ok), len(bad)))
sys.exit(1 if bad else 0)
