import tkinter as tk

class EntryWithPlaceholder(tk.Entry):
    def __init__(
        self,
        master=None,
        placeholder="Enter text...",
        initial_text="",
        show=None,
        color="grey",  # Placeholder color
        width=25,
        *args,
        **kwargs
    ):
        self.placeholder = placeholder
        self.real_show = show
        self._placeholder_active = False

        # ThemeManager will override these
        self.default_fg_color = None
        self.default_font = None
        self.placeholder_font = None
        self.placeholder_color = color

        kwargs["show"] = ""  # Ensure placeholder is visible
        super().__init__(master, width=width, *args, **kwargs)

        self.bind("<FocusIn>", self._on_focus_in)
        self.bind("<FocusOut>", self._on_focus_out)

        if initial_text:
            self.insert(0, initial_text)
            if self.real_show:
                self.config(show=self.real_show)
        else:
            self.after_idle(self._set_placeholder)

    def _set_placeholder(self):
        if not self.get():
            self._placeholder_active = True
            self.config(show="")
            self.delete(0, tk.END)
            self.insert(0, self.placeholder)
            self.config(fg=self.placeholder_color)
            if self.placeholder_font:
                self.config(font=self.placeholder_font)

    def _on_focus_in(self, event):
        if self._placeholder_active:
            self._placeholder_active = False
            self.delete(0, tk.END)
            if self.real_show:
                self.config(show=self.real_show)
            if self.default_fg_color:
                self.config(fg=self.default_fg_color)
            if self.default_font:
                self.config(font=self.default_font)

    def _on_focus_out(self, event):
        if not self.get():
            self._set_placeholder()

    def reset_to_placeholder(self):
        self._placeholder_active = False
        self.delete(0, tk.END)
        self._set_placeholder()

    def is_placeholder_active(self):
        return self._placeholder_active

    def refresh_placeholder(self):
        """Ensure placeholder is styled correctly after theme update."""
        if self._placeholder_active:
            self.config(show="")
            self.config(fg=self.placeholder_color)
            if self.placeholder_font:
                self.config(font=self.placeholder_font)
        else:
            if self.default_fg_color:
                self.config(fg=self.default_fg_color)
            if self.default_font:
                self.config(font=self.default_font)
            if self.real_show:
                self.config(show=self.real_show)

    def get_user_input(self):
        """Returns actual user input, ignoring placeholder."""
        return "" if self._placeholder_active else self.get()


class ScrollableFrame(tk.Frame):
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)

        canvas = tk.Canvas(self, borderwidth=0, highlightthickness=0)
        self.scrollable_frame = tk.Frame(canvas)

        # Hide scrollbar but retain scroll functionality
        scrollbar = tk.Scrollbar(self, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack_forget()  # 🫥 hides scrollbar from view

        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")

        def on_scroll(event):
            canvas.yview_scroll(-1 * (event.delta // 120), "units")

        self.scrollable_frame.bind(
            "<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        self.scrollable_frame.bind_all("<MouseWheel>", on_scroll)

        canvas.pack(side="left", fill="both", expand=True)


class TicketCard(tk.Frame):
    def __init__(self, ticket_data, theme_manager, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.ticket_key = ticket_data[1]  # Adjust index to match your data structure
        self.configure(padx=10, pady=5, bd=1, relief="solid")
        theme_manager.register(self, "frame")

        # Title or ticket key
        title = tk.Label(
            self,
            text=self.ticket_key,
            font=("Segoe UI", 12, "bold"),
        )
        title.pack(anchor="w")
        theme_manager.register(title, "label")

        # Optional Description or Detail
        if len(ticket_data) > 2:
            descript = tk.Label(
                self,
                text=ticket_data[2],
                font=("Segoe UI", 10),
                wraplength=400,
                justify="left"
            )
            descript.pack(anchor="w")
            theme_manager.register(descript, "label")

        # Feel free to add buttons, status indicators, icons, etc.
