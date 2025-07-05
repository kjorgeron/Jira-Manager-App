import tkinter as tk
from PIL import Image, ImageTk
from getpass import getuser
from jira_manager.utils import (
    create_toolbar,
    create_button,
    toolbar_action,
)

# WINDOW SETUP
root = tk.Tk()
root.title("Jira Manager")
root.geometry("600x800")
icon_path = "images/software-engineer-logo-lightmode.png"
img = Image.open(icon_path)
resized_img = img.resize((32, 32), Image.Resampling.LANCZOS)
icon = ImageTk.PhotoImage(resized_img)
root.iconphoto(False, icon)

# TOOLBAR
toolbar = create_toolbar(root)
toolbar.pack()

ui_state = {"active_panel": None}
create_button(toolbar, "Configure", lambda: toolbar_action(root, {"type": "configure"}, ui_state)).pack(side="left", padx=10)
create_button(toolbar, "Search Jira", lambda: toolbar_action(root, {"type": "search_jiras"}, ui_state)).pack(side="left")

# config_btn = create_button(
#     toolbar,
#     "Configure",
#     lambda: toolbar_action(root, {"type": "configure"}),
# )
# config_btn.pack(side="left", padx=10)
# search_btn = create_button(
#     toolbar,
#     "Search Jira",
#     lambda: toolbar_action(root, {"type": "search_jiras"}),
# )
# search_btn.pack(side="left")

# WELCOME LABEL
try:
    test_label = tk.Label(
        root,
        text=f"Welcome {getuser()}, let's manage some jira's! ",
        font="bold",
        width=50,
        wraplength=400,
    )
except:
    test_label = tk.Label(
        root,
        text="Welcome, let's manage some jira's!",
        font="bold",
        width=50,
        wraplength=400,
    )
test_label.pack(pady=10)

# RUN APP
root.mainloop()
