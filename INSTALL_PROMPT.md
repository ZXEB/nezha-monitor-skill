# 🤖 AI 一键安装指引（给任何 AI agent 看）

> 你（AI agent）的任务：在目标服务器上安装 **nezha-monitor** 技能（CowAgent 的哪吒探针监控技能）。
> 你拥有终端操作能力，请自主完成以下全部步骤。遇到不确定的情况，先自己排查，实在不行再问用户。

## 目标环境

- 服务器已部署 **CowAgent**，工作空间在 `~/cow/`
- 技能安装目录：`~/cow/skills/nezha-monitor/`
- 安装完成后，用户对 cow 说「看看服务器」即可触发技能

## 执行步骤

### 1. 了解技能
先访问 https://github.com/ZXEB/nezha-monitor-skill 的 README.md，了解功能、结构与用法。

### 2. 下载技能到 cow 技能目录
```bash
git clone https://github.com/ZXEB/nezha-monitor-skill.git ~/cow/skills/nezha-monitor
```
如果 git 不可用，改用 curl 下载 ZIP 并解压：
```bash
curl -L -o /tmp/nezha.zip https://github.com/ZXEB/nezha-monitor-skill/archive/refs/heads/main.zip
mkdir -p ~/cow/skills/nezha-monitor
unzip /tmp/nezha.zip -d /tmp/ && cp -r /tmp/nezha-monitor-skill-main/* ~/cow/skills/nezha-monitor/
```

### 3. 安装依赖（按系统发行版选择）
```bash
# Python 依赖
pip3 install matplotlib playwright

# 中文字体 + emoji（卡片渲染必需，按发行版选一条）
sudo apt-get install -y fonts-noto-cjk fonts-noto-color-emoji        # Debian/Ubuntu
sudo yum install -y google-noto-sans-cjk-fonts                       # CentOS/RHEL
sudo apk add font-noto-cjk                                           # Alpine

# 浏览器内核（卡片截图用）
python3 -m playwright install chromium --with-deps
```
如果当前用户无 sudo 权限，尝试 `pip3 install --user` 并在报错时询问用户。

### 4. 获取凭证（必须问用户要，禁止编造/猜测）
向用户询问两项信息：
- **NEZHA_URL**：哪吒面板访问地址，如 `http://1.2.3.4:8008`
- **NEZHA_TOKEN**：面板后台「设置 → API Token」生成的令牌

### 5. 写入配置（权限收紧到 600）
```bash
cat > ~/cow/skills/nezha-monitor/.env <<'EOF'
NEZHA_URL=<用户提供的面板地址>
NEZHA_TOKEN=<用户提供的API令牌>
EOF
chmod 600 ~/cow/skills/nezha-monitor/.env
```

### 6. 验证安装（必须实际跑通）
```bash
cd ~/cow/skills/nezha-monitor && python3 scripts/nezha_render.py status
```
- ✅ 成功：生成 `nezha_status.png` 且无报错 → 继续第 7 步
- ❌ 失败：按下方「排错提示」处理，处理完重新验证

### 7. 收尾汇报
告诉用户：
- 技能已安装完成 ✅，可用触发词：**「服务器状态 / 看看服务器 / 探针 / 哪吒」**
- 其他能力：`详情 <ID>` 单台详情、`服务监控`、`历史 <ID> <指标>` 趋势图
- **重启 cow 主进程**让技能生效
- ⚠️ `.env` 含面板凭证，绝不可提交到 git、不可外泄

## 排错提示

| 现象 | 原因 | 处理 |
|------|------|------|
| 401 认证失败 | API Token 错误或无权限 | 让用户检查 token，面板后台重新生成 |
| 图片中文乱码/方块 | 缺中文字体 | 补装 fonts-noto-cjk |
| 截图空白 | 缺 chromium 内核 | `python3 -m playwright install chromium --with-deps` |
| 历史趋势提示无数据 | 面板 TSDB 未启用/刚启用 | 告诉用户等数据积累后再试 |
| 找不到 `~/cow` | 工作空间路径不同 | 用 `find / -maxdepth 3 -name skills -type d 2>/dev/null` 定位后询问用户确认 |

## 安全红线

- ❌ 绝不把 `.env`、NEZHA_TOKEN 写进任何仓库、日志、聊天记录之外的地方
- ❌ 不向用户索要不必要的权限（不需要 root 就别用 sudo）
- ✅ 安装过程如遇重大意外（磁盘满、依赖冲突），停下并如实汇报，不要硬来
