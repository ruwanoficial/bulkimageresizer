import os
import threading
import platform
import subprocess
from PIL import Image
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import io

MAX_SIZE = 1024 * 1024  # 1MB

def compress_image(input_path, output_path, format_choice):
    try:
        with Image.open(input_path) as img:
            img = img.convert("RGB")
            quality = 95
            step = 5

            ext = format_choice.upper()
            save_kwargs = {'format': ext}
            if ext == 'JPEG':
                save_kwargs['quality'] = quality
            elif ext == 'WEBP':
                save_kwargs['quality'] = quality
                save_kwargs['method'] = 6

            MAX_WIDTH = 1920
            MAX_HEIGHT = 1080

            width, height = img.size
            width_ratio = MAX_WIDTH / width if width > MAX_WIDTH else 1
            height_ratio = MAX_HEIGHT / height if height > MAX_HEIGHT else 1
            scale_factor = min(width_ratio, height_ratio)

            if scale_factor < 1:
                new_width = int(width * scale_factor)
                new_height = int(height * scale_factor)
                img = img.resize((new_width, new_height), Image.LANCZOS)

            while quality > 5:
                buffer = io.BytesIO()
                img.save(buffer, **save_kwargs)
                size = buffer.tell()

                if size <= MAX_SIZE:
                    with open(output_path, 'wb') as f:
                        f.write(buffer.getvalue())
                    return True

                quality -= step
                if ext in ['JPEG', 'WEBP']:
                    save_kwargs['quality'] = quality

            width, height = img.size
            scale_factor = 0.9
            while True:
                width = int(width * scale_factor)
                height = int(height * scale_factor)
                img = img.resize((width, height), Image.LANCZOS)
                buffer = io.BytesIO()
                img.save(buffer, **save_kwargs)

                if buffer.tell() <= MAX_SIZE or width < 300 or height < 300:
                    with open(output_path, 'wb') as f:
                        f.write(buffer.getvalue())
                    return True

    except Exception as e:
        print(f"Error compressing {input_path}: {e}")
        return False

def save_image_in_format(input_path, output_path, format_choice):
    try:
        with Image.open(input_path) as img:
            img = img.convert("RGB")
            if format_choice.upper() == 'WEBP':
                img.save(output_path, format='WEBP', quality=95, method=6)
            elif format_choice.upper() == 'PNG':
                img.save(output_path, format='PNG', optimize=True)
            else:
                img.save(output_path, format='JPEG', quality=95)
    except Exception as e:
        print(f"Error saving {input_path} in format {format_choice}: {e}")

def open_folder(path):
    if platform.system() == "Windows":
        os.startfile(path)
    elif platform.system() == "Darwin":
        subprocess.Popen(["open", path])
    else:
        subprocess.Popen(["xdg-open", path])

def process_folder(folder_path, format_choice, status_label, progress_bar, start_button, select_button, folder_label, open_button, start_over_button):
    supported_formats = ('.jpg', '.jpeg', '.png', '.webp', '.gif', '.bmp')
    output_base = os.path.join(folder_path, "compressed")
    os.makedirs(output_base, exist_ok=True)

    ext_map = {
        'JPEG': '.jpeg',
        'PNG': '.png',
        'WEBP': '.webp'
    }
    output_ext = ext_map.get(format_choice.upper(), '.jpeg')

    total_files = 0
    for root, _, files in os.walk(folder_path):
        total_files += sum(1 for f in files if f.lower().endswith(supported_formats))

    if total_files == 0:
        status_label.config(text="No supported images found in the folder.")
        start_button.config(state="normal")
        select_button.config(state="normal")
        progress_bar.pack_forget()
        open_button.config(state="disabled")
        start_over_button.config(state="disabled")
        return

    progress_bar['maximum'] = total_files
    progress_bar['value'] = 0
    progress_bar.pack()

    count = 0
    for root, _, files in os.walk(folder_path):
        for file in files:
            if file.lower().endswith(supported_formats):
                input_path = os.path.join(root, file)
                rel_path = os.path.relpath(root, folder_path)
                output_folder = os.path.join(output_base, rel_path)
                os.makedirs(output_folder, exist_ok=True)

                output_file = os.path.splitext(file)[0] + output_ext
                output_path = os.path.join(output_folder, output_file)

                if os.path.getsize(input_path) <= MAX_SIZE:
                    save_image_in_format(input_path, output_path, format_choice)
                else:
                    compress_image(input_path, output_path, format_choice)

                count += 1
                progress_bar['value'] = count
                progress_bar.update()  # Ensure progress bar redraws properly
                status_label.config(text=f"Processing {count} of {total_files} images...")
                status_label.update()

    status_label.config(text=f"✅ Done! {count} images processed to '{format_choice.upper()}' in:\n{output_base}")
    messagebox.showinfo("Finished", f"{count} images processed and saved to:\n{output_base}")

    start_button.config(state="disabled")
    select_button.config(state="disabled")
    open_button.config(state="normal")
    start_over_button.config(state="normal")
    progress_bar.pack_forget()

def select_folder(folder_label, start_button, open_button, folder_path_var, start_over_button):
    folder_selected = filedialog.askdirectory()
    if folder_selected:
        folder_label.config(text=f"Selected folder:\n{folder_selected}")
        start_button.config(state="normal")
        open_button.config(state="disabled")
        start_over_button.config(state="disabled")
        folder_path_var.set(folder_selected)
    else:
        folder_label.config(text="")
        start_button.config(state="disabled")
        open_button.config(state="disabled")
        start_over_button.config(state="disabled")
        folder_path_var.set("")

