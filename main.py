import os
import csv
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from yt_dlp import YoutubeDL
import sys
import subprocess
import webbrowser
import threading

from translations import set_language, t, get_language_choices, code_from_choice, get_current_choice


# Rutas base (compatibles con PyInstaller)
BASE_PATH = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
FFMPEG_PATH = os.path.join(BASE_PATH, 'ffmpeg', 'bin')


def seleccionar_csv():
    return filedialog.askopenfilename(
        title=t("select_csv"),
        filetypes=[("Archivos CSV", "*.csv"), ("Todos los archivos", "*.*")]
    )


def seleccionar_carpeta_descarga():
    return filedialog.askdirectory(title=t("select_folder"))


def es_url_valida(url: str) -> bool:
    if not url:
        return False
    url = url.strip()
    return url.startswith(("http://", "https://", "youtube.com", "youtu.be"))


def abrir_carpeta(path: str):
    if not path or not os.path.isdir(path):
        return
    try:
        if sys.platform.startswith("win"):
            os.startfile(path)
        elif sys.platform == "darwin":
            subprocess.run(["open", path], check=False)
        else:
            subprocess.run(["xdg-open", path], check=False)
    except Exception:
        pass


def construir_opciones_ydl(formato: str, carpeta_salida: str):
    outtmpl = os.path.join(carpeta_salida, "%(title)s")
    if formato == "MP3":
        return {
            "format": "bestaudio/best",
            "ffmpeg_location": FFMPEG_PATH,
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                }
            ],
            "outtmpl": outtmpl,
            "windowsfilenames": True,
            "restrictfilenames": True,
        }
    else:  # MP4
        return {
            "format": "bestvideo*+bestaudio/best",
            "ffmpeg_location": FFMPEG_PATH,
            "merge_output_format": "mp4",
            "outtmpl": outtmpl,
            "windowsfilenames": True,
            "restrictfilenames": True,
        }


