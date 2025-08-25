import tkinter as tk
class WorkReceiptsPanel(tk.Frame):
    def __init__(self, master, existing_ticket_keys=None, added_ticket_keys=None, theme_manager=None):
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
        title_label = tk.Label(frame, text="Work Receipts", font=("Trebuchet MS", 15, "bold"))
        self.theme_manager.register(title_label, "label")
        title_label.pack(pady=(0, 10))

        # Scrollable receipts list
        receipts_canvas = tk.Canvas(frame, borderwidth=0, height=300)
        self.theme_manager.register(receipts_canvas, "frame")
        receipts_canvas.pack(side="left", fill="both", expand=True)
        receipts_scrollbar = tk.Scrollbar(frame, orient="vertical", command=receipts_canvas.yview)
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
            receipt_frame = tk.Frame(receipts_inner, bd=1, relief="groove", padx=8, pady=8)
            self.theme_manager.register(receipt_frame, "frame")
            receipt_frame.pack(fill="x", pady=6)
            title = tk.Label(receipt_frame, text=f"Receipt #{receipt['receipt_id']} - {receipt['created_at'][:19]}", font=("Trebuchet MS", 14, "bold"))
            self.theme_manager.register(title, "label")
            title.pack(anchor="w")
            existing = tk.Label(receipt_frame, text=f"Existing Tickets: {', '.join(receipt['existing_tickets'])}", font=("Trebuchet MS", 12))
            self.theme_manager.register(existing, "label")
            existing.pack(anchor="w", pady=(2,0))
            added = tk.Label(receipt_frame, text=f"Added Tickets: {', '.join(receipt['added_tickets'])}", font=("Trebuchet MS", 12))
            self.theme_manager.register(added, "label")
            added.pack(anchor="w", pady=(2,0))

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
            print(f"[DEBUG] TicketCard.__init__: panel_choice is None for ticket {ticket_data.get('key')}")
        elif "ticket_panel" not in self.panel_choice:
            print(f"[DEBUG] TicketCard.__init__: panel_choice missing 'ticket_panel' for ticket {ticket_data.get('key')}")
        else:
            print(f"[DEBUG] TicketCard.__init__: panel_choice OK for ticket {ticket_data.get('key')}")

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
        if not hasattr(tool_bar, "dynamic_btn_frame") or not tool_bar.dynamic_btn_frame.winfo_exists():
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
                command=lambda:print("Update Selected")
            )
            update_button.pack(side="left", padx=5)  # No space between buttons
            self.theme_manager.register(update_button, "base_button")
            self.widget_registry["update_btn"] = update_button
            # Delete Selected button
            delete_button = tk.Button(
                dynamic_btn_frame,
                text="Delete Selected",
                command=lambda:print("Delete Selected")
            )
            delete_button.pack(side="left", padx=5)  # No space between buttons
            self.theme_manager.register(delete_button, "flashy_button")
            self.widget_registry["delete_btn"] = delete_button
        else:
            # Hide the frame if no buttons
            print(f"[DEBUG] Hiding dynamic_btn_frame, selected_items: {self.selected_items}")
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
            print(f"[ERROR] select_for_update: self.panel_choice is None for ticket {self.ticket_key}")
            return
        if "ticket_panel" not in self.panel_choice:
            print(f"[ERROR] select_for_update: 'ticket_panel' missing in panel_choice for ticket {self.ticket_key}")
            return
        
        # Setup of dynamic update and delete buttons for selected tickets
        self.update_toolbar_buttons()
        # tool_bar = self.panel_choice["ticket_panel"].widget_registry.get("tool_bar")
        # if len(self.selected_items) > 0:
        #     # Update Selected button
        #     if not hasattr(tool_bar, "update_btn") or not tool_bar.update_btn.winfo_exists():
        #         update_button = tk.Button(
        #             tool_bar,
        #             text="Update Selected",
        #         )
        #         update_button.pack(side="left", padx=40)  # Increased space to 40
        #         self.theme_manager.register(update_button, "base_button")
        #         self.widget_registry["update_btn"] = update_button
        #         tool_bar.update_btn = update_button
        #     # Delete Selected button
        #     if not hasattr(tool_bar, "delete_btn") or not tool_bar.delete_btn.winfo_exists():
        #         delete_button = tk.Button(
        #             tool_bar,
        #             text="Delete Selected",
        #         )
        #         delete_button.pack(side="left", padx=10)
        #         self.theme_manager.register(delete_button, "base_button")
        #         self.widget_registry["delete_btn"] = delete_button
        #         tool_bar.delete_btn = delete_button
        # else:
        #     # Remove the buttons if they exist
        #     if hasattr(tool_bar, "update_btn") and tool_bar.update_btn.winfo_exists():
        #         tool_bar.update_btn.destroy()
        #         del tool_bar.update_btn
        #     if hasattr(tool_bar, "delete_btn") and tool_bar.delete_btn.winfo_exists():
        #         tool_bar.delete_btn.destroy()
        #         del tool_bar.delete_btn

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



