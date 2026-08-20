# AGENTS.md

本文件的约定**只适用于 `AI产品经理面试手册.html`**（一个自包含的单页学习手册）。
同目录下的简历、岗位清单、脚本等与本约定无关，不要顺手改动。

---

## 一、这个页面是什么

- **单文件 HTML**，约 1200 行 / 96KB。没有构建步骤，没有依赖，没有 `package.json`。
- 结构顺序：
  - `<title>` + `<meta>` + Google Fonts `<link>`（第 1–7 行）
  - `<style>` … `</style>`（第 8–323 行，全部 CSS 在这里）
  - `<header class="bar">`（顶部工具条：搜索框 + 背诵模式开关）
  - `.rail`（左侧目录）
  - 五个 `<section>`：`#map` `#terms` `#diff` `#qa` `#line`
  - `<script>`（文件末尾，约 55 行原生 JS，无框架）
- **改完直接用浏览器打开文件即可验证，不需要起服务器。**

---

## 二、五条硬约束（违反会让页面出错）

### 1. 颜色必须走 CSS 变量，禁止写死色值

页面有**三套主题状态**，缺一不可：

```css
:root { --ink:#141E1C; ... }                                  /* 浅色：完整定义 */
@media (prefers-color-scheme:dark){
  :root:not([data-theme="light"]){ --ink:#E8EDEA; ... }        /* 系统深色 */
}
:root[data-theme="dark"]{ --ink:#E8EDEA; ... }                 /* 显式深色 */
```

- 新增颜色时，**三个块都要加**，否则某一种主题下会出现「深色字配深色底」。
- 组件样式里只能写 `var(--xxx)`，**绝对不要**把 `#RRGGBB` 直接写进 `.class{}` 里。
- 后两个块只重新定义变量，不要在里面写组件规则。

### 2. 三张架构图是手写的内联 SVG，坐标是死的

`.dg` 那几个 `<svg>` 里所有 `<rect>` `<line>` `<path>` `<text>` 的坐标都是人工排的。

- **改图里的文案 = 会改变文字宽度 = 可能撑出方框或跟旁边的字重叠。** 文案变长了必须同时调 `<rect>` 的 `width` 和相邻元素的 `x`。
- 粗略估宽：一个汉字 ≈ 字号 px，一个英文字母 ≈ 字号 × 0.55。图里 `.cn` 是 13px、`.sm` 是 11px、`.en` 是 10.5px。
- 每个 `<svg>` 的 `<marker id="...">` **必须全局唯一**（现有 `a1 a1a a1d a2 a2a a3 a3a a4`）。复制 SVG 时一定要改 id，否则箭头会串。
- SVG 里**不要**加 `<style>` `<script>` `<foreignObject>`；样式统一在页面 CSS 的 `.dg .xxx` 里。
- 改完跑 `python3 check_handbook.py` 检查。

### 3. 术语卡的 DOM 结构不能动

背诵模式（`body.recall`）靠这个结构工作：

```html
<article class="term">
  <div class="term-h">…编号 / 英文 / 中文 / 标签…</div>
  <div class="term-c">
    <div class="reveal">   ← 必须有且只有一个，否则背诵模式失效
      <p class="def">…</p>
      <div class="body">…</div>
      <p class="note">…</p>
    </div>
  </div>
</article>
```

- 每张卡**必须恰好有一个 `.reveal`**，要隐藏的内容全部放在它里面。
- 新增术语请**复制一张现有卡再改内容**，不要手写结构。
- 编号 `.term-no` 是连续的 `01`–`59`，中间插入术语要顺延后面所有编号。

### 4. 搜索依赖 `textContent`

搜索框直接匹配整张 `.term` 卡的纯文本。想让某个术语能被某个关键词搜到，就把那个词**写进卡片可见文案里**，不要另加 `data-*` 属性（现有 JS 不读）。

### 5. 只允许 Google Fonts 一个外链

不要引入任何 CDN 脚本、外部样式表、远程图片、`fetch` 请求。这个页面会发布到一个有严格 CSP 的环境，外链会被拦掉，页面会静默降级。图片如需添加，必须内联成 `data:` URI。

---

## 三、文案风格

- 中文用**全角标点**。不使用 `「」`，不使用分号 `；`。
- 每个术语卡固定三段式：`.def`（一句可直接在面试里说出口的定义）→ `.body`（展开解释 / 例子）→ `.note`（易错点，可选）。
- `.note` 的语气是「这里容易被追问穿」，不是泛泛的补充说明。
- 不写「值得注意的是」「总而言之」这类填充句。

---

## 四、改完必须做的验证

```bash
python3 check_handbook.py
```

全绿之后，在浏览器里再确认三件事：

1. **深色模式**（macOS 系统设置切深色，或 devtools 里 Rendering → prefers-color-scheme）—— 文字和背景都要看得清。
2. **窄屏**（devtools 调到 375px 宽）—— 页面**不能**出现横向滚动条；图和表格应该在自己的框里横向滚动。
3. **背诵模式**开关 —— 打开后术语只剩英文和中文，点卡片能展开答案，关掉后全部复原。

粘到浏览器 Console 里可以快速验证图有没有撑破：

```js
document.querySelectorAll('.dg').forEach((s,i)=>{
  const [,,W,H]=s.getAttribute('viewBox').split(' ').map(Number);
  const bad=[...s.querySelectorAll('text')].filter(t=>{const b=t.getBBox();
    return b.x<-1||b.x+b.width>W+1||b.y<-1||b.y+b.height>H+1});
  console.log('图'+(i+1), bad.length?'⚠️ 溢出: '+bad.map(t=>t.textContent):'ok');
});
```

---

## 五、不要做的事

- 不要拆成多个文件（`.css` / `.js` 分离）—— 它就是要能双击打开、能整份发布。
- 不要引入 Tailwind、React、构建工具。
- 不要重排 `<section>` 的顺序或改它们的 `id`（左侧目录和滚动高亮靠 id 定位）。
- 不要动 `.dg` 的 `min-width`（那是让图在窄屏下横向滚动而不是被压扁的关键）。
