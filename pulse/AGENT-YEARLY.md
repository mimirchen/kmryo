# Pulse 年报 — 年度回顾 Agent 操作手册(The Year in Structural Heart)

每年 1 月 2 日由一个**独立的**云端 routine 执行一次:把刚结束的自然年里最重要的结构心条目汇编成一封**英文**年度回顾邮件(Story of the Year + 按主题分节的年度精选),通过 Buttondown 发给订阅者。

这是第四条流水线,与每日([AGENT.md](AGENT.md))、周报([AGENT-WEEKLY.md](AGENT-WEEKLY.md))、月报([AGENT-MONTHLY.md](AGENT-MONTHLY.md))并列。年报**不搜集新数据**。

## 每年流程

1. **确定目标年**:目标年 `Y` = 今天年份 − 1(1 月 2 日运行,回顾刚结束的上一年)。
2. **生成邮件正文**:运行
   ```bash
   python3 pulse/make_yearly.py $Y
   ```
   它读取 `pulse/data/*.json`,选出该年所有条目排序,写出 `pulse/yearly/YYYY.html`:整体头条(Story of the Year)+ 六个主题区(Aortic/TAVI、Mitral、Tricuspid、LAA、Imaging、Other)各 top 5,并打印 `SUBJECT: ...`。
3. **质量闸门**:年报原则上**总是发**;仅当全年条目少于 10 条时不发,总结说明。
4. **发送(Buttondown API)**:与周报同一套流程与密钥纪律(见 [AGENT-WEEKLY.md](AGENT-WEEKLY.md) 第 4 步),body 换成 `pulse/yearly/YYYY.html`。**只有 HTTP 201/200 才算成功;失败如实报告。**
5. **归档**:
   ```bash
   git add pulse/yearly && git commit -m "yearly: YYYY in review" && git push
   ```
   除 `pulse/yearly/` 外**不改动仓库其他任何内容**。
6. **总结**:发了没、订阅者数、主题行、全年条数/覆盖天数。

## 排期

- 建议 **每年 1 月 2 日 08:00 苏黎世时间**(冬令时 = UTC 07:00)→ cron `0 7 2 1 *`。
- 避开 1 月 1 日,给月报(12 月月报,1 月 1 日发)留出间隔,订阅者两天各收到一封,内容不同。

## 与其他线的关系

四条线共用同一份 `pulse/data/` 与评分逻辑,互不写对方的文件。
