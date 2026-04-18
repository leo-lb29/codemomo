import threading
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Button, DataTable, Header, Footer, RichLog
from textual.screen import Screen
from textual.containers import Vertical as VerticalContainer
from textual.widgets import Static, Button as DialogButton

from utils.utils import (
    HOST_CLIENTS, HOST_CLIENTS_LOCK,
    HOST_STOP_EVENT, set_speaker_host,
    playback_worker_host, host_speak, server_main,
    accept_speak_request, reject_speak_request, reset_all_speak_requests
)


class ConfirmSpeakScreen(Screen):
    """Popup de confirmation pour accepter/refuser la parole."""
    
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
    
    def __init__(self, cid, pseudo, app):
        super().__init__()
        self.cid = cid
        self.pseudo = pseudo
        self.app_ref = app
    
    def compose(self) -> ComposeResult:
        with VerticalContainer(id="dialog"):
            yield Static(f"Demande de {self.pseudo} (Client {self.cid})", id="dialog-title")
            yield Static("Accepter la demande de parole ?")
            with Horizontal(id="dialog-buttons"):
                yield DialogButton("Accepter", id="btn_confirm_accept", variant="success", classes="dialog-btn")
                yield DialogButton("Refuser", id="btn_confirm_reject", variant="error", classes="dialog-btn")
    
    def on_button_pressed(self, event: DialogButton.Pressed) -> None:
        if event.button.id == "btn_confirm_accept":
            accept_speak_request(self.cid, self.app_ref)
            self.dismiss()
        elif event.button.id == "btn_confirm_reject":
            reject_speak_request(self.cid, self.app_ref)
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

        # yield Footer()

    def on_mount(self) -> None:
        # Configurer la table
        table_client = self.query_one('#liste-clients', DataTable)
        table_client.cursor_type = "row"
        table_client.add_columns(
            "ID Clients", "pseudo", "Adresse IP", "Statut (Micro)")

        table_demandes = self.query_one('#liste-demandes', DataTable)
        table_demandes.cursor_type = "row"
        table_demandes.add_columns(
            "ID Clients", "pseudo", "Adresse IP")

        # Lancer les threads d'arrière-plan en passant l'instance `self` (l'app)
        threading.Thread(target=playback_worker_host, daemon=True).start()
        threading.Thread(target=server_main, args=(self,), daemon=True).start()

    # --- Fonctions pour mettre à jour l'UI (appelées depuis les threads) ---
    def add_log(self, text: str):
        self.query_one(RichLog).write(text)

    def refresh_clients_table(self):
        from utils.utils import HOST_SPEAKER_STATE
        table_client = self.query_one('#liste-clients', DataTable)
        table_client.clear()
        with HOST_CLIENTS_LOCK:
            for _, addr, cid, prenom in HOST_CLIENTS:
                status = "[+] le client parle" if HOST_SPEAKER_STATE["id"] == cid else "[-] le client est en écoute"
                table_client.add_row(str(cid), prenom, str(addr[0]), status, key=str(cid))

    def refresh_demandes_table(self, demandes):
        table_demandes = self.query_one('#liste-demandes', DataTable)
        table_demandes.clear()
        for item in demandes:
            if isinstance(item, tuple) and len(item) >= 2:
                cid, addr = item[0], item[1]
                pseudo = f"Client {cid}"
                table_demandes.add_row(str(cid), pseudo, str(
                    addr[0]), key=str(cid))

    # --- Événements UI ---
    def on_button_pressed(self, event: Button.Pressed) -> None:
        from utils.utils import HOST_SPEAKER_STATE
        if event.button.id == "btn_host_speak":
            if HOST_SPEAKER_STATE["id"] == -1:
                # Arrêter de parler
                HOST_STOP_EVENT.set()
                set_speaker_host(None, self)
                self.query_one("#btn_host_speak", Button).variant = "default"
                self.query_one("#btn_host_speak",
                               Button).label = "Prendre la parole"
                set_speaker_host(None, self)
            else:
                # Commencer à parler
                set_speaker_host(-1, self)
                self.query_one("#btn_host_speak", Button).variant = "success"
                self.query_one("#btn_host_speak",
                               Button).label = "Arreter de parler"
                HOST_STOP_EVENT.clear()
                threading.Thread(target=host_speak, args=(
                    self,), daemon=True).start()

        elif event.button.id == "btn_mute_all":
            self.query_one("#btn_host_speak", Button).variant = "default"
            self.query_one("#btn_host_speak",
                           Button).label = "Prendre la parole"
            HOST_STOP_EVENT.set()
            set_speaker_host(None, self)
            reset_all_speak_requests(self)

        elif event.button.id == "btn_quit":
            HOST_STOP_EVENT.set()
            self.exit()

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        # Vérifier quelle table a été cliquée
        if event.control.id == "liste-demandes":
            # Clic sur une demande de parole
            if event.row_key.value is not None:
                cid = int(event.row_key.value)
                # Chercher le pseudo du client
                from utils.utils import HOST_SPEAK_REQUESTS, HOST_SPEAK_REQUESTS_LOCK
                with HOST_SPEAK_REQUESTS_LOCK:
                    pseudo = None
                    for c, addr, _ in HOST_SPEAK_REQUESTS:
                        if c == cid:
                            pseudo = "Client"  # On peut améliorer ça later
                            break
                
                # Afficher la popup
                self.push_screen(ConfirmSpeakScreen(cid, pseudo or "Client", self))
        
        elif event.control.id == "liste-clients":
            # Clic sur un client de la liste (toggle pour retirer/donner la parole)
            if event.row_key.value is not None:
                from utils.utils import HOST_SPEAKER_STATE
                cid = int(event.row_key.value)
                
                # Si ce client a déjà la parole, la retirer
                if HOST_SPEAKER_STATE["id"] == cid:
                    set_speaker_host(None, self)
                else:
                    # Sinon, lui donner
                    self.query_one("#btn_host_speak", Button).variant = "default"
                    self.query_one("#btn_host_speak",
                                   Button).label = "Prendre la parole"
                    set_speaker_host(cid, self)