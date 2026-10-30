<p align="center"><img src="docs/logo.svg" width="440" alt="萝卜设计 luobo-design"></p>

# luobo-design 萝卜设计

一句模糊的想法进去，能直接用的设计物料出来。给商家、老师、自媒体、社区和小团队用，开业海报、通知、菜单、请柬、奖状、名片、logo、小红书封面都能做。

它是一个遵循 SKILL.md 开放标准的 Agent skill，Claude、Codex、Gemini CLI、Cursor、GitHub Copilot 这类能执行命令、能看图片的 Agent 都能用。

![五个品类的创意海报](docs/concept-posters.jpg)

## 它会做什么

接到需求，它按设计师接单的顺序走一遍：先把需求听懂，缺的信息最多问三个问题；海报会先想一个画面上的创意，比如律所招人想说“较真”，就画一支红钢笔在合同上圈出一个逗号；再出三个视觉方向让人看着选；然后写成一份规格文件，一条命令出图；最后自己检查文字溢出、对比度、广告法用语、还缺的信息，再把图拿出来看一遍。

能做的物料：

- 活动海报和正式通知，横、竖、方和 A4 印刷一次出齐
- 小红书封面，七种结构：实拍花字、文字卡、备忘录、清单榜单、拼图、前后对比、手绘插画
- 价目表、菜单、课程表
- 邀请函和请柬（按宾客批量），能点的电子请柬 H5（导航、加入日历、倒计时、每位宾客一条专属链接）
- 奖状证书（整班批量）、桌号牌、席位卡、名片（带出血）
- logo 和品牌套件，文字转成矢量轮廓
- 23 个节日包，10 种艺术画风（没接生图模型也能画）

![小红书封面七种结构](docs/xiaohongshu-covers.jpg)

## 接不接生图模型

不接也能用。字一律由排版程序排，画面用程序画的插画和画风滤镜，还会给出能贴进即梦、GPT Image、Nano Banana 的提示词。

想要照片级的画面，就接一个生图模型。接了以后，海报可以让模型按创意一步画出整张（连字一起），同时排一版备份；小红书封面可以生成不露脸的美食、家居照片和插画。真人出镜的封面建议用你自己的照片。

![接和不接生图模型的对比](docs/with-and-without-model.jpg)

## 安装

在 Agent 里说一句就能装：

```text
帮我安装这个 skill：https://github.com/zhouwei713/luobo-design
```

也可以手动装：

```bash
git clone https://github.com/zhouwei713/luobo-design.git ~/.claude/skills/luobo-design
pip install playwright pillow fonttools brotli
python -m playwright install chromium
```

其他 Agent 的装法见 [INSTALL.md](INSTALL.md)。

最省事的办法是解压后运行 `install.sh`（macOS、Linux）或双击 `install.bat`（Windows），脚本会识别你装了哪些 Agent，复制过去，补装依赖，再跑一次自测。

## 怎么用

装好以后直接跟 Agent 说需求就行：

```text
小区门口开了家奶茶店，下周开业，帮我弄个海报
做个停水通知，周三上午九点到下午五点
帮我做个小红书封面，讲我每天在用的 10 个 AI 工具
婚礼请柬，5 月 22 日，宾客名单在 guests.txt
```

不支持 skill 的 Agent，可以让它先读一遍 `SKILL.md`，再按里面的步骤做。

想直接跑脚本也可以：

```bash
python scripts/pipeline.py examples/02-xiaohongshu-covers/spec.json
```

`examples/` 里有六份样例规格，宠物店开业、小红书封面、海南旅游、婚礼一套、电子请柬、社区通知，改改文字就能出你自己的。

## 生图模型配置

在工作目录放一份 `luobo-design.config.json`，或者放到 `~/.config/luobo-design/config.json`。key 不要写进文件，放环境变量。

```json
{
  "provider": "hiapi",
  "model": "gpt-image-2.5-flare/text-to-image",
  "api_key_env": "HIAPI_API_KEY",
  "resolution": "2K",
  "timeout": 240,
  "retries": 1
}
```

OpenAI、Gemini、即梦、兼容 OpenAI 接口的服务和本地命令也都支持，模板在 `templates/`，说明在 `references/imagegen.md`。

## 目录

| 路径 | 作用 |
|---|---|
| `SKILL.md` | 给 Agent 看的主说明，流程和硬规则 |
| `references/` | 行业包、物料说明、设计精华、方向和平台数据 |
| `scripts/` | 渲染、检查、生图、提示词，`pipeline.py` 一条命令跑完 |
| `templates/` | 生图配置模板 |
| `examples/` | 六份样例规格 |
| `install.*` | 一键安装 |

## 许可

MIT
