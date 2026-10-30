---
name: luobo-design
display_name: 萝卜设计
display_name_en: Luobo Design
description: 把一句模糊的想法变成能直接用的设计物料，同时给出可复制的生图提示词。面向商家、老板、个体户、老师、自媒体，覆盖餐饮、美业、健身瑜伽、教育培训、中小学老师、自媒体个人品牌、企业行政 HR、律所财税等专业服务、社区物业居委会、婚宴庆典、旅游文旅。能做活动海报、小红书封面（实拍花字、文字卡、备忘录、榜单、拼图、对比、手绘七种结构）、停水放假这类正式通知、价目表菜单、课程表、邀请函和请柬（按宾客批量）、可以点击的电子请柬 H5（一键导航、加入日历、倒计时、每位宾客一条专属链接）、奖状证书和感谢信（支持整班批量）、桌号牌和席位卡、名片（带出血可直接印刷）、logo 和品牌套件（矢量文件），内置春节、中秋、圣诞、双十一等 23 个节日的节日包，配图有水彩、剪纸、孔版印刷、3D 黏土、线描、蜡笔、波普、霓虹、弥散光、水墨 10 种艺术画风（没有生图模型也能画），还有字图穿插、撑满大字堆、拼贴风这类潮流版式。海报会先想一个画面上的创意概念，配了生图模型时能按概念让模型一步画出整张海报（连图带字），没配时用排版和程序插画实现，并给出可以贴进即梦、GPT 的整图提示词。先出三个方向的对比图让用户看着选，再一次出朋友圈、小红书、手机长图、门店屏幕、A4 印刷等多个尺寸。中文由排版程序排字，交付前自动检查溢出、对比度、广告法和行业禁用说法、缺失信息。用户说"帮我做张海报""开业海报""春节海报""出个停水通知""做个菜单/价目表/课表""做个邀请函""婚礼请柬""电子请柬""H5邀请函""桌号牌""帮我做奖状""设计个名片""做个 logo""做成水彩风/剪纸风""拼贴风""大字报""帮我设计一下""做个小红书封面""出个生图提示词"，或者只描述了店铺、活动、想法时使用。文章封面和配图交给 article-visual-director，PPT 交给 luobo-ppt。
description_zh: 一句模糊的想法进去，能直接用的设计物料出来。活动海报、小红书封面、通知、菜单价目表、邀请函和电子请柬、奖状、名片、logo 都能做，先想创意再出三个方向让你选，中文由程序排版不会错字，交付前自动检查溢出、对比度和广告法用语，也能接生图模型出照片级画面。
description_en: Turn a vague idea into design materials you can use right away, with copy-ready image prompts. Covers event posters, Xiaohongshu covers, notices, menus and price lists, invitations and H5 e-invites, certificates, business cards and logos. It thinks up a visual concept first, offers three directions, sets Chinese text by code so no character is wrong, and checks overflow, contrast and ad-law wording before delivery. An image model can be plugged in for photo-grade results.
version: 0.10.1
author: 萝卜哥
---

# 萝卜设计

用户往往只说得出一句话，比如"小区门口开了家奶茶店，下周开业，帮我弄个海报"。这个 skill 负责把这句话变成专业的设计物料，流程和设计师接单一样，先听懂需求，想创意，再定方向，冻结成规格，然后出图，最后自己检查。

脚本负责确定的活，排版、渲染、测量、检查。你负责听懂人、写文案、选方向、看图挑毛病。

下面命令里的 `scripts/` 指本 skill 目录下的 scripts 文件夹。每次开工前先跑一次 `python scripts/setup_check.py --quick --install`，环境查过就秒过，缺东西会自动补装。样例规格在 `examples/`。

## 第一步 听懂需求，填需求表

先读 @references/brief.md，再按行业读对应的行业包，按物料读物料说明，只读用得上的那几份。

