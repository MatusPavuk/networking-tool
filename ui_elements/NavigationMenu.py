import customtkinter


class NavigationMenu(customtkinter.CTkFrame):
    def __init__(self, parent, variant, screen_switch_function, is_generating, stop_generating):
        super().__init__(parent, fg_color=parent.cget("fg_color"))
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self.grid(row=1, column=0, sticky="nw", padx=20)
        self.font_style = customtkinter.CTkFont(family="Rubik", size=20)
        self.is_generating = is_generating
        self.stop_generating = stop_generating
        self.screen_switch_function = screen_switch_function

        if variant == "Topology":
            communication_navigation = customtkinter.CTkButton(self, text="Communication Generator", command=lambda: screen_switch_function("CommunicationGenerator"), font=self.font_style)
            communication_navigation.grid(row=0, column=0, sticky="nsew")

        elif variant == "Communication":
            topology_navigation = customtkinter.CTkButton(self, text="Topology Generator", command=lambda: self._switch_from_communication_screen(), font=self.font_style)
            topology_navigation.grid(row=0, column=0, sticky="nsew")

        main_menu_navigation = customtkinter.CTkButton(self, text="Main Menu", command=lambda: screen_switch_function("MainScreen"), font=self.font_style)
        main_menu_navigation.grid(row=1, column=0, sticky="nsew")


    def _switch_from_communication_screen(self):
        if self.is_generating.get():
            self.stop_generating()
        self.screen_switch_function("TopologyGenerator")