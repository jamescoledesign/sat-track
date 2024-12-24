"""
Satellite Tracker

"""

__author__ = "James Cole <james@jamescole.info"



from sattrack_functions import *
import pandas as pd
from skyfield.api import load

from textual.app import App, ComposeResult
from textual.containers import Horizontal, VerticalScroll, Grid, Vertical
from textual.widgets import *



# ----------
# Placeholder data
labels = ['Timestamp', 'Visibility', 'Distance', 'Altitude', 'Azimuth', 'X', 'Y', 'Z']
decimal_degrees = []
dms = []

sats = ["GOES-16", "GOES-17", "GOES-19"]

# sat_data = ['2024-12-22-18-52-11', 'Above horizon', 
#             '37425.0', '44.73387643437857', '143.64121832067354',
#             '0.421144', '-0.572086', '0.703815']

user_preferences = [('satellite', 'GOES-16', Select((sat, sat) for sat in sats)), 
                    ('coordinates', 'decimal_degrees', Switch()), 
                    ('show_xyz', True, Switch()), ('rounding', '4', '4')]

# ----------


# Load CSV
sats_df = pd.read_csv('satellites.csv')

# Your current location (lat/lon)
ground_station = (33.253408, -97.134179)

ts = load.timescale()

# Placeholder index for testing
index = 0

sat_name = sats[index]
sat_data = sats_df.iloc[index]
line1 = sat_data['tle_line1']
line2 = sat_data['tle_line2']

# positions = skyfieldTracker(line1, line2, sat_name, ground_station)
# print(positions[0])
class SatTrackApp(App[None]):
    CSS_PATH = "styles.tcss"
    BINDINGS = [("q", "request_quit", "Quit")]
    
    rounding = 5
    tracking = False
    clear = False
    button_msg = "Start"
    
    data = [str(0)] * 8
    
    

    def compose(self) -> ComposeResult:
                
        with Horizontal(id="buttons"):  
            yield Button("Tracking", id="tracking", classes="top-button") 
            yield Button("Settings", id="settings", classes="top-button") 
            yield Button("Quit", id="quit", classes="top-button") 
            
        tracked_sat = Static(sat_name, id='tracked-sat')
        tracked_sat.border_title = "Satellite"
        yield tracked_sat
            
        with ContentSwitcher(initial="tracking", id='switcher'):

            # Tracking tab
            with VerticalScroll(id="tracking"):
                
                # Top boxes
                lbl1 = Label(self.data[0], classes="tracking-header-item", id='d0')
                lbl1.border_title = "Timestamp" 
                lbl2 = Label(self.data[1], classes="tracking-header-item", id='d1')
                lbl2.border_title = "Visibility" 
                
                yield Horizontal(
                    lbl1, lbl2, id='tracking-header'
                )
                
                # Telemetry 
                distance = self.data[2]
                # t1 = Vertical(Label("Distance"), 
                #               Digits(f'{distance} km', classes="digits"),)
                t1 = Digits(f'{distance}', classes="digit", id='d2')
                t1.border_title = "Distance (km)" 
                
                altitude = self.data[3]
                t2 = Digits(f'{altitude}', classes="digit", id='d3')
                t2.border_title = "Altitude (degrees)" 
                
                azimuth = self.data[4]
                t3 = Digits(f'{azimuth}', classes="digit", id='d4')
                t3.border_title = "Azimuth (degrees)" 
                
                yield Vertical(
                    t1, t2, t3, id='telemetry'
                )
                
                # Spherical coordinates
                x = self.data[5]
                y = self.data[6]
                z = self.data[7]
                
                x_grid = Label(x, classes="spherical", id="d5")
                x_grid.border_title = "X" 
                
                y_grid = Label(y, classes="spherical", id="d6")
                y_grid.border_title = "Y" 
                
                z_grid = Label(z, classes="spherical", id="d7")
                z_grid.border_title = "Z" 
                
                # yield Label("Spherical coordinates", id='spherical-title')
                spherical_container = Grid(x_grid, 
                                           y_grid, 
                                           z_grid, 
                                           id="spherical-container")
                
                spherical_container.border_title = "Spherical coordinates" 
                
                yield spherical_container
                
                yield Button("Start tracking", id="track-btn", classes="start")
                yield Button("Clear", id="clear-btn", classes="clear", disabled=True)

            # Settings tab
            with VerticalScroll(id="settings"):
                yield Grid(
                    Static("Setting", id='s1'),
                    Static("Selected", id='s2'),
                    Static("Actions", id='s3'),
                    id='first-row'
                )
                yield Grid(
                    Static("Satellite", classes="label"),
                    Static("GOES-16", classes="label"),
                    Select((sat, sat) for sat in sats),
                    classes="grid",
                )
                yield Grid(
                    Static("Coordinates", classes="label"),
                    Static("Decimal Degrees", classes="label"),
                    RadioSet(
                        RadioButton("Decimal Degrees", value=True),
                        RadioButton("DMS")
                    )
                )
                yield Grid(
                    Static("Rounding", classes="label"),
                    Static(str(self.rounding), classes="label"),
                    RadioSet(
                        RadioButton(str(2)),
                        RadioButton(str(3)),
                        RadioButton(str(4)),
                        RadioButton(str(5), value=True),
                        RadioButton("None")
                    )
                )   
                yield Grid(
                    Static("Show XYZ", classes="label"),
                    Static(str(True), classes="label"),
                    Switch(True, id="custom-design"),
                    classes="grid",
                )
    
                
    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "quit":
            self.app.exit()
        elif event.button.id == "track-btn":
            if self.tracking: 
                self.tracking = False
                event.button.label = "Start tracking"
                event.button.classes = "start"
                self.notify("Tracking stopped", severity="warning", timeout=3)
                self.query_one("#clear-btn").disabled = False
            else: 
                self.tracking = True
                event.button.label = "Stop tracking"
                event.button.classes = "stop"
                self.notify("Tracking started", timeout=3)
                self.update_numbers()

                
        elif event.button.id == "clear-btn":
            self.clear = True
            
        else:
            self.query_one(ContentSwitcher).current = event.button.id

    
    def on_mount(self) -> None:
        self.title = "Satellite Tracker" 
        self.sub_title = f'Tracking {sat_name}'
        self.set_interval(1, self.update_numbers, pause=False)
    
        
    # Watch for changes and update numbers
    def on_ready(self) -> None:
        # Set initial state
        self.update_numbers()
            
    def run_tracker(self, line1, line2, sat_name, ground_station):
        
        positions = skyfieldTracker(line1, line2, sat_name, ground_station, rounding=self.rounding, print_data=False)

        return positions
            
    def update_numbers(self) -> None:
        if self.tracking:
            # Update each of the number containers
            self.data = self.run_tracker(line1, line2, sat_name, ground_station)

            for d in enumerate(self.data):
                self.query_one(f'#d{d[0]}').update(f'{d[1]}')
                
        elif self.clear:
            self.data = [str(0)] * 8
            
            for d in enumerate(self.data):
                self.query_one(f'#d{d[0]}').update(f'{d[1]}')
                
            self.clear = False
            self.query_one("#clear-btn").disabled = True
        
            
    def action_request_quit(self) -> None:
        self.app.exit()
                
        
if __name__ == "__main__":
    SatTrackApp().run()