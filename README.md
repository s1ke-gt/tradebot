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

**4. Edit the config manually, if needed**

Open `config.ini` and fill in your cookie and 2FA secret code.

Then repeat step number #2 or use the dashboard start button and it will start
trading!
