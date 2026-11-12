/* 站内搜索：纯前端，读取 /index.json，无第三方依赖。 */
(function () {
  var input = document.getElementById("search-input");
  var status = document.getElementById("search-status");
  var results = document.getElementById("search-results");
  if (!input || !results) return;

  var index = null;

  function load() {
    var base = document.body.getAttribute("data-baseurl") || "/";
    var url = base.replace(/\/$/, "") + "/index.json";
    return fetch(url).then(function (r) {
      if (!r.ok) throw new Error("HTTP " + r.status);
      return r.json();
    }).then(function (data) {
      index = data;
      if (status) status.textContent = "已载入 " + data.length + " 条作品索引。";
    }).catch(function (e) {
      if (status) status.textContent = "无法载入搜索索引：" + e.message;
    });
  }

  function render(q) {
    results.innerHTML = "";
    if (!index) return;
    q = (q || "").trim().toLowerCase();
    if (!q) { if (status) status.textContent = ""; return; }
    var hits = index.filter(function (item) {
      return (item.title || "").toLowerCase().indexOf(q) !== -1 ||
             (item.content || "").toLowerCase().indexOf(q) !== -1;
    });
    if (status) status.textContent = "找到 " + hits.length + " 条结果。";
    hits.slice(0, 50).forEach(function (item) {
      var li = document.createElement("li");
      li.className = "archive-item";
      var a = document.createElement("a");
      a.href = item.url;
      a.textContent = item.title;
      li.appendChild(a);
      var d = document.createElement("span");
      d.className = "date";
      d.textContent = item.date || "";
      li.appendChild(d);
      results.appendChild(li);
    });
  }

  input.addEventListener("input", function () { render(input.value); });
  load().then(function () {
    var q = new URLSearchParams(location.search).get("q");
    if (q) { input.value = q; render(q); }
  });
})();
