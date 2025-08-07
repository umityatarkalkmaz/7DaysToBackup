import os
import shutil
import zipfile
from datetime import datetime
from tkinter import Tk, Listbox, Button, END, messagebox, Label, filedialog, StringVar, OptionMenu, Frame
from languages import LANGUAGES


class App:
    def __init__(self):
        self.bg_color = '#23272e'
        self.fg_color = '#f5f6fa'
        self.accent1 = '#3a3f4b'
        self.accent2 = '#2d313a'
        self.button_backup = '#388e3c'
        self.button_delete = '#b71c1c'
        self.button_export = '#1565c0'
        self.button_import = '#e65100'
        self.button_fg = '#f5f6fa'
        self.highlight = '#444a56'

        self.LANG = 'tr'
        self.L = LANGUAGES[self.LANG]
        self.appdata_path = os.path.expandvars(r"%appdata%\\7DaysToDie\\Saves")

        self.root = Tk()
        self.root.geometry("540x420")
        self.root.configure(bg=self.bg_color)
        self.root.title(self.L['title'])

        self.main_frame = Frame(self.root, bg=self.bg_color)
        self.main_frame.pack(fill='both', expand=True, padx=10, pady=10)

        self.lang_display = {'tr': 'Türkçe', 'en': 'English'}
        self.lang_var = StringVar(self.root)
        self.lang_var.set(self.lang_display[self.LANG])
        self.lang_menu = OptionMenu(self.root, self.lang_var, *self.lang_display.values(), command=self.lang_callback)
        self.lang_menu.config(bg=self.accent2, fg=self.fg_color, font=('Segoe UI', 9), highlightthickness=0, bd=0,
                              activebackground=self.accent1, activeforeground=self.fg_color)
        self.lang_menu.place(relx=1.0, rely=0.0, anchor='ne', x=-10, y=10, width=90, height=28)

        self.map_label = Label(self.main_frame, text=self.L['map_list'], bg=self.bg_color, fg=self.fg_color,
                               font=('Segoe UI', 11, 'bold'))
        self.map_label.grid(row=0, column=0, sticky='ew', padx=5, pady=5)
        self.map_listbox = Listbox(self.main_frame, height=10, exportselection=0, bg=self.accent1, fg=self.fg_color,
                                   font=('Segoe UI', 10), highlightthickness=1, highlightbackground=self.highlight,
                                   selectbackground=self.accent2, selectforeground=self.fg_color)
        self.map_listbox.grid(row=1, column=0, sticky='nsew', padx=5, pady=5)
        self.map_listbox.bind('<<ListboxSelect>>', self.list_saves)

        self.save_label = Label(self.main_frame, text=self.L['save_list'], bg=self.bg_color, fg=self.fg_color,
                                font=('Segoe UI', 11, 'bold'))
        self.save_label.grid(row=0, column=1, sticky='ew', padx=5, pady=5)
        self.save_listbox = Listbox(self.main_frame, height=10, bg=self.accent1, fg=self.fg_color,
                                    font=('Segoe UI', 10), highlightthickness=1, highlightbackground=self.highlight,
                                    selectbackground=self.accent2, selectforeground=self.fg_color)
        self.save_listbox.grid(row=1, column=1, sticky='nsew', padx=5, pady=5)

        self.backup_button = Button(self.main_frame, text=self.L['backup'],
                                    command=lambda: self.perform_action(self.backup_folder, self.L['backup_success'],
                                                                        self.L['backup_error']), bg=self.button_backup,
                                    fg=self.button_fg, font=('Segoe UI', 10, 'bold'), activebackground='#2e7031',
                                    activeforeground=self.button_fg, bd=0, highlightthickness=0)
        self.delete_button = Button(self.main_frame, text=self.L['delete'],
                                    command=lambda: self.perform_action(self.delete_folder, self.L['delete_success'],
                                                                        self.L['delete_error']), bg=self.button_delete,
                                    fg=self.button_fg, font=('Segoe UI', 10, 'bold'), activebackground='#7f1d1d',
                                    activeforeground=self.button_fg, bd=0, highlightthickness=0)
        self.export_button = Button(self.main_frame, text=self.L['export'], command=self.export_save,
                                    bg=self.button_export, fg=self.button_fg, font=('Segoe UI', 10, 'bold'),
                                    activebackground='#0d47a1', activeforeground=self.button_fg, bd=0,
                                    highlightthickness=0)
        self.import_button = Button(self.main_frame, text=self.L['import'], command=self.import_save,
                                    bg=self.button_import, fg=self.button_fg, font=('Segoe UI', 10, 'bold'),
                                    activebackground='#a04000', activeforeground=self.button_fg, bd=0,
                                    highlightthickness=0)

        self.backup_button.grid(row=2, column=0, sticky='ew', padx=5, pady=10)
        self.delete_button.grid(row=2, column=1, sticky='ew', padx=5, pady=10)
        self.export_button.grid(row=3, column=0, sticky='ew', padx=5, pady=5)
        self.import_button.grid(row=3, column=1, sticky='ew', padx=5, pady=5)

        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_columnconfigure(1, weight=1)
        self.main_frame.grid_rowconfigure(1, weight=1)

        for map_name in os.listdir(self.appdata_path):
            if os.path.isdir(os.path.join(self.appdata_path, map_name)):
                self.map_listbox.insert(END, map_name)

        self.setup_grid_layout()
        self.root.mainloop()

    def lang_callback(self, selected):
        for code, display in self.lang_display.items():
            if display == selected:
                self.change_language(code)
                self.lang_var.set(display)
                break

    def get_selected_paths(self):
        selected_map = self.map_listbox.get(self.map_listbox.curselection())
        selected_save = self.save_listbox.get(self.save_listbox.curselection())
        source_path = os.path.join(self.appdata_path, selected_map, selected_save)
        return selected_map, selected_save, source_path

    def perform_action(self, action, success_message, error_message):
        try:
            action()
            messagebox.showinfo(self.L['title'], success_message)
        except Exception as e:
            messagebox.showerror(self.L['title'], f"{error_message} - {str(e)}")

    def backup_folder(self):
        selected_map, selected_save, source_path = self.get_selected_paths()
        backup_date = datetime.now().strftime("_backup_%Y.%m.%d-%H.%M.%S")
        destination_path = f"{source_path}{backup_date}"
        shutil.copytree(source_path, destination_path)
        self.list_saves()

    def delete_folder(self):
        selected_map, selected_save, source_path = self.get_selected_paths()
        if messagebox.askyesno(self.L['title'], self.L['delete_confirm'].format(selected_save)):
            shutil.rmtree(source_path)
            self.list_saves()

    def list_saves(self, event=None):
        selection = self.map_listbox.curselection()
        self.save_listbox.delete(0, END)
        if not selection:
            return
        selected_map = self.map_listbox.get(selection)
        saves_path = os.path.join(self.appdata_path, selected_map)
        for save in os.listdir(saves_path):
            self.save_listbox.insert(END, save)

    def export_save(self):
        try:
            selected_map, selected_save, source_path = self.get_selected_paths()
            desktop = os.path.join(os.path.expanduser("~"), "Desktop")
            zip_filename = f"{selected_save}.zip"
            zip_path = os.path.join(desktop, zip_filename)
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root_dir, dirs, files in os.walk(source_path):
                    for file in files:
                        abs_path = os.path.join(root_dir, file)
                        rel_path = os.path.relpath(abs_path, os.path.join(source_path, '..'))
                        zipf.write(abs_path, rel_path)
            messagebox.showinfo(self.L['title'], self.L['export_success'].format(zip_path))
        except Exception as e:
            messagebox.showerror(self.L['title'], self.L['export_error'].format(str(e)))

    def import_save(self):
        try:
            selected_map = self.map_listbox.get(self.map_listbox.curselection())
            target_map_path = os.path.join(self.appdata_path, selected_map)
            zip_path = filedialog.askopenfilename(title=self.L['import_select'], filetypes=[("Zip files", "*.zip")])
            if not zip_path:
                return
            with zipfile.ZipFile(zip_path, 'r') as zipf:
                top_level_folder = zipf.namelist()[0].split('/')[0]
                extract_path = os.path.join(target_map_path, top_level_folder)
                if os.path.exists(extract_path):
                    messagebox.showerror(self.L['title'], self.L['import_exists'])
                    return
                zipf.extractall(target_map_path)
            self.list_saves()
            messagebox.showinfo(self.L['title'], self.L['import_success'])
        except Exception as e:
            messagebox.showerror(self.L['title'], self.L['import_error'].format(str(e)))

    def change_language(self, lang_code):
        self.LANG = lang_code
        self.L = LANGUAGES[self.LANG]
        self.root.title(self.L['title'])
        self.backup_button.config(text=self.L['backup'])
        self.delete_button.config(text=self.L['delete'])
        self.export_button.config(text=self.L['export'])
        self.import_button.config(text=self.L['import'])
        self.map_label.config(text=self.L['map_list'])
        self.save_label.config(text=self.L['save_list'])
        self.lang_menu.config(bg=self.accent2, fg=self.fg_color)
        self.list_saves()

    def setup_grid_layout(self):
        self.map_label.grid(row=0, column=0, sticky='ew', padx=10, pady=5)
        self.map_listbox.grid(row=1, column=0, sticky='nsew', padx=10, pady=5)
        self.save_label.grid(row=0, column=1, sticky='ew', padx=10, pady=5)
        self.save_listbox.grid(row=1, column=1, sticky='nsew', padx=10, pady=5)
        self.backup_button.grid(row=2, column=0, columnspan=2, sticky='ew', padx=10, pady=10)
        self.delete_button.grid(row=3, column=0, columnspan=2, sticky='ew', padx=10, pady=10)
        self.export_button.grid(row=4, column=0, sticky='ew', padx=10, pady=10)
        self.import_button.grid(row=4, column=1, sticky='ew', padx=10, pady=10)
        self.main_frame.grid_columnconfigure(0, weight=1, pad=10)
        self.main_frame.grid_columnconfigure(1, weight=1, pad=10)
        self.main_frame.grid_rowconfigure(1, weight=1, pad=10)


if __name__ == "__main__":
    App()
