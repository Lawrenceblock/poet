# 第二轮视觉设计 · 修改清单、影响评估与风险（POET-VISUAL-REFINEMENT-02）

基线：`design/phase1-visual-refinement-2026-11-13` @ `b73178c`。
分支：`design/phase2-black-white-composition-2026-11-13`。

## 一、修改文件清单（13 个源文件 + 154 个审阅页重新生成）

| 文件 | 性质 | 说明 |
| --- | --- | --- |
| `hugo/assets/css/style.css` | 重写 | 全站样式；建立黑色骨架配色与结构 |
| `hugo/layouts/_default/baseof.html` | 重写 | 黑色页眉（站名 + 中英标识 + 导航）、黑色页脚 |
| `hugo/layouts/index.html` | 重写 | 首页：黑色主视觉 + 4 个黑色栏目标题条 |
| `hugo/layouts/_default/single.html` | 改写 | 诗歌页：黑色诗歌页头 + 白色正文 |
| `hugo/layouts/_default/list.html` | 改写 | 列表页：黑色页面标题条 |
| `hugo/layouts/_default/archive.html` | 改写 | 卷目：黑色年份标题条 |
| `hugo/layouts/_default/years.html` | 改写 | 年代索引：黑色年份标题条 + 年份跳转 |
| `hugo/layouts/_default/about.html` | 改写 | 档案说明：黑色标题条 |
| `hugo/layouts/_default/preface.html` | 改写 | 题记：黑色标题条 |
| `hugo/layouts/_default/search.html` | 改写 | 搜索：黑色标题条 |
| `hugo/layouts/404.html` | 改写 | 404：黑色标题条 |
| `tools/author-review/build_review_site.py` | 改写 | 审阅页页眉/页脚标记 + `page()` 支持 `depth` 参数 |
| `tools/author-review/build_oldsite_review.py` | 改写 | 旧站审阅页调用 `page(depth=1)` |
| `docs/author-review/site/**`（154 个 HTML） | 重新生成 | 样式 + 页眉/页脚变化，**正文逐字不变** |

**未改动**：`hugo/content/**`、`hugo/hugo.toml`、`hugo/static/**`、
`docs/author-review/review-records/**`、`docs/author-review/private/**`、`main`。

## 二、影响评估

| 维度 | 结论 |
| --- | --- |
| 诗歌正文 | **逐字不变**（见测试报告：内容身份核对 0 差异） |
| 审阅数据 / 记录 | **不变**（`review-records` 未改动，SHA 未变） |
| URL / 路由 | **不变**（未触碰 permalink、content 路径、配置） |
| 功能 | **不变**（25/25 路由 200） |
| 安全 | **不变**（令牌门禁 4/4 正确；无泄漏） |
| 可见变化 | 仅视觉：黑/白块面结构、栏目标题条、页眉页脚、诗歌页头 |

## 三、风险与缓解

| 风险 | 等级 | 缓解 |
| --- | --- | --- |
| 暗红 `#762B35` 在黑底不可见（1.85:1） | 中 | 黑底改用提亮衍生色 `#CB6E77`（5.15:1）；**需作者确认是否接受该衍生色** |
| 黑色块面过多，阅读压迫感 | 低 | 黑色仅限结构位；正文/条目全白；已在截图逐页确认黑白比例（见测试报告像素采样） |
| 移动端页眉拥挤/重叠 | 低 | 320/360/414px 逐宽度检查，无横向溢出 |
| 审阅页页眉相对链接在子目录失效 | 低 | `page()` 增加 `depth` 参数；`poem/`、`oldsite/` 用 `depth=1`；已验证目标 200 |
| 第一轮预览被覆盖，作者看不到旧版 | 低 | 第一轮完整保存在 git（分支 + 提交）与截图；本轮同地址展示最新版，符合迭代预期 |

## 四、回滚

本分支为**独立候选分支**，可随时整体回滚：

```bash
# 丢弃本轮全部改动，回到第一轮
git checkout design/phase1-visual-refinement-2026-11-13

# 或删除本轮分支
git branch -D design/phase2-black-white-composition-2026-11-13
```

`main`、`impl/phase1-candidate-2026-11-12`、第一轮分支均未被改写，
历史提交完整保留。

## 五、需作者确认的决策点

1. **黑底暗红衍生色** `#CB6E77` 是否接受（或改用其他提亮/纯白处理）。
2. 首页主视觉的黑色块面比例是否符合「安静、简洁、以文学阅读为中心」的预期。
3. 是否保留诗歌正文页的黑色页头（也可退回纯白页头 + 暗红细线）。
