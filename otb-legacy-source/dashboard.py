"""Local web dashboard for the Olympian trading bot.

Run with: python otb-legacy-source/dashboard.py
"""

from __future__ import annotations

import configparser
import json
import os
import subprocess
import sys
import threading
import time
import webbrowser
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

import requests

from roli_trade_ads import REQUEST_TAGS, create_payload, post_trade_ad

ROOT_DIR = Path(__file__).resolve().parent.parent
SOURCE_DIR = Path(__file__).resolve().parent
CONFIG_PATH = ROOT_DIR / "config.ini"
LOG_DIR = ROOT_DIR / "logs"
HOST = "127.0.0.1"
PORT = int(os.environ.get("OTB_DASHBOARD_PORT", "8765"))

BOT_PROCESS: subprocess.Popen | None = None
BOT_LOCK = threading.Lock()

DEFAULT_CONFIG = {
    "General": {
        "roblosecurity": "",
        "authenticator_code": "",
        "roli_verification": "",
        "colors": "false",
        "archive_trade_messages": "true",
        "message_check_interval": "60",
        "switch_proxy_every_minutes": "10",
        "webhook_url": "none",
    },
    "Trading": {
        "testing": "false",
        "use_old_value_algorithm": "true",
        "maximum_item_value": "27500",
        "partner_rap_scan_limit_multiplier": "1.5",
        "value_op_items_at_rap": "false",
        "not_for_trade": "0",
        "do_not_trade_away": "0",
        "do_not_trade_for": "0",
        "only_trade_accessories": "false",
        "minimum_item_age": "5184000",
        "minimum_volume": ".15",
        "safety": "true",
        "keep_items_on_sale": "false",
        "sale_price_multiplier": "1",
        "maximum_item_value_for_resale": "15000",
        "interval_between_placing_items_on_sale": "10",
        "constant_reseller_list_position": "-1",
        "handle_inbound_trades": "true",
        "ignore_inbound_above_value": "15000",
        "interval_between_checking_inbound": "60",
        "accept_but_dont_decline": "false",
        "minimum_time_between_trades": "30",
        "auto_adjust_time_between_trades": "true",
        "maximum_xv1": "4",
        "maximum_1vx": "4",
        "vary_trade_grades": "true",
        "maximum_time_searching_with_partner": "10",
        "minimum_trade_partner_cooldown": "86400",
        "score_threshold": ".1123",
        "score_function_of_rap_or_value": "rap",
        "minimum_value_gain": "1",
        "apply_minimum_value_to_inbound": "true",
        "additional_minimum_value_gain_per_item_downgraded": "0.05",
        "minimum_rap_gain": "none",
        "apply_minimum_rap_to_inbound": "true",
        "maximum_inbound_rap_loss": "0",
        "minimum_trade_value": "100",
        "max_weighted_item_volume_slippage_allowance": "none",
        "weighted_item_volume_high_value_bias": "1.5",
        "trade_priority": "2",
    },
    "Debugging": {"easy_debug": "false", "memory_debugging": "false"},
}

