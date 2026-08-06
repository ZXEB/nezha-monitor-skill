---
name: nezha-monitor
description: "哪吒探针（Nezha Monitor）服务器监控查询。生成服务器状态总览图、单台详情卡、服务监控图、历史趋势图。Use when the user asks about 服务器状态、看看服务器、探针、哪吒、服务器详情、服务监控、服务器历史趋势、server status、nezha monitor. Triggers: (1) 服务器状态/看看服务器/探针/哪吒 → status overview image, (2) 服务器详情加服务器ID/详情 → single server detail, (3) 服务监控/服务状态 → service monitoring, (4) 历史/趋势加服务器ID加指标 → historical trend chart."
metadata:
  requires:
    bins: ["python3"]
---

# 哪吒探针监控（Nezha Monitor）

查询哪吒探针面板，把服务器实时状态渲染成图片发给用户。全部通过本技能的 `scripts/` 脚本完成，无需额外平台。

## Setup（首次使用必做）

### 1. 安装依赖（一次性）

```bash
# Python 依赖
pip3 install matplotlib playwright

# 中文字体 + emoji（卡片渲染必需）
apt-get install -y fonts-noto-cjk fonts-noto-color-emoji

# 浏览器内核（卡片截图用）
python3 -m playwright install chromium --with-deps
```

### 2. 配置哪吒面板

在**技能同目录**（`<base_dir>/`）创建 `.env` 文件：

```bash
NEZHA_URL=http://你的面板地址:端口
NEZHA_TOKEN=你的API令牌
```

- 面板地址：哪吒面板的访问地址，如 `http://1.2.3.4:8008`
- API 令牌：在面板后台「设置 → API Token」生成，`Authorization: Bearer <TOKEN>` 认证
- ⚠️ `.env` 含敏感凭证，不要提交到公开仓库、不要写入记忆

## Usage

脚本位于本技能 base_dir（见技能列表）下的 `scripts/`。

### 📊 服务器总览（status）

```bash
python3 "<base_dir>/scripts/nezha_render.py" status
```

生成 `nezha_status.png`（暗黑科技风总览卡：全部服务器 CPU/内存/磁盘/在线状态）→ 用 send 工具发给用户。

### 📋 单台详情（detail）

```bash
python3 "<base_dir>/scripts/nezha_render.py" detail <ID>
```

生成 `nezha_detail_<ID>.png`（CPU 型号/内存/磁盘/网络/负载/运行时间）。

### 🛡️ 服务监控（service）

```bash
python3 "<base_dir>/scripts/nezha_render.py" service
```

生成 `nezha_service.png`（HTTP/TCP 服务监控项；无监控项时显示空状态）。

### 📈 历史趋势（history，需面板开启 TSDB）

```bash
python3 "<base_dir>/scripts/nezha_history.py" <server_id> [metric] [period]
```

- `metric`: cpu | memory | disk | net_in_speed | net_out_speed | load1 | tcp_conn | process_count | uptime 等（默认 cpu）
- `period`: 1d | 7d | 30d（默认 1d）
- 生成 `nezha_history_<ID>_<metric>.png`
- 若提示"无历史数据"：TSDB 刚启用，数据积累中，稍后再试

### 纯文本查询（调试/轻量）

```bash
python3 "<base_dir>/scripts/nezha.py" status    # 文本版总览
python3 "<base_dir>/scripts/nezha.py" detail <ID>
python3 "<base_dir>/scripts/nezha.py" service
python3 "<base_dir>/scripts/nezha.py" raw       # 原始 JSON
```

## 常见问题

- **中文乱码/方块**：未装中文字体，执行 `apt-get install -y fonts-noto-cjk`
- **截图空白**：playwright chromium 未安装，执行 `python3 -m playwright install chromium --with-deps`
- **401 认证失败**：检查 `.env` 的 `NEZHA_TOKEN` 是否正确、是否有权限
- **卡片样式**：`nezha_render.py` 用 playwright 截图 HTML 模板，模板自动生成在脚本同目录，可自行调整配色

## 技术要点

- 哪吒 API 实时数据在 `state` 字段，硬件总量在 `host` 字段，地区在 `geoip`
- 历史数据接口：`/api/v1/server/<ID>/metrics?metric=<m>&period=<p>`
- 中文渲染：matplotlib 需加载 Noto CJK 字体（Droid Sans Fallback 与 matplotlib 3.11 不兼容）
