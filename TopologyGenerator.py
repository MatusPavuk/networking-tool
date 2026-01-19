import random
import string
import customtkinter
import json
import os
import networkx as nx
from networkx.readwrite import json_graph
from customtkinter import filedialog
from ui_elements import VisualizationAndOutput, ControlPanel


class TopologyGenerator(customtkinter.CTkFrame):
    def __init__(self, parent, screen_switch_function):
        super().__init__(parent)
        # Configure grid -> 1row 2columns
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=3)
        self.grid_rowconfigure(0, weight=1)
        self.grid(row=0, column=0, sticky="nsew")

        # Declare and initialize variables
        self.number_of_nodes = customtkinter.StringVar()
        self.topology_type = customtkinter.StringVar()
        self.save_node_link_only = customtkinter.BooleanVar(value=False)
        self.ip_network = [10,0,0,0]
        self.used_mac_addresses = []
        self.used_serial_numbers = []
        self.total_memory = 536870912

        # Create UI elements -> control_panel and visualization panels
        self.control_panel = ControlPanel.ControlPanel(self, "topology_generator", self.number_of_nodes, self.topology_type,screen_switch_function, self.generate_topology, None, None, None, None, None, None,self.save_node_link_only)
        self.visualization = VisualizationAndOutput.VisualizationAndOutput(self)

    # Main method for generating topologies
    def generate_topology(self):

        if (self.number_of_nodes.get().isnumeric()
                and int(self.number_of_nodes.get()) > 0
                and self.topology_type.get() in {"full-mesh", "hub-and-spoke"}):

            # Reset IP network and used addresses arrays when generating more topologies in row
            self._reset_network_and_used_addresses()

            number_of_nodes_value = int(self.number_of_nodes.get())
            topology_type_value = self.topology_type.get()
            topology = {
                "nodes": [],
                "edges": [],
                "flows": []
            }

            self._generate_nodes(topology, number_of_nodes_value)

            if topology_type_value == "full-mesh":
                self.generate_edges_fullmesh(topology, number_of_nodes_value)
            elif topology_type_value == "hub-and-spoke":
                self.generate_edges_hubandspoke(topology, number_of_nodes_value)

            self.visualization.construct_graph(topology)

            self._save_topology(topology)
            return

        self.visualization.print_text("Insert number of nodes and choose topology type.\n")
        return


    def _reset_network_and_used_addresses(self):
        if self.ip_network != [10, 0, 0, 0]:
            self.ip_network = [10, 0, 0, 0]
        if self.used_serial_numbers is not []:
            self.used_serial_numbers = []
        if self.used_mac_addresses is not []:
            self.used_mac_addresses = []


    def _save_topology(self, topology):
        save_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=(("json files", "*.json"), ("all files", "*.*")),
            title="Save topology file as"
        )

        # normalize dialog result
        if isinstance(save_path, (tuple, list)):
            save_path = save_path[0] if save_path else ''

        # if a file-like object was returned (asksaveasfile), get its name
        if hasattr(save_path, 'name'):
            try:
                save_path = save_path.name
            except Exception:
                save_path = str(save_path)

        # handle cancel or empty
        if not save_path:
            self.visualization.print_text("No file selected or file save interrupted.\n")
            return

        # normalize and absolute path
        save_path_abs = os.path.abspath(os.path.expanduser(save_path))

        # if user selected to save only node-link format, write node-link to chosen name (no suffix)
        try:
            save_node_link_only = bool(self.save_node_link_only.get()) if hasattr(self, 'save_node_link_only') else False
        except Exception:
            save_node_link_only = False

        if save_node_link_only:
            try:
                # create parent directory if necessary
                parent = os.path.dirname(save_path_abs)
                if parent and not os.path.isdir(parent):
                    os.makedirs(parent, exist_ok=True)

                # write node-link JSON directly to chosen path
                self._save_node_link(topology, save_path_abs, add_suffix=False)
            except Exception as e:
                self.visualization.print_text(f"Failed to save node-link topology: {e}\n")
            return
        
        else:
            self._save_original_format(topology, save_path_abs)


    def _save_node_link(self, topology, original_save_path, add_suffix=True):
        """Convert topology to a NetworkX graph and save node-link JSON."""
        # Ensure nodes are a list of node dicts
        nodes = topology.get("nodes")
        if isinstance(nodes, dict):
            nodes = list(nodes.values())

        G = nx.Graph()

        # Add nodes with attributes
        for n in nodes:
            node_id = n.get("node_id")
            # copy node attributes except node_id to avoid duplication
            attrs = {k: v for k, v in n.items() if k != "node_id"}
            G.add_node(node_id, **attrs)

        # Add edges with attributes
        for e in topology.get("edges", []):
            u = e.get("start_node_id")
            v = e.get("end_node_id")
            # copy edge attributes except start/end ids
            edge_attrs = {k: v for k, v in e.items() if k not in {"start_node_id", "end_node_id"}}
            # include edge id if present
            G.add_edge(u, v, **edge_attrs)

        node_link_data = json_graph.node_link_data(G, edges="edges")

        node_link_path = original_save_path

        # Ensure parent directory exists
        parent = os.path.dirname(node_link_path)
        if parent and not os.path.isdir(parent):
            os.makedirs(parent, exist_ok=True)

        with open(node_link_path, 'w', encoding='utf-8') as f:
            json.dump(node_link_data, f, indent=4, ensure_ascii=False)
            try:
                f.flush()
                os.fsync(f.fileno())
            except Exception:
                pass

        self.visualization.print_text("NetworkX node-link topology saved to " + node_link_path + "\n")


    def _save_original_format(self, topology, save_path_abs):
        """Save topology in the original JSON format to save_path_abs."""
        try:
            parent = os.path.dirname(save_path_abs)
            if parent and not os.path.isdir(parent):
                os.makedirs(parent, exist_ok=True)

            with open(save_path_abs, 'w', encoding='utf-8') as file:
                nodes_as_list = list(topology["nodes"].values()) if isinstance(topology.get("nodes"), dict) else topology.get("nodes")
                topology["nodes"] = nodes_as_list
                json.dump(topology, file, indent=4, ensure_ascii=False)
                file.flush()
                try:
                    os.fsync(file.fileno())
                except Exception:
                    pass

            if os.path.exists(save_path_abs):
                self.visualization.print_text(f"Topology saved to {save_path_abs}\n")
            else:
                self.visualization.print_text(f"Failed to save topology to {save_path_abs}\n")
        except Exception as e:
            self.visualization.print_text(f"Error saving topology: {e}\n")


    def _generate_nodes(self, topology, number_of_nodes):

        topology["nodes"] = {
            i: {
                "serial_number": self._generate_unique_serial_number(),
                "node_id": i,
                "hostname": f"R{i}",
                "interfaces": []
            }
            for i in range(number_of_nodes)
        }


    def generate_interface(self, topology, node_index_from, node_index_to, ip, ip_neighbour):
        topology["nodes"][node_index_from]["interfaces"].append({
            "name": f"GigabitEthernet0/0/{node_index_to-1 if node_index_to > 0 else 0}",
            "description": f"Connection to R{node_index_to}",
            "ip_address": ip,
            "subnet_mask": "255.255.255.252",
            "prefix_length": "30",
            "mac_address": self._generate_new_mac_address(),
            "status": "up",
            "line_protocol": "up",
            "transport_information": {
                "bandwidth": "1000000",
                "delay": "10",
                "input_packets": "0",
                "input_bytes": "0",
                "output_packets": "0",
                "output_bytes": "0",
                "input_error": "0",
                "output_error": "0"
            },
            "neighbor": {
                "neighbor_name": f"R{node_index_to}",
                "neighbor_ip_address": ip_neighbour,
                "neighbor_interface": "",
                "neighbor_mac_address": ""
            }
        })

        used_memory = random.randint(int(self.total_memory * 0.2),int(self.total_memory * 0.7))
        free_memory = self.total_memory - used_memory

        topology["nodes"][node_index_from].update({
            "cpu_utilization": {
                "5_second": random.randint(5, 30),
                "1_minute": random.randint(3, 20),
                "5_minute": random.randint(2, 15)
            },
            "memory_utilization": {
                "total": self.total_memory,
                "used": used_memory,
                "free": free_memory
            },
            "static_routes": [
                {
                    "destination_address": "",
                    "destination_prefix": "",
                    "destination_prefix_length": "",
                    "next_hop_address": "",
                    "output_interface": ""
                }
            ],
            "existing_flows": [],
            "running_config": "<output of show running-config command>"
        })


    def generate_edges_fullmesh(self, topology, number_of_nodes):

        edge_id = 0
        for start_node_id in range(number_of_nodes):
            for end_node_id in range(start_node_id + 1, number_of_nodes):

                start_ip = f"{self.ip_network[0]}.{self.ip_network[1]}.{self.ip_network[2]}.{self.ip_network[3]+1}"
                end_ip = f"{self.ip_network[0]}.{self.ip_network[1]}.{self.ip_network[2]}.{self.ip_network[3]+2}"

                topology["edges"].append({
                    "edge_id": edge_id,
                    "start_node_id": start_node_id,
                    "start_node_interface": "",
                    "start_node_address": start_ip,
                    "end_node_id": end_node_id,
                    "end_node_interface": "",
                    "end_node_address": end_ip,
                    "enabled": True,
                    "speed": "1000",
                    "availableBandwidth": "1000",
                    "existing_flows": []
                })
                edge_id += 1

                # Interface with connection to end_node from start_node
                if start_node_id in topology["nodes"]:
                    self.generate_interface(topology, start_node_id, end_node_id, start_ip, end_ip)
                    topology["edges"][edge_id - 1]["start_node_interface"] = topology["nodes"][start_node_id]["interfaces"][-1]["name"]

                # Interface with connection to start_node from end_node
                if end_node_id in topology["nodes"]:
                    self.generate_interface(topology, end_node_id, start_node_id, end_ip, start_ip)
                    topology["edges"][edge_id - 1]["end_node_interface"] = topology["nodes"][end_node_id]["interfaces"][-1]["name"]

                # Put name of neighbor interface to start_node and end_node
                if start_node_id in topology["nodes"] and end_node_id in topology["nodes"]:
                    start_int = topology["nodes"][start_node_id]["interfaces"][-1]["name"]
                    start_mac = topology["nodes"][start_node_id]["interfaces"][-1]["mac_address"]
                    end_int = topology["nodes"][end_node_id]["interfaces"][-1]["name"]
                    end_mac = topology["nodes"][end_node_id]["interfaces"][-1]["mac_address"]
                    topology["nodes"][start_node_id]["interfaces"][-1]["neighbor"]["neighbor_interface"] = end_int
                    topology["nodes"][start_node_id]["interfaces"][-1]["neighbor"]["neighbor_mac_address"] = end_mac
                    topology["nodes"][end_node_id]["interfaces"][-1]["neighbor"]["neighbor_interface"] = start_int
                    topology["nodes"][end_node_id]["interfaces"][-1]["neighbor"]["neighbor_mac_address"] = start_mac

                self.update_network()


    def generate_edges_hubandspoke(self, topology, number_of_nodes):

        edge_id = 0
        for i in range(1, number_of_nodes):

            start_ip = f"{self.ip_network[0]}.{self.ip_network[1]}.{self.ip_network[2]}.{self.ip_network[3] + 1}"
            end_ip = f"{self.ip_network[0]}.{self.ip_network[1]}.{self.ip_network[2]}.{self.ip_network[3] + 2}"

            topology["edges"].append({
                "edge_id": edge_id,
                "start_node_id": 0,
                "start_node_interface": "",
                "start_node_address": start_ip,
                "end_node_id": i,
                "end_node_interface": "",
                "end_node_address": end_ip,
                "enabled": True,
                "speed": "",
                "availableBandwidth": "",
                "existing_flows": []
            })
            edge_id += 1

            if 0 in topology["nodes"]:
                self.generate_interface(topology, 0, i, start_ip, end_ip)
                topology["edges"][edge_id - 1]["start_node_interface"] = topology["nodes"][0]["interfaces"][-1]["name"]

            if i in topology["nodes"]:
                self.generate_interface(topology, i, 0, end_ip, start_ip)
                topology["edges"][edge_id - 1]["end_node_interface"] = topology["nodes"][i]["interfaces"][-1]["name"]

            if i in topology["nodes"] and 0 in topology["nodes"]:
                start_int = topology["nodes"][0]["interfaces"][-1]["name"]
                start_mac = topology["nodes"][0]["interfaces"][-1]["mac_address"]
                end_int = topology["nodes"][i]["interfaces"][-1]["name"]
                end_mac = topology["nodes"][i]["interfaces"][-1]["mac_address"]
                topology["nodes"][0]["interfaces"][-1]["neighbor"]["neighbor_interface"] = end_int
                topology["nodes"][0]["interfaces"][-1]["neighbor"]["neighbor_mac_address"] = end_mac
                topology["nodes"][i]["interfaces"][-1]["neighbor"]["neighbor_interface"] = start_int
                topology["nodes"][i]["interfaces"][-1]["neighbor"]["neighbor_mac_address"] = start_mac

            self.update_network()


    # Function to update ip_address variable to next network address
    def update_network(self):
        self.ip_network[3] += 4
        # 4th octet is equal to 256 => increment 3rd octet by one
        if self.ip_network[3] == 256:
            self.ip_network[3] = 0
            self.ip_network[2] += 1
        # 3rd octet is equal to 256 => increment 2nd octet by one
        if self.ip_network[2] == 256:
            self.ip_network[2] = 0
            self.ip_network[1] += 1
        # 2nd octet is equal to 256 => increment 1st octet by one
        if self.ip_network[1] == 256:
            self.ip_network[1] = 0
            self.ip_network[0] += 1


    # Function for generating unique mac addresses
    def _generate_new_mac_address(self):
        new_mac_address = '.'.join(''.join(random.choices('0123456789ABCDEF', k=4)) for _ in range(3))
        while new_mac_address in self.used_mac_addresses:
            new_mac_address = '.'.join(''.join(random.choices('0123456789ABCDEF', k=4)) for _ in range(3))
        self.used_mac_addresses.append(new_mac_address)
        return new_mac_address


    # Function for generating unique serial numbers for nodes according to serial numbers of Cisco devices -> LLLYYWWXXXX
    def _generate_unique_serial_number(self):
        new_serial_number = self._create_serial_number()

        while new_serial_number in self.used_serial_numbers:
            new_serial_number = self._create_serial_number()

        self.used_serial_numbers.append(new_serial_number)
        return new_serial_number


    def _create_serial_number(self):
        factory_ids = ['FTX', 'JMX', 'CAT', 'FOX', 'FCZ', 'FHH']
        prefix = random.choice(factory_ids)

        year = random.randint(1, 29)
        year_formatted = f"{year:02d}"

        week = random.randint(1, 52)
        week_formatted = f"{week:02d}"

        identifier = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
        new_serial_number = prefix + year_formatted + week_formatted + identifier
        return new_serial_number