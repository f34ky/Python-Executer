import sys
from tkinter import *
import tkinter as tk
from tkinter import ttk, scrolledtext
import random
import time
import keyboard
import subprocess
import threading
import os

# только попробуйте сказать что это ИИ! Это все писал ЯЯЯЯЯ!
# Библиотеки написаны для будущих версий ес шо.
# крч бтв кстати это я писал все сам бтв кстати!
# дада, все сам, в ирл реальной жизни бтв кстати.

# Глобальные переменные для окон
main_window = None
executor_window = None
close_window_ref = None


def create_custom_titlebar(window, title_text, bg_color="#1a1a1a", window_ref=None, is_main=False):
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


def start():
    global main_window, executor_window, close_window_ref

    # открывает окно крч
    def close():
        global close_window_ref

        # ес ор но(ес)
        def ye():
            sys.exit()

        # ес ор но(но)
        def no():
            global close_window_ref
            if close_window_ref:
                close_window_ref.destroy()
                close_window_ref = None

        # окно ес ор но
        close_window = Tk()
        close_window.geometry("200x150")
        close_window.configure(bg="#2c3e50")
        close_window_ref = close_window

        create_custom_titlebar(close_window, "Confirm", "#1a1a1a")

        content_frame = tk.Frame(close_window, bg="#2c3e50")
        content_frame.pack(fill="both", expand=True)

        lb = tk.Label(content_frame, text="You sure?",
                      font=("Segoe UI", 10), fg="White", bg="#2c3e50")
        lb.pack(pady=10)

        btn_frame = tk.Frame(content_frame, bg="#2c3e50")
        btn_frame.pack(pady=10)

        btn1 = tk.Button(btn_frame, text="Yes", command=ye,
                         bg="#242424", fg="white",
                         font=("Segoe UI", 10, "bold"),
                         padx=20, pady=5)
        btn1.pack(side="left", padx=5)

        btn2 = tk.Button(btn_frame, text="No", command=no,
                         bg="#242424", fg="white",
                         font=("Segoe UI", 10, "bold"),
                         padx=20, pady=5)
        btn2.pack(side="left", padx=5)

        close_window.update_idletasks()
        width = close_window.winfo_width()
        height = close_window.winfo_height()
        x = (close_window.winfo_screenwidth() // 2) - (width // 2)
        y = (close_window.winfo_screenheight() // 2) - (height // 2)
        close_window.geometry(f"{width}x{height}+{x}+{y}")

        close_window.mainloop()

    # открывает само окно с экзекьютером.
    def open_executor():
        global executor_window

        if executor_window:
            try:
                executor_window.deiconify()
                executor_window.lift()
                return
            except:
                executor_window = None

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
                output.insert(END, "⚠️ No code to execute!\n")
                return

            output.delete("1.0", END)
            output.insert(END, "▶️ Executing...\n")

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
                    output.insert(END, f"❌ Error: {e}\n")
                finally:
                    sys.stdout = old_stdout
                    output.insert(END, "\n✅ Execution complete!\n")

            threading.Thread(target=execute, daemon=True).start()

        def install_library():
            lib_name = lib_entry.get().strip()
            if not lib_name:
                output.insert(END, "⚠️ Enter library name!\n")
                return

            output.insert(END, f"📦 Installing {lib_name}...\n")

            def install():
                try:
                    result = subprocess.run(
                        [sys.executable, "-m", "pip", "install", lib_name],
                        capture_output=True,
                        text=True
                    )
                    if result.returncode == 0:
                        output.insert(END, f"✅ {lib_name} installed successfully!\n")
                        output.insert(END, result.stdout + "\n")
                    else:
                        output.insert(END, f"❌ Installation failed!\n{result.stderr}\n")
                except Exception as e:
                    output.insert(END, f"❌ Error: {e}\n")

            threading.Thread(target=install, daemon=True).start()

        def clear_output():
            output.delete("1.0", END)

        exemenu = Tk()
        exemenu.geometry("700x600")
        exemenu.configure(bg="#060708")
        executor_window = exemenu

        create_custom_titlebar(exemenu, "Code Executer", "#0a0a0a", [executor_window])

        main_frame = tk.Frame(exemenu, bg="#060708")
        main_frame.pack(fill="both", expand=True)

        button_frame = tk.Frame(main_frame, bg="#060708")
        button_frame.pack(pady=5)

        btn = tk.Button(button_frame, text="▶", command=run_code, bg="#060708", fg="white",
                        font=('Arial', 10), padx=10)
        btn.pack(side="left", padx=5)

        btn2 = tk.Button(button_frame, text="Clear", command=clear_output, bg="#060708", fg="white",
                         font=('Arial', 10), padx=10)
        btn2.pack(side="left", padx=5)

        sep = tk.Frame(button_frame, width=2, height=30, bg="#2c3136")
        sep.pack(side="left", padx=10)

        lib_label = tk.Label(button_frame, text="pip install:", bg="#060708", fg="white", font=('Arial', 10))
        lib_label.pack(side="left", padx=5)

        lib_entry = tk.Entry(button_frame, width=20, bg="#2c3136", fg="white",
                             insertbackground='white')
        lib_entry.pack(side="left", padx=5)
        lib_entry.bind("<Return>", lambda e: install_library())

        lib_btn = tk.Button(button_frame, text="Install", command=install_library,
                            bg="#060708", fg="white", font=('Arial', 10), padx=10)
        lib_btn.pack(side="left", padx=5)

        txt_label = tk.Label(main_frame, text=" Code Editor:", font=("Arial", 10), bg="#060708", fg="white")
        txt_label.pack(anchor="w", padx=10)

        txtpole = scrolledtext.ScrolledText(main_frame,
                                            height=15,
                                            font=("Courier", 10),
                                            bg="#1e1e1e",
                                            fg="#d4d4d4",
                                            insertbackground='white',
                                            selectbackground='#264f78',
                                            relief='flat',
                                            bd=0)
        txtpole.pack(padx=10, pady=5, fill=BOTH, expand=True)

        txtpole.bind("<Tab>", insert_tab)

        def remove_tab(event):
            cursor_pos = txtpole.index(INSERT)
            line_start = f"{cursor_pos.split('.')[0]}.0"
            line_end = f"{cursor_pos.split('.')[0]}.4"

            if txtpole.get(line_start, line_end) == "    ":
                txtpole.delete(line_start, line_end)
            return "break"

        txtpole.bind("<Shift-Tab>", remove_tab)
        txtpole.bind("<Return>", auto_indent)

        output_label = tk.Label(main_frame, text="Output:", font=("Arial", 10), bg="#060708", fg="white")
        output_label.pack(anchor="w", padx=10)

        output = scrolledtext.ScrolledText(main_frame,
                                           height=10,
                                           font=("Courier", 10),
                                           bg="#1e1e1e",
                                           fg="#d4d4d4",
                                           insertbackground='white',
                                           selectbackground='#264f78',
                                           relief='flat',
                                           bd=0)
        output.pack(padx=10, pady=5, fill=BOTH, expand=True)

        def on_closing():
            global executor_window
            executor_window = None
            exemenu.destroy()

        exemenu.protocol("WM_DELETE_WINDOW", on_closing)
        exemenu.mainloop()

    # а не, вот главное меню бтв кстати
    menu = Tk()
    menu.title("Main Menu")
    menu.geometry("200x150")
    menu.configure(bg="#050505")
    main_window = menu

    create_custom_titlebar(menu, "Main Menu", "#0a0a0a", is_main=True)

    content_frame = tk.Frame(menu, bg="#050505")
    content_frame.pack(fill="both", expand=True)

    bt1 = tk.Button(content_frame, text="Executer", command=open_executor,
                    bg="#242424", fg="white", font=('Arial', 10, 'bold'),
                    padx=20, pady=8)
    bt1.pack(pady=10)

    bt2 = tk.Button(content_frame, text="Close", command=close,
                    bg="#242424", fg="white", font=('Arial', 10, 'bold'),
                    padx=20, pady=8)
    bt2.pack(pady=10)

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