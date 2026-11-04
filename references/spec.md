# spec.json 写法

一份 spec 就是一单活，里面可以有多件物料，共用品牌和事实。

```json
{
  "project": "茶小满开业",
  "profile": {
    "industry": "food",
    "goal": "开业引流，让小区居民知道并进店",
    "confirmed": ["奶茶店", "下周开业", "在小区门口"],
    "inferred": ["受众是小区居民和学生", "方向用 pop-fresh"],
    "defaulted": ["开业优惠写第二杯半价"],
    "missing": ["电话", "群二维码"],
    "direction_candidates": ["pop-fresh", "festive-red", "soft-pastel"],
    "direction_choice": "用户选了 A：'就要黄色那个，热闹'"
  },
  "brand": {
    "name": "茶小满",
    "direction": "pop-fresh",
    "logo": null,
    "tokens": {},
    "fonts": {},
    "voice": "像邻居打招呼，口语，不端着"
  },
  "festival": null,
  "facts": {"date": "10月18日至20日", "address": "幸福里小区南门 12 号", "hours": "10:00 至 22:00"},
  "items": [
    {
      "id": "opening",
      "type": "poster",
      "layout": "product-hero",
      "sizes": ["portrait", "square", "a4"],
      "content": {
        "kicker": "新店开业",
        "headline": "小区门口\n开了家奶茶店",
        "sub": "珍珠现煮，鲜奶现打，每一杯都是刚做好的",
        "offer": {"big": "第二杯半价", "small": "{date}"},
        "details": [{"k": "地址", "v": "{address}"}, {"k": "营业", "v": "{hours}"}, {"k": "电话", "v": "{phone}"}],
        "cta": "到店出示这张图，免费加一份珍珠",
        "qr": {"label": "扫码进福利群", "src": null}
      },
      "art": {
        "motif": "milk-tea",
        "subject": "一杯珍珠奶茶，透明塑料杯，黑糖珍珠沉在杯底，奶茶表面有细腻奶泡，杯身有水珠",
        "subject_en": "a cup of bubble milk tea in a clear plastic cup, brown-sugar tapioca pearls at the bottom, creamy foam on top, light condensation"
      }
    }
  ]
}
```

## 字段说明

**profile** 需求表，见 brief.md。`industry` 用行业包的 id（food）。`direction_candidates` 是给用户看的三个方向，`direction_choice` 记下用户选了哪个、原话怎么说。

**brand**
- `direction` 必填，directions.json 里的 id
- `tokens` 可选，覆盖方向里的颜色（用户有自己的品牌色时）。只填要改的，比如 `{"accent": "#E60012"}`。荧光色（很亮又很艳的绿、青这类）做主色和辅色会被收成同色相里稳一点的颜色，文字色和底色对比不到 7:1 会被加深，qa 里会写明从什么调成了什么。用户坚持用原色，加 `"exact_colors": true`
- `fonts` 可选，覆盖字体，`{"display": "wenkai"}`
- `logo` 图片路径（相对 spec 所在目录），没有就用店名做文字标
- 有 brand.json 时，把里面的 direction、tokens、fonts、voice 抄进来
- 品牌有档案时（`brands.py list`），用 `brands.py apply spec.json --name 店名` 自动填，不用手抄
- `remember` 可选，写 `false` 时这次的品牌不进档案库

**festival** 可选，节日包，`{"id": "spring-festival", "mode": "full"}` 或只写 id。full 换上节日配色，accent 保留品牌色只加节日点缀。没写 art.motif 的物料自动用节日插画，提示词也会加上节日元素。id 和用法见 festival-pack.md。

**facts** 真实信息。文案里写 `{address}` 这样的占位会自动替换；facts 里没有的会显示成【地址】，检查时列为待补。常用 key：date、time、address、hours、phone、wechat。

