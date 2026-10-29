
from pathlib import Path
import customtkinter as ctk
from PIL import Image, ImageTk


BASE_DIR = Path(__file__).resolve().parents[2]
ASSETS_DIR = BASE_DIR / "assets"

F_LOGO_PATH = ASSETS_DIR / "logo3.png"
FULL_LOGO_PATH = ASSETS_DIR / "logo_fedomek.png"



class SplashScreen(ctk.CTkToplevel):
    def __init__(self, master, on_complete):
        super().__init__(master)

        self.on_complete = on_complete
        self.animation_angle = 0
        self.finished = False

        self.title("FIDOMEK")
        self.overrideredirect(True)
        self.configure(fg_color="#FFFFFF")

        width, height = 760, 460
        x = (self.winfo_screenwidth() - width) // 2
        y = (self.winfo_screenheight() - height) // 2
        self.geometry(f"{width}x{height}+{x}+{y}")

        self.symbol_image = Image.open(F_LOGO_PATH).convert("RGBA")
        self.full_logo_image = Image.open(FULL_LOGO_PATH).convert("RGBA")

        self.symbol_label = ctk.CTkLabel(self, text="")
        self.symbol_label.place(
            relx=0.5, rely=0.43, anchor="center"
        )

        self.full_logo_label = ctk.CTkLabel(self, text="")
        self.full_logo_label.place(
            relx=0.5, rely=0.43, anchor="center"
        )
        self.full_logo_label.place_forget()

       
    
        self._show_symbol()
        self.after(100, self._rotate_symbol)

    def _show_symbol(self):
        image = self.symbol_image.copy()
        image.thumbnail((200, 200), Image.Resampling.LANCZOS)

        self.symbol_photo = ImageTk.PhotoImage(image)
        self.symbol_label.configure(image=self.symbol_photo)

    def _rotate_symbol(self):
        if self.finished:
            return

        self.animation_angle += 15

        rotated = self.symbol_image.rotate(
            self.animation_angle,
            resample=Image.Resampling.BICUBIC,
            expand=True,
        )
        rotated.thumbnail((200, 200), Image.Resampling.LANCZOS)

        self.symbol_photo = ImageTk.PhotoImage(rotated)
        self.symbol_label.configure(image=self.symbol_photo)

        if self.animation_angle < 360:
            self.after(25, self._rotate_symbol)
        else:
            self.after(150, self._show_full_logo)

    def _show_full_logo(self):
        image = self.full_logo_image.copy()
        image.thumbnail((540, 240), Image.Resampling.LANCZOS)

        self.full_logo_photo = ImageTk.PhotoImage(image)
        self.full_logo_label.configure(image=self.full_logo_photo)

        self.symbol_label.place_forget()
        self.full_logo_label.place(
            relx=0.5, rely=0.40, anchor="center"
        )

        

        self.after(1200, self._finish)

    def _finish(self):
        if self.finished:
            return

        self.finished = True
        self.destroy()
        self.on_complete()
