# ocserv Dashboard

[English](README_en.md) | 中文版

基于 Web 的 [ocserv](https://ocserv.openconnect-vpn.net/)（OpenConnect VPN 服务器）管理面板。

## 功能特性

- **仪表盘** — 用户信息、VPN 状态、服务器状态、在线用户
- **用户管理** — 添加 / 删除 / 锁定 / 解锁用户
- **在线用户** — 查看已连接的客户端，按需断开连接
- **修改密码** — 用户可自行修改 VPN 密码
- **国际化** — 中文（zh-CN）和英文（en），一键切换
- **JWT 认证** — 基于 ocserv 的 `ocpasswd` 文件进行无状态认证

## 技术栈

| 层级 | 技术 |
|------|------|
| 后端 | Python 3 + Flask + Gunicorn |
| 前端 | Vue 3 + Vue Router + Axios |
| 国际化 | 后端 JSON 语言文件，前端 vue-i18n |
| 认证 | JWT (HS256)，基于 `/etc/ocserv/ocpasswd` |

## 环境要求

- Python 3.8+
- Node.js 18+
- ocserv（提供 `ocpasswd` 和 `occtl` 命令）

## 快速安装

```bash
sudo bash install.sh
```

脚本将自动完成以下步骤：
1. 安装系统依赖（Python venv、Node.js）
2. 创建 Python 虚拟环境并安装依赖包
3. 构建 Vue 3 前端
4. 安装并启动 systemd 服务

## 手动部署

### 后端

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app.py --host 0.0.0.0 --port 5000
```

### 前端

```bash
cd frontend
npm install
npm run build        # 生产构建 → dist/
npm run dev          # 开发服务器 :5173，含 API 代理
```

### Systemd 服务

```bash
sudo cp ocserv-manager.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now ocserv-manager
```

## 使用说明

| URL | 说明 |
|-----|------|
| `http://<host>:5000/` | Web 管理界面 |
| `http://<host>:5000/api/health` | 健康检查 |
| `http://<host>:5000/api/lang` | 当前语言 |

### 默认登录

使用已有的 ocserv 账号密码登录。用户名为 `admin`（或所在组包含 "admin" 的用户）具有管理员权限。

## API 接口

| 方法 | 路径 | 权限 | 说明 |
|------|------|------|------|
| GET | `/api/health` | — | 健康检查 |
| POST | `/api/login` | — | 登录，返回 JWT |
| GET | `/api/me` | 用户 | 当前用户信息 |
| GET | `/api/users` | 管理员 | 列出所有用户 |
| POST | `/api/users` | 管理员 | 添加用户 |
| DELETE | `/api/users/<name>` | 管理员 | 删除用户 |
| POST | `/api/users/<name>/lock` | 管理员 | 锁定 / 解锁用户 |
| GET | `/api/users/online` | 管理员 | 在线用户列表 |
| POST | `/api/users/<name>/disconnect` | 管理员 | 断开用户连接 |
| POST | `/api/change-password` | 用户 | 修改自己的密码 |
| GET | `/api/server/status` | 管理员 | ocserv 服务器状态 |

### 语言检测

在 API 请求中设置 `Accept-Language` 请求头：

```bash
curl -H "Accept-Language: zh-CN" http://host:5000/api/login ...
curl -H "Accept-Language: en"    http://host:5000/api/login ...
```

## 项目结构

```
ocserv-manager/
├── backend/
│   ├── app.py              # Flask 应用
│   ├── i18n.py             # 翻译模块
│   ├── requirements.txt    # Python 依赖
│   └── locales/
│       ├── en.json         # 英文翻译
│       └── zh_CN.json      # 中文翻译
├── frontend/
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   └── src/
│       ├── main.js         # 应用入口
│       ├── i18n.js          # vue-i18n 配置
│       ├── App.vue          # 根组件 + 导航栏
│       ├── router/index.js  # Vue Router
│       ├── locales/
│       │   ├── en.json
│       │   └── zh-CN.json
│       └── views/
│           ├── Login.vue
│           ├── Dashboard.vue
│           ├── AdminUsers.vue
│           └── ChangePassword.vue
├── install.sh              # 一键安装脚本
├── ocserv-manager.service  # systemd 单元文件
├── README.md               # 中文文档（默认）
└── README_en.md            # 英文文档
```

## 开源协议

MIT