# class TicketsExistPopup(tk.Toplevel):
#     def __init__(self, master, existing_ticket_keys, added_ticket_keys, theme_manager):
#         super().__init__(master)
#         self.withdraw()  # Hide initially to prevent flicker
#         self.overrideredirect(True)  # Remove title bar
#         self.resizable(False, False)
#         self.transient(master)
#         self.grab_set()
#         self.theme_manager = theme_manager
#         self.theme_manager.register(self, "frame")

#         # Set geometry before packing widgets
#         w, h = 500, 350
#         main_x = master.winfo_x()
#         main_y = master.winfo_y()
#         main_w = master.winfo_width()
#         main_h = master.winfo_height()
#         x = main_x + (main_w // 2) - (w // 2)
#         y = main_y + (main_h // 2) - (h // 2)
#         self.geometry(f"{w}x{h}+{x}+{y}")

#         frame = tk.Frame(self, padx=20, pady=20)
#         self.theme_manager.register(frame, "frame")
#         frame.pack(fill="both", expand=True)

#         # Split frame for left/right ticket lists
#         split_frame = tk.Frame(frame)
#         self.theme_manager.register(split_frame, "frame")
#         split_frame.pack(fill="both", expand=True)

#         show_left = bool(existing_ticket_keys)
#         show_right = bool(added_ticket_keys)

#     def __init__(self, master, existing_ticket_keys, added_ticket_keys, theme_manager):
#         super().__init__(master)
#         self.withdraw()  # Hide initially to prevent flicker
#         self.overrideredirect(True)  # Remove title bar
#         self.resizable(False, False)
#         self.transient(master)
#         self.grab_set()
#         self.theme_manager = theme_manager
#         self.theme_manager.register(self, "frame")

#         # Set geometry before packing widgets
#         w, h = 500, 350
#         main_x = master.winfo_x()
#         main_y = master.winfo_y()
#         main_w = master.winfo_width()
#         main_h = master.winfo_height()
#         x = main_x + (main_w // 2) - (w // 2)
#         y = main_y + (main_h // 2) - (h // 2)
#         self.geometry(f"{w}x{h}+{x}+{y}")

#         frame = tk.Frame(self, padx=20, pady=20)
#         self.theme_manager.register(frame, "frame")
#         frame.pack(fill="both", expand=True)

#         # Split frame for left/right ticket lists
#         split_frame = tk.Frame(frame)
#         self.theme_manager.register(split_frame, "frame")
#         split_frame.pack(fill="both", expand=True)

#         show_left = bool(existing_ticket_keys)
#         show_right = bool(added_ticket_keys)

#         self.left_canvas = None
#         self.right_canvas = None
#         # Track which canvas is currently focused
#         self._focused_canvas = None

