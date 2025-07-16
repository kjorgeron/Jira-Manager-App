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
}

dark_mode = {
    "background": "#101417",  # Gunmetal Black
    "primary_color": "#D2691E",  # Burnt Copper
    "secondary_color": "#4F6D7A",  # Slate Steel Blue
    "main_text": "#F0F0F0",  # Light Gray
    "muted_text": "#A0A0A0",  # Sub / Meta
    "btn_highlight": "#E3B23C",  # Forge Gold
    "error_color": "#C45D5D",  # Iron Red
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

    # def _init_styles(self):
    #     # Use "clam" for extended styling support
    #     self.style.theme_use("clam")

    #     # Custom label style (optional if not using ttk.Label)
    #     self.style.configure(
    #         "Custom.TLabel",
    #         background=self.theme["background"],
    #         foreground=self.theme["primary_color"],
    #     )

    #     # Custom button style
    #     self.style.configure(
    #         "Custom.TButton",
    #         background=self.theme["background"],
    #         foreground=self.theme["primary_color"],
    #         borderwidth=0,
    #         padding=6,
    #     )

    #     # Custom combobox styling with dynamic border highlights
    #     self.style.configure(
    #         "Custom.TCombobox",
    #         foreground=self.theme["primary_color"],
    #         fieldbackground=self.theme["background"],
    #         borderwidth=2,
    #         relief="flat",
    #     )
    #     self.style.map(
    #         "Custom.TCombobox",
    #         fieldbackground=[
    #             ("readonly", self.theme["background"]),
    #             ("!readonly", self.theme["background"]),
    #         ],
    #         foreground=[
    #             ("readonly", self.theme["primary_color"]),
    #             ("!readonly", self.theme["primary_color"]),
    #         ],
    #         bordercolor=[
    #             ("focus", self.theme["btn_highlight"]),
    #             ("!focus", self.theme["primary_color"]),
    #         ],
    #     )

    #     # Combobox styling
    #     self.style.configure(
    #         "Custom.TCombobox",
    #         foreground=self.theme["primary_color"],
    #         fieldbackground=self.theme["background"],
    #     )
    #     self.style.map(
    #         "Custom.TCombobox",
    #         fieldbackground=[("readonly", self.theme["background"])],
    #         foreground=[("readonly", self.theme["primary_color"])],
    #     )

    def register(self, widget, role):
        self.widgets.append((widget, role))
        self.apply_to_widget(widget, role)

    def apply_to_widget(self, widget, role):
        match role:
            case "label":
                widget.configure(
                    bg=self.theme["background"], fg=self.theme["primary_color"]
                )
            case "button":
                widget.configure(bg=self.theme["button_bg"], fg=self.theme["button_fg"])
            case "frame" | "root":
                widget.configure(bg=self.theme["background"])
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
                widget.reset_to_placeholder()
            case "entry":
                widget.configure(
                    font=("Arial", 14, "bold"),  # Or font_style if you're passing it in
                    highlightbackground=self.theme["primary_color"],  # Unfocused
                    highlightcolor=self.theme["btn_highlight"],  # Focused
                    highlightthickness=2,
                    bd=0,
                    relief=tk.FLAT,
                    bg=self.theme["background"],
                    fg=self.theme["primary_color"],
                    insertbackground=self.theme["btn_highlight"],  # Caret color
                )

    def update_theme(self, new_theme):
        self.theme = new_theme
        self.root.configure(bg=self.theme["background"])
        self._init_styles()  # Refresh styles with new theme
        for widget, role in self.widgets:
            self.apply_to_widget(widget, role)


def switch_theme(theme_manager):
    new_theme = dark_mode if theme_manager.theme == light_mode else light_mode
    theme_manager.update_theme(new_theme)
