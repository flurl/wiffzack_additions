#!/usr/bin/env python3

import subprocess
import tomllib
import os
import random
from typing import LiteralString, Any
from pathlib import Path
import urllib.request

from tkinter import (
    Tk, Frame, Menubutton, Menu, messagebox
)


SCRIPT_DIR: Path = Path(__file__).resolve().parent
DEFAULT_CONFIG_PATH: Path = SCRIPT_DIR / "config.default.toml"
USER_CONFIG_DIR: Path = Path.home() / ".wiffzack_additions"
USER_CONFIG_PATH: Path = USER_CONFIG_DIR / "config.client.toml"

config: dict[str, Any] = {}
try:
    with open(DEFAULT_CONFIG_PATH, "rb") as f:
        config = tomllib.load(f)
except FileNotFoundError:
    print(
        f"Default configuration file not found at {DEFAULT_CONFIG_PATH}. Exiting.")
    exit(1)  # Good to exit if default is missing too
except tomllib.TOMLDecodeError as e:
    print(
        f"Error decoding default configuration file {DEFAULT_CONFIG_PATH}: {e}. Exiting.")
    exit(1)

try:
    with open(USER_CONFIG_PATH, "rb") as f:
        config_user: dict[str, Any] = tomllib.load(f)
        # This is fine if client.toml replaces whole sections like [client]
        config |= config_user
except FileNotFoundError:
    print(
        f"Client config not found. Please create a '{USER_CONFIG_PATH}' file.")
    exit(1)
except tomllib.TOMLDecodeError as e:
    print(
        f"Error decoding user configuration file {USER_CONFIG_PATH}: {e}. Exiting.")
    exit(1)

FRONTEND_URLS: dict[str, str] = {
    "all_articles": "/data_table/artikel",
    "sales": "/data_table/{client}/sales",
    "tallied_articles": "/data_table/{client}/tallied_articles",
    "latest_tallied_articles": "/data_table/{client}/latest_tallied_articles",
    "wardrobe_sales": "/data_table/wardrobe_sales",
    "messages": "/message/list",
    "invoices_dlg": "/invoices?terminal={client}",
    "receipes": "/data_table/recipe/list?groupByColumn=0",
    "request_restart": "/api/restart",
    "alarm": "/alarm?terminal={client}",
    "jotd": "/jotd"
}

