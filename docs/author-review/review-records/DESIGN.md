# 作者审阅系统 · 技术设计说明

> 状态：**设计已定稿，进入实现**。
> 分支：`feat/author-review-system`。本文档只描述设计，不改变任何原始数据。

---

## 0. 现状与本轮目标

现状：`/review/` 是**只读阅读站**（154 个静态 HTML），每篇有一个 `disabled` 的下拉框，
只是“示意”，没有任何提交/保存/读取/导出能力。预览服务器是纯静态
`SimpleHTTPRequestHandler`（POST 返回 501）。

本轮目标：在**不引入数据库、不引入第三方服务、不引入复杂后端**的前提下，
让作者真正能够**审阅 → 保存 → 重新打开仍在 → 导出 CSV/JSON → 备份/恢复**。

---

## 1. 审阅结果采用什么数据格式保存？

采用**两层结构**，兼顾“不丢历史”与“读取快、易备份”：

| 层 | 文件 | 作用 | 写入方式 |
| --- | --- | --- | --- |
| ① 追加式流水账（权威） | `docs/author-review/review-records/journal.jsonl` | 每次保存**追加一行** JSON，永不覆盖 | append-only |
| ② 物化快照（派生） | `docs/author-review/review-records/snapshot.json` | 每篇的**当前最新**记录，由流水账重放得到 | 整体重写 |
| ③ 导出（派生） | `review-records/export-review-records.csv` / `.json` | 供作者下载 | 整体重写 |

单条记录字段（固定 schema）：

```json
{
  "candidate_id": "C0010",
  "status": "keep",            // keep | hold | exclude | pending
  "nature": "single_poem",     // single_poem | multi_poem | non_poem | unsure | unset
  "comment": "……中文意见……",
  "reviewer": "",              // 可选署名
  "updated_at": "2026-11-12T12:34:56+08:00",
  "rev": 3,                    // 该候选第几次保存（从 1 递增）
  "test": false                // 是否为测试记录（便于清理，不污染正式数据）
}
```

`status` / `nature` 用**英文枚举键**存储，界面显示中文标签，避免编码与别名问题。

---

## 2. 保存操作由什么程序或服务负责？

由**一个极小的本地 Python 服务**负责：`tools/review/serve_review.py`
（仅用 Python 标准库 `http.server`，无第三方依赖）。

- 它 = 静态文件服务（和现在一样）+ 一个 `/api/*` 的 JSON 接口。
- **关键前提（已实测）**：当前暴露的工作主机
  `work-1-…all-hands.dev` 会把 **POST 请求转发**到本地服务器
  （实测对静态服务器 POST 返回 501，说明请求确实到达了本地进程）。
  因此**无需数据库或云服务**即可实现真正的服务端持久化。
- 写入目标就是第 1 节的三个文件，全部在**工作区文件系统**上。

如果未来在**没有**写入转发能力的环境部署，本设计提供降级路径（见第 3、8 节）。

---

## 3. 如何保证结果不会只存在浏览器 localStorage？

- **权威数据在服务端文件**（`journal.jsonl` + `snapshot.json`）。
- 浏览器端**只做两件事**：
  1. 表单交互；
  2. 在 `localStorage` 里存一份**“未保存草稿”**，仅用于防止误刷新丢字。
- 保存成功与否**以服务端返回为准**：
  - 服务端写入成功 → 返回 `{ok:true, rev:N, updated_at:...}` → 界面显示“已保存（第 N 版）”。
  - 服务端失败/超时/返回非 2xx → 界面显示**“保存失败”**，并保留草稿。
- **绝不**把“写入 localStorage”当成保存成功。
- 服务端每次保存后**立即读回该文件校验**（read-after-write），确认落盘再回 `ok:true`。

---

## 4. 手机浏览器能否正常操作？

