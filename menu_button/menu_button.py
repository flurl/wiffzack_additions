#!/usr/bin/env python3

from tkinter import (
    Tk, Frame, Menubutton, Menu, Toplevel, Scrollbar, Button,
    TOP, BOTTOM, LEFT, RIGHT, Y, BOTH
)
from typing import LiteralString
import requests
from tkinterweb import HtmlFrame

SERVER: LiteralString = "127.0.0.1:5000"

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
        self.menu.add_command(label="Lager umbuchen", underline=0,
                              command=self.dummyCmd, font=("Helvetica", 18, "bold"))
        self.menu.add_command(label="Umsatz", underline=0,
                              command=self.get_sales, font=("Helvetica", 18, "bold"))
        self.menu.add_command(label="Bonierte Artikel", underline=0,
                              command=self.dummyCmd, font=("Helvetica", 18, "bold"))
        self.menu.add_command(label="letzte Bonierungen", underline=0,
                              command=self.dummyCmd, font=("Helvetica", 18, "bold"))

        # Assign the Menu object to the Menubutton using the menu option
        self.menuBtn['menu'] = self.menu
        self.menuBtn.pack(side="left")

    def get_articles(self) -> None:
        html: str = self.fetch_data("/api/artikel")
        self.show_output_window(html)

    def get_sales(self) -> None:
        print("get_sales")
        self.show_output_window("<html><body><h1>Umsatz</h1></body></html>")

    def dummyCmd(self) -> None:
        print("dummyCmd")
        self.show_output_window("<html><body><h1>Test</h1></body></html>")

    def show_output_window(self, html_content: str) -> None:
        win: Toplevel = Toplevel()

        frame: Frame = Frame(win, borderwidth=1, bg="blue")
        frame.pack(side=TOP, fill=BOTH, expand=True)

        scrollbar: Scrollbar = Scrollbar(frame)

        html_frame: HtmlFrame = HtmlFrame(frame, vertical_scrollbar=False)
        html_frame.load_html(html_content)
        html_frame.pack(side=LEFT, fill=BOTH, expand=True)
        html_frame.html.configure(yscrollcommand=scrollbar.set)

        scrollbar.config(command=html_frame.yview,
                         bg="#ff0000",
                         width=100)
        scrollbar.pack(side=RIGHT, fill=Y)

        frame2: Frame = Frame(win)
        frame2.pack(side=BOTTOM)

        btn: Button = Button(frame2, text="OK", command=win.destroy,
                     font=("Helvetica", 24, "bold"))
        btn.pack(side=BOTTOM)

        #self._resultWindow: Toplevel = win

        #return self._resultWindow

    def fetch_data(self, url: str) -> str:
        headers = {"Accept": "text/html"}
        response: requests.Response = requests.get(f"http://{SERVER}{url}", headers=headers)
        return response.text


if __name__ == '__main__':
    root: Tk = Tk()

    # if os.name == 'nt': root.wm_attributes("-topmost", 1)
    # root.overrideredirect(1)
    root.geometry('100x50+0+350')

    app: MenuButton = MenuButton(root)

    root.mainloop()
