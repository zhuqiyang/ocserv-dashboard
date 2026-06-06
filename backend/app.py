#!/usr/bin/env python3
"""ocserv Web Manager - Flask Backend"""

import os
import re
import sys
import json
import crypt
import hashlib
import subprocess
import secrets
from datetime import datetime, timedelta
from functools import wraps

import jwt
from flask import Flask, request, jsonify, g, send_from_directory
from flask_cors import CORS

from i18n import _, get_locale

# ============================================================
# Configuration
# ============================================================
OCPASSWD_FILE = "/etc/ocserv/ocpasswd"
OCCTL_BIN = "/usr/bin/occtl"
OCPASSWD_BIN = "/usr/bin/ocpasswd"
FRONTEND_DIR = "/opt/ocserv-manager/frontend/dist"
JWT_SECRET = secrets.token_hex(32)
JWT_EXPIRY_HOURS = 24

# Write JWT secret to file for persistence across restarts
SECRET_FILE = "/opt/ocserv-manager/backend/.jwt_secret"
if os.path.exists(SECRET_FILE):
    with open(SECRET_FILE) as f:
        JWT_SECRET = f.read().strip()
else:
    with open(SECRET_FILE, "w") as f:
        f.write(JWT_SECRET)
    os.chmod(SECRET_FILE, 0o600)

app = Flask(__name__, static_folder=FRONTEND_DIR, static_url_path="")
CORS(app, supports_credentials=True)

# ============================================================
# Password helpers (compatible with ocpasswd crypt format)
# ============================================================

def parse_ocpasswd():
    """Parse the ocpasswd file. Returns dict: username -> {group, hash}"""
    users = {}
    if not os.path.exists(OCPASSWD_FILE):
        return users
    with open(OCPASSWD_FILE) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split(":", 2)
            if len(parts) >= 3:
                users[parts[0]] = {"group": parts[1], "hash": parts[2]}
    return users


def verify_password(password, stored_hash):
    """Verify a password against a crypt(3) hash (as used by ocpasswd)."""
    if not stored_hash:
        return False
    try:
        return crypt.crypt(password, stored_hash) == stored_hash
    except Exception:
        return False


def hash_password(password):
    """Hash a password using SHA-512 crypt (same as ocpasswd default)."""
    salt_chars = "./0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
    salt = "$6$" + "".join(secrets.choice(salt_chars) for _ in range(16))
    return crypt.crypt(password, salt)


# ============================================================
# JWT helpers
# ============================================================

def create_token(username, is_admin):
    """Create a JWT token."""
    payload = {
        "sub": username,
        "admin": is_admin,
        "iat": datetime.utcnow(),
        "exp": datetime.utcnow() + timedelta(hours=JWT_EXPIRY_HOURS),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")


def decode_token(token):
    """Decode and verify a JWT token. Returns payload or None."""
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def admin_required(f):
    """Decorator: require admin role."""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get("Authorization", "").replace("Bearer ", "")
        if not token:
            return jsonify({"error": _("no_token")}), 401
        payload = decode_token(token)
        if not payload:
            return jsonify({"error": _("invalid_token")}), 401
        if not payload.get("admin"):
            return jsonify({"error": _("admin_required")}), 403
        g.user = payload
        return f(*args, **kwargs)
    return decorated


def login_required(f):
    """Decorator: require valid login."""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get("Authorization", "").replace("Bearer ", "")
        if not token:
            return jsonify({"error": _("no_token")}), 401
        payload = decode_token(token)
        if not payload:
            return jsonify({"error": _("invalid_token")}), 401
        g.user = payload
        return f(*args, **kwargs)
    return decorated


# ============================================================
# API Routes
# ============================================================

@app.route("/api/lang", methods=["GET"])
def get_lang():
    """Return the detected language (useful for frontend sync)."""
    return jsonify({"lang": get_locale()})


@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "timestamp": datetime.utcnow().isoformat()})


@app.route("/api/login", methods=["POST"])
def login():
    """Authenticate user against ocpasswd file."""
    data = request.get_json()
    if not data:
        return jsonify({"error": _("no_data")}), 400

    username = data.get("username", "").strip()
    password = data.get("password", "")

    if not username or not password:
        return jsonify({"error": _("username_password_required")}), 400

    users = parse_ocpasswd()
    if username not in users:
        return jsonify({"error": _("invalid_credentials")}), 401

    user_info = users[username]
    # Check if user is locked (ocpasswd uses '!' prefix in hash to lock)
    if user_info["hash"].startswith("!"):
        return jsonify({"error": _("account_locked")}), 403

    if not verify_password(password, user_info["hash"]):
        return jsonify({"error": _("invalid_credentials")}), 401

    # Check if user is admin (group name contains 'admin' or username is 'admin')
    is_admin = (username == "admin" or "admin" in user_info.get("group", "").lower())

    token = create_token(username, is_admin)

    return jsonify({
        "token": token,
        "username": username,
        "is_admin": is_admin,
    })


