import socket
import threading
import struct
import queue
import sys
import pyaudio
from textual.app import App, ComposeResult
from textual.containers import Vertical
from textual.widgets import Header, Footer, Static, RichLog

from utils.utils import _close_stream, _create_input_stream, _create_output_stream, _handle_audio_message, _handle_control_message, _log_error, _log_info, _log_success, recv_message, send_message

# ── Audio (Identique) ──────────────────────────────────────────────────────────
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
pyaudio_instance = pyaudio.PyAudio()
STRUCTURE_PROTOCOL = "!BI"
# ── État global ────────────────────────────────────────────────────────────────
speaker_lock = threading.Lock()
queue_audio = queue.Queue()


# ── Protocole réseau (Compatibilité) ──────────────────────────────────────────

class Protocol:
    @staticmethod
    def send(sock, ptype, data):
        send_message(sock, ptype, data)

    @staticmethod
    def recv(sock):
        return recv_message(sock)


# ── Workers Audio ──────────────────────────────────────────────────────────────

def mic_worker(sock, app):
    """Capture le micro en continu et envoie si c'est notre tour."""
    stream = _create_input_stream()
    try:
        while True:
            data = stream.read(CHUNK, exception_on_overflow=False)
            with speaker_lock:
                if app.is_speaker:
                    try:
                        Protocol.send(sock, 0x02, data)
                    except Exception:
                        break
    except Exception:
        print("Erreur avec le worker micro")
    finally:
        _close_stream(stream)


def playback_worker():
    """Joue les chunks audio reçus du host."""
    stream = _create_output_stream()
    try:
        while True:
            data = queue_audio.get()
            if data is None:
                break
            stream.write(data)
    except Exception:
        print("Erreur avec le worker playback")
    finally:
        _close_stream(stream)


# ── Logique Réseau (Réception & Connexion) ────────────────────────────────────

def receive_loop(sock, app):
    """Reçoit les messages du host et met à jour l'UI."""
    try:
        while True:
            ptype, data = Protocol.recv(sock)
            if ptype is None:
                _log_error(app, "Connexion perdue avec le host")
                break

            if ptype == 0x01:  # message de contrôle
                if data is None:
                    continue
                msg = data.decode()
                _handle_control_message(app, msg)

            elif ptype == 0x02:  # chunk audio
                _handle_audio_message(data)

    except Exception as e:
        _log_error(app, f"Erreur de réception : {e}")
    finally:
        queue_audio.put(None)


def _connect_to_host(sock, host_addr, app):
    """Établit la connexion au host."""
    try:
        sock.connect((host_addr, 5001))
        _log_info(app, f"Connecté à {host_addr}:5001")
        return True
    except ConnectionRefusedError:
        _log_error(app, f"Impossible de se connecter à {host_addr}:5001")
        return False


def _perform_handshake(sock, app):
    """Effectue le handshake avec le host."""
    Protocol.send(sock, 0x01, "coucou")
    ptype, data = Protocol.recv(sock)
    if ptype is not None and data:
        client_id = int(data.decode().split(':')[1])
        _log_success(app, f"Vous êtes le Client {client_id}")
        _log_info(app, "En attente que l'host vous donne la parole...\n")
        return True
    return False


def _start_audio_workers(sock, app):
    """Démarre les workers audio."""
    threading.Thread(target=playback_worker, daemon=True).start()
    threading.Thread(target=mic_worker, args=(sock, app), daemon=True).start()


def connect_and_run(app, host_addr):
    """Gère la connexion initiale puis lance les workers en arrière-plan."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        if not _connect_to_host(sock, host_addr, app):
            return

        if not _perform_handshake(sock, app):
            return

        _start_audio_workers(sock, app)
        receive_loop(sock, app)

    except Exception as e:
        _log_error(app, f"Erreur lors du handshake: {e}")
    finally:
        sock.close()

# ── Interface Textual ──────────────────────────────────────────────────────────


class Client(App):

    # partie textural pour l'interface user

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

    # partie init de la class

    def __init__(self, host_addr):
        super().__init__()
        # stockage du host
        self.host_addr = host_addr
        # L'état est maintenant géré dans l'App
        self.is_speaker = False

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical():
            # Grand affichage pour indiquer l'état du micro
            yield Static("En attente de connexion...", id="status-box", classes="status-listening")
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
