import tkinter as tk
from jira_manager.sql_manager import run_sql_stmt

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


# class ScrollableFrame(tk.Frame):
#     def __init__(self, parent, *args, **kwargs):
#         super().__init__(parent, *args, **kwargs)

#         canvas = tk.Canvas(self, borderwidth=0, highlightthickness=0)
#         self.scrollable_frame = tk.Frame(canvas)

#         # Hide scrollbar but retain scroll functionality
#         scrollbar = tk.Scrollbar(self, orient="vertical", command=canvas.yview)
#         canvas.configure(yscrollcommand=scrollbar.set)
#         scrollbar.pack_forget()  # 🫥 hides scrollbar from view

#         canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")

#         def on_scroll(event):
#             canvas.yview_scroll(-1 * (event.delta // 120), "units")

#         self.scrollable_frame.bind(
#             "<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
#         )
#         self.scrollable_frame.bind_all("<MouseWheel>", on_scroll)

#         canvas.pack(side="left", fill="both", expand=True)


class TicketCard(tk.Frame):
    def __init__(self, ticket_data, theme_manager, on_click=None, selected_items=None, card_retainer=None, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.widget_registry = {}
        self.selected_items = selected_items
        self.theme_manager = theme_manager
        self.card_retainer = card_retainer  # Prevent GC of cards
        self.db_path = "jira_manager/tickets.db"

        self.ticket_key = ticket_data["key"]
        self.configure(padx=10, pady=5, bd=1, relief="solid")
        self.theme_manager.register(self, "frame")

        base = tk.Frame(self)
        base.pack(fill="x")
        self.theme_manager.register(base, "frame")

        info = tk.Frame(base)
        info.pack(side="left", fill="y")
        self.theme_manager.register(info, "frame")

        actions = tk.Frame(base)
        actions.pack(side="right", fill="y")
        self.theme_manager.register(actions, "frame")

        title = tk.Label(
            info,
            text=self.ticket_key,
            font=("Segoe UI", 12, "bold"),
            justify="left"
        )
        title.pack(anchor="w")
        self.theme_manager.register(title, "label")

        if len(ticket_data) > 2:
            descript = tk.Label(
                info,
                text=ticket_data["fields"]["description"],
                font=("Segoe UI", 10),
                wraplength=400,
                justify="left"
            )
            descript.pack(anchor="w")
            self.theme_manager.register(descript, "label")

        delete_btn = tk.Button(actions, text="Delete", justify="right", command=lambda: self.delete_from_database(self.delete))
        delete_btn.pack(side="left", padx=10, pady=10)
        self.theme_manager.register(delete_btn, "base_button")

        update_btn = tk.Button(actions, text="Update", justify="right")
        update_btn.pack(side="left", padx=10, pady=10)
        self.theme_manager.register(update_btn, "base_button")

        select_btn = tk.Button(actions, text="Select", justify="right", command=self.select_for_update)
        select_btn.pack(side="right", padx=10, pady=10)
        self.theme_manager.register(select_btn, "flashy_button")
        self.widget_registry["select_btn"] = select_btn

        # Bind click and hover to all non-button children
        # if on_click:
        #     self._bind_all_children(self, lambda event: on_click(self.ticket_key))

    def delete(self, _):
        run_sql_stmt(self.db_path, "DELETE FROM tickets WHERE key = ?", params=(self.ticket_key,), stmt_type="delete")
        if self.card_retainer is not None:
            self.card_retainer[:] = [t for t in self.card_retainer if t.get("key") != self.ticket_key]
        print(f"Deleted ticket {self.ticket_key} from database and card_retainer.")
        self.destroy()  # Remove the widget from the UI

    def _bind_all_children(self, widget, callback):
        # Avoid binding click event to buttons
        if not isinstance(widget, tk.Button):
            widget.bind("<Button-1>", callback)

        # All widgets still get the cursor change for hover
        widget.bind("<Enter>", lambda e: widget.configure(cursor="hand2"))
        widget.bind("<Leave>", lambda e: widget.configure(cursor=""))

        for child in widget.winfo_children():
            self._bind_all_children(child, callback)
    
    def select_for_update(self):
        select = self.widget_registry["select_btn"]
        old_bg = self.theme_manager.theme["background"]

        if select.cget("text") == "Select":
            self.configure(bg=self.theme_manager.theme["pending_color"])
            self.selected_items.append(self.ticket_key)
            print(f"{self.selected_items=}")
            select.config(bg=self.theme_manager.theme["pending_color"])
            self.widget_registry["select_btn"].config(text="Unselect")
        elif select.cget("text") == "Unselect":
            self.configure(bg=old_bg)
            select.config(bg=self.theme_manager.theme["btn_highlight"])
            self.selected_items.remove(self.ticket_key)
            self.widget_registry["select_btn"].config(text="Select")

    def delete_from_database(self, on_delete=None):
        print(self.ticket_key)
        # Prevent multiple popups
        if hasattr(self, '_delete_popup') and self._delete_popup is not None:
            try:
                self._delete_popup.destroy()
            except Exception:
                pass
            self._delete_popup = None
        # Custom popup with no title bar
        root = self.winfo_toplevel()
        popup = tk.Toplevel(root)
        self._delete_popup = popup
        popup.overrideredirect(True)  # Remove title bar
        # popup.configure(bg=self.theme_manager.theme.get("background", "#fff"))
        self.theme_manager.register(popup, "frame")
        # Center the popup relative to the main window and follow it
        def center_popup():
            if not popup.winfo_exists():
                # Popup is destroyed, do nothing
                return
            popup.update_idletasks()
            w, h = 300, 140
            main_x = root.winfo_x()
            main_y = root.winfo_y()
            main_w = root.winfo_width()
            main_h = root.winfo_height()
            x = main_x + (main_w // 2) - (w // 2)
            y = main_y + (main_h // 2) - (h // 2)
            popup.geometry(f"{w}x{h}+{x}+{y}")
            popup.lift()
            try:
                popup.focus_force()
            except Exception:
                pass
        center_popup()
        root.bind('<Configure>', lambda e: center_popup())

        frame = tk.Frame(popup, padx=20, pady=20)
        self.theme_manager.register(frame, "frame")
        frame.pack(fill="both", expand=True)

        label = tk.Label(frame, text=f"Delete ticket {self.ticket_key}?", font=("Trebuchet MS", 14, "bold"))
        self.theme_manager.register(label, "label")
        label.pack(pady=(0, 20))

        btn_frame = tk.Frame(frame)
        self.theme_manager.register(btn_frame, "frame")
        btn_frame.pack()

        def cleanup_popup():
            root.unbind('<Configure>')
            try:
                self._delete_popup = None
            except Exception:
                pass

        def cancel():
            print("Cancelled deletion")
            cleanup_popup()
            popup.destroy()

        def do_delete():
            print(f"Deleting ticket {self.ticket_key}...")
            cleanup_popup()
            popup.destroy()
            if on_delete:
                on_delete(self.ticket_key)

        cancel_btn = tk.Button(btn_frame, text="Cancel", command=cancel, padx=12, pady=4, relief="flat", cursor="hand2")
        self.theme_manager.register(cancel_btn, "base_button")
        cancel_btn.pack(side="left", padx=8)

        delete_btn = tk.Button(btn_frame, text="Delete", command=do_delete, padx=12, pady=4, relief="flat", cursor="hand2")
        self.theme_manager.register(delete_btn, "flashy_button")
        delete_btn.pack(side="left", padx=8)
    
    def set_bg(self, bg):
        self.configure(bg=bg)

# class TicketCard(tk.Frame):
#     def __init__(self, ticket_data, theme_manager, on_click=None, *args, **kwargs):
#         super().__init__(*args, **kwargs)

#         self.ticket_key = ticket_data["key"]
#         self.configure(padx=10, pady=5, bd=1, relief="solid")
#         theme_manager.register(self, "frame")

#         base = tk.Frame(self)
#         base.pack(fill="x")
#         theme_manager.register(base, "frame")

#         info = tk.Frame(base)
#         info.pack(side="left", fill="y")
#         theme_manager.register(info, "frame")

#         actions = tk.Frame(base)
#         actions.pack(side="right", fill="y")
#         theme_manager.register(actions, "frame")

#         title = tk.Label(
#             info,
#             text=self.ticket_key,
#             font=("Segoe UI", 12, "bold"),
#             justify="left"
#         )
#         title.pack(anchor="w")
#         theme_manager.register(title, "label")

#         if len(ticket_data) > 2:
#             descript = tk.Label(
#                 info,
#                 text=ticket_data["fields"]["description"],
#                 font=("Segoe UI", 10),
#                 wraplength=400,
#                 justify="left"
#             )
#             descript.pack(anchor="w")
#             theme_manager.register(descript, "label")

#         update_btn = tk.Button(actions, text="Update", justify="right")
#         update_btn.pack(side="left", padx=10, pady=10)
#         theme_manager.register(update_btn, "base_button")

#         select_btn = tk.Button(actions, text="Select", justify="right")
#         select_btn.pack(side="right", padx=10, pady=10)
#         theme_manager.register(select_btn, "flashy_button")

#         # Bind click event to all children if callback provided
#         if on_click:
#             self._bind_all_children(self, lambda event: on_click(self.ticket_key))

#     def _bind_all_children(self, widget, callback):
#         widget.bind("<Button-1>", callback)
#         for child in widget.winfo_children():
#             self._bind_all_children(child, callback)

