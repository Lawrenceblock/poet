# Phase 1 · Hugo 框架本地构建验证记录（阶段标识：Phase 1 基础框架）

> 验证日期：**2026-11-12**
> 验证环境：`hugo v0.168.0-e27a6760c5547237f87d353aebe0580feadb20f4+extended linux/amd64`（Hugo **Extended**）
> 命令：`hugo build --minify --gc`（另以 `--buildDrafts` 验证样例页）

## 1. 构建结果（**【已验证事实】**）

| 检查项 | 结果 |
| --- | --- |
| 构建是否成功 | ✅ **成功**（exit 0，无 ERROR） |
| 模板错误 | ✅ **无** |
| 资源路径错误 | ✅ **无**（CSS/图片均生成） |
| 警告（warn） | ✅ **无**（修正了 `languageCode`/`languageName` 弃用警告与 sitemap 重复路径警告） |
| 弃用警告 | ✅ **无** |
| 占位/默认内容 | ✅ 仅一个明确标注的 `draft` 验证样例，**不含真实诗歌** |

## 2. 生成产物（生产构建，不含草稿）

```
public/404.html
public/archive/index.html          # /archive/
public/assets/img/cover.png        # /assets/img/cover.png
public/css/style.min.<hash>.css    # 经 Hugo Pipes 压缩+指纹
public/index.html                  # /
public/index.xml                   # RSS
public/posts/index.html            # 诗歌列表
public/posts/index.xml
public/preface/index.html          # /preface/
public/sitemap.xml
```

## 3. 逐项功能验证（**【已验证事实】**）

| 功能 | 验证方式 | 结果 |
| --- | --- | --- |
| 首页 | 生成 `index.html` | ✅ |
| 诗歌列表页 | `posts/index.html` + `archive/` 卷目 | ✅ |
| 单篇模板 | `single.html` → 标题/日期/正文/返回卷目 | ✅ |
| **诗歌分行保留** | 行尾换行 → `<br>`（`hardWraps=true`） | ✅ 实测 `<p>第一行<br>第二行…</p>` |
| **poem 短代码** | `{{< poem >}}` 逐行 `<br>`，空行保留 | ✅ 实测输出 `<div class="poem-verse">…<br>…</div>` |
| 中文排版 | 宋体衬线、行距 2.4、居中 | ✅ |
| 移动端响应式 | `<meta name="viewport" content="width=device-width,initial-scale=1">` | ✅ **已修复旧站缺失 viewport 的问题** |
| RSS Feed | `index.xml` 生成，仅含 `posts` 文章 | ✅ |
| Sitemap | `sitemap.xml` 生成 | ✅ |
| robots.txt | `layouts/robots.txt` → `public/robots.txt` | ✅（注：生产构建产物已含；见下） |
| canonical URL | 每页 `<link rel=canonical>` | ✅ |
| 404 页面 | `404.html` 生成 | ✅ |
| 基础导航 | 页头“卷目·题记·小传” + 页脚 | ✅ |
| 页面标题/元数据 | `<title>`、`description`、OG、author | ✅ |

## 4. URL 验证（**【已验证事实】**）

| 期望 URL | 生成结果 | 是否一致 |
| --- | --- | --- |
| `/archive/` | `public/archive/index.html` | ✅ |
| `/preface/` | `public/preface/index.html` | ✅ |
| `/<slug>/`（如 `/na-la-ti/`） | `public/<slug>/index.html` | ✅（**前提：Front Matter 显式 `slug`**） |

**关键发现**：Hugo **不**默认用文件名做 URL；若不显式指定 `slug`，会由**中文标题**生成中文 URL（与旧站不符）。已在 `docs/migration/url-compatibility.md` 记录并规定**每篇必须显式 `slug`**。

## 5. 尚未验证 / 待办

- **【待验证】** 真实诗歌正文迁入后的渲染（本阶段未迁移正文）。
- **【待验证】** Vercel 上使用 `HUGO_VERSION=0.168.0` 的实际构建。
- **【待验证】** 移动端真机渲染（仅本地 HTML 结构验证）。
- **【待决策】** 是否启用 tags/categories（当前关闭，避免空分类页）。