CLIENT_NAME: LiteralString = config['client']['name']
WEB_SERVER: LiteralString = config['client']['web_server']
KIOSK_BROWSER_CMD: LiteralString = config['client']['browser_cmd']


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
        self.menu.add_cascade(label='Lager', menu=storageMenu,
                              underline=0, font=("Helvetica", 18, "bold"))

        salesMenu: Menu = Menu(self.menu)
        salesMenu.add_command(label="Umsatz", underline=0,
                              command=self.get_sales, font=("Helvetica", 18, "bold"))
        salesMenu.add_command(label="Bonierte Artikel", underline=0,
                              command=self.get_tallied_articles, font=("Helvetica", 18, "bold"))
        salesMenu.add_command(label="letzte Bonierungen", underline=0,
                              command=self.get_latest_tallied_articles, font=("Helvetica", 18, "bold"))
        salesMenu.add_command(label="Garderoben Umsatz", underline=0,
                              command=self.get_wardrobe_sales, font=("Helvetica", 18, "bold"))
        self.menu.add_cascade(label='Moneten', menu=salesMenu,
                              underline=0, font=("Helvetica", 18, "bold"))

        self.menu.add_command(label="Rechnungen", underline=0,
                              command=self.open_invoices_dlg, font=("Helvetica", 18, "bold"))

        self.menu.add_command(label="Nachrichten", underline=0,
                              command=self.show_messages, font=("Helvetica", 18, "bold"))

        self.menu.add_command(label="Rezepturen", underline=0,
                              command=self.show_receipes, font=("Helvetica", 18, "bold"))

        systemMenu: Menu = Menu(self.menu)
        systemMenu.add_command(label='Logout', underline=0,
                               command=self.logout, font=("Helvetica", 18, "bold"))
        systemMenu.add_command(label='Reboot', underline=0,
                               command=self.reboot, font=("Helvetica", 18, "bold"))
        self.menu.add_cascade(label='System', menu=systemMenu,
                              underline=0, font=("Helvetica", 18, "bold"))

        alarmMenu: Menu = Menu(self.menu)
        alarmMenu.add_command(label='Alarm', underline=0,
                              command=self.open_alarm_dlg, font=("Helvetica", 18, "bold"))
        self.menu.add_separator()
        self.menu.add_cascade(label='Alarm', menu=alarmMenu,
                              underline=0, font=("Helvetica", 18, "bold"))

        self.easter_egg_menu: Menu = Menu(self.menu)
        self.make_easter_egg_menu()
        self.menu.add_cascade(
            label='Admin only', menu=self.easter_egg_menu, font=("Helvetica", 18, "bold"))
        self.easter_egg_menu.configure(
            postcommand=lambda: self.make_easter_egg_menu())

        if config["client"]["debug"]:
            debugMenu: Menu = Menu(self.menu)
            debugMenu.add_command(label="Restart server process", underline=0,
                                  command=self.request_server_process_restart, font=("Helvetica", 18, "bold"))
            self.menu.add_separator()
            self.menu.add_cascade(label='Debug', menu=debugMenu,
                                  underline=0, font=("Helvetica", 18, "bold"))

        # Assign the Menu object to the Menubutton using the menu option
        self.menuBtn['menu'] = self.menu
        self.menuBtn.pack(side="left")

    def open_storage_mask(self, mode: str) -> None:
        url: str = f"http://{WEB_SERVER}/storage/{mode}?terminal={CLIENT_NAME}"
        self.open_browser(url)

    def get_articles(self) -> None:
        self.open_browser(
            f"http://{WEB_SERVER}{FRONTEND_URLS['all_articles']}")

    def get_sales(self) -> None:
        self.open_browser(
            f"http://{WEB_SERVER}{FRONTEND_URLS['sales'].format(client=CLIENT_NAME)}")

    def get_tallied_articles(self) -> None:
        self.open_browser(
            f"http://{WEB_SERVER}{FRONTEND_URLS['tallied_articles'].format(client=CLIENT_NAME)}")

    def get_latest_tallied_articles(self) -> None:
        self.open_browser(
            f"http://{WEB_SERVER}{FRONTEND_URLS['latest_tallied_articles'].format(client=CLIENT_NAME)}")

    def get_wardrobe_sales(self) -> None:
        self.open_browser(
            f"http://{WEB_SERVER}{FRONTEND_URLS['wardrobe_sales']}")

    def open_invoices_dlg(self) -> None:
        self.open_browser(
            f"http://{WEB_SERVER}{FRONTEND_URLS['invoices_dlg'].format(client=CLIENT_NAME)}")

    def show_messages(self) -> None:
        self.open_browser(
            f"http://{WEB_SERVER}{FRONTEND_URLS['messages']}")

    def show_receipes(self) -> None:
        self.open_browser(
            f"http://{WEB_SERVER}{FRONTEND_URLS['receipes']}")

    def open_browser(self, url: str) -> None:
        # allow newly opened window to become the top window
        if os.name == 'nt':
            root.wm_attributes("-topmost", 0)
        subprocess.run(f"{KIOSK_BROWSER_CMD} \"{url}\"", shell=True)
        # enable always on top again
        if os.name == 'nt':
            root.wm_attributes("-topmost", 1)

    def logout(self) -> None:
        os.system("shutdown -l")

    def reboot(self) -> None:
        os.system("shutdown -r")

    def open_alarm_dlg(self) -> None:
        self.open_browser(
            f"http://{WEB_SERVER}{FRONTEND_URLS['alarm'].format(client=CLIENT_NAME)}")

    def show_jotd(self) -> None:
        self.open_browser(
            f"http://{WEB_SERVER}{FRONTEND_URLS['jotd']}")

    def request_server_process_restart(self) -> None:
        answer: bool = messagebox.askyesno(  # type: ignore
            title="Restart server process", message="Do you really want to restart the server process?")
        if answer:
            url: str = f"http://{WEB_SERVER}{FRONTEND_URLS['request_restart']}"
            try:
                # allow newly opened window to become the top window
                if os.name == 'nt':
                    root.wm_attributes("-topmost", 0)
                with urllib.request.urlopen(url) as response:
                    if response.status == 200:
                        messagebox.showinfo(  # type: ignore
                            "Server Neustart", "Neustart-Anfrage an den Server gesendet.")
                    else:
                        messagebox.showerror(  # type: ignore
                            "Server Neustart", f"Fehler beim Senden der Neustart-Anfrage: {response.status}")
            except Exception as e:
                messagebox.showerror(  # type: ignore
                    "Server Neustart", f"Fehler bei der Verbindung zum Server: {e}")
            finally:  # enable always on top again
                if os.name == 'nt':
                    root.wm_attributes("-topmost", 1)

    def dummyCmd(self) -> None:
        pass

    def make_easter_egg_menu(self) -> None:
        menu_labels: list[str] = [
            "Achtung, Minenfeld!",
            "Hier endet die Gemütlichkeit!",
            "Weiterklicken auf eigene Gefahr!",
            "Nicht öffnen – Monster drin!",
            "Klick hier und du bist gefeuert!",
            "Warnung: Langweilig!",
            "Nur für Mutige – oder Dumme!",
            "Hier wartet nur Enttäuschung!",
            "Weiter geht’s in den Abgrund!",
            "Nicht klicken – ernsthaft!",
            "Klick hier und dein Computer explodiert!",
            "Nur für Katzenliebhaber!",
            "Weiterklicken = Kaffeefleck auf Touchscreen!",
            "Hier beginnt die Langeweile!",
            "Warnung: Enthält Mathematik!",
            "Nicht öffnen – Pandorabüchse!",
            "Klick hier und du verlierst das Spiel!",
            "Weiterklicken führt zu Montagsgefühlen!",
            "Achtung: Hier wartet ein Papiertiger!",
            "Nicht klicken – außer du magst Fehler!",
            "Letzte Warnung!",
            "Nicht weiter!",
            "Weitergehen bedeutet Gefahr fürs System!",
            "Stop!!!",
            "Wer weitermacht wird gemeldet!"
        ]
        self.easter_egg_menu.delete(0, 'end')

        level1_menu: Menu = Menu(self.easter_egg_menu)
        level2_menu: Menu = Menu(level1_menu)
        level3_menu: Menu = Menu(level2_menu)
        level4_menu: Menu = Menu(level3_menu)

        self.easter_egg_menu.add_cascade(label=menu_labels.pop(
            random.randint(0, len(menu_labels) - 1)), menu=level1_menu,
            underline=0, font=("Helvetica", 18, "bold"))
        level1_menu.add_cascade(label=menu_labels.pop(
            random.randint(0, len(menu_labels) - 1)), menu=level2_menu,
            underline=0, font=("Helvetica", 18, "bold"))
        level2_menu.add_cascade(label=menu_labels.pop(
            random.randint(0, len(menu_labels) - 1)), menu=level3_menu,
            underline=0, font=("Helvetica", 18, "bold"))
        level3_menu.add_cascade(label=menu_labels.pop(
            random.randint(0, len(menu_labels) - 1)), menu=level4_menu,
            underline=0, font=("Helvetica", 18, "bold"))
        level4_menu.add_command(label=menu_labels.pop(
            random.randint(0, len(menu_labels) - 1)), underline=0,
            command=self.show_jotd, font=("Helvetica", 18, "bold"))


if __name__ == '__main__':
    root: Tk = Tk()

    # always on top only on windows
    if os.name == 'nt':
        root.wm_attributes("-topmost", 1)
    root.overrideredirect(True)
    root.geometry('100x50+0+350')

    app: MenuButton = MenuButton(root)

    root.mainloop()
