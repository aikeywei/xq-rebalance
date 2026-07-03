# 调仓计划与安全检查

## 两种调仓模式

`full` 模式：

- 表示“这就是完整目标组合”。
- 目标权重合计必须等于 100。
- 如果旧持仓要清掉，必须在计划里显式写成 `0`。
- 适合策略每天或每周输出完整组合。

`partial` 模式：

- 表示“只调整列出来的这些标的”。
- 目标权重不要求合计 100。
- 没列出的标的不会主动纳入计划。
- 适合临时微调，或“把当前已有持仓权重取整”。

不确定时，优先用 `full`，因为它更明确。

## JSON 计划格式

最小格式：

```json
{
  "mode": "full",
  "targets": [
    {"stock_code": "SH510300", "weight": 50},
    {"stock_code": "SH511880", "weight": 50}
  ]
}
```

如果没有保存默认组合，写完整：

```json
{
  "portfolio_code": "ZH3114624",
  "portfolio_market": "cn",
  "mode": "full",
  "targets": [
    {"stock_code": "SH510300", "weight": 50},
    {"stock_code": "SH511880", "weight": 50}
  ]
}
```

说明：

- `portfolio_code` 是雪球组合代码，例如 `ZH3114624`。
- `portfolio_market` A 股一般是 `cn`。
- `stock_code` 要带交易所前缀，例如 `SH510300`、`SZ159915`。
- `weight` 是目标百分比，不是金额、股数或价格。

## CSV 计划格式

```csv
stock_code,weight
SH510300,50
SH511880,50
```

## 保存默认组合

单组合用户先保存默认组合：

```powershell
python scripts/xq_rebalance.py --set-default-portfolio ZH3114624 --portfolio-alias default --portfolio-name "我的策略"
```

保存后，计划文件里可以不写 `portfolio_code`。

## 读取当前持仓并取整

如果只是测试流程，可以先把当前已有持仓权重取整：

```powershell
python scripts/xq_rebalance.py --round-existing --output-plan round_existing_plan.json
```

这一步：

- 会读取当前组合持仓。
- 会生成一个目标计划。
- 不会提交调仓。

## Dry-run 检查

执行前必须先 dry-run：

```powershell
python scripts/xq_rebalance.py --plan target_plan.json
```

检查点：

- 组合代码是否正确。
- 市场是否正确，A 股通常是 `cn`。
- 模式是 `full` 还是 `partial`。
- `full` 模式合计是否为 100。
- 股票代码是否有 `SH` / `SZ` / `BJ` 前缀。
- 权重是否是目标百分比。
- 计划里有没有遗漏要清零的旧持仓。

## 执行调仓

只有 dry-run 通过，并且用户确认后，才能执行：

```powershell
python scripts/xq_rebalance.py --plan target_plan.json --execute --confirm EXECUTE_XQ_REBALANCE
```

执行后必须打开雪球组合页面核对：

```text
https://xueqiu.com/P/<你的组合代码>
```

## 多组合设计

多个组合不要混在一次不可回滚的执行里。

推荐做法：

1. 在本机 `~/.xq-rebalance/portfolios.json` 里保存多个别名。
2. 每个组合单独生成计划。
3. 每个组合单独 dry-run。
4. 每个组合单独确认执行。

配置示例：

```json
{
  "default_portfolio_code": "ZH1111111",
  "default_portfolio_market": "cn",
  "portfolios": {
    "momentum": {
      "name": "动量策略",
      "code": "ZH1111111",
      "market": "cn",
      "default": true
    },
    "value": {
      "name": "价值策略",
      "code": "ZH2222222",
      "market": "cn",
      "default": false
    }
  }
}
```

指定别名运行：

```powershell
python scripts/xq_rebalance.py --portfolio-alias momentum --plan momentum_plan.json
```

## 失败处理

如果执行到一半失败：

- 不要立刻重复执行。
- 先打开雪球页面看实际权重。
- 判断哪些标的已经提交、哪些没有。
- 必要时重新生成一个修正计划，而不是重跑旧计划。
