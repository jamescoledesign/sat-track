"""
Satellite Tracker

"""

__author__ = "James Cole <james@jamescole.info"


from sattrack_functions import *
import pandas as pd
from skyfield.api import load
from textual import on
from textual.app import App, ComposeResult
from textual.containers import Horizontal, VerticalScroll, Grid, Vertical
from textual.widgets import *


# Load CSV
sats_df = pd.read_csv("satellites.csv")
ts = load.timescale()

class SatTrackApp(App[None]):
    CSS_PATH = "styles.tcss"
    BINDINGS = [("q", "request_quit", "Quit")]


    # User settings -> To do: Move/write to JSON for persistent storage
    settings = {
        "Ground Station": (33.253408, -97.134179),
        "Satellite": [sats_df['sat_name'], "GOES-16"],
        "Coordinates": [["Decimal Degrees", "DMS"], "Decimal Degrees"],
        "Rounding": [["2", "3", "4", "5", "None"], 5],
        "Show XYZ": [[True, False], True]
    }
    
    # Default states
    data = [str(0)] * 8
    sat_name = settings["Satellite"][1]
    tracking = False
    clear = False
    
    def compose(self) -> ComposeResult:
        
        settings = self.settings
        data = self.data
        
        yield Header()

        with Horizontal(id="buttons"):
            yield Button("Tracking", id="tracking", classes="left-button")
            yield Button("Settings", id="settings", classes="middle-button")
            yield Button("Quit", id="quit", classes="right-button")

        with ContentSwitcher(initial="tracking", id="switcher"):

            # Tracking tab
            with VerticalScroll(id="tracking"):
                
                tracked_sat = Static(settings['Satellite'][1], id="tracked-sat")
                tracked_sat.border_title = "Satellite"
                
                yield tracked_sat

                # Top boxes
                lbl1 = Label(data[0], classes="tracking-header-item", id="d0")
                lbl1.border_title = "Timestamp" 
                lbl2 = Label(data[1], classes="tracking-header-item", id="d1")
                lbl2.border_title = "Visibility" 

                yield Horizontal(
                    lbl1, lbl2, id="tracking-header"
                )
                
                # Telemetry
                distance = data[2]

                t1 = Digits(f"{distance}", classes="digit", id="d2")
                t1.border_title = "Distance (km)"

                altitude = data[3]
                t2 = Digits(f"{altitude}", classes="digit", id="d3")
                t2.border_title = "Altitude (degrees)"

                azimuth = data[4]
                t3 = Digits(f"{azimuth}", classes="digit", id="d4")
                t3.border_title = "Azimuth (degrees)"

                yield Vertical(
                    t1, t2, t3, id="telemetry"
                )

                # Spherical coordinates
                x = data[5]
                y = data[6]
                z = data[7]

                x_grid = Label(x, classes="spherical", id="d5")
                x_grid.border_title = "X" 

                y_grid = Label(y, classes="spherical", id="d6")
                y_grid.border_title = "Y" 

                z_grid = Label(z, classes="spherical", id="d7")
                z_grid.border_title = "Z" 

                spherical_container = Grid(x_grid,
                                           y_grid,
                                           z_grid,
                                           id="spherical-container")

                spherical_container.border_title = "Spherical coordinates" 

                yield spherical_container

                yield Button("Start tracking", id="track-btn", classes="start")
                yield Button("Clear", id="clear-btn", classes="clear", disabled=True)

            # Settings tab -> To do: move to tracking page for convenience 
            with VerticalScroll(id="settings"):
                yield Grid(
                    Static("Setting", id="s1"),
                    Static("Selected", id="s2"),
                    Static("Actions", id="s3"),
                    id="first-row"
                )
                yield Grid(
                    Static("Satellite"),
                    Static(settings["Satellite"][1], id="sat_name"),
                    Select((sat, sat) for sat in settings['Satellite'][0]),
                    classes="grid",
                )
                
                # To do: Make configurable / get from IP
                yield Grid(
                    Static("Coordinates"),
                    Static(settings["Coordinates"][1], id="Coordinates"),
                    RadioSet(
                        RadioButton(label="Decimal Degrees", name="Coordinates", value=settings['Coordinates'][1]),
                        RadioButton(label="DMS", name="Coordinates"), 
                        id="coordinates-radios"
                    )
                )
                
                yield Grid(
                    Static("Rounding"),
                    Static(str(settings['Rounding'][1]), id="Rounding"),
                    RadioSet(
                        RadioButton(label="0", name="Rounding"),
                        RadioButton(label="1", name="Rounding"),
                        RadioButton(label="2", name="Rounding"),
                        RadioButton(label="3", name="Rounding"),
                        RadioButton(label="4", name="Rounding"),
                        RadioButton(label="5", name="Rounding", value=settings['Rounding'][1]),
                        id="rounding-radios"
                ))
                
                # To do: Enable setting
                yield Grid(
                    Static("Show XYZ", name="Show XYZ"),
                    Static(str(settings["Show XYZ"][1]), id="showXYZ"),
                    Switch(settings["Show XYZ"][1], name="Show XYZ")
                )           


    # Radio button selections
    def on_radio_set_changed(self, event: RadioSet.Changed) -> None:
        pressed_name = event.pressed.name
        selected = event.pressed.label
        
        if pressed_name == "Rounding":
            selected = int(selected._text[0])
                
        self.settings[pressed_name][1] = selected
        event.pressed.value = True
        self.query_one(f"#{pressed_name}", Static).update(
            event.pressed.label
        )


    def on_select_changed(self, event: Select.Changed) -> None:
        self.settings['Satellite'][1] = event.value
        tracked_sat = self.settings['Satellite'][1]
        self.query_one("#sat_name", Static).update(tracked_sat)
        self.query_one("#tracked-sat", Static).update(tracked_sat)
        
        if self.tracking:
            self.sub_title = f"Tracking {str(tracked_sat)}"
        

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "quit":
            self.app.exit()
        elif event.button.id == "track-btn":
            if self.tracking: 
                self.tracking = False
                self.sub_title = f""
                event.button.label = "Start tracking"
                event.button.classes = "start"
                self.notify("Tracking stopped", severity="warning", timeout=2)
                self.query_one("#clear-btn").disabled = False
            else: 
                self.tracking = True
                tracked_sat = self.settings['Satellite'][1]
                self.sub_title = f"Tracking {str(tracked_sat)}"
                event.button.label = "Stop tracking"
                event.button.classes = "stop"
                self.notify("Tracking started", timeout=2)
                self.update_numbers()

        elif event.button.id == "clear-btn":
            self.clear = True

        else:
            self.query_one(ContentSwitcher).current = event.button.id


    def on_mount(self) -> None:
        self.title = "Satellite Tracker" 
        self.set_interval(1, self.update_numbers, pause=False)
        

    # Watch for changes and update numbers
    def on_ready(self) -> None:
        # Set initial state
        self.update_numbers()
        
        
    def get_sat(self, return_idx=False):
        sat_name = self.settings['Satellite'][1]
        sat_data = sats_df[sats_df['sat_name'] == sat_name]

        line1 = sat_data["tle_line1"].item()
        line2 = sat_data["tle_line2"].item()
        
        if return_idx:
            return sat_data.index, line1, line2
        else:
            return line1, line2
        
        
    def update_numbers(self) -> None:
        settings = self.settings
        
        if self.tracking:
            # Get data
            line1, line2 = self.get_sat()
            data = skyfieldTracker(line1, line2, 
                                   settings['Satellite'][1],
                                   settings['Ground Station'], 
                                   settings['Rounding'][1], 
                                   print_data=False)

            # Update each of the number containers
            for d in enumerate(data):
                self.query_one(f"#d{d[0]}").update(f"{d[1]}")

        elif self.clear:
            # Reset data to zeros
            data = [str(0)] * 8

            # Update each of the number containers
            for d in enumerate(data):
                self.query_one(f"#d{d[0]}").update(f"{d[1]}")

            # Update states
            self.clear = False
            self.query_one("#clear-btn").disabled = True


    def action_request_quit(self) -> None:
        self.app.exit()
        

if __name__ == "__main__":
    SatTrackApp().run()
    