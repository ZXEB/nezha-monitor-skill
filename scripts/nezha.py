#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
哪吒探针查询脚本（cow 版 v2）
用法:
  python3 nezha.py status              # 服务器状态概览图
  python3 nezha.py detail <ID>         # 单台服务器详情（文本）
  python3 nezha.py service             # 服务监控列表（文本）
  python3 nezha.py raw                 # 原始 JSON（调试用）
配置:
  同目录 .env 文件: NEZHA_URL=... / NEZHA_TOKEN=...
输出:
  status 生成 nezha_status.png
"""

import os
import sys
import json
import urllib.request
import urllib.error

# ---------- 配置 ----------
BASE_URL = os.environ.get("NEZHA_URL", "http://103.236.70.18:8008").rstrip("/")
TOKEN = os.environ.get("NEZHA_TOKEN", "")

_env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
if os.path.exists(_env_path):
    with open(_env_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                k, v = k.strip(), v.strip()
                if k == "NEZHA_URL":
                    BASE_URL = v.rstrip("/")
                elif k == "NEZHA_TOKEN":
                    TOKEN = v

# ---------- API 封装 ----------
def api(path, method="GET"):
    if not TOKEN:
        print("❌ 未配置 API Token，请在 .env 中设置 NEZHA_TOKEN")
        sys.exit(1)
    url = f"{BASE_URL}{path}"
    req = urllib.request.Request(url, method=method)
    req.add_header("Authorization", f"Bearer {TOKEN}")
    req.add_header("Accept", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="ignore")
        print(f"❌ API 错误 {e.code}: {body[:300]}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 请求失败: {e}")
        sys.exit(1)

def get_servers():
    data = api("/api/v1/server")
    return data.get("data", data) if isinstance(data, dict) else data

# ---------- 工具函数 ----------
def fmt_bytes(b):
    if b is None:
        return "N/A"
    b = float(b)
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if b < 1024 or unit == "TB":
            return f"{b:.1f}{unit}" if unit != "B" else f"{int(b)}B"
        b /= 1024

def fmt_uptime(sec):
    sec = int(sec or 0)
    d, rem = divmod(sec, 86400)
    h, rem = divmod(rem, 3600)
    m = rem // 60
    if d > 0:
        return f"{d}天{h}小时"
    if h > 0:
        return f"{h}小时{m}分"
    return f"{m}分钟"

def server_metrics(s):
    """从服务器对象提取关键指标"""
    st = s.get("state", {}) or {}
    h = s.get("host", {}) or {}
    mem_total = h.get("mem_total") or 0
    disk_total = h.get("disk_total") or 0
    mem_used = st.get("mem_used") or 0
    disk_used = st.get("disk_used") or 0
    return {
        "id": s.get("id"),
        "name": s.get("name", "?"),
        "cpu": st.get("cpu", 0),
        "mem_pct": (mem_used / mem_total * 100) if mem_total else 0,
        "mem_used": mem_used,
        "mem_total": mem_total,
        "disk_pct": (disk_used / disk_total * 100) if disk_total else 0,
        "disk_used": disk_used,
        "disk_total": disk_total,
        "uptime": st.get("uptime", 0),
        "load": st.get("load_1", 0),
        "net_in": st.get("net_in_transfer", 0),
        "net_out": st.get("net_out_transfer", 0),
        "platform": h.get("platform", "?"),
        "ip": (s.get("geoip", {}) or {}).get("ip", {}).get("ipv4_addr", "?"),
        "last_active": s.get("last_active", ""),
        "cpu_model": (h.get("cpu") or ["?"])[0] if isinstance(h.get("cpu"), list) else h.get("cpu", "?"),
    }

# ---------- 画图 ----------
def plot_status(servers, outfile="nezha_status.png"):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib import font_manager
    import numpy as np

    # 中文字体
    zh_fonts = [
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf",
    ]
    for fp in zh_fonts:
        if os.path.exists(fp):
            font_manager.fontManager.addfont(fp)
            name = font_manager.FontProperties(fname=fp).get_name()
            plt.rcParams["font.family"] = name
            break
    plt.rcParams["axes.unicode_minus"] = False

    metrics = [server_metrics(s) for s in servers]
    names = [m["name"][:12] for m in metrics]
    cpus = [m["cpu"] for m in metrics]
    mems = [m["mem_pct"] for m in metrics]
    disks = [m["disk_pct"] for m in metrics]

    x = np.arange(len(names))
    width = 0.25
    fig, ax = plt.subplots(figsize=(11, 6), dpi=130)
    b1 = ax.bar(x - width, cpus, width, label="CPU", color="#e74c3c")
    b2 = ax.bar(x, mems, width, label="内存", color="#f39c12")
    b3 = ax.bar(x + width, disks, width, label="磁盘", color="#27ae60")

    ax.set_ylabel("使用率 (%)")
    ax.set_title("哪吒探针 · 服务器状态概览", fontsize=15, pad=12)
    ax.set_xticks(x)
    ax.set_xticklabels(names, rotation=20, ha="right", fontsize=9)
    ax.legend(loc="upper right")
    ax.set_ylim(0, 105)
    ax.grid(axis="y", alpha=0.3)

    for bars in (b1, b2, b3):
        for bar in bars:
            h = bar.get_height()
            ax.annotate(f"{h:.0f}%", xy=(bar.get_x() + bar.get_width() / 2, h),
                        xytext=(0, 2), textcoords="offset points", ha="center", fontsize=7)

    plt.tight_layout()
    plt.savefig(outfile, bbox_inches="tight")
    plt.close()
    return outfile

# ---------- 文本输出 ----------
def print_detail(s):
    m = server_metrics(s)
    print(f"📡 {m['name']} (ID={m['id']})")
    print(f"   IP: {m['ip']} | 系统: {m['platform']}")
    print(f"   CPU: {m['cpu']:.1f}% | 型号: {m['cpu_model'][:40]}")
    print(f"   内存: {fmt_bytes(m['mem_used'])} / {fmt_bytes(m['mem_total'])} ({m['mem_pct']:.1f}%)")
    print(f"   磁盘: {fmt_bytes(m['disk_used'])} / {fmt_bytes(m['disk_total'])} ({m['disk_pct']:.1f}%)")
    print(f"   负载: {m['load']:.2f} | 运行: {fmt_uptime(m['uptime'])}")
    print(f"   流量: ↑{fmt_bytes(m['net_in'])} ↓{fmt_bytes(m['net_out'])}")

def print_service_list(services):
    data = services.get("data", services) if isinstance(services, dict) else services
    if not data:
        print("暂无服务监控")
        return
    print(f"{'ID':<5}{'名称':<20}{'类型':<10}{'状态'}")
    print("-" * 50)
    for svc in data:
        sid = svc.get("id", "?")
        name = svc.get("name", "?")
        typ = svc.get("type", "?")
        now = svc.get("current_down", False)
        status = "🟢" if now else "🔴"
        print(f"{sid:<5}{str(name)[:18]:<20}{typ:<10}{status}")

# ---------- 主入口 ----------
def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    cmd = sys.argv[1]
    if cmd == "status":
        servers = get_servers()
        out = plot_status(servers)
        print(f"✅ 已生成概览图: {out} (共 {len(servers)} 台服务器)")
    elif cmd == "detail":
        if len(sys.argv) < 3:
            print("用法: python3 nezha.py detail <ID>")
            sys.exit(1)
        sid = sys.argv[2]
        servers = get_servers()
        target = next((s for s in servers if str(s.get("id")) == sid), None)
        if not target:
            print(f"❌ 找不到 ID={sid} 的服务器，可用: {[s.get('id') for s in servers]}")
            sys.exit(1)
        print_detail(target)
    elif cmd == "service":
        services = api("/api/v1/service")
        print_service_list(services)
    elif cmd == "raw":
        print(json.dumps(get_servers(), ensure_ascii=False, indent=2)[:3000])
    else:
        print(f"未知命令: {cmd}")
        print(__doc__)
        sys.exit(1)

if __name__ == "__main__":
    main()
