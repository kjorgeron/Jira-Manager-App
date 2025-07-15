light_mode = {
    "background" : "#F7F7F7", # Soft Ash
    "primary_color": "#D2691E", # Burnt Copper
    "secondary_color": "#2E3A4F", # Forged Steel
    "main_text": "#222222", # Charcoal
    "muted_text": "#666666", # Sub / Meta 
    "btn_highlight": "#E3B23C", # Forge Gold
    "error_color": "#C45D5D", # Itron Red
}

dark_mode = {
    "background" : "#101417", # Gunmetal Black
    "primary_color": "#D2691E", # Burnt Copper
    "secondary_color": "#4F6D7A", # Slate Steel Blue
    "main_text": "#F0F0F0", # Light Gray
    "muted_text": "#A0A0A0", # Sub / Meta 
    "btn_highlight": "#E3B23C", # Forge Gold
    "error_color": "#C45D5D", # Iron Red
}


class ThemeManager:
    def __init__(self, root, theme):
        self.root = root
        self.theme = theme
        self.widgets = []

    def register(self, widget, role):
        self.widgets.append((widget, role))
        self.apply_to_widget(widget, role)

    def apply_to_widget(self, widget, role):
        if role == "label":
            widget.configure(bg=self.theme["background"], fg=self.theme["foreground"])
        elif role == "button":
            widget.configure(bg=self.theme["button_bg"], fg=self.theme["button_fg"])
        elif role == "frame":
            widget.configure(bg=self.theme["background"])

    def update_theme(self, new_theme):
        self.theme = new_theme
        self.root.configure(bg=self.theme["background"])
        for widget, role in self.widgets:
            self.apply_to_widget(widget, role)

def switch_theme(theme_manager):
    new_theme = dark_mode if theme_manager.theme == light_mode else light_mode
    theme_manager.update_theme(new_theme)
