# luobo-design 安装说明

luobo-design（萝卜设计）遵循 SKILL.md 开放标准，Claude、Codex、Gemini CLI、Cursor、GitHub Copilot 等支持 skill 的 Agent 都能装。装好之后，Agent 需要能执行命令、能看图片，skill 才能完整跑起来。

安装脚本会做三件事：把 skill 复制到对应 Agent 的 skills 目录，检查并安装依赖，最后渲染两张小样做自测。

## 方式一：Claude 应用（Cowork / claude.ai）

在对话里点 `.skill` 文件卡片上的保存按钮即可。Claude 的云端环境里依赖基本是现成的。

## 方式二：本地 Agent 一键安装（推荐）

1. 解压 `luobo-design.zip`（或 `.skill`，它本质也是 zip，Windows 上可以先把后缀改成 `.zip`）
2. 进入解压出来的 `luobo-design` 文件夹，运行安装脚本

macOS / Linux

```bash
bash install.sh
```

Windows

双击 `install.bat`，或者在 PowerShell 里运行 `.\install.ps1`。

脚本会自动识别你电脑上装了哪些 Agent，分别装进去。想指定 Agent 或位置，可以加参数。

| 参数 | 作用 |
|---|---|
| `--agent codex`（Windows 用 `-Agent codex`） | 只装给某个 Agent，可选 claude-code、codex、gemini、cursor、copilot、agents、all |
| `--project 路径` | 装进某个项目目录（只在这个项目里生效） |
| `--dest 路径` | 装进任意 skills 目录 |
| `--skip-deps` | 只复制文件，不检查依赖 |
| `--uninstall` | 卸载 |

## 方式三：手动安装

把整个 `luobo-design` 文件夹复制到下表对应的目录，然后运行一次依赖检查。

```bash
python3 <skill目录>/scripts/setup_check.py --install --selftest
```

Windows 上把 `python3` 换成 `python` 或 `py -3`。

| Agent | 个人目录（所有项目可用） | 项目目录 |
|---|---|---|
| Claude Code | `~/.claude/skills/` | `.claude/skills/` |
| OpenAI Codex CLI | `~/.agents/skills/` | `.agents/skills/` |
| Gemini CLI | `~/.gemini/skills/` | `.gemini/skills/` |
| Cursor | `~/.cursor/skills/` | `.cursor/skills/` |
| GitHub Copilot（VS Code） | `~/.copilot/skills/` | `.github/skills/` |
| 其他支持开放标准的 Agent | `~/.agents/skills/` | `.agents/skills/` |

`~` 在 Windows 上是 `C:\Users\你的用户名`。Cursor 也会读取 Claude 和 Codex 的目录，所以装过这两个的话，一键脚本不会再给 Cursor 重复装一份。各家目录偶尔会调整，装完 Agent 认不出来时，以它的官方文档为准。

不支持 skill 的 Agent，把文件夹放进项目里，跟它说“先读 luobo-design/SKILL.md，再按里面的流程帮我做”就行。

## 依赖清单

| 级别 | 组件 | 用途 | 缺了会怎样 |
|---|---|---|---|
| 必需 | Python 3.9+ | 运行脚本 | 无法使用 |
| 必需 | Pillow、playwright | 画图、排版 | 无法使用 |
| 必需 | Playwright 的 Chromium | 把版式渲染成 PNG 和 PDF | 无法出图。`python -m playwright install chromium` 安装，Linux 可能还要 `python -m playwright install-deps chromium` |
| 推荐 | fonttools、brotli | logo 转矢量、电子请柬的字体子集、修复个别字体 | logo 只能出位图，电子请柬字体变大 |
| 推荐 | 能访问 npm（registry.npmjs.org） | 首次运行下载开源中文字体，之后走缓存 | 退回系统字体，报告里会注明 |
| 推荐 | requests | 调用生图模型 | 只影响生图，程序插画不受影响 |
| 可选 | 生图模型配置 | 照片级配图、整图海报 | 改用程序插画，配置方法见 `references/imagegen.md` |

`--install` 会自动用 pip 安装缺少的 Python 包和 Chromium。在国内网络下 npm 字体源较慢时，可以设置环境变量 `LUOBO_DESIGN_NPM` 换成镜像地址，比如 `https://registry.npmmirror.com`。

## 检查结果

检查通过后，结果缓存在 `~/.config/luobo-design/setup.json`，之后 Agent 每次使用前只做秒级的快速确认。想重新检查，删掉这个文件或者直接运行 `setup_check.py`。

## 生图模型

不配也能用。要配的话，在工作目录放 `luobo-design.config.json`，或放到 `~/.config/luobo-design/config.json`，模板在 `templates/`。key 放环境变量，不要写进文件，比如 HiAPI 用 `HIAPI_API_KEY`。

单独试一张，确认 key 和网络都通：

```bash
python scripts/imagegen.py --test "a cup of orange carrot fruit tea, watercolour" --out test.png --ratio 3:4
```
