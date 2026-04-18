import threading
from textual.app import App, ComposeResult
from textual.containers import Vertical
from textual.widgets import Header, Footer, Static, RichLog
from utils.utils import connect_and_run


class Client(App):

    TITLE = "PRJ1401"
    SUB_TITLE = "Client"
    CSS = """
    #status-box {
        height: 30%;
        content-align: center middle;
        background: $boost;
        margin: 1 2;
        border: solid $surface;
        text-style: bold;
    }
    #zone-logs {
        height: 70%;
        margin: 0 2 1 2;
        border: solid $primary;
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
    """

    def __init__(self, host_addr):
        super().__init__()
        self.host_addr = host_addr
        self.is_speaker = False

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical():
            yield Static("Recherche de l'hôte...", id="status-box", classes="status-listening")
            yield RichLog(id="zone-logs", highlight=True, markup=True)
        yield Footer()

    def on_mount(self) -> None:
        self.update_status(False)
        threading.Thread(target=connect_and_run, args=(
            self, self.host_addr), daemon=True).start()

    def add_log(self, text: str):
        self.query_one(RichLog).write(text)

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
