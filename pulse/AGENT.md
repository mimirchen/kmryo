# Pulse 每日焦点 — 更新 Agent 操作手册

本目录驱动 kmryo.com 主页的「结构心 · 每日焦点」拼图墙。每天由自动 agent 执行一次以下流程。

## 每日流程

1. **搜索当天(欧洲中部时间)的结构性心脏病重点信息**,三类来源:
   - **期刊**:NEJM、Lancet、JAMA、JAMA Cardiology、Circulation、EHJ、JACC 及子刊(Interventions / Imaging / Case Reports)、EuroIntervention、Circ: Cardiovascular Interventions、JSCAI、Structural Heart。主题限结构性心脏病:TAVI/TAVR、二尖瓣(TEER/TMVR)、三尖瓣介入、LAA 封堵、PFO/ASD、瓣膜耐久性、结构介入影像与 AI。
   - **会议**:TCT、EuroPCR、PCR London Valves、New York Valves、TVT、CSI 等的 late-breaking 发布与重要日程消息。
   - **社媒/新闻/监管**:TCTMD、Medscape、theheart.org 的热点;#CardioTwitter 热议;FDA/CE 审批;器械公司重要公告(Edwards、Medtronic、Abbott、Boston Scientific、JenaValve、Jenscare 等)。
2. **只收录真实、可验证的条目**:每条必须有能打开的 URL。宁缺毋滥,严禁编造标题/数据/链接。典型每天 4–10 条;确实没有大新闻时可以少于 4 条。
3. **写入数据文件** `pulse/data/YYYY-MM-DD.json`(格式见下)。
4. **更新 `pulse/data/manifest.json`**:把新日期追加进 `days` 数组(保持升序,勿删旧日期)。
5. **提交并推送**:`git add pulse/data && git commit -m "pulse: YYYY-MM-DD daily update" && git push`。GitHub Pages 约 1 分钟后生效。
6. 除 `pulse/data/` 外**不得改动仓库其他任何文件**。

## 数据格式

`pulse/data/YYYY-MM-DD.json`:

```json
{
  "date": "2026-07-16",
  "items": [
    {
      "date": "2026-07-16",
      "title": "英文原标题",
      "title_zh": "中文标题",
      "summary_zh": "2-3 句中文摘要:研究设计、核心结果(带关键数字)、临床意义。",
      "summary_en": "REQUIRED 1-2 sentence English summary (shown when the site is in EN mode). 英文界面显示它,绝不能留空或塞中文。",
      "source": "NEJM",
      "type": "journal",
      "topic": "TAVI",
      "weight": 4,
      "url": "https://...",
      "image": "(可选) 一张可公开、可外链的图片 URL 或 data:URI"
    }
  ]
}
```

字段约定:

- `type`: `journal` | `conference` | `regulatory` | `industry` | `social` | `news` | `guideline`(决定卡片色带与刊名品牌色)。
- `topic`: `TAVI` | `Mitral` | `Tricuspid` | `LAA` | `Imaging` | `Other`(决定原创示意插图)。
- `title` / `title_zh`:英文原标题 / 中文标题,两者都必填。
- `summary_en` / `summary_zh`:两者都必填。英文界面只显示 `summary_en`,中文界面只显示 `summary_zh`,**严禁在任一字段里混入另一种语言**。
- `image`(可选):仅当存在**可合法公开外链**的开放获取图(如开放的 graphical abstract)时才填。**不要抓取/外链期刊付费或受版权保护的 central illustration 原图**(会侵权且经常加载失败)。留空时前端自动按 `topic` 渲染原创示意插图。
- `source`:显示为刊名 masthead;前端按来源匹配品牌色与影响因子。若来源不在内置表内,会原样显示来源名,可正常工作。
- `weight` 1–5,与来源影响力、传播热度一起决定拼图卡片大小(前端综合评分):
  - **5** 改变实践的大型 RCT / 重磅审批(每天至多 1 条)
  - **4** 重要 RCT / 大型注册研究 / late-breaking / 重要指南
  - **3** 值得读的研究或重要行业新闻
  - **2** 较小研究、病例系列、观点文章
  - **1** 简讯、社媒热议
- `manifest.json`: `{ "updated": "YYYY-MM-DD", "days": [...], "weeks": [], "months": [], "years": [] }`。`weeks/months/years` 为后续周报/月报/年报预留,暂不填。

## 质量标准

- 中文摘要必须包含关键数字(样本量、主要终点、HR/p 值等,如适用)。
- 同一研究多来源报道时只收一条,URL 指向最原始来源(期刊页 > 会议官网 > 新闻报道)。
- 观点与争议类条目在摘要中说明"为什么圈内在讨论"。