def on_start(format_var, folder_path_var, status_label, progress_bar, start_button, select_button, folder_label, open_button, start_over_button):
    folder_path = folder_path_var.get()
    if not folder_path:
        messagebox.showerror("Error", "Please select a folder first.")
        return

    format_choice = format_var.get()
    if not format_choice:
        messagebox.showerror("Error", "Please select an output format.")
        return

    start_button.config(state="disabled")
    select_button.config(state="disabled")
    open_button.config(state="disabled")
    start_over_button.config(state="disabled")
    status_label.config(text="Starting compression...")
    progress_bar['value'] = 0
    progress_bar.pack()

    def run_process():
        process_folder(folder_path, format_choice, status_label, progress_bar, start_button, select_button, folder_label, open_button, start_over_button)

    threading.Thread(target=run_process, daemon=True).start()

def on_start_over(folder_label, start_button, select_button, open_button, status_label, progress_bar, folder_path_var, start_over_button):
    folder_path_var.set("")
    folder_label.config(text="")
    start_button.config(state="disabled")
    select_button.config(state="normal")
    open_button.config(state="disabled")
    start_over_button.config(state="disabled")
    status_label.config(text="")
    progress_bar.pack_forget()

def create_gui():
    root = tk.Tk()
    root.title("EvoLabs Image Compressor")
    root.geometry("480x510")
    root.resizable(False, False)

    style = ttk.Style()
    style.theme_use("clam")

    # Style for labels and buttons
    root.configure(bg="#1e1e1e")
    style.configure("TLabel", background="#1e1e1e", foreground="#f0f0f0", font=("Segoe UI", 11))
    style.configure("TButton", background="#4CAF50", foreground="white", font=("Segoe UI", 11, "bold"), padding=6)
    style.map("TButton",
              background=[("active", "#45a049"), ("disabled", "#888")],
              foreground=[("active", "white")])
    style.configure("TCombobox", font=("Segoe UI", 10))

    # Progress bar style — thicker and clearly visible
    style.configure("green.Horizontal.TProgressbar",
                    troughcolor='#2e2e2e',
                    background='#4CAF50',
                    thickness=25,
                    bordercolor='#1e1e1e',
                    lightcolor='#66bb6a',
                    darkcolor='#388e3c')

    style.layout("green.Horizontal.TProgressbar",
        [('Horizontal.Progressbar.trough',
          {'children': [('Horizontal.Progressbar.pbar',
                         {'side': 'left', 'sticky': 'nswe'})],
           'sticky': 'nswe'})])

    title = ttk.Label(root, text="📦 Image Compressor - Under 1MB")
    title.pack(pady=(20, 10))

    format_label = ttk.Label(root, text="Select output format:")
    format_label.pack()

    format_var = tk.StringVar()
    format_dropdown = ttk.Combobox(root, textvariable=format_var, state="readonly", width=10)
    format_dropdown['values'] = ('JPEG', 'PNG', 'WEBP')
    format_dropdown.current(0)
    format_dropdown.pack(pady=5)

    folder_label = ttk.Label(root, text="", font=("Segoe UI", 9), wraplength=460, justify="center")
    folder_label.pack(pady=(10, 5))

    select_button = ttk.Button(root, text="📂 Select Folder")
    select_button.pack(pady=(5,10))

    start_button = ttk.Button(root, text="▶️ Start Compression", state="disabled")
    start_button.pack(pady=10)

    open_button = ttk.Button(root, text="📁 Open Compressed Folder", state="disabled")
    open_button.pack(pady=(5, 15))

    start_over_button = ttk.Button(root, text="🔄 Start Over", state="disabled")
    start_over_button.pack(pady=(5, 15))

    status_label = ttk.Label(root, text="", font=("Segoe UI", 10), wraplength=460, justify="center")
    status_label.pack(pady=(5,10))

    progress_bar = ttk.Progressbar(root, orient="horizontal", length=420,
                                   mode='determinate', style="green.Horizontal.TProgressbar")
    progress_bar.pack(pady=(10, 25))

    # Try to set height explicitly (may not work on all platforms)
    try:
        progress_bar.config(height=25)
    except:
        pass

    footer = ttk.Label(root, text="© 2025 EvoLabs. All rights reserved.", font=("Segoe UI", 8))
    footer.pack(side="bottom", pady=10)

    folder_path_var = tk.StringVar()

    def on_select():
        select_folder(folder_label, start_button, open_button, folder_path_var, start_over_button)

    def on_open():
        output_folder = os.path.join(folder_path_var.get(), "compressed")
        if os.path.exists(output_folder):
            open_folder(output_folder)
        else:
            messagebox.showerror("Error", "Compressed folder not found.")

    select_button.config(command=on_select)
    start_button.config(command=lambda: on_start(format_var, folder_path_var, status_label, progress_bar, start_button, select_button, folder_label, open_button, start_over_button))
    open_button.config(command=on_open)
    start_over_button.config(command=lambda: on_start_over(folder_label, start_button, select_button, open_button, status_label, progress_bar, folder_path_var, start_over_button))

    root.mainloop()

if __name__ == "__main__":
    create_gui()
