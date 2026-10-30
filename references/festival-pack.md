# 节日包

节日不算行业，它是叠在任何行业上的一层皮。奶茶店的春节海报、律所的元旦放假通知、幼儿园的六一邀请函，用的都是自己行业的方向和版式，再在 spec 顶层加一个 `festival`。

```json
"festival": {"id": "spring-festival", "mode": "full"}
```

也可以只写 id，`"festival": "spring-festival"`，这时用节日自己的默认 mode。

## 两种叠法

**full** 换上节日配色。春节变红金，圣诞变深绿暖红，底纹换成节日的（祥云、雪花、爱心、彩纸、星星）。适合一次性的节日海报，店铺平时的颜色不重要。

**accent** 保留品牌自己的底色、文字色和强调色，只借节日的辅助色和底纹。适合连锁店、有成熟品牌色的公司，节日物料还要一眼认得出是谁家的。

拿不准时不用问，直接跑 directions.py。spec 里有 festival 又没写 direction_candidates 时，三个选项会自动变成这样：

- A 品牌原来的方向，换上节日配色
- B 品牌原来的方向，保留品牌色，只加节日点缀
- C 节日推荐的另一个方向，用它自己的配色加节日点缀

用户看图选完，把选中的方向写回 brand.direction，mode 写进 festival。无人值守时按 festivals.json 里的默认 mode。

## 节日包会自动做的事

- 物料没写 art.motif 也没给图片时，用节日的默认插画（春节灯笼、中秋月饼、端午粽子、圣诞树……）
- 生图提示词里加上节日元素和氛围词
- 品牌小卡（brand.json）不会记下节日配色，节后做的物料自动回到原来的颜色

## 支持的节日

id 和日期都在 @references/festivals.json。农历节日的日期按年份写死，已核对过公历对照表；每年的法定放假安排不存，由国务院办公厅每年公布，物料里写放假日期前一定和用户确认，公布前别写死。

| id | 节日 | 日期 | 默认叠法 | 推荐方向 |
|---|---|---|---|---|
| double-ninth | 重阳节 | 2026-10-18，2027-10-08 | full | guochao、warm-hand |
| double-11 | 双十一 | 11-11 | full | pop-fresh、festive-red |
| thanksgiving | 感恩节 | 2026-11-26 | accent | warm-hand、clean-minimal |
| winter-solstice | 冬至 | 2026-12-22 左右，按当年历书确认 | accent | guochao、clean-minimal |
| christmas | 圣诞节 | 12-25 | full | dark-premium、warm-hand、festive-red |
| new-year | 元旦 | 01-01 | full | dark-premium、editorial、festive-red |
| laba | 腊八节 | 2027-01-15 | accent | guochao、warm-hand |
| little-new-year | 小年 | 北方 2027-01-30，南方 01-31 | full | festive-red、guochao |
| spring-festival | 春节 | 2027-02-06，除夕 02-05 | full | festive-red、guochao、dark-premium |
| lantern | 元宵节 | 2027-02-20 | full | guochao、festive-red |
| valentine | 情人节 | 02-14 | full | soft-pastel、dark-premium |
| womens-day | 妇女节 | 03-08 | accent | soft-pastel、clean-minimal |
| qingming | 清明节 | 2027-04-05 | accent | clean-minimal、guochao |
| labor-day | 劳动节 | 05-01 | accent | pop-fresh、campus-fresh |
| 520 | 520 | 05-20 | full | soft-pastel、pop-fresh |
| mothers-day | 母亲节 | 2027-05-09 | full | soft-pastel、warm-hand |
| childrens-day | 儿童节 | 06-01 | full | campus-fresh、pop-fresh |
| dragon-boat | 端午节 | 2027-06-09 | full | guochao、clean-minimal |
| fathers-day | 父亲节 | 2027-06-20 | accent | clean-minimal、trust-blue |
| qixi | 七夕 | 2027-08-08 | full | dark-premium、soft-pastel |
| teachers-day | 教师节 | 09-10 | full | campus-fresh、warm-hand |
| mid-autumn | 中秋节 | 2027-09-15 | full | guochao、dark-premium |
| national-day | 国庆节 | 10-01 | full | festive-red、trust-blue |

母亲节是 5 月第二个周日，父亲节是 6 月第三个周日，感恩节是 11 月第四个周四，跨年使用时按这个规则重算。

每个节日在 festivals.json 里还带了 kickers（顶部小标签候选）、ideas（标题思路）和 tips（这个节日特有的坑），写文案前先看一眼。

## 节日文案的几条硬规矩

- 清明是祭扫的日子，不写"清明快乐"，不做打折促销
- 端午稳妥起见写"端午安康"
- 商业海报里不放国旗、国徽，也不用国歌歌词，国庆只用红黄配色和烟花
- 双十一不仿平台的标识和注册商标样式，价格写真实的，"全年最低""史上最低"不能写
- 生肖年的形象自己画或用通用纹样，别用别人的 IP 形象
- 放假通知里的日期，用户没确认就留占位

检查脚本会拦"清明快乐""国旗""国徽"这类说法，报错必须改。

## 高频组合

| 场景 | 物料 | 版式 |
|---|---|---|
| 春节营业时间、放假通知 | poster | notice |
| 年夜饭、月饼礼盒、粽子预订 | poster 加 menu | product-hero，menu cards |
| 节日限定新品 | poster | product-hero 或 type-hero |
| 公司节日福利、慰问信 | poster | notice 或 editorial |
| 社区和学校的猜灯谜、包粽子活动 | poster 加 invitation | editorial，invitation split |
| 圣诞、跨年派对 | invitation 加 tablecard | invitation split，tablecard tent |

## 一个例子

用户："春节我们店初一到初三休息，初四开门，帮我出个通知，再做张新春海报。"

- 叠法：店里平时是黄色元气风，问一句要不要换成红色。用户说"红的喜庆"就用 full
- 物料：notice 版式的营业安排，product-hero 的新春海报，同一份 spec 里两件
- 事实：除夕和初一到初四的具体公历日期要写对（2027 年除夕是 2 月 5 日，初一 2 月 6 日），营业时间问用户
