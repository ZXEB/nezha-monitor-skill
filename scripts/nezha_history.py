#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
哪吒探针 · 历史趋势图（依赖 TSDB，2026-08-06 已启用）
用法:
  python3 nezha_history.py <server_id> [metric] [period]
  metric: cpu | memory | disk | net_in_speed | net_out_speed | load1 | tcp_conn | process_count | uptime
  period: 1d | 7d | 30d   (默认 1d)
示例:
  python3 nezha_history.py 5 cpu 1d      # 香港2-2 CPU 一天趋势
  python3 nezha_history.py 5 memory 7d    # 内存 7 天
  python3 nezha_history.py 5 net_in_speed 1d
读取同目录 .env 配置（NEZHA_URL / NEZHA_TOKEN）
输出: nezha_history_<server_id>_<metric>.png
"""

import os
import sys
import json
import urllib.request
import datetime

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

METRIC_LABELS = {
    "cpu": ("CPU 使用率", "%"),
    "memory": ("内存使用量", ""),
    "disk": ("磁盘使用量", ""),
    "net_in_speed": ("下行速度", ""),
    "net_out_speed": ("上行速度", ""),
    "net_in_transfer": ("下行总流量", ""),
    "net_out_transfer": ("上行总流量", ""),
    "load1": ("负载 Load1", ""),
    "tcp_conn": ("TCP 连接数", "个"),
    "process_count": ("进程数", "个"),
    "uptime": ("运行时间", "秒"),
    "temperature": ("温度", "°C"),
    "gpu": ("GPU", ""),
    "swap": ("Swap", ""),
}

def api(path):
    req = urllib.request.Request(f"{BASE_URL}{path}")
    req.add_header("Authorization", f"Bearer {TOKEN}")
    req.add_header("Accept", "application/json")
    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.loads(resp.read().decode("utf-8"))

def get_servers():
    data = api("/api/v1/server")
    return data.get("data", data) if isinstance(data, dict) else data

def fmt_bytes(b):
    if b is None: return "N/A"
    b = float(b)
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if b < 1024 or unit == "TB":
            return f"{b:.1f}{unit}" if unit != "B" else f"{int(b)}B"
        b /= 1024

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    server_id = sys.argv[1]
    metric = sys.argv[2] if len(sys.argv) > 2 else "cpu"
    period = sys.argv[3] if len(sys.argv) > 3 else "1d"
    if metric not in METRIC_LABELS:
        print(f"❌ 未知指标: {metric}，可用: {', '.join(METRIC_LABELS.keys())}")
        sys.exit(1)

    # 服务器名称
    servers = get_servers()
    sname = next((s.get("name") for s in servers if str(s.get("id")) == server_id), f"服务器{server_id}")

    # 拉历史数据
    data = api(f"/api/v1/server/{server_id}/metrics?metric={metric}&period={period}")
    pts = data.get("data", {}).get("data_points", [])
    if not pts:
        print(f"⚠️ 无历史数据（TSDB 刚启用，数据积累中）。请稍后再试。")
        sys.exit(1)

    ts = [p["ts"] / 1000 for p in pts]
    vals = [p["value"] for p in pts]

    # 转成 datetime（东八区）
    from datetime import datetime, timezone, timedelta
    tz = timezone(timedelta(hours=8))
    dt = [datetime.fromtimestamp(t, tz=tz) for t in ts]

    # 画图
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib import font_manager

    for fp in ["/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
               "/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf"]:
        if os.path.exists(fp):
            font_manager.fontManager.addfont(fp)
            plt.rcParams["font.family"] = font_manager.FontProperties(fname=fp).get_name()
            break
    plt.rcParams["axes.unicode_minus"] = False

    label, unit = METRIC_LABELS[metric]
    fig, ax = plt.subplots(figsize=(12, 5), dpi=130)
    ax.plot(dt, vals, color="#2b7fff", linewidth=1.2)
    ax.fill_between(dt, vals, alpha=0.15, color="#2b7fff")
    ax.set_title(f"📈 {sname} · {label} 趋势（{period}）", fontsize=14, pad=10)
    ax.set_ylabel(f"{label} ({unit})" if unit else label)
    ax.grid(alpha=0.3)

    # 时间轴格式化
    import matplotlib.dates as mdates
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%m-%d %H:%M", tz=tz))
    fig.autofmt_xdate()

    # 标注最大最小值
    if len(vals) > 2:
        imax = vals.index(max(vals))
        imin = vals.index(min(vals))
        ax.annotate(f"峰值 {max(vals):.1f}", xy=(dt[imax], vals[imax]),
                    xytext=(0, 10), textcoords="offset points",
                    color="#e74c3c", fontsize=9, ha="center")
        ax.annotate(f"最低 {min(vals):.1f}", xy=(dt[imin], vals[imin]),
                    xytext=(0, -16), textcoords="offset points",
                    color="#27ae60", fontsize=9, ha="center")

    plt.tight_layout()
    outfile = f"nezha_history_{server_id}_{metric}.png"
    plt.savefig(outfile, bbox_inches="tight")
    plt.close()
    print(f"✅ 已生成趋势图: {outfile}（{len(pts)} 个数据点）")

if __name__ == "__main__":
    main()
