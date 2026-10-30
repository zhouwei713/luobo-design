# 行业包：婚宴庆典

id 是 `celebration`。婚礼、订婚、满月宴、生日宴、寿宴、升学宴、乔迁宴。做物料的大多是新人和家里人，自己没时间找设计，又想要体面。

一场宴席通常要一整套：请柬、桌号牌、席位卡，有时还要迎宾海报。同一份 spec 放在一起，风格自然统一。

## 默认方向

国内说起请柬，大多数人默认就是红的。用户没提风格时一律从喜事红（xi-red）开始，正红底配金字，带囍字和细金框，看三个方向时再放一个森系浪漫和一个新中式，给想要素一点的人留个选择。用户自己说了"西式""草坪""简约""不要太红"，才把 garden-romance 放到第一位。

| 场景 | 首选方向 | 备选 | 默认插画 motif |
|---|---|---|---|
| 婚礼、订婚、回门宴（没说风格） | xi-red | guochao、garden-romance | double-happiness（囍）、rings |
| 西式、草坪、简约婚礼 | garden-romance | clean-minimal、soft-pastel | rings、bouquet |
| 寿宴、敬老 | xi-red | guochao、warm-hand | peach |
| 满月、百日、周岁 | xi-red | soft-pastel、garden-romance | heart、gift |
| 生日派对 | pop-fresh | soft-pastel、dark-premium | birthday-cake |
| 升学宴、谢师宴 | campus-fresh | festive-red、editorial | grad-cap、trophy |

## 高频需求和对应物料

- 请柬：invitation。formal 端庄，适合婚礼和寿宴；split 有一块大色面，适合生日和满月。发微信用 portrait 或 story，印刷用 a5。一位宾客一张，用 batch 列名字，称呼写进 guest（"王叔叔、王阿姨"）
- 桌号牌：tablecard number，见 @references/item-tablecard.md。每桌一张，可以把这桌的宾客名写上
- 席位卡：tablecard tent，对折立在桌上，正反两面都是名字
- 电子请柬 H5：h5 invite，见 @references/item-h5.md。发微信时比图片好用，宾客点一下就能导航、加日历、回复出席，每人一条带称呼的链接。印刷请柬和 H5 放在同一份 spec 里，风格自动一致
- 迎宾海报、签到处指示：poster editorial，big_number 放日期
- 答谢卡、回礼卡：card 或 poster square

## 文案套路

- 请柬标题口语一点更有温度，"我们结婚啦""奶奶八十岁了，请您来吃寿面"
- 正文一两句讲故事，再说邀请，"从校园到今天，我们一起走过了九年"
- details 写时间和地点，时间精确到迎宾和开席，地点写到厅名
- rsvp 写回复截止日期，closing 写"恭候光临"一类的话
- 寿宴落款常用"某某携儿孙敬邀"，满月宴常用"某某、某某携小儿/小女"

## 必须问到的事实

主人的名字（新人、寿星、宝宝）、日期和时间、酒店和厅名、宾客名单（批量时）、每桌的安排（桌号牌写名字时）、回复截止日期。

## 注意事项

- 宾客名单是私人信息。批量请柬和席位卡只用在这一单里，交付时提醒用户别把带全部名单的总览图发到群里
- 名字错一个字很失礼，批量出完逐个核对
- 婚礼日期常有讲究，按用户给的写，不替用户算"好日子"
- 中式喜事避开大面积黑白，丧事物料这个行业包不做
- festive-red 是给开业促销用的，放射光芒和活泼的标题字不适合请柬。喜事用 xi-red，排请柬和桌号牌时脚本也会自动去掉放射光芒
- 新人照片要两个人都同意再用；宝宝照片不放进要公开转发的物料

## 一个完整的例子

用户："我们五月二十二号在西湖国宾馆办婚礼，想要电子请柬，再做一下桌号牌和席位卡。"

- 推断：用户没说风格，方向 xi-red，三选一时放 garden-romance 和 guochao。invitation formal 出 portrait 和 a5，tablecard number 和 tent，motif double-happiness
- 必须要：新人名字、具体时间、厅名、宾客称呼名单、每桌宾客、回复截止日期
- 物料：invite（batch 按宾客），table（number，batch 按桌，guests 列宾客），name（tent，batch 是名字列表）。用户说"电子请柬"或要发微信，再加一件 h5（invite），when、venue、address、rsvp_url 要问到