- 页面已带 `viewport`，表单用**大号触摸控件**（下拉/单选块 ≥ 44px 高）。
- 审阅结论、作品性质用**原生 `<select>`**（Android 上最稳、最易点、支持中文）。
- 意见框用 `<textarea>`，`inputmode` 默认文本，方便中文输入法。
- 保存按钮**固定在页面底部**（sticky），随时可见。
- 保存反馈用**文字 + 颜色**，不依赖悬停。
- 总目录：手机下表格可横向滚动，进度条与筛选按钮为大按钮。
- 验收时在移动视口（390×844 等）实测，而非只测桌面。

---

## 5. 页面重新打开后如何读取此前的审阅结果？

1. 打开作品页时，JS 调 `GET /api/review/<candidate_id>`。
2. 服务端从 `snapshot.json`（若缺则回放 `journal.jsonl`）取该条记录返回。
3. 表单**预填**已保存的值；若无记录，则为默认“待审阅 / 未设置 / 空”。
4. 页面同时显示“上次保存时间”。
5. 若服务端不可达，界面明确提示“无法读取历史记录（离线）”，不假装有数据。

---

## 6. 如何导出 CSV 和 JSON？

- 界面提供两个按钮：**导出 CSV**、**导出 JSON**，直接下载：
  - `GET /api/export.csv` → `export-review-records.csv`
  - `GET /api/export.json` → `export-review-records.json`
- 导出内容 = 全部 137 篇的**当前**审阅状态（未审阅的也列出，标为 `pending`），
  列：`candidate_id, title, published, category, status, status_label,
  nature, nature_label, comment, reviewer, updated_at, rev, reviewed(是否已审)`。
- 导出文件同时**落盘**到 `review-records/`，可随 Git 提交，便于长期归档。

---

## 7. 如何备份、恢复和迁移审阅数据？

- **备份**：三个文件（`journal.jsonl`、`snapshot.json`、`export-*`）都是普通文本，
  直接复制或随 Git 提交即可。`journal.jsonl` 是**追加式**，天然是完整历史。
- **恢复**：把 `journal.jsonl` 放回 `review-records/`，运行
  `python3 tools/review/rebuild_snapshot.py` 即可从流水账重建快照与导出。
- **迁移**：审阅记录**完全独立**于作品正文与候选 CSV；换环境只需搬运
  `review-records/` 目录。
- **兼容已有 CSV 字段**：`docs/author-review/poetry-candidates-author-review.csv`
  的“作者确认状态”列**只读**，导入时作为**初始值**参考，**绝不**被覆盖或删除；
  新审阅结果写入独立的 `review-records/`。

---

## 8. 如何避免审阅结果覆盖原始作品或原始候选数据？

- 原始作品正文来自 `work/feed/`（只读、且未纳入版本控制）与
  `docs/poetry-discovery/poetry-candidates.v2.csv`（只读）。
- 审阅系统**只写** `docs/author-review/review-records/` 下的三个文件。
- 生成脚本 `build_review_site.py` **从不修改**任何源 CSV；审阅页只是展示。
- 服务器对写入做**白名单校验**：只接受合法 `candidate_id` 与合法枚举值，
  拒绝其它路径/字段，避免越权写文件。
- 正式 Hugo 构建**不含** `/review/`（`enableReview=false`），审阅数据与审阅工具
  **不进入生产站**（已由 `build_preview.py` 隔离，并在验收中复验）。

---

## 9. 降级路径（若预览环境无写入能力时）

若某部署环境**不能**转发 POST（只能静态托管），则退化为：
界面在保存时**生成一个“审阅记录 JSON 文件”供下载**，作者把文件放回
`review-records/inbox/`，再运行导入脚本合并。此路径仍满足
“可保存、可恢复、可导出”，但需要多一步手动搬运。
本轮实测当前环境**支持 POST 转发**，故直接实现**服务端持久化**（首选方案）。

---

## 10. 验收对照

本设计直接覆盖任务书第三节（字段）、第四节（进度/筛选）、第五节（导出/备份）、
第六节（手机）、第七节（边界）、第九节（15 项验收测试）。
实现后将逐项测试并出具报告，测试记录一律带 `"test": true` 标记，测后清理。
