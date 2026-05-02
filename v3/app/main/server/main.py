import threading
import socket
import pyaudio
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Button, DataTable, Header, RichLog
from textual.screen import Screen
from textual.containers import Vertical as VerticalContainer
from textual.widgets import Static, Button as DialogButton

from app.functions.server.main import Serveur
from config import PORT_AUDIO_OUT, PORT_AUDIO_IN, BROADCAST_ADDR


class ConfirmSpeakScreen(Screen):
    CSS = """
    Screen {
        align: center middle;
    }

    #dialog {
        width: 60;
        height: 10;
        border: solid $primary;
        background: $panel;
        layout: vertical;
    }

    #dialog-title {
        text-align: center;
        margin-bottom: 1;
    }

    #dialog-buttons {
        layout: horizontal;
        height: 3;
        align: center middle;
    }

    .dialog-btn {
        width: 20;
        margin: 0 1;
    }
    """

    def __init__(self, client_id, pseudo, app):
        super().__init__()
        self.client_id = client_id
        self.pseudo = pseudo
        self.host_app = app

    def compose(self) -> ComposeResult:
        with VerticalContainer(id="dialog"):
            yield Static(f"Demande de {self.pseudo} (Client {self.client_id})", id="dialog-title")
            yield Static("Accepter la demande de parole ?")
            with Horizontal(id="dialog-buttons"):
                yield DialogButton("Accepter", id="btn_confirm_accept", variant="success", classes="dialog-btn")
                yield DialogButton("Refuser", id="btn_confirm_reject", variant="error", classes="dialog-btn")

    def on_button_pressed(self, event: DialogButton.Pressed) -> None:
        if event.button.id == "btn_confirm_accept":
            self.host_app.arreter_audio_host()
            self.host_app.serveur.donner_la_parole(self.client_id)
            self.host_app.query_one("#btn_host_speak", Button).variant = "default"
            self.host_app.query_one("#btn_host_speak", Button).label = "Prendre la parole"
            self.dismiss()
        elif event.button.id == "btn_confirm_reject":
            self.host_app.serveur.refuser_parole(self.client_id)
            self.dismiss()


