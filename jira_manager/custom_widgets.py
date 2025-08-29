import tkinter as tk


class WorkReceiptsPanel(tk.Frame):
    def __init__(
        self,
        master,
        existing_ticket_keys=None,
        added_ticket_keys=None,
        theme_manager=None,
    ):
        super().__init__(master)
        self.theme_manager = theme_manager
        self.theme_manager.register(self, "frame")

        from jira_manager.sql_manager import fetch_all_receipts, insert_receipt
        import os

        db_path = os.path.join(os.path.dirname(__file__), "tickets.db")

        # If new receipt is provided, insert it
        if existing_ticket_keys or added_ticket_keys:
            insert_receipt(db_path, existing_ticket_keys or [], added_ticket_keys or [])

        # Panel dimensions can be set by parent layout
        frame = tk.Frame(self, padx=20, pady=20)
        self.theme_manager.register(frame, "frame")
        frame.pack(fill="both", expand=True)

        # Title
        title_label = tk.Label(
            frame, text="Work Receipts", font=("Trebuchet MS", 15, "bold")
        )
        self.theme_manager.register(title_label, "label")
        title_label.pack(pady=(0, 10))

        # Scrollable receipts list
        receipts_canvas = tk.Canvas(frame, borderwidth=0, height=300)
        self.theme_manager.register(receipts_canvas, "frame")
        receipts_canvas.pack(side="left", fill="both", expand=True)
        receipts_scrollbar = tk.Scrollbar(
            frame, orient="vertical", command=receipts_canvas.yview
        )
        receipts_scrollbar.pack(side="right", fill="y")
        receipts_canvas.configure(yscrollcommand=receipts_scrollbar.set)
        receipts_inner = tk.Frame(receipts_canvas)
        self.theme_manager.register(receipts_inner, "frame")
        receipts_canvas.create_window((0, 0), window=receipts_inner, anchor="nw")

        def on_receipts_configure(event):
            receipts_canvas.configure(scrollregion=receipts_canvas.bbox("all"))

        receipts_inner.bind("<Configure>", on_receipts_configure)

        # Load and display all receipts
        receipts = fetch_all_receipts(db_path)
        for receipt in receipts:
            receipt_frame = tk.Frame(
                receipts_inner, bd=1, relief="groove", padx=8, pady=8
            )
            self.theme_manager.register(receipt_frame, "frame")
            receipt_frame.pack(fill="x", pady=6)
            title = tk.Label(
                receipt_frame,
                text=f"Receipt #{receipt['receipt_id']} - {receipt['created_at'][:19]}",
                font=("Trebuchet MS", 14, "bold"),
            )
            self.theme_manager.register(title, "label")
            title.pack(anchor="w")
            existing = tk.Label(
                receipt_frame,
                text=f"Existing Tickets: {', '.join(receipt['existing_tickets'])}",
                font=("Trebuchet MS", 12),
            )
            self.theme_manager.register(existing, "label")
            existing.pack(anchor="w", pady=(2, 0))
            added = tk.Label(
                receipt_frame,
                text=f"Added Tickets: {', '.join(receipt['added_tickets'])}",
                font=("Trebuchet MS", 12),
            )
            self.theme_manager.register(added, "label")
            added.pack(anchor="w", pady=(2, 0))

        def on_receipts_mousewheel(event):
            if receipts_canvas != receipts_canvas.focus_displayof():
                receipts_canvas.focus_set()
            receipts_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
            return "break"

        receipts_canvas.bind("<MouseWheel>", on_receipts_mousewheel)
        receipts_canvas.bind("<Button-4>", on_receipts_mousewheel)
        receipts_canvas.bind("<Button-5>", on_receipts_mousewheel)


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
        **kwargs,
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
    def __init__(
        self,
        ticket_data,
        theme_manager,
        on_click=None,
        selected_items=None,
        card_retainer=None,
        panel_choice=None,
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)

        self.widget_registry = {}
        self.selected_items = selected_items
        self.theme_manager = theme_manager
        self.card_retainer = card_retainer  # Prevent GC of cards
        self.db_path = "jira_manager/tickets.db"
        self.panel_choice = panel_choice
        # Debug: print panel_choice and check for ticket_panel
        if self.panel_choice is None:
            print(
                f"[DEBUG] TicketCard.__init__: panel_choice is None for ticket {ticket_data.get('key')}"
            )
        elif "ticket_panel" not in self.panel_choice:
            print(
                f"[DEBUG] TicketCard.__init__: panel_choice missing 'ticket_panel' for ticket {ticket_data.get('key')}"
            )
        else:
            print(
                f"[DEBUG] TicketCard.__init__: panel_choice OK for ticket {ticket_data.get('key')}"
            )

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
            info, text=self.ticket_key, font=("Segoe UI", 12, "bold"), justify="left"
        )
        title.pack(anchor="w")
        self.theme_manager.register(title, "label")

        if len(ticket_data) > 2:
            descript = tk.Label(
                info,
                text=ticket_data["fields"]["description"],
                font=("Segoe UI", 10),
                wraplength=400,
                justify="left",
            )
            descript.pack(anchor="w")
            self.theme_manager.register(descript, "label")

        delete_btn = tk.Button(
            actions,
            text="Delete",
            justify="right",
            command=lambda: self.delete_from_database(self.delete),
        )
        delete_btn.pack(side="left", padx=10, pady=10)
        self.theme_manager.register(delete_btn, "base_button")

        update_btn = tk.Button(actions, text="Update", justify="right")
        update_btn.pack(side="left", padx=10, pady=10)
        self.theme_manager.register(update_btn, "base_button")

        select_btn = tk.Button(
            actions, text="Select", justify="right", command=self.select_for_update
        )
        select_btn.pack(side="right", padx=10, pady=10)
        self.theme_manager.register(select_btn, "flashy_button")
        self.widget_registry["select_btn"] = select_btn

    def update_card_retainer(self):
        for saved_card_info in self.card_retainer:
            if saved_card_info["key"] == self.ticket_key:
                if saved_card_info["widget"] is None:
                    saved_card_info["widget"] = self
                break

    def update_panel_choice(self, panel_choice):
        self.panel_choice = panel_choice

    def update_toolbar_buttons(self):
        print(f"{self.theme_manager=}")
        # Setup of dynamic update and delete buttons for selected tickets
        if self.panel_choice is None or "ticket_panel" not in self.panel_choice:
            return
        tool_bar = self.panel_choice["ticket_panel"].widget_registry.get("tool_bar")
        if not tool_bar:
            return
        # Create or get the dynamic button frame
        if (
            not hasattr(tool_bar, "dynamic_btn_frame")
            or not tool_bar.dynamic_btn_frame.winfo_exists()
        ):
            dynamic_btn_frame = tk.Frame(tool_bar)
            self.theme_manager.register(dynamic_btn_frame, "frame")
            tool_bar.dynamic_btn_frame = dynamic_btn_frame
        else:
            dynamic_btn_frame = tool_bar.dynamic_btn_frame

        # Remove any existing buttons in the frame
        for child in dynamic_btn_frame.winfo_children():
            child.destroy()
        print(f"[DEBUG] selected_items before button logic: {self.selected_items}")
        if len(self.selected_items) > 0:
            # Always pack the frame when showing buttons
            dynamic_btn_frame.pack(side="left", padx=40)
            # Update Selected button
            update_button = tk.Button(
                dynamic_btn_frame,
                text="Update Selected",
                command=lambda: print("Update Selected"),
            )
            update_button.pack(side="left", padx=5)  # No space between buttons
            self.theme_manager.register(update_button, "base_button")
            self.widget_registry["update_btn"] = update_button
            # Delete Selected button
            delete_button = tk.Button(
                dynamic_btn_frame,
                text="Delete Selected",
                command=lambda: self.delete_all_selected_tickets(),
            )
            delete_button.pack(side="left", padx=5)  # No space between buttons
            self.theme_manager.register(delete_button, "flashy_button")
            self.widget_registry["delete_btn"] = delete_button
        else:
            # Hide the frame if no buttons
            print(
                f"[DEBUG] Hiding dynamic_btn_frame, selected_items: {self.selected_items}"
            )
            dynamic_btn_frame.pack_forget()

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

        # Update toolbar buttons after selection change
        self.update_toolbar_buttons()

    def delete(self, _):
        run_sql_stmt(
            self.db_path,
            "DELETE FROM tickets WHERE key = ?",
            params=(self.ticket_key,),
            stmt_type="delete",
        )
        # Remove from selected_items if present
        if self.selected_items and self.ticket_key in self.selected_items:
            self.selected_items.remove(self.ticket_key)
            print(f"{self.selected_items=}")
        # Update toolbar buttons after deletion
        self.update_toolbar_buttons()
        if self.card_retainer is not None:
            self.card_retainer[:] = [
                t for t in self.card_retainer if t.get("key") != self.ticket_key
            ]
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

        # Defensive check for panel_choice and ticket_panel
        if self.panel_choice is None:
            print(
                f"[ERROR] select_for_update: self.panel_choice is None for ticket {self.ticket_key}"
            )
            return
        if "ticket_panel" not in self.panel_choice:
            print(
                f"[ERROR] select_for_update: 'ticket_panel' missing in panel_choice for ticket {self.ticket_key}"
            )
            return

        # Setup of dynamic update and delete buttons for selected tickets
        self.update_toolbar_buttons()

    def delete_from_database(self, on_delete=None):
        print(self.ticket_key)
        # Prevent multiple popups
        if hasattr(self, "_delete_popup") and self._delete_popup is not None:
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
        root.bind("<Configure>", lambda e: center_popup())

        frame = tk.Frame(popup, padx=20, pady=20)
        self.theme_manager.register(frame, "frame")
        frame.pack(fill="both", expand=True)

        label = tk.Label(
            frame,
            text=f"Delete ticket {self.ticket_key}?",
            font=("Trebuchet MS", 14, "bold"),
        )
        self.theme_manager.register(label, "label")
        label.pack(pady=(0, 20))

        btn_frame = tk.Frame(frame)
        self.theme_manager.register(btn_frame, "frame")
        btn_frame.pack()

        def cleanup_popup():
            root.unbind("<Configure>")
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

        cancel_btn = tk.Button(
            btn_frame,
            text="Cancel",
            command=cancel,
            padx=12,
            pady=4,
            relief="flat",
            cursor="hand2",
        )
        self.theme_manager.register(cancel_btn, "base_button")
        cancel_btn.pack(side="left", padx=8)

        delete_btn = tk.Button(
            btn_frame,
            text="Delete",
            command=do_delete,
            padx=12,
            pady=4,
            relief="flat",
            cursor="hand2",
        )
        self.theme_manager.register(delete_btn, "flashy_button")
        delete_btn.pack(side="left", padx=8)

    def set_bg(self, bg):
        self.configure(bg=bg)

    def delete_all_selected_tickets(self):
        # Themed, centered confirmation popup before deleting all selected tickets
        root = self.winfo_toplevel()
        popup = tk.Toplevel(root)
        popup.overrideredirect(True)
        popup.transient(root)
        popup.grab_set()
        popup.resizable(False, False)

        # Center popup and follow main window resize
        # def center_popup():
        #     if not popup.winfo_exists():
        #         return
        #     popup.update_idletasks()
        #     w, h = 370, 170
        #     main_x = root.winfo_x()
        #     main_y = root.winfo_y()
        #     main_w = root.winfo_width()
        #     main_h = root.winfo_height()
        #     x = main_x + (main_w // 2) - (w // 2)
        #     y = main_y + (main_h // 2) - (h // 2)
        #     popup.geometry(f"{w}x{h}+{x}+{y}")
        #     popup.lift()
        #     try:
        #         popup.focus_force()
        #     except Exception:
        #         pass
        popup.withdraw()  # Hide initially

        def center_popup():
            if not popup.winfo_exists():
                return
            popup.update_idletasks()
            w, h = 370, 170
            main_x = root.winfo_x()
            main_y = root.winfo_y()
            main_w = root.winfo_width()
            main_h = root.winfo_height()
            x = main_x + (main_w // 2) - (w // 2)
            y = main_y + (main_h // 2) - (h // 2)
            popup.geometry(f"{w}x{h}+{x}+{y}")
            popup.deiconify()  # Show after centering
            popup.lift()
            try:
                popup.focus_force()
            except Exception:
                pass

        popup.after(150, center_popup)
        popup.after(300, center_popup)
        root.bind("<Configure>", lambda e: center_popup())

        # Force center popup
        # popup.after(50, center_popup)
        # popup.after(150, center_popup)
        # popup.after(300, center_popup)

        frame = tk.Frame(popup, padx=20, pady=20)
        self.theme_manager.register(frame, "frame")
        frame.pack(fill="both", expand=True)
        label = tk.Label(
            frame,
            text=f"Are you sure you want to delete {len(self.selected_items)} selected ticket(s)?",
            font=("Trebuchet MS", 13, "bold"),
            wraplength=300,
        )
        self.theme_manager.register(label, "label")
        label.pack(pady=(0, 20))
        btn_frame = tk.Frame(frame)
        self.theme_manager.register(btn_frame, "frame")
        btn_frame.pack()

        def cleanup_popup():
            root.unbind("<Configure>")
            try:
                self._delete_popup = None
            except Exception:
                pass

        def do_delete():
            cleanup_popup()
            popup.destroy()
            for key in list(self.selected_items):
                try:
                    run_sql_stmt(
                        self.db_path,
                        "DELETE FROM tickets WHERE key = ?",
                        params=(key,),
                        stmt_type="delete",
                    )
                except Exception:
                    print(
                        f"Error deleting ticket {key} from delete_all_selected_tickets"
                    )
                self.selected_items.remove(key)
                for card_info in self.card_retainer:
                    if card_info.get("key") == key:
                        print(f"{card_info=} from delete_all_selected_tickets")

                        try:
                            card_info["widget"].destroy()
                        except Exception:
                            print(
                                f"Error destroying widget for {key} from delete_all_selected_tickets"
                            )

                        try:
                            del card_info
                        except Exception:
                            print(
                                f"Error deleting card_info for {key} from delete_all_selected_tickets"
                            )
            self.update_toolbar_buttons()

        def cancel():
            cleanup_popup()
            popup.destroy()

        cancel_btn = tk.Button(
            btn_frame,
            text="Cancel",
            command=cancel,
            padx=12,
            pady=4,
            relief="flat",
            cursor="hand2",
        )
        self.theme_manager.register(cancel_btn, "base_button")
        cancel_btn.pack(side="left", padx=8)
        delete_btn = tk.Button(
            btn_frame,
            text="Delete",
            command=do_delete,
            padx=12,
            pady=4,
            relief="flat",
            cursor="hand2",
        )
        self.theme_manager.register(delete_btn, "flashy_button")
        delete_btn.pack(side="left", padx=8)
