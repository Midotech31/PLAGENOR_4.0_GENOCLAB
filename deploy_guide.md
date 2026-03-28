# PLAGENOR 4.0 — Windows Self-Hosted Deployment Guide

> **Target audience:** System administrator setting up PLAGENOR 4.0 on a Windows server or workstation.
> **Estimated setup time:** 30–60 minutes.

---

## Prerequisites

Before you begin, install or download the following:

| Tool | Version | Source |
|------|---------|--------|
| Python | 3.10 or newer | https://python.org/downloads |
| Git | Latest | https://git-scm.com/download/win |
| NSSM | 2.24+ | https://nssm.cc/download |
| cloudflared | Latest | https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/ |
| Cloudflare account | Free tier | https://dash.cloudflare.com/sign-up |
| Domain name | Any | Pointed to Cloudflare DNS (nameservers changed at registrar) |

> **Tip:** Place `nssm.exe` and `cloudflared.exe` in a folder that is on your system `PATH`
> (e.g. `C:\Windows\System32\` or a dedicated `C:\Tools\` folder added to the PATH environment variable)
> so the commands below work without specifying full paths.

---

## Step 1: Clone and Set Up the Application

Open **Command Prompt** (or PowerShell) as Administrator, then run:

```bat
cd C:\Apps
git clone https://github.com/Midotech31/PLAGENOR_4.0_GENOCLAB.git plagenor
cd plagenor
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

**What each command does:**
- `git clone …` — downloads the source code into `C:\Apps\plagenor\`
- `python -m venv venv` — creates an isolated Python environment so PLAGENOR's packages do not conflict with other Python software
- `venv\Scripts\activate` — activates the virtual environment for the current session
- `pip install -r requirements.txt` — installs all required Python libraries

---

## Step 2: Configure the Environment

```bat
copy .env.example .env
```

Open `.env` with a text editor (Notepad, VS Code, etc.) and adjust the values to match your setup:

| Variable | Description | Default |
|----------|-------------|---------|
| `PLAGENOR_DATA_DIR` | Where the database is stored | `./data` |
| `PLAGENOR_SESSION_TIMEOUT` | Session timeout in minutes | `60` |
| `PLAGENOR_MAX_LOGIN` | Max failed logins before lockout | `5` |
| `PLAGENOR_VAT_RATE` | VAT rate (decimal) | `0.19` |
| `PLAGENOR_BUDGET_CAP` | Annual budget cap in DZD | `200000.0` |
| `PLAGENOR_SMTP_ENABLED` | Enable email notifications | `false` |
| `PLAGENOR_LOG_LEVEL` | Logging verbosity | `INFO` |

Then create the data directory:

```bat
mkdir data
mkdir logs
mkdir backup
```

---

## Step 3: First Run (Test Mode)

Run the application manually to confirm everything works:

```bat
venv\Scripts\activate
streamlit run app.py
```

- Open a browser and navigate to **http://localhost:8501**
- Log in with the default Super Admin credentials
- Confirm that `data\plagenor.db` was created:

```bat
dir data\plagenor.db
```

Press `Ctrl+C` in the terminal to stop the application when done testing.

---

## Step 4: Install as a Windows Service (NSSM)

Running PLAGENOR via **NSSM** ensures it starts automatically when Windows boots and restarts automatically if it crashes.

Open **Command Prompt as Administrator** and run each command:

```bat
nssm install PLAGENOR "C:\Apps\plagenor\venv\Scripts\python.exe" "-m" "streamlit" "run" "app.py"
```
*Registers a new Windows service called `PLAGENOR` that runs Streamlit via the virtual environment's Python.*

```bat
nssm set PLAGENOR AppDirectory "C:\Apps\plagenor"
```
*Sets the working directory so relative paths (like `./data`) resolve correctly.*

```bat
nssm set PLAGENOR AppStdout "C:\Apps\plagenor\logs\service.log"
nssm set PLAGENOR AppStderr "C:\Apps\plagenor\logs\error.log"
```
*Redirects application output to log files for troubleshooting.*

```bat
nssm set PLAGENOR Start SERVICE_AUTO_START
```
*Configures the service to start automatically at Windows boot.*

```bat
nssm set PLAGENOR AppRestartDelay 5000
```
*Waits 5 seconds before restarting the service if it crashes, preventing rapid restart loops.*

```bat
nssm start PLAGENOR
```
*Starts the service immediately.*

### Service Management Commands

| Action | Command |
|--------|---------|
| Check status | `nssm status PLAGENOR` |
| Stop service | `nssm stop PLAGENOR` |
| Restart service | `nssm restart PLAGENOR` |
| Remove service | `nssm remove PLAGENOR confirm` |
| Edit service config (GUI) | `nssm edit PLAGENOR` |

> **Alternative:** You can also manage the service through **Windows Services** (`services.msc`).

---

## Step 5: Cloudflare Tunnel Setup

A Cloudflare Tunnel allows secure HTTPS access to PLAGENOR from the internet without opening any firewall ports.

### 5.1 Log in to Cloudflare

```bat
cloudflared login
```

A browser window opens. Select the domain you want to use and click **Authorize**.

### 5.2 Create the Tunnel

```bat
cloudflared tunnel create plagenor
```

Note the **Tunnel ID** printed in the output (a UUID like `a1b2c3d4-...`).

### 5.3 Configure the Tunnel

Open `cloudflare\config.yml` and replace the placeholders:

| Placeholder | Replace with |
|-------------|-------------|
| `<YOUR_TUNNEL_ID>` | The UUID from step 5.2 |
| `<USERNAME>` | Your Windows username (e.g. `Administrator`) |
| `<YOUR_DOMAIN>` | Your domain (e.g. `plagenor.example.com`) |

### 5.4 Route DNS

```bat
cloudflared tunnel route dns plagenor plagenor.example.com
```

*This creates a CNAME record in your Cloudflare DNS pointing to the tunnel.*

### 5.5 Test the Tunnel

```bat
cloudflared tunnel --config cloudflare\config.yml run plagenor
```

Open `https://plagenor.example.com` in a browser. If the login page appears, the tunnel works.
Press `Ctrl+C` to stop the test run.

### 5.6 Install the Tunnel as a Service

```bat
copy cloudflare\config.yml C:\Users\%USERNAME%\.cloudflared\config.yml
cloudflared service install
```

The tunnel now runs as a Windows service (`Cloudflared`) and starts automatically at boot.

> **Verify tunnel service:** Open `services.msc` and look for **Cloudflared** — its status should be **Running**.

---

## Step 6: Backup Automation

Schedule `backup_plagenor.py` to run daily at 02:00 AM:

```bat
schtasks /create ^
  /tn "PLAGENOR_Backup" ^
  /tr "\"C:\Apps\plagenor\venv\Scripts\python.exe\" \"C:\Apps\plagenor\backup_plagenor.py\"" ^
  /sc daily ^
  /st 02:00 ^
  /ru SYSTEM
```

**What this does:**
- `/tn "PLAGENOR_Backup"` — names the scheduled task
- `/tr "python … backup_plagenor.py"` — the command to execute
- `/sc daily /st 02:00` — runs once per day at 2:00 AM
- `/ru SYSTEM` — runs as the SYSTEM account (no user needs to be logged in)

### Verify the Task

```bat
schtasks /query /tn "PLAGENOR_Backup"
```

### Run a Manual Backup Test

```bat
C:\Apps\plagenor\venv\Scripts\python.exe C:\Apps\plagenor\backup_plagenor.py
```

Check that a file was created in `C:\Apps\plagenor\backup\`:

```bat
dir C:\Apps\plagenor\backup\
```

The backup script automatically keeps only the **last 30 backups**, deleting older files.

---

## Step 7: Verification Checklist

After completing all steps, verify the following:

- [ ] `http://localhost:8501` loads the PLAGENOR login page
- [ ] `https://yourdomain.com` loads the PLAGENOR login page over HTTPS
- [ ] Login with Super Admin credentials succeeds
- [ ] Data persists after stopping and restarting the PLAGENOR service (`nssm restart PLAGENOR`)
- [ ] `backup\` directory contains at least one `.db` file after running the backup script
- [ ] `logs\service.log` is being written to by the service
- [ ] PLAGENOR service is listed as **Running** in `services.msc`
- [ ] Cloudflared service is listed as **Running** in `services.msc`
- [ ] After a **full machine reboot**, both services start automatically and the app is accessible

---

## Troubleshooting

### Application not accessible at localhost:8501

1. Check the service is running: `nssm status PLAGENOR`
2. Check for errors: `type C:\Apps\plagenor\logs\error.log`
3. Verify the port is not blocked by Windows Firewall:
   ```bat
   netstat -ano | findstr :8501
   ```
4. Try starting manually to see live errors:
   ```bat
   cd C:\Apps\plagenor
   venv\Scripts\activate
   streamlit run app.py
   ```

### NSSM service fails to start

- Confirm the path to `python.exe` is correct:
  ```bat
  C:\Apps\plagenor\venv\Scripts\python.exe --version
  ```
- Check that `requirements.txt` packages were installed:
  ```bat
  C:\Apps\plagenor\venv\Scripts\pip.exe list
  ```
- Open the NSSM GUI for detailed configuration: `nssm edit PLAGENOR`

### Cloudflare Tunnel not working

- Verify credentials file exists:
  ```bat
  dir C:\Users\%USERNAME%\.cloudflared\
  ```
- Check cloudflared logs in Event Viewer (`eventvwr.msc`) → Windows Logs → Application
- Re-authenticate: `cloudflared login`
- Confirm the DNS CNAME record exists in the Cloudflare dashboard (DNS → Records)

### Login fails / database corruption

1. Stop the PLAGENOR service: `nssm stop PLAGENOR`
2. Restore from a backup:
   ```bat
   copy backup\plagenor_YYYYMMDD_HHMMSS.db data\plagenor.db
   ```
3. Restart the service: `nssm start PLAGENOR`

### Reset the database (destructive — all data lost)

```bat
nssm stop PLAGENOR
del data\plagenor.db
del data\plagenor.db-wal
del data\plagenor.db-shm
nssm start PLAGENOR
```

A fresh database with default seed data will be created on next startup.

### How to check application logs

```bat
:: Live tail of the service log (requires PowerShell)
Get-Content C:\Apps\plagenor\logs\service.log -Wait -Tail 50

:: View last 100 lines of error log
powershell "Get-Content C:\Apps\plagenor\logs\error.log -Tail 100"
```

---

## Directory Structure Reference

```
C:\Apps\plagenor\
├── app.py                   ← Streamlit entry point
├── requirements.txt         ← Python dependencies
├── start_plagenor.bat       ← Manual/NSSM launch script
├── backup_plagenor.py       ← Backup script (Task Scheduler)
├── .env                     ← Your local config (never commit)
├── .env.example             ← Config template
├── .gitignore
├── .streamlit\
│   └── config.toml          ← Streamlit server/theme settings
├── cloudflare\
│   └── config.yml           ← Cloudflare Tunnel config
├── venv\                    ← Python virtual environment
├── data\
│   └── plagenor.db          ← SQLite database (auto-created)
├── backup\
│   └── plagenor_*.db        ← Timestamped database backups
├── logs\
│   ├── service.log          ← NSSM stdout log
│   └── error.log            ← NSSM stderr log
├── core\                    ← Business logic modules
├── ui\                      ← Streamlit page components
├── services\                ← Service integrations
├── templates\               ← Word document templates
└── assets\                  ← Logos and static images
```

---

*PLAGENOR 4.0 — Developed by Midotech31 / GENOCLAB. For issues, open a ticket on the GitHub repository.*
