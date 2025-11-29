import os
import csv
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from yt_dlp import YoutubeDL
import sys
import subprocess

# Rutas base (compatibles con PyInstaller)
BASE_PATH = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
FFMPEG_PATH = os.path.join(BASE_PATH, 'ffmpeg', 'bin')

def seleccionar_csv():
    return filedialog.askopenfilename(
        title="Selecciona el archivo CSV con enlaces de YouTube",
        filetypes=[("Archivos CSV", "*.csv"), ("Todos los archivos", "*.*")]
    )

def seleccionar_carpeta_descarga():
    return filedialog.askdirectory(title="Selecciona la carpeta de descarga")

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
        messagebox.showerror("Error", f"No se pudo leer el CSV: {str(e)}")
    return urls

def main():
    root = tk.Tk()
    root.title("dwSongs")
    root.geometry("520x680")

    tk.Label(root, text="dwSongs: Descargador de YouTube", font=("Arial", 16, "bold")).pack(pady=10)

    fuente_var = tk.StringVar(value="CSV")
    formato_var = tk.StringVar(value="MP3")
    csv_file_var = tk.StringVar(value="Sin archivo seleccionado")
    carpeta_var = tk.StringVar(value="Sin carpeta seleccionada")

    frame_carpeta = tk.LabelFrame(root, text="Carpeta de descarga")
    frame_carpeta.pack(fill="x", padx=12, pady=8)
    def on_seleccionar_carpeta():
        carpeta = seleccionar_carpeta_descarga()
        if carpeta:
            carpeta_var.set(carpeta)
    btn_carpeta = tk.Button(frame_carpeta, text="Seleccionar carpeta...", command=on_seleccionar_carpeta, width=30).pack(pady=5)
    tk.Label(frame_carpeta, textvariable=carpeta_var, wraplength=460, fg="blue").pack(pady=2)

    frame_fuente = tk.LabelFrame(root, text="Fuente de enlaces")
    frame_fuente.pack(fill="both", padx=12, pady=8)

    radios_frame = tk.Frame(frame_fuente)
    radios_frame.pack(fill="x", pady=5)
    rb_csv = tk.Radiobutton(radios_frame, text="CSV", variable=fuente_var, value="CSV").pack(side="left", padx=5)
    rb_texto = tk.Radiobutton(radios_frame, text="Pegar texto", variable=fuente_var, value="TEXTO").pack(side="left", padx=5)

    frame_csv = tk.Frame(frame_fuente)
    frame_csv.pack(fill="x", pady=5)
    def on_seleccionar_csv():
        file = seleccionar_csv()
        if file:
            csv_file_var.set(file)
    btn_csv = tk.Button(frame_csv, text="Seleccionar archivo CSV...", command=on_seleccionar_csv, width=30).pack(pady=5)
    tk.Label(frame_csv, textvariable=csv_file_var, wraplength=460, fg="blue").pack(pady=2)

    frame_texto = tk.Frame(frame_fuente)
    frame_texto.pack(fill="both", pady=5)
    tk.Label(frame_texto, text="Pega aquí los enlaces (uno por línea):").pack(anchor="w")
    texto_urls = tk.Text(frame_texto, height=8, wrap="word")
    texto_urls.pack(fill="both", padx=2, pady=4)

    def actualizar_visibilidad_fuente(*args):
        if fuente_var.get() == "CSV":
            frame_csv.pack(fill="x", pady=5)
            frame_texto.pack_forget()
        else:
            frame_texto.pack(fill="both", pady=5)
            frame_csv.pack_forget()
    fuente_var.trace_add("write", actualizar_visibilidad_fuente)
    actualizar_visibilidad_fuente()

    frame_formato = tk.LabelFrame(root, text="Formato de salida")
    frame_formato.pack(fill="x", padx=12, pady=8)
    rb_mp3 = tk.Radiobutton(frame_formato, text="MP3 (audio)", variable=formato_var, value="MP3").pack(side="left", padx=8, pady=5)
    rb_mp4 = tk.Radiobutton(frame_formato, text="MP4 (video)", variable=formato_var, value="MP4").pack(side="left", padx=8, pady=5)

    # Barra de progreso
    progress_var = tk.IntVar()
    progress_bar = ttk.Progressbar(root, orient="horizontal", length=400, mode="determinate", variable=progress_var)
    progress_bar.pack(pady=10)

    # Lista de widgets a bloquear (excepto la barra de progreso)


    def on_descargar():
        #bloquear_widgets()

        carpeta = carpeta_var.get()
        if not carpeta or not os.path.isdir(carpeta):
            messagebox.showerror("Error", "Por favor, selecciona una carpeta válida de descarga.")
            return

        if fuente_var.get() == "CSV":
            ruta_csv = csv_file_var.get()
            if not ruta_csv or not os.path.isfile(ruta_csv):
                messagebox.showerror("Error", "Por favor, selecciona un archivo CSV válido.")
                return
            urls = leer_urls_de_csv(ruta_csv)
        else:
            contenido = texto_urls.get("1.0", "end").strip()
            urls = [line for line in contenido.splitlines() if line.strip()]

        if not urls:
            messagebox.showerror("Error", "No se han encontrado enlaces para descargar.")
            return

        ok_count = 0
        error_count = 0
        invalid_count = 0

        ydl_opts = construir_opciones_ydl(formato_var.get(), carpeta)

        progress_bar["maximum"] = len(urls)
        progress_var.set(0)

        with YoutubeDL(ydl_opts) as ydl:
            for i, raw in enumerate(urls, start=1):
                url = (raw or "").strip()
                if not es_url_valida(url):
                    invalid_count += 1
                    print(f"Saltando URL inválida: {url}")
                else:
                    try:
                        ydl.download([url])
                        ok_count += 1
                    except Exception as e:
                        print(f"Error al descargar {url}: {e}")
                        error_count += 1
                progress_var.set(i)
                root.update_idletasks()

        msg = (
            f"Descarga finalizada.\n\n"
            f"Correctas: {ok_count}\n"
            f"Con error: {error_count}\n"
            f"Inválidas: {invalid_count}\n\n"
            f"¿Quieres abrir la carpeta de descarga?"
        )
        abrir = messagebox.askyesno("Finalizado", msg)
        if abrir:
            abrir_carpeta(carpeta)
        #desbloquear_widgets()

    btn_descargar = tk.Button(root, text="Descargar", command=on_descargar, width=30, bg="green", fg="white")
    btn_descargar.pack(pady=12)

    widgets_a_bloquear = [btn_carpeta, btn_csv, rb_csv, rb_texto, rb_mp3, rb_mp4, texto_urls, btn_descargar]

    tk.Label(root, text="Usa este programa respetando los términos de YouTube y derechos de autor.", fg="gray").pack(pady=6)


    def bloquear_widgets():
        for w in widgets_a_bloquear:
            w.config(state="disabled")

    def desbloquear_widgets():
        for w in widgets_a_bloquear:
            w.config(state="normal")

    root.mainloop()

if __name__ == "__main__":
    main()
