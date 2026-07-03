# xq-rebalance

雪球组合自动调仓 Skill。支持 Windows 和 macOS，用 `easytrader` 读取雪球组合、生成目标权重计划、dry-run 预演，并在明确确认后执行调仓。

它适合这种场景：

- 你有雪球组合，例如 `ZH3114624`。
- 你有策略输出的目标权重。
- 你想少做手工调仓，但又要保留预演、确认和核对流程。

## 原理

雪球没有稳定公开的组合调仓 API。本工具复用浏览器登录态：

1. 你先在浏览器登录雪球。
2. 从 `xueqiu.com` 请求里复制 Request Headers 或 Cookie。
3. 脚本保存到本机 `~/.xq-rebalance/headers.txt`。
4. 后续脚本自动读取这个 txt，用 `easytrader` 调整指定组合。

不要把 Cookie 或 Request Headers 发给别人，也不要提交到 GitHub。

## 快速开始

新手先看：

- [小白快速开始](references/quickstart-for-beginners.md)

完整教程：

- [介绍与教程](references/intro-and-tutorial.md)
- [登录表头获取与排坑](references/setup-auth-and-headers.md)
- [调仓计划与安全检查](references/rebalance-plan-and-safety.md)

## 安装依赖

Windows:

```powershell
py -m pip install -r requirements.txt
```

macOS:

```bash
python3 -m pip install -r requirements.txt
```

## 保存登录表头

浏览器登录雪球后，复制 `xueqiu.com` 请求的 Request Headers 或 `Copy as cURL`，然后运行：

Windows:

```powershell
py scripts/xq_rebalance.py --save-headers-from-clipboard
```

macOS:

```bash
python3 scripts/xq_rebalance.py --save-headers-from-clipboard
```

表头会保存到：

```text
~/.xq-rebalance/headers.txt
```

过期后重新复制并运行同一条命令，会覆盖旧文件。

## 保存默认组合

```powershell
python scripts/xq_rebalance.py --set-default-portfolio ZH3114624 --portfolio-alias default --portfolio-name "我的策略"
```

## 生成当前持仓取整计划

这一步只读取和生成计划，不会调仓：

```powershell
python scripts/xq_rebalance.py --round-existing --output-plan round_existing_plan.json
```

## Dry-run 预演

```powershell
python scripts/xq_rebalance.py --plan examples/target_plan.full.json
```

## 执行调仓

必须先 dry-run。确认无误后才执行：

```powershell
python scripts/xq_rebalance.py --plan examples/target_plan.full.json --execute --confirm EXECUTE_XQ_REBALANCE
```

执行后打开雪球组合页面手动核对。

## 示例计划

完整目标组合：

- [examples/target_plan.full.json](examples/target_plan.full.json)

局部调整：

- [examples/target_plan.partial.json](examples/target_plan.partial.json)

CSV 示例：

- [examples/target_plan.csv](examples/target_plan.csv)

## 安全提醒

- 不要提交 `headers.txt`、`cookies.txt`、真实 `portfolios.json`。
- 不要把 Cookie 发到聊天、Issue、PR 或截图里。
- 不要跳过 dry-run。
- 如果执行中失败，先看雪球页面实际权重，不要盲目重复执行。

## 许可证

当前未指定开源许可证。公开仓库仅表示代码可见，不代表自动授予再分发或商用许可。
