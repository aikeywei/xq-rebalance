# 登录表头获取与排坑

## 你要复制的到底是什么

你不是复制股票表格，也不是复制组合持仓。你要复制的是浏览器访问雪球时发送给 `xueqiu.com` 的请求表头，最关键的是里面这一项：

```text
Cookie: xq_a_token=...; xqat=...; u=...; ...
```

脚本可以处理三种复制内容：

- 只复制 `Cookie` 后面的值。
- 复制整个 `Request Headers` 区块。
- 右键请求后 `Copy -> Copy as cURL`。

推荐复制整个 `Request Headers` 或 `Copy as cURL`，脚本会自己提取 Cookie。

## 本机保存逻辑

复制完表头后运行：

```powershell
python scripts/xq_rebalance.py --save-headers-from-clipboard
```

脚本会把剪贴板内容保存到：

```text
~/.xq-rebalance/headers.txt
```

Windows:

```text
C:\Users\<user>\.xq-rebalance\headers.txt
```

macOS:

```text
/Users/<user>/.xq-rebalance/headers.txt
```

以后脚本每次自动读取这个 txt。如果登录过期，就重新复制表头，再运行同一条保存命令，旧文件会被覆盖。

## 方法 A：Application 里复制 Cookie

适合不熟悉 Network 的用户。

1. 用电脑浏览器登录雪球，打开自己的组合页面。组合代码看组合名称旁边的 `ZH...`，或者看地址栏 `/P/ZH...`。地址栏通常类似：

   ```text
   https://xueqiu.com/P/ZHxxxxxxx
   ```

2. 确认已经登录。
3. 按 `F12` 打开开发者工具。
4. 点 `Application`。
5. 左侧展开 `Storage -> Cookies`。
6. 点 `https://xueqiu.com`。
7. 右侧表格里确认有 `xq_a_token`、`xqat`、`u` 等 cookie。
8. 把相关 cookie 拼成：

   ```text
   name=value; name=value; name=value
   ```

9. 复制后运行：

   ```powershell
   python scripts/xq_rebalance.py --save-headers-from-clipboard
   ```

如果你觉得拼 cookie 麻烦，用方法 B 或 C。

## 方法 B：Network 里复制 Request Headers

这是最常用的方法。

1. 打开雪球组合页面并登录。
2. 按 `F12`。
3. 点 `Network`。
4. 勾选 `Preserve log`。
5. 清空过滤框。
6. 刷新网页。
7. 在请求列表里点真正属于雪球的请求，优先点名称类似：

   ```text
   ZHxxxxxxx?...
   ```

8. 点右侧或下方的 `Headers`。
9. 先看 `General` 里的 `Request URL`，确认域名是：

   ```text
   xueqiu.com
   ```

10. 往下找 `Request Headers`。
11. 复制 `Cookie` 那一行，或者复制整个 `Request Headers` 区块。
12. 运行：

   ```powershell
   python scripts/xq_rebalance.py --save-headers-from-clipboard
   ```

## 方法 C：Copy as cURL

这是最稳的方法之一。

1. 打开 `Network`。
2. 刷新雪球页面。
3. 找到一个真正属于 `xueqiu.com` 的请求。
4. 右键它。
5. 选择：

   ```text
   Copy -> Copy as cURL
   ```

6. 运行：

   ```powershell
   python scripts/xq_rebalance.py --save-headers-from-clipboard
   ```

脚本会从 cURL 命令里自动提取 `Cookie`。

## 常见坑

### Network 里搜 `xueqiu` 什么都没有

这是 Chrome/Edge 的常见坑。Network 的过滤有时主要匹配 `Name` 列，而 `Name` 列不一定显示域名。

处理方式：

- 清空过滤框。
- 勾选 `Preserve log`。
- 刷新页面。
- 找名称像 `ZHxxxxxxx?...` 的请求。
- 点进去后看 `General -> Request URL` 是否是 `https://xueqiu.com/...`。

### 点到了卡巴斯基或其他插件请求

不要用这种请求：

```text
gc.kis.v2.scr.kaspersky-labs.com
```

这不是雪球，是浏览器安全插件请求。复制它没有用。

### 一直出现 `debugger`，页面暂停

如果开发者工具显示：

```text
Paused in debugger
debugger;
VM101619
```

处理方式：

- 按 `F8` 继续运行。
- 或按 `Ctrl + F8` 禁用断点。
- 然后不要停在 `Sources`，回到 `Network` 或 `Application`。

这不是雪球账号问题，只是网页脚本触发了调试暂停。

### 没看到 Request Headers

通常是两个原因：

- 点错请求了，比如点到插件请求。
- 详情面板停在 `Response Headers` 附近，需要继续往下滚。

解决：

- 回到请求列表。
- 点 `ZH...` 或确认 URL 是 `xueqiu.com` 的请求。
- 在 `Headers` 里往下滚到 `Request Headers`。

### 表头过期

现象：

- 读取持仓失败。
- 脚本提示 Cookie 缺失或无效。
- 雪球网页要求重新登录。

处理：

1. 浏览器重新登录雪球。
2. 重新复制请求表头。
3. 运行：

   ```powershell
   python scripts/xq_rebalance.py --save-headers-from-clipboard
   ```

这会覆盖旧的 `headers.txt`。

## 查看和清理本地认证文件

查看保存路径：

```powershell
python scripts/xq_rebalance.py --show-auth-path
```

删除本地认证文件：

```powershell
python scripts/xq_rebalance.py --clear-saved-auth
```
