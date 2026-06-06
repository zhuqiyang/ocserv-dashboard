# ocserv Dashboard

Web-based management dashboard for [ocserv](https://ocserv.openconnect-vpn.net/) (OpenConnect VPN server).

## Features

- **Dashboard** — user info, VPN status, server status, online users
- **User Management** — add / delete / lock / unlock users
- **Online Users** — view connected clients, disconnect on demand
- **Change Password** — users can change their own VPN password
- **i18n** — Chinese (zh-CN) and English (en) with one-click switch
- **JWT Auth** — stateless authentication against ocserv's `ocpasswd` file

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3 + Flask + Gunicorn |
| Frontend | Vue 3 + Vue Router + Axios |
| i18n | Backend JSON locales, Frontend vue-i18n |
| Auth | JWT (HS256) against `/etc/ocserv/ocpasswd` |

## Prerequisites

- Python 3.8+
- Node.js 18+
- ocserv (provides `ocpasswd` and `occtl`)

## Quick Install

```bash
sudo bash install.sh
```

The script will:
1. Install system dependencies (Python venv, Node.js)
2. Set up Python virtual environment and install packages
3. Build the Vue 3 frontend
4. Install and start the systemd service

## Manual Setup

### Backend

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app.py --host 0.0.0.0 --port 5000
```

### Frontend

```bash
cd frontend
npm install
npm run build        # production build → dist/
npm run dev          # dev server on :5173 with API proxy
```

### Systemd Service

```bash
sudo cp ocserv-manager.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now ocserv-manager
```

## Usage

| URL | Description |
|-----|-------------|
| `http://<host>:5000/` | Web UI |
| `http://<host>:5000/api/health` | Health check |
| `http://<host>:5000/api/lang` | Current language |

### Default Login

Use your existing ocserv account credentials. The user `admin` (or any user in a group containing "admin") has administrator privileges.

## API Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/health` | — | Health check |
| POST | `/api/login` | — | Login, returns JWT |
| GET | `/api/me` | user | Current user info |
| GET | `/api/users` | admin | List all users |
| POST | `/api/users` | admin | Add user |
| DELETE | `/api/users/<name>` | admin | Delete user |
| POST | `/api/users/<name>/lock` | admin | Lock / unlock user |
| GET | `/api/users/online` | admin | Online users |
| POST | `/api/users/<name>/disconnect` | admin | Disconnect user |
| POST | `/api/change-password` | user | Change own password |
| GET | `/api/server/status` | admin | ocserv server status |

### Language Detection

Set the `Accept-Language` header in API requests:

```bash
curl -H "Accept-Language: zh-CN" http://host:5000/api/login ...
curl -H "Accept-Language: en"    http://host:5000/api/login ...
```

## Project Structure

```
ocserv-manager/
├── backend/
│   ├── app.py              # Flask application
│   ├── i18n.py             # Translation module
│   ├── requirements.txt    # Python dependencies
│   └── locales/
│       ├── en.json         # English translations
│       └── zh_CN.json      # Chinese translations
├── frontend/
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   └── src/
│       ├── main.js         # App entry
│       ├── i18n.js         # vue-i18n setup
│       ├── App.vue         # Root component + navbar
│       ├── router/index.js # Vue Router
│       ├── locales/
│       │   ├── en.json
│       │   └── zh-CN.json
│       └── views/
│           ├── Login.vue
│           ├── Dashboard.vue
│           ├── AdminUsers.vue
│           └── ChangePassword.vue
├── install.sh              # One-click installer
├── ocserv-manager.service  # systemd unit
└── README.md
```

## License

MIT