HTML = r"""
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Olympian Trading Dashboard</title>
  <style>
    :root {
      --cream: #f7f1e6;
      --paper: #fffaf0;
      --beige: #e8dcc8;
      --tan: #d3b98e;
      --oak: #b98d55;
      --oak-dark: #775735;
      --ink: #2f2922;
      --muted: #786b5d;
      --line: rgba(119, 87, 53, .22);
      --good: #5f7f4f;
      --bad: #a15d4f;
      --shadow: 0 18px 50px rgba(82, 61, 38, .12);
    }
    * { box-sizing: border-box; }
    body { margin: 0; font-family: Inter, ui-sans-serif, system-ui, -apple-system, Segoe UI, sans-serif; color: var(--ink); background: radial-gradient(circle at top left, #fff8e9, var(--cream) 42%, #eadcc5); }
    .shell { min-height: 100vh; display: grid; grid-template-columns: 270px 1fr; }
    aside { padding: 28px 22px; background: linear-gradient(180deg, rgba(255,250,240,.86), rgba(232,220,200,.82)); border-right: 1px solid var(--line); }
    .brand { display: flex; gap: 13px; align-items: center; margin-bottom: 34px; }
    .mark { width: 42px; height: 42px; border-radius: 14px; background: linear-gradient(135deg, var(--tan), var(--oak)); box-shadow: inset 0 1px 0 rgba(255,255,255,.45); }
    h1 { font-size: 18px; margin: 0; letter-spacing: -.02em; }
    .caption { margin: 4px 0 0; color: var(--muted); font-size: 12px; }
    nav a { display: block; padding: 12px 14px; margin: 8px 0; border-radius: 14px; color: var(--oak-dark); text-decoration: none; font-weight: 650; }
    nav a.active, nav a:hover { background: rgba(185,141,85,.16); }
    main { padding: 34px; }
    .topbar { display:flex; justify-content:space-between; gap:20px; align-items:center; margin-bottom:26px; }
    h2 { font-size: 32px; margin: 0; letter-spacing: -.04em; }
    .status { display:inline-flex; align-items:center; gap:8px; padding:10px 14px; border:1px solid var(--line); border-radius:999px; background:rgba(255,250,240,.72); color:var(--muted); }
    .dot { width:10px; height:10px; border-radius:99px; background:var(--bad); }
    .dot.running { background:var(--good); }
    .grid { display:grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap:18px; }
    .card { background: rgba(255,250,240,.78); border:1px solid var(--line); border-radius:24px; box-shadow: var(--shadow); padding:22px; backdrop-filter: blur(14px); }
    .card h3 { margin:0 0 14px; font-size:15px; color:var(--oak-dark); }
    .stat { font-size:32px; font-weight:800; letter-spacing:-.04em; }
    .muted { color: var(--muted); font-size: 13px; }
    .wide { grid-column: span 2; }
    .full { grid-column: 1 / -1; }
    button, input, select, textarea { font: inherit; }
    button { border:0; padding:12px 16px; border-radius:14px; font-weight:750; cursor:pointer; background:var(--oak-dark); color:#fff9ed; box-shadow:0 10px 20px rgba(119,87,53,.16); }
    button.secondary { background:#f2e7d5; color:var(--oak-dark); border:1px solid var(--line); box-shadow:none; }
    button.danger { background:var(--bad); }
    .actions { display:flex; gap:12px; flex-wrap:wrap; }
    label { display:block; font-size:12px; font-weight:760; color:var(--oak-dark); margin:12px 0 6px; }
    input, select, textarea { width:100%; border:1px solid var(--line); background:rgba(255,255,255,.56); border-radius:14px; padding:12px 13px; color:var(--ink); outline:none; }
    textarea { min-height:82px; resize:vertical; }
    .form-grid { display:grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap:14px; }
    .setup { position:fixed; inset:0; display:none; place-items:center; background:rgba(47,41,34,.28); padding:24px; }
    .setup.open { display:grid; }
    .modal { max-width:900px; width:100%; max-height:90vh; overflow:auto; background:var(--paper); border-radius:28px; padding:28px; box-shadow:0 30px 90px rgba(47,41,34,.28); }
    .toast { position:fixed; right:24px; bottom:24px; max-width:420px; padding:14px 16px; border-radius:16px; background:var(--ink); color:var(--paper); display:none; }
    .toast.show { display:block; }
    @media (max-width: 980px) { .shell{grid-template-columns:1fr} aside{display:none}.grid{grid-template-columns:1fr}.wide{grid-column:auto}.form-grid{grid-template-columns:1fr} main{padding:22px} }
  </style>
</head>
<body>
  <div class="shell">
    <aside>
      <div class="brand"><div class="mark"></div><div><h1>Olympian</h1><p class="caption">Local trading console</p></div></div>
      <nav><a class="active" href="#overview">Overview</a><a href="#trade-ads">Trade Ads</a><a href="#settings">Settings</a></nav>
    </aside>
    <main>
      <div class="topbar"><div><h2>Dashboard</h2><p class="caption">Beige oak workspace for bot control, setup, stats, and ROLI ads.</p></div><div class="status"><span id="statusDot" class="dot"></span><span id="botStatus">Stopped</span></div></div>
      <section id="overview" class="grid">
        <div class="card wide"><h3>Logged-in account</h3><div class="stat" id="accountName">Not connected</div><p class="muted" id="accountMeta">Save your cookie in setup to identify the account.</p></div>
        <div class="card"><h3>Trades sent</h3><div class="stat" id="tradesSent">0</div><p class="muted">Detected from local logs.</p></div>
        <div class="card"><h3>Queued trades</h3><div class="stat" id="queuedTrades">0</div><p class="muted">Recovered from .tradequeue.</p></div>
        <div class="card wide"><h3>Trade botting</h3><p class="muted">Start or stop the existing trading bot process without leaving the dashboard.</p><div class="actions"><button id="startBtn">Start bot</button><button id="stopBtn" class="danger">Stop bot</button><button id="refreshBtn" class="secondary">Refresh</button></div></div>
        <div class="card wide"><h3>Overall statistics</h3><div class="form-grid"><div><div class="stat" id="logFiles">0</div><p class="muted">Log files</p></div><div><div class="stat" id="lastEvent">—</div><p class="muted">Latest local bot event</p></div></div></div>
      </section>
      <section id="trade-ads" class="grid" style="margin-top:18px">
        <div class="card full"><h3>Post ROLI Trade Ad</h3><p class="muted">Enter item IDs separated by commas or spaces. Request tags can be used instead of requested items.</p><div class="form-grid"><div><label>Player ID</label><input id="adPlayerId" placeholder="Roblox user ID"></div><div><label>Request tags</label><select id="adTags" multiple size="5"></select></div><div><label>Offering item IDs</label><textarea id="adOffer" placeholder="6803423284, 7212273948"></textarea></div><div><label>Requesting item IDs</label><textarea id="adRequest" placeholder="259425946"></textarea></div></div><div class="actions" style="margin-top:16px"><button id="postAdBtn">Create trade ad</button></div></div>
      </section>
      <section id="settings" class="grid" style="margin-top:18px"><div class="card full"><h3>Settings</h3><p class="muted">Use setup to update account credentials and core bot preferences.</p><button id="openSetup" class="secondary">Open setup</button></div></section>
    </main>
  </div>
  <div id="setup" class="setup"><div class="modal"><h2>First-time setup</h2><p class="muted">Settings are saved locally to config.ini. Keep credentials private.</p><div class="form-grid"><div><label>.ROBLOSECURITY</label><input id="cfgRoblo" type="password"></div><div><label>Authenticator secret</label><input id="cfgAuth" type="password"></div><div><label>ROLI verification</label><input id="cfgRoli" type="password"></div><div><label>Webhook URL</label><input id="cfgWebhook" placeholder="none"></div><div><label>Testing mode</label><select id="cfgTesting"><option value="true">true - dry run</option><option value="false">false - real actions</option></select></div><div><label>Handle inbound trades</label><select id="cfgInbound"><option>true</option><option>false</option></select></div><div><label>Minimum value gain</label><input id="cfgMinGain"></div><div><label>Maximum item value</label><input id="cfgMaxItem"></div><div><label>Minimum time between trades</label><input id="cfgCooldown"></div><div><label>Minimum volume</label><input id="cfgVolume"></div></div><div class="actions" style="margin-top:18px"><button id="saveSetup">Save setup</button><button id="closeSetup" class="secondary">Close</button></div></div></div>
  <div id="toast" class="toast"></div>
<script>
const $ = id => document.getElementById(id);
function toast(msg){ $('toast').textContent = msg; $('toast').classList.add('show'); setTimeout(()=>$('toast').classList.remove('show'), 5000); }
async function api(path, opts={}){ const res = await fetch(path, {headers:{'Content-Type':'application/json'}, ...opts}); const data = await res.json(); if(!res.ok) throw new Error(data.error || 'Request failed'); return data; }
function fillConfig(cfg){ const g=cfg.General||{}, t=cfg.Trading||{}; $('cfgRoblo').value=g.roblosecurity||''; $('cfgAuth').value=g.authenticator_code||''; $('cfgRoli').value=g.roli_verification||''; $('cfgWebhook').value=g.webhook_url||'none'; $('cfgTesting').value=t.testing||'true'; $('cfgInbound').value=t.handle_inbound_trades||'true'; $('cfgMinGain').value=t.minimum_value_gain||'1'; $('cfgMaxItem').value=t.maximum_item_value||'27500'; $('cfgCooldown').value=t.minimum_time_between_trades||'30'; $('cfgVolume').value=t.minimum_volume||'.15'; $('adPlayerId').value=g.last_player_id||''; }
function render(data){ $('botStatus').textContent=data.bot.running?'Running':'Stopped'; $('statusDot').className='dot '+(data.bot.running?'running':''); $('accountName').textContent=data.account.name||'Not connected'; $('accountMeta').textContent=data.account.id?`User ID ${data.account.id}`:(data.setup_complete?'Configured locally; account lookup unavailable.':'Setup required.'); $('tradesSent').textContent=data.stats.trades_sent; $('queuedTrades').textContent=data.stats.queued_trades; $('logFiles').textContent=data.stats.log_files; $('lastEvent').textContent=data.stats.last_event||'—'; fillConfig(data.config); if(!data.setup_complete) $('setup').classList.add('open'); }
async function refresh(){ try { render(await api('/api/status')); } catch(e){ toast(e.message); } }
async function saveSetup(){ const body={General:{roblosecurity:$('cfgRoblo').value, authenticator_code:$('cfgAuth').value, roli_verification:$('cfgRoli').value, webhook_url:$('cfgWebhook').value || 'none'}, Trading:{testing:$('cfgTesting').value, handle_inbound_trades:$('cfgInbound').value, minimum_value_gain:$('cfgMinGain').value, maximum_item_value:$('cfgMaxItem').value, minimum_time_between_trades:$('cfgCooldown').value, minimum_volume:$('cfgVolume').value}}; try{ await api('/api/config',{method:'POST', body:JSON.stringify(body)}); $('setup').classList.remove('open'); toast('Settings saved locally.'); refresh(); }catch(e){ toast(e.message); } }
async function postAd(){ const tags=[...$('adTags').selectedOptions].map(o=>o.value); const body={player_id:$('adPlayerId').value, offer_item_ids:$('adOffer').value, request_item_ids:$('adRequest').value, request_tags:tags}; try{ const data=await api('/api/trade-ad',{method:'POST', body:JSON.stringify(body)}); toast(data.message); }catch(e){ toast(e.message); } }
for(const tag of Object.keys(%TAGS%)){ const opt=document.createElement('option'); opt.value=tag; opt.textContent=tag; $('adTags').appendChild(opt); }
$('startBtn').onclick=()=>api('/api/bot/start',{method:'POST'}).then(d=>{toast(d.message);refresh();}).catch(e=>toast(e.message));
$('stopBtn').onclick=()=>api('/api/bot/stop',{method:'POST'}).then(d=>{toast(d.message);refresh();}).catch(e=>toast(e.message));
$('refreshBtn').onclick=refresh; $('openSetup').onclick=()=>$('setup').classList.add('open'); $('closeSetup').onclick=()=>$('setup').classList.remove('open'); $('saveSetup').onclick=saveSetup; $('postAdBtn').onclick=postAd; refresh(); setInterval(refresh, 10000);
</script>
</body>
</html>
""".replace("%TAGS%", json.dumps(REQUEST_TAGS))


