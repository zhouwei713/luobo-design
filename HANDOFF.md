# luobo-design 接手说明

给接手改代码的人和 Agent。为什么这样设计见 PRODUCT.md，Agent 干活时读的是 SKILL.md。

## 一次运行里发生了什么

一切从一份 spec.json 开始，脚本只读它，所有改动最后也都写回它。`python scripts/pipeline.py spec.json` 按这个顺序走：

1. `pipeline.validate` 校验规格，品牌档案有出入时提醒
2. `images.py` 配了生图模型才跑，按 art.subject 或概念生成配图，回填 art.image
3. `render.py` 把每件物料的每个尺寸排成 HTML，用 Playwright 里的 Chromium 截成 PNG，印刷尺寸另出 PDF。截图会先交给 `shotframe.py` 加框。每张图的文字框、自适应结果、图片块和可点击的文案位置都写进 `render_report.json`
4. `aiposter.py` 只处理 `"mode": "ai"` 的海报，让模型按概念画整张，存成 `-ai.png`
5. `h5.py` 把电子请柬的各屏拼成一个能点的页面
6. `preview.py` 出小红书信息流和朋友圈的发布预览
7. `check.py` 读 render_report 做检查，写 `qa.json`，最后排出“下一步”
8. `sheet.py` 总览图，`prompts.py` 生图提示词，`brand.py` 品牌小卡，`studio.py build` 编辑页，`brands.py save` 更新品牌档案

所有输出在 spec 旁边的 `out/`（或 `--out` 指定的位置）。

## 文件分工

| 文件 | 管什么 |
|---|---|
| `common.py` | 版本号 SKILL_VERSION、颜色工具（对比度、OKLCH、品牌色收敛）、方向配色解析、画布尺寸 |
| `layouts.py` | 海报和菜单的版式，Ctx、T（一个文字节点）、page（页面骨架和自适应脚本 FIT_JS），也是所有版式的注册入口 |
| `layouts_more.py`、`layouts_trend.py`、`layouts_art.py`、`layouts_artthemes.py`、`layouts_xhs.py`、`layouts_h5.py` | 其余版式，按物料和风格分文件，各自在 layouts.py 里注册 |
| `art.py`、`art_drinks.py`、`artstyle.py` | 程序插画、饮品杯、十种画风滤镜 |
| `imgtone.py` | 读照片放字的区域，算出按需的同色调遮罩 |
| `shotframe.py` | 截图加圆角、阴影、浏览器框、手机框 |
| `stock.py` | 免费图库搜图下载，记来源和许可 |
| `studio.py`、`studio.html` | 编辑页：离线版、实时服务、评论、修改单 |
| `brands.py` | 品牌档案库 |
| `fonts.py`、`fontfix.py`、`outline.py` | 开源字体下载和缓存、修坏字形、文字转矢量 |
| `imagegen.py` | 各家生图接口的统一封装，key 只从环境变量读 |
| `references/` | Agent 读的说明文档和数据（方向、平台尺寸、字体、广告法词表、节日） |

## 常见改动怎么做

**加一个版式。** 在对应的 layouts_*.py 里写一个 `(ctx, fonts_css) -> html` 的函数，用 T 输出每段文字（这样检查和编辑页都认得它），最后 `return page(ctx, fonts_css, body, css)`。在该文件的 register 里登记名字，用到的字体写进 LAYOUT_FONTS。双栏布局写 `minmax(0,1fr)`，别写裸的 `1fr`，否则长标题会把另一栏挤成一个字一行。

**加一个物料。** pipeline.py 的 KEYS 里写上它允许的文案字段，layouts.py 的 LAYOUTS 里登记版式，references 里加一份 item-*.md，SKILL.md 的物料表加一行。

**加一个行业包或节日。** 行业包是 references/industry-*.md，写清推荐方向、常用文案、行业禁用说法（禁用词进 copy_words.json）。节日在 festivals.json。

**加一条检查。** check.py 里 check_render 管单张图，run 管整份规格。新问题要在 FIXES 里配一句怎么改，这样“下一步”会带上它。

**改编辑页。** 页面是 studio.html 一个文件，服务端在 studio.py。改动一律通过 apply_changes 写回 spec.json，别在页面上直接改图。

## 怎么测

没有单元测试框架，靠样例回归。每次改完跑一遍六个样例，期望都是 0 个错误：

```bash
export LUOBO_DESIGN_HOME=/tmp/lb-test   # 品牌档案写到临时目录，别弄脏自己的
for e in examples/*/; do python scripts/pipeline.py $e/spec.json --no-images --out /tmp/reg/$(basename $e); done
```

05-wedding-h5 固定有一条回执相关的提醒，属于正常。改了版式要打开 overview.png 看。改了编辑页，用 Playwright 打开 `out/editor.html` 点一遍，实时模式用 `studio.py open` 起服务再测保存和评论。`setup_check.py --selftest` 是安装后的冒烟测试。

## 发版

1. 改 `scripts/common.py` 的 SKILL_VERSION 和 SKILL.md 头部的 version，两处一致
2. 跑完回归
3. GitHub 包就是整个目录去掉 `.git`、`__pycache__`、`out`
4. WorkBuddy 包只允许“根目录/二级目录/文件”两级，所以要把 `examples/*/spec.json` 拍平成 `examples/*.json`，去掉 docs、安装脚本和 INSTALL.md，并改掉文档里对应的路径。SKILL.md 头部必须有 version、display_name、display_name_en、description_zh、description_en
5. 打包前搜一遍有没有 API key

## 约定

API key 只放环境变量（配置里写 `api_key_env`），任何文件、规格、日志、包里都不出现 key。生成的文件只写进输出目录，不写进 skill 目录。用户的照片、名单只用在当次任务。新加的文字和代码都要是原创的，参考别人项目时只学思路。

## 还没做完的

小红书内页组图、公众号封面对、编辑页拖动元素、旅行路线图。stock.py 的真实请求还没在联网环境里跑过，只用模拟数据测过解析、下载记录和署名检查，第一次在用户那边用时要留意。
