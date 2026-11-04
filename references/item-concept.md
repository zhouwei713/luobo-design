# 概念版式：自己给海报构图

预设版式再好，也只能长成预设的样子。一张海报的想法定下来以后（巨大的二分之一、一张时间小票、他的十二和她的十二），用概念版式把它亲手排出来。你写构图，脚本照样负责字体、自适应、对比度、贴边、互相压字、广告法和发布预览，文案也照样能在编辑页里改。

样例在 `examples/07-concept-poster/`，先打开看一眼。

## 规格怎么写

```json
{
 "id": "half", "type": "poster", "layout": "concept",
 "sizes": ["portrait", "square", "landscape"],
 "html": {"portrait": "half-portrait.html", "square": "half-square.html"},
 "fallback": "jing",
 "fonts": ["dyh"],
 "concept": {"idea": "第二杯半价，直接画成一个巨大的二分之一"},
 "content": {"kicker": "小满茶铺开张啦", "headline": "第二杯\n**半价**", "sub": "开业三天",
             "details": [{"k": "日期", "v": "11月18日至20日"}, {"k": "电话", "v": "{phone}"}]}
}
```

- `html` 可以是一个文件，也可以按尺寸写：先找尺寸名（portrait、a4），再找方向（portrait、square、landscape），最后找 default。一个文件里也能用 `<section data-size="portrait">…</section>` 分开写
- 路径相对 spec.json 所在的目录
- 没写构图的尺寸自动换成 `fallback` 版式（不写时素净组用 jing，其他用 type-hero），所以每个尺寸都能出图。最要紧的竖版和方图一定自己写，换尺寸要重新构图，不能等比缩放
- `fonts` 写这张图用到的字体 id（见 fonts.json），方向本身的标题字和正文字会自动带上
- content 里的字段随便起名，只要构图里用 data-field 绑上就行

## 构图片段里能用什么

片段就是画布里面的内容，画布大小等于这个尺寸的像素（竖版 1080 x 1440，方图 1080 x 1080）。用绝对定位或 flex 都行，可以带自己的 `<style>`。

**颜色只用方向变量**，换方向或用户给了品牌色时才会跟着变：

| 变量 | 是什么 |
|---|---|
| `var(--bg)` `var(--surface)` | 底色、浅一点的色块底 |
| `var(--ink)` `var(--muted)` | 文字色、次要文字色 |
| `var(--accent)` `var(--accent2)` | 强调色、辅助色 |
| `var(--accent-text)` | 压在底色上也读得清的强调色，小字用它 |
| `var(--on-accent)` | 压在强调色上的字该用的颜色 |
| `var(--line)` `var(--soft)` | 线条色、很淡的强调色 |

**尺寸用 `var(--u)`**，它是短边的 1%，`calc(var(--u) * 12)` 就是短边的 12%。`var(--safe)` 是安全边距，带信息的字都放在它里面。

**字体用类名**：`.f-dyh`（得意黑）、`.f-song`（宋体）、`.f-qingke`（庆科黄油）、`.f-xiaowei`（小薇）、`.f-wenkai`（文楷）、`.f-hei`（黑体），或者 `.f-display`、`.f-body` 用方向自带的两种字。用到的要写进规格的 fonts。

## 文案和检查

- `data-field="headline"` 这样的元素，内容会从 spec 的 content 里填进来，`**重点**` 照样变成强调色。路径可以往下走，比如 `details.0.v`、`offer.big`
- 每段字写明它是什么、压在什么颜色上：`data-role`（headline、sub、body、label、badge、caption），`data-c` 字的颜色，`data-on` 底的颜色，都写变量名去掉 `--` 和把 `-` 换成 `_`（ink、bg、accent、on_accent、accent_text）。对比度就是按这两个算的，写错了检查就不准
- 自己写在片段里的字（不绑 data-field 的）也会被当成文字检查
- 想让一段字自己缩到放得下，写 `data-fit="最大,最小"`（px），比如 `data-fit="180,90"`
- `<img data-field="art.image">` 会换成这件物料的图片
- 当画面用的巨大字形和色块（二分之一里的 1 和 2）写 `data-art`，它们可以出血、可以压在字下面，按图片算。价格、日期、店名这些带信息的字永远不能标 data-art
- 片段里的 script 和 onclick 这类属性会被删掉

## 写构图时守住的几条

- 一张图只讲一个想法，主角占画面的三四成以上，其他字小下去
- 字和图要咬在一起，具体怎么咬见 poster-craft.md 第二节
- 带信息的字（日期、地址、电话、价格）收在一处，别散落在画面各个角
- 不用渐变铺底、毛玻璃、左边色条的圆角卡片、emoji、阴影堆出来的立体感，检查会提醒
- 写完跑 pipeline，打开 png 自己看，对着 qa.json 改到 0 个错误