#         # Left side: Existing tickets
#         if show_left:
#             left_frame = tk.Frame(split_frame)
#             self.theme_manager.register(left_frame, "frame")
#             left_frame.pack(side="left", fill="both", expand=True)
#             left_label = tk.Label(left_frame, text="Already Existing Tickets", font=("Trebuchet MS", 13, "bold"))
#             self.theme_manager.register(left_label, "label")
#             left_label.pack(pady=(0, 8))
#             self.left_canvas = tk.Canvas(left_frame, borderwidth=0, width=200, height=200)
#             self.theme_manager.register(self.left_canvas, "frame")
#             self.left_canvas.pack(side="left", fill="both", expand=True)
#             left_scrollbar = tk.Scrollbar(left_frame, orient="vertical", command=self.left_canvas.yview)
#             left_scrollbar.pack(side="right", fill="y")  # Always visible
#             self.left_canvas.configure(yscrollcommand=left_scrollbar.set)
#             left_inner = tk.Frame(self.left_canvas)
#             self.theme_manager.register(left_inner, "frame")
#             self.left_canvas.create_window((0, 0), window=left_inner, anchor="nw")
#             def on_left_configure(event):
#                 self.left_canvas.configure(scrollregion=self.left_canvas.bbox("all"))
#             left_inner.bind("<Configure>", on_left_configure)
#             for key in existing_ticket_keys:
#                 ticket_label = tk.Label(left_inner, text=key, anchor="w", font=("Segoe UI", 11))
#                 ticket_label.pack(fill="x", padx=5, pady=2)
#                 self.theme_manager.register(ticket_label, "label")
#             # Simple, direct mouse wheel binding
#             def on_left_mousewheel(event):
#                 print(f"[DEBUG] on_left_mousewheel: left_canvas={self.left_canvas}, has focus={self.left_canvas == self.left_canvas.focus_displayof()}")
#                 if self.left_canvas != self.left_canvas.focus_displayof():
#                     self.left_canvas.focus_set()
#                     print(f"[DEBUG] Focus set to left_canvas: {self.left_canvas}")
#                 if event.num == 4 or event.delta > 0:
#                     self.left_canvas.yview_scroll(-1, "units")
#                 elif event.num == 5 or event.delta < 0:
#                     self.left_canvas.yview_scroll(1, "units")
#                 return "break"
#             self.left_canvas.bind("<MouseWheel>", on_left_mousewheel)
#             self.left_canvas.bind("<Button-4>", on_left_mousewheel)
#             self.left_canvas.bind("<Button-5>", on_left_mousewheel)

#         # Vertical separator if both sides are shown
#         if show_left and show_right:
#             sep = tk.Frame(split_frame, width=2, bg="#888")
#             sep.pack(side="left", fill="y", padx=8, pady=8)

#         # Right side: Added tickets
#         if show_right:
#             right_frame = tk.Frame(split_frame)
#             self.theme_manager.register(right_frame, "frame")
#             right_frame.pack(side="left", fill="both", expand=True)
#             right_label = tk.Label(right_frame, text="Newly Added Tickets", font=("Trebuchet MS", 13, "bold"))
#             self.theme_manager.register(right_label, "label")
#             right_label.pack(pady=(0, 8))
#             self.right_canvas = tk.Canvas(right_frame, borderwidth=0, width=200, height=200)
#             self.theme_manager.register(self.right_canvas, "frame")
#             self.right_canvas.pack(side="left", fill="both", expand=True)
#             right_scrollbar = tk.Scrollbar(right_frame, orient="vertical", command=self.right_canvas.yview)
#             right_scrollbar.pack(side="right", fill="y")  # Always visible
#             self.right_canvas.configure(yscrollcommand=right_scrollbar.set)
#             right_inner = tk.Frame(self.right_canvas)
#             self.theme_manager.register(right_inner, "frame")
#             self.right_canvas.create_window((0, 0), window=right_inner, anchor="nw")
#             def on_right_configure(event):
#                 self.right_canvas.configure(scrollregion=self.right_canvas.bbox("all"))
#             right_inner.bind("<Configure>", on_right_configure)
#             for key in added_ticket_keys:
#                 ticket_label = tk.Label(right_inner, text=key, anchor="w", font=("Segoe UI", 11))
#                 ticket_label.pack(fill="x", padx=5, pady=2)
#                 self.theme_manager.register(ticket_label, "label")
#             # Simple, direct mouse wheel binding
#             def on_right_mousewheel(event):
#                 print(f"[DEBUG] on_right_mousewheel: right_canvas={self.right_canvas}, has focus={self.right_canvas == self.right_canvas.focus_displayof()}")
#                 if self.right_canvas != self.right_canvas.focus_displayof():
#                     self.right_canvas.focus_set()
#                     print(f"[DEBUG] Focus set to right_canvas: {self.right_canvas}")
#                 if event.num == 4 or event.delta > 0:
#                     self.right_canvas.yview_scroll(-1, "units")
#                 elif event.num == 5 or event.delta < 0:
#                     self.right_canvas.yview_scroll(1, "units")
#                 return "break"
#             self.right_canvas.bind("<MouseWheel>", on_right_mousewheel)
#             self.right_canvas.bind("<Button-4>", on_right_mousewheel)
#             self.right_canvas.bind("<Button-5>", on_right_mousewheel)