| 行业包 | 覆盖 |
|---|---|
| @references/industry-food.md | 奶茶、咖啡、茶馆、小吃简餐 |
| @references/industry-beauty.md | 美甲美睫、美发、皮肤管理 |
| @references/industry-fitness.md | 健身房、私教、瑜伽普拉提 |
| @references/industry-education.md | 素质类培训、职业培训、讲座 |
| @references/industry-teacher.md | 中小学和幼儿园老师的班级物料 |
| @references/industry-creator.md | 自媒体、博主、个人品牌 |
| @references/industry-corporate.md | 年会、表彰、招聘、通知 |
| @references/industry-professional.md | 律所、财税、咨询、工作室 |
| @references/industry-community.md | 物业、居委会、业委会、社团 |
| @references/industry-celebration.md | 婚礼、寿宴、满月、生日、升学宴 |
| @references/industry-travel.md | 旅行社、民宿酒店、景区、城市和海岛文旅、研学 |

| 物料 | type | 说明 |
|---|---|---|
| 海报、正式通知 | poster | @references/item-poster.md |
| 价目表、菜单、课程表 | menu | @references/item-menu.md |
| 邀请函 | invitation | @references/item-invitation.md |
| 奖状、证书 | certificate | @references/item-certificate.md |
| 名片 | card | @references/item-card.md |
| logo 和品牌套件 | brandkit | @references/item-brandkit.md |
| 桌号牌、席位卡 | tablecard | @references/item-tablecard.md |
| H5 手机互动页（电子请柬） | h5 | @references/item-h5.md |
| 小红书封面 | xhs | @references/item-xhs.md |

用户的行业不在表里时，挑最接近的行业包，按它的思路推断。

用户想要某种画风（水彩、剪纸、黏土、霓虹、水墨……），或者一个系列想每张画法不一样，读 @references/art-styles.md，在 art 里写 style，海报用 art-hero 或 art-frame 版式。

用户提到节日（"春节海报""中秋礼盒""元旦放假通知"），再读 @references/festival-pack.md。节日包叠在行业包上面，在 spec 顶层写 `festival`，配色、底纹、插画和提示词会跟着变。农历节日的日期已经写好，法定放假安排每年由国务院办公厅公布，必须和用户确认。

需求表把每条信息分成五类，用户说了的、你推断的、用了默认值的、还缺的、前后矛盾的。分完再决定要不要问。

只在真正缺关键信息时提问，一轮最多 3 题，每题都带一个推荐答案，用户可以直接说"就按你的来"。电话、地址、日期、价格这类事实绝不编，用户没给就在画面上留【电话】这样的占位，交付时列出来。

## 第二步 想创意概念

海报要先想清楚让人记住哪一点，再给这一点找一个画面。先读 @references/poster-craft.md，按里面的顺序做决定，想法、字和图怎么咬、层级、小字、颜色、质感。

给每张主海报想两三个概念，每个用一句话说想法、一句话说画面，和方向一起拿给用户挑。用户说"你定"，就选你觉得最好的那个直接做。

通知、菜单、证书、名片、请柬这类信息优先的物料不用想概念，排得清楚就是好设计。

小红书封面也不走这一步和下面的三个方向。它的气质由结构决定，按 item-xhs.md 选结构、写钩子标题；用户有照片就看图填好 art.focus。

## 第三步 出三个方向，让用户看着选

用户只看文字描述没法判断风格，所以方向要用看得见的图来选。先按 @references/directions.md 和行业包挑三个方向，一个最稳妥、一个大胆一点、一个安静一点，写进 profile.direction_candidates。主物料的文案写好以后（第三步的 spec 先写一份草稿），跑：

```bash
python scripts/directions.py work/spec.json
```

它会把主物料用三个方向各渲染一张方图，每个方向配不同的版式，三张图的区别在构图上，不只是换个颜色，最后拼成 out/directions/board.png，下面标着方向名、气质和色板。把这张图发给用户，问一句选 A、B 还是 C，也可以混搭（"A 的颜色配 C 的版式"）。发完就停下等回复，不要替用户选。

