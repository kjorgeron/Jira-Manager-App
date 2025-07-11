import tkinter as tk
from PIL import Image, ImageTk
from getpass import getuser
from jira_manager.utils import (
    create_toolbar,
    toolbar_action,
)
from jira_manager.custom_widgets import EntryWithPlaceholder

# WINDOW SETUP
root = tk.Tk()
root.configure(bg="white")
root.title("Jira Manager")
root.geometry("600x800")
icon_path = "images/software-engineer-logo-lightmode.png"
img = Image.open(icon_path)
resized_img = img.resize((32, 32), Image.Resampling.LANCZOS)
icon = ImageTk.PhotoImage(resized_img)
root.iconphoto(False, icon)
root.resizable(False, False)

# TOOLBAR
toolbar = create_toolbar(root)
toolbar.pack()
ui_state = {"active_panel": None}

tk.Button(
    toolbar,
    text="Configure",
    font=("Trebuchet MS", 12, "bold"),
    bg="#4C30EB",
    fg="white",
    activebackground="#2C2C2C",  # Hover color
    activeforeground="white",
    command=lambda: toolbar_action(root, {"type": "configure", "jql": ""}, ui_state),
).pack(side="left", padx=10)


tk.Button(
    toolbar,
    text="Search Jira",
    font=("Trebuchet MS", 12, "bold"),
    bg="#4C30EB",
    fg="white",
    activebackground="#2C2C2C",  # Hover color
    activeforeground="white",
    command=lambda: toolbar_action(root, {"type": "search_jiras", "jql": jql_search.get()}, ui_state),
).pack(side="left", padx=10)

jql_search = EntryWithPlaceholder(toolbar, placeholder="Enter proper JQL query...", color="grey", initial_text=None,font=("Arial", 12, "bold"), width=25)
jql_search.pack(side="left", padx=10)

# WELCOME LABEL
try:
    test_label = tk.Label(
        root,
        text=f"Welcome {getuser()}, let's manage some jira's! ",
        font=("Trebuchet MS", 12, "bold"),
        bg="white",
        fg="#4C30EB",
        width=50,
        wraplength=400,
    )
except:
    test_label = tk.Label(
        root,
        text="Welcome, let's manage some jira's!",
        font=("Trebuchet MS", 12, "bold"),
        width=50,
        wraplength=400,
    )
test_label.pack(pady=10)

# RUN APP
root.mainloop()
