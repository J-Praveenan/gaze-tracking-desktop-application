import threading
from PIL import Image
import pystray

class SystemTrayIcon:
    def __init__(self, on_restore, on_exit):
        self.icon = None
        self.on_restore = on_restore
        self.on_exit = on_exit

    def show(self):
        def run_tray():
            image = Image.open("assets/eyelogo.ico")  # use your app icon

            menu = pystray.Menu(
                pystray.MenuItem("Restore", lambda: self._restore()),
                pystray.MenuItem("Show Instructions", lambda: self._show_instructions()),
                pystray.MenuItem("Exit", lambda: self._exit_app())
            )

            self.icon = pystray.Icon("LookTrackVision", image, "Look Track Vision", menu)
            self.icon.run()

        threading.Thread(target=run_tray, daemon=True).start()

    def _restore(self):
        self.icon.stop()
        self.on_restore()

    def _exit_app(self):
        self.icon.stop()
        self.on_exit()

    def _show_instructions(self):
        
        from frontend.pages.instruction_tray import InstructionTray
        tray = InstructionTray()
        tray.focus_force()