class Host(App):
    TITLE = "PRJ1401"
    SUB_TITLE = "Maître de conférence"
    CSS = """
        #layout-principal { layout: horizontal; }
        #layout-liste { layout: horizontal; height: 70%; }
        #menu-gauche { width: 25%; padding: 1 2 ; }
        #zone-droite { width: 75%; layout: vertical; }
        #zone-gauche { width: 50%; layout: vertical; }
        #zone-droite-droite { width: 50%; layout: vertical; }
        #label-clients { height: 1; text-align: center; }
        #label-demandes { height: 1; text-align: center; }
        #liste-clients { height: 1fr; }
        #liste-demandes { height: 1fr; }
        #zone-logs { height: 30%; }
        Button { width: 100%; margin-bottom: 1; }
        """

    def __init__(self):
        super().__init__()
        self.serveur = Serveur()
        self.audio = None
        self.stream_out = None
        self.stream_in = None
        self.sending_audio = False
        self.receiving_audio = False
        self.socket_audio_in = None
        self.socket_audio_out = None

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal(id="layout-principal"):
            with Vertical(id="menu-gauche"):
                yield Button("Prendre la parole", id="btn_host_speak")
                yield Button("Couper le micro", id="btn_mute_all")
                yield Button("Quitter", id="btn_quit")

            with Vertical(id="zone-droite"):
                with Horizontal(id="layout-liste"):
                    with Vertical(id="zone-gauche"):
                        yield Static("Clients connectés:", id="label-clients")
                        yield DataTable(id="liste-clients")
                    with Vertical(id="zone-droite-droite"):
                        yield Static("Demandes de parole en attente:", id="label-demandes")
                        yield DataTable(id="liste-demandes")
                yield RichLog(id="zone-logs", highlight=True, markup=True)

    def on_mount(self) -> None:
        table_client = self.query_one('#liste-clients', DataTable)
        table_client.cursor_type = "row"
        table_client.add_columns("ID", "Pseudo", "@IP", "Status de la parole")

        table_demandes = self.query_one('#liste-demandes', DataTable)
        table_demandes.cursor_type = "row"
        table_demandes.add_columns("ID", "Pseudo", "@IP")

        threading.Thread(
            target=self.serveur.demarrer_serveur, daemon=True).start()

        self.serveur.demarrer_reception_audio()
        self.setup_host_audio_reception()
        self.set_interval(0.5, self.update_tables)

    def add_log(self, text: str):
        self.query_one(RichLog).write(text)

    def setup_host_audio_reception(self):
        try:
            self.socket_audio_out = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, proto=socket.IPPROTO_UDP)
            self.socket_audio_out.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket_audio_out.bind(("0.0.0.0", PORT_AUDIO_OUT))
            self.audio = pyaudio.PyAudio()
            self.stream_in = self.audio.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=44100,
                output=True,
                frames_per_buffer=1024
            )
            self.receiving_audio = True
            threading.Thread(target=self._recevoir_audio_host, daemon=True).start()
        except Exception as e:
            pass

    def _recevoir_audio_host(self):
        while self.receiving_audio:
            try:
                data, addr = self.socket_audio_out.recvfrom(65535)
                if data and self.stream_in:
                    self.stream_in.write(data)
            except Exception as e:
                if self.receiving_audio:
                    pass
                break

    def setup_host_audio(self):
        try:
            if not self.audio:
                self.audio = pyaudio.PyAudio()
            self.stream_out = self.audio.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=44100,
                input=True,
                frames_per_buffer=1024
            )
            self.sending_audio = True
            threading.Thread(target=self._envoyer_audio_host, daemon=True).start()
        except Exception as e:
            pass

    def _envoyer_audio_host(self):
        socket_audio_in = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, proto=socket.IPPROTO_UDP)
        while self.sending_audio:
            try:
                data = self.stream_out.read(1024, exception_on_overflow=False)
                socket_audio_in.sendto(data, ("127.0.0.1", PORT_AUDIO_IN))
            except Exception as e:
                if self.sending_audio:
                    pass
                break

    def arreter_audio_host(self):
        self.sending_audio = False
        if self.stream_out:
            try:
                self.stream_out.stop_stream()
                self.stream_out.close()
            except:
                pass
            self.stream_out = None

    def update_tables(self):
        self.refresh_clients_table()
        self.refresh_demandes_table()

    def refresh_clients_table(self):
        table_client = self.query_one('#liste-clients', DataTable)
        table_client.clear()
        for client in self.serveur.clients:
            status = "[+] le client parle" if self.serveur.speaker_id == client["id"] else "[-] le client est en écoute"
            table_client.add_row(
                str(client["id"]),
                client["prenom"],
                str(client["addr"][0]),
                status,
                key=str(client["id"])
            )

    def refresh_demandes_table(self):
        table_demandes = self.query_one('#liste-demandes', DataTable)
        table_demandes.clear()
        for client_id, prenom in self.serveur.clients_demandes_parole:
            try:
                table_demandes.add_row(
                    str(client_id), prenom, "", key=str(client_id))
            except:
                pass

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn_host_speak":
            if self.serveur.host_is_speaking:
                self.query_one("#btn_host_speak", Button).variant = "default"
                self.query_one("#btn_host_speak",
                               Button).label = "Prendre la parole"
                self.serveur.host_stop_speaking()
                self.arreter_audio_host()
            else:
                self.query_one("#btn_host_speak", Button).variant = "success"
                self.query_one("#btn_host_speak",
                               Button).label = "Arreter de parler"
                self.serveur.host_start_speaking()
                self.setup_host_audio()

        elif event.button.id == "btn_mute_all":
            self.query_one("#btn_host_speak", Button).variant = "default"
            self.query_one("#btn_host_speak",
                           Button).label = "Prendre la parole"
            self.serveur.reset_speak()
            self.arreter_audio_host()

        elif event.button.id == "btn_quit":
            self.exit()

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        if event.control.id == "liste-demandes":
            if event.row_key.value is not None:
                client_id = int(event.row_key.value)
                self.push_screen(ConfirmSpeakScreen(client_id, "Client", self))

        elif event.control.id == "liste-clients":
            if event.row_key.value is not None:
                client_id = int(event.row_key.value)
                if self.serveur.speaker_id == client_id:
                    self.serveur.retirer_la_parole(client_id)
                else:
                    self.arreter_audio_host()
                    self.query_one("#btn_host_speak",
                                   Button).variant = "default"
                    self.query_one("#btn_host_speak",
                                   Button).label = "Prendre la parole"
                    self.serveur.donner_la_parole(client_id)
