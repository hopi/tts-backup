#!/usr/bin/env python
# Shared GUI functions & classes.

import os
import os.path
import threading
import argparse

from tkinter import *
from tkinter.font import Font

from libgui.entry import (DirEntry,
                          FileEntry,
                          ToggleEntry)
from libgui.frame import (EntryFrame,
                          ButtonFrame,
                          OutputFrame)

import libtts
tts_prefetch = __import__("tts-prefetch")


class GUI (Frame):

    argparser = argparse.ArgumentParser(
        description="Back-up locally cached content "
                    "from a TTS .json file."
    )

    argparser.add_argument('infile',
                           metavar="FILENAME",
                           default="",
                           nargs='?',
                           help='The save file or mod in JSON format.')

    def __init__(self, master):

        super().__init__(master)

        self.running = None
        self.semaphore = None

        self.args = self.argparser.parse_args()

        self.make_widgets()

    def make_widgets(self):

        self.label = Label(self,
                           text="TTS-Prefetch",
                           font=Font(size=14, weight="bold"))
        self.label.pack()

        leftpane = Frame(self)
        leftpane.configure(bg="black")

        homedir = os.path.expanduser("~")
        self.settings = EntryFrame(
            leftpane,

            ("infile",   FileEntry, {"label": "Input file",
                                     "initialdir": libtts.GAMEDATA_DEFAULT,
                                     "filetypes": ["JSON-file {.json}"],
                                     "action": "open",
                                     "default": self.args.infile}),
            ("gamedata", DirEntry,  {"label": "Gamedata path",
                                     "default": libtts.GAMEDATA_DEFAULT,
                                     "initialdir": homedir,
                                     "mustexist": True}),

            ("dry_run", ToggleEntry,  {"label": "Dry run"}),
            ("refetch", ToggleEntry,  {"label": "Refetch"}),
            ("relax",   ToggleEntry,  {"label": "Relax"}),

            text="Settings",
            width=60
        )
        self.settings.pack(fill=X)

        control = LabelFrame(leftpane, text="Control")
        self.buttons = ButtonFrame(control, "Run", "Stop", "Quit")
        self.buttons.pack()
        self.buttons.on("Run", self.run)
        self.buttons.on("Stop", self.stop)
        self.buttons.on("Quit", self.quit)
        control.pack(fill=X)

        leftpane.pack(side=LEFT, anchor=N)

        self.output = OutputFrame(self, text="Output")
        self.output.pack(expand=True, fill=BOTH)

    def run(self):

        if self.running and self.running.is_alive():
            return

        args = self.parse_args()
        if not args:
            return

        self.output.clear()

        self.semaphore = threading.Semaphore(0)

        def callback():
            with self.output:
                try:
                    tts_prefetch.main(args, self.semaphore)
                except SystemExit:
                    pass

        thread = threading.Thread(target=callback)
        thread.start()
        self.running = thread

    def stop(self):

        def callback():

            if self.running and self.running.is_alive():
                self.semaphore.release()
                self.running.join()

        thread = threading.Thread(target=callback)
        thread.start()

    def parse_args(self):

        commands = []

        infile = self.settings.infile.get()
        if infile:
            commands.append(infile)
        else:
            return

        gamedata = self.settings.gamedata.get()
        if gamedata:
            commands.extend(["--gamedata", gamedata])

        if self.settings.dry_run.get():
            commands.append("--dry-run")

        if self.settings.relax.get():
            commands.append("--relax")

        if self.settings.refetch.get():
            commands.append("--refetch")

        return tts_prefetch.parser.parse_args(args=commands)


if __name__ == "__main__":

    root = Tk()
    gui = GUI(root)
    gui.pack(fill=BOTH, expand=True)
    root.mainloop()