#         # On popup open, set focus to first visible canvas for instant mouse wheel scrolling
#         if show_left and self.left_canvas:
#             self.left_canvas.focus_set()
#             print(f"[DEBUG] Popup focused left_canvas: {self.left_canvas}, has focus: {self.left_canvas == self.left_canvas.focus_displayof()}")
#         elif show_right and self.right_canvas:
#             self.right_canvas.focus_set()
#             print(f"[DEBUG] Popup focused right_canvas: {self.right_canvas}, has focus: {self.right_canvas == self.right_canvas.focus_displayof()}")

#         btn_frame = tk.Frame(frame)
#         self.theme_manager.register(btn_frame, "frame")
#         btn_frame.pack(pady=10)

#         def cleanup_popup():
#             master.unbind("<Configure>")
#             # Unbind mouse wheel events from canvases if present
#             if show_left and self.left_canvas:
#                 try:
#                     unbind_left_mousewheel()
#                 except Exception:
#                     pass
#             if show_right and self.right_canvas:
#                 try:
#                     unbind_right_mousewheel()
#                 except Exception:
#                     pass
#             # Restore ticket panel canvas focus for instant mouse wheel scrolling
#             try:
#                 root = master.winfo_toplevel()
#                 ticket_panel = None
#                 if hasattr(root, 'panel_choice'):
#                     ticket_panel = root.panel_choice.get('ticket_panel')
#                 if not ticket_panel and hasattr(master, 'panel_choice'):
#                     ticket_panel = master.panel_choice.get('ticket_panel')
#                 if ticket_panel:
#                     canvas = ticket_panel.widget_registry.get('canvas')
#                     if canvas:
#                         canvas.focus_set()
#                         print(f"[DEBUG] Restored focus to ticket_panel canvas: {canvas}, has focus: {canvas == canvas.focus_displayof()}")
#                     else:
#                         print("[DEBUG] No canvas found in ticket_panel.widget_registry")
#                 else:
#                     print("[DEBUG] No ticket_panel found in root or master.panel_choice")
#             except Exception as e:
#                 print(f"[DEBUG] Error restoring focus to ticket_panel canvas: {e}")

#         ok_btn = tk.Button(
#             btn_frame,
#             text="OK",
#             command=lambda: (cleanup_popup(), self.destroy()),
#             padx=12,
#             pady=4,
#             relief="flat",
#             cursor="hand2",
#             font=("Segoe UI", 12, "bold"),
#         )
#         self.theme_manager.register(ok_btn, "base_button")
#         ok_btn.pack()

#         self.update_idletasks()
#         self.deiconify()  # Show after geometry and widgets are set
#         self.lift()
#         try:
#             self.focus_force()
#             self.focus_set()
#         except Exception:
#             pass
#         master.bind("<Configure>", lambda e: self._center_on_configure(w, h, master))

