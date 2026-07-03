---
name: xq-rebalance
description: 用于帮助用户配置、认证、预演和执行雪球组合自动调仓。适用于雪球/Xueqiu 组合、easytrader、目标权重计划、复制浏览器请求表头/Cookie、把表头保存到本机 txt、Windows/macOS 跨平台设置、组合代码管理和安全执行调仓。
---

# XQ Rebalance

## 定位

这是一个“雪球组合自动调仓”Skill。它不是实盘券商交易工具，而是把雪球组合调仓流程自动化：

网页登录雪球 -> 复制请求表头 -> 保存到本机 txt -> 设置默认组合 -> 生成目标权重 -> dry-run 预演 -> 明确确认后执行 -> 回到雪球页面核对。

## 核心原理

雪球没有提供稳定公开的组合调仓 API。`easytrader` 的做法是复用用户浏览器的登录态：

- 用户先在浏览器登录雪球。
- 浏览器访问 `xueqiu.com` 时会发送 `Cookie` 请求表头。
- 脚本从本机 `headers.txt` 里解析出 Cookie。
- 脚本把 Cookie 交给 `easytrader`。
- `easytrader` 针对指定组合代码，例如 `ZH3114624`，读取持仓或提交调仓。

因此必须区分两类本地状态：

- 组合配置：不敏感，保存组合代码、别名、默认组合。
- 登录表头：敏感，只保存在用户本机 `~/.xq-rebalance/headers.txt`，不能进仓库，不能贴到聊天里。

## 必须遵守

- 不要求用户把 Cookie 或完整请求表头发到聊天里。
- 不把 Cookie、Request Headers、token、账号信息写入仓库、Skill、Markdown 或调仓计划。
- 表头只保存到用户本机：
  - Windows: `C:\Users\<user>\.xq-rebalance\headers.txt`
  - macOS: `~/.xq-rebalance/headers.txt`
- 如果登录过期，让用户重新复制表头，再运行 `--save-headers-from-clipboard`；旧 txt 会被覆盖。
- 用户保存默认组合后，不要每次重复询问组合代码，除非用户明确要切换组合。
- 默认只做 dry-run。真实执行必须同时有用户确认和命令参数 `--execute --confirm EXECUTE_XQ_REBALANCE`。
- 执行后必须提醒用户打开雪球组合页面核对。

## 必读资料

给别人介绍这个 Skill 或从零教学时，先读：

- `references/quickstart-for-beginners.md`
- `references/intro-and-tutorial.md`

需要指导用户复制表头、解决 Chrome/Edge 开发者工具问题时，读：

- `references/setup-auth-and-headers.md`

需要生成调仓计划、解释 full/partial 模式、执行前检查时，读：

- `references/rebalance-plan-and-safety.md`

## 常用命令

脚本位置：

```text
scripts/xq_rebalance.py
```

安装依赖：

```powershell
python -m pip install easytrader
```

macOS 常用：

```bash
python3 -m pip install easytrader
```

保存剪贴板里的请求表头：

```powershell
python scripts/xq_rebalance.py --save-headers-from-clipboard
```

保存默认组合：

```powershell
python scripts/xq_rebalance.py --set-default-portfolio ZH3114624 --portfolio-alias default --portfolio-name "我的策略"
```

读取当前持仓，并生成“现有权重取整”计划：

```powershell
python scripts/xq_rebalance.py --round-existing --output-plan round_existing_plan.json
```

预演目标计划：

```powershell
python scripts/xq_rebalance.py --plan target_plan.json
```

确认后执行：

```powershell
python scripts/xq_rebalance.py --plan target_plan.json --execute --confirm EXECUTE_XQ_REBALANCE
```

## 回答格式

和用户沟通时优先用这个结构：

```text
当前状态：
下一步：
要运行的命令：
这个命令会写入哪里：
这个命令不会做什么：
如何核对：
失败时怎么办：
```

## 禁止模式

- 把 Cookie 当成普通文本让用户贴进聊天。
- 把 `headers.txt`、`cookies.txt` 或真实 `portfolios.json` 放进 Skill/仓库。
- 跳过 dry-run 直接执行。
- 用户没有确认组合代码或默认组合时执行调仓。
- 在 Network 里只搜 `xueqiu`，没搜到就判断没有雪球请求；Chrome 的 Name 列经常不显示域名。
- 点到 `kaspersky-labs.com` 等浏览器安全插件请求，却当成雪球请求。
