# P1-B · 内容完整性与诗歌保真报告

- 日期：2026-11-12
- 工具：`tools/author-review/verify_verbatim.py`、`tools/author-review/build_phase1_lists.py`
- 结论：**137/137 逐字保真通过；站内链接 0 断链；未发现重复/缺失/异常作品**

## 1. 逐字保真（【已验证】）

```
$ python3 tools/author-review/verify_verbatim.py
candidates checked : 137
verbatim-identical : 137
OK: all checks passed
```

- 判定方式：逐候选比对审阅页 `<div class="poem">` 内文本与 `sanitize(原始 feed HTML)` 是否**逐字节一致**；同时校验无 `<script>`/`on*`/`javascript:` 残留、候选数与源 CSV 一致、内部链接可解析。
- **137/137 全部一致。未发生任何正文改写、标点改动或重新断行。** 【已验证】

## 2. 站内链接（【已验证】）

- 审阅站内部链接（index → batch → poem）在 `verify_verbatim.py` 中校验通过（**0 断链**）。
- 完整构建产物另有独立检查（见 P1-G）：预览树 795 条内部链接、正式树 209 条，**0 断链**。

## 3. 内容清单（【已验证】）

- 候选总数：**137**（文章级候选；**不等于 137 首诗**，独立作品数待作者确认）。
- 分类分布：A=104，B=31，C=1，D=1（脚本判定，**非作者确认**）。
- 语言分布：zh=87，zh+en=49，en=1。
- 含多首线索（`multi_poem_flag=yes`）：**7**（需作者确认是否拆分）。
- 全部 137 条 `full_text_present=yes`。
- 旧博客总文章：**305** 篇（`blog-post-inventory.v2.csv`），其中 137 篇进入候选。

详见：`docs/author-review/phase1/candidate-list.md`、`docs/author-review/phase1/to-confirm.md`。

## 4. 待作者确认清单（摘要）

完整版见 `docs/author-review/phase1/to-confirm.md`。要点：

1. 标题：**117 条**候选未检测到独立标题。
2. 组诗拆分：**7 条**含多首线索。
3. 创作时间 / 首次发表时间：脚本无此数据，**不得由 AI 推断**。
4. 作品版本（如《青春的物语》旧站版 vs 博客版）。
5. 收录范围：137 是否为最终集；旧博客其余 168 篇是否纳入。
6. 归属存疑条目（如《放牧的星星》《安然》）。
7. 小传 / 题记 / 版权文本定稿。

## 5. 内容保护声明

- 本轮**未修改任何诗歌正文、作者小传、题记或文学内容**。**【已验证】**
- 审阅状态清单含作者意见，已写入 git-ignored 的 `docs/author-review/private/`，**未提交公开仓库**。**【已验证】**
