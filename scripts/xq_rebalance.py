#!/usr/bin/env python3
"""Dry-run and optionally execute Xueqiu portfolio rebalancing via easytrader."""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import time
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path
from typing import Any


CONFIRM_TEXT = "EXECUTE_XQ_REBALANCE"
STOCK_CODE_RE = re.compile(r"^(SH|SZ|BJ)?\d{6}$", re.IGNORECASE)
COOKIE_TOKEN_RE = re.compile(r"\b(?:xq_a_token|xqat|xq_r_token|u)=")
CURL_COOKIE_RE = re.compile(r"""-H\s+(['"])cookie:\s*(.*?)\1""", re.IGNORECASE | re.DOTALL)
HEADER_COOKIE_RE = re.compile(r"(?im)^\s*cookie\s*:\s*(.+)$")

SKILL_DIR = Path(__file__).resolve().parents[1]
STATE_DIR = Path(
    os.getenv("XQ_REBALANCE_HOME")
    or os.getenv("XUEQIU_SECRET_DIR")
    or str(Path.home() / ".xq-rebalance")
)
DEFAULT_HEADERS_PATH = STATE_DIR / "headers.txt"
DEFAULT_COOKIES_PATH = STATE_DIR / "cookies.txt"
DEFAULT_CONFIG_PATH = STATE_DIR / "portfolios.json"
LEGACY_COOKIES_PATH = Path.home() / ".xueqiu-auto-rebalance" / "cookies.txt"


@dataclass(frozen=True)
class Target:
    stock_code: str
    weight: Decimal


@dataclass(frozen=True)
class Plan:
    targets: list[Target]
    mode: str
    portfolio_code: str | None
    portfolio_market: str


def parse_decimal(value: Any) -> Decimal:
    text = str(value).strip()
    if text.endswith("%"):
        text = text[:-1].strip()
    try:
        return Decimal(text)
    except InvalidOperation as exc:
        raise ValueError(f"权重格式不合法: {value!r}") from exc


def fmt_decimal(value: Decimal) -> str:
    quantized = value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return f"{quantized.normalize():f}"


def normalize_stock_code(value: Any) -> str:
    code = str(value).strip().upper()
    if not code:
        raise ValueError("股票代码为空")
    return code


def extract_cookie_value(text: str) -> str:
    raw = text.strip()
    if not raw:
        raise ValueError("剪贴板或表头文件为空")

    curl_match = CURL_COOKIE_RE.search(raw)
    if curl_match:
        return " ".join(curl_match.group(2).split())

    header_match = HEADER_COOKIE_RE.search(raw)
    if header_match:
        return " ".join(header_match.group(1).split())

    lines = [line.strip() for line in raw.splitlines() if line.strip()]
    for index, line in enumerate(lines):
        lower = line.lower()
        if lower == "cookie" and index + 1 < len(lines):
            return " ".join(lines[index + 1].split())
        if lower.startswith("cookie "):
            return " ".join(line[7:].split())

    joined = " ".join(lines)
    if COOKIE_TOKEN_RE.search(joined) and ";" in joined:
        return joined

    raise ValueError("没有识别到雪球 Cookie 表头")


def clipboard_from_tkinter() -> str | None:
    try:
        import tkinter  # type: ignore
    except Exception:
        return None

    try:
        root = tkinter.Tk()
        root.withdraw()
        try:
            return root.clipboard_get()
        finally:
            root.destroy()
    except Exception:
        return None


def clipboard_from_command(command: list[str]) -> str | None:
    try:
        return subprocess.check_output(command, text=True, stderr=subprocess.DEVNULL)
    except Exception:
        return None


