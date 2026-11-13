# 旧 Jekyll 站点隔离提案（**建议，未实施于 main**）

> 日期：2026-11-12
> 状态：**【建议】** 本提案**未**应用到 `main`，`main` 的 `_config.yml` **未修改**。
> 目的：在 Hugo 迁移期间，保证旧站构建**不会把新站源码当作页面发布**。

## 1. 问题（已实测复现）

旧站由 **Jekyll** 构建，默认会处理仓库根目录下**除 `_`/`.` 开头及 `exclude` 之外**的所有文件。

在**包含 `hugo/` 目录的分支**上本地运行 `jekyll build`，结果：

```
_site/hugo/layouts/index.html
_site/hugo/layouts/shortcodes/poem.html
_site/hugo/archetypes/posts/index.html
_site/hugo/README-HUGO.md
_site/hugo/assets/css/style.css
_site/docs/migration/...            # docs/ 同样泄漏
```

即：**Hugo 模板、README、文档会被当作旧站页面输出**（`hugo/layouts/*.html` 尤其会生成垃圾页面）。

> 复现命令（只读、临时目录）：
> ```bash
> git archive HEAD | tar -x -C /tmp/jekyll-iso && cd /tmp/jekyll-iso && jekyll build
> find _site/hugo _site/docs -type f   # 泄漏 14 + 4 个文件
> ```

## 2. 提案：在 `_config.yml` 的 `exclude` 增加条目

```yaml
exclude:
  - README.md
  - "元宝代码"
  - vendor
  - Gemfile
  - Gemfile.lock
  # ↓ 新增（隔离新站与内部文档，不参与旧站构建）
  - hugo
  - docs
  - tools
  - PROGRESS.md
```

## 3. 验证（已在临时目录实测）

对上述 `exclude` 打补丁后重跑 `jekyll build`：

| 检查项 | 结果 |
| --- | --- |
| `_site/hugo/` 文件数 | **0** |
| `_site/docs/` 文件数 | **0** |
| `_site/tools/` 文件数 | **0** |
| `_site/PROGRESS.md` | **已排除** |
| 旧站页面是否仍生成 | ✅ `/`、`/archive/`、`/preface/`、`/na-la-ti/`、`/qing-chun-de-wu-yu/`、`/shi-ren-xiao-zhuan/` 均在 |

## 4. 风险与替代方案

- **风险**：若 `hugo/` 合入 `main` 而**未**加 `exclude`，旧站会发布 Hugo 源文件（含模板）。
  - 影响：产生垃圾 URL、可能暴露内部结构；**不影响诗歌正文**。
  - 等级：**中**（可用性/整洁问题，非内容损坏）。
- **替代**：先切换 GitHub Pages 发布源为 Hugo 构建产物，再合入 `hugo/`；或把 `hugo/` 放在**独立仓库**。
- **本阶段不做**：不修改 `main`、不改 Pages 设置。仅提交提案与实测证据。
