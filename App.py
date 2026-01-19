import customtkinter
import TopologyGenerator
import CommunicationGenerator
import MainScreen


class App(customtkinter.CTk):
    def __init__(self):
        super().__init__()
        self.geometry("800x600")
        self.title("Networking application")
        self.resizable(False, False)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        topology_generator = TopologyGenerator.TopologyGenerator(self, self.switch_screen)
        communication_generator = CommunicationGenerator.CommunicationGenerator(self, self.switch_screen)
        main_screen = MainScreen.MainScreen(self, self.switch_screen)

        self.frames = {
            "MainScreen": main_screen,
            "TopologyGenerator": topology_generator,
            "CommunicationGenerator": communication_generator
        }


    def switch_screen(self, screen_name):
        if screen_name in self.frames and self.frames[screen_name] is not None:
            frame = self.frames[screen_name]
            frame.tkraise()