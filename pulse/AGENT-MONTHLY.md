# Pulse 月报 — 每月发信 Agent 操作手册(The Monthly Digest)

每月 1 日由一个**独立的**云端 routine 执行一次:把上一个自然月评分最高的结构心条目汇编成一封**英文** HTML 邮件,通过 Buttondown 发给订阅者。

这是每日更新([AGENT.md](AGENT.md))与周报([AGENT-WEEKLY.md](AGENT-WEEKLY.md))之外的**第三条**流水线。月报**不搜集新数据**——只消费 `pulse/data/` 里已有的当月数据。

## 每月流程

1. **确定目标月**:取"昨天"的日期(每月 1 日运行时即上月最后一天),它所在的月记作 `YM=YYYY-MM`。
2. **生成邮件正文**:运行
   ```bash
   python3 pulse/make_monthly.py $YM
   ```
   它读取 `pulse/data/*.json`,选出该月所有条目,按评分(期刊影响力 + weight + type,与分享卡同一套)排序,写出 `pulse/monthly/YYYY-MM.html`(头条 + 其余 top 14),并把建议主题行打印为 `SUBJECT: ...`。**记下:文件路径 + 主题行。**
3. **质量闸门**:该月条目 **少于 5 条** 视为"淡月",**不发信**,只在总结说明。
4. **发送(Buttondown API)**:与周报完全同一套流程与密钥纪律(见 [AGENT-WEEKLY.md](AGENT-WEEKLY.md) 第 4 步),把 body 换成 `pulse/monthly/YYYY-MM.html`。**只有 HTTP 201/200 才算成功;失败读 /tmp/bd_resp.json 如实报告。**
5. **归档**:
   ```bash
   git add pulse/monthly && git commit -m "monthly: YYYY-MM digest" && git push
   ```
   除 `pulse/monthly/` 外**不改动仓库其他任何内容**。
6. **总结**:发了没、订阅者数、主题行、当月条数/天数;淡月未发或发送失败如实说明。

## 排期

- 建议 **每月 1 日 08:00 苏黎世时间**发出(在每日更新 04:00 UTC 与周报之后)。夏令时 cron `0 6 1 * *`,冬令时 `0 7 1 * *`。
- 若当月 1 日恰逢周一,月报与周报同日发出——没关系,内容颗粒度不同。

## 与其他线的关系

- 每日线:搜集 → 写 `pulse/data/` → push。
- 周报线:读数据 → `pulse/weekly/` → 群发。
- 月报线:读数据 → `pulse/monthly/` → 群发。
- 三条线共用同一份数据与评分逻辑,互不写对方的文件。
