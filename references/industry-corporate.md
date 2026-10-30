# 行业包：企业行政、HR 和老板

id 是 `corporate`。公司内部和对外的日常物料：年会、表彰、招聘、通知、节日福利。

## 默认方向

| 场景 | 首选方向 | 备选 | 默认插画 motif |
|---|---|---|---|
| 年会、晚宴 | dark-premium | festive-red、editorial | laurel、trophy |
| 春节、周年庆 | festive-red | dark-premium、guochao | gift、laurel |
| 年度表彰、优秀员工 | festive-red | dark-premium、trust-blue | trophy、medal |
| 招聘 | trust-blue | pop-fresh、clean-minimal | briefcase |
| 通知公告 | trust-blue | clean-minimal | calendar |

公司有自己的品牌色时，在 brand.tokens 里覆盖 accent，其余用方向的颜色。公司有 logo 文件就放进 brand.logo。

## 高频需求和对应物料

- 年会邀请函：invitation，formal 最常用。给重要客户的版本用 batch 一人一张，带上称呼
- 表彰证书：certificate，batch 列获奖名单，每人奖项不同，证书编号用 {n} 自动编号
- 招聘海报：poster type-hero，标题写岗位，details 写薪资范围、地点、要求，cta 写投递方式
- 通知公告：poster editorial，标题写事情，正文写时间和安排
- 节日福利、团建：poster product-hero

## 文案套路

- 年会邀请的正文两三句话，回顾这一年，再说邀请，别写成工作报告
- 表彰证书正文："在 2026 年度工作中……特授予……荣誉称号"
- 招聘写清楚岗位职责和真实薪资范围，比"薪资面议"更能招到人

## 必须问到的事实

公司名称、日期地点、获奖名单和奖项、招聘岗位和薪资、联系人。

## 禁忌和合规

- 招聘信息不能有性别、年龄、婚育、地域等歧视性条件："限男""35 岁以下""已婚已育""本地户口"，检查脚本会报错
- 证书留"盖章处"，公司公章由行政盖，skill 不画仿制的公章
- 对外物料不写"行业第一""最大""领先"，除非有权威出处，就算有也建议换成具体事实
- 年会邀请里的嘉宾姓名要逐个核对

## 一个完整的例子

用户："公司 1 月 16 号年会，帮我做邀请函，再做几张年度表彰的证书。"

- 推断：方向 dark-premium，备选 festive-red、editorial
- 缺：地点、时间、着装要求、联系人、获奖名单和奖项
- 物料：gala（invitation formal，portrait + a5），honor（certificate classic，batch 列名单，a4-landscape）
