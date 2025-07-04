import tkinter as tk
from PIL import Image, ImageTk

# WINDOW SETUP
root = tk.Tk()
root.title("Jira Manager")
root.geometry("600x800")
icon_path = "images/software-engineer-logo-lightmode.png"
img = Image.open(icon_path)
resized_img = img.resize((32, 32), Image.Resampling.LANCZOS)
icon = ImageTk.PhotoImage(resized_img)
root.iconphoto(False, icon)

# TEST LABEL
test_label = tk.Label(root, text="Test Label")
test_label.pack()
root.mainloop()