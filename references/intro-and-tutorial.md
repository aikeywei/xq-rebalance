# XQ Rebalance 介绍与教程

## 这个 Skill 是什么

`xq-rebalance` 用来辅助完成雪球组合自动调仓。它适合这种场景：

- 你已经在电脑浏览器登录雪球，并能在自己的组合页面看到组合名称旁边或页面地址里的 `ZH...` 组合代码。
- 你有一个策略，每天或每周会生成目标权重。
- 你不想每次手动打开雪球组合逐个改权重。
- 你希望先预演、确认无误后，再提交组合调仓。

它做的是雪球组合调仓，不是券商实盘交易。即便如此，也要按真实交易流程对待：先预演，再确认，再执行，最后回到雪球页面核对。

## 它为什么需要复制“表头”

雪球网页知道你已经登录，是因为浏览器请求里带了登录 Cookie。这个 Cookie 在开发者工具里表现为请求表头的一部分：

```text
Cookie: xq_a_token=...; xqat=...; u=...; ...
```

脚本不能凭空登录你的雪球账号，也不应该保存账号密码。正确做法是：

1. 你自己在浏览器登录雪球。
2. 从浏览器复制 `xueqiu.com` 请求表头。
3. 脚本把这段表头保存到你本机的 txt。
4. 后续每次运行时，脚本自动读取这个 txt。
5. 如果过期，重新复制表头并覆盖旧 txt。

## 本机文件保存在哪里

默认目录：

```text
~/.xq-rebalance/
```

Windows 通常是：

```text
C:\Users\<你的用户名>\.xq-rebalance\
```

macOS 通常是：

```text
/Users/<你的用户名>/.xq-rebalance/
```

里面主要有：

- `headers.txt`：复制下来的雪球请求表头，敏感，不要分享。
- `cookies.txt`：兼容旧流程的 Cookie 文件，可不用。
- `portfolios.json`：你的组合代码和别名，比如默认组合。

这些文件不应该放进 Git 仓库，也不应该发给别人。

## 第一次使用：Windows

1. 安装依赖：

```powershell
py -m pip install easytrader
```

如果你的电脑没有 `py`，用：

```powershell
python -m pip install easytrader
```

2. 用电脑浏览器打开雪球并登录，进入自己的组合页面。组合代码看两个地方：

   - 优先看组合名称旁边的 `ZH...` 编号。
   - 如果页面上没看到，就看地址栏 `/P/ZH...` 后面的编号。

   地址栏通常类似：

```text
https://xueqiu.com/P/ZHxxxxxxx
```

3. 复制请求表头。推荐先看 `setup-auth-and-headers.md`，里面有截图排坑逻辑。

4. 保存剪贴板里的表头：

```powershell
py scripts/xq_rebalance.py --save-headers-from-clipboard
```

5. 保存默认组合：

```powershell
py scripts/xq_rebalance.py --set-default-portfolio ZHxxxxxxx --portfolio-alias default --portfolio-name "我的策略"
```

6. 读取当前持仓并生成取整计划：

```powershell
py scripts/xq_rebalance.py --round-existing --output-plan round_existing_plan.json
```

这一步只读取和生成计划，不会调仓。

7. 预演计划：

```powershell
py scripts/xq_rebalance.py --plan round_existing_plan.json
```

8. 确认无误后执行：

```powershell
py scripts/xq_rebalance.py --plan round_existing_plan.json --execute --confirm EXECUTE_XQ_REBALANCE
```

执行后打开雪球组合页面核对。

## 第一次使用：macOS

1. 安装依赖：

```bash
python3 -m pip install easytrader
```

2. 用电脑浏览器打开雪球并登录，进入自己的组合页面。组合代码看两个地方：

   - 优先看组合名称旁边的 `ZH...` 编号。
   - 如果页面上没看到，就看地址栏 `/P/ZH...` 后面的编号。

   地址栏通常类似：

```text
https://xueqiu.com/P/ZHxxxxxxx
```

3. 复制请求表头。

4. 保存剪贴板里的表头：

```bash
python3 scripts/xq_rebalance.py --save-headers-from-clipboard
```

5. 保存默认组合：

```bash
python3 scripts/xq_rebalance.py --set-default-portfolio ZHxxxxxxx --portfolio-alias default --portfolio-name "我的策略"
```

6. 生成当前持仓取整计划：

```bash
python3 scripts/xq_rebalance.py --round-existing --output-plan round_existing_plan.json
```

7. 预演：

```bash
python3 scripts/xq_rebalance.py --plan round_existing_plan.json
```

8. 确认后执行：

```bash
python3 scripts/xq_rebalance.py --plan round_existing_plan.json --execute --confirm EXECUTE_XQ_REBALANCE
```

## 日常使用流程

日常不需要每次复制表头。只要 `headers.txt` 没过期，就直接：

```powershell
python scripts/xq_rebalance.py --plan target_plan.json
```

确认无误后：

```powershell
python scripts/xq_rebalance.py --plan target_plan.json --execute --confirm EXECUTE_XQ_REBALANCE
```

如果过期：

1. 浏览器重新登录雪球。
2. 重新复制请求表头。
3. 再运行：

```powershell
python scripts/xq_rebalance.py --save-headers-from-clipboard
```

旧的 `headers.txt` 会被覆盖。

## 目标权重计划格式

JSON 示例：

```json
{
  "mode": "full",
  "targets": [
    {"stock_code": "SH510300", "weight": 50},
    {"stock_code": "SH511880", "weight": 50}
  ]
}
```

如果已经保存默认组合，可以不写 `portfolio_code`。如果要指定组合：

```json
{
  "portfolio_code": "ZHxxxxxxx",
  "portfolio_market": "cn",
  "mode": "full",
  "targets": [
    {"stock_code": "SH510300", "weight": 50},
    {"stock_code": "SH511880", "weight": 50}
  ]
}
```

## 怎么判断已经成功

成功的最低标准：

- 能保存 headers。
- 能保存默认组合。
- 能读取当前持仓。
- dry-run 显示目标组合正确。
- 执行后雪球网页上的组合权重与计划一致。

失败时不要盲目重复执行，先看雪球页面实际状态。
