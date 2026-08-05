import sys
from tkinter import *
import tkinter as tk
from tkinter import ttk, scrolledtext, colorchooser, filedialog
import random
import time
import keyboard
import subprocess
import threading
import os
import json

main_window = None
executor_window = None
close_window_ref = None
settings_window = None
find_window = None

settings = {
    'bg_color': '#060708',
    'text_color': '#d4d4d4',
    'editor_bg': '#1e1e1e',
    'output_bg': '#1e1e1e',
    'button_bg': '#242424',
    'button_fg': 'white',
    'font_family': 'Courier',
    'font_size': 10,
    'title_bg': '#0a0a0a',
    'autosave': True
}

SETTINGS_FILE = 'settings.json'
current_file = None


def load_settings():
    global settings
    try:
        with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
            loaded = json.load(f)
            settings.update(loaded)
    except:
        save_settings()


def save_settings():
    try:
        with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
            json.dump(settings, f, indent=4)
    except:
        pass


def create_custom_titlebar(window, title_text, bg_color=None, window_ref=None, is_main=False):
    if bg_color is None:
        bg_color = settings.get('title_bg', '#0a0a0a')

    window.overrideredirect(True)

    title_frame = tk.Frame(window, bg=bg_color, height=35)
    title_frame.pack(fill="x", side="top")
    title_frame.pack_propagate(False)

    title_label = tk.Label(title_frame, text=title_text,
                           bg=bg_color, fg="white",
                           font=("Segoe UI", 10))
    title_label.pack(side="left", padx=10, pady=5)

    def close_window():
        window.destroy()
        if window_ref:
            window_ref[0] = None
        if is_main:
            sys.exit()

    close_btn = tk.Button(title_frame, text="✕",
                          command=close_window,
                          bg=bg_color, fg="white",
                          relief="flat", padx=8, pady=0,
                          font=("Arial", 12))
    close_btn.pack(side="right", padx=2)

    def on_enter_btn(btn, color="#c0392b"):
        btn.config(bg=color)

    def on_leave_btn(btn, color=bg_color):
        btn.config(bg=color)

    close_btn.bind("<Enter>", lambda e: on_enter_btn(close_btn, "#c0392b"))
    close_btn.bind("<Leave>", lambda e: on_leave_btn(close_btn, bg_color))

    def start_move(event):
        window.x = event.x
        window.y = event.y

    def do_move(event):
        x = window.winfo_x() + (event.x - window.x)
        y = window.winfo_y() + (event.y - window.y)
        window.geometry(f"+{x}+{y}")

    title_frame.bind("<Button-1>", start_move)
    title_frame.bind("<B1-Motion>", do_move)
    title_label.bind("<Button-1>", start_move)
    title_label.bind("<B1-Motion>", do_move)

    def on_map(event):
        window.overrideredirect(True)

    window.bind("<Map>", on_map)

    return title_frame


def highlight_syntax(text_widget, start="1.0", end="end"):
    for tag in text_widget.tag_names():
        text_widget.tag_delete(tag)

    text_widget.tag_config("keyword", foreground="#569CD6")
    text_widget.tag_config("string", foreground="#CE9178")
    text_widget.tag_config("comment", foreground="#6A9955")
    text_widget.tag_config("function", foreground="#DCDCAA")
    text_widget.tag_config("number", foreground="#B5CEA8")
    text_widget.tag_config("builtin", foreground="#4EC9B0")
    text_widget.tag_config("decorator", foreground="#C586C0")
    text_widget.tag_config("class", foreground="#4EC9B0")

    keywords = [
        'and', 'as', 'assert', 'break', 'class', 'continue', 'def', 'del',
        'elif', 'else', 'except', 'finally', 'for', 'from', 'global', 'if',
        'import', 'in', 'is', 'lambda', 'nonlocal', 'not', 'or', 'pass',
        'raise', 'return', 'try', 'while', 'with', 'yield'
    ]

    for kw in keywords:
        text_widget.tag_remove("keyword", "1.0", "end")
        start_idx = "1.0"
        while True:
            pos = text_widget.search(rf'\y{kw}\y', start_idx, "end", regexp=True)
            if not pos:
                break
            end_idx = f"{pos}+{len(kw)}c"
            text_widget.tag_add("keyword", pos, end_idx)
            start_idx = end_idx

    start_idx = "1.0"
    while True:
        pos = text_widget.search(r'\y\w+\s*\(', start_idx, "end", regexp=True)
        if not pos:
            break
        end_idx = text_widget.search(r'\s*\(', pos, "end", regexp=True)
        if not end_idx:
            break
        text_widget.tag_add("function", pos, end_idx)
        start_idx = f"{pos}+1c"

    for quote in ['"', "'"]:
        start_idx = "1.0"
        while True:
            pos = text_widget.search(f'{quote}', start_idx, "end", regexp=False)
            if not pos:
                break
            end_pos = text_widget.search(f'{quote}', f"{pos}+1c", "end", regexp=False)
            if not end_pos:
                break
            text_widget.tag_add("string", pos, f"{end_pos}+1c")
            start_idx = f"{end_pos}+1c"

    start_idx = "1.0"
    while True:
        pos = text_widget.search(r'#.*$', start_idx, "end", regexp=True)
        if not pos:
            break
        end_idx = text_widget.index(f"{pos} lineend")
        text_widget.tag_add("comment", pos, end_idx)
        start_idx = end_idx

    start_idx = "1.0"
    while True:
        pos = text_widget.search(r'\b\d+\b', start_idx, "end", regexp=True)
        if not pos:
            break
        end_idx = f"{pos}+{len(text_widget.get(pos, f'{pos} lineend').split()[0])}c"
        text_widget.tag_add("number", pos, end_idx)
        start_idx = end_idx


