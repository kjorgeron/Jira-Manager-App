from tkinter import ttk
import tkinter as tk

light_mode = {
    "background": "#F7F7F7",  # Soft Ash
    # "primary_color": "#D2691E",  # Burnt Copper
    "primary_color": "#2E3A4F",  # Forged Steel
    "main_text": "#222222",  # Charcoal
    "muted_text": "#666666",  # Sub / Meta
    "btn_highlight": "#666666",  # Sub / Meta
    # "btn_highlight": "#E3B23C",  # Forge Gold
    "error_color": "#C45D5D",  # Itron Red
    "conf_btn_bg": "#2E3A4F",
}

dark_mode = {
    "background": "#101417",  # Gunmetal Black
    "primary_color": "#D2691E",  # Burnt Copper
    "secondary_color": "#4F6D7A",  # Slate Steel Blue
    "main_text": "#F0F0F0",  # Light Gray
    "muted_text": "#A0A0A0",  # Sub / Meta
    "btn_highlight": "#E3B23C",  # Forge Gold
    "error_color": "#C45D5D",  # Iron Red
    "conf_btn_bg": "#D2691E",
}


class ThemeManager:
    def __init__(self, root, theme):
        self.root = root
        self.theme = theme
        self.widgets = []
        self.style = ttk.Style()
        self._init_styles()

    def _init_styles(self):
        self.style.theme_use("default")

        # Combobox styling
        self.style.configure(
            "Custom.TCombobox",
            foreground=self.theme["primary_color"],
            fieldbackground=self.theme["background"],
            background=self.theme["background"],
            arrowcolor=self.theme["primary_color"],
        )

        # Handle readonly state appearance and suppress click highlight
        self.style.map(
            "Custom.TCombobox",
            fieldbackground=[("readonly", self.theme["background"])],
            foreground=[("readonly", self.theme["primary_color"])],
            arrowcolor=[
                ("active", self.theme["btn_highlight"]),
                ("readonly", self.theme["primary_color"]),
            ],
            selectbackground=[("!disabled", self.theme["background"])],
            selectforeground=[("!disabled", self.theme["primary_color"])],
        )


    def register(self, widget, role):
        self.widgets.append((widget, role))
        self.apply_to_widget(widget, role)

    def apply_to_widget(self, widget, role):
        match role:
            case "label":
                widget.configure(
                    bg=self.theme["background"], fg=self.theme["primary_color"]
                )
            case "flashy_button":
                widget.configure(
                    font=("Trebuchet MS", 12, "bold"),
                    bg=self.theme["btn_highlight"],
                    fg=self.theme["background"],
                    activebackground=self.theme["primary_color"],
                    activeforeground="white",
                )
            case "base_button":
                widget.configure(
                    font=("Trebuchet MS", 12, "bold"),
                    bg=self.theme["primary_color"],
                    fg=self.theme["background"],
                    activebackground=self.theme["btn_highlight"],
                    activeforeground="white",
                )
            case "frame" | "root":
                try:
                    widget.configure(bg=self.theme["background"])
                except Exception as th_e:
                    print(f"{th_e=}")
                    print(f"{widget=}")
            case "combobox":
                widget.configure(style="Custom.TCombobox")
            case "placeholder_entry":
                widget.configure(
                    bg=self.theme["background"],
                    fg=self.theme["primary_color"],
                    insertbackground=self.theme["btn_highlight"],
                    highlightthickness=2,
                    highlightbackground=self.theme["primary_color"],
                    highlightcolor=self.theme["btn_highlight"],
                    relief=tk.FLAT,
                    bd=0,
                    font=("Arial", 14, "bold"),
                )
                widget.default_fg_color = self.theme["primary_color"]
                widget.placeholder_color = self.theme["btn_highlight"]
                widget.default_font = ("Arial", 14, "bold")
                widget.placeholder_font = ("Arial", 14, "italic")
                widget.refresh_placeholder()
            case "entry":
                widget.configure(
                    font=("Arial", 14, "bold"),
                    highlightbackground=self.theme["primary_color"],
                    highlightcolor=self.theme["btn_highlight"],
                    highlightthickness=2,
                    bd=0,
                    relief=tk.FLAT,
                    bg=self.theme["background"],
                    fg=self.theme["primary_color"],
                    insertbackground=self.theme["btn_highlight"],
                )
            case "error_border_frame":
                widget.configure(bg=self.theme["error_color"])
            case "error_canvas":
                widget.configure(bg=self.theme["background"], highlightthickness=0)
            case "border":
                widget.configure(bg=self.theme["btn_highlight"])
            case "error_label":
                widget.configure(
                    font=("Trebuchet MS", 12, "bold"),  # Clean, heroic font
                    fg=self.theme["error_color"],
                    bg=self.theme["background"],
                )

    # def update_theme(self, new_theme):
    #     self.theme = new_theme
    #     self.root.configure(bg=self.theme["background"])
    #     self._init_styles()
    #     for widget, role in self.widgets:
    #         self.apply_to_widget(widget, role)
    def update_theme(self, new_theme):
        self.theme = new_theme

        # Update root background safely
        try:
            if self.root.winfo_exists():
                self.root.configure(bg=self.theme.get("background", "#FFFFFF"))
            else:
                print("Root widget no longer exists — skipping background update.")
        except Exception as e:
            print(f"Error configuring root background: {e}")

        # Refresh styles
        self._init_styles()

        # Safely apply theme to registered widgets
        for widget, role in self.widgets:
            try:
                if widget.winfo_exists():
                    self.apply_to_widget(widget, role)
                else:
                    print(f"Skipped styling for destroyed widget (role={role}).")
            except Exception as e:
                print(f"Error applying theme to widget (role={role}): {e}")