def leer_urls_de_csv(ruta_csv):
    urls = []
    try:
        with open(ruta_csv, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            for row in reader:
                if row:
                    urls.append(row[0])
    except Exception as e:
        messagebox.showerror("Error", t("csv_read_error").format(error=str(e)))
    return urls


def main():
    # Idioma por defecto
    set_language("es")

    root = tk.Tk()
    def resource_path(relative_path):
        if getattr(sys, 'frozen', False):
            return os.path.join(sys._MEIPASS, relative_path)
        return os.path.join(os.path.abspath("."), relative_path)
    # Intentar cargar icono desde la carpeta assets (prevenir estiramiento si no es cuadrado)
    try:
        icon_path = resource_path("assets/dwSongs.ico")
        if os.path.exists(icon_path):
            try:
                # Preferible: usar Pillow para crear una imagen cuadrada y aplicar con iconphoto
                from PIL import Image, ImageTk
                img = Image.open(icon_path)
                img = img.convert("RGBA")
                w, h = img.size
                size = max(w, h)
                # Crear fondo transparente cuadrado y centrar la imagen original
                new = Image.new("RGBA", (size, size), (0, 0, 0, 0))
                new.paste(img, ((size - w) // 2, (size - h) // 2), img)
                tk_img = ImageTk.PhotoImage(new)
                root.iconphoto(False, tk_img)
                # Mantener referencia para que no lo recoja el GC
                root._icon_img = tk_img
            except Exception:
                # Fallback sencillo: usar .ico nativo en Windows
                try:
                    root.iconbitmap(icon_path)
                except Exception:
                    pass
    except Exception:
        pass
    root.minsize(520, 560)
    root.title(t("app_title"))

    # Título
    title_label = tk.Label(root, text=t("app_title"), font=("Arial", 16, "bold"))
    title_label.pack(pady=10)

    # Selector de idioma (OptionMenu)
    lang_var = tk.StringVar(value=get_current_choice())
    option_lang = tk.OptionMenu(root, lang_var, *get_language_choices())
    option_lang.config(width=20)
    option_lang.pack(pady=4)

    fuente_var = tk.StringVar(value="CSV")
    formato_var = tk.StringVar(value="MP3")
    csv_file_var = tk.StringVar(value=t("no_csv"))
    carpeta_var = tk.StringVar(value=t("no_folder"))

    # Frame carpeta
    frame_carpeta = tk.LabelFrame(root, text=t("folder_frame"))
    frame_carpeta.pack(fill="x", padx=12, pady=8)

    def on_seleccionar_carpeta():
        carpeta = seleccionar_carpeta_descarga()
        if carpeta:
            carpeta_var.set(carpeta)

    btn_carpeta = tk.Button(frame_carpeta, text=t("select_folder"), command=on_seleccionar_carpeta, width=30)
    btn_carpeta.pack(pady=5)
    tk.Label(frame_carpeta, textvariable=carpeta_var, wraplength=460, fg="blue").pack(pady=2)

    # Fuente de enlaces
    frame_fuente = tk.LabelFrame(root, text=t("source_frame"))
    frame_fuente.pack(fill="both", padx=12, pady=8)

    radios_frame = tk.Frame(frame_fuente)
    radios_frame.pack(fill="x", pady=5)
    rb_csv = tk.Radiobutton(radios_frame, text=t("csv"), variable=fuente_var, value="CSV")
    rb_csv.pack(side="left", padx=5)
    rb_texto = tk.Radiobutton(radios_frame, text=t("paste_text"), variable=fuente_var, value="TEXTO")
    rb_texto.pack(side="left", padx=5)

    frame_csv = tk.Frame(frame_fuente)
    frame_csv.pack(fill="x", pady=5)

    def on_seleccionar_csv():
        file = seleccionar_csv()
        if file:
            csv_file_var.set(file)

    btn_csv = tk.Button(frame_csv, text=t("select_csv"), command=on_seleccionar_csv, width=30)
    btn_csv.pack(pady=5)
    tk.Label(frame_csv, textvariable=csv_file_var, wraplength=460, fg="blue").pack(pady=2)

    frame_texto = tk.Frame(frame_fuente)
    frame_texto.pack(fill="both", pady=5)
    label_paste = tk.Label(frame_texto, text=t("paste_links_label"))
    label_paste.pack(anchor="w")
    texto_urls = tk.Text(frame_texto, height=8, wrap="word")
    texto_urls.pack(fill="both", padx=2, pady=4)

    def actualizar_visibilidad_fuente(*args):
        if fuente_var.get() == "CSV":
            frame_csv.pack(fill="x", pady=5)
            frame_texto.pack_forget()
        else:
            frame_texto.pack(fill="both", pady=5)
            frame_csv.pack_forget()
        # Forzar recálculo de tamaño de la ventana para ajustar altura dinámica
        try:
            root.update_idletasks()
            # mantener el ancho mínimo de 520 y ajustar la altura requerida
            root.geometry(f"{max(520, root.winfo_width())}x{root.winfo_reqheight()}")
        except Exception:
            pass

    fuente_var.trace_add("write", actualizar_visibilidad_fuente)
    actualizar_visibilidad_fuente()

    # Formato
    frame_formato = tk.LabelFrame(root, text=t("format_frame"))
    frame_formato.pack(fill="x", padx=12, pady=8)
    rb_mp3 = tk.Radiobutton(frame_formato, text=t("mp3"), variable=formato_var, value="MP3")
    rb_mp3.pack(side="left", padx=8, pady=5)
    rb_mp4 = tk.Radiobutton(frame_formato, text=t("mp4"), variable=formato_var, value="MP4")
    rb_mp4.pack(side="left", padx=8, pady=5)

    # Barra de progreso
    progress_var = tk.IntVar()
    progress_bar = ttk.Progressbar(root, orient="horizontal", length=400, mode="determinate", variable=progress_var)
    progress_bar.pack(pady=10)

    # Enlace autor
    link1 = tk.Label(root, text=t("author_link"), fg="blue", cursor="hand2")
    link1.pack(pady=6)

    def _abrir_github(event=None):
        try:
            webbrowser.open_new("https://github.com/ldbl1")
        except Exception:
            pass

    link1.bind("<Button-1>", _abrir_github)

    # Funciones de descarga
    def realizar_descarga(urls, carpeta, formato):
        ok_count = 0
        error_count = 0
        invalid_count = 0

        ydl_opts = construir_opciones_ydl(formato, carpeta)

        progress_bar["maximum"] = len(urls)
        progress_var.set(0)

        with YoutubeDL(ydl_opts) as ydl:
            for i, raw in enumerate(urls, start=1):
                url = (raw or "").strip()
                if not es_url_valida(url):
                    invalid_count += 1
                else:
                    try:
                        ydl.download([url])
                        ok_count += 1
                    except Exception as e:
                        print(f"Error al descargar {url}: {e}")
                        error_count += 1
                progress_var.set(i)
                root.update_idletasks()

        root.after(0, lambda: mostrar_resultado(ok_count, error_count, invalid_count, carpeta))

    def mostrar_resultado(ok_count, error_count, invalid_count, carpeta):
        desbloquear_widgets()
        stats = t("download_stats").format(ok=ok_count, err=error_count, inv=invalid_count)
        msg = f"{t('download_finished')}\n\n{stats}\n\n{t('download_open_folder_question')}"
        abrir = messagebox.askyesno(t("download_finished"), msg)
        if abrir:
            abrir_carpeta(carpeta)

    def on_descargar():
        bloquear_widgets()

        carpeta = carpeta_var.get()
        if not carpeta or not os.path.isdir(carpeta):
            messagebox.showerror("Error", t("error_select_folder"))
            desbloquear_widgets()
            return

        if fuente_var.get() == "CSV":
            ruta_csv = csv_file_var.get()
            if not ruta_csv or not os.path.isfile(ruta_csv):
                messagebox.showerror("Error", t("error_select_csv"))
                desbloquear_widgets()
                return
            urls = leer_urls_de_csv(ruta_csv)
        else:
            contenido = texto_urls.get("1.0", "end").strip()
            urls = [line for line in contenido.splitlines() if line.strip()]

        if not urls:
            messagebox.showerror("Error", t("error_no_urls"))
            desbloquear_widgets()
            return

        thread = threading.Thread(target=realizar_descarga, args=(urls, carpeta, formato_var.get()), daemon=True)
        thread.start()

    def reset_values():
        carpeta_var.set(t("no_folder"))
        csv_file_var.set(t("no_csv"))
        texto_urls.delete("1.0", "end")
        progress_var.set(0)
        fuente_var.set("CSV")
        formato_var.set("MP3")
        actualizar_visibilidad_fuente()

    # Botones
    frame_botones = tk.Frame(root)
    frame_botones.pack(pady=12)

    btn_descargar = tk.Button(frame_botones, text=t("download"), command=on_descargar, width=15, bg="green", fg="white")
    btn_descargar.pack(side="left", padx=6)

    btn_reset = tk.Button(frame_botones, text=t("reset"), command=reset_values, width=15, bg="orange", fg="white")
    btn_reset.pack(side="left", padx=6)

    widgets_a_bloquear = [btn_carpeta, btn_csv, rb_csv, rb_texto, rb_mp3, rb_mp4, texto_urls, btn_descargar, btn_reset]

    notice_label = tk.Label(root, text=t("uses_notice"), fg="gray")
    notice_label.pack(pady=6)

    def bloquear_widgets():
        for w in widgets_a_bloquear:
            try:
                w.config(state="disabled")
            except Exception:
                pass

    def desbloquear_widgets():
        for w in widgets_a_bloquear:
            try:
                w.config(state="normal")
            except Exception:
                pass

    # Actualizar UI cuando se cambia el idioma
    def update_ui_language():
        root.title(t("app_title"))
        title_label.config(text=t("app_title"))
        frame_carpeta.config(text=t("folder_frame"))
        btn_carpeta.config(text=t("select_folder"))
        frame_fuente.config(text=t("source_frame"))
        rb_csv.config(text=t("csv"))
        rb_texto.config(text=t("paste_text"))
        btn_csv.config(text=t("select_csv"))
        label_paste.config(text=t("paste_links_label"))
        frame_formato.config(text=t("format_frame"))
        rb_mp3.config(text=t("mp3"))
        rb_mp4.config(text=t("mp4"))
        btn_descargar.config(text=t("download"))
        btn_reset.config(text=t("reset"))
        link1.config(text=t("author_link"))
        notice_label.config(text=t("uses_notice"))

    def on_lang_change(*args):
        choice = lang_var.get()
        code = code_from_choice(choice)
        set_language(code)
        # actualizar textos
        update_ui_language()

    lang_var.trace_add("write", on_lang_change)

    root.mainloop()


if __name__ == "__main__":
    main()