用户选好后，把选择写进 profile.direction_choice（记下用户原话），改 brand.direction 和对应的 layout，再进入下一步。

以下情况跳过这一步，直接用一个方向，用一句话说明并给两个备选名字：
- 用户说了"直接做""你定就行""不用给我选"
- 用户已经有品牌小卡（brand.json），沿用里面的方向。节日物料例外，照样出三个选项，比的是节日配色还是保留品牌色
- 同一单里已经选过方向，现在只是改稿、加物料、换尺寸
- 无人值守的任务，没人能回答。用最稳妥的那个方向，交付时附上 board.png，说明可以换

## 第四步 冻结成规格文件

按 @references/spec.md 写 spec.json，一份规格可以放多件物料，共用一套品牌和事实。文案在这一步写定，标题按意思手动断行，每行不超过 8 个字最好看，重点词用 `**` 标成强调色。选中的概念写进海报的 concept，再按下一步的表决定每张海报的 mode。

## 第五步 出图

```bash
python scripts/pipeline.py work/spec.json
```

依次做校验、拉字体、生成配图、排版渲染、生成整图、检查、出总览图、写提示词和品牌小卡。

有没有生图模型，前面几步完全一样，概念照样要想，分叉只在“谁来画、谁来写字”这一步，而且是按每件物料分的。

| 情况 | 走哪条路 | 怎么写 |
|---|---|---|
| 没配生图模型 | 排版。字由排版程序排，画面用程序插画和画风滤镜 | 不写 mode。概念用来挑版式和插画；prompts.md 里有按概念写的整图提示词，用户可以贴进即梦自己出，出好的图放回 art.image 重出，或者直接当成品 |
| 配了模型，海报的创意比信息重要，要写的字只有标题和几处短字，主要发手机 | 整图。模型按概念连图带字画整张 | `"mode": "ai"`，写 concept 和 layout |
| 配了模型，但信息必须一字不错，或者要印刷、要批量、要多个尺寸完全统一 | 排版。模型只按概念画配图，字由排版程序排 | 不写 mode，写 concept 或 art.subject |
| 通知、菜单、证书、名片、请柬、桌牌、H5、logo | 永远排版 | 校验会拦住这些物料的 ai 模式 |

整图模式的海报同时也会排一版，叫 `<id>-<尺寸>.png`，整图叫 `<id>-<尺寸>-ai.png`。没模型、调用失败、印刷尺寸时，交付的就是排版版，用户不会拿到空手。

生图配置见 @references/imagegen.md，提示词的写法和三个模型的差别见 @references/prompt-guide.md。

## 第六步 自己看图，打分，返工

检查脚本只能管尺寸、溢出、对比度、文字重叠、末行孤字、极限词这些硬指标。好不好看要你自己看，按 @references/critique.md 打五个维度的分，低于 3 分的改 spec 重出，最多三轮。

一定要打开 overview.png 和每张成品图看过再交付，脚本全绿不代表好看。

整图要多看两件事。第一是字，qa.json 会列出模型画的每一处文字，打开图逐字对，错一个字就改提示词后跑 `python scripts/aiposter.py work/spec.json --force` 重画，最多重画两次（每次都要扣费），还不对就交付排版版。第二是概念有没有画出来，尤其是字和图有没有咬上、字有没有被挡得认不出，没做到就把 concept.interlock 写得更死再重画。

## 第七步 交付

成品 PNG（整图模式另有 -ai.png）（印刷尺寸另附 PDF），overview.png 总览，prompts.md，brand.md 和 brand.json，src 里的 HTML 源文件。有 h5 物料时还有 h5 文件夹，里面是能直接打开的 html、长图预览和每位宾客的专属链接；告诉用户这个文件要放到网上才能发进微信，放法见 item-h5.md，别承诺发出去就一定能打开。交付时用一两句话说明做了什么、用了什么方向，再把还缺的信息和文案风险（qa.json 里的 todo 和 copy）告诉用户。

## 硬规则

