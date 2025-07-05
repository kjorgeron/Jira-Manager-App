import tkinter as tk


def create_jira_card(parent, title, description, aspect_ratio=3.0, radius=20):
    # Create a canvas to draw the rounded background
    canvas = tk.Canvas(parent, bg=parent["bg"], highlightthickness=0)
    canvas.config(width=300, height=100)  # Initial size

    # Create a frame to hold the content
    content = tk.Frame(canvas, bg="white")

    # Add title and description
    tk.Label(
        content,
        text=title,
        font=("Arial", 12, "bold"),
        bg="white",
        anchor="center",
        justify="center",
    ).pack(pady=(5, 2))
    tk.Label(
        content, text=description, wraplength=280, justify="center", bg="white"
    ).pack(pady=(0, 5))

    # Draw rounded rectangle on canvas
    def draw_rounded_rect(w, h):
        canvas.delete("bg")
        x1, y1, x2, y2 = 0, 0, w, h
        r = radius
        points = [
            x1 + r,
            y1,
            x2 - r,
            y1,
            x2,
            y1,
            x2,
            y1 + r,
            x2,
            y2 - r,
            x2,
            y2,
            x2 - r,
            y2,
            x1 + r,
            y2,
            x1,
            y2,
            x1,
            y2 - r,
            x1,
            y1 + r,
            x1,
            y1,
        ]
        canvas.create_polygon(
            points, fill="white", outline="#ccc", smooth=True, tags="bg"
        )

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
    toolbar = tk.Frame(parent, bg=bg, pady=padding)
    toolbar.pack(fill="x", padx=padding, pady=(padding, 0))
    return toolbar


def create_button(parent, text, command, **style):
    return tk.Button(parent, text=text, command=command, **style)


def error_message(parent, message: str):
    pass


def toolbar_action(parent, options: dict, state: dict):
    # Remove previous panel if exists
    if state["active_panel"]:
        state["active_panel"].destroy()
        state["active_panel"] = None

    if not options:
        return

    if options["type"] == "configure":
        try:
            panel = tk.Frame(parent, bg="blue")
            tk.Label(
                panel,
                text="Jira Server: ",
                font=("Arial", 12, "bold"),
                fg="white",
                bg="blue",
            ).grid(row=0, column=0)
            tk.Entry(panel).grid(row=0, column=1, rowspan=2)
            panel.pack(fill="both", padx=10, pady=10, expand=1)
        except Exception as e:
            print("Error:", e)
            panel = tk.Frame(parent, bg="red")
            tk.Label(
                panel,
                text=f"Failed to create Configure Panel\nReason: {e}",
                font=("Arial", 12, "bold"),
                fg="white",
                bg="red",
                wraplength=500
            ).pack(padx=10, pady=10)
            panel.pack(fill="both", padx=10, pady=10)
        state["active_panel"] = panel

    elif options["type"] == "search_jiras":
        panel = tk.Frame(parent, bg="green")
        tk.Label(
            panel,
            text="Search Jira Panel",
            font=("Arial", 12, "bold"),
            fg="white",
            bg="green",
        ).pack(pady=10)
        panel.pack(fill="both", expand=True, padx=10, pady=10)
        state["active_panel"] = panel
