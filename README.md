# Claude Usage Dashboard

Monitor all your Claude accounts in one place. Automatically detects Chrome profiles logged into claude.ai and displays real-time usage.

## Features

- 🔍 **Auto-detect**: Scans all Chrome profiles for Claude sessions
- 📊 **Real-time usage**: Session (5h), Weekly (7d), Opus, Sonnet breakdown
- 🔄 **Auto-refresh**: Configurable interval (5s ~ 3600s)
- 🖥️ **Desktop app**: System tray icon with localhost web UI
- 🔒 **Local only**: All data stays on your machine

## Install

### Windows
Download `Claude-Usage-Dashboard-Windows.exe` from [Releases](https://github.com/2ndlifeinc/claude-usage-dashboard-public/releases).

### macOS
Download `Claude-Usage-Dashboard-macOS` from [Releases](https://github.com/2ndlifeinc/claude-usage-dashboard-public/releases).

```bash
chmod +x Claude-Usage-Dashboard-macOS
./Claude-Usage-Dashboard-macOS
```

## How it works

1. Reads Chrome cookie databases (copies to temp file to avoid locks)
2. Decrypts `sessionKey` cookies using OS-level crypto (DPAPI on Windows, Keychain on macOS)
3. Calls Claude.ai API endpoints to fetch usage data
4. Displays everything in a local web dashboard (http://localhost:18080)

## Requirements

- Google Chrome with claude.ai logged in
- Windows 10+ or macOS 12+
- Claude Pro/Max subscription

## License

MIT
