# Pulse 周报 — 每周发信 Agent 操作手册(The Monday Briefing)

每周一由一个**独立的**云端 routine 执行一次:把上一周(刚结束的 ISO 周,周一–周日)评分最高的结构心条目汇编成一封**英文** HTML 邮件,通过 Buttondown 发给订阅者。

这是每日更新(见 [AGENT.md](AGENT.md))之外的**第二条**流水线。周报**不搜集新数据**——它只消费 `pulse/data/` 里已经存在的当周数据。

## 每周流程

1. **确定目标周**:取"昨天"的日期(周一运行时即上周日),记作 `SUN=YYYY-MM-DD`。该日期落在哪个 ISO 周,脚本就汇总那一整周。
2. **生成邮件正文**:运行
   ```bash
   python3 pulse/make_weekly.py $SUN
   ```
   它会读取 `pulse/data/*.json`,选出该 ISO 周内所有条目,按评分(期刊影响力 + weight + type,与分享卡同一套)排序,写出 `pulse/weekly/YYYY-Www.html`,并把建议主题行打印为 `SUBJECT: ...`。**记下这两样:文件路径 + 主题行。**
3. **质量闸门**:如果该周条目 **少于 2 条**,视为"淡周",**不发信**,只在总结里说明。宁可不发,也不发一封空briefing。
4. **发送(Buttondown API)**:密钥从环境变量 `BUTTONDOWN_API_KEY` 读取(**绝不出现在仓库、日志、总结里**)。用 `pulse/weekly/YYYY-Www.html` 的内容做 body、上一步的 SUBJECT 做 subject,POST 到 Buttondown:
   ```bash
   BODY=$(cat pulse/weekly/YYYY-Www.html)
   curl -s -o /tmp/bd_resp.json -w "%{http_code}" \
     -X POST "https://api.buttondown.com/v1/emails" \
     -H "Authorization: Token $BUTTONDOWN_API_KEY" \
     -H "Content-Type: application/json" \
     --data "$(python3 -c 'import json,sys; print(json.dumps({"subject": sys.argv[1], "body": open(sys.argv[2]).read(), "status": "about_to_send"}))' "$SUBJECT" pulse/weekly/YYYY-Www.html)"
   ```
   - `status: "about_to_send"` = 立即群发给所有确认订阅者。
   - **只有 HTTP 201/200 才算成功**。若是 404,改用 `https://api.buttondown.email/v1/emails` 重试(域名迁移期两者可能并存);其他错误码把 `/tmp/bd_resp.json` 的报错读出来写进总结,**不要谎报成功**。
   - 邮件正文里有 `{{ unsubscribe_url }}` 模板标记,Buttondown 会自动替换成一键退订链接,勿改。
5. **归档(可选,推荐)**:把 `pulse/weekly/YYYY-Www.html` 提交进仓库,作为公开的往期存档(未来可在站内做 /pulse/weekly/ 索引页,利于 SEO 与回访):
   ```bash
   git add pulse/weekly && git commit -m "weekly: YYYY-Www briefing" && git push
   ```
   除 `pulse/weekly/` 外**不改动仓库其他任何内容**。
6. **总结**:报告发了没、发给多少订阅者(响应里有)、主题行、当周收录条数;若淡周未发或发送失败,如实说明原因。

## 密钥怎么配(一次性,用户操作)

`BUTTONDOWN_API_KEY` 作为**环境密钥**存进云端环境,不进仓库、不进 prompt:
- 在 https://claude.ai/code 的 Environments/routine 设置里,给本 routine 所用环境添加密钥 `BUTTONDOWN_API_KEY = <你的 Buttondown API key>`(Settings → Programming/API 里获取)。
- 之后 agent 用 `$BUTTONDOWN_API_KEY` 引用即可。
- 若密钥泄露,在 Buttondown 里 regenerate,再更新这里的环境密钥。

## 排期

- 建议 **每周一 07:00 苏黎世时间**发出。夏令时(CEST)= UTC 05:00 → cron `0 5 * * 1`;冬令时(CET)= UTC 06:00 → `0 6 * * 1`。当前(7 月)用 `0 5 * * 1`。
- 必须晚于当日的每日更新 routine(04:00 UTC),以免与写数据竞争。周报只读数据,风险低。

## 与每日线的关系

- 每日线:搜集 → 写 `pulse/data/` → 重画分享卡 → push(见 [AGENT.md](AGENT.md))。
- 周报线:读 `pulse/data/` → 生成 HTML → Buttondown 群发 →(可选)归档 push。
- 两条线共用同一份数据与评分逻辑,互不写对方的文件。
