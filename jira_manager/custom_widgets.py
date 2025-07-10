import tkinter as tk

# class EntryWithPlaceholder(tk.Entry):
#     def __init__(self, master=None, placeholder="Enter text...", color='grey',
#                  show=None, initial_text="", *args, **kwargs):
#         self.real_show = show
#         kwargs['show'] = ""  # Start with visible text for placeholder
#         super().__init__(master, *args, **kwargs)

#         self.placeholder = placeholder
#         self.placeholder_color = color
#         self.default_fg_color = self['fg']

#         self.bind("<FocusIn>", self._clear_placeholder)
#         self.bind("<FocusOut>", self._add_placeholder)

#         if initial_text:
#             self.insert(0, initial_text)
#             self.config(show=self.real_show)
#             self['fg'] = self.default_fg_color
#         else:
#             self._add_placeholder()

# class EntryWithPlaceholder(tk.Entry):
#     def __init__(self, master=None, placeholder="Enter text...", color='grey',
#                  show=None, initial_text="", *args, **kwargs):
#         self.real_show = show  # Save the masking character (e.g. "*")
#         kwargs['show'] = ""  # Start with plain text so placeholder is visible if needed
#         super().__init__(master, *args, **kwargs)

#         self.placeholder = placeholder
#         self.placeholder_color = color
#         self.default_fg_color = self['fg']

#         self.bind("<FocusIn>", self._clear_placeholder)
#         self.bind("<FocusOut>", self._add_placeholder)

#         if initial_text:
#             self.insert(0, initial_text)
#             self.config(show=self.real_show)
#             self['fg'] = self.default_fg_color
#         else:
#             self._add_placeholder()

#     def _add_placeholder(self, *args):
#         if not self.get():
#             self.config(show="")  # Show placeholder text normally
#             self.insert(0, self.placeholder)
#             self['fg'] = self.placeholder_color

#     def _clear_placeholder(self, *args):
#         if self['fg'] == self.placeholder_color:
#             self.delete(0, tk.END)
#             self.config(show=self.real_show)
#             self['fg'] = self.default_fg_color

class EntryWithPlaceholder(tk.Entry):
    def __init__(self, master=None, placeholder="Enter text...", color='grey',
                 show=None, initial_text="", *args, **kwargs):
        self.real_show = show
        kwargs['show'] = ""
        super().__init__(master, *args, **kwargs)

        self.placeholder = placeholder
        self.placeholder_color = color
        self.default_fg_color = self['fg']

        self.bind("<FocusIn>", self._clear_placeholder)
        self.bind("<FocusOut>", self._add_placeholder)

        if initial_text:
            self.insert(0, initial_text)
            self.config(show=self.real_show)
            self['fg'] = self.default_fg_color
        else:
            self._add_placeholder()

    def _add_placeholder(self, *args):
        if not self.get():
            self.config(show="")
            self.insert(0, self.placeholder)
            self['fg'] = self.placeholder_color

    def _clear_placeholder(self, *args):
        if self['fg'] == self.placeholder_color:
            self.delete(0, tk.END)
            self.config(show=self.real_show)
            self['fg'] = self.default_fg_color

    def reset_to_placeholder(self):
        self.delete(0, tk.END)
        self._add_placeholder()