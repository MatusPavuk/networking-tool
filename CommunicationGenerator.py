import customtkinter
import scapy.interfaces
from scapy.all import *
import Server
import Client
from ui_elements import VisualizationAndOutput, ControlPanel


class CommunicationGenerator(customtkinter.CTkFrame):
    def __init__(self, parent, screen_switch_function):
        super().__init__(parent)
        # Grid configuration -> 1row 2columns
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=3)
        self.grid_rowconfigure(0, weight=1)
        self.grid(row=0, column=0, sticky="nsew")

        # Declaration and initialization of variables
        self.type_of_traffic = customtkinter.StringVar()
        self.type_of_client = customtkinter.StringVar()
        self.server_ip_port = customtkinter.StringVar()
        self.screen_switch_function = screen_switch_function
        self.stop_generation = threading.Event()
        self.is_generating = customtkinter.BooleanVar()
        self.root = parent

        # Creation of UI elements
        self.control_panel = ControlPanel.ControlPanel(self, "communication_generator", None, None, self.screen_switch_function, None, self.generate_communication, self.stop_generating, self.type_of_traffic, self.type_of_client, self.server_ip_port, self.is_generating)
        self.visualization = VisualizationAndOutput.VisualizationAndOutput(self)


    def generate_communication(self):

        if self.is_generating.get():
            self.visualization.print_text("Generating in process. Stop generation, before generating new communication.\n")

        else:
            nic = self.nic_selection()
            if not nic:
                self.visualization.print_text("No NIC selected.\n")
            else:
                if self.type_of_client.get() == "client":

                    if self.type_of_traffic.get() in ["video_demand", "video_live", "audio_live", "audio_demand", "voip"]:

                        if self._is_valid_server_ip_port():
                            ip, port = self.server_ip_port.get().split(":")
                            self.start_client(ip, int(port), nic)
                            self.is_generating.set(True)
                        else:
                            self.visualization.print_text("Enter server IP and port.\n")
                    else:
                        self.visualization.print_text("Choose type of traffic.\n")

                elif self.type_of_client.get() == "server":
                    self.start_server(nic)
                    self.is_generating.set(True)


    def start_server(self, nic):
        server = Server.Server(self.stop_generation, self.visualization.print_text, nic, self.is_generating)
        server_thread = threading.Thread(target=server.start_and_handle_connection, daemon=True)
        server_thread.start()


    def start_client(self, server_ip, server_port, nic):
        client = Client.Client(self.type_of_traffic.get(), server_ip, server_port, nic, self.stop_generation, self.is_generating)
        client_thread = threading.Thread(target=client.establish_and_handle_connection, daemon=True)
        client_thread.start()


    def stop_generating(self):
        if self.is_generating.get():
            self.visualization.print_text("Stopping generation.\n")
            self.stop_generation.set()
            self.is_generating.set(False)
        else:
            self.visualization.print_text("No generation in process, nothing to stop.\n")


    def _is_valid_server_ip_port(self):
        if self.server_ip_port.get():
            match = re.match(r"^(\d{1,3}(?:\.\d{1,3}){3}):(\d+)$", self.server_ip_port.get())
            if not match:
                return False
            ip_parts = match.group(1).split('.')
            port = int(match.group(2))
            return int(ip_parts[0]) > 0 and all(0 <= int(part) <= 255 for part in ip_parts[1:]) and 1 <= port <= 65535
        return False


    def nic_selection(self):
        popup = customtkinter.CTkToplevel()
        self._set_up_popup(popup)

        # Bring popup window to the front and disable interaction with main window
        popup.lift()
        popup.focus_force()
        popup.grab_set()

        popup_choice = customtkinter.StringVar()
        self._list_available_nics(popup, popup_choice)

        confirm_selection = customtkinter.CTkButton(popup, text="Confirm", command=lambda: popup.destroy())
        confirm_selection.pack(pady=20)

        popup.protocol("WM_DELETE_WINDOW", lambda: popup.destroy())
        popup.wait_window()
        return popup_choice.get().split(" ")[0] if popup_choice.get() else None


    def _set_up_popup(self, popup):
        popup.resizable(False, False)
        popup_width = 600
        popup_height = 200

        # Compute coordinates so popup is in center of the screen
        screen_width = popup.winfo_screenwidth()
        screen_height = popup.winfo_screenheight()
        x = int((screen_width / 2) - (popup_width / 2))
        y = int((screen_height / 2) - (popup_height / 2))

        popup.geometry(f"{popup_width}x{popup_height}+{x}+{y}")
        popup.title("NIC Selection")


    def _list_available_nics(self, popup, popup_choice):
        interfaces = scapy.interfaces.get_if_list()
        options = []

        for interface in interfaces:
            interface_ip_address = get_if_addr(interface)
            if interface_ip_address and interface_ip_address != "0.0.0.0":
                options.append(interface + " - " + get_if_addr(interface))

        nics_label = customtkinter.CTkLabel(popup,
                                            text="Select NIC:")
        nics_label.pack(pady=10)

        nics = customtkinter.CTkOptionMenu(popup,
                                           width=500,
                                           values=options,
                                           variable=popup_choice)
        nics.pack(pady=15)