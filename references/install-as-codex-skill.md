# 安装为 Codex Skill

这份文档只解决安装问题：别人怎么把 `xq-rebalance` 放进自己的 Codex。

## 先说结论

- 不是 npm 包。
- 不用 `npx`。
- 不需要先登录雪球才能安装。
- 安装动作只是把这个仓库下载到本机 Codex 的 skills 目录。
- 登录雪球、复制表头、设置组合代码，是安装完成后的配置步骤。

## 方式 A：让 Codex 自动安装

在 Codex 里直接说：

```text
安装 GitHub 仓库 https://github.com/aikeywei/xq-rebalance 根目录这个 skill，名称用 xq-rebalance。
```

如果当前 Codex 支持 `skill-installer`，它会自动下载安装到：

```text
~/.codex/skills/xq-rebalance
```

安装后重启 Codex。

如果自动安装失败，通常是 installer 没有识别“仓库根目录就是 skill”。这时直接用下面的手动安装方式。

## 方式 B：Windows 手动安装

打开 PowerShell，运行：

```powershell
git clone https://github.com/aikeywei/xq-rebalance.git $env:USERPROFILE\.codex\skills\xq-rebalance
py -m pip install -r $env:USERPROFILE\.codex\skills\xq-rebalance\requirements.txt
```

如果电脑没有 `py`，把第二行改成：

```powershell
python -m pip install -r $env:USERPROFILE\.codex\skills\xq-rebalance\requirements.txt
```

然后重启 Codex。

## 方式 C：macOS 手动安装

打开 Terminal，运行：

```bash
git clone https://github.com/aikeywei/xq-rebalance.git ~/.codex/skills/xq-rebalance
python3 -m pip install -r ~/.codex/skills/xq-rebalance/requirements.txt
```

然后重启 Codex。

## 怎么确认安装成功

重启 Codex 后，说：

```text
使用 xq-rebalance，告诉我下一步怎么配置雪球组合。
```

如果 Codex 能识别 `xq-rebalance` 并开始讲登录雪球、复制表头、设置组合代码，说明安装成功。

## 安装后还要做什么

安装只解决“Codex 认识这个 Skill”。真正调仓前，还需要完成三件事：

1. 在电脑浏览器登录雪球。
2. 在组合页面找到组合名称旁边或地址栏 `/P/ZH...` 里的组合代码。
3. 按教程复制 `xueqiu.com` 请求表头并保存到本机。

之后再进入 dry-run 和执行调仓流程。

## 常见误解

### 登录雪球后是不是直接 npx 安装

不是。`npx` 是 Node/npm 生态的执行方式，Codex Skill 不走这个流程。

### 这个是不是一个智能体

它不是独立智能体，而是给 Codex 用的一套本地技能说明和脚本。Codex 读到 `SKILL.md` 后，会按里面的流程帮你操作。

### 能不能下载安装到项目目录

可以下载到项目目录做开发，但 Codex 要自动识别，最终应该放在：

```text
~/.codex/skills/xq-rebalance
```

Windows 对应：

```text
C:\Users\<你的用户名>\.codex\skills\xq-rebalance
```
