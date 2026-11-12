# 诗歌普查工具（poetry-discovery）

本目录脚本用于从**公开** Blogger Feed 复现“安然诗歌普查”的全过程。
**所有脚本只读公开内容；不修改旧博客；不写入完整诗歌正文。**

---

## 1. 快速开始（三步复现）

在**仓库根目录**执行：

```bash
# 1) 抓取公开 Feed（写入 work/，不提交 git）
python3 tools/poetry-discovery/fetch_feed.py

# 2) 生成 v1 冻结基线 CSV（写入 docs/poetry-discovery/）
python3 tools/poetry-discovery/build_inventory.py

# 3) 生成 v2 分类结果 + v1↔v2 差异表（不覆盖 v1）
python3 tools/poetry-discovery/build_inventory_v2.py

# （可选）与现有站点对照
python3 tools/poetry-discovery/build_comparison.py
```

> 第 1 步会打印 `feed entries == totalResults == sitemap <loc>` 的交叉校验结果。
> 第 2 步应输出：`posts total: 305`、`with poetry: 137`、`categories: {A:106, B:29, C:1, D:1}`。
> 第 3 步应输出：`v2 categories: {A:104, B:31, C:1, D:1}`，`changed rows: 4`。

### 1.1 重建 **v1 冻结基线**（**不可覆盖**）

```bash
python3 tools/poetry-discovery/fetch_feed.py          # 需先有 work/
python3 tools/poetry-discovery/build_inventory.py
```

产出（**仓库内为冻结基线，勿覆盖**）：

- `docs/poetry-discovery/blog-post-inventory.csv`（305 篇）
- `docs/poetry-discovery/poetry-candidates.csv`（137 条候选）

校验：**重新生成的结果应与仓库中的 v1 CSV 逐字节一致**（`cmp` 无差异）。

### 1.2 重建 **v2 分类结果**

```bash
python3 tools/poetry-discovery/build_inventory_v2.py
```

产出（**新文件，不覆盖 v1**）：

- `docs/poetry-discovery/blog-post-inventory.v2.csv`
- `docs/poetry-discovery/poetry-candidates.v2.csv`
- `docs/poetry-discovery/classification-diff-v1-v2.csv`

v2 的 A 类**必须有结构性署名证据**；仅“标签+标题”命中的记录归 **B**（待作者审核）。

### 1.3 检查 **v1 ↔ v2 差异**

```bash
# 差异表：每一行是一条分类发生变化的记录（post_title + category_v1 -> category_v2）
column -s, -t docs/poetry-discovery/classification-diff-v1-v2.csv   # 或直接打开

# 或直接比较两份候选 CSV 的分类列
diff <(cut -d, -f1,7 docs/poetry-discovery/poetry-candidates.csv) \
     <(cut -d, -f1,7 docs/poetry-discovery/poetry-candidates.v2.csv)
```

期望：`classification-diff-v1-v2.csv` 含 **4 行**变化（2 条 Phase 2 + 2 条 Phase 3）。

### 1.4 获取原始 Feed

原始 Feed 由 `fetch_feed.py` 从**公开** Blogger 端点抓取（见 §2），写入 `work/`，**不入库**（见 §3）。

---

## 2. 数据来源（公开、无需鉴权）

| 用途 | URL |
| --- | --- |
| 文章全文（JSON） | `https://www.ismaelan.com/feeds/posts/default?alt=json&max-results=150&start-index=N` |
| 独立计数校验 | `https://www.ismaelan.com/sitemap.xml` |

- 站点为 **Blogger**（Blog ID `2031587887831324661`）。
- `start-index` 以 150 为步长分页（1、151、301…），脚本会自动发现并抓取所有页。

---

## 3. 原始 Feed 是否入库？

**否。** `work/feed-full-*.json`、`work/sitemap.xml` **不进入版本控制**（在 `.gitignore` 中忽略）。