def load_config() -> configparser.ConfigParser:
    config = configparser.ConfigParser()
    for section, values in DEFAULT_CONFIG.items():
        config[section] = values.copy()
    if CONFIG_PATH.exists():
        config.read(CONFIG_PATH)
    return config


def save_config(updates: dict[str, dict[str, str]]) -> None:
    config = load_config()
    for section, values in updates.items():
        if section not in config:
            config.add_section(section)
        for key, value in values.items():
            config.set(section, key, str(value))
    with CONFIG_PATH.open("w") as file:
        config.write(file)


def public_config(config: configparser.ConfigParser) -> dict[str, dict[str, str]]:
    data = {section: dict(config[section]) for section in config.sections()}
    for section, key in [("General", "roblosecurity"), ("General", "authenticator_code"), ("General", "roli_verification")]:
        data.setdefault(section, {})[key] = config.get(section, key, fallback="")
    return data


def setup_complete(config: configparser.ConfigParser) -> bool:
    roblosecurity = config.get("General", "roblosecurity", fallback="").strip()
    authenticator = config.get("General", "authenticator_code", fallback="").strip()
    return (
        bool(roblosecurity)
        and roblosecurity != "put your .roblosecurity here"
        and bool(authenticator)
        and authenticator != "enter auth code here"
    )


