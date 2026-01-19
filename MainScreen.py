import customtkinter


class MainScreen(customtkinter.CTkFrame):
    def __init__(self, parent, screen_switch_function):
        super().__init__(parent)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self.grid_rowconfigure(2, weight=1)
        self.grid(row=0, column=0, sticky="nsew")

        app_name_label = customtkinter.CTkLabel(self, text="NETWORKING APPLICATION", font=("Rubik", 45))
        app_name_label.grid(row=0, column=0, sticky="sew")

        navigate_topology_generator = customtkinter.CTkButton(self,
                                                              text="TOPOLOGY GENERATOR",
                                                              command=lambda: screen_switch_function("TopologyGenerator"),
                                                              font=("Rubik", 30),
                                                              height=50)
        navigate_topology_generator.grid(row=1, column=0, sticky="sew", padx=100, pady=10)

        navigate_communication_generator = customtkinter.CTkButton(self,
                                                                   text="COMMUNICATION GENERATOR",
                                                                   command=lambda: screen_switch_function("CommunicationGenerator"),
                                                                   font=("Rubik", 30),
                                                                   height=50)
        navigate_communication_generator.grid(row=2, column=0, sticky="new", padx=100)