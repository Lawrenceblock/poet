# Phase 2 · 文章候选与独立作品的数据模型复核

> 日期：**2026-11-12**
> 复核对象：`docs/poetry-discovery/poetry-candidates.csv`（137 行）与 `blog-post-inventory.csv`（305 行）
> 相关分支：`review/poetry-classification-phase2`
> 结论一律区分：**【已验证事实】【自动识别】【推断】【建议】【待作者审核】**

---

## 0. 最重要的一句话（**【已验证事实】**）

**137 是“文章级候选记录”（article-level candidate records）的数量，不是“已确认的独立诗歌作品”数量。**

- 每 1 条候选 = **1 篇含诗歌信号的博客文章**，不是 1 首诗。
- 因存在“一篇文章含多首诗”，**独立作品数量 ≥ 137**，但具体多少**尚未确认**。
- 在作者确认前，**禁止**使用“137 首已发现诗歌”这类确定性表述。

---

## 1. 复核问题逐条回答（**【已验证事实】**）

### 1.1 一篇文章是否可能含多首诗？——**是**

标题带多首标记的文章 **7 篇**（`multi_poem_flag=yes`）：

| 日期 | 标题 | 备注 |
| --- | --- | --- |
| 2010-11-27 | 安息茴香（外一首） | 含 2 首 |
| 2010-12-07 | 第一个殉道者（外一首） | 含 2 首 |
| 2009-12-08 | 致昨日的情人(外一首) | 含 2 首 |
| 2011-07-28 | 我们事先从未反对(外二首) | 含 3 首 |
| 2012-07-23 | 牙与魂(二首) | 含 2 首 |
| 2012-11-13 | 两首格则勒 | 含 2 首 |
| 2010-01-18 | 【组诗】现代西域诗草… | 组诗，正文实为公告 |

> 但**标题无标记、正文仍含多首**的情况更普遍，脚本**无法自动发现**。**【待作者审核】**

### 1.2 一篇文章是否可能同时含诗歌与散文？——**是**

已确认**复合文章**（诗 + 散文/评论 + 翻译同处一篇）：

| 日期 | 标题 | 结构（**【已验证事实】**） |
| --- | --- | --- |
| 2025-05-08 | 齐水行 | 诗（`文/安然`）+ **AI 诗评《齐水行》** + 英译（`Poem Review`） |
| 2025-06-21 | West Buddha Valley | 诗 + 评论段 |

### 1.3 文章标题是否一定等于诗歌标题？——**否**

- **32 处**文章正文出现 `X/安然` 形式的**内嵌标题**，与文章标题不同。**【已验证事实】**
- 例：文章《狱中书简》《这个秋天的雨很大》《马梅兰》等，正文首行为独立诗题/署名结构。
- 因此 `work_title` **不能**默认等于文章标题。

### 1.4 `position_in_post` 字段是否准确？——**否，且为占位值**

- 全部 137 行的 `position_in_post` **恒为** `entire post (auto)`。**【已验证事实】**
- 该字段**未实现**真正的“作品在文章中的位置/范围”信息，属占位符，**不具信息量**。

### 1.5 `work_title` 字段是否足以表达作品边界？——**否**

- 137 行中 **117 行** `work_title` 为空；其余 20 行**等于文章标题**（无内嵌标题时）。
- 该字段**仅**“标题含诗歌关键字时才填文章标题”，**无法**表达“一篇含多首”的边界。**【已验证事实】**

---

## 2. 现有字段问题汇总（**【已验证事实】**）

| 字段 | 问题 |
| --- | --- |
| `position_in_post` | 恒为占位值，无实际信息 |
| `work_title` | 117/137 为空；非空时仅=文章标题，不表达作品边界 |
| （缺失）`source_post_id` | 候选 CSV **无**显式文章主键，仅靠 `source_url` 关联 |
| `candidate_id` | 是**文章级**候选 ID，易被误读为“作品 ID” |

