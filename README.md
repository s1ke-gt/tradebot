# otb-legacy

Roblox trading bot
- https://olympian.xyz
- https://discord.gg/mmXtqGu (OTB Discord)


# Install Guide
> [!NOTE]
> Install Python and make sure it's in your PATH. Compatible with atleast **Python 3.13**.


Launch Command Prompt, PowerShell, or Terminal and navigate to the root folder of the project. `otb-legacy`

**1. Install dependencies**

```bash
pip install -r requirements.txt
```

**2. Run the bot**

```bash
python otb-legacy-source/tradingbot.py
```

**3. Run the local dashboard**

```bash
python otb-legacy-source/dashboard.py
```

On Windows, you can also double-click `otb-legacy-source/olympian.bat`; it
launches the same local dashboard using your installed Python rather than a
nonexistent `olympian.exe`.

The dashboard runs locally at `http://127.0.0.1:8765/` and provides first-time
setup, account status, bot start/stop controls, local trade statistics, and a
ROLI trade ad posting form.

To avoid unnecessary Roblox resale-data lookups, the bot pre-filters other
users' inventories before generating values. By default it only values partner
items whose RAP is at or below `1.5x` your tradable account RAP; change
`partner_rap_scan_limit_multiplier` in `config.ini` to adjust this percentage,
or set it to `none` to disable the pre-filter.

Inbound trades also have an extra RAP safety guard. By default,
`maximum_inbound_rap_loss = 0`, so the bot will not accept inbound trades that
lose RAP even if the internal value calculation says the trade is profitable.
Raise this number or set it to `none` only if you intentionally want to allow
RAP-loss inbound accepts.

Dynamic face/head avoidance can already be done manually by adding item IDs to
`do_not_trade_for`, but the dashboard also exposes `auto_counter_dynamic_faces`.
When enabled, inbound trades offering an item listed in `faces.txt` are declined
and the bot immediately searches for a counter offer that excludes those items.
Add one dynamic head/face ID or exact item name per line in `faces.txt`; matching
is case-insensitive.

Trade-cycle mode is stored in editable `trade_cycle.txt` so it persists across
2-day trade holds and restarts. Use `UPG` for upgrade mode or `DG` for downgrade
mode. Upgrade mode only sends trades where you give more items for fewer items
and allows up to `upgrade_maximum_value_loss_percent` value loss. Downgrade mode
only sends trades where you receive more items and requires at least
`downgrade_minimum_value_gain_percent` overpay.

**4. Edit the config manually, if needed**

Open `config.ini` and fill in your cookie and 2FA secret code.

Then repeat step number #2 or use the dashboard start button and it will start
trading!
