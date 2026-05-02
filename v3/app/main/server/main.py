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
            self.host_app.serveur.donner_la_parole(self.client_id)
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

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal(id="layout-principal"):
            with Vertical(id="menu-gauche"):
                yield Button("Prendre la parole", id="btn_host_speak")
                yield Button("Couper le micros", id="btn_mute_all")
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

        self.setup_audio_broadcast()
        self.setup_audio_receiver()
        self.set_interval(0.5, self.update_tables)

    def add_log(self, text: str):
        self.query_one(RichLog).write(text)

    def setup_audio_broadcast(self):
        socket_signal = socket.socket(
            socket.AF_INET, socket.SOCK_DGRAM, proto=socket.IPPROTO_UDP)
        socket_signal.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        capture_micro = pyaudio.PyAudio()
        stream = capture_micro.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=44100,
            input=True,
            frames_per_buffer=1024
        )

        def envoyer_audio():
            while True:
                data = stream.read(512, exception_on_overflow=False)
                socket_signal.sendto(data, ("192.168.1.255", 5002))

        threading.Thread(target=envoyer_audio, daemon=True).start()

    def setup_audio_receiver(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(("0.0.0.0", 5000))
        audio = pyaudio.PyAudio()
        stream = audio.open(format=pyaudio.paInt16, channels=1,
                            rate=44100, output=True, frames_per_buffer=1024)

        def recevoir_audio():
            try:
                while True:
                    data, addr = sock.recvfrom(1024)
                    if not data:
                        break
                    stream.write(data)
            except KeyboardInterrupt:
                pass
            finally:
                sock.close()
                stream.stop_stream()
                stream.close()
                audio.terminate()

        threading.Thread(target=recevoir_audio, daemon=True).start()

    def update_tables(self):
        self.refresh_clients_table()
        self.refresh_demandes_table()

    def refresh_clients_table(self):
        table_client = self.query_one('#liste-clients', DataTable)
        table_client.clear()
        for conn, addr, client_id, prenom in self.serveur.clients:
            status = "[+] le client parle" if self.serveur.speaker_id == client_id else "[-] le client est en écoute"
            table_client.add_row(str(client_id), prenom, str(
                addr[0]), status, key=str(client_id))

    def refresh_demandes_table(self):
        table_demandes = self.query_one('#liste-demandes', DataTable)
        table_demandes.clear()
        for client_id, prenom in self.serveur.clients_demandes_parole:
            table_demandes.add_row(
                str(client_id), prenom, "", key=str(client_id))

    # --- Événements UI ---
    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn_host_speak":
            if self.serveur.speaker_id is not None:
                self.query_one("#btn_host_speak", Button).variant = "default"
                self.query_one("#btn_host_speak",
                               Button).label = "Prendre la parole"
            else:
                # Commencer à parler
                self.query_one("#btn_host_speak", Button).variant = "success"
                self.query_one("#btn_host_speak",
                               Button).label = "Arreter de parler"

        elif event.button.id == "btn_mute_all":
            self.query_one("#btn_host_speak", Button).variant = "default"
            self.query_one("#btn_host_speak",
                           Button).label = "Prendre la parole"
            self.serveur.reset_speak()

        elif event.button.id == "btn_quit":
            self.exit()
        pass

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
                    self.query_one("#btn_host_speak",
                                   Button).variant = "default"
                    self.query_one("#btn_host_speak",
                                   Button).label = "Prendre la parole"
                    self.serveur.donner_la_parole(client_id)