**items[]**
- `id` 文件名用，英文和短横线
- `type` poster、menu、invitation、certificate、card、brandkit、tablecard、h5、xhs（小红书封面，见 item-xhs.md）
- `layout` 见各物料说明（item-*.md），不填用第一种
- `batch` 批量，一项出一张。邀请函是宾客、证书是获奖人、桌号牌是桌号、席位卡是名字，可以写字符串列表或对象列表
- `sizes` platforms.json 里的 id，或者 `1242x1660` 这样的自定义像素
- `content` 文案，各物料的字段见物料说明
- `size_copy` 可选，某个尺寸专用的文案，覆盖 content 里同名的字段，比如 `{"square": {"headline": "难啃的书\n一起读完"}, "landscape": {"headline": "难啃的书，一起读完"}}`。键写尺寸 id，也可以写 portrait、square、landscape 按方向套用，两种都写时尺寸 id 优先。只写要换的字段，其余照用 content
- `art`
  - `motif` 程序画的插画，共 61 个
    - 餐饮：milk-tea、iced-coffee、hot-coffee、latte、gaiwan（盖碗茶）、bread、noodle-bowl、gift
    - 行业：dumbbell、nail-polish、scissors-comb、lotus、open-book、grad-cap、microphone、camera、trophy、medal、laurel、briefcase、scales、calendar、envelope、building（楼房）、megaphone（喇叭）
    - 节日和喜事：lantern、red-envelope、mooncake、zongzi、xmas-tree、fireworks、heart、bouquet、shopping-bag、rings（婚戒）、double-happiness（囍字剪纸）、birthday-cake、peach（寿桃）
    - 宠物：pet-box（纸箱里探头的小猫）、paw（爪印）、bone（骨头）
    - 旅行：palm-beach（圆形海岛小景）、plane-window（看得见海滩的飞机舷窗）、sailboat、suitcase
    - 饮品和原料：drink（可描述的饮品杯）、carrot、orange-slice、lemon-slice、coconut、mango、jasmine、osmanthus、taro、coffee-bean、ice-cube、tea-leaf、leaf、pearl、strawberry、carrot-mini
  - `subject` / `subject_en` 给生图模型的主体描述，中文给即梦，英文给 GPT 和 Nano Banana
  - `style` 艺术风格：flat、watercolor、papercut、riso、clay、lineart、crayon、pop、neon、diffuse、ink，见 art-styles.md。没有生图模型时用滤镜画出来，有模型时写进提示词
  - `drink` motif 为 drink 时描述这杯饮品（颜色、奶盖、小料、杯型），见 art-styles.md
  - `ingredients` 散在画面四周的小原料，最多 6 个
  - `mode` cutout（抠图放进版式，默认）或 scene（整幅背景，photo-full 版式用）
  - `setting` / `setting_en` 场景描述，scene 模式用
  - `image` 已有的图片路径（用户给的产品照，或生图后自动填上）
  - `image_fit` contain（抠图）或 cover（照片铺满）
  - `generate` 设为 false 时即使配了模型也不生图
  - `screenshot` 截图路径（App、网页、后台界面），会自动加圆角、阴影和外框后放进版式，内容不拉伸不重画。配 `frame`：browser（浏览器窗口，宽截图默认）、phone（手机，竖截图默认）、window（只有窗口三个点）、plain（只加圆角描边）；`frame_dark` 为 true 时用深色外框
  - 照片来自免费图库时，用 `python scripts/stock.py search "英文关键词"` 下载，路径写进 image。许可要求署名的照片，在 content.credit 里写上出处，会排成右下角一行小字

- `mode` 海报才有，layout（默认）或 ai。ai 表示配了生图模型时由模型按 concept 一步画出整张海报，连字一起画，见下面
- `concept` 创意概念，写法见 poster-craft.md。layout 和 ai 两种 mode 都可以写，layout 时它决定配图画什么，ai 时它决定整张海报
- `html` 只给 concept 版式，你写的构图片段，一个路径或 `{"portrait": "x.html", "square": "y.html"}`，见 item-concept.md
- `fonts` concept 版式用到的字体 id 列表，比如 `["dyh", "song"]`
- `fallback` concept 版式里没写构图的尺寸改用哪个版式，不写时素净组用 jing，其他用 type-hero

