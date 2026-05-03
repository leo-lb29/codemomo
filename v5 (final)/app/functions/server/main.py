from typing import Any

from textual.widgets import Static, Button as DialogButton
from textual.containers import Vertical as VerticalContainer
from textual.screen import Screen
from textual.widgets import Button, DataTable, Header, Footer, RichLog
from textual.containers import Horizontal, Vertical
from textual.app import App, ComposeResult
import threading
import socket as socket_module
import time
import pyaudio

from config import (
    PORT_CONTROL, PORT_AUDIO_BROADCAST, PORT_AUDIO_CLIENT,
    BROADCAST_ADDR, CHUNK, FORMAT, CHANNELS, RATE, PYAUDIO_INSTANCE
)


class Serveur:
    def __init__(self):
        self.socket = socket_module.socket(socket_module.AF_INET, socket_module.SOCK_STREAM, proto=socket_module.IPPROTO_TCP)
        self.port_control = PORT_CONTROL
        self.clients = []
        self.clients_demandes_parole = []
        self.speaker_id = None
        self.host_is_speaking = False
        self.client_id_counter = 0
        self.app_ref: Any = None
        self.udp_broadcast_sock = None
        self.udp_receive_sock = None
        self.audio_running = False

    def nettoyer_clients_disconnected(self):
        self.clients = [c for c in self.clients if self.socket_connected(c["socket"])]

    def socket_connected(self, sock):
        try:
            sock.getpeername()
            return True
        except:
            return False

    def envoyer_message(self, client, message_text):
        try:
            client["socket"].send(message_text.encode())
        except (ConnectionAbortedError, ConnectionResetError, BrokenPipeError):
            if client in self.clients:
                self.clients.remove(client)

    def demarrer_serveur(self):
        self.socket.bind(("0.0.0.0", self.port_control))
        self.socket.listen(5)
        self._demarrer_audio()
        while True:
            conn, addr = self.socket.accept()
            self.nettoyer_clients_disconnected()
            threading.Thread(target=self.handle_client, args=(conn, addr), daemon=True).start()

    def handle_client(self, conn, addr):
        try:
            data = conn.recv(1024).decode()
            if data.startswith("PRENOM:"):
                prenom = data.split(":")[1]
                client_id = self.client_id_counter
                self.client_id_counter += 1
                self.clients.append({"id": client_id, "addr": addr, "prenom": prenom, "socket": conn})

                while True:
                    try:
                        data = conn.recv(1024).decode()
                        if not data:
                            break
                        if data == "REQUEST_TO_SPEAK":
                            self.clients_demandes_parole.append((client_id, prenom, addr))
                    except:
                        break

                self.clients = [c for c in self.clients if c["id"] != client_id]
                self.clients_demandes_parole = [(cid, p, ip) for cid, p, ip in self.clients_demandes_parole if cid != client_id]
                
                if self.speaker_id == client_id:
                    self.speaker_id = None
            else:
                conn.close()
        except Exception:
            try:
                conn.close()
            except:
                pass

    # ─── Contrôle de la parole ───────────────────────────────────────────────

    def accepter_parole(self, id_client):
        if self.clients and any(c["id"] == id_client for c in self.clients):
            client = next(c for c in self.clients if c["id"] == id_client)
            self.envoyer_message(client, "SPEAK_ACCEPTED")
            self.clients_demandes_parole = [(cid, p, ip) for cid, p, ip in self.clients_demandes_parole if cid != id_client]
        self.donner_la_parole(id_client)

    def refuser_parole(self, id_client):
        if self.clients and any(c["id"] == id_client for c in self.clients):
            client = next(c for c in self.clients if c["id"] == id_client)
            self.envoyer_message(client, "SPEAK_REJECTED")
            self.clients_demandes_parole = [(cid, p, ip) for cid, p, ip in self.clients_demandes_parole if cid != id_client]

    def reset_speak(self):
        for client in self.clients:
            try:
                self.envoyer_message(client, "RESET_SPEAK")
            except:
                pass
        self.speaker_id = None
        self.host_is_speaking = False

    def prendre_la_parole(self):
        if not self.host_is_speaking:
            if self.speaker_id is not None and self.speaker_id != -1:
                self.retirer_la_parole(self.speaker_id)
            else:
                for client in self.clients:
                    try:
                        self.envoyer_message(client, "RESET_SPEAK")
                    except:
                        pass
            self.host_is_speaking = True
            self.speaker_id = -1
            if self.app_ref is not None:
                self.app_ref.query_one("#btn_host_speak", Button).variant = "success"
                self.app_ref.query_one("#btn_host_speak", Button).label = "Arreter de parler"
        else:
            self.host_is_speaking = False
            self.speaker_id = None
            if self.app_ref is not None:
                self.app_ref.query_one("#btn_host_speak", Button).variant = "default"
                self.app_ref.query_one("#btn_host_speak", Button).label = "Prendre la parole"

    def retirer_la_parole(self, id_client):
        if self.clients and any(c["id"] == id_client for c in self.clients):
            client = next(c for c in self.clients if c["id"] == id_client)
            self.envoyer_message(client, "SPEAKER:0")
        self.speaker_id = None

    def donner_la_parole(self, id_client):
        self.speaker_id = id_client
        self.host_is_speaking = False
        if self.app_ref is not None:
            self.app_ref.query_one("#btn_host_speak", Button).variant = "default"
            self.app_ref.query_one("#btn_host_speak", Button).label = "Prendre la parole"
        if self.clients and any(c["id"] == id_client for c in self.clients):
            client = next(c for c in self.clients if c["id"] == id_client)
            self.envoyer_message(client, "SPEAKER:1")

    def _demarrer_audio(self):

        self._audio_running = True

        self._udp_broadcast_sock = socket_module.socket(socket_module.AF_INET, socket_module.SOCK_DGRAM)
        self._udp_broadcast_sock.setsockopt(socket_module.SOL_SOCKET, socket_module.SO_BROADCAST, 1)

        self._udp_receive_sock = socket_module.socket(socket_module.AF_INET, socket_module.SOCK_DGRAM)
        self._udp_receive_sock.setsockopt(socket_module.SOL_SOCKET, socket_module.SO_REUSEADDR, 1)
        self._udp_receive_sock.bind(("0.0.0.0", PORT_AUDIO_CLIENT))
        self._udp_receive_sock.settimeout(0.5)

        threading.Thread(target=self._thread_capture_micro, daemon=True).start()
        threading.Thread(target=self._thread_recevoir_client, daemon=True).start()

    def _thread_capture_micro(self):

        try:
            stream = PYAUDIO_INSTANCE.open(
                format=FORMAT, channels=CHANNELS, rate=RATE,
                input=True, frames_per_buffer=CHUNK)
        except Exception:
            return

        while self._audio_running:
            try:
                data = stream.read(CHUNK, exception_on_overflow=False)
                if self.host_is_speaking:
                    try:
                        self._udp_broadcast_sock.sendto(data, (BROADCAST_ADDR, PORT_AUDIO_BROADCAST)) # type: ignore
                    except:
                        pass
            except:
                time.sleep(0.01)

        stream.stop_stream()
        stream.close()

    def _thread_recevoir_client(self):

        try:
            stream = PYAUDIO_INSTANCE.open(format=FORMAT, channels=CHANNELS, rate=RATE,   output=True, frames_per_buffer=CHUNK)
        except Exception:
            return

        while self._audio_running:
            try:
                data, _ = self._udp_receive_sock.recvfrom(CHUNK * 2)  # type: ignore
                if self.speaker_id is not None and self.speaker_id != -1:
                    stream.write(data)
            except socket_module.timeout:
                pass
            except:
                time.sleep(0.01)

        stream.stop_stream()
        stream.close()