def bot_running() -> bool:
    global BOT_PROCESS
    with BOT_LOCK:
        return BOT_PROCESS is not None and BOT_PROCESS.poll() is None


def start_bot() -> str:
    global BOT_PROCESS
    with BOT_LOCK:
        if BOT_PROCESS is not None and BOT_PROCESS.poll() is None:
            return "Bot is already running."
        BOT_PROCESS = subprocess.Popen(
            [sys.executable, str(SOURCE_DIR / "tradingbot.py")],
            cwd=str(ROOT_DIR),
        )
        return "Bot started."


def stop_bot() -> str:
    global BOT_PROCESS
    with BOT_LOCK:
        if BOT_PROCESS is None or BOT_PROCESS.poll() is not None:
            return "Bot is already stopped."
        BOT_PROCESS.terminate()
        try:
            BOT_PROCESS.wait(timeout=10)
        except subprocess.TimeoutExpired:
            BOT_PROCESS.kill()
        return "Bot stopped."


def account_info(config: configparser.ConfigParser) -> dict[str, str | None]:
    cookie = config.get("General", "roblosecurity", fallback="").strip()
    if not cookie:
        return {"id": None, "name": None}
    try:
        response = requests.get(
            "https://users.roblox.com/v1/users/authenticated",
            cookies={".ROBLOSECURITY": cookie},
            timeout=8,
        )
        if response.status_code == 200:
            data = response.json()
            return {"id": str(data.get("id")), "name": data.get("name")}
    except requests.RequestException:
        pass
    return {"id": None, "name": None}


