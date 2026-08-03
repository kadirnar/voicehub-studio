"""Linux desktop/server launcher for VoiceHub Studio."""

from __future__ import annotations

import argparse
import os
import socket
import threading
import time
import urllib.request
import webbrowser


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run the local VoiceHub Studio application."
    )
    parser.add_argument(
        "--host", default=None, help="Bind host (defaults to the saved setting)."
    )
    parser.add_argument(
        "--port",
        type=int,
        default=None,
        help="Bind port (defaults to the saved setting).",
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--window", action="store_true", help="Open the optional native webview window."
    )
    mode.add_argument("--browser", action="store_true", help="Open the system browser.")
    mode.add_argument(
        "--server", action="store_true", help="Run without opening a user interface."
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable development logging and webview tools.",
    )
    return parser


def _available_port(host: str, requested: int) -> int:
    for port in range(requested, min(65_536, requested + 50)):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
            try:
                probe.bind((host, port))
                return port
            except OSError:
                continue
    raise RuntimeError(f"No available port was found near {requested}.")


def _wait_until_ready(url: str, timeout: float = 30.0) -> None:
    deadline = time.monotonic() + timeout
    last_error: Exception | None = None
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(f"{url}/api/health", timeout=1) as response:
                if response.status == 200:
                    return
        except Exception as error:
            last_error = error
        time.sleep(0.15)
    raise RuntimeError(
        f"VoiceHub Studio did not start within {timeout:g} seconds: {last_error}"
    )


def _serve_forever(app, host: str, port: int, debug: bool) -> None:
    import uvicorn

    uvicorn.run(app, host=host, port=port, log_level="debug" if debug else "info")


def main() -> None:
    arguments = _parser().parse_args()
    from voicehub_studio.app import app

    state = app.state.studio
    settings = state.settings.load()
    host = arguments.host or settings.bind_host
    requested_port = arguments.port or settings.port
    if (
        host not in {"127.0.0.1", "localhost", "::1"}
        and os.environ.get("VOICEHUB_STUDIO_ALLOW_REMOTE") != "1"
    ):
        raise SystemExit(
            "Refusing a non-loopback bind without VOICEHUB_STUDIO_ALLOW_REMOTE=1. "
            "The local API has no remote authentication layer."
        )
    selected_mode = (
        "window"
        if arguments.window
        else "browser"
        if arguments.browser
        else "server"
        if arguments.server
        else settings.open_mode
    )
    if selected_mode == "server":
        _serve_forever(app, host, requested_port, arguments.debug)
        return

    port = _available_port(host, requested_port)
    import uvicorn

    configuration = uvicorn.Config(
        app,
        host=host,
        port=port,
        log_level="debug" if arguments.debug else "warning",
    )
    server = uvicorn.Server(configuration)
    thread = threading.Thread(
        target=server.run, name="voicehub-studio-server", daemon=True
    )
    thread.start()
    url = f"http://{host}:{port}"
    try:
        _wait_until_ready(url)
        if selected_mode == "window":
            try:
                import webview

                webview.create_window(
                    "VoiceHub Studio",
                    url,
                    width=1480,
                    height=940,
                    min_size=(1080, 720),
                    background_color="#0b0d10",
                    text_select=True,
                )
                webview.start(debug=arguments.debug, private_mode=False)
            except Exception as error:
                print(
                    "The native webview is unavailable; opening VoiceHub Studio in your "
                    f"browser instead ({error})."
                )
                webbrowser.open(url)
                while thread.is_alive():
                    time.sleep(0.5)
        else:
            webbrowser.open(url)
            print(f"VoiceHub Studio is running at {url}. Press Ctrl+C to stop.")
            while thread.is_alive():
                time.sleep(0.5)
    except KeyboardInterrupt:
        pass
    finally:
        server.should_exit = True
        thread.join(timeout=10)


if __name__ == "__main__":
    main()
