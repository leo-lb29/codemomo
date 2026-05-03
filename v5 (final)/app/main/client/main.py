from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Button, Header, Static, RichLog, Input
from app.functions.client.main import Client as ClientFunction
from config import CSS_CLIENT, TITLE_CLIENT, SUB_TITLE_CLIENT

class Client(App):
    TITLE = TITLE_CLIENT
    SUB_TITLE = SUB_TITLE_CLIENT
    CSS = CSS_CLIENT

    def __init__(self, host_addr):
        super().__init__()
        self.host_addr = host_addr
        self.is_speaker = False
        self.client_socket = None
        self.mic_active = True
        self.prenom = None
        self.client = ClientFunction(host_addr)
        self.client.app_ref = self

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical(id="container-prenom"):
            yield Static("Entrez votre pseudo:", id="label-prenom")
            yield Input(id="prenom-input", placeholder="Pseudo")
            yield Button("Continuer", id="btn_prenom_continue")
            yield Static("", id="error-prenom")

        with Vertical(id="container-main"):
            with Horizontal(id="layout-principal"):
                with Vertical(id="menu-gauche"):
                    yield Button("Demander la parole", id="btn_request_speak")
                    yield Button("Couper le micro", id="btn_mute_myself")
                    yield Button("Quitter", id="btn_quit")
                with Vertical(id="zone-droite"):
                    yield Static("Recherche de l'hôte...", id="status-box", classes="status-listening")
                    yield RichLog(id="zone-logs", highlight=True, markup=True)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn_prenom_continue":
            prenom_input = self.query_one("#prenom-input", Input)
            if prenom_input.value.strip():
                self.prenom = prenom_input.value
                self.client.se_connecter(self.prenom)
                self.client_socket = True
                self.query_one("#container-prenom").styles.display = "none"
                self.query_one("#container-main").styles.display = "block"
                self.update_status(False)
            else:
                self.query_one("#error-prenom").update("Veuillez entrer votre prénom") # type: ignore

        elif event.button.id == "btn_quit":
            self.exit()

        elif event.button.id == "btn_request_speak":
            if self.client_socket:
                try:
                    self.client.demander_la_parole()
                    btn = self.query_one("#btn_request_speak", Button)
                    btn.variant = "success"
                    btn.disabled = True
                    btn.label = "Requête envoyée"
                    self.add_log("[yellow] Demande de parole envoyée...[/]")
                except Exception as e:
                    self.add_log(f"[red]Erreur: {e}[/]")
            else:
                self.add_log("[red]Non connecté au serveur[/]")

        elif event.button.id == "btn_mute_myself":
            self.mic_active = not self.mic_active
            self.client.set_mic_muted(not self.mic_active)
            if self.mic_active:
                self.query_one("#btn_mute_myself", Button).variant = "default"
                self.query_one("#btn_mute_myself", Button).label = "Couper le micro"
                self.add_log("[green] Micro réactivé[/]")
            else:
                self.query_one("#btn_mute_myself", Button).variant = "error"
                self.query_one("#btn_mute_myself", Button).label = "Réactiver le micro"
                self.add_log("[red] Micro désactivé[/]")

    def add_log(self, text: str):
        self.query_one(RichLog).write(text)

    def reset_speak_request_button(self):
        btn = self.query_one("#btn_request_speak", Button)
        btn.variant = "default"
        btn.disabled = False
        btn.label = "Demander la parole"

    def update_status(self, is_speaking: bool):
        status_box = self.query_one("#status-box", Static)
        if is_speaking:
            status_box.update("On vous entend ! Parlez maintenant...")
            status_box.set_classes("status-speaking")
        else:
            status_box.update("En écoute...")
            status_box.set_classes("status-listening")

    def hote_deconnecte(self):
        try:
            status_box = self.query_one("#status-box", Static)
            status_box.update("Hôte déconnecté, l'app va ce fermer dans quelques secondes")
            status_box.set_classes("status-disconnected")
            self.add_log("[red bold]L'hôte s'est déconnecté. Fermeture dans 3 secondes...[/]")
        except Exception:
            pass

        import threading
        def _quitter():
            import time
            time.sleep(3)
            self.exit()
        threading.Thread(target=_quitter, daemon=True).start()