def show_autocomplete(text_widget, event=None):
    word = text_widget.get("insert-1c", "insert")
    if not word or not word.isalpha():
        return

    suggestions = [
        'print', 'len', 'range', 'str', 'int', 'float', 'list', 'dict',
        'set', 'tuple', 'open', 'input', 'type', 'isinstance', 'sum', 'max',
        'min', 'sorted', 'reversed', 'enumerate', 'zip', 'map', 'filter',
        'any', 'all', 'def', 'class', 'import', 'from', 'return', 'if',
        'else', 'elif', 'for', 'while', 'break', 'continue', 'try', 'except',
        'finally', 'with', 'as', 'lambda', 'True', 'False', 'None'
    ]

    matches = [s for s in suggestions if s.startswith(word)]
    if not matches:
        return

    menu = Menu(text_widget, tearoff=0, bg='#2c3136', fg='white')
    for match in matches[:10]:
        menu.add_command(label=match, command=lambda m=match: insert_autocomplete(text_widget, word, m))
    menu.post(text_widget.winfo_pointerx(), text_widget.winfo_pointery())


def insert_autocomplete(text_widget, old_word, new_word):
    text_widget.delete("insert-{}c".format(len(old_word)), "insert")
    text_widget.insert("insert", new_word)


def find_text(editor_widget):
    global find_window
    if find_window:
        try:
            find_window.lift()
            return
        except:
            find_window = None

    find_window = Toplevel()
    find_window.title("Search and Replace")
    find_window.geometry("400x180")
    find_window.configure(bg=settings['bg_color'])
    find_window.overrideredirect(True)

    def close_find():
        global find_window
        find_window.destroy()
        find_window = None

    title_frame = tk.Frame(find_window, bg=settings['title_bg'], height=30)
    title_frame.pack(fill="x", side="top")
    title_frame.pack_propagate(False)

    title_label = tk.Label(title_frame, text="Search and Replace", bg=settings['title_bg'], fg="white",
                           font=("Segoe UI", 10))
    title_label.pack(side="left", padx=10, pady=3)

    close_btn = tk.Button(title_frame, text="✕", command=close_find,
                          bg=settings['title_bg'], fg="white",
                          relief="flat", padx=8, pady=0)
    close_btn.pack(side="right", padx=2)

    def start_move(event):
        find_window.x = event.x
        find_window.y = event.y

    def do_move(event):
        x = find_window.winfo_x() + (event.x - find_window.x)
        y = find_window.winfo_y() + (event.y - find_window.y)
        find_window.geometry(f"+{x}+{y}")

    title_frame.bind("<Button-1>", start_move)
    title_frame.bind("<B1-Motion>", do_move)
    title_label.bind("<Button-1>", start_move)
    title_label.bind("<B1-Motion>", do_move)

    main_frame = tk.Frame(find_window, bg=settings['bg_color'])
    main_frame.pack(fill="both", expand=True, padx=15, pady=15)

    tk.Label(main_frame, text="Find:", bg=settings['bg_color'], fg=settings['text_color'], font=("Segoe UI", 10)).grid(
        row=0, column=0, sticky="w", pady=3)
    find_entry = tk.Entry(main_frame, width=30, bg="#2c3136", fg="white", insertbackground='white',
                          font=("Segoe UI", 10))
    find_entry.grid(row=0, column=1, pady=3, padx=5)
    find_entry.focus()

    tk.Label(main_frame, text="Replace:", bg=settings['bg_color'], fg=settings['text_color'],
             font=("Segoe UI", 10)).grid(row=1, column=0, sticky="w", pady=3)
    replace_entry = tk.Entry(main_frame, width=30, bg="#2c3136", fg="white", insertbackground='white',
                             font=("Segoe UI", 10))
    replace_entry.grid(row=1, column=1, pady=3, padx=5)

    def find_next():
        search_text = find_entry.get()
        if not search_text:
            return

        editor_widget.tag_remove("search", "1.0", "end")

        start_pos = editor_widget.index("insert")
        pos = editor_widget.search(search_text, start_pos, "end")
        if pos:
            end_pos = f"{pos}+{len(search_text)}c"
            editor_widget.tag_config("search", background="#264f78", foreground="white")
            editor_widget.tag_add("search", pos, end_pos)
            editor_widget.mark_set("insert", end_pos)
            editor_widget.see(pos)
        else:
            pos = editor_widget.search(search_text, "1.0", "end")
            if pos:
                end_pos = f"{pos}+{len(search_text)}c"
                editor_widget.tag_config("search", background="#264f78", foreground="white")
                editor_widget.tag_add("search", pos, end_pos)
                editor_widget.mark_set("insert", end_pos)
                editor_widget.see(pos)

    def replace_one():
        search_text = find_entry.get()
        replace_text = replace_entry.get()
        if not search_text:
            return

        start_pos = editor_widget.index("insert")
        pos = editor_widget.search(search_text, start_pos, "end")
        if pos:
            end_pos = f"{pos}+{len(search_text)}c"
            editor_widget.delete(pos, end_pos)
            editor_widget.insert(pos, replace_text)
            editor_widget.tag_remove("search", "1.0", "end")

    def replace_all():
        search_text = find_entry.get()
        replace_text = replace_entry.get()
        if not search_text:
            return
        content = editor_widget.get("1.0", "end")
        new_content = content.replace(search_text, replace_text)
        editor_widget.delete("1.0", "end")
        editor_widget.insert("1.0", new_content)
        editor_widget.tag_remove("search", "1.0", "end")

    button_frame = tk.Frame(main_frame, bg=settings['bg_color'])
    button_frame.grid(row=2, column=0, columnspan=2, pady=10)

    tk.Button(button_frame, text="Find", command=find_next,
              bg=settings['button_bg'], fg=settings['button_fg'],
              font=("Segoe UI", 10), padx=15).pack(side="left", padx=3)
    tk.Button(button_frame, text="Replace", command=replace_one,
              bg=settings['button_bg'], fg=settings['button_fg'],
              font=("Segoe UI", 10), padx=15).pack(side="left", padx=3)
    tk.Button(button_frame, text="Replace All", command=replace_all,
              bg=settings['button_bg'], fg=settings['button_fg'],
              font=("Segoe UI", 10), padx=15).pack(side="left", padx=3)

    find_entry.bind("<Return>", lambda e: find_next())

    find_window.protocol("WM_DELETE_WINDOW", close_find)
    find_window.mainloop()


