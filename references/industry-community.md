# 行业包：社区、物业、居委会、社团

id 是 `community`。物业服务中心、居委会、业委会、小区社群和各类社团自己做的物料。特点是信息要清楚、语气要客气，看的人从年轻人到老人都有，字一定要大。

## 默认方向

| 场景 | 首选方向 | 备选 | 默认插画 motif |
|---|---|---|---|
| 物业通知、停水停电、维修 | trust-blue | clean-minimal | building、calendar |
| 社区活动、志愿者招募 | campus-fresh | pop-fresh、warm-hand | megaphone、heart |
| 传统节日活动、敬老 | guochao | festive-red、warm-hand | lantern、peach |
| 社团招新、兴趣小组 | pop-fresh | campus-fresh、sport-bold | megaphone |
| 表彰、感谢信 | trust-blue | festive-red、campus-fresh | medal、laurel |

## 高频需求和对应物料

- 停水、停电、停气、电梯维修、消杀通知：poster 的 notice 版式。关键信息（时间、范围、原因）放进信息框，正文写注意事项。张贴用 a4，业主群用 portrait
- 放假和节日值班安排：notice 版式，加上 festival 节日包
- 垃圾分类、文明养犬、防诈骗宣传：poster editorial 或 type-hero，标题一句话说清楚要大家做什么
- 社区活动、义诊、便民服务日：poster editorial，时间地点写进 details
- 志愿者感谢信、优秀业主表彰：certificate modern，title 改成"感谢信"，recipient_suffix 留空，可以批量
- 社团招新：poster type-hero，cta 写怎么报名，配群二维码
- 值班表、保洁排班：menu list，不写价格

## 文案套路

- 通知的标题直接写结果，"10 月 16 日 3 号楼至 8 号楼停水"比"关于停水的通知"有用得多
- kicker 用两到四个字的类别，"停水通知""温馨提示""放假通知"
- 正文第一段"尊敬的各位业主："单独成段，不缩进，脚本会自动处理
- 正文按原因、要大家做什么、致歉这个顺序写，每段两三句
- 落款写单位全称加日期，服务电话放 cta
- 感谢信说具体做了什么，"每天早晚在垃圾房值守"比"积极参与社区工作"动人

## 必须问到的事实

单位全称、具体时间段、影响范围（楼栋、单元）、原因、联系电话、发布日期。少一个都不能编，留占位。

## 注意事项

- 字号宁大勿小。A4 张贴在电梯和单元门口，正文不要缩到很小，放不下就删字
- 不写业主的门牌号加全名，表彰物料只写姓氏加称呼（"张阿姨"）或用户明确同意的全名
- 收费、催缴类通知只写事实和依据，不用威胁语气，不公开欠费业主的信息
- 公章只留"盖章处"，不画任何仿制印章
- 消防、燃气类安全提示，具体数据和规定以主管部门的文件为准，不自己编

## 一个完整的例子

用户："下周三小区要清洗水箱，3 到 8 号楼停水一天，帮我出个通知，贴电梯里也发群里。"

- 推断：方向 trust-blue，poster notice，尺寸 a4 和 portrait，motif building
- 必须要：具体日期和起止时间、物业名称、服务电话、发布日期
- 物料：water（notice），details 三行写停水时间、影响范围、停水原因，正文写储水和关龙头的提醒
