---
title: "{{ replace .File.ContentBaseName `-` ` ` | title }}"
date: {{ .Date }}
# 可选字段（与旧站 Front Matter 兼容）：
# author: "安然"
# tags: ["诗歌"]
# note: "附注/题记（可选）"
# 双语作品请在同一文件中分段保留中英文，勿改动原文分行。
draft: true
---
<!-- 诗歌正文：逐字保留原文（标点、分行、空行、标题、署名）。
     需要保留换行时，可使用 poem 短代码或行尾双空格。 -->