#         # Left side: Existing tickets
#         if show_left:
#             left_frame = tk.Frame(split_frame)
#             self.theme_manager.register(left_frame, "frame")
#             left_frame.pack(side="left", fill="both", expand=True)
#             left_label = tk.Label(left_frame, text="Already Existing Tickets", font=("Trebuchet MS", 13, "bold"))
#             self.theme_manager.register(left_label, "label")
#             left_label.pack(pady=(0, 8))
#             left_canvas = tk.Canvas(left_frame, borderwidth=0, width=200, height=200)
#             self.theme_manager.register(left_canvas, "frame")
#             left_canvas.pack(side="left", fill="both", expand=True)
#             left_scrollbar = tk.Scrollbar(left_frame, orient="vertical", command=left_canvas.yview)
#             left_scrollbar.pack(side="right", fill="y")
#             left_canvas.configure(yscrollcommand=left_scrollbar.set)
#             left_inner = tk.Frame(left_canvas)
#             self.theme_manager.register(left_inner, "frame")
#             left_canvas.create_window((0, 0), window=left_inner, anchor="nw")
#             def on_left_configure(event):
#                 left_canvas.configure(scrollregion=left_canvas.bbox("all"))
#             left_inner.bind("<Configure>", on_left_configure)
#             for key in existing_ticket_keys:
#                 ticket_label = tk.Label(left_inner, text=key, anchor="w", font=("Segoe UI", 11))
#                 ticket_label.pack(fill="x", padx=5, pady=2)
#                 self.theme_manager.register(ticket_label, "label")
#             # Mouse wheel scrolling for left_canvas (cross-platform)
#             def on_left_mousewheel(event):
#                 if event.num == 4 or event.delta > 0:
#                     left_canvas.yview_scroll(-1, "units")
#                 elif event.num == 5 or event.delta < 0:
#                     left_canvas.yview_scroll(1, "units")
#                 return "break"
#             def bind_left_mousewheel():
#                 left_canvas.bind("<MouseWheel>", on_left_mousewheel)
#                 left_canvas.bind("<Button-4>", on_left_mousewheel)
#                 left_canvas.bind("<Button-5>", on_left_mousewheel)
#                 left_inner.bind("<MouseWheel>", on_left_mousewheel)
#                 left_inner.bind("<Button-4>", on_left_mousewheel)
#                 left_inner.bind("<Button-5>", on_left_mousewheel)
#             def unbind_left_mousewheel():
#                 left_canvas.unbind("<MouseWheel>")
#                 left_canvas.unbind("<Button-4>")
#                 left_canvas.unbind("<Button-5>")
#                 left_inner.unbind("<MouseWheel>")
#                 left_inner.unbind("<Button-4>")
#                 left_inner.unbind("<Button-5>")
#             def focus_left_canvas(event=None):
#                 left_canvas.focus_set()
#                 bind_left_mousewheel()
#                 self._focused_canvas = left_canvas
#             left_canvas.bind("<Enter>", focus_left_canvas)
#             left_canvas.bind("<Leave>", lambda e: unbind_left_mousewheel())
#             left_inner.bind("<Enter>", focus_left_canvas)
#             left_inner.bind("<Leave>", lambda e: unbind_left_mousewheel())

#         # Vertical separator if both sides are shown
#         if show_left and show_right:
#             sep = tk.Frame(split_frame, width=2, bg="#888")
#             sep.pack(side="left", fill="y", padx=8, pady=8)

