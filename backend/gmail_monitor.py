
import logging
import queue
import threading

from pathlib import Path

from backend import download_attachments as downloader


logger = logging.getLogger(__name__)


class GmailMonitor:
    """Service de surveillance Gmail exécuté en arrière-plan."""

    def __init__(self):
        self._thread = None
        self._stop_event = threading.Event()
        self.events = queue.Queue()

        self._lock = threading.Lock()
        self._running = False

    @property
    def is_running(self):
        with self._lock:
            return self._running

    @property
    def is_alive(self):
        """Vérifier si le thread Gmail travaille encore."""
        return self._thread is not None and self._thread.is_alive()

    def _send_event(self, event_type, message):
        """Transmettre un événement à l'interface."""
        self.events.put({
            "type": event_type,
            "message": message,
        })

    def start(self, download_dir=None):
        """Démarrer la surveillance Gmail."""

        with self._lock:
            if self._running:
                return False

            if self._thread and self._thread.is_alive():
                return False

            self._stop_event.clear()
            self._running = True

            self._thread = threading.Thread(
                target=self._monitor_loop,
                args=(download_dir,),
                daemon=True,
                name="GmailMonitor",
            )

            self._thread.start()

        self._send_event(
            "status",
            "Démarrage de la surveillance Gmail...",
        )

        return True

    def stop(self):
        """Demander l'arrêt de la surveillance."""

        if not self.is_alive:
            return False

        self._stop_event.set()

        self._send_event(
            "status",
            "Arrêt de la surveillance en cours...",
        )

        return True

    def _monitor_loop(self, download_dir):
        try:
            # Configurer le dossier de destination.
            if download_dir:
                downloader.DOWNLOAD_DIR = Path(download_dir)

            downloader.DOWNLOAD_DIR.mkdir(
                parents=True,
                exist_ok=True,
            )

            # Initialiser la base SQLite existante.
            downloader.initialize_database()

            self._send_event(
                "status",
                "Connexion à Gmail en cours...",
            )

            # Réutiliser l'authentification existante.
            service = downloader.authenticate_gmail()

            self._send_event(
                "connected",
                "Connexion Gmail réussie.",
            )

            while not self._stop_event.is_set():

                self._send_event(
                    "checking",
                    "Vérification des nouveaux emails...",
                )

                try:
                    downloader.check_emails(service)

                    if not self._stop_event.is_set():
                        self._send_event(
                            "status",
                            "Surveillance active — prochaine vérification dans 5 minutes.",
                        )

                except Exception as error:
                    logger.exception(
                        "Erreur pendant la vérification Gmail."
                    )

                    self._send_event(
                        "error",
                        f"Erreur de vérification : {error}",
                    )

                # Attendre 5 minutes ou interrompre l'attente sur demande.
                self._stop_event.wait(
                    downloader.CHECK_INTERVAL_SECONDS
                )

        except Exception as error:
            logger.exception(
                "Impossible de démarrer la surveillance Gmail."
            )

            self._send_event(
                "error",
                f"Erreur de connexion : {error}",
            )

        finally:
            with self._lock:
                self._running = False

            self._send_event(
                "stopped",
                "Surveillance Gmail arrêtée.",
            )

    def get_events(self):
        """Récupérer les événements en attente."""

        received_events = []

        while True:
            try:
                received_events.append(
                    self.events.get_nowait()
                )
            except queue.Empty:
                break

        return received_events