def stats() -> dict[str, object]:
    log_files = sorted(LOG_DIR.glob("*.log")) if LOG_DIR.exists() else []
    trades_sent = 0
    last_event = ""
    for path in log_files[-10:]:
        try:
            lines = path.read_text(errors="ignore").splitlines()
        except OSError:
            continue
        for line in lines:
            if "Trade sent successfully" in line:
                trades_sent += 1
            if line.strip():
                last_event = line[-90:]
    queue_path = ROOT_DIR / ".tradequeue"
    queued_trades = 0
    if queue_path.exists():
        queued_trades = len([part for part in queue_path.read_text(errors="ignore").split(",") if part.strip()])
    return {"trades_sent": trades_sent, "queued_trades": queued_trades, "log_files": len(log_files), "last_event": last_event}


class DashboardHandler(BaseHTTPRequestHandler):
    def _json(self, payload: dict[str, object], status: HTTPStatus = HTTPStatus.OK) -> None:
        data = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _body(self) -> dict[str, object]:
        length = int(self.headers.get("Content-Length", "0"))
        if length == 0:
            return {}
        return json.loads(self.rfile.read(length).decode())

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if path == "/":
            page = HTML.encode()
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(page)))
            self.end_headers()
            self.wfile.write(page)
            return
        if path == "/api/status":
            config = load_config()
            self._json({"setup_complete": setup_complete(config), "bot": {"running": bot_running()}, "account": account_info(config), "stats": stats(), "config": public_config(config)})
            return
        self.send_error(HTTPStatus.NOT_FOUND)

    def do_POST(self) -> None:
        path = urlparse(self.path).path
        try:
            if path == "/api/config":
                save_config(self._body())
                self._json({"ok": True})
                return
            if path == "/api/bot/start":
                self._json({"ok": True, "message": start_bot()})
                return
            if path == "/api/bot/stop":
                self._json({"ok": True, "message": stop_bot()})
                return
            if path == "/api/trade-ad":
                config = load_config()
                body = self._body()
                player_id = body.get("player_id") or account_info(config).get("id")
                payload = create_payload(player_id, body.get("offer_item_ids", ""), body.get("request_item_ids", ""), body.get("request_tags", []))
                result = post_trade_ad(config.get("General", "roli_verification", fallback=""), payload)
                self._json(result)
                return
        except Exception as exc:
            self._json({"ok": False, "error": str(exc)}, HTTPStatus.BAD_REQUEST)
            return
        self.send_error(HTTPStatus.NOT_FOUND)

    def log_message(self, format: str, *args: object) -> None:
        return


def main() -> None:
    server = ThreadingHTTPServer((HOST, PORT), DashboardHandler)
    url = f"http://{HOST}:{PORT}/"
    print(f"Olympian dashboard running at {url}")
    if os.environ.get("OTB_DASHBOARD_NO_BROWSER") != "1":
        threading.Timer(0.5, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        stop_bot()


if __name__ == "__main__":
    main()