#         # Right side: Added tickets
#         if show_right:
#             right_frame = tk.Frame(split_frame)
#             self.theme_manager.register(right_frame, "frame")
#             right_frame.pack(side="left", fill="both", expand=True)
#             right_label = tk.Label(right_frame, text="Newly Added Tickets", font=("Trebuchet MS", 13, "bold"))
#             self.theme_manager.register(right_label, "label")
#             right_label.pack(pady=(0, 8))
#             right_canvas = tk.Canvas(right_frame, borderwidth=0, width=200, height=200)
#             self.theme_manager.register(right_canvas, "frame")
#             right_canvas.pack(side="left", fill="both", expand=True)
#             right_scrollbar = tk.Scrollbar(right_frame, orient="vertical", command=self.right_canvas.yview)
#             right_scrollbar.pack(side="right", fill="y")
#             right_canvas.configure(yscrollcommand=right_scrollbar.set)
#             right_inner = tk.Frame(self.right_canvas)
#             self.theme_manager.register(right_inner, "frame")
#             right_canvas.create_window((0, 0), window=right_inner, anchor="nw")
#             def on_right_configure(event):
#                 self.right_canvas.configure(scrollregion=self.right_canvas.bbox("all"))
#             right_inner.bind("<Configure>", on_right_configure)
#             for key in added_ticket_keys:
#                 ticket_label = tk.Label(right_inner, text=key, anchor="w", font=("Segoe UI", 11))
#                 ticket_label.pack(fill="x", padx=5, pady=2)
#                 self.theme_manager.register(ticket_label, "label")
#             # Mouse wheel scrolling for right_canvas (cross-platform)
#             def on_right_mousewheel(event):
#                 if event.num == 4 or event.delta > 0:
#                     right_canvas.yview_scroll(-1, "units")
#                 elif event.num == 5 or event.delta < 0:
#                     right_canvas.yview_scroll(1, "units")
#                 return "break"
#             def bind_right_mousewheel():
#                 right_canvas.bind("<MouseWheel>", on_right_mousewheel)
#                 right_canvas.bind("<Button-4>", on_right_mousewheel)
#                 right_canvas.bind("<Button-5>", on_right_mousewheel)
#                 right_inner.bind("<MouseWheel>", on_right_mousewheel)
#                 right_inner.bind("<Button-4>", on_right_mousewheel)
#                 right_inner.bind("<Button-5>", on_right_mousewheel)
#             def unbind_right_mousewheel():
#                 right_canvas.unbind("<MouseWheel>")
#                 right_canvas.unbind("<Button-4>")
#                 right_canvas.unbind("<Button-5>")
#                 right_inner.unbind("<MouseWheel>")
#                 right_inner.unbind("<Button-4>")
#                 right_inner.unbind("<Button-5>")
#             def focus_right_canvas(event=None):
#                 right_canvas.focus_set()
#                 bind_right_mousewheel()
#                 self._focused_canvas = right_canvas
#             right_canvas.bind("<Enter>", focus_right_canvas)
#             right_canvas.bind("<Leave>", lambda e: unbind_right_mousewheel())
#             right_inner.bind("<Enter>", focus_right_canvas)
#             right_inner.bind("<Leave>", lambda e: unbind_right_mousewheel())

#         # On popup open, set focus to first visible canvas and bind mouse wheel
#         if show_left and left_canvas:
#             left_canvas.focus_set()
#             bind_left_mousewheel()
#             self._focused_canvas = left_canvas
#         elif show_right and right_canvas:
#             right_canvas.focus_set()
#             bind_right_mousewheel()
#             self._focused_canvas = right_canvas

#         btn_frame = tk.Frame(frame)
#         self.theme_manager.register(btn_frame, "frame")
#         btn_frame.pack(pady=10)

#         def cleanup_popup():
#             master.unbind("<Configure>")
#             # Unbind mouse wheel events from canvases if present
#             if show_left and left_canvas:
#                 try:
#                     unbind_left_mousewheel()
#                 except Exception:
#                     pass
#             if show_right and right_canvas:
#                 try:
#                     unbind_right_mousewheel()
#                 except Exception:
#                     pass
#             # Restore ticket panel canvas focus and mouse wheel binding
#             try:
#                 root = master.winfo_toplevel()
#                 ticket_panel = None
#                 if hasattr(root, 'panel_choice'):
#                     ticket_panel = root.panel_choice.get('ticket_panel')
#                 if not ticket_panel and hasattr(master, 'panel_choice'):
#                     ticket_panel = master.panel_choice.get('ticket_panel')
#                 if ticket_panel:
#                     canvas = ticket_panel.widget_registry.get('canvas')
#                     if canvas:
#                         canvas.focus_set()
#                         # Rebind mouse wheel events for ticket panel canvas
#                         def _on_mousewheel(event):
#                             if event.num == 4 or event.delta > 0:
#                                 canvas.yview_scroll(-1, "units")
#                             elif event.num == 5 or event.delta < 0:
#                                 canvas.yview_scroll(1, "units")
#                         canvas.bind("<MouseWheel>", _on_mousewheel)
#                         canvas.bind("<Button-4>", _on_mousewheel)
#                         canvas.bind("<Button-5>", _on_mousewheel)
#             except Exception:
#                 pass

