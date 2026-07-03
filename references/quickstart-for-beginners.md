# 小白快速开始

这份文档只解决一个问题：第一次用的人，照着做，能把雪球组合调仓跑起来。

不要把 Cookie、Request Headers、表头内容发给别人。它们只保存到你自己电脑里。

## 你需要准备什么

你只需要三样东西：

1. 电脑浏览器：Chrome 或 Edge。
2. 雪球账号：能登录并看到自己的组合。
3. 组合代码：电脑网页登录雪球后，在自己的组合页面里找 `ZH...`。

## 怎么找到组合代码

先用电脑浏览器登录雪球，打开你的组合页面。组合代码通常有两个位置：

1. 组合名称旁边的 `ZH...` 编号。
2. 地址栏 `/P/ZH...` 后面的编号。

地址栏通常类似：

```text
https://xueqiu.com/P/ZHxxxxxxx
```

其中 `ZHxxxxxxx` 这一段就是组合代码。后面所有命令都要把它换成你自己看到的真实代码。

## Windows 第一次配置

### 第 1 步：安装依赖

打开 PowerShell，运行：

```powershell
py -m pip install easytrader
```

如果提示找不到 `py`，改用：

```powershell
python -m pip install easytrader
```

### 第 2 步：登录雪球

用 Chrome 或 Edge 打开你的雪球组合页面：

```text
https://xueqiu.com/P/你的组合代码
```

确认已经登录，并且能看到组合持仓。

### 第 3 步：复制表头

最稳的方式是 `Copy as cURL`：

1. 按 `F12` 打开开发者工具。
2. 点 `Network`。
3. 勾选 `Preserve log`。
4. 刷新页面。
5. 找到名称类似 `ZH...` 的请求。
6. 点进去确认 `Request URL` 是 `xueqiu.com`。
7. 回到请求列表，右键这个请求。
8. 选择 `Copy -> Copy as cURL`。

不要把复制出来的内容发给别人。

### 第 4 步：保存表头到本机

回到 PowerShell，在 Skill 目录下运行：

```powershell
py scripts/xq_rebalance.py --save-headers-from-clipboard
```

成功后会保存到：

```text
C:\Users\<你的用户名>\.xq-rebalance\headers.txt
```

### 第 5 步：保存默认组合

把下面的 `ZHxxxxxxx` 换成你在组合名称旁边或地址栏看到的真实组合代码：

```powershell
py scripts/xq_rebalance.py --set-default-portfolio ZHxxxxxxx --portfolio-alias default --portfolio-name "我的雪球组合"
```

### 第 6 步：测试读取组合

先跑一个安全测试，只读取持仓并生成计划，不会调仓：

```powershell
py scripts/xq_rebalance.py --round-existing --output-plan round_existing_plan.json
```

如果能看到当前持仓和目标权重，说明配置成功。

## macOS 第一次配置

### 第 1 步：安装依赖

打开 Terminal，运行：

```bash
python3 -m pip install easytrader
```

### 第 2 步：登录雪球

用 Chrome 或 Edge 打开你的雪球组合页面：

```text
https://xueqiu.com/P/你的组合代码
```

确认已经登录，并且能看到组合持仓。

### 第 3 步：复制表头

推荐 `Copy as cURL`：

1. 按 `Option + Command + I` 打开开发者工具。
2. 点 `Network`。
3. 勾选 `Preserve log`。
4. 刷新页面。
5. 找到名称类似 `ZH...` 的请求。
6. 点进去确认 `Request URL` 是 `xueqiu.com`。
7. 回到请求列表，右键这个请求。
8. 选择 `Copy -> Copy as cURL`。

不要把复制出来的内容发给别人。

### 第 4 步：保存表头到本机

回到 Terminal，在 Skill 目录下运行：

```bash
python3 scripts/xq_rebalance.py --save-headers-from-clipboard
```

成功后会保存到：

```text
/Users/<你的用户名>/.xq-rebalance/headers.txt
```

### 第 5 步：保存默认组合

把下面的 `ZHxxxxxxx` 换成你在组合名称旁边或地址栏看到的真实组合代码：

```bash
python3 scripts/xq_rebalance.py --set-default-portfolio ZHxxxxxxx --portfolio-alias default --portfolio-name "我的雪球组合"
```

### 第 6 步：测试读取组合

只读取持仓并生成计划，不会调仓：

```bash
python3 scripts/xq_rebalance.py --round-existing --output-plan round_existing_plan.json
```

如果能看到当前持仓和目标权重，说明配置成功。

## 日常怎么用

以后正常使用时，不需要每次复制表头。

只要表头没过期，直接运行：

```powershell
python scripts/xq_rebalance.py --plan target_plan.json
```

确认没问题后，才执行：

```powershell
python scripts/xq_rebalance.py --plan target_plan.json --execute --confirm EXECUTE_XQ_REBALANCE
```

## 表头过期怎么办

如果脚本提示 Cookie 无效、读取失败，或者雪球网页要求重新登录：

1. 浏览器重新登录雪球。
2. 按上面的方式重新 `Copy as cURL`。
3. 再运行：

```powershell
python scripts/xq_rebalance.py --save-headers-from-clipboard
```

旧的 `headers.txt` 会自动被覆盖。

## 最容易卡住的地方

### Network 里搜不到 xueqiu

不要只搜 `xueqiu`。清空过滤框，刷新页面，找 `ZH...` 这个组合页面请求。

### 点到了奇怪的网站

只用 `xueqiu.com` 的请求。不要用 `kaspersky-labs.com`、插件、广告、统计请求。

### 页面一直暂停

如果看到 `Paused in debugger` 或 `debugger;`：

```text
按 F8 继续
或按 Ctrl + F8 禁用断点
```

### 不确定有没有成功

成功标志是：

- 运行 `--save-headers-from-clipboard` 后显示已保存。
- 运行 `--set-default-portfolio` 后显示已保存组合。
- 运行 `--round-existing` 后能看到当前持仓。

这三步都过了，配置就完成了。