- 排版版的字一律由排版程序排。整图里模型只写标题和最多五处短字，电话、价格、地址、二维码不交给它，整图交付前逐字看过
- 事实不编，缺了就占位并告诉用户
- 一张图只用方向里的颜色，强调色一屏最多两处
- 中文不压字距，标题行距约 1.2，正文约 1.5，最多两种字体
- 换尺寸要重新排版，不能等比缩放；pipeline 已经按横、竖、方三种重排
- 广告法极限词（最、第一、国家级等）、疗效承诺、教育培训的保过承诺，检查报错就必须改
- 用户的原话和品牌名一字不改
- 证书只留"盖章处"，不画任何仿制的公章或印章
- 招聘物料不写性别、年龄、婚育、地域限制
- 商业物料不放国旗、国徽；清明不写"快乐"
- 宾客名单、业主信息只用在这一单里，提醒用户别把带全部名单的总览图发到群里

## 文件

| 路径 | 作用 |
|---|---|
| `scripts/pipeline.py` | 一条命令跑完全流程 |
| `scripts/directions.py` | 三个方向的对比图，给用户看着选 |
| `scripts/render.py` | spec 转 HTML，用 Chromium 渲染 PNG/PDF，记录每个文字框 |
| `scripts/layouts.py` | 海报五种基础版式（含正式通知）、菜单两种版式，横竖方自动重排 |
| `scripts/layouts_more.py` | 邀请函、证书、名片、桌号牌和席位卡的版式 |
| `scripts/layouts_h5.py`、`scripts/h5.py` | H5 每一屏的版式；把各屏拼成一个能点的 html，打包字体，在几种手机尺寸上实测 |
| `scripts/brandkit.py`、`scripts/outline.py` | 三个 logo 方案和品牌板，文字转矢量轮廓 |
| `scripts/check.py` | 质量检查和文案风险检查 |
| `scripts/prompts.py` | 三个模型的素材提示词和整图提示词，写了 concept 的按概念写 |
| `scripts/aiposter.py` | mode 为 ai 的海报，让模型按概念画整张，放大到平台尺寸，记下 taskId，同提示词不重复扣费 |
| `scripts/images.py`、`scripts/imagegen.py` | 调用生图模型（OpenAI、Gemini、即梦、HiAPI、兼容接口、本地命令），抠图；`imagegen.py --test` 单独试一张 |
| `scripts/art.py`、`scripts/art_drinks.py` | 程序化产品插画、可描述的饮品杯和小原料、底纹、质感 |
| `scripts/layouts_xhs.py` | 小红书封面的七种结构和花字系统 |
| `scripts/layouts_trend.py` | 字图穿插、撑满大字堆、拼贴风三种潮流版式，可选数据装饰层 |
| `scripts/artstyle.py`、`scripts/layouts_art.py`、`scripts/layouts_artthemes.py` | 10 种艺术画风（SVG 滤镜和生成背景），art-hero、art-frame 两种艺术海报版式，竖版时每种画风一套整页主题 |
| `scripts/fonts.py`、`scripts/fontfix.py` | 首次运行从 npm 拉开源中文字体到缓存，顺手修好个别字体里会印成黑块的字 |
| `scripts/brand.py`、`scripts/sheet.py` | 品牌小卡、总览图 |
| `references/poster-craft.md` | 海报的设计精华，想概念和写 concept 之前读 |
| `references/*.json` | 方向、平台尺寸、字体、文案风险词、节日的数据 |
| `templates/config.example.json` | 生图配置模板 |
| `scripts/setup_check.py` | 检查和补装依赖，`--selftest` 渲染两张小样自测 |
| `examples/` | 六份样例规格 |

依赖 Python 3.9+、Pillow、Playwright（`pip install playwright pillow` 后 `python -m playwright install chromium`），logo 转矢量还需要 `pip install fonttools brotli`。`scripts/setup_check.py --install` 会一次装好，安装方法见 INSTALL.md。字体首次需要联网下载，不能联网时自动退回系统字体并在报告里注明。
