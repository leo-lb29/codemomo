import threading
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Button, Header, Static, RichLog, Input
from utils.utils import connect_and_run


class Client(App):
    TITLE = "PRJ1401"
    SUB_TITLE = "Client"
    CSS = """
    #status-box {
        height: 75%;
        content-align: center middle;
        background: $boost;
        margin: 1 2;
        border: solid $surface;
        text-style: bold;
    }
    .status-listening {
        color: gray;
        border: solid gray;
    }
    .status-speaking {
        color: #00ff00;
        background: rgba(0, 255, 0, 0.1);
        border: solid #00ff00;
    }
        #layout-principal { layout: horizontal; }
        #menu-gauche { width: 25%; padding: 1 2 ; }
        #zone-droite { width: 75%; layout: vertical; }
        #zone-logs { height: 100%; }
        Button { width: 100%; margin-bottom: 1; }
        #container-prenom { layout: vertical; align: center middle; border: solid $primary; padding: 2 4; }
        #label-prenom { margin-bottom: 1;  text-align: center; }
        #prenom-input { margin-bottom: 1; width: 100%; }
        #error-prenom { color: $error; margin-bottom: 1; text-align: center; }
        #container-main { display: none; }
    """

    def __init__(self, host_addr):
        super().__init__()
        self.host_addr = host_addr
        self.is_speaker = False
        self.client_socket = None
        self.mic_active = True
        self.prenom = None

    def compose(self) -> ComposeResult:
        yield Header()
        # Écran de saisie du prénom
        with Vertical(id="container-prenom"):
            yield Static("Entrez votre pseudo:", id="label-prenom")
            yield Input(id="prenom-input", placeholder="Pseudo")
            yield Button("Continuer", id="btn_prenom_continue")
            yield Static("", id="error-prenom")
        # Interface principale
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
        from utils.utils import send_message

        if event.button.id == "btn_prenom_continue":
            prenom_input = self.query_one("#prenom-input", Input)
            if prenom_input.value.strip():
                self.prenom = prenom_input.value
                # Afficher l'interface principale
                self.query_one("#container-prenom").styles.display = "none"
                self.query_one("#container-main").styles.display = "block"
                # Démarrer la connexion
                self.update_status(False)
                threading.Thread(target=connect_and_run, args=(
                    self, self.host_addr), daemon=True).start()
            else:
                self.query_one(
                    "#error-prenom").update("⚠️ Veuillez entrer votre prénom")  # type: ignore

        elif event.button.id == "btn_quit":
            self.exit()

        elif event.button.id == "btn_request_speak":
            if self.client_socket:
                try:
                    send_message(self.client_socket, 0x01, "REQUEST_SPEAK")
                    self.query_one("#btn_request_speak",
                                   Button).variant = "success"
                    self.query_one("#btn_request_speak",
                                   Button).disabled = True
                    self.query_one("#btn_request_speak",
                                   Button).label = "Requête envoyée"
                    self.add_log("[yellow]📢 Demande de parole envoyée...[/]")
                except Exception as e:
                    self.add_log(f"[red]Erreur: {e}[/]")
            else:
                self.add_log("[red]Non connecté au serveur[/]")

        elif event.button.id == "btn_mute_myself":
            self.mic_active = not self.mic_active
            if self.mic_active:
                self.query_one("#btn_mute_myself", Button).variant = "default"
                self.query_one("#btn_mute_myself",
                               Button).label = "Couper le micro"
                self.add_log("[green]🎤 Micro réactivé[/]")
            else:
                self.query_one("#btn_mute_myself", Button).variant = "error"
                self.query_one("#btn_mute_myself",
                               Button).label = "Réactiver le micro"
                self.add_log("[red]🔇 Micro désactivé[/]")

    def add_log(self, text: str):
        self.query_one(RichLog).write(text)

    def reset_speak_request_button(self):
        """Réinitialise le bouton de demande de parole après un refus."""
        self.query_one("#btn_request_speak", Button).variant = "default"
        self.query_one("#btn_request_speak", Button).disabled = False
        self.query_one("#btn_request_speak",
                       Button).label = "Demander la parole"

    def update_status(self, is_speaking: bool):
        status_box = self.query_one("#status-box", Static)
        if is_speaking:
            status_box.update("On vous entend ! Parlez maintenant...")
            status_box.remove_class("status-listening")
            status_box.add_class("status-speaking")
        else:
            status_box.update("En écoute...")
            status_box.remove_class("status-speaking")
            status_box.add_class("status-listening")