#         ok_btn = tk.Button(
#             btn_frame,
#             text="OK",
#             command=lambda: (cleanup_popup(), self.destroy()),
#             padx=12,
#             pady=4,
#             relief="flat",
#             cursor="hand2",
#             font=("Segoe UI", 12, "bold"),
#         )
#         self.theme_manager.register(ok_btn, "base_button")
#         ok_btn.pack()

#         self.update_idletasks()
#         self.deiconify()  # Show after geometry and widgets are set
#         self.lift()
#         try:
#             self.focus_force()
#             self.focus_set()
#         except Exception:
#             pass
#         master.bind("<Configure>", lambda e: self._center_on_configure(w, h, master))

#         # Temporarily unbind mouse wheel events from root while popup is visible
#         root = master.winfo_toplevel()
#         root_mousewheel_binding = root.bind_class("Toplevel", "<MouseWheel>")
#         root.unbind_all("<MouseWheel>")

#         # Ensure canvases get focus when mouse enters, so mouse wheel events are handled only by popup
#         if show_left:
#             left_canvas.bind("<Enter>", lambda e: (left_canvas.focus_set(), print(f"[DEBUG] <Enter> left_canvas: {left_canvas}, has focus: {left_canvas == left_canvas.focus_displayof()}")))
#         if show_right:
#             right_canvas.bind("<Enter>", lambda e: (right_canvas.focus_set(), print(f"[DEBUG] <Enter> right_canvas: {right_canvas}, has focus: {right_canvas == right_canvas.focus_displayof()}")))

#         # Restore mouse wheel events and focus on root when popup is closed
#         def restore_root_mousewheel():
#             # Unbind the popup's global mouse wheel handler
#             self.unbind_all("<MouseWheel>")
#             # Restore root focus
#             try:
#                 root.focus_force()
#             except Exception:
#                 pass
#             # Restore mouse wheel for ticket panel canvas if present
#             try:
#                 ticket_panel = None
#                 if hasattr(root, 'panel_choice'):
#                     ticket_panel = root.panel_choice.get('ticket_panel')
#                 if not ticket_panel and hasattr(master, 'panel_choice'):
#                     ticket_panel = master.panel_choice.get('ticket_panel')
#                 if ticket_panel:
#                     canvas = ticket_panel.widget_registry.get('canvas')
#                     if canvas:
#                         def ticket_panel_mousewheel(event):
#                             canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
#                             return "break"
#                         canvas.bind("<MouseWheel>", ticket_panel_mousewheel)
#                         canvas.bind("<Button-4>", ticket_panel_mousewheel)
#                         canvas.bind("<Button-5>", ticket_panel_mousewheel)
#             except Exception:
#                 pass

#         def cleanup_popup():
#             master.unbind("<Configure>")
#             restore_root_mousewheel()

#     def _center_on_configure(self, w, h, master):
#         if not self.winfo_exists():
#             return
#         main_x = master.winfo_x()
#         main_y = master.winfo_y()
#         main_w = master.winfo_width()
#         main_h = master.winfo_height()
#         x = main_x + (main_w // 2) - (w // 2)
#         y = main_y + (main_h // 2) - (h // 2)
#         self.geometry(f"{w}x{h}+{x}+{y}")
#         self.lift()


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
