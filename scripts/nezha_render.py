#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
哪吒探针 · 暗黑卡片渲染（cow 版 v2，三合一）
用法:
  python3 nezha_render.py status                 # 总览卡片 -> nezha_status.png
  python3 nezha_render.py detail <ID>            # 单台详情卡片 -> nezha_detail_<ID>.png
  python3 nezha_render.py service                # 服务监控卡片 -> nezha_service.png
  python3 nezha_render.py --out <file> status    # 指定输出文件
读取同目录 .env 配置（NEZHA_URL / NEZHA_TOKEN）
"""

import os
import sys
import json
import urllib.request
import datetime
from datetime import timezone

BASE_URL = os.environ.get("NEZHA_URL", "http://103.236.70.18:8008").rstrip("/")
TOKEN = os.environ.get("NEZHA_TOKEN", "")

ONLINE_THRESHOLD_SECONDS = 300  # 超过5分钟无上报视为离线（state 是缓存，不可用于在线判断）


def is_server_online(s):
    """用 last_active（真实上报时间）判断在线，state 缓存不可靠"""
    la = s.get("last_active", "")
    if not la or la.startswith("0001"):  # 空/初始值 = 从未上报
        return False
    try:
        t = datetime.datetime.fromisoformat(la.replace("Z", "+00:00"))
        if t.tzinfo is None:
            t = t.replace(tzinfo=timezone.utc)
        return (datetime.datetime.now(timezone.utc) - t).total_seconds() < ONLINE_THRESHOLD_SECONDS
    except Exception:
        return False

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

def api(path):
    req = urllib.request.Request(f"{BASE_URL}{path}")
    req.add_header("Authorization", f"Bearer {TOKEN}")
    req.add_header("Accept", "application/json")
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode("utf-8"))

def get_servers():
    data = api("/api/v1/server")
    return data.get("data", data) if isinstance(data, dict) else data

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
        return f"{d}天 {h}小时"
    if h > 0:
        return f"{h}小时 {m}分"
    return f"{m}分钟"

FLAGS = {
    "hk": "🇭🇰", "us": "🇺🇸", "cn": "🇨🇳", "jp": "🇯🇵", "sg": "🇸🇬",
    "de": "🇩🇪", "gb": "🇬🇧", "fr": "🇫🇷", "kr": "🇰🇷", "tw": "🇹🇼",
    "ru": "🇷🇺", "ca": "🇨🇦", "au": "🇦🇺", "nl": "🇳🇱", "fi": "🇫🇮",
}
PLATFORM_ICONS = {
    "ubuntu": "🐧", "debian": "🐧", "centos": "🐧", "fedora": "🐧",
    "windows": "🪟", "darwin": "🍎", "alpine": "🐧", "arch": "🐧",
}

def bar_color(pct):
    if pct < 60: return "#27c93f"
    if pct < 85: return "#ffbd2e"
    return "#ff5f57"

CSS = """
  * { margin:0; padding:0; box-sizing:border-box; }
  body { background:#111214; font-family:'Noto Sans CJK SC','Noto Sans',sans-serif; padding:20px; color:#e8eaed; }
  .card { background:#1a1d21; border-radius:14px; padding:20px 22px; max-width:780px; margin:0 auto; box-shadow:0 4px 24px rgba(0,0,0,.5); }
  .header { display:flex; align-items:center; justify-content:space-between; margin-bottom:14px; }
  .logo { display:flex; align-items:center; gap:10px; font-size:18px; font-weight:700; }
  .logo-badge { width:30px; height:30px; border-radius:8px; background:linear-gradient(135deg,#2b7fff,#1f5fd6); display:flex; align-items:center; justify-content:center; font-size:16px; }
  .time { font-size:11px; color:#8a919c; }
  .stats { display:flex; gap:10px; margin-bottom:16px; }
  .stat { display:flex; align-items:center; gap:6px; background:#23262b; border-radius:20px; padding:5px 14px; font-size:13px; }
  .stat .dot { width:8px; height:8px; border-radius:50%; display:inline-block; }
  .dot.blue { background:#2b7fff; } .dot.green { background:#27c93f; } .dot.red { background:#ff5f57; }
  .stat b { font-weight:700; }
  .row { display:flex; align-items:center; gap:14px; background:#23262b; border-radius:12px; padding:14px 16px; margin-bottom:10px; }
  .row:last-child { margin-bottom:0; }
  .flag { font-size:24px; line-height:1; }
  .info { flex:0 0 170px; }
  .name { font-size:14px; font-weight:600; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
  .sub { font-size:11px; color:#8a919c; margin-top:3px; }
  .metrics { flex:1; display:flex; gap:16px; }
  .metric { flex:1; }
  .m-label { font-size:10px; color:#8a919c; margin-bottom:4px; }
  .m-bar { height:5px; background:#33363d; border-radius:3px; overflow:hidden; margin-bottom:4px; }
  .m-fill { height:100%; border-radius:3px; }
  .m-val { font-size:12px; font-weight:600; font-variant-numeric:tabular-nums; }
  .status { display:flex; align-items:center; gap:5px; border-radius:20px; padding:4px 10px; font-size:12px; flex:0 0 auto; }
  .status .dot { width:7px; height:7px; border-radius:50%; display:inline-block; }
  .status.online { background:rgba(39,201,63,.12); color:#27c93f; }
  .status.offline { background:rgba(255,95,87,.12); color:#ff5f57; }
  .footer { display:flex; align-items:center; justify-content:flex-end; gap:6px; margin-top:14px; font-size:11px; color:#8a919c; }
  /* detail 卡片样式 */
  .dt-hero { display:flex; align-items:center; gap:14px; background:#23262b; border-radius:12px; padding:18px; margin-bottom:12px; }
  .dt-flag { font-size:38px; line-height:1; }
  .dt-title { font-size:19px; font-weight:700; }
  .dt-sub { font-size:12px; color:#8a919c; margin-top:4px; }
  .dt-status { margin-left:auto; }
  .dt-grid { display:grid; grid-template-columns:1fr 1fr; gap:10px; margin-bottom:12px; }
  .dt-item { background:#23262b; border-radius:12px; padding:14px 16px; }
  .dt-item.full { grid-column:1/-1; }
  .dt-label { font-size:11px; color:#8a919c; margin-bottom:6px; }
  .dt-val { font-size:17px; font-weight:700; font-variant-numeric:tabular-nums; }
  .dt-val small { font-size:12px; color:#8a919c; font-weight:400; }
  .dt-bar { height:6px; background:#33363d; border-radius:3px; overflow:hidden; margin-top:8px; }
  .dt-fill { height:100%; border-radius:3px; }
  .dt-mini { display:flex; justify-content:space-between; font-size:11px; color:#8a919c; margin-top:5px; }
"""

def build_status_html(servers):
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    total = len(servers)
    online = sum(1 for s in servers if is_server_online(s))
    offline = total - online

    rows = []
    for s in servers:
        st = s.get("state", {}) or {}
        h = s.get("host", {}) or {}
        g = s.get("geoip", {}) or {}
        name = s.get("name", "?")
        cc = (g.get("country_code") or "?").lower()
        flag = FLAGS.get(cc, "🌐")
        platform = (h.get("platform") or "").lower()
        icon = PLATFORM_ICONS.get(platform, "🖥️")
        mem_total = h.get("mem_total") or 0
        disk_total = h.get("disk_total") or 0
        mem_used = st.get("mem_used") or 0
        disk_used = st.get("disk_used") or 0
        cpu = st.get("cpu", 0) or 0
        mem_pct = (mem_used / mem_total * 100) if mem_total else 0
        disk_pct = (disk_used / disk_total * 100) if disk_total else 0
        is_online = is_server_online(s)
        status_html = ('<span class="status online"><span class="dot green"></span>在线</span>'
                       if is_online else
                       '<span class="status offline"><span class="dot red"></span>离线</span>')
        c1, c2, c3 = bar_color(cpu), bar_color(mem_pct), bar_color(disk_pct)
        rows.append(f"""
        <div class="row">
          <div class="flag">{flag}</div>
          <div class="info">
            <div class="name">{name}</div>
            <div class="sub">{icon} {platform or 'unknown'}</div>
          </div>
          <div class="metrics">
            <div class="metric">
              <div class="m-label">CPU</div>
              <div class="m-bar"><div class="m-fill" style="width:{cpu:.1f}%;background:{c1}"></div></div>
              <div class="m-val" style="color:{c1}">{cpu:.1f}%</div>
            </div>
            <div class="metric">
              <div class="m-label">内存</div>
              <div class="m-bar"><div class="m-fill" style="width:{mem_pct:.1f}%;background:{c2}"></div></div>
              <div class="m-val" style="color:{c2}">{mem_pct:.1f}%</div>
            </div>
            <div class="metric">
              <div class="m-label">磁盘</div>
              <div class="m-bar"><div class="m-fill" style="width:{disk_pct:.1f}%;background:{c3}"></div></div>
              <div class="m-val" style="color:{c3}">{disk_pct:.1f}%</div>
            </div>
          </div>
          {status_html}
        </div>""")

    return f"""<!DOCTYPE html>
<html lang="zh"><head><meta charset="UTF-8"><style>{CSS}</style></head>
<body><div class="card">
  <div class="header">
    <div class="logo"><div class="logo-badge">🛡️</div><span>哪吒监控</span></div>
    <div class="time">{now}</div>
  </div>
  <div class="stats">
    <span class="stat"><span class="dot blue"></span>总计 <b>{total}</b></span>
    <span class="stat"><span class="dot green"></span>在线 <b>{online}</b></span>
    <span class="stat"><span class="dot red"></span>离线 <b>{offline}</b></span>
  </div>
  {''.join(rows)}
  <div class="footer">⚡ 哪吒探针 · 数据实时刷新</div>
</div></body></html>"""

def build_detail_html(s):
    st = s.get("state", {}) or {}
    h = s.get("host", {}) or {}
    g = s.get("geoip", {}) or {}
    name = s.get("name", "?")
    cc = (g.get("country_code") or "?").lower()
    flag = FLAGS.get(cc, "🌐")
    platform = h.get("platform", "?")
    plat_ver = h.get("platform_version", "")
    arch = h.get("arch", "?")
    virt = h.get("virtualization", "?")
    cpu_model = (h.get("cpu") or ["?"])
    cpu_model = cpu_model[0] if isinstance(cpu_model, list) else cpu_model
    ip = (g.get("ip", {}) or {}).get("ipv4_addr", "?")
    agent_ver = h.get("version", "?")

    mem_total = h.get("mem_total") or 0
    disk_total = h.get("disk_total") or 0
    swap_total = h.get("swap_total") or 0
    mem_used = st.get("mem_used") or 0
    disk_used = st.get("disk_used") or 0
    swap_used = st.get("swap_used") or 0
    cpu = st.get("cpu", 0) or 0
    mem_pct = (mem_used / mem_total * 100) if mem_total else 0
    disk_pct = (disk_used / disk_total * 100) if disk_total else 0
    swap_pct = (swap_used / swap_total * 100) if swap_total else 0

    is_online = is_server_online(s)
    status_html = ('<span class="status online"><span class="dot green"></span>在线</span>'
                   if is_online else
                   '<span class="status offline"><span class="dot red"></span>离线</span>')

    c1, c2, c3 = bar_color(cpu), bar_color(mem_pct), bar_color(disk_pct)
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def bar(pct, color):
        return f'<div class="dt-bar"><div class="dt-fill" style="width:{pct:.1f}%;background:{color}"></div></div>'

    return f"""<!DOCTYPE html>
<html lang="zh"><head><meta charset="UTF-8"><style>{CSS}</style></head>
<body><div class="card">
  <div class="header">
    <div class="logo"><div class="logo-badge">🛡️</div><span>哪吒监控 · 服务器详情</span></div>
    <div class="time">{now}</div>
  </div>
  <div class="dt-hero">
    <div class="dt-flag">{flag}</div>
    <div>
      <div class="dt-title">{name}</div>
      <div class="dt-sub">{platform} {plat_ver} · {arch} · {virt}</div>
    </div>
    <div class="dt-status">{status_html}</div>
  </div>
  <div class="dt-grid">
    <div class="dt-item">
      <div class="dt-label">💻 CPU 使用率</div>
      <div class="dt-val" style="color:{c1}">{cpu:.1f}%</div>
      {bar(cpu, c1)}
      <div class="dt-mini"><span>{cpu_model[:38]}</span></div>
    </div>
    <div class="dt-item">
      <div class="dt-label">📊 内存</div>
      <div class="dt-val">{mem_pct:.1f}% <small>{fmt_bytes(mem_used)} / {fmt_bytes(mem_total)}</small></div>
      {bar(mem_pct, c2)}
      <div class="dt-mini"><span>Swap {fmt_bytes(swap_used)} / {fmt_bytes(swap_total)}</span></div>
    </div>
    <div class="dt-item">
      <div class="dt-label">💾 磁盘</div>
      <div class="dt-val">{disk_pct:.1f}% <small>{fmt_bytes(disk_used)} / {fmt_bytes(disk_total)}</small></div>
      {bar(disk_pct, c3)}
      <div class="dt-mini"><span>已用 {fmt_bytes(disk_used)}</span></div>
    </div>
    <div class="dt-item">
      <div class="dt-label">🌐 网络</div>
      <div class="dt-val">{fmt_bytes(st.get('net_in_speed', 0))}<small>/s 下载</small></div>
      <div class="dt-mini"><span>↓ 总 {fmt_bytes(st.get('net_in_transfer', 0))} · ↑ 总 {fmt_bytes(st.get('net_out_transfer', 0))}</span></div>
    </div>
    <div class="dt-item">
      <div class="dt-label">⚙️ 负载 & 进程</div>
      <div class="dt-val">{st.get('load_1', 0):.2f} <small>load</small></div>
      <div class="dt-mini"><span>进程 {st.get('process_count', 0)} · TCP {st.get('tcp_conn_count', 0)}</span></div>
    </div>
    <div class="dt-item">
      <div class="dt-label">⏱️ 运行时间</div>
      <div class="dt-val">{fmt_uptime(st.get('uptime', 0))}</div>
      <div class="dt-mini"><span>IP {ip} · Agent v{agent_ver}</span></div>
    </div>
  </div>
  <div class="footer">⚡ 哪吒探针 · ID {s.get('id')}</div>
</div></body></html>"""

def build_service_html(services):
    data = services.get("data", services) if isinstance(services, dict) else services
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if not data:
        rows = '<div class="row"><div class="info"><div class="name">暂无服务监控</div><div class="sub">在哪吒面板中添加 HTTP/TCP/Ping 监控后显示</div></div></div>'
    else:
        rows = ""
        for svc in data:
            name = svc.get("name", "?")
            typ = svc.get("type", "?")
            now_status = svc.get("current_down", False)
            status_html = ('<span class="status offline"><span class="dot red"></span>故障</span>'
                           if now_status else
                           '<span class="status online"><span class="dot green"></span>正常</span>')
            rows += f"""
            <div class="row">
              <div class="flag">🔗</div>
              <div class="info"><div class="name">{name}</div><div class="sub">类型 {typ}</div></div>
              {status_html}
            </div>"""
    return f"""<!DOCTYPE html>
<html lang="zh"><head><meta charset="UTF-8"><style>{CSS}</style></head>
<body><div class="card">
  <div class="header">
    <div class="logo"><div class="logo-badge">🛡️</div><span>哪吒监控 · 服务状态</span></div>
    <div class="time">{now}</div>
  </div>
  {rows}
  <div class="footer">⚡ 哪吒探针 · 服务监控</div>
</div></body></html>"""

def render(html, outfile):
    from playwright.sync_api import sync_playwright
    html_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "nezha_card.html")
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)
    with sync_playwright() as p:
        browser = p.chromium.launch(args=["--no-sandbox", "--disable-dev-shm-usage"])
        page = browser.new_page(viewport={"width": 820, "height": 1200}, device_scale_factor=2)
        page.goto(f"file://{html_path}")
        page.evaluate("document.fonts.ready")
        page.wait_for_timeout(300)
        card = page.locator(".card")
        card.screenshot(path=outfile)
        browser.close()
    print(f"✅ 已生成: {outfile}")

if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    outfile = "nezha_status.png"
    if "--out" in sys.argv:
        outfile = sys.argv[sys.argv.index("--out") + 1]

    cmd = args[0] if args else "status"
    servers = get_servers()
    if cmd == "status":
        render(build_status_html(servers), outfile if outfile != "nezha_status.png" else "nezha_status.png")
    elif cmd == "detail":
        sid = args[1] if len(args) > 1 else None
        if not sid:
            print("用法: python3 nezha_render.py detail <ID>")
            sys.exit(1)
        target = next((s for s in servers if str(s.get("id")) == sid), None)
        if not target:
            print(f"❌ 找不到 ID={sid}，可用: {[s.get('id') for s in servers]}")
            sys.exit(1)
        render(build_detail_html(target), outfile if outfile != "nezha_status.png" else f"nezha_detail_{sid}.png")
    elif cmd == "service":
        services = api("/api/v1/service")
        render(build_service_html(services), outfile if outfile != "nezha_status.png" else "nezha_service.png")
    else:
        print(f"未知命令: {cmd}")
        sys.exit(1)
