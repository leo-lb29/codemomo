def _log_connection(app, message, color):
    markup = {
        "cyan": "[bold cyan][*]",
        "red": "[bold red][!]",
        "green": "[bold green][+]",
        "grey": "[bold grey][-]"
    }
    app.call_from_thread(app.add_log, f"{markup.get(color, '')} {message}[/]")


def _log_info(app, message):
    _log_connection(app, message, "cyan")


def _log_error(app, message):
    _log_connection(app, message, "red")


def _log_success(app, message):
    _log_connection(app, message, "green")


def _log_grey(app, message):
    _log_connection(app, message, "grey")
