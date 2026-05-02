import socket as socket_module
import threading
import pyaudio
from textual.widgets import Button
from typing import Any
from config import PORT_AUDIO, PORT_CONTROL



class Client:
    def __init__(self, ip_du_serveur="192.168.10.1"):
        self.port_control = PORT_CONTROL
        self.port_audio = PORT_AUDIO
        self.ip_du_serveur = ip_du_serveur
        self.socket = socket_module.socket(
            socket_module.AF_INET, socket_module.SOCK_STREAM, proto=socket_module.IPPROTO_TCP)
        self.socket_audio_send = socket_module.socket(
            socket_module.AF_INET, socket_module.SOCK_DGRAM, proto=socket_module.IPPROTO_UDP)
        self.socket_audio_recv = socket_module.socket(
            socket_module.AF_INET, socket_module.SOCK_DGRAM, proto=socket_module.IPPROTO_UDP)
        self.socket_audio_recv.setsockopt(socket_module.SOL_SOCKET, socket_module.SO_REUSEADDR, 1)
        self.prenom = None
        self.connected = False
        self.app_ref: Any = None
        self.is_speaking = False
        self.client_id = None
        self.setup_audio()

    def send_message(self, message):
        try:
            if not self.connected:
                self.socket.connect((self.ip_du_serveur, self.port_control))
                self.connected = True
            message_encoded = message.encode()
            self.socket.send(message_encoded)
        except Exception as e:
            print(f"Erreur lors de l'envoi: {e}")

    def setup_audio(self):
        self.socket_audio_recv.setsockopt(socket_module.SOL_SOCKET, socket_module.SO_REUSEADDR, 1)
        self.socket_audio_recv.bind(("0.0.0.0", 5002))
        print("[SETUP AUDIO] Sockets bindés sur port 5002")
        audio = pyaudio.PyAudio()

        stream_send = audio.open(format=pyaudio.paInt16, channels=1,
                                 rate=44100, input=True, frames_per_buffer=1024)
        stream_recv = audio.open(format=pyaudio.paInt16, channels=1,
                                 rate=44100, output=True, frames_per_buffer=1024)

        def envoyer_audio():
            while True:
                try:
                    data = stream_send.read(1024, exception_on_overflow=False)
                    if self.is_speaking:
                        self.socket_audio_send.sendto(data, (self.ip_du_serveur, self.port_audio))
                        if self.app_ref:
                            self.app_ref.add_log("[cyan][AUDIO SEND] Envoi audio au serveur[/]")
                except Exception as e:
                    print(f"Erreur envoi audio: {e}")
                    if self.app_ref:
                        self.app_ref.add_log(f"[red]Erreur envoi audio: {e}[/]")

        def recevoir_audio():
            try:
                while True:
                    data, addr = self.socket_audio_recv.recvfrom(1024)
                    if not data:
                        break
                    if not self.is_speaking:
                        stream_recv.write(data)
                        if self.app_ref:
                            self.app_ref.add_log("[cyan][AUDIO RECV] Audio reçu et joué[/]")
                    else:
                        if self.app_ref:
                            self.app_ref.add_log("[yellow][AUDIO RECV] Audio reçu mais rejeté (en train de parler)[/]")
            except Exception as e:
                print(f"Erreur réception audio: {e}")
                if self.app_ref:
                    self.app_ref.add_log(f"[red]Erreur réception audio: {e}[/]")
            finally:
                stream_send.stop_stream()
                stream_send.close()
                stream_recv.stop_stream()
                stream_recv.close()
                audio.terminate()

        threading.Thread(target=envoyer_audio, daemon=True).start()
        threading.Thread(target=recevoir_audio, daemon=True).start()

    def se_connecter(self, prenom):
        self.prenom = prenom
        self.send_message(f"PRENOM:{prenom}")
        threading.Thread(target=self.recevoir_message, daemon=True).start()

    def recevoir_message(self):
        while True:
            try:
                data = self.socket.recv(1024).decode()
                if data.startswith("CLIENT_ID:"):
                    self.client_id = int(data.split(":")[1])
                elif data == "SPEAKER:1":
                    self.parler()
                elif data == "SPEAKER:0":
                    self.arreter_de_parler()
                elif data == "SPEAK_ACCEPTED":
                    self.parole_acceptee()
                elif data == "SPEAK_REJECTED":
                    self.parole_refusee()
                elif data == "RESET_SPEAK":
                    self.reset_speak()
                else:
                    break
            except Exception as e:
                print(f"Erreur de réception: {e}")
                break

    def demander_la_parole(self):
        self.send_message("REQUEST_TO_SPEAK")

    def couper_mon_micro(self):
        # couper le micro sur mon pc
        pass

    # receive_message
    def parole_acceptee(self):
        # SPEAK_ACCEPTED
        print("Votre demande de parole a été acceptée.")
        if self.app_ref:
            self.app_ref.add_log(
                "[green]Votre demande de parole a été acceptée.[/]")
            self.app_ref.reset_speak_request_button()

    # receive_message
    def parole_refusee(self):
        # SPEAK_REJECTED
        print("Votre demande de parole a été refusée.")
        if self.app_ref:
            self.app_ref.add_log(
                "[red]Votre demande de parole a été refusée.[/]")
            self.app_ref.reset_speak_request_button()

    # receive_message
    def reset_speak(self):
        # RESET_SPEAK
        self.bouton_demander_retourner_style_defaut()

    # receive_message
    def arreter_de_parler(self):
        # SPEAKER:0
        self.is_speaking = False
        print("Vous avez perdu la parole.")
        if self.app_ref:
            self.bouton_demander_retourner_style_defaut()
            self.app_ref.add_log("[yellow]Vous avez perdu la parole.[/]")
            self.app_ref.update_status(False)

    # receive_message
    def parler(self):
        # SPEAKER:1
        self.is_speaking = True
        print("Vous avez la parole !")
        if self.app_ref:
            self.bouton_demander_style_vous_parler()
            self.app_ref.add_log("[green]Vous avez la parole ![/]")
            self.app_ref.update_status(True)

    def bouton_demander_style_vous_parler(self):
        if self.app_ref:
            self.app_ref.query_one("#btn_request_speak",
                                   Button).variant = "default"
            self.app_ref.query_one("#btn_request_speak",
                                   Button).disabled = True
            self.app_ref.query_one("#btn_request_speak",
                                   Button).label = "Vous parlez"

    def bouton_demander_retourner_style_defaut(self):
        if self.app_ref:
            self.app_ref.query_one("#btn_request_speak",
                                   Button).variant = "default"
            self.app_ref.query_one("#btn_request_speak",
                                   Button).disabled = False
            self.app_ref.query_one("#btn_request_speak",
                                   Button).label = "Demander la parole"
