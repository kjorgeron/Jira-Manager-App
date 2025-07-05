import tkinter as tk

def create_jira_card(parent, title, description, aspect_ratio=3.0, radius=20):
    # Create a canvas to draw the rounded background
    canvas = tk.Canvas(parent, bg=parent["bg"], highlightthickness=0)
    canvas.config(width=300, height=100)  # Initial size

    # Create a frame to hold the content
    content = tk.Frame(canvas, bg="white")

    # Add title and description
    tk.Label(content, text=title, font=("Arial", 12, "bold"), bg="white", anchor="center", justify="center").pack(pady=(5, 2))
    tk.Label(content, text=description, wraplength=280, justify="center", bg="white").pack(pady=(0, 5))

    # Draw rounded rectangle on canvas
    def draw_rounded_rect(w, h):
        canvas.delete("bg")
        x1, y1, x2, y2 = 0, 0, w, h
        r = radius
        points = [
            x1+r, y1,
            x2-r, y1,
            x2, y1,
            x2, y1+r,
            x2, y2-r,
            x2, y2,
            x2-r, y2,
            x1+r, y2,
            x1, y2,
            x1, y2-r,
            x1, y1+r,
            x1, y1
        ]
        canvas.create_polygon(points, fill="white", outline="#ccc", smooth=True, tags="bg")

    # Handle resizing and aspect ratio
    def enforce_aspect(event):
        width = event.width
        height = int(width / aspect_ratio)
        canvas.config(width=width, height=height)
        draw_rounded_rect(width, height)
        canvas.coords("content", width // 2, height // 2)

    # Bind resize event
    canvas.bind("<Configure>", enforce_aspect)

    # Place content in the center of the canvas
    canvas.create_window(0, 0, window=content, anchor="center", tags="content")

    return canvas

def create_toolbar(parent, bg="#4C30EB", padding=10):
    """
    Create and return a toolbar frame anchored at the top of the parent.

    Args:
        parent (tk.Widget): The container to add the toolbar to.
        bg (str): Background color of the toolbar.
        padding (int): Padding around the toolbar.

    Returns:
        tk.Frame: A styled toolbar frame.
    """
    toolbar = tk.Frame(parent, bg=bg, pady=padding)
    toolbar.pack(fill="x", padx=padding, pady=(padding, 0))
    return toolbar


def create_button(parent, text, command, **style):
    """
    Create and return a Tkinter button with optional styling.

    Args:
        parent (tk.Widget): The parent container.
        text (str): The label on the button.
        command (function): The callback function.
        **style: Additional styling options (bg, fg, font, padx, etc.)

    Returns:
        tk.Button: A configured button widget.
    """
    return tk.Button(parent, text=text, command=command, **style)

def toolbar_action(options: dict = None):
    if options != None:
        if options["type"] == "configure":
            print("configure mode")
        if options["type"] == "search_jiras":
            print("search_mode")
    else:
        pass