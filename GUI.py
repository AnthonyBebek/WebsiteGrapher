"""
Main GUI file
"""
import asyncio
from nicegui import app, ui


class GUI():

    def updateUrls(self) -> None:
        self.LastUrls.push("4")
        return

    def __init__(self) -> None:

        with ui.header():
            ui.markdown("# **Website Grapher GUI**")
        ui.markdown("""
                    This is an example program
                    """)
        self.LastUrls = ui.log(max_lines=10). classes('w-full h-20')
        ui.button("UpdateUrls", on_click=self.updateUrls())
        
        with ui.footer():
            ui.markdown("Website Grapher V1.0.0 This program is free software: you can redistribute it and/or modify it under the terms of the [GNU Affero General Public License](https://www.gnu.org/licenses/agpl-3.0.html) as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.")


        ui.run()


    def shutdown(self) -> None:
        app.shutdown()

if __name__ in {"__main__", "__mp_main__"}:
    gui = GUI()