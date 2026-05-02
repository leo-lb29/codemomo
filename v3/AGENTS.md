# Agent Customization Guide for PRJ1401

## Project Overview

**PRJ1401** is a multi-client conference system with real-time audio streaming and speaker management. It's a Python/Textual TUI application where:
- A **host** controls who can speak at any given time
- **Clients** can join the conference, request speaking permission, and stream audio when granted
- Communication uses **TCP** for control messages and **UDP** for audio streaming

## Key Facts for Productivity

### Architecture
```
app/
├── functions/    # Business logic (networking, message protocol, speaker management)
│   ├── client/main.py     # Client-side TCP socket handling
│   └── server/main.py     # Host-side multi-threaded server with client registry
├── main/        # UI layer (Textual-based TUI)
│   ├── client/main.py     # Client UI with pseudo input, request button, logs
│   └── server/main.py     # Host UI with client table, request queue, speaker controls
└── utils/log.py # Logging with color markup
```

### Entry Points
- **Host:** `python host.py`
- **Client:** `python client.py [host_ip]` (default: 192.168.1.156)

### Language & Naming
⚠️ **French throughout:** UI text, method names, variable names are in French (e.g., `prenom`, `demander_la_parole()`, `Serveur`).

### Protocol & Networking
- **TCP (port 5000):** Control messages: `PRENOM:name`, `REQUEST_TO_SPEAK`, `SPEAKER:1/0`, `CLIENT_ID:n`
- **UDP (port 5001):** Audio streaming (44.1kHz, 16-bit mono, 1024-byte chunks)
- **Threading:** Daemon threads for background listeners; `threading.Lock()` protects shared state

### Configuration
All settings (ports, audio params, host IP) are in `config.py`. Modify there for deployment or testing.

### Known Issues
- `app/utils/audio.py` is imported but does not exist — will cause runtime error if audio code is invoked

## Common Tasks

### Add a New Message Type
1. Define protocol string in `app/functions/{client,server}/main.py`
2. Handle both send (if initiator) and receive (in listener thread)
3. Update TUI display in `app/main/{client,server}/main.py`

### Modify Client/Host UI
Use **Textual widgets** in `app/main/{client,server}/main.py`. CSS styling is supported. Widget IDs follow pattern `#btn_action`, `#zone-logs`.

### Adjust Audio Streaming
Audio parameters live in `config.py`. If implementing `app/utils/audio.py`, use PyAudio with config values.

### Debug Networking
- Logs show all received/sent messages
- Client connects to host on `config.HOST_IP:config.TCP_PORT`
- Check firewall if connection fails

## Testing
No test framework is configured. When adding features, consider manual TUI testing or adding pytest if scale grows.
