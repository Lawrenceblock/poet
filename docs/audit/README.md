# Phase C 审计材料索引

> 日期：2026-11-12 · 分支：`audit/phase-c-production-readiness-2026-11-12`
> 基线：`main` @ `ee94501`（本阶段**未修改** `main`）
> 性质：**只读审计 + 设计 + 临时目录实测**。未迁移真实作品，未改生产环境。

## 本目录文件

| 文件 | 用途 |
| --- | --- |
| `phase-c-author-review-audit.md` | 作者审阅系统审计（PR #6 的可靠性、可回写性、可追溯性） |
| `phase-c-production-readiness-audit.md` | 生产准备度、Vercel 部署、文学作品保护机制、整体架构建议 |
| `phase-c-legacy-archive-migration-plan.md` | 旧版网站静态归档到 `/legacy/` 的可行性与保护方案 |
| `legacy-content-url-migration-plan.csv` | 旧博客 305 篇文章的 URL 迁移规划表（一行一篇） |
| `phase-c-url-risk-summary.md` | 305 篇文章 URL 迁移风险总结 |
| `README.md` | 本索引 |

## 关键结论速览

1. **旧博客 URL 风险最高**：305 篇文章仅 **135 个不同 slug**，**199 篇**与其他文章重名；
   若新站用扁平 `/:slug/`，将产生 **170 处 URL 冲突**。建议改用 `/:year/:month/:slug/`（**0 冲突**，且与旧博客路径一致）。
2. **旧版网站只有 6 个 HTML 页面**（非“两三个”），静态归档到 `/legacy/` **技术可行**，
   但需修正绝对路径引用（仅改路径，不改文字）。
3. **作者审阅系统安全但不可回写**：审阅表会被生成脚本覆盖，需“生成视图 + 回复文件”分离。
4. **Jekyll 退出生产**：需先加 `exclude`（已实测泄漏 0），再切 Vercel，最后归档。
5. **Vercel 未部署**，全部部署结论标注为**未验证**。

## 边界遵守

- 未修改 `main`；未合并 PR；未部署；未改 DNS/域名/HTTPS/Vercel；未迁移真实作品；未改 `bio.ismaelan.com`。
- 临时实测在 `/tmp`（`hugo-legacy-test`、`preview-build`），**未提交**任何旧站/作品内容。
