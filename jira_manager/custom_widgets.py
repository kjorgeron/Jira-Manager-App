import tkinter as tk


class EntryWithPlaceholder(tk.Entry):
    def __init__(
        self,
        master=None,
        placeholder="Enter text...",
        color="grey",
        show=None,
        initial_text="",
        *args,
        **kwargs
    ):
        self.real_show = show
        kwargs["show"] = ""
        super().__init__(master, *args, **kwargs)

        self.placeholder = placeholder
        self.placeholder_color = color
        self.default_fg_color = self["fg"]

        self.bind("<FocusIn>", self._clear_placeholder)
        self.bind("<FocusOut>", self._add_placeholder)

        if initial_text:
            self.insert(0, initial_text)
            self.config(show=self.real_show)
            self["fg"] = self.default_fg_color
        else:
            self._add_placeholder()

    def _add_placeholder(self, *args):
        if not self.get():
            self.config(show="")
            self.insert(0, self.placeholder)
            self["fg"] = self.placeholder_color

    def _clear_placeholder(self, *args):
        if self["fg"] == self.placeholder_color:
            self.delete(0, tk.END)
            self.config(show=self.real_show)
            self["fg"] = self.default_fg_color

    def reset_to_placeholder(self):
        self.delete(0, tk.END)
        self._add_placeholder()


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

        self.scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        self.scrollable_frame.bind_all("<MouseWheel>", on_scroll)

        canvas.pack(side="left", fill="both", expand=True)

