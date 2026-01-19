# Project README (English)

This repository contains a desktop application which has two main modules:

- Topology Generator: generates JSON files representing network topologies.
- Communication Generator: generates network traffic streams for selected real services by crafting and sending real packets.

## Technologies used:

- Python
- CustomTkinter (UI built on top of `tkinter`)
- Scapy (packet building, sending, capturing)
- Matplotlib and NetworkX (topology visualization)

## Installation

You can run the application directly with Python or inside Docker.

### Run with Python

Requires Python >= 3.13 and these packages:

| Package        | Minimum version |
|----------------|-----------------|
| Scapy          | 2.6.1           |
| Matplotlib     | 3.10.0          |
| Networkx       | 3.4.2           |
| CustomTkinter  | 5.2.2           |

After installing dependencies, place the repository files in one directory and run `Main.py` with one of these commands:

```bash
python .\\Main.py
py .\\Main.py
python3 .\\Main.py
```

### Run with Docker

If using Docker, ensure Docker is installed and use a Python image of at least `3.13.3-alpine`.

Build and run the container:

```bash
docker-compose up --build
```

Because the app includes a GUI, an X server on the host is required. The application has been used with VcXsrv. In order to use VcXsrv download it, start it with display number set to 0 and choose "Multiple windows".

## Usage

On startup the main menu lets you switch between the modules.

### Topology Generator

Enter the number of devices and choose a topology type, then click **Generate**. Save the produced JSON file and the topology graph will be displayed; you can manipulate it or save it as an image.

#### Docker + X server

In order to save generated topologies to host machine, filepath /networking_application must be used as save path. This path will save generated topology files to directory with application files on host machine. For example choosing path /networking_application and specifying file name to "topology_10_fullmesh" will save file named "topology_10_fullmesh.json" and "topology_10_fullmesh_node_link.json" to host directory .../networking_tool/ .

### Communication Generator

Run the application on two devices in the same network: set one to `Server` and the other to `Client`.

On the server click **GENERATE** and choose the network interface. The server will display `IP_address:Port` combinations for both **TCP** and **UDP**. On the client select the desired service and enter the server `IP_address:Port` (use UDP for **VoIP**, TCP for other services), then click **GENERATE** and select the client interface to start sending traffic. Use **STOP GENERATING** to stop.