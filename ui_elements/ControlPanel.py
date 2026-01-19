import customtkinter
from ui_elements import NavigationMenu
from PIL import Image

class ControlPanel(customtkinter.CTkFrame):

    def __init__(self, master, variant, number_of_nodes,
                 topology_type, screen_switch_function, generate_topology_function,
                 generate_communication_function, stop_generating_communication_function,
                 type_of_traffic, type_of_client, server_info, is_generating,
                 save_node_link_var=None):

        if customtkinter.get_appearance_mode() == "Light":
            super().__init__(master, fg_color="white")
        else:
            super().__init__(master)

        # Initialization of variables
        self.number_of_nodes = number_of_nodes
        self.topology_type = topology_type
        self.type_of_traffic = type_of_traffic
        self.type_of_client = type_of_client
        self.server_info = server_info
        self.variant = variant
        self.is_generating = is_generating
        self.isMenuOpen = False
        self.Menu = None
        self.menu_frame = None
        self.menu_button = {}
        self.screen_switch_function = screen_switch_function
        self.generate_topology_function = generate_topology_function
        self.generate_communication_function = generate_communication_function
        self.stop_generation = stop_generating_communication_function
        self.save_node_link_var = save_node_link_var
        self.font_style = customtkinter.CTkFont(family="Rubik", size=20)

        self.client_communication_type_radio = None
        self.client_communication_server_info_label = None
        self.client_communication_server_info_radio = None

        # Grid configuration
        self._configure_grid()

        # Creation of UI elements
        self._create_menu_and_section_name()
        self._create_controls()
        self._create_buttons()


    def _configure_grid(self):
        self.grid(row=0, column=0, sticky="nsew")
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self.grid_rowconfigure(2, weight=1)
        self.grid_rowconfigure(3, weight=1)
        self.grid_rowconfigure(4, weight=1)
        self.grid_rowconfigure(5, weight=1)
        self.grid_rowconfigure(6, weight=2)
        self.grid_rowconfigure(7, weight=2)


    def toggle_menu(self):
        if self.isMenuOpen:
            self.Menu.destroy()
            self.menu_button["opened"].grid_forget()
            self.menu_button["closed"].grid(row=0, column=0, sticky="new", padx=20, pady=10)
            self.isMenuOpen = False
        else:
            if self.variant == "topology_generator":
                self.Menu = NavigationMenu.NavigationMenu(self.menu_frame, "Topology", self.screen_switch_function, None, None)
            elif self.variant == "communication_generator":
                self.Menu = NavigationMenu.NavigationMenu(self.menu_frame, "Communication", self.screen_switch_function, self.is_generating, self.stop_generation)
            self.menu_button["closed"].grid_forget()
            self.menu_button["opened"].grid(row=0, column=0, sticky="new", padx=20, pady=10)
            self.isMenuOpen = True

    def _create_menu_and_section_name(self):
        menu_and_name = customtkinter.CTkFrame(self, fg_color=self.cget("fg_color"))
        menu_and_name.grid(row=0, column=0, sticky="sew")
        menu_and_name.grid_columnconfigure(0, weight=1)
        menu_and_name.grid_columnconfigure(1, weight=1)
        menu_and_name.grid_rowconfigure(0, weight=1)

        # Section switching menu
        menu_icon = customtkinter.CTkImage(Image.open("assets/menu_close.png"), size=(40, 40))
        menu_icon1 = customtkinter.CTkImage(Image.open("assets/menu_open.png"), size=(40, 40))
        self.menu_button["opened"] = customtkinter.CTkButton(menu_and_name, image=menu_icon1, text="", width=40, height=40, command=lambda: self.toggle_menu())
        self.menu_button["closed"] = customtkinter.CTkButton(menu_and_name, image=menu_icon, text="", width=40, height=40, command=lambda: self.toggle_menu())
        self.menu_button["closed"].grid(row=0, column=0, sticky="new", padx=20, pady=10)

        section_label = customtkinter.CTkLabel(menu_and_name, text="TOPOLOGY\nGENERATOR" if self.variant == "topology_generator" else "COMMUNICATION\nGENERATOR", font=self.font_style)
        section_label.grid(row=0, column=1, sticky="e", padx=20, pady=10)

        self.menu_frame = customtkinter.CTkFrame(self, fg_color=self.cget("fg_color"), height=60)
        self.menu_frame.grid(row=1, column=0, sticky="new")
        self.menu_frame.grid_propagate(False)


    def _create_controls(self):

        if self.variant == "topology_generator":
            # Entry field and label for entering number of devices
            number_of_devices_label = customtkinter.CTkLabel(self, text="Number of devices:", font=self.font_style)
            number_of_devices_label.grid(row=2, column=0, sticky="sw", padx=20)

            number_of_devices_input = customtkinter.CTkEntry(self, placeholder_text="Number of devices",textvariable=self.number_of_nodes, font=self.font_style)
            number_of_devices_input.grid(row=3, column=0, sticky="nwe", padx=20)

            # Dropdown input and label for choosing type of topology
            topology_type_label = customtkinter.CTkLabel(self, text="Topology Type:", font=self.font_style)
            topology_type_label.grid(row=4, column=0, sticky="sw", padx=20)

            topology_type_dropdown = customtkinter.CTkComboBox(self, values=["full-mesh", "hub-and-spoke"], variable=self.topology_type, state="readonly", font=self.font_style)
            topology_type_dropdown.grid(row=5, column=0, sticky="new", padx=20)

            # Checkbox: save as node-link format only
            if self.save_node_link_var is not None:
                save_node_link_checkbox = customtkinter.CTkCheckBox(self, text="Save in node-link format", variable=self.save_node_link_var, font=self.font_style)
                save_node_link_checkbox.grid(row=6, column=0, sticky="w", padx=20, pady=(6, 0))

        elif self.variant == "communication_generator":

            # -------------------------------------- Communication type frame, radio buttons and label --------------------------------------------------
            communication_type_radio_frame = customtkinter.CTkFrame(self, fg_color=self.cget("fg_color"))
            self._configure_communication_type_radio_grid(communication_type_radio_frame)
            self._create_communication_type_radio_variables(communication_type_radio_frame)
            self.client_communication_type_radio = communication_type_radio_frame

            # -----------------------------Client type frame, radio buttons and label ----------------------------------------------
            client_type_frame = customtkinter.CTkFrame(self, fg_color=self.cget("fg_color"))
            self._configure_client_selection_frame_grid(client_type_frame)
            self._create_client_selection_elements(client_type_frame)

            # ------------------------------- Client input for setting server IP address and port -----------------------------
            server_information_label = customtkinter.CTkLabel(self, text="Server information (IP:Port):", font=self.font_style)
            self.client_communication_server_info_label = server_information_label

            server_information_input = customtkinter.CTkEntry(self, placeholder_text="ServerIP:ServerPort",textvariable=self.server_info, font=self.font_style)
            self.client_communication_server_info_radio = server_information_input


    def _configure_communication_type_radio_grid(self, communication_type_radio_frame):
        communication_type_radio_frame.grid_columnconfigure(0, weight=1)
        communication_type_radio_frame.grid_rowconfigure(0, weight=1)
        communication_type_radio_frame.grid_rowconfigure(1, weight=1)
        communication_type_radio_frame.grid_rowconfigure(2, weight=1)
        communication_type_radio_frame.grid_rowconfigure(3, weight=1)
        communication_type_radio_frame.grid_rowconfigure(4, weight=1)
        communication_type_radio_frame.grid_rowconfigure(5, weight=1)


    def _create_communication_type_radio_variables(self, communication_type_radio_frame):
        communication_type_label = customtkinter.CTkLabel(communication_type_radio_frame, text="Communication Type:",
                                                          font=self.font_style)
        communication_type_label.grid(row=0, column=0, sticky="sw", padx=20)

        communication_type_radio1 = customtkinter.CTkRadioButton(communication_type_radio_frame,
                                                                 text="Video-On-Demand", value="video_demand",
                                                                 variable=self.type_of_traffic, font=self.font_style)
        communication_type_radio1.grid(row=1, column=0, sticky="new", pady=5)

        communication_type_radio4 = customtkinter.CTkRadioButton(communication_type_radio_frame, text="Video-live",
                                                                 value="video_live", variable=self.type_of_traffic,
                                                                 font=self.font_style)
        communication_type_radio4.grid(row=2, column=0, sticky="new", pady=5)

        communication_type_radio2 = customtkinter.CTkRadioButton(communication_type_radio_frame, text="Audio-live",
                                                                 value="audio_live", variable=self.type_of_traffic,
                                                                 font=self.font_style)
        communication_type_radio2.grid(row=3, column=0, sticky="new", pady=5)

        communication_type_radio3 = customtkinter.CTkRadioButton(communication_type_radio_frame, text="Audio-on-demand",
                                                                 value="audio_demand", variable=self.type_of_traffic,
                                                                 font=self.font_style)
        communication_type_radio3.grid(row=4, column=0, sticky="new", pady=5)

        communication_type_radio4 = customtkinter.CTkRadioButton(communication_type_radio_frame, text="VoIP",
                                                                 value="voip", variable=self.type_of_traffic,
                                                                 font=self.font_style)
        communication_type_radio4.grid(row=5, column=0, sticky="new", pady=5)


    def _configure_client_selection_frame_grid(self, client_type_frame):
        client_type_frame.grid_columnconfigure(0, weight=1)
        client_type_frame.grid_rowconfigure(0, weight=1)
        client_type_frame.grid_rowconfigure(1, weight=1)
        client_type_frame.grid(row=2, column=0, sticky="new", padx=20)


    def _create_client_selection_elements(self, client_type_frame):
        client_type_radio1 = customtkinter.CTkRadioButton(client_type_frame,
                                                          text="Server", value="server",
                                                          variable=self.type_of_client,
                                                          font=self.font_style,
                                                          command=self._toggle_client_ui)
        client_type_radio1.grid(row=0, column=0, sticky="new", pady=5)

        client_type_radio4 = customtkinter.CTkRadioButton(client_type_frame, text="Client",
                                                          value="client", variable=self.type_of_client,
                                                          font=self.font_style,
                                                          command=self._toggle_client_ui)
        client_type_radio4.grid(row=1, column=0, sticky="new", pady=5)


    def _toggle_client_ui(self):
        if self.type_of_client.get() == "client":
            if (self.client_communication_type_radio is not None
                    and self.client_communication_server_info_label is not None
                    and self.client_communication_server_info_radio is not None):
                self.client_communication_type_radio.grid(row=3, column=0, sticky="new", padx=20)
                self.client_communication_server_info_label.grid(row=4, column=0, sticky="sw", padx=20)
                self.client_communication_server_info_radio.grid(row=5, column=0, sticky="nwe", padx=20)

        elif self.type_of_client.get() == "server":
            if (self.client_communication_type_radio is not None
                    and self.client_communication_server_info_label is not None
                    and self.client_communication_server_info_radio is not None):
                self.client_communication_type_radio.grid_forget()
                self.client_communication_server_info_label.grid_forget()
                self.client_communication_server_info_radio.grid_forget()


    def _create_buttons(self):
        if self.variant == "topology_generator":
            generate_button = customtkinter.CTkButton(self, text="Generate", height=60, command=lambda: self.generate_topology_function(), font=self.font_style)
            generate_button.grid(row=7, column=0, sticky="sew", padx=20, pady=5)
        elif self.variant == "communication_generator":
            generate_button = customtkinter.CTkButton(self, text="Generate", height=60, command=lambda: self.generate_communication_function(), font=self.font_style)
            generate_button.grid(row=6, column=0, sticky="sew", padx=20, pady=5)
            stop_generation = customtkinter.CTkButton(self, text="Stop Generating", height=60, command=lambda: self.stop_generation(), font=self.font_style)
            stop_generation.grid(row=7, column=0, sticky="new", padx=20, pady=5)

