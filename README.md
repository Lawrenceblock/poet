# 《安然诗客栈》运维备忘（2026-09-07）

## 一、站点基本信息

- **站名**：安然诗客栈
- **线上地址**：https://poet.ismaelan.com
- **GitHub 仓库**：Lawrenceblock/poet
- **默认备用地址**：https://lawrenceblock.github.io/poet/
- **框架**：Jekyll（GitHub Pages 自动构建）
- **核心逻辑**：写 Markdown → Git 推送 → 自动生成网页

---

## 二、目录结构（严禁乱放）

```
poet/
├─ index.html              ← 首页（含导航：卷目·题记）
├─ archive.md              ← 卷目页（自动生成目录，勿手写链接）
├─ preface.md              ← 题记页
├─ _posts/                 ← 【诗歌正文唯一存放地】
│   └─ 2026-09-07-na-la-ti.md
├─ _layouts/               ← 页面骨架（改样式改这里）
│   ├─ default.html        ← 全局底版
│   └─ post.html           ← 诗歌详情页模板（含"返回卷目"链接）
├─ assets/img/
│   └─ cover.png           ← 首页封面（透明背景）
├─ style.css               ← 全局样式（宋体/浅蓝底等）
├─ _config.yml             ← 站点配置文件（已定稿，少动）
└─ CNAME                   ← 自定义域名文件（勿删）
```

> ⚠️ **铁律**：
> - `archive.md` 和 `preface.md` **必须在根目录**，绝不可放进 `_posts`。
> - `_posts` 里的文件必须带日期前缀，如 `2026-09-07-xxx.md`。

---

## 三、核心机制说明（重点！）

### 1. 卷目自动生成（Liquid 语法）

`archive.md` 里用的是 Jekyll 的循环语法，不是手写 HTML：

```liquid
{% for post in site.posts %}
  <div class="archive-item">
    <span class="idx">{{ forloop.index }}</span>
    <a href="{{ post.url | relative_url }}">{{ post.title }}</a>
    <span class="dots"></span>
    <span class="date">{{ post.date | date: "%Y.%m" }}</span>
  </div>
{% endfor %}
```

**效果**：只要在 `_posts` 里加了新诗，`git push` 后卷目页会自动出现新链接。

### 2. 链接规则（防 404 核心）

- **站内链接一律不带 `.md` 或 `.html` 后缀**。
- **自定义域名下**，链接直接写根路径：
  - 卷目：`/archive/`
  - 题记：`/preface/`
  - 首页：`./` 或 `/`
- **诗歌页返回卷目**：在 `_layouts/post.html` 中写 `<a href="/archive/">← 卷目</a>`。

### 3. Permalink（永久链接）

- `archive.md` 头部：`permalink: /archive/`
- `preface.md` 头部：`permalink: /preface/`
- 诗歌正文：由 Jekyll 按日期自动生成，如 `/2026/09/07/na-la-ti/`。

---

## 四、日常写诗与发版流程

### 1. 写新诗

1. 在 `_posts/` 下新建文件，命名格式：`2026-09-08-诗名拼音.md`。
2. 头部必须包含：

   ```markdown
   ---
   layout: post
   title: 诗名
   date: 2026-09-08
   ---
   ```

3. 下方直接写诗（Markdown 格式）。

### 2. 推送上线（四步曲）

在 VS Code 终端执行：

```powershell
git status          # 查看改动
git add .           # 添加所有改动
git commit -m "add: 新诗名"   # 提交（备注写清楚）
git push            # 推送到 GitHub
```

4. 等待 1–2 分钟，刷新浏览器（`Ctrl+F5` 强刷）。

---

## 五、常见坑位与急救包

### 1. 页面 404

- 检查链接是否带了 `.md` 或 `.html`（应改为 `/archive/` 格式）。
- 检查 `archive.md` / `preface.md` 是否在根目录，且头部有 `permalink`。
- 执行 `Ctrl + F5` 清除缓存。

### 2. Push 时报错 `Connection was reset`

- 网络问题，重试 `git push` 即可。
- 若持续失败，检查代理或切换网络（如手机热点）。

### 3. 自定义域名失效

- 确保 DNS 中 `poet` 的 CNAME 指向 `lawrenceblock.github.io.`。
- 确保仓库根目录 `CNAME` 文件内容为 `poet.ismaelan.com`。
- 若 GitHub Pages 显示 DNS 检查失败，**删除 Custom domain 并重新填写**可强制刷新状态。

### 4. 样式错乱

- 只改 `style.css`，勿动 `_layouts` 里的结构，除非你清楚 HTML。

---

## 六、关键配置快照（_config.yml）

```yaml
title: 安然诗客栈
author: 安然
url: "https://poet.ismaelan.com"
baseurl: ""
markdown: kramdown
permalink: /:title/
```

---

## 七、求助话术模板

以后如果遇到问题，可以直接把下面这段话发给元宝：

> "元宝，这是我《安然诗客栈》的备忘（附上本文件内容）。我现在遇到的问题是：______。目前的报错/现象是：______。请根据之前的架构帮我看看。"

---

## 八、特别备注

今天踩过的坑，都是资深运维才会遇到的：

- 发现了 **GitHub Pages 先填域名后配 DNS 会卡死** 的规律。
- 理清了 **Jekyll 的 `permalink` 与物理文件路径的区别**。
- 成功配置了 **自定义域名 + HTTPS**。

**现在已经不是初学者了。** 这份备忘是"剑谱"，剑法已经练成。🌿