def get_clipboard_text() -> str:
    text = clipboard_from_tkinter()
    if text:
        return text

    if sys.platform == "darwin":
        text = clipboard_from_command(["pbpaste"])
        if text:
            return text

    if os.name == "nt":
        powershell = shutil.which("powershell") or shutil.which("powershell.exe") or shutil.which("pwsh")
        if powershell:
            text = clipboard_from_command([powershell, "-NoProfile", "-Command", "Get-Clipboard -Raw"])
            if text:
                return text

    for command in (["wl-paste"], ["xclip", "-selection", "clipboard", "-o"], ["xsel", "--clipboard", "--output"]):
        if shutil.which(command[0]):
            text = clipboard_from_command(command)
            if text:
                return text

    raise RuntimeError("当前系统无法读取剪贴板，请改用 --cookies-file 指定本机表头文件")


def validate_cookie_shape(cookie: str) -> list[str]:
    warnings: list[str] = []
    if "xq_a_token=" not in cookie and "xqat=" not in cookie:
        warnings.append("cookie 中没有 xq_a_token/xqat，登录可能失败")
    if "u=" not in cookie:
        warnings.append("cookie 中没有 u，登录可能失败")
    return warnings


def write_secret_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.strip() + "\n", encoding="utf-8")
    try:
        path.chmod(stat.S_IRUSR | stat.S_IWUSR)
    except OSError:
        pass


def save_headers_from_clipboard(args: argparse.Namespace) -> None:
    raw_headers = get_clipboard_text().strip()
    cookie = extract_cookie_value(raw_headers)
    warnings = validate_cookie_shape(cookie)
    headers_path = Path(args.headers_file) if args.headers_file else DEFAULT_HEADERS_PATH
    write_secret_text(headers_path, raw_headers)
    print(f"已保存雪球请求表头到: {headers_path}")
    print("这会覆盖旧的本机表头文件；该文件不在仓库内。")
    for warning in warnings:
        print(f"提醒: {warning}")


def save_cookies_from_clipboard(args: argparse.Namespace) -> None:
    cookie = extract_cookie_value(get_clipboard_text())
    warnings = validate_cookie_shape(cookie)
    cookie_path = Path(args.cookies_file) if args.cookies_file else DEFAULT_COOKIES_PATH
    write_secret_text(cookie_path, cookie)
    print(f"已保存提取后的雪球 Cookie 到: {cookie_path}")
    print("这会覆盖旧的本机 Cookie 文件；该文件不在仓库内。")
    for warning in warnings:
        print(f"提醒: {warning}")


def clear_saved_auth(args: argparse.Namespace) -> None:
    paths = [
        Path(args.headers_file) if args.headers_file else DEFAULT_HEADERS_PATH,
        Path(args.cookies_file) if args.cookies_file else DEFAULT_COOKIES_PATH,
    ]
    for path in paths:
        if path.exists():
            path.unlink()
            print(f"已删除: {path}")
        else:
            print(f"未找到: {path}")


