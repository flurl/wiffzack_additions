#!/usr/bin/env python3

import subprocess
import tomllib
from typing import LiteralString, Any
import platformdirs


from tkinter import (
    Tk, Frame, Menubutton, Menu
)

BACKEND_SERVER: LiteralString = "127.0.0.1:5000"
KIOSK_BROWSER_CMD: LiteralString = "chromium --kiosk --noerrdialogs --disable-infobars --enable-features=OverlayScrollbar "

API_PATHS: dict[str, str] = {
    "all_articles": "/api/artikel",
    "sales": "/api//{client}/sales",
    "tallied_articles": "/api/{client}/tallied_articles",
    "latest_tallied_articles": "/api/{client}/latest_tallied_articles",
    "wardrobe_sales": "/api/wardrobe_sales"
}

config: dict[str, Any] = {}
try:
    with open("config.toml", "rb") as f:
        config = tomllib.load(f)
except FileNotFoundError:
    pass
    

with open(f"{platformdirs.user_config_dir('wiffzack')}/config.toml", "rb") as f:
    config_user: dict[str, Any] = tomllib.load(f)
    config |= config_user

CLIENT_NAME: LiteralString = config['client']['name']

class MenuButton(object):

    def __init__(self, master: Tk) -> None:
        frame: Frame = Frame(master)
        frame.pack()
        self.menuBtn: Menubutton = Menubutton(
            frame, text=u"Menü", width=100, height=50, font=("Helvetica", 24, "bold"))

        # Create the Menu object
        self.menu: Menu = Menu(self.menuBtn)

        self.menu.add_command(label="Artikel", underline=0,
                              command=self.get_articles, font=("Helvetica", 18, "bold"))

        storageMenu: Menu = Menu(self.menu)
        storageMenu.add_command(label="Ware anfordern", underline=0,
                              command=lambda: self.open_storage_mask("request"), font=("Helvetica", 18, "bold"))
        storageMenu.add_command(label="Ware annehmen", underline=0,
                              command=lambda: self.open_storage_mask("transfer"), font=("Helvetica", 18, "bold"))
        storageMenu.add_command(label="Stand", underline=0,
                              command=lambda: self.open_storage_mask("stock"), font=("Helvetica", 18, "bold"))
        self.menu.add_cascade(label='Lager', menu=storageMenu, underline=0, font=("Helvetica", 18, "bold"))


        
        salesMenu: Menu = Menu(self.menu)
        salesMenu.add_command(label="Umsatz", underline=0,
                              command=self.get_sales, font=("Helvetica", 18, "bold"))
        salesMenu.add_command(label="Bonierte Artikel", underline=0,
                              command=self.get_tallied_articles, font=("Helvetica", 18, "bold"))
        salesMenu.add_command(label="letzte Bonierungen", underline=0,
                              command=self.get_latest_tallied_articles, font=("Helvetica", 18, "bold"))
        salesMenu.add_command(label="Garderoben Umsatz", underline=0,
                              command=self.get_wardrobe_sales, font=("Helvetica", 18, "bold"))
        self.menu.add_cascade(label='Moneten', menu=salesMenu, underline=0, font=("Helvetica", 18, "bold"))
        

        systemMenu: Menu = Menu(self.menu)
        systemMenu.add_command(label='Logout', underline=0, command=self.dummyCmd, font=("Helvetica", 18, "bold"))
        systemMenu.add_command(label='Reboot', underline=0, command=self.dummyCmd, font=("Helvetica", 18, "bold"))		
        self.menu.add_cascade(label='System', menu=systemMenu, underline=0, font=("Helvetica", 18, "bold"))

        # Assign the Menu object to the Menubutton using the menu option
        self.menuBtn['menu'] = self.menu
        self.menuBtn.pack(side="left")

    def open_storage_mask(self, mode: str) -> None:
        url: str = f"http://localhost:5173/storage/{mode}?terminal={CLIENT_NAME}"
        self.open_browser(url)

    def get_articles(self) -> None:
        self.open_browser(f"http://{BACKEND_SERVER}{API_PATHS['all_articles']}")

    def get_sales(self) -> None:
        self.open_browser(f"http://{BACKEND_SERVER}{API_PATHS['sales'].format(client=CLIENT_NAME)}")

    def get_tallied_articles(self) -> None:
        self.open_browser(f"http://{BACKEND_SERVER}{API_PATHS['tallied_articles'].format(client=CLIENT_NAME)}")
        

    def get_latest_tallied_articles(self) -> None:
        self.open_browser(f"http://{BACKEND_SERVER}{API_PATHS['latest_tallied_articles'].format(client=CLIENT_NAME)}")

    def get_wardrobe_sales(self) -> None:
        self.open_browser(f"http://{BACKEND_SERVER}{API_PATHS['wardrobe_sales']}")

    def open_browser(self, url: str) -> None:
        subprocess.run(f"{KIOSK_BROWSER_CMD} '{url}'", shell=True)
        
    def dummyCmd(self) -> None:
        pass



if __name__ == '__main__':
    root: Tk = Tk()

    # if os.name == 'nt': root.wm_attributes("-topmost", 1)
    # root.overrideredirect(1)
    root.geometry('100x50+0+350')

    app: MenuButton = MenuButton(root)

    root.mainloop()
