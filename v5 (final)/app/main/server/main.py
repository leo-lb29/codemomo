import threading
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Button, DataTable, Header, RichLog
from textual.screen import Screen
from textual.containers import Vertical as VerticalContainer
from textual.widgets import Static, Button as DialogButton

from app.functions.server.main import Serveur
from config import CSS_CONFIRM_SPEAK_SCREEN, CSS_HOST, SUB_TITLE_HOST, TITLE_HOST


class ConfirmSpeakScreen(Screen):
    CSS = CSS_CONFIRM_SPEAK_SCREEN

    def __init__(self, client_id, pseudo, app):
        super().__init__()
        self.client_id = client_id
        self.pseudo = pseudo
        self.host_app = app

    def compose(self) -> ComposeResult:
        with VerticalContainer(id="dialog"):
            yield Static(f"Demande de {self.pseudo} (Client {self.client_id})", id="dialog-title")
            yield Static("Accepter la prise de parole ?")
            with Horizontal(id="dialog-buttons"):
                yield DialogButton("Accepter", id="btn_confirm_accept", variant="success", classes="dialog-btn")
                yield DialogButton("Refuser", id="btn_confirm_reject", variant="error", classes="dialog-btn")

    def on_button_pressed(self, event: DialogButton.Pressed) -> None:
        if event.button.id == "btn_confirm_accept":
            self.host_app.serveur.accepter_parole(self.client_id)
            self.host_app.query_one("#btn_host_speak", Button).variant = "default"
            self.host_app.query_one("#btn_host_speak", Button).label = "Prendre la parole"
            try:
                self.host_app.query_one('#liste-demandes', DataTable).remove_row(str(self.client_id))
            except Exception:
                pass
            self.dismiss()
        elif event.button.id == "btn_confirm_reject":
            self.host_app.serveur.refuser_parole(self.client_id)
            try:
                self.host_app.query_one('#liste-demandes', DataTable).remove_row(str(self.client_id))
            except Exception:
                pass
            self.dismiss()


class Host(App):
    TITLE = TITLE_HOST
    SUB_TITLE = SUB_TITLE_HOST
    CSS = CSS_HOST

    def __init__(self):
        super().__init__()
        self.serveur = Serveur()
        self.serveur.app_ref = self

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

        self.set_interval(0.5, self.update_tables)

    def add_log(self, text: str):
        self.query_one(RichLog).write(text)

    def update_tables(self):
        self.refresh_clients_table()
        self.refresh_demandes_table()

    def refresh_clients_table(self):
        table_client = self.query_one('#liste-clients', DataTable)
        table_client.clear()
        for client in self.serveur.clients:
            status = "[+] le client parle" if self.serveur.speaker_id == client["id"] else "[-] le client est en écoute"
            table_client.add_row(str(client["id"]), client["prenom"], str(client["addr"][0]), status, key=str(client["id"]))

    def refresh_demandes_table(self):
        table_demandes = self.query_one('#liste-demandes', DataTable)
        table_demandes.clear()
        for client_id, prenom, ip in self.serveur.clients_demandes_parole:
            try:
                table_demandes.add_row(
                    str(client_id), prenom, str(ip[0]), key=str(client_id))
            except:
                pass

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn_host_speak":
            self.serveur.prendre_la_parole()

        elif event.button.id == "btn_mute_all":
            self.query_one("#btn_host_speak", Button).variant = "default"
            self.query_one("#btn_host_speak",
                           Button).label = "Prendre la parole"
            self.serveur.reset_speak()

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
                    self.query_one("#btn_host_speak",
                                   Button).variant = "default"
                    self.query_one("#btn_host_speak",
                                   Button).label = "Prendre la parole"
                    self.serveur.donner_la_parole(client_id)