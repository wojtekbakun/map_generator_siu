# Track Map Generator

A dynamic, tile-based track map visualizer and generator built in Python using Pygame CE. This tool acts as an interactive level editor for designing complex pathways and road networks, intelligently auto-coloring direction vectors and corners based on tile connectivity.

## Features

* **Dynamic Auto-Coloring** – Automatically maps tile colors based on road network logic: recognizes `Up`, `Down`, `Left`, `Right` flows, as well as complex multi-tile `Intersections`. 
* **Brush & Arc Tools** – Support for drawing discrete straight segments ("Road") as well as sweeping circular tracks (`Arc Left`, `Arc Right`, `Arc Top`, `Arc Bottom`). Arcs snap accurately to the grid space utilizing analytic trigonometric sub-pixel gradients to maintain completely seamless boundaries. 
* **Drag-to-Paint Interaction** – Continuous interaction loop allowing you to draw and erase roads smoothly simply by holding and dragging the mouse.
* **Scalable UI Interface** – Fully mathematically bounded layout that is 100% resizable on-the-fly (`RESIZABLE`). The map viewport perfectly frames the internal coordinate canvas while the menu remains statically anchored.
* **Responsive Hover GUI** – Interactive checklist elements, buttons, and state indicators with functional keyboard event routing.
* **Canvas Exporting** – Write any desired custom filename via the on-screen text input and directly export the rendered matrix to a flat `.png` image.

## Requirements

* Python 3.x
* [Pygame Community Edition](https://pyga.me/) (`pygame-ce`)

It is highly recommended to install dependencies inside a Python virtual environment (`venv`).

```bash
# 1. Create the virtual environment
python3 -m venv venv

# 2. Activate the virtual environment
# On macOS and Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# 3. Install the mapped requirements
pip install pygame-ce
```

## Controls & Usage

### Painting
* **Left Mouse Button (Click & Drag)**: Paints continuous straight road tiles across the grid map.
* **Arc Selection**: Selecting an Arc tool requests you to click two distinct connection points on the map. The arc is generated upon selecting the second point.
* **Right Mouse Button (Click & Drag)**: Broad eraser. Drag over existing road segments or arc endpoints to delete them and organically revert the canvas.

### User Interface
* **Direction (CW/CCW)**: Toggles the logical flow of the track, instantly recoloring the left/right and up/down vector orientations array-wide.
* **Filename Input**: Click on the filename box at the bottom right to focus it, type your desired filename using the keyboard.
* **Save Image**: Exports the map grid to `[your_filename].png` in the current working directory.
* **Clear Board**: Instantly wipes the map state to green grass.

## Running the Application

Execute the engine natively from the terminal:
```bash
python3 map_generator.py
```