def load_config(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(data, dict):
        raise ValueError(f"配置文件必须是 JSON 对象: {path}")
    return data


def save_config(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def save_default_portfolio(args: argparse.Namespace) -> None:
    code = str(args.set_default_portfolio).strip().upper()
    if not code.startswith("ZH"):
        raise ValueError("雪球组合代码通常以 ZH 开头，例如 ZH3114624")

    path = Path(args.config)
    data = load_config(path)
    portfolios = data.get("portfolios")
    if not isinstance(portfolios, dict):
        portfolios = {}

    alias = args.portfolio_alias or "default"
    for item in portfolios.values():
        if isinstance(item, dict):
            item["default"] = False
    portfolios[alias] = {
        "name": args.portfolio_name or alias,
        "code": code,
        "market": args.portfolio_market or "cn",
        "default": True,
    }
    data["default_portfolio_code"] = code
    data["default_portfolio_market"] = args.portfolio_market or "cn"
    data["portfolios"] = portfolios
    save_config(path, data)
    print(f"已保存默认组合 {code} 到: {path}")


def resolve_portfolio(args: argparse.Namespace, metadata: dict[str, Any] | None = None) -> tuple[str | None, str]:
    metadata = metadata or {}
    config = load_config(Path(args.config))
    portfolios = config.get("portfolios", {})
    if not isinstance(portfolios, dict):
        portfolios = {}

    alias = args.portfolio_alias or metadata.get("portfolio_alias")
    alias_config: dict[str, Any] = {}
    if alias:
        raw_alias_config = portfolios.get(alias)
        if raw_alias_config is None:
            raise ValueError(f"配置里没有这个组合别名: {alias}")
        if not isinstance(raw_alias_config, dict):
            raise ValueError(f"组合别名配置必须是对象: {alias}")
        alias_config = raw_alias_config
    else:
        for item in portfolios.values():
            if isinstance(item, dict) and item.get("default"):
                alias_config = item
                break

    portfolio_code = (
        args.portfolio_code
        or metadata.get("portfolio_code")
        or os.getenv("XQ_PORTFOLIO_CODE")
        or os.getenv("XUEQIU_PORTFOLIO_CODE")
        or alias_config.get("code")
        or config.get("default_portfolio_code")
    )
    portfolio_market = (
        args.portfolio_market
        or metadata.get("portfolio_market")
        or os.getenv("XQ_PORTFOLIO_MARKET")
        or os.getenv("XUEQIU_PORTFOLIO_MARKET")
        or alias_config.get("market")
        or config.get("default_portfolio_market")
        or "cn"
    )
    return portfolio_code, str(portfolio_market).strip().lower()


def read_json_plan(path: Path) -> tuple[list[Target], dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(data, dict):
        raise ValueError("JSON 计划必须是一个对象")

    raw_targets: Any
    if "targets" in data:
        raw_targets = data["targets"]
    elif "weights" in data:
        raw_targets = data["weights"]
    else:
        ignored = {"portfolio_code", "portfolio_market", "portfolio_alias", "mode"}
        raw_targets = {k: v for k, v in data.items() if k not in ignored}

    targets = parse_targets(raw_targets)
    return targets, data


def read_csv_plan(path: Path) -> tuple[list[Target], dict[str, Any]]:
    with path.open("r", encoding="utf-8-sig", newline="") as fh:
        rows = list(csv.DictReader(fh))

    if not rows:
        raise ValueError("CSV 计划为空")

    stock_columns = ["stock_code", "code", "symbol", "证券代码", "标的"]
    weight_columns = ["weight", "target_weight", "目标权重", "权重"]
    stock_col = next((col for col in stock_columns if col in rows[0]), None)
    weight_col = next((col for col in weight_columns if col in rows[0]), None)

    if not stock_col or not weight_col:
        raise ValueError("CSV 计划需要包含列: stock_code, weight")

    targets = [
        Target(stock_code=normalize_stock_code(row[stock_col]), weight=parse_decimal(row[weight_col]))
        for row in rows
    ]
    return targets, {}


def parse_targets(raw_targets: Any) -> list[Target]:
    if isinstance(raw_targets, dict):
        return [
            Target(stock_code=normalize_stock_code(code), weight=parse_decimal(weight))
            for code, weight in raw_targets.items()
        ]

    if not isinstance(raw_targets, list):
        raise ValueError("targets 必须是列表或对象")

    targets: list[Target] = []
    for item in raw_targets:
        if not isinstance(item, dict):
            raise ValueError("每个 target 必须是对象")
        code = item.get("stock_code", item.get("code", item.get("symbol")))
        if code is None:
            raise ValueError(f"target 缺少 stock_code: {item!r}")
        if "weight" not in item and "target_weight" not in item:
            raise ValueError(f"target 缺少 weight: {item!r}")
        weight = item.get("weight", item.get("target_weight"))
        targets.append(Target(stock_code=normalize_stock_code(code), weight=parse_decimal(weight)))
    return targets


def load_plan(path: Path, args: argparse.Namespace) -> Plan:
    suffix = path.suffix.lower()
    if suffix == ".json":
        targets, metadata = read_json_plan(path)
    elif suffix == ".csv":
        targets, metadata = read_csv_plan(path)
    else:
        raise ValueError("计划文件必须是 .json 或 .csv")

    mode = (args.mode or metadata.get("mode") or "full").strip().lower()
    portfolio_code, portfolio_market = resolve_portfolio(args, metadata)
    return Plan(targets=targets, mode=mode, portfolio_code=portfolio_code, portfolio_market=portfolio_market)


def validate_plan(plan: Plan, tolerance: Decimal) -> list[str]:
    warnings: list[str] = []
    errors: list[str] = []

    if plan.mode not in {"full", "partial"}:
        errors.append("mode 必须是 'full' 或 'partial'")
    if not plan.targets:
        errors.append("计划里没有 targets")

    seen: set[str] = set()
    for target in plan.targets:
        if target.stock_code in seen:
            errors.append(f"股票代码重复: {target.stock_code}")
        seen.add(target.stock_code)
        if not STOCK_CODE_RE.match(target.stock_code):
            warnings.append(f"股票代码可能不合法: {target.stock_code}")
        elif not target.stock_code[:2].isalpha():
            warnings.append(f"股票代码没有交易所前缀: {target.stock_code}")
        if target.weight < Decimal("0") or target.weight > Decimal("100"):
            errors.append(f"{target.stock_code} 权重超出 0-100 范围: {target.weight}")

    total = sum((target.weight for target in plan.targets), Decimal("0"))
    if plan.mode == "full" and abs(total - Decimal("100")) > tolerance:
        errors.append(f"full 模式目标权重合计必须等于 100，目前是 {fmt_decimal(total)}")
    if not plan.portfolio_code:
        warnings.append("缺少 portfolio_code；请用 --portfolio-code 指定，或先用 --set-default-portfolio 保存默认组合")

    if errors:
        raise ValueError("\n".join(errors))
    return warnings


def read_cookies(args: argparse.Namespace) -> str | None:
    if args.cookies:
        return args.cookies.strip()
    if args.cookies_file:
        return extract_cookie_value(Path(args.cookies_file).read_text(encoding="utf-8"))
    value = os.getenv("XQ_COOKIES") or os.getenv("XUEQIU_COOKIES")
    if value:
        return extract_cookie_value(value)
    if not args.no_default_auth_file:
        for path in (DEFAULT_HEADERS_PATH, DEFAULT_COOKIES_PATH, LEGACY_COOKIES_PATH):
            if path.exists():
                return extract_cookie_value(path.read_text(encoding="utf-8"))
    return None


def create_xueqiu_user(args: argparse.Namespace, portfolio_code: str, portfolio_market: str) -> Any:
    cookies = read_cookies(args)
    if not cookies:
        raise ValueError("缺少雪球登录表头。请先复制请求表头，并运行 --save-headers-from-clipboard。")

    try:
        import easytrader  # type: ignore
    except ImportError as exc:
        raise RuntimeError("当前 Python 环境没有安装 easytrader。请运行: python -m pip install easytrader") from exc

    user = easytrader.use("xq")
    user.prepare(cookies=cookies, portfolio_code=portfolio_code, portfolio_market=portfolio_market)
    return user


def quantize_weight(value: Decimal, increment: Decimal) -> Decimal:
    if increment <= 0:
        raise ValueError("--round-to 必须大于 0")
    units = (value / increment).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    return (units * increment).quantize(increment, rounding=ROUND_HALF_UP)


def generate_round_existing_plan(args: argparse.Namespace) -> Plan:
    portfolio_code, portfolio_market = resolve_portfolio(args, {})
    if not portfolio_code:
        raise ValueError("--round-existing 需要组合代码，请先保存默认组合或用 --portfolio-code 指定")

    user = create_xueqiu_user(args, portfolio_code, portfolio_market)
    holdings = user._get_position()
    if not holdings:
        raise ValueError("该组合没有可取整的股票持仓")

    increment = parse_decimal(args.round_to)
    rounded: list[dict[str, Any]] = []
    for holding in holdings:
        code = normalize_stock_code(holding.get("stock_symbol", holding.get("code")))
        current_weight = parse_decimal(holding.get("weight"))
        target_weight = quantize_weight(current_weight, increment)
        rounded.append(
            {
                "stock_code": code,
                "stock_name": holding.get("stock_name") or holding.get("name") or "",
                "current_weight": current_weight,
                "target_weight": target_weight,
                "round_delta": target_weight - current_weight,
            }
        )

    target_total = sum((item["target_weight"] for item in rounded), Decimal("0"))
    if target_total > Decimal("100"):
        candidates = sorted(
            (item for item in rounded if item["target_weight"] > Decimal("0")),
            key=lambda item: item["round_delta"],
            reverse=True,
        )
        idx = 0
        while target_total > Decimal("100") and candidates:
            item = candidates[idx % len(candidates)]
            if item["target_weight"] >= increment:
                item["target_weight"] -= increment
                target_total -= increment
            idx += 1
            if idx > 1000:
                raise ValueError("无法把取整后的权重合计压到 100 以内")

    print("当前持仓 -> 取整后的目标权重")
    for item in rounded:
        print(
            f"  - {item['stock_code']} {item['stock_name']}: "
            f"{fmt_decimal(item['current_weight'])}% -> {fmt_decimal(item['target_weight'])}%"
        )

    return Plan(
        targets=[Target(stock_code=item["stock_code"], weight=item["target_weight"]) for item in rounded],
        mode="partial",
        portfolio_code=portfolio_code,
        portfolio_market=portfolio_market,
    )


def write_plan(plan: Plan, path: Path, source: str) -> None:
    data = {
        "portfolio_code": plan.portfolio_code,
        "portfolio_market": plan.portfolio_market,
        "mode": plan.mode,
        "generated_from": source,
        "targets": [{"stock_code": target.stock_code, "weight": fmt_decimal(target.weight)} for target in plan.targets],
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def print_plan(plan: Plan, warnings: list[str]) -> None:
    total = sum((target.weight for target in plan.targets), Decimal("0"))
    print("雪球组合调仓计划")
    print(f"  模式: {plan.mode}")
    print(f"  组合代码: {plan.portfolio_code or '(未设置)'}")
    print(f"  市场: {plan.portfolio_market}")
    print(f"  目标数量: {len(plan.targets)}")
    print(f"  目标权重合计: {fmt_decimal(total)}")
    print("")
    print("目标权重:")
    for target in plan.targets:
        print(f"  - {target.stock_code}: {fmt_decimal(target.weight)}%")
    if warnings:
        print("")
        print("提醒:")
        for warning in warnings:
            print(f"  - {warning}")


def safe_get(label: str, getter: Any) -> None:
    try:
        value = getter()
    except Exception as exc:
        print(f"{label}: 读取失败 ({exc})")
        return
    print(f"{label}:")
    print(value)


def execute_plan(plan: Plan, args: argparse.Namespace) -> None:
    if args.confirm != CONFIRM_TEXT:
        raise ValueError(f"--execute 必须同时带上 --confirm {CONFIRM_TEXT}")
    if not plan.portfolio_code:
        raise ValueError("执行调仓需要 portfolio_code")
    user = create_xueqiu_user(args, plan.portfolio_code, plan.portfolio_market)

    print("")
    print("执行前")
    safe_get("资金/资产", lambda: user.balance)
    safe_get("持仓", lambda: user.position)

    print("")
    print("正在提交 adjust_weight 调仓请求")
    for target in plan.targets:
        print(f"  adjust_weight({target.stock_code}, {fmt_decimal(target.weight)})")
        result = user.adjust_weight(target.stock_code, float(target.weight))
        if result is not None:
            print(f"    返回: {result}")
        if args.sleep_seconds > 0:
            time.sleep(args.sleep_seconds)

    print("")
    print("执行后")
    safe_get("资金/资产", lambda: user.balance)
    safe_get("持仓", lambda: user.position)
    print("")
    print("请打开雪球组合页面，手动核对最终权重。")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="通过 easytrader 预演或执行雪球组合目标权重调仓。")
    parser.add_argument("--plan", help="目标权重计划文件路径，支持 .json 或 .csv。")
    parser.add_argument("--mode", choices=["full", "partial"], help="覆盖计划里的模式：full 或 partial。")
    parser.add_argument("--config", default=str(DEFAULT_CONFIG_PATH), help="本机组合配置 JSON 路径。")
    parser.add_argument("--portfolio-alias", help="本机配置里的组合别名。")
    parser.add_argument("--portfolio-name", help="保存配置时使用的组合名称。")
    parser.add_argument("--portfolio-code", help="雪球组合代码，例如 ZH3114624。")
    parser.add_argument("--portfolio-market", default=None, help="雪球市场，A 股通常是 cn。")
    parser.add_argument("--set-default-portfolio", help="把这个组合代码保存为本机默认组合。")
    parser.add_argument("--tolerance", default="0.01", help="full 模式下目标权重合计容忍误差。")
    parser.add_argument("--round-existing", action="store_true", help="读取当前持仓，并把已有权重取整生成计划。")
    parser.add_argument("--round-to", default="1", help="取整单位，默认 1 表示 1 个百分点。")
    parser.add_argument("--output-plan", help="把生成的计划写入这个 JSON 文件。")
    parser.add_argument("--execute", action="store_true", help="真实调用 easytrader adjust_weight 提交调仓。")
    parser.add_argument("--confirm", default="", help=f"真实执行必须填写的确认文本: {CONFIRM_TEXT}")
    parser.add_argument("--cookies", help="原始 Cookie 或复制的请求表头。更推荐使用本机 auth 文件。")
    parser.add_argument("--cookies-file", help="仓库外的本机 Cookie/表头文件路径。")
    parser.add_argument("--headers-file", help="仓库外的本机请求表头文件路径。")
    parser.add_argument("--no-default-auth-file", action="store_true", help="不读取默认本机认证文件。")
    parser.add_argument("--save-headers-from-clipboard", action="store_true", help="从剪贴板保存复制的请求表头。")
    parser.add_argument("--save-cookies-from-clipboard", action="store_true", help="从剪贴板提取并保存 Cookie。")
    parser.add_argument("--clear-saved-auth", action="store_true", help="删除本机保存的表头/Cookie 文件。")
    parser.add_argument("--clear-saved-cookies", action="store_true", help="--clear-saved-auth 的兼容别名。")
    parser.add_argument("--show-auth-path", action="store_true", help="显示默认本机认证文件路径。")
    parser.add_argument("--show-cookies-path", action="store_true", help="--show-auth-path 的兼容别名。")
    parser.add_argument("--show-config-path", action="store_true", help="显示默认本机组合配置路径。")
    parser.add_argument("--sleep-seconds", type=float, default=1.0, help="每次 adjust_weight 调用之间的等待秒数。")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.show_auth_path or args.show_cookies_path:
            print(f"headers: {DEFAULT_HEADERS_PATH}")
            print(f"cookies: {DEFAULT_COOKIES_PATH}")
            return 0
        if args.show_config_path:
            print(DEFAULT_CONFIG_PATH)
            return 0
        if args.save_headers_from_clipboard:
            save_headers_from_clipboard(args)
            return 0
        if args.save_cookies_from_clipboard:
            save_cookies_from_clipboard(args)
            return 0
        if args.clear_saved_auth or args.clear_saved_cookies:
            clear_saved_auth(args)
            return 0
        if args.set_default_portfolio:
            save_default_portfolio(args)
            return 0

        tolerance = parse_decimal(args.tolerance)
        if args.round_existing:
            plan = generate_round_existing_plan(args)
            source = "round_existing"
        else:
            if not args.plan:
                raise ValueError("除非使用 --round-existing，否则必须提供 --plan")
            plan = load_plan(Path(args.plan), args)
            source = str(args.plan)
        warnings = validate_plan(plan, tolerance)
        print_plan(plan, warnings)
        if args.output_plan:
            write_plan(plan, Path(args.output_plan), source)
            print("")
            print(f"已写入计划: {args.output_plan}")
        if not args.execute:
            print("")
            print(f"当前只是 dry-run 预演。若要真实提交调仓，请加 --execute --confirm {CONFIRM_TEXT}")
            return 0
        execute_plan(plan, args)
        return 0
    except Exception as exc:
        print(f"错误: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
