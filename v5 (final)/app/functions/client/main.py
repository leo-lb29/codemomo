import socket as socket_module
import threading
import time
from textual.widgets import Button
from typing import Any
from config import PORT_CONTROL, PORT_AUDIO_BROADCAST, PORT_AUDIO_CLIENT, CHUNK, FORMAT, CHANNELS, RATE, PYAUDIO_INSTANCE

class Client:
    def __init__(self, ip_du_serveur="192.168.1.156"):
        self.port_control = PORT_CONTROL
        self.ip_du_serveur = ip_du_serveur
        self.socket = socket_module.socket(socket_module.AF_INET, socket_module.SOCK_STREAM, proto=socket_module.IPPROTO_TCP)
        self.prenom = None
        self.connected = False
        self.is_speaker = False
        self.mic_muted = False
        self.app_ref: Any = None

        self.udp_send_sock = None
        self.udp_listen_sock = None
        self.audio_running = False

    def send_message(self, message):
        try:
            if not self.connected:
                self.socket.connect((self.ip_du_serveur, self.port_control))
                self.connected = True
            self.socket.send(message.encode())
        except Exception:
            pass

    def se_connecter(self, prenom):
        self.prenom = prenom
        self.send_message(f"PRENOM:{prenom}")
        self._demarrer_audio()
        threading.Thread(target=self.recevoir_message, daemon=True).start()

    def recevoir_message(self):
        while True:
            try:
                data = self.socket.recv(1024).decode()
                if not data:
                    break
                if data == "SPEAKER:1":
                    self.parler()
                elif data == "SPEAKER:0":
                    self.arreter_de_parler()
                elif data == "SPEAK_ACCEPTED":
                    self.parole_acceptee()
                elif data == "SPEAK_REJECTED":
                    self.parole_refusee()
                elif data == "RESET_SPEAK":
                    self.arreter_de_parler()
            except Exception:
                break

        self._audio_running = False
        if self.app_ref is not None:
            try:
                self.app_ref.call_from_thread(self.app_ref.hote_deconnecte)
            except Exception:
                pass

    def demander_la_parole(self):
        self.send_message("REQUEST_TO_SPEAK")

    def parole_acceptee(self):
        if self.app_ref:
            self.app_ref.add_log(
                "[green]Votre demande de parole a été acceptée.[/]")
            self.app_ref.reset_speak_request_button()

    def parole_refusee(self):
        if self.app_ref:
            self.app_ref.add_log(
                "[red]Votre demande de parole a été refusée.[/]")
            self.app_ref.reset_speak_request_button()

    def arreter_de_parler(self):
        self.is_speaker = False
        if self.app_ref:
            self.bouton_demander_retourner_style_defaut()
            self.app_ref.add_log("[yellow]Vous avez perdu la parole.[/]")
            self.app_ref.update_status(False)

    def parler(self):
        self.is_speaker = True
        if self.app_ref:
            self.bouton_demander_style_vous_parler()
            self.app_ref.add_log("[green]Vous avez la parole ![/]")
            self.app_ref.update_status(True)

    def set_mic_muted(self, muted: bool):
        self.mic_muted = muted

    def bouton_demander_style_vous_parler(self):
        if self.app_ref:
            btn = self.app_ref.query_one("#btn_request_speak", Button)
            btn.variant = "default"
            btn.disabled = True
            btn.label = "Vous parlez"

    def bouton_demander_retourner_style_defaut(self):
        if self.app_ref:
            btn = self.app_ref.query_one("#btn_request_speak", Button)
            btn.variant = "default"
            btn.disabled = False
            btn.label = "Demander la parole"

    def _demarrer_audio(self):
        self._audio_running = True
        self._udp_send_sock = socket_module.socket(socket_module.AF_INET, socket_module.SOCK_DGRAM)
        self._udp_listen_sock = socket_module.socket(socket_module.AF_INET, socket_module.SOCK_DGRAM)
        self._udp_listen_sock.setsockopt(socket_module.SOL_SOCKET, socket_module.SO_REUSEADDR, 1)
        self._udp_listen_sock.bind(("", PORT_AUDIO_BROADCAST))
        self._udp_listen_sock.settimeout(0.5)

        threading.Thread(target=self._thread_envoi_micro, daemon=True).start()
        threading.Thread(target=self._thread_ecoute_broadcast, daemon=True).start()

    def _thread_envoi_micro(self):
        try:
            stream = PYAUDIO_INSTANCE.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)
        except Exception:
            return

        while self._audio_running:
            try:
                data = stream.read(CHUNK, exception_on_overflow=False)
                if self.is_speaker and not self.mic_muted:
                    try:
                        self._udp_send_sock.sendto(data, (self.ip_du_serveur, PORT_AUDIO_CLIENT)) # type: ignore 
                    except:
                        pass
            except:
                time.sleep(0.01)

        stream.stop_stream()
        stream.close()

    def _thread_ecoute_broadcast(self):
        try:
            stream = PYAUDIO_INSTANCE.open(
                format=FORMAT, channels=CHANNELS, rate=RATE,
                output=True, frames_per_buffer=CHUNK)
        except Exception:
            return

        while self._audio_running:
            try:
                data, _ = self._udp_listen_sock.recvfrom(CHUNK * 2) # type: ignore
                if not self.is_speaker:
                    stream.write(data)
            except socket_module.timeout:
                pass
            except:
                time.sleep(0.01)

        stream.stop_stream()
        stream.close()