@app.route("/api/me", methods=["GET"])
@login_required
def get_me():
    """Get current user info."""
    username = g.user["sub"]
    users = parse_ocpasswd()
    user_info = users.get(username, {})
    online = _check_user_online(username)

    return jsonify({
        "username": username,
        "is_admin": g.user["admin"],
        "group": user_info.get("group", ""),
        "online": online,
    })


@app.route("/api/users", methods=["GET"])
@admin_required
def list_users():
    """List all users (admin only)."""
    users = parse_ocpasswd()
    online_users = _get_online_users()

    result = []
    for username, info in users.items():
        locked = info["hash"].startswith("!")
        result.append({
            "username": username,
            "group": info["group"],
            "locked": locked,
            "online": username in online_users,
            "online_details": online_users.get(username),
        })

    return jsonify({"users": result, "total": len(result)})


@app.route("/api/users", methods=["POST"])
@admin_required
def add_user():
    """Add a new user (admin only)."""
    data = request.get_json()
    if not data:
        return jsonify({"error": _("no_data")}), 400

    username = data.get("username", "").strip()
    password = data.get("password", "")
    group = data.get("group", "*")

    if not username or not password:
        return jsonify({"error": _("username_password_required")}), 400

    # Validate username
    if not re.match(r'^[a-zA-Z0-9_\-\.@]+$', username):
        return jsonify({"error": _("invalid_username")}), 400

    if len(password) < 6:
        return jsonify({"error": _("password_too_short")}), 400

    # Check if user already exists
    users = parse_ocpasswd()
    if username in users:
        return jsonify({"error": _("user_exists")}), 409

    # Add user using ocpasswd
    try:
        proc = subprocess.run(
            [OCPASSWD_BIN, "-c", OCPASSWD_FILE, "-g", group, username],
            input=password + "\n",
            capture_output=True,
            text=True,
            timeout=10,
        )
        if proc.returncode != 0:
            return jsonify({"error": _("create_user_failed", error=proc.stderr.strip())}), 500
    except Exception as e:
        return jsonify({"error": _("create_user_failed", error=str(e))}), 500

    return jsonify({"message": _("user_created", username=username)}), 201


