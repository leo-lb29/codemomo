import threading
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Button, DataTable, Header, Footer, RichLog

from utils.utils import (
    HOST_CLIENTS, HOST_CLIENTS_LOCK,
    HOST_STOP_EVENT, set_speaker_host,
    playback_worker_host, host_speak, server_main
)


class Host(App):
    TITLE = "PRJ1401"
    SUB_TITLE = "Maître de conférence"
    CSS = """
        #layout-principal { layout: horizontal; }
        #menu-gauche { width: 25%; padding: 1 2 ; }
        #zone-droite { width: 75%; layout: vertical; }
        #liste-clients { height: 70%;}
        #zone-logs { height: 30%; }
        Button { width: 100%; margin-bottom: 1; }
        """

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal(id="layout-principal"):
            with Vertical(id="menu-gauche"):
                yield Button("Prendre la parole", id="btn_host_speak")
                yield Button("Couper le micros", id="btn_mute_all")

            with Vertical(id="zone-droite"):
                yield DataTable(id="liste-clients")
                yield RichLog(id="zone-logs", highlight=True, markup=True)
        yield Footer()

    def on_mount(self) -> None:
        # Configurer la table
        table = self.query_one(DataTable)
        table.cursor_type = "row"
        table.add_columns("ID Clients", "Adresse IP", "Statut (Micro)")

        # Lancer les threads d'arrière-plan en passant l'instance `self` (l'app)
        threading.Thread(target=playback_worker_host, daemon=True).start()
        threading.Thread(target=server_main, args=(self,), daemon=True).start()

    # --- Fonctions pour mettre à jour l'UI (appelées depuis les threads) ---
    def add_log(self, text: str):
        self.query_one(RichLog).write(text)

    def refresh_clients_table(self):
        from utils.utils import HOST_SPEAKER_STATE
        table = self.query_one(DataTable)
        table.clear()
        with HOST_CLIENTS_LOCK:
            for _, addr, cid in HOST_CLIENTS:
                status = "[+] le client parle" if HOST_SPEAKER_STATE["id"] == cid else "[-] le client est en écoute"
                table.add_row(str(cid), str(addr[0]), status, key=str(cid))

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

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        self.query_one("#btn_host_speak", Button).variant = "default"
        self.query_one("#btn_host_speak",
                       Button).label = "Prendre la parole"

        if event.row_key.value is not None:
            cid = int(event.row_key.value)
            set_speaker_host(cid, self)