> 关联链现状：`poetry-candidates.csv.source_url` ↔ `blog-post-inventory.csv.url`（可关联，但未显式）。

---

## 3. 建议的数据模型（**【建议】**）

明确三层实体，**逐层收敛，禁止跳跃**：

```
source_post (305)  ──1:N──▶  candidate_work (137)  ──1:N──▶  confirmed_work (0, 待作者确认)
   原始博客文章                  诗歌候选（文章级）              已确认的独立作品
```

### 3.1 `source_post`（原始博客文章，= 现有 inventory）

| 字段 | 说明 |
| --- | --- |
| `post_id` | Blogger 文章 ID（主键） |
| `url`、`title`、`published`、`year`、`labels`、`lang`、`content_chars` | 元数据 |
| `has_poetry_signal` | 是否含诗歌信号 |

### 3.2 `candidate_work`（诗歌候选，= 现有 candidates，建议增改字段）

| 字段 | 变更 | 说明 |
| --- | --- | --- |
| `candidate_id` | 保留 | 文章级候选 ID（语义：**候选记录**，非作品） |
| `source_post_id` | **新增** | 外键 → `source_post.post_id`（补齐显式关联） |
| `source_url`、`source_post_title` | 保留 | 便于回溯 |
| `candidate_title` | **改名**（原 `work_title`） | 默认=文章标题，**非**确认诗题 |
| `title_source` | **新增** | `article_title` / `inner_byline` / `none` |
| `boundary_status` | **替换** `position_in_post` | `entire_post` / `unknown` / `needs_split` |
| `work_count_estimate` | **新增** | `1` 或 `>=2`（据多首标记；无标记亦可能 >1） |
| `category`、`confidence`、`authorship_evidence`、`labels`、`note` | 保留 | 现有证据字段 |

### 3.3 `confirmed_work`（已确认的独立作品，本阶段**为空**）

| 字段 | 说明 |
| --- | --- |
| `work_id` | 作品 ID（作者确认后分配） |
| `candidate_id` | 外键 → 候选 |
| `final_title` | 最终诗题 |
| `author_status` | `original` / `translation` / `quotation` |
| `boundary` | 作品在文章中的起止（行号或锚点） |
| `verified_by`、`verified_date` | 确认人与日期 |
| `body_sha256` | 正文指纹（逐字比对付迁移用） |

> **本阶段不创建 `confirmed_work`**，也不擅自把文章拆成“已确认作品”。

---

## 4. 字段调整方案（**不擅自拆分**，**【建议】**）

1. 在 `poetry-candidates.csv` **新增** `source_post_id`（不改动 v1 原文件，另存 v2 或新文件）。
2. 将 `position_in_post` **标记为废弃**，替换为 `boundary_status`。
3. 将 `work_title` 语义**澄清为** `candidate_title`（默认=文章标题），并新增 `title_source`。
4. **保留**原始 `candidate_id`、`source_url`、`source_post_title` 的对应关系。
5. **不拆分**多首诗文章；仅在 `boundary_status=needs_split`、`work_count_estimate>=2` 中**标注待人工拆分**。

> 本阶段**未**改动 v1 CSV；上表为**方案**，待审阅后再实施。

---

## 5. 仍需人工/作者确认（**【待作者审核】**）

1. 7 篇多首标记文章的**实际作品拆分**（标题、边界）。
2. **无标记但正文含多首**的文章（脚本无法自动发现）。
3. 复合文章（`齐水行`、`West Buddha Valley`）中，**诗歌部分**的边界。
4. 内嵌标题（32 处 `X/安然`）中，哪些是**诗题**、哪些只是署名行。

---

## 6. 结论

- **137 = 文章级候选记录**（**【已验证事实】**），**不是** 137 首独立诗歌。
- 现有字段 `position_in_post` 无信息量、`work_title` 不足以表达边界、且缺少显式 `source_post_id`。
- 建议采用 **source_post → candidate_work → confirmed_work** 三层模型，本阶段仅提出方案，**未实施拆分**。
