import customtkinter
import networkx
import matplotlib.pyplot as plt
from matplotlib.backends._backend_tk import NavigationToolbar2Tk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


class VisualizationAndOutput(customtkinter.CTkFrame):

    def __init__(self, parent):
        super().__init__(parent)
        # Configure grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=3)
        self.grid_rowconfigure(1, weight=1)
        self.grid(row=0, column=1, sticky="nsew")

        # Create and configure visualization canvas for drawing graphs of topologies
        self.visualization_canvas = customtkinter.CTkFrame(self)
        self.visualization_canvas.grid(row=0, column=0, sticky="nsew")

        # Create and configure output area for writing messages for communication with user
        self.output_panel = customtkinter.CTkTextbox(master=self)
        self.output_panel.grid(row=1, column=0, sticky="nsew")
        self.output_panel.configure(state="disabled")


    # Method for printing text to output area / panel
    def print_text(self, text):
        if text is not None and len(text) > 0:
            self.output_panel.configure(state="normal")
            self.output_panel.insert(customtkinter.END, text)
            self.output_panel.configure(state="disabled")


    # Method for printing visualization of topology as graph to visualization canvas
    def draw_graph(self, G):
        # Configure grid in visualization_panel
        self.visualization_canvas.grid_columnconfigure(0, weight=1)
        self.visualization_canvas.grid_rowconfigure(0, weight=6)
        self.visualization_canvas.grid_rowconfigure(1, weight=1)

        fig, ax = plt.subplots()
        fig.set_size_inches(5, 4)
        networkx.draw(G, ax=ax, with_labels=True)

        # Integration of graph to tkinter
        canvas = FigureCanvasTkAgg(fig, master=self.visualization_canvas)
        canvas_widget = canvas.get_tk_widget()
        canvas_widget.grid(column=0, row=0, sticky="nsew")

        toolbar_frame = customtkinter.CTkFrame(master=self.visualization_canvas)
        toolbar_frame.grid(row=1, column=0, sticky="nsew")
        toolbar = NavigationToolbar2Tk(canvas, toolbar_frame)
        toolbar.update()


    # Method to construct graph from given topology represented as dictionary
    def construct_graph(self, topology):
        G = networkx.Graph()

        G.add_nodes_from(topology["nodes"].keys())

        for edge in topology["edges"]:
            G.add_edge(edge["start_node_id"], edge["end_node_id"])

        print(G.nodes)
        print(G.edges)
        self.draw_graph(G)