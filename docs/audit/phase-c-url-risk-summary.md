# Phase C：旧博客 305 篇文章 URL 迁移风险总结

> 日期：2026-11-12 · 只读分析
> 数据源：`docs/poetry-discovery/blog-post-inventory.v2.csv`（PR #4，305 行）
> 详细逐篇规划：`legacy-content-url-migration-plan.csv`

---

## 1. 旧博客 URL 结构（**已验证**）

- 全部 305 篇文章均为 Blogger 路径：`https://www.ismaelan.com/{YYYY}/{MM}/{slug}.html`
- 路径形态 **305/305** 符合 `/{年}/{月}/{slug}.html`；**无**中文 URL；**无**日期以外的层级。
- 域名：全部 `www.ismaelan.com`；`/feed` 404，但 `/feeds/posts/default` 200（Blogger feed）。
- 抽样 8 篇线上复查：**全部 200**（2026-11-12）。

## 2. slug 分布（**已验证**）

| 指标 | 数值 |
| --- | --- |
| 文章总数 | 305 |
| **不同 slug 数** | **135** |
| 出现多次的 slug | 29 个 |
| 最常见 slug | `blog-post.html`（**86 次**） |
| 其余多为 `blog-post_<NN>.html` | 例如 `blog-post_23` 9 次、`blog-post_26` 7 次 |

> **原因**：Blogger 对**中文标题**自动生成的 slug 退化为 `blog-post.html`，
> 同月多篇时加数字后缀（`blog-post_07.html` 等），**跨年份重复**。

## 3. URL 冲突模拟（**已验证**）

用 305 篇的 slug 模拟三种新站 permalink 方案：

| 方案 | 生成 URL 数 | 冲突数 | 结论 |
| --- | --- | --- | --- |
| A：`/:slug/`（当前新站配置） | 135 | **170** | ❌ **不可用**：多篇互相覆盖 |
| B：`/:year/:month/:slug/` | 305 | **0** | ✅ 与旧博客路径一致，零冲突 |
| C：`/:year/:slug/` | 204 | 101 | ❌ 同年仍有重名 |

**实测命令**
```bash
python3 - <<'PY'
import csv,re
inv=list(csv.DictReader(open("/tmp/inv_v2.csv",encoding="utf-8")))
def s(u): return re.search(r"/(\d{4})/(\d{2})/([^/]+)\.html$",u).groups()
flat={s(r["url"])[2] for r in inv}
print("flat outputs:",len(flat),"collisions:",len(inv)-len(flat))   # 135 / 170
PY
```

**结论**：**扁平 `/:slug/` 无法承载 305 篇**。必须为重复 slug 指定唯一值，或采用日期路径。

## 4. 建议方案（**需作者/负责人决定**）

**推荐：`/:year/:month/:slug/`**
- 与旧博客路径**一一对应**（去掉 `.html`），**零冲突**；
- 可对旧 `.html` URL 做 **301** 到新路径，**保留历史链接**；
- 唯一“缺点”：中文标题文章的 slug 仍是 `blog-post` 系（可读性差），
  但**可读性**可用“作者指定英文 slug”逐步改进（**由作者决定，AI 不代定**）。

**次选：作者为每篇指定唯一英文 slug**，用扁平 `/:slug/`
- 与**旧站 6 个页面**的扁平风格一致；
- 但需作者**逐篇命名**（工作量大），且仍需为 305 篇保证全局唯一。

**无论哪种方案**：旧博客域名 `www.ismaelan.com` 的 `.html` URL 都应保留 **301**
指向新站对应路径（或保留旧博客原样，视负责人决定）。

## 5. 与旧站 6 页的区别（**再次强调**）

| | 旧站 6 页 | 旧博客 305 篇 |
| --- | --- | --- |
| URL | `poet.ismaelan.com/<slug>/` | `www.ismaelan.com/YYYY/MM/slug.html` |
| 处理 | **保留原 URL**（同址升级） | **待定**（本 CSV） |
| 风险 | 低 | **高** |

**不得混淆**：旧站 6 页的 URL 与 305 篇文章的 URL 是**两套独立系统**。

## 6. 风险等级

| 风险 | 等级 | 说明 |
| --- | --- | --- |
| 扁平 permalink 导致 170 处冲突 | **高** | 会静默覆盖内容 |
| 中文标题无唯一 slug | **高** | 需作者命名或日期路径 |
| 301 缺失导致旧链接失效 | **中** | 取决于是否保留旧博客域名 |
| 一篇文章含多首（组诗）需拆分 | **高** | 7 篇已标记，拆分后 URL 需作者决定 |
| 未识别为候选的 168 篇是否迁移 | **中** | 需作者判断 |

## 7. 需要作者决定的问题（汇总）

1. 305 篇中哪些要迁入新站（137 候选？还是更多/更少）？
2. 采用 `/:year/:month/:slug/` 还是作者指定英文 slug？
3. 中文标题文章是否需要**可读英文 slug**？由谁命名？
4. 组诗/多首文章**是否拆分**？拆分后各自 URL？
5. 旧博客域名 `www.ismaelan.com` 是否保留？是否设置 301？
6. 未被识别为候选的 168 篇如何处理？

> 本报告**不替作者决定任何作品的新 URL**，也不拆分/合并任何作品。
