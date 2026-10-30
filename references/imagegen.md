# 生图模型配置

不配也能用：海报里的产品用程序插画，提示词照样写进 prompts.md。配了以后，pipeline 会自动给每件物料生成产品素材或背景图，抠图后放进版式。

## 配置文件放哪

按顺序找，找到第一个就用：

1. `--config PATH`
2. 环境变量 `LUOBO_DESIGN_CONFIG` 指向的文件
3. 当前目录或 spec 所在目录的 `luobo-design.config.json`
4. `~/.config/luobo-design/config.json`
5. skill 目录下的 `config.json`
6. luobo-ppt 的配置（`~/.config/luobo-ppt/config.json`），两个 skill 可以共用一份

模板在 templates/config.example.json。key 建议放环境变量，配置里写 `api_key_env` 指向它。

## 三个常用写法

GPT Image 2：
```json
{"provider": "openai", "model": "gpt-image-2", "api_key_env": "OPENAI_API_KEY", "quality": "high"}
```

即梦 / Seedream（火山方舟），model 填控制台里你开通的模型 ID：
```json
{"provider": "ark", "model": "你的 Seedream 模型 ID", "api_key_env": "ARK_API_KEY"}
```

Nano Banana 2：
```json
{"provider": "gemini", "model": "gemini-3.1-flash-image", "api_key_env": "GEMINI_API_KEY"}
```

用中转服务时 provider 写 `openai_compatible`，再填 `base_url` 和 `model`。

HiAPI（异步任务接口，默认模型 GPT Image 2.5 Flare）：
```json
{"provider": "hiapi", "model": "gpt-image-2.5-flare/text-to-image", "api_key_env": "HIAPI_API_KEY", "resolution": "2K"}
```
它是先提交任务、再轮询结果，一张图一般要等几十秒，timeout 建议 240。抠图素材会直接要透明底 PNG，这时分辨率固定 1K（接口只在 1K 支持透明）；整幅背景图按 resolution 出 2K 或 4K。结果链接有过期时间，脚本拿到就立刻下载保存。

先单独试一张，确认 key 和网络都通：
```bash
python scripts/imagegen.py --provider hiapi --test "a cup of orange carrot fruit tea, watercolour" --out test.png --ratio 3:4
```

## 注意

- 有的账号或模型只允许一种分辨率（比如只能 1K），接口会在报错里说明，脚本会自动改成它要求的分辨率再提交一次，被拒的请求不扣费。1K 的竖图是 864x1152，发手机够用，印刷要用排版版
- `mode: ai` 的海报由 aiposter.py 生成整图，原图存在 out/ai/，放大到平台尺寸后存成 `<id>-<尺寸>-ai.png`，每张旁边有 .task.json 记着 taskId，可以去 API 后台对账。提示词没变时重跑会直接复用，不会重复扣费，想重新生成就单独跑 `python scripts/aiposter.py spec.json --force`
- 生成失败会自动退回程序插画，交付时要告诉用户
- 云端环境可能拦截生图请求（代理返回 403），同样会退回，交付时如实说明，并告诉用户把接口域名加进 Claude 设置里允许访问的网络域名，或者在自己电脑上跑
- 生成的图会存到 spec 旁边的 images 目录，并写回 spec 的 art.image，下次重出不再花钱；想重新生成加 `--force`