@app.route("/api/users/<username>", methods=["DELETE"])
@admin_required
def delete_user(username):
    """Delete a user (admin only)."""
    if username == "admin":
        return jsonify({"error": _("cannot_delete_admin")}), 403

    users = parse_ocpasswd()
    if username not in users:
        return jsonify({"error": _("user_not_found")}), 404

    try:
        proc = subprocess.run(
            [OCPASSWD_BIN, "-c", OCPASSWD_FILE, "-d", username],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if proc.returncode != 0:
            return jsonify({"error": _("delete_user_failed", error=proc.stderr.strip())}), 500
    except Exception as e:
        return jsonify({"error": _("delete_user_failed", error=str(e))}), 500

    # Also disconnect the user if online
    _disconnect_user(username)

    return jsonify({"message": _("user_deleted", username=username)})


@app.route("/api/users/<username>/lock", methods=["POST"])
@admin_required
def toggle_lock_user(username):
    """Lock or unlock a user (admin only)."""
    if username == "admin":
        return jsonify({"error": _("cannot_lock_admin")}), 403

    data = request.get_json() or {}
    action = data.get("action", "lock")  # 'lock' or 'unlock'

    users = parse_ocpasswd()
    if username not in users:
        return jsonify({"error": _("user_not_found")}), 404

    try:
        flag = "-l" if action == "lock" else "-u"
        proc = subprocess.run(
            [OCPASSWD_BIN, "-c", OCPASSWD_FILE, flag, username],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if proc.returncode != 0:
            return jsonify({"error": _("lock_user_failed", action=action, error=proc.stderr.strip())}), 500
    except Exception as e:
        return jsonify({"error": _("lock_user_failed", action=action, error=str(e))}), 500

    if action == "lock":
        _disconnect_user(username)

    if action == "lock":
        msg_key = "user_locked"
    else:
        msg_key = "user_unlocked"
    return jsonify({"message": _(msg_key, username=username)})


@app.route("/api/users/online", methods=["GET"])
@admin_required
def get_online_users():
    """Get currently connected users (admin only)."""
    online = _get_online_users()
    return jsonify({"online_users": list(online.keys()), "details": online, "count": len(online)})


@app.route("/api/users/<username>/disconnect", methods=["POST"])
@admin_required
def disconnect_user_api(username):
    """Disconnect a user (admin only)."""
    success = _disconnect_user(username)
    if success:
        return jsonify({"message": _("user_disconnected", username=username)})
    return jsonify({"error": _("disconnect_failed", username=username)}), 500


@app.route("/api/change-password", methods=["POST"])
@login_required
def change_password():
    """Change own password."""
    data = request.get_json()
    if not data:
        return jsonify({"error": _("no_data")}), 400

    current_password = data.get("current_password", "")
    new_password = data.get("new_password", "")

    if not current_password or not new_password:
        return jsonify({"error": _("username_password_required")}), 400

    if len(new_password) < 6:
        return jsonify({"error": _("password_too_short")}), 400

    username = g.user["sub"]

    # Verify current password
    users = parse_ocpasswd()
    if username not in users:
        return jsonify({"error": _("user_not_in_file")}), 404

    if not verify_password(current_password, users[username]["hash"]):
        return jsonify({"error": _("current_password_wrong")}), 401

    # Change password
    try:
        new_hash = hash_password(new_password)
        group = users[username]["group"]

        lines = []
        with open(OCPASSWD_FILE) as f:
            lines = f.readlines()

        found = False
        for i, line in enumerate(lines):
            if line.startswith(username + ":"):
                lines[i] = f"{username}:{group}:{new_hash}\n"
                found = True
                break

        if not found:
            return jsonify({"error": _("user_entry_not_found")}), 500

        with open(OCPASSWD_FILE, "w") as f:
            f.writelines(lines)

    except Exception as e:
        return jsonify({"error": _("change_password_failed", error=str(e))}), 500

    return jsonify({"message": _("change_password_success")})


@app.route("/api/server/status", methods=["GET"])
@admin_required
def server_status():
    """Get ocserv server status (admin only)."""
    try:
        proc = subprocess.run(
            [OCCTL_BIN, "-j", "show", "status"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if proc.returncode != 0:
            return jsonify({
                "running": False,
                "error": proc.stderr.strip() or _("cannot_connect_ocserv"),
            })

        status_data = json.loads(proc.stdout) if proc.stdout.strip() else {}
        status_data["running"] = True
        return jsonify(status_data)
    except json.JSONDecodeError:
        return jsonify({"running": True, "raw": proc.stdout.strip()})
    except FileNotFoundError:
        return jsonify({"running": False, "error": _("occtl_not_found")})
    except Exception as e:
        return jsonify({"running": False, "error": str(e)})


# ============================================================
# Helper functions
# ============================================================

def _get_online_users():
    """Get dict of online users from occtl."""
    online = {}
    try:
        proc = subprocess.run(
            [OCCTL_BIN, "-j", "show", "users"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if proc.returncode == 0 and proc.stdout.strip():
            data = json.loads(proc.stdout)
            for entry in data if isinstance(data, list) else []:
                username = entry.get("Username") or entry.get("username", "")
                if username:
                    online[username] = entry
    except Exception:
        pass
    return online


def _check_user_online(username):
    """Check if a specific user is online."""
    online = _get_online_users()
    return username in online


def _disconnect_user(username):
    """Disconnect a user by username. Returns True if successful."""
    try:
        proc = subprocess.run(
            [OCCTL_BIN, "disconnect", "user", username],
            capture_output=True,
            text=True,
            timeout=10,
        )
        return proc.returncode == 0
    except Exception:
        return False


# ============================================================
# Serve Frontend (SPA)
# ============================================================

@app.route("/")
def serve_index():
    """Serve the Vue SPA index.html."""
    if os.path.exists(os.path.join(FRONTEND_DIR, "index.html")):
        return send_from_directory(FRONTEND_DIR, "index.html")
    return jsonify({"message": _("api_message"), "frontend": _("frontend_not_built")}), 200


@app.route("/<path:path>")
def serve_static(path):
    """Serve static files from the frontend build directory."""
    full_path = os.path.join(FRONTEND_DIR, path)
    if os.path.isfile(full_path):
        return send_from_directory(FRONTEND_DIR, path)
    # For SPA routing, return index.html for non-file paths
    if os.path.exists(os.path.join(FRONTEND_DIR, "index.html")):
        return send_from_directory(FRONTEND_DIR, "index.html")
    return jsonify({"error": _("not_found")}), 404


# ============================================================
# Main
# ============================================================

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="ocserv Web Manager Backend")
    parser.add_argument("--host", default="127.0.0.1", help="Bind address")
    parser.add_argument("--port", type=int, default=5000, help="Bind port")
    parser.add_argument("--debug", action="store_true", help="Debug mode")
    args = parser.parse_args()

    print(f"JWT Secret file: {SECRET_FILE}")
    print(f"Starting ocserv Web Manager on {args.host}:{args.port}")
    app.run(host=args.host, port=args.port, debug=args.debug)
