"""
CLIENT - Rejoindre une session de parole (Interface Textual)
Usage : python client.py [adresse_host]
        python client.py 192.168.1.10
"""

import socket
import threading
import struct
import queue
import sys
import pyaudio
from textual.app import App, ComposeResult
from textual.containers import Vertical
from textual.widgets import Header, Footer, Static, RichLog

# ── Audio (Identique) ──────────────────────────────────────────────────────────
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
pa = pyaudio.PyAudio()

# ── État global ────────────────────────────────────────────────────────────────
speaker_lock = threading.Lock()
audio_q = queue.Queue()

# ── Protocole réseau (Identique) ──────────────────────────────────────────────


def send(sock, ptype, data):
    if isinstance(data, str):
        data = data.encode()
    sock.sendall(struct.pack('!BI', ptype, len(data)) + data)


def recv(sock):
    def exact(n):
        buf = b''
        while len(buf) < n:
            chunk = sock.recv(n - len(buf))
            if not chunk:
                return None
            buf += chunk
        return buf
    header = exact(5)
    if not header:
        return None, None
    ptype, length = struct.unpack('!BI', header)
    return ptype, exact(length)

# ── Workers Audio ──────────────────────────────────────────────────────────────


def mic_worker(sock, app):
    """Capture le micro en continu et envoie si c'est notre tour."""
    stream = pa.open(format=FORMAT, channels=CHANNELS, rate=RATE,
                     input=True, frames_per_buffer=CHUNK)
    try:
        while True:
            data = stream.read(CHUNK, exception_on_overflow=False)
            with speaker_lock:
                if app.is_speaker:
                    try:
                        send(sock, 0x02, data)
                    except Exception:
                        break
    except Exception:
        pass
    finally:
        stream.stop_stream()
        stream.close()


def playback_worker():
    """Joue les chunks audio reçus du host."""
    stream = pa.open(format=FORMAT, channels=CHANNELS, rate=RATE,
                     output=True, frames_per_buffer=CHUNK)
    try:
        while True:
            data = audio_q.get()
            if data is None:
                break
            stream.write(data)
    finally:
        stream.stop_stream()
        stream.close()

# ── Logique Réseau (Réception & Connexion) ────────────────────────────────────


def receive_loop(sock, app):
    """Reçoit les messages du host et met à jour l'UI."""
    try:
        while True:
            ptype, data = recv(sock)
            if ptype is None:
                app.call_from_thread(
                    app.add_log, "[bold red][!] Connexion perdue avec le host[/]")
                break

            if ptype == 0x01:                       # message de contrôle
                if data is None:
                    continue
                msg = data.decode()
                if msg == "SPEAKER:1":
                    with speaker_lock:
                        app.is_speaker = True
                    # Met à jour l'affichage
                    app.call_from_thread(app.update_status, True)
                    app.call_from_thread(
                        app.add_log, "[bold green][+] C'est votre tour de parler ![/]")
                elif msg == "SPEAKER:0":
                    with speaker_lock:
                        app.is_speaker = False
                    # Met à jour l'affichage
                    app.call_from_thread(app.update_status, False)
                    app.call_from_thread(
                        app.add_log, "[bold grey][-] En écoute...[/]")

            elif ptype == 0x02:                     # chunk audio
                audio_q.put(data)

    except Exception as e:
        app.call_from_thread(
            app.add_log, f"[bold red][!] Erreur de réception : {e}[/]")
    finally:
        audio_q.put(None)


def connect_and_run(app, host_addr):
    """Gère la connexion initiale puis lance les workers en arrière-plan."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.connect((host_addr, 5001))
        app.call_from_thread(
            app.add_log, f"[bold cyan][*] Connecté à {host_addr}:5001[/]")
    except ConnectionRefusedError:
        app.call_from_thread(
            app.add_log, f"[bold red][!] Impossible de se connecter à {host_addr}:5001[/]")
        return

    # Handshake
    try:
        send(sock, 0x01, "coucou")
        ptype, data = recv(sock)
        if ptype is not None and data:
            client_id = int(data.decode().split(':')[1])
            app.call_from_thread(
                app.add_log, f"[bold green][+] Vous êtes le Client {client_id}[/]")
            app.call_from_thread(
                app.add_log, "[*] En attente que l'host vous donne la parole...\n")

            # Lancement des threads audio et réception
            threading.Thread(target=playback_worker, daemon=True).start()
            threading.Thread(target=mic_worker, args=(
                sock, app), daemon=True).start()

            # Bloque ce thread (qui est déjà en arrière-plan) pour écouter
            receive_loop(sock, app)
    except Exception as e:
        app.call_from_thread(
            app.add_log, f"[bold red][!] Erreur lors du handshake: {e}[/]")
    finally:
        sock.close()

# ── Interface Textual ──────────────────────────────────────────────────────────


class ClientDashboard(App):
    TITLE = "PRJ1401"
    SUB_TITLE = "Client"

    CSS = """
    #status-box {
        height: 30%;
        content-align: center middle;
        background: $boost;
        margin: 1 2;
        border: solid $surface;
        text-style: bold;
    }
    #zone-logs {
        height: 70%;
        margin: 0 2 1 2;
        border: solid $primary;
    }
    .status-listening {
        color: gray;
        border: solid gray;
    }
    .status-speaking {
        color: #00ff00;
        background: rgba(0, 255, 0, 0.1);
        border: solid #00ff00;
    }
    """

    def __init__(self, host_addr):
        super().__init__()
        self.host_addr = host_addr
        self.is_speaker = False  # L'état est maintenant géré dans l'App

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical():
            # Bannière bien visible pour l'état du micro
            yield Static("🎧 En attente de connexion...", id="status-box", classes="status-listening")
            # Zone de logs
            yield RichLog(id="zone-logs", highlight=True, markup=True)
        yield Footer()

    def on_mount(self) -> None:
        self.update_status(False)  # Force l'état visuel initial
        # Lancer la connexion réseau dans un thread séparé pour ne pas bloquer l'UI
        threading.Thread(target=connect_and_run, args=(
            self, self.host_addr), daemon=True).start()

    # --- Fonctions pour mettre à jour l'UI depuis d'autres threads ---
    def add_log(self, text: str):
        self.query_one(RichLog).write(text)

    def update_status(self, is_speaking: bool):
        status_box = self.query_one("#status-box", Static)
        if is_speaking:
            status_box.update("🎙️ C'EST VOTRE TOUR DE PARLER ! 🎙️")
            status_box.remove_class("status-listening")
            status_box.add_class("status-speaking")
        else:
            status_box.update("🎧 En écoute... le micro est fermé 🎧")
            status_box.remove_class("status-speaking")
            status_box.add_class("status-listening")


if __name__ == '__main__':
    # Récupérer l'adresse IP passée en argument ou utiliser localhost par défaut
    target_ip = sys.argv[1] if len(sys.argv) > 1 else '192.168.1.177'
    app = ClientDashboard(target_ip)
    app.run()
