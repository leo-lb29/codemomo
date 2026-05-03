import socket as socket_module
import threading
import pyaudio
from textual.widgets import Button
from typing import Any
from config import PORT_CONTROL, CHUNK, FORMAT, CHANNELS, RATE

class Client:
    def __init__(self, ip_du_serveur="192.168.1.156"):
        self.port_control = PORT_CONTROL
        self.ip_du_serveur = ip_du_serveur
        self.socket = socket_module.socket(socket_module.AF_INET, socket_module.SOCK_STREAM, proto=socket_module.IPPROTO_TCP)
        self.prenom = None
        self.connected = False
        self.app_ref: Any = None


    def send_message(self, message):
        try:
            if not self.connected:
                self.socket.connect((self.ip_du_serveur, self.port_control))
                self.connected = True
            message_encoded = message.encode()
            self.socket.send(message_encoded)
        except Exception as e:
            pass

    def se_connecter(self, prenom):
        self.prenom = prenom
        self.send_message(f"PRENOM:{prenom}")
        threading.Thread(target=self.recevoir_message, daemon=True).start()

    def recevoir_message(self):
        while True:
            try:
                data = self.socket.recv(1024).decode()
                if data == "SPEAKER:1":
                    self.parler()
                elif data == "SPEAKER:0":
                    self.arreter_de_parler()
                elif data == "SPEAK_ACCEPTED":
                    self.parole_acceptee()
                elif data == "SPEAK_REJECTED":
                    self.parole_refusea()
                elif data == "RESET_SPEAK":
                    self.arreter_de_parler()
                else:
                    break
            except Exception as e:
                break

    def demander_la_parole(self):
        self.send_message("REQUEST_TO_SPEAK")

    def couper_mon_micro(self):
        pass

    def parole_acceptee(self):
        if self.app_ref:
            self.app_ref.add_log(
                "[green]Votre demande de parole a été acceptée.[/]")
            self.app_ref.reset_speak_request_button()

    def parole_refusea(self):
        if self.app_ref:
            self.app_ref.add_log(
                "[red]Votre demande de parole a été refusée.[/]")
            self.app_ref.reset_speak_request_button()



    def arreter_de_parler(self):
        if self.app_ref:
            self.bouton_demander_retourner_style_defaut()
            self.app_ref.add_log("[yellow]Vous avez perdu la parole.[/]")
            self.app_ref.update_status(False)

    def parler(self):
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