原因：
1. Feed 内含**全部诗歌正文 HTML**，体积大（约 3 MB），且涉及**作品版权**；
2. 数据可**随时从公开 Feed 重新获取**，无需长期保存副本；
3. 入库会与“不批量复制诗歌正文进仓库”的要求冲突。

**数据丢失风险：低。** 只要公开 Feed 可用，随时可完整重建。`fetch_feed.py` 会打印每页
**SHA256 校验值**，便于比对“重新抓取是否与历史一致”。

若未来需要留存校验指纹（**不含正文**），可运行：

```bash
python3 tools/poetry-discovery/fetch_feed.py 2>&1 | tee work/fetch-log.txt
# 记录每个 feed 页的 sha256，作为“普查时点”的证据（可选）。
```

---

## 4. 能否仅依靠公开 Blogger Feed 重跑全流程？

**能，已实测验证（2026-11-12）。** 步骤：

1. `fetch_feed.py` 重新抓取 → 得到 305 篇、sitemap 305 条（一致）；
2. `build_inventory.py` 重新生成 CSV；
3. 与仓库中已提交的 CSV 对比，**逐字节一致**（byte-identical）。

因此普查结果**不依赖任何 OpenHands Workspace 临时文件**。

---

## 5. 脚本清单

| 脚本 | 作用 | 产出 |
| --- | --- | --- |
| `fetch_feed.py` | 抓取公开 Feed + sitemap（含校验值） | `work/feed-full-*.json`、`work/sitemap.xml` |
| `build_inventory.py` | 分类与清单生成（v1，**冻结基线**） | `blog-post-inventory.csv`、`poetry-candidates.csv` |
| `build_inventory_v2.py` | 更严格的署名/翻译规则（v2） | `*.v2.csv`、`classification-diff-v1-v2.csv` |
| `build_comparison.py` | 现有站点 vs 博客对照 | `existing-site-comparison.csv` |
| `verify_clues.py` | 已知线索核对 | 标准输出 |
| `analyze_authorship.py` | A 类署名规则归因分析 | 标准输出 |
| `scan_risks.py` / `scan_anran_contexts.py` / `scan_substring_fp.py` | 误判风险扫描 | 标准输出 |
| `phase2_risk_samples.py` | 代表性风险样本 | 标准输出 |

---

## 6. 版权与边界

- 脚本**只读取公开页面**，不登录、不写入旧博客。
- CSV 中 `note` 字段仅含**用于识别的截断摘录**，**不含完整诗歌正文**。
- 重新抓取的原始 Feed 含正文，仅存于本地 `work/`，**不入库**。

---

## 7. 重要：候选记录 ≠ 已确认独立作品（**【已验证事实】**）

- `poetry-candidates.csv` 中的每一行是**文章级候选记录（article-level candidate record）**，
  **不是**一首“已确认的独立诗歌作品”。
- 一篇文章可能包含：**多首诗**、**诗 + AI 诗评 + 英译**、或**入选喜讯/公告**等复合内容。
- **137 是文章级候选记录数，不代表独立作品数量。** 独立作品总数**尚未确定，可能少于或多于 137**。
  只有经过**作者逐篇确认文章中的作品边界**后，才能统计独立作品总数。
- 必须始终区分四个层级：

  | 层级 | 含义 | 当前数量 |
  | --- | --- | ---: |
  | 原始博客文章 | 旧博客公开文章 | **305** |
  | 诗歌候选文章 | 命中诗歌信号的**文章** | **137** |
  | 候选文章中的单首/多首诗 | 文章内实际诗作（**未拆分、未确认**） | **未确定** |
  | 作者已确认的独立作品 | 作者逐篇确认后的作品 | **0（待确认）** |

- `work_count_estimate` 字段表达的是**作品数**估计，不是文章数：
  - `>=2`：标题有明确多首标记；
  - `unknown`：无标记，作品数**无法**从元数据证明（**不得**假定为 1）。
- 在作者人工确认前，**禁止**使用“137 首已发现诗歌”这类确定性表述。
