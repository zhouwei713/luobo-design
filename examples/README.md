# 样例规格

每个文件夹里一份 `spec.json`，改改文字就能出你自己的。在 skill 目录里运行：

```bash
python scripts/pipeline.py examples/01-pet-shop-opening/spec.json
```

成品会出在同一个文件夹的 `out/` 里。没配生图模型时加不加 `--no-images` 都一样，配了的话加上它可以先只看排版版，不花钱。

| 样例 | 包含 | 看点 |
|---|---|---|
| 01-pet-shop-opening | 开业主海报、新客券海报、logo 和品牌小卡 | 主海报写了创意概念和 `"mode": "ai"`，接了模型会整张生成，没接就出排版版 |
| 02-xiaohongshu-covers | 实拍花字、文字卡、备忘录、清单榜单、手绘插画五张封面 | 实拍那张没有照片时画占位；接了模型会按 art.subject 生成照片 |
| 03-hainan-travel | 旅游宣传海报三个尺寸 | 创意概念里字和图怎么咬在一起的写法 |
| 04-wedding-set | 请柬、桌号牌、席位卡 | 喜事默认大红，席位卡对折两面都是正的 |
| 05-wedding-h5 | 电子请柬 H5 | 一屏一屏滑动、导航、加日历、倒计时、宾客专属链接 |
| 06-community-notice | 停水通知、志愿者证书 | 信息优先的正式物料 |

接了生图模型以后整图会多出 `*-ai.png`，交付前要看图逐字核对，`qa.json` 会列出要核对的字。
