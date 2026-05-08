# Claude Code + Kali MCP 配置模板

在 macOS 上通过 Claude Code MCP 协议远程调用 Kali Linux VM 中的安全工具。

## 架构

```
Claude Code (macOS)
  └─ .mcp.json → mcp-wrapper.sh → mcp_server.py (FastMCP bridge)
       └─ HTTP → Kali VM (192.168.64.2:5000) → api_server.py (Flask)
            └─ subprocess → nmap, nikto, sqlmap, gobuster...
```

## 前置条件

- macOS 上安装 UTM，运行 Kali Linux ARM VM
- UTM 网络模式：**Shared Network**（VM 自动获得 192.168.64.x 地址）
- macOS 安装 pyenv Python 3.12

## 快速开始

### 1. Kali VM 端

将 `api_server.py` 复制到 Kali VM 并配置 systemd 自启动：

```bash
# 在 Kali VM 内
mkdir -p ~/.config/systemd/user

cat > ~/.config/systemd/user/kali-api.service << 'EOF'
[Unit]
Description=Kali MCP API Server
After=network.target

[Service]
Type=simple
ExecStart=/usr/bin/python3 /home/<user>/api_server.py
Restart=always
RestartSec=5

[Install]
WantedBy=default.target
EOF

sudo loginctl enable-linger $USER
systemctl --user daemon-reload
systemctl --user enable --now kali-api.service
```

### 2. macOS 端

```bash
# 创建 venv
$HOME/.pyenv/versions/3.12.0/bin/python3.12 -m venv ~/.cache/mcp-kali-workspace/venv
~/.cache/mcp-kali-workspace/venv/bin/pip install requests Flask "mcp>=1.0.0"

# 安装 Playwright（可选）
npm install -g @playwright/mcp
npx playwright install chromium
```

### 3. 配置 MCP

本项目的 `.mcp.json` 已包含 kaliMcp 和 playwright 两个服务器。
复制到你的项目目录，或通过 `claude /config` 手动添加。

### 4. 验证

```bash
# 健康检查
curl -s http://192.168.64.2:5000/health

# 执行命令
curl -s -X POST http://192.168.64.2:5000/api/command \
  -H "Content-Type: application/json" \
  -d '{"command": "which nmap"}'
```

## 文件说明

| 路径 | 说明 |
|------|------|
| `.mcp.json` | Claude Code MCP 服务器配置 |
| `.mcp-kali/mcp-wrapper.sh` | MCP 桥接启动脚本 |
| `.mcp-kali/mcp_server.py` | FastMCP 桥接服务（macOS 运行） |
| `.mcp-kali/api_server.py` | Flask API 服务（Kali VM 运行） |
| `.mcp-kali/requirements.txt` | Python 依赖 |
| `.vscode/mcp.json` | VS Code MCP 配置（可选） |

## 常见问题

- **连接失败** — 检查 Kali VM 是否运行、`systemctl --user status kali-api.service`
- **macOS 代理干扰** — curl 测试时加 `--noproxy '*'`，脚本中设置 `session.trust_env = False`
- **venv Python 版本不对** — 用 pyenv Python 3.12 重建 venv