## concept 创意概念

```json
"mode": "ai",
"layout": "type-sandwich",
"concept": {
  "idea": "它怕，但有人管它",
  "scene": "一只真实的金毛幼犬像小孩趴栅栏一样，下巴和两只前爪搭在标题上沿。一条细细的心电图线从左横穿到右，最后一个波峰变成一个小爪印",
  "scene_en": "A real golden retriever puppy leans over the headline like a child on a fence, chin and both front paws resting on top of the characters. A thin heartbeat line runs across the poster and its last peak turns into a small paw print.",
  "interlock": "爪子压住“别”“怕”两个字的上沿，最多盖住字高的三分之一",
  "interlock_en": "The paws overlap the top edge of the characters 别 and 怕, covering at most a third of their height.",
  "headline_style": "超粗黑体，两行，字距紧，占画面高度四成",
  "headline_style_en": "massive heavy black Chinese sans serif, two lines, tightly set, about 40 percent of the poster height",
  "look": "暖米色纸张底，带一点颗粒，小狗是真实照片质感，其余是干净的平面设计",
  "look_en": "Warm cream paper with faint grain, the puppy photographed with fine fur detail, everything else flat graphic design.",
  "palette": ["#F3EBDD", "#1A1A1A", "#6FB08E"],
  "text": [
    {"text": "小禾宠物医院", "where": "左上角", "where_en": "top left"},
    {"text": "{date} 开业", "where": "右上角", "where_en": "top right"}
  ]
}
```

- `idea` 一句话的想法，看的人记住的那一点
- `scene` 画什么，写成能拍出来的具体东西和动作，不写形容词
- `interlock` 字和图怎么咬，哪个东西挡住哪个字的哪个部位，要说死
- `headline_style` 标题用什么字、几行、多大
- `look` 质感、光线、年代
- `palette` 可选，最后一个当强调色；不写就用方向的底色、文字色和强调色
- `text` 交给模型写的小字，最多 5 处，每处十几个字以内。可以用 `{date}` 这样的事实占位，事实缺了这一处就不画
- 每个字段都可以加 `_en` 版本给 GPT 和 Nano Banana，不加就用中文

标题用 content.headline，写法和平常一样。

**ai 模式的限制。** 只有海报能用。电话号码一律不交给模型，校验直接报错；价格会提醒核对。印刷尺寸（a4 这些）不出整图，用排版版。同一件物料始终会再排一版，没模型、生成失败或者字必须一字不错时，就用这一版，所以 `layout` 照样要写，挑和概念最接近的，字压图用 type-sandwich，满屏大字用 type-stack，撕纸拼贴用 collage。

## 文案标记

- `\n` 手动换行，标题必用
- `**重点**` 显示成强调色
- `{fact}` 替换成 facts 里的值
- 【xxx】 显示为待补占位


## 一份文案，几种尺寸

竖版能放下的标题，放到方图和横版上常常太长，挤成小字或者三行。别指望程序把字缩小硬塞，给这些尺寸单独写一句短的，放进 size_copy。

短标题这样写。先找出整句里那个动作和它作用的东西，比如“给孩子讲了三年睡前故事，我把它们攒成了一本绘本”，动作是攒成，东西是绘本，三年是钩子，压成“三年睡前故事，攒成一本书”。方图标题控制在四到十个字，最多两行，每行不超过六个字；横版门店屏一行能放十二三个字。问句改成陈述句，“怎样三个月减十斤”写成“三个月瘦十斤”。数字本身就是新闻时，把数字放在最前面。副标题能删就删，方图上一句标题就够了。

检查时，标题有一行超过 9 个字，或者某个尺寸的标题比主尺寸小了三成以上，qa 会提醒你写短标题。
