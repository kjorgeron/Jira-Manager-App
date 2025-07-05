import tkinter as tk
from PIL import Image, ImageTk
from jira_manager.utils import create_jira_card, create_toolbar, create_button, toolbar_action

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

config_btn = create_button(toolbar, "Configure", lambda: toolbar_action({"type": "configure"}))
config_btn.pack(side="left", padx=10)
search_btn = create_button(toolbar, "Search Jira", lambda: toolbar_action({"type": "search_jiras"}))
search_btn.pack(side="left")

# TEST LABEL
test_label = tk.Label(root, text="Test Label")
test_label.pack()

# TEST JIRA CARD
title = "SCRUM-1"
description = "Test Jira Ticket"
card1 = create_jira_card(root, title, description, 3.0)
card1.pack()

# RUN APP
root.mainloop()