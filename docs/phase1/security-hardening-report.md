# P1-D · 审阅系统安全加固报告

- 日期：2026-11-12
- 目标文件：`tools/review/serve_review.py`
- 结论：**已修复 3 项访问控制/日志问题；真实审阅数据 SHA 全程未变**

## 1. 修复项（【已验证】）

### N1 · HEAD / OPTIONS 绕过令牌
- 问题：`SimpleHTTPRequestHandler` 的 `do_HEAD` 不走 `do_GET`，原实现未对 HEAD 校验令牌，可据此探测 `/review/` 页面是否存在。
- 修复：新增 `do_HEAD` / `do_OPTIONS`，对**需要授权的路径**执行同一令牌校验；未授权返回 401。

### N2 · 访问日志泄露令牌
- 问题：访问日志按请求行记录，若 URL 带 `?token=...`，令牌会写进日志。
- 修复：日志输出前剥离查询串（只记录路径与状态码）；令牌永不出现在日志中。

### N3 · `?token=` 长期驻留
- 问题：令牌作为查询参数打开后会留在浏览器历史与分享链接中。
- 修复：URL 携带令牌时校验通过后 **303 重定向**到去掉令牌的同路径；通过 Cookie 维持会话。

## 2. 授权范围收敛（【已验证】）

- 仅 `/review/` 与 `/api/` 需要令牌；**阅读页（`/`、`/archive/`、`/preface/`、`/search/` 等）保持公开**。
- 目的：作者私密审阅与公开阅读互不干扰。

## 3. 验证（【已验证】）

`tools/review/test_review_system.py`（新增测试 15–17）：

```
15. 令牌门禁
  [PASS] 无令牌 -> /api/reviews 401
  [PASS] 无令牌 -> /review/ 401
  [PASS] 带头令牌 -> 200
  [PASS] 错误令牌 -> 401
  [PASS] 无令牌 -> Cookie -> 200
  [PASS] ?token= -> 303（URL 已剥离）
  [PASS] HEAD 无令牌 -> 401
  [PASS] HEAD 有令牌 -> 200
  [PASS] OPTIONS 无令牌 -> 401
16. 访问日志不含令牌
  [PASS] 日志中无令牌
  [PASS] 非 2xx 仍被记录
17. 阅读页开放、/review/ 受控
  [PASS] / 200  [PASS] /archive/ 200  [PASS] /search/ 200  [PASS] /review/ 401
OK: all review-system tests passed
```

线上实测（临时域名）：公开页 200；`/review/` 无令牌 401、带令牌 200。

## 4. 数据安全（【已验证】）

- 加固前后 `docs/author-review/review-records/journal.jsonl` 的 SHA-256 始终为
  `7f311871818e8b15a49654171f4ea20de726cc5879f513f1a257f5f5cb7ccb4d`（23 行，19 条唯一候选）。
- 端到端写入测试使用 `?test=1` 隔离通道，写入 `journal-test.jsonl`（已 git-ignore），**未污染真实记录**；测试后已清理该文件。

## 5. 边界声明

- 未修改任何审阅记录、诗歌内容、站点配置或线上部署。**【已验证】**
