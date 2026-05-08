# Kali MCP + Playwright 项目

Claude Code 连接 Kali Linux VM 的 MCP 配置模板。

## MCP 配置

### Kali MCP

- **配置**: `.mcp.json` → `kaliMcp`
- **Kali VM**: `192.168.64.2:5000`（UTM Shared Network）
- **macOS 桥接**: `.mcp-kali/mcp-wrapper.sh` → `.mcp-kali/mcp_server.py` (FastMCP)
- **Kali 端**: `api_server.py` (Flask)，通过 systemd 自启动

### Playwright MCP

- **安装**: `npm install @playwright/mcp && npx playwright install chromium`
- **配置**: `.mcp.json` → `playwright`

### venv 环境

```bash
# 路径
~/.cache/mcp-kali-workspace/venv

# 重建
$HOME/.pyenv/versions/3.12.0/bin/python3.12 -m venv ~/.cache/mcp-kali-workspace/venv
~/.cache/mcp-kali-workspace/venv/bin/pip install requests Flask "mcp>=1.0.0"
```

### 健康检查

```bash
curl -s --noproxy '*' http://192.168.64.2:5000/health
curl -s --noproxy '*' -X POST http://192.168.64.2:5000/api/command \
  -H "Content-Type: application/json" \
  -d '{"command": "which nmap"}'
```

### 常见问题

- **VM 重启后端口不通** — 检查 systemd 服务：`systemctl --user status kali-api.service`
- **venv Python 版本不对** — 用 pyenv Python 3.12 重建
- **macOS 代理干扰** — 加 `--noproxy '*'`，脚本中 `session.trust_env = False`
- **utmctl 不可用** — 终端会话无法调用（macOS 安全限制），直接进 UTM 控制台操作
