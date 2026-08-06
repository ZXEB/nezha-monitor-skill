# 🛰️ Nezha Monitor — 哪吒探针监控技能包（Cow）

> 把哪吒探针面板变成一张张精美的状态卡：服务器总览、单台详情、服务监控、历史趋势，说句话就出图。

适用于 **CowAgent**（`~/cow`）工作空间。灵感来自 astrbot 哪吒插件，但无需换平台——装好技能，你的 cow 就是你的探针助手。

---

## ✨ 功能特性

| 能力 | 效果 |
|------|------|
| 📊 **服务器总览** | 全部服务器 CPU / 内存 / 磁盘 / 在线状态，暗黑科技风总览卡 |
| 📋 **单台详情** | CPU 型号 / 内存 / 磁盘 / 网络 / 负载 / 运行时间 |
| 🛡️ **服务监控** | HTTP / TCP 服务监控项状态 |
| 📈 **历史趋势** | CPU / 内存 / 网络 / 负载等 14 种指标，支持 1d / 7d / 30d 趋势图 |

---

## 🚀 安装

### 1. 安装技能

把本仓库的 `nezha-monitor/` 目录（或 `.skill` 包）放到你的技能目录：

```bash
# 方法一：直接 clone 到技能目录
git clone https://github.com/ZXEB/nezha-monitor-skill.git ~/cow/skills/nezha-monitor

# 方法二：拿到 .skill 包后解压
mkdir -p ~/cow/skills/nezha-monitor
unzip nezha-monitor.skill -d ~/cow/skills/
```

### 2. 安装运行依赖（一次性）

```bash
# Python 依赖
pip3 install matplotlib playwright

# 中文字体 + emoji（卡片渲染必需）
sudo apt-get install -y fonts-noto-cjk fonts-noto-color-emoji

# 浏览器内核（卡片截图用）
python3 -m playwright install chromium --with-deps
```

### 3. 配置你的哪吒面板（关键！）

在技能目录创建 `.env` 文件，填入你自己的面板信息：

```bash
cd ~/cow/skills/nezha-monitor
echo "NEZHA_URL=http://你的面板地址:端口" > .env
echo "NEZHA_TOKEN=你的API令牌" >> .env
```

| 配置项 | 说明 |
|--------|------|
| `NEZHA_URL` | 哪吒面板访问地址，如 `http://1.2.3.4:8008` |
| `NEZHA_TOKEN` | 面板后台「设置 → API Token」生成，`Authorization: Bearer <TOKEN>` 认证 |

> ⚠️ `.env` 含敏感凭证：**已被 .gitignore 排除**，不要提交到任何公开仓库，也不要发给别人。

### 4. 重启 cow，完成 🎉

重启后对你的 cow 说一句「**看看服务器**」，它就会自动调用本技能给你出图。

---

## 💬 使用方式（触发词）

| 你说 | cow 执行 |
|------|---------|
| 服务器状态 / 看看服务器 / 探针 / 哪吒 | 生成服务器状态总览图 |
| 服务器详情 5 / 详情 5 | 生成 5 号服务器详情卡（ID 换成你的） |
| 服务监控 / 服务状态 | 生成服务监控图 |
| 历史 5 cpu / 趋势 5 memory 7d | 生成 5 号服务器 CPU 一天 / 内存七天趋势图 |

手动运行脚本也可以：

```bash
# 总览 / 详情 / 服务 / 历史
python3 scripts/nezha_render.py status
python3 scripts/nezha_render.py detail 5
python3 scripts/nezha_render.py service
python3 scripts/nezha_history.py 5 cpu 7d
```

---

## 🛠️ 常见问题

| 问题 | 解决 |
|------|------|
| 图片中文乱码 / 方块 | 没装中文字体：`sudo apt-get install -y fonts-noto-cjk` |
| 截图空白 | 没装浏览器内核：`python3 -m playwright install chromium --with-deps` |
| 401 认证失败 | 检查 `.env` 的 `NEZHA_TOKEN` 是否正确、是否有面板权限 |
| 历史趋势提示"无数据" | TSDB 刚启用，数据积累中，等一段时间再试 |

## 📁 项目结构

```
nezha-monitor/
├── SKILL.md               # 技能说明（cow 读取）
├── scripts/
│   ├── nezha.py           # 文本版查询（调试/轻量）
│   ├── nezha_render.py    # 卡片渲染主脚本（status/detail/service）
│   └── nezha_history.py   # 历史趋势图（需面板开启 TSDB）
```

## ⚖️ 说明

- 本项目是个人自用工具的开源分享，与哪吒探针官方无关
- 面板地址与 Token 请务必妥善保管，泄露 = 你的服务器裸奔