def start():
    global main_window, executor_window, close_window_ref, settings_window, current_file

    load_settings()

    def close():
        global close_window_ref

        def ye():
            sys.exit()

        def no():
            global close_window_ref
            if close_window_ref:
                close_window_ref.destroy()
                close_window_ref = None

        close_window = Tk()
        close_window.geometry("200x150")
        close_window.configure(bg="#2c3e50")
        close_window_ref = close_window

        create_custom_titlebar(close_window, "Confirm", "#1a1a1a")

        content_frame = tk.Frame(close_window, bg="#2c3e50")
        content_frame.pack(fill="both", expand=True)

        lb = tk.Label(content_frame, text="You sure?",
                      font=("Segoe UI", 11), fg="White", bg="#2c3e50")
        lb.pack(pady=15)

        btn_frame = tk.Frame(content_frame, bg="#2c3e50")
        btn_frame.pack(pady=5)

        btn1 = tk.Button(btn_frame, text="Yes", command=ye,
                         bg="#242424", fg="white",
                         font=("Segoe UI", 10, "bold"),
                         padx=25, pady=5)
        btn1.pack(side="left", padx=10)

        btn2 = tk.Button(btn_frame, text="No", command=no,
                         bg="#242424", fg="white",
                         font=("Segoe UI", 10, "bold"),
                         padx=25, pady=5)
        btn2.pack(side="left", padx=10)

        close_window.update_idletasks()
        width = close_window.winfo_width()
        height = close_window.winfo_height()
        x = (close_window.winfo_screenwidth() // 2) - (width // 2)
        y = (close_window.winfo_screenheight() // 2) - (height // 2)
        close_window.geometry(f"{width}x{height}+{x}+{y}")

        close_window.mainloop()

    def open_settings():
        global settings_window

        if settings_window:
            try:
                settings_window.lift()
                return
            except:
                settings_window = None

        settings_window = Tk()
        settings_window.geometry("500x600")
        settings_window.configure(bg=settings['bg_color'])

        create_custom_titlebar(settings_window, "Settings", settings['title_bg'])

        main_frame = tk.Frame(settings_window, bg=settings['bg_color'])
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        title = tk.Label(main_frame, text="Settings",
                         font=("Segoe UI", 16, "bold"),
                         bg=settings['bg_color'], fg=settings['text_color'])
        title.pack(pady=(0, 20))

        def change_bg():
            color = colorchooser.askcolor(title="Select background color")[1]
            if color:
                settings['bg_color'] = color
                settings_window.configure(bg=color)
                main_frame.configure(bg=color)
                save_settings()
                update_preview()

        btn_bg = tk.Button(main_frame, text="Background color",
                           command=change_bg,
                           bg=settings['button_bg'], fg=settings['button_fg'],
                           font=("Segoe UI", 10), padx=20, pady=5)
        btn_bg.pack(pady=5)

        def change_editor_bg():
            color = colorchooser.askcolor(title="Select editor color")[1]
            if color:
                settings['editor_bg'] = color
                save_settings()
                update_preview()

        btn_editor = tk.Button(main_frame, text="Editor color",
                               command=change_editor_bg,
                               bg=settings['button_bg'], fg=settings['button_fg'],
                               font=("Segoe UI", 10), padx=20, pady=5)
        btn_editor.pack(pady=5)

        def change_output_bg():
            color = colorchooser.askcolor(title="Select output color")[1]
            if color:
                settings['output_bg'] = color
                save_settings()
                update_preview()

        btn_output = tk.Button(main_frame, text="Output color",
                               command=change_output_bg,
                               bg=settings['button_bg'], fg=settings['button_fg'],
                               font=("Segoe UI", 10), padx=20, pady=5)
        btn_output.pack(pady=5)

        def change_text_color():
            color = colorchooser.askcolor(title="Select text color")[1]
            if color:
                settings['text_color'] = color
                save_settings()
                update_preview()

        btn_text = tk.Button(main_frame, text="Text color",
                             command=change_text_color,
                             bg=settings['button_bg'], fg=settings['button_fg'],
                             font=("Segoe UI", 10), padx=20, pady=5)
        btn_text.pack(pady=5)

        def change_font():
            font_frame = tk.Toplevel(settings_window)
            font_frame.title("Select font")
            font_frame.geometry("300x200")
            font_frame.configure(bg=settings['bg_color'])

            tk.Label(font_frame, text="Select font:",
                     bg=settings['bg_color'], fg=settings['text_color'],
                     font=("Segoe UI", 10)).pack(pady=10)

            fonts = ['Courier', 'Arial', 'Times New Roman', 'Consolas', 'Segoe UI', 'Verdana']

            font_list = tk.Listbox(font_frame, height=6, font=("Segoe UI", 10))
            for f in fonts:
                font_list.insert(END, f)
            font_list.pack(pady=10, padx=20, fill=BOTH, expand=True)

            def apply_font():
                selected = font_list.get(ACTIVE)
                if selected:
                    settings['font_family'] = selected
                    save_settings()
                    font_frame.destroy()
                    update_preview()

            tk.Button(font_frame, text="Apply", command=apply_font,
                      bg=settings['button_bg'], fg=settings['button_fg'],
                      font=("Segoe UI", 10)).pack(pady=5)

        btn_font = tk.Button(main_frame, text="Font",
                             command=change_font,
                             bg=settings['button_bg'], fg=settings['button_fg'],
                             font=("Segoe UI", 10), padx=20, pady=5)
        btn_font.pack(pady=5)

        def change_font_size():
            size_frame = tk.Toplevel(settings_window)
            size_frame.title("Font size")
            size_frame.geometry("250x150")
            size_frame.configure(bg=settings['bg_color'])

            tk.Label(size_frame, text="Font size:",
                     bg=settings['bg_color'], fg=settings['text_color'],
                     font=("Segoe UI", 10)).pack(pady=10)

            size_var = tk.IntVar(value=settings['font_size'])
            size_spin = tk.Spinbox(size_frame, from_=8, to=24, textvariable=size_var,
                                   width=10, font=("Segoe UI", 10))
            size_spin.pack(pady=10)

            def apply_size():
                settings['font_size'] = size_var.get()
                save_settings()
                size_frame.destroy()
                update_preview()

            tk.Button(size_frame, text="Apply", command=apply_size,
                      bg=settings['button_bg'], fg=settings['button_fg'],
                      font=("Segoe UI", 10)).pack(pady=5)

        btn_size = tk.Button(main_frame, text="Font size",
                             command=change_font_size,
                             bg=settings['button_bg'], fg=settings['button_fg'],
                             font=("Segoe UI", 10), padx=20, pady=5)
        btn_size.pack(pady=5)

        def reset_settings():
            settings.update({
                'bg_color': '#060708',
                'text_color': '#d4d4d4',
                'editor_bg': '#1e1e1e',
                'output_bg': '#1e1e1e',
                'button_bg': '#242424',
                'button_fg': 'white',
                'font_family': 'Courier',
                'font_size': 10,
                'title_bg': '#0a0a0a',
                'autosave': True
            })
            save_settings()
            settings_window.destroy()
            settings_window = None
            open_settings()

        btn_reset = tk.Button(main_frame, text="Reset settings",
                              command=reset_settings,
                              bg="#c0392b", fg="white",
                              font=("Segoe UI", 10), padx=20, pady=5)
        btn_reset.pack(pady=20)

        preview_frame = tk.Frame(main_frame, bg=settings['bg_color'])
        preview_frame.pack(fill=BOTH, expand=True, pady=10)

        preview_text = tk.Text(preview_frame, height=4, width=40,
                               bg=settings['editor_bg'], fg=settings['text_color'],
                               font=(settings['font_family'], settings['font_size']),
                               relief='flat', bd=0)
        preview_text.pack(pady=5, padx=5, fill=BOTH, expand=True)
        preview_text.insert(END, "Preview text\nWith settings 😊")
        preview_text.config(state=DISABLED)

        def update_preview():
            try:
                preview_text.config(bg=settings['editor_bg'],
                                    fg=settings['text_color'],
                                    font=(settings['font_family'], settings['font_size']))
                main_frame.configure(bg=settings['bg_color'])
                settings_window.configure(bg=settings['bg_color'])
                for widget in main_frame.winfo_children():
                    if isinstance(widget, tk.Label) and widget != title:
                        widget.configure(bg=settings['bg_color'], fg=settings['text_color'])
                    elif isinstance(widget, tk.Frame):
                        widget.configure(bg=settings['bg_color'])
                        for child in widget.winfo_children():
                            if isinstance(child, tk.Label):
                                child.configure(bg=settings['bg_color'], fg=settings['text_color'])
            except:
                pass

        settings_window.mainloop()

    def open_executor():
        global executor_window, current_file

        if executor_window:
            try:
                executor_window.deiconify()
                executor_window.lift()
                return
            except:
                executor_window = None

        def new_file():
            global current_file
            txtpole.delete("1.0", END)
            current_file = None
            exemenu.title("Code Executer - New File")

        def open_file():
            global current_file
            file_path = filedialog.askopenfilename(
                defaultextension=".py",
                filetypes=[("Python files", "*.py"), ("Text files", "*.txt"), ("All files", "*.*")]
            )
            if file_path:
                current_file = file_path
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        txtpole.delete("1.0", END)
                        txtpole.insert("1.0", content)
                        exemenu.title(f"Code Executer - {os.path.basename(file_path)}")
                        highlight_syntax(txtpole)
                except Exception as e:
                    txtpole.insert("1.0", f"Error opening file: {e}")

        def save_file():
            global current_file
            if current_file:
                try:
                    with open(current_file, 'w', encoding='utf-8') as f:
                        f.write(txtpole.get("1.0", END).strip())
                    exemenu.title(f"Code Executer - {os.path.basename(current_file)}")
                except Exception as e:
                    txtpole.insert(END, f"\nError saving file: {e}")
            else:
                save_file_as()

        def save_file_as():
            global current_file
            file_path = filedialog.asksaveasfilename(
                defaultextension=".py",
                filetypes=[("Python files", "*.py"), ("Text files", "*.txt"), ("All files", "*.*")]
            )
            if file_path:
                current_file = file_path
                try:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(txtpole.get("1.0", END).strip())
                    exemenu.title(f"Code Executer - {os.path.basename(file_path)}")
                except Exception as e:
                    txtpole.insert(END, f"\nError saving file: {e}")

        def auto_save():
            if current_file and settings.get('autosave', True):
                try:
                    with open(current_file, 'w', encoding='utf-8') as f:
                        f.write(txtpole.get("1.0", END).strip())
                    status_var.set(f"Autosave: {os.path.basename(current_file)}")
                except:
                    pass
            exemenu.after(30000, auto_save)

        def insert_tab(event):
            txtpole.insert(INSERT, "    ")
            return "break"

        def auto_indent(event):
            cursor_pos = txtpole.index(INSERT)
            line_num = int(cursor_pos.split('.')[0]) - 1

            line_start = f"{line_num + 1}.0"
            line_end = f"{line_num + 1}.end"
            current_line = txtpole.get(line_start, line_end)

            if current_line.strip().endswith(':'):
                indent = "    "
                current_indent = len(current_line) - len(current_line.lstrip())
                if current_indent > 0:
                    indent = " " * current_indent + "    "
                txtpole.insert(INSERT, "\n" + indent)
                return "break"

            current_indent = len(current_line) - len(current_line.lstrip())
            if current_indent > 0:
                txtpole.insert(INSERT, "\n" + " " * current_indent)
                return "break"
            return None

        def run_code():
            code = txtpole.get("1.0", END).strip()
            if not code:
                output.insert(END, "No code to execute!\n")
                return

            output.delete("1.0", END)
            output.insert(END, "Executing...\n")

            def execute():
                try:
                    old_stdout = sys.stdout

                    class TextRedirector:
                        def __init__(self, text_widget):
                            self.text_widget = text_widget

                        def write(self, string):
                            self.text_widget.insert(END, string)
                            self.text_widget.see(END)

                        def flush(self):
                            pass

                    sys.stdout = TextRedirector(output)
                    exec_globals = {'__name__': '__main__'}
                    exec(code, exec_globals)

                except Exception as e:
                    output.insert(END, f"Error: {e}\n")
                finally:
                    sys.stdout = old_stdout
                    output.insert(END, "\nExecution complete!\n")

            threading.Thread(target=execute, daemon=True).start()

        def install_library():
            lib_name = lib_entry.get().strip()
            if not lib_name:
                output.insert(END, "Enter library name!\n")
                return

            output.insert(END, f"Installing {lib_name}...\n")

            def install():
                try:
                    result = subprocess.run(
                        [sys.executable, "-m", "pip", "install", lib_name],
                        capture_output=True,
                        text=True
                    )
                    if result.returncode == 0:
                        output.insert(END, f"{lib_name} installed successfully!\n")
                        output.insert(END, result.stdout + "\n")
                    else:
                        output.insert(END, f"Installation failed!\n{result.stderr}\n")
                except Exception as e:
                    output.insert(END, f"Error: {e}\n")

            threading.Thread(target=install, daemon=True).start()

        def clear_output():
            output.delete("1.0", END)

        def update_line_numbers(event=None):
            line_numbers.config(state=NORMAL)
            line_numbers.delete("1.0", END)

            content = txtpole.get("1.0", END)
            lines = content.count('\n')

            numbers = "\n".join(str(i) for i in range(1, lines + 2))
            line_numbers.insert("1.0", numbers)
            line_numbers.config(state=DISABLED)
            line_numbers.yview_moveto(txtpole.yview()[0])

        def on_text_change(event=None):
            update_line_numbers()
            if hasattr(on_text_change, 'after_id'):
                exemenu.after_cancel(on_text_change.after_id)
            on_text_change.after_id = exemenu.after(500, lambda: highlight_syntax(txtpole))

            if event and event.keysym in ['space', 'parenleft']:
                show_autocomplete(txtpole)

            update_status()

        def update_status():
            cursor_pos = txtpole.index(INSERT)
            line, col = cursor_pos.split('.')
            content = txtpole.get("1.0", END)
            char_count = len(content) - 1

            if current_file:
                file_name = os.path.basename(current_file)
                status_var.set(f"File: {file_name} | Line: {line} | Col: {col} | Chars: {char_count}")
            else:
                status_var.set(f"New file | Line: {line} | Col: {col} | Chars: {char_count}")

        exemenu = Tk()
        exemenu.geometry("900x700")
        exemenu.configure(bg=settings['bg_color'])
        executor_window = exemenu

        create_custom_titlebar(exemenu, "Code Executer", settings['title_bg'], [executor_window])

        main_container = tk.Frame(exemenu, bg=settings['bg_color'])
        main_container.pack(fill="both", expand=True)

        button_frame = tk.Frame(main_container, bg=settings['bg_color'])
        button_frame.pack(pady=5, fill="x")

        btn_new = tk.Button(button_frame, text="New", command=new_file,
                            bg=settings['button_bg'], fg=settings['button_fg'],
                            font=('Arial', 10), padx=10)
        btn_new.pack(side="left", padx=2)

        btn_open = tk.Button(button_frame, text="Open", command=open_file,
                             bg=settings['button_bg'], fg=settings['button_fg'],
                             font=('Arial', 10), padx=10)
        btn_open.pack(side="left", padx=2)

        btn_save = tk.Button(button_frame, text="Save", command=save_file,
                             bg=settings['button_bg'], fg=settings['button_fg'],
                             font=('Arial', 10), padx=10)
        btn_save.pack(side="left", padx=2)

        btn_save_as = tk.Button(button_frame, text="Save As", command=save_file_as,
                                bg=settings['button_bg'], fg=settings['button_fg'],
                                font=('Arial', 10), padx=10)
        btn_save_as.pack(side="left", padx=2)

        sep1 = tk.Frame(button_frame, width=2, height=30, bg="#2c3136")
        sep1.pack(side="left", padx=5)

        btn_run = tk.Button(button_frame, text="Run", command=run_code,
                            bg=settings['button_bg'], fg=settings['button_fg'],
                            font=('Arial', 10), padx=10)
        btn_run.pack(side="left", padx=2)

        btn_clear = tk.Button(button_frame, text="Clear", command=clear_output,
                              bg=settings['button_bg'], fg=settings['button_fg'],
                              font=('Arial', 10), padx=10)
        btn_clear.pack(side="left", padx=2)

        btn_find = tk.Button(button_frame, text="Find", command=lambda: find_text(txtpole),
                             bg=settings['button_bg'], fg=settings['button_fg'],
                             font=('Arial', 10), padx=10)
        btn_find.pack(side="left", padx=2)

        sep2 = tk.Frame(button_frame, width=2, height=30, bg="#2c3136")
        sep2.pack(side="left", padx=5)

        lib_label = tk.Label(button_frame, text="pip install:",
                             bg=settings['bg_color'], fg=settings['text_color'],
                             font=('Arial', 10))
        lib_label.pack(side="left", padx=5)

        lib_entry = tk.Entry(button_frame, width=20, bg="#2c3136", fg="white",
                             insertbackground='white')
        lib_entry.pack(side="left", padx=5)
        lib_entry.bind("<Return>", lambda e: install_library())

        lib_btn = tk.Button(button_frame, text="Install", command=install_library,
                            bg=settings['button_bg'], fg=settings['button_fg'],
                            font=('Arial', 10), padx=10)
        lib_btn.pack(side="left", padx=2)

        editor_frame = tk.Frame(main_container, bg=settings['bg_color'])
        editor_frame.pack(padx=10, pady=5, fill=BOTH, expand=True)

        line_numbers = tk.Text(editor_frame, width=4, padx=4,
                               bg="#252526", fg="#858585",
                               font=(settings['font_family'], settings['font_size']),
                               relief='flat', bd=0, state=DISABLED)
        line_numbers.pack(side=LEFT, fill=Y)

        txtpole = scrolledtext.ScrolledText(editor_frame,
                                            height=15,
                                            font=(settings['font_family'], settings['font_size']),
                                            bg=settings['editor_bg'],
                                            fg=settings['text_color'],
                                            insertbackground='white',
                                            selectbackground='#264f78',
                                            relief='flat',
                                            bd=0,
                                            undo=True,
                                            maxundo=100)
        txtpole.pack(padx=0, pady=0, fill=BOTH, expand=True)

        txtpole.bind("<Tab>", insert_tab)
        txtpole.bind("<Return>", auto_indent)
        txtpole.bind("<KeyRelease>", on_text_change)
        txtpole.bind("<ButtonRelease>", update_line_numbers)
        txtpole.bind("<MouseWheel>", lambda e: update_line_numbers())
        txtpole.bind("<Control-z>", lambda e: txtpole.edit_undo())
        txtpole.bind("<Control-y>", lambda e: txtpole.edit_redo())
        txtpole.bind("<Control-f>", lambda e: find_text(txtpole))
        txtpole.bind("<Control-F>", lambda e: find_text(txtpole))
        txtpole.bind("<Control-space>", lambda e: show_autocomplete(txtpole))

        exemenu.bind("<Control-o>", lambda e: open_file())
        exemenu.bind("<Control-O>", lambda e: open_file())
        exemenu.bind("<Control-s>", lambda e: save_file())
        exemenu.bind("<Control-S>", lambda e: save_file())
        exemenu.bind("<Control-n>", lambda e: new_file())
        exemenu.bind("<Control-N>", lambda e: new_file())

        def remove_tab(event):
            cursor_pos = txtpole.index(INSERT)
            line_start = f"{cursor_pos.split('.')[0]}.0"
            line_end = f"{cursor_pos.split('.')[0]}.4"

            if txtpole.get(line_start, line_end) == "    ":
                txtpole.delete(line_start, line_end)
            return "break"

        txtpole.bind("<Shift-Tab>", remove_tab)

        output_label = tk.Label(main_container, text="Output:",
                                font=("Arial", 10),
                                bg=settings['bg_color'], fg=settings['text_color'])
        output_label.pack(anchor="w", padx=10)

        output = scrolledtext.ScrolledText(main_container,
                                           height=10,
                                           font=(settings['font_family'], settings['font_size']),
                                           bg=settings['output_bg'],
                                           fg=settings['text_color'],
                                           insertbackground='white',
                                           selectbackground='#264f78',
                                           relief='flat',
                                           bd=0)
        output.pack(padx=10, pady=5, fill=BOTH, expand=True)

        status_var = tk.StringVar()
        status_var.set("Ready")

        status_bar = tk.Label(exemenu, textvariable=status_var,
                              bg="#252526", fg="#858585",
                              font=("Arial", 9), anchor="w", padx=10)
        status_bar.pack(side=BOTTOM, fill=X)

        update_line_numbers()
        update_status()
        auto_save()

        def on_closing():
            global executor_window
            if current_file and settings.get('autosave', True):
                try:
                    with open(current_file, 'w', encoding='utf-8') as f:
                        f.write(txtpole.get("1.0", END).strip())
                except:
                    pass
            executor_window = None
            exemenu.destroy()

        exemenu.protocol("WM_DELETE_WINDOW", on_closing)
        exemenu.mainloop()

    def open_donation():
        import webbrowser
        webbrowser.open("https://dalink.to/fr34ky")

    menu = Tk()
    menu.title("Main Menu")
    menu.geometry("220x250")
    menu.configure(bg=settings['bg_color'])
    main_window = menu

    create_custom_titlebar(menu, "Main Menu", settings['title_bg'], is_main=True)

    content_frame = tk.Frame(menu, bg=settings['bg_color'])
    content_frame.pack(fill="both", expand=True, pady=10)

    bt1 = tk.Button(content_frame, text="Executer", command=open_executor,
                    bg=settings['button_bg'], fg=settings['button_fg'],
                    font=('Arial', 10, 'bold'),
                    padx=20, pady=8, width=15)
    bt1.pack(pady=5)

    bt3 = tk.Button(content_frame, text="Settings", command=open_settings,
                    bg=settings['button_bg'], fg=settings['button_fg'],
                    font=('Arial', 10, 'bold'),
                    padx=20, pady=8, width=15)
    bt3.pack(pady=5)

    donate_btn = tk.Button(content_frame, text="Support", command=open_donation,
                           bg="#f39c12", fg="white",
                           font=('Arial', 10, 'bold'),
                           padx=20, pady=8, width=15)
    donate_btn.pack(pady=5)

    bt2 = tk.Button(content_frame, text="Close", command=close,
                    bg=settings['button_bg'], fg=settings['button_fg'],
                    font=('Arial', 10, 'bold'),
                    padx=20, pady=8, width=15)
    bt2.pack(pady=5)

    def hotkey_open():
        if executor_window:
            try:
                executor_window.deiconify()
                executor_window.lift()
            except:
                open_executor()
        else:
            open_executor()

    def start_keyboard_listener():
        try:
            keyboard.add_hotkey('\\', hotkey_open)
        except:
            pass

    threading.Thread(target=start_keyboard_listener, daemon=True).start()

    menu.mainloop()


start()
