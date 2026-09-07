---
layout: default
title: 卷目
permalink: /archive/
---

<div class="archive">
  <div class="archive-title">卷一 · 未赴之境</div>
  <div class="archive-line"></div>

  {% for post in site.posts %}
    <div class="archive-item">
      <span class="idx">{{ forloop.index }}</span>
      <a href="{{ post.url | relative_url }}">{{ post.title }}</a>
      <span class="dots"></span>
      <span class="date">{{ post.date | date: "%Y.%m" }}</span>
    </div>
  {% endfor %}

  <div class="archive-line"></div>
  <div class="archive-footer">客栈启于丙午年秋 · 安然</div>
</div>
