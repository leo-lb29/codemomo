import socket as socket_module
import threading
import pyaudio
from textual.widgets import Button
from typing import Any
from config import PORT_AUDIO_OUT, PORT_AUDIO_IN, PORT_CONTROL, CHUNK, FORMAT, CHANNELS, RATE

try:
    from ctypes import *
    ERROR_HANDLER_FUNC = CFUNCTYPE(None, c_char_p, c_int, c_char_p, c_int, c_char_p)
    def py_error_handler(filename, line, function, err, fmt):
        pass
    c_error_handler = ERROR_HANDLER_FUNC(py_error_handler)
    try:
        asound = cdll.LoadLibrary('libasound.so.2')
        asound.snd_lib_error_set_handler(c_error_handler)
    except:
        pass
except:
    pass


class Client:
    def __init__(self, ip_du_serveur="192.168.10.1"):
        self.port_control = PORT_CONTROL
        self.port_audio_out = PORT_AUDIO_OUT
        self.port_audio_in = PORT_AUDIO_IN
        self.ip_du_serveur = ip_du_serveur
        self.socket = socket_module.socket(socket_module.AF_INET, socket_module.SOCK_STREAM, proto=socket_module.IPPROTO_TCP)
        self.socket_audio_out = socket_module.socket(socket_module.AF_INET, socket_module.SOCK_DGRAM, proto=socket_module.IPPROTO_UDP)
        self.socket_audio_in = socket_module.socket(socket_module.AF_INET, socket_module.SOCK_DGRAM, proto=socket_module.IPPROTO_UDP)
        self.prenom = None
        self.connected = False
        self.app_ref: Any = None
        self.audio = None
        self.stream_in = None
        self.stream_out = None
        self.receiving_audio = False
        self.sending_audio = False

    def setup_audio_reception(self):
        try:
            self.socket_audio_out.setsockopt(socket_module.SOL_SOCKET, socket_module.SO_REUSEADDR, 1)
            self.socket_audio_out.bind(("0.0.0.0", self.port_audio_out))
            self.audio = pyaudio.PyAudio()
            self.stream_in = self.audio.open(
                format=FORMAT,
                channels=CHANNELS,
                rate=RATE,
                output=True,
                frames_per_buffer=CHUNK
            )
            self.receiving_audio = True
            threading.Thread(target=self.recevoir_audio, daemon=True).start()
        except Exception as e:
            pass

    def setup_audio_emission(self):
        try:
            if not self.audio:
                self.audio = pyaudio.PyAudio()
            self.stream_out = self.audio.open(
                format=FORMAT,
                channels=CHANNELS,
                rate=RATE,
                input=True,
                frames_per_buffer=CHUNK
            )
            self.sending_audio = True
            threading.Thread(target=self.envoyer_audio, daemon=True).start()
        except Exception as e:
            pass

    def recevoir_audio(self):
        while self.receiving_audio:
            try:
                data, addr = self.socket_audio_out.recvfrom(65535)
                if data and self.stream_in and not self.sending_audio:
                    self.stream_in.write(data)
            except Exception as e:
                if self.receiving_audio:
                    pass
                break

    def envoyer_audio(self):
        while self.sending_audio:
            try:
                data = self.stream_out.read(CHUNK, exception_on_overflow=False)
                self.socket_audio_in.sendto(data, (self.ip_du_serveur, self.port_audio_in))
            except Exception as e:
                break

    def arreter_emission_audio(self):
        self.sending_audio = False
        if self.stream_out:
            try:
                self.stream_out.stop_stream()
                self.stream_out.close()
            except:
                pass
            self.stream_out = None

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
        self.setup_audio_reception()
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
                    self.reset_speak()
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

    def reset_speak(self):
        self.arreter_emission_audio()
        self.bouton_demander_retourner_style_defaut()

    def arreter_de_parler(self):
        self.arreter_emission_audio()
        if self.app_ref:
            self.bouton_demander_retourner_style_defaut()
            self.app_ref.add_log("[yellow]Vous avez perdu la parole.[/]")
            self.app_ref.update_status(False)

    def parler(self):
        self.setup_audio_emission()
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

    def nettoyer(self):
        self.receiving_audio = False
        self.sending_audio = False
        if self.stream_in:
            self.stream_in.stop_stream()
            self.stream_in.close()
        if self.stream_out:
            self.stream_out.stop_stream()
            self.stream_out.close()
        if self.audio:
            self.audio.terminate()
        if self.socket_audio_out:
            self.socket_audio_out.close()
        if self.socket_audio_in:
            self.socket_audio_in.close()
        if self.socket:
            self.socket.close()