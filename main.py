import os
import csv
import tkinter as tk
from tkinter import filedialog, messagebox
from yt_dlp import YoutubeDL
import sys
import subprocess

# Rutas base (compatibles con PyInstaller)
BASE_PATH = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
FFMPEG_PATH = os.path.join(BASE_PATH, 'ffmpeg', 'bin')

def seleccionar_csv():
    """Diálogo para seleccionar CSV"""
    return filedialog.askopenfilename(
        title="Selecciona el archivo CSV con enlaces de YouTube",
        filetypes=[("Archivos CSV", "*.csv"), ("Todos los archivos", "*.*")]
    )

def seleccionar_carpeta_descarga():
    """Diálogo para seleccionar carpeta de destino"""
    return filedialog.askdirectory(title="Selecciona la carpeta de descarga")

def es_url_valida(url: str) -> bool:
    """Valida si la URL parece de YouTube"""
    if not url:
        return False
    url = url.strip()
    return url.startswith(("http://", "https://", "youtube.com", "youtu.be"))

def abrir_carpeta(path: str):
    """Abrir carpeta de forma multiplataforma"""
    if not path or not os.path.isdir(path):
        return
    try:
        if sys.platform.startswith("win"):
            os.startfile(path)  # Windows
        elif sys.platform == "darwin":
            subprocess.run(["open", path], check=False)  # macOS
        else:
            subprocess.run(["xdg-open", path], check=False)  # Linux
    except Exception:
        # En caso de fallo, no hacemos nada; ya se mostró ruta en UI
        pass

def construir_opciones_ydl(formato: str, carpeta_salida: str):
    """Construye opciones para yt-dlp según formato objetivo."""
    # Plantilla de nombre de salida (sin extensión explícita; la gestiona yt-dlp)
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
            # Evita espacios raros y caracteres problemáticos en nombres
            "windowsfilenames": True,
            "restrictfilenames": True,
        }
    else:  # MP4
        return {
            # Intenta mejor video+audio, si no disponible, mejor disponible
            "format": "bestvideo*+bestaudio/best",
            "ffmpeg_location": FFMPEG_PATH,
            # Fuerza contenedor MP4 en el merge si es posible
            "merge_output_format": "mp4",
            "outtmpl": outtmpl,
            "windowsfilenames": True,
            "restrictfilenames": True,
        }

def descargar_desde_fuente(urls, carpeta_salida, formato_objetivo):
    """Descarga una lista de URLs, devuelve (ok, errores, invalidas)."""
    ok_count = 0
    error_count = 0
    invalid_count = 0

    ydl_opts = construir_opciones_ydl(formato_objetivo, carpeta_salida)

    try:
        with YoutubeDL(ydl_opts) as ydl:
            for raw in urls:
                url = (raw or "").strip()
                if not es_url_valida(url):
                    invalid_count += 1
                    print(f"Saltando URL inválida: {url}")
                    continue
                print(f"Descargando: {url}")
                try:
                    ydl.download([url])
                    ok_count += 1
                except Exception as e:
                    print(f"Error al descargar {url}: {e}")
                    error_count += 1
    except Exception as e:
        messagebox.showerror("Error", f"Se produjo un error general: {str(e)}")

    return ok_count, error_count, invalid_count

def leer_urls_de_csv(ruta_csv):
    """Lee la primera columna del CSV como lista de URLs."""
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
    """Ventana principal de GUI"""
    root = tk.Tk()
    root.title("dwSongs")
    root.geometry("520x540")

    # Título
    tk.Label(root, text="dwSongs: Descargador de YouTube", font=("Arial", 16, "bold")).pack(pady=10)

    # Variables de estado
    fuente_var = tk.StringVar(value="CSV")  # CSV o TEXTO
    formato_var = tk.StringVar(value="MP3") # MP3 o MP4
    csv_file_var = tk.StringVar(value="Sin archivo seleccionado")
    carpeta_var = tk.StringVar(value="Sin carpeta seleccionada")

    # Sección: seleccionar carpeta
    frame_carpeta = tk.LabelFrame(root, text="Carpeta de descarga")
    frame_carpeta.pack(fill="x", padx=12, pady=8)
    def on_seleccionar_carpeta():
        carpeta = seleccionar_carpeta_descarga()
        if carpeta:
            carpeta_var.set(carpeta)
    tk.Button(frame_carpeta, text="Seleccionar carpeta...", command=on_seleccionar_carpeta, width=30).pack(pady=5)
    tk.Label(frame_carpeta, textvariable=carpeta_var, wraplength=460, fg="blue").pack(pady=2)

    # Sección: fuente de enlaces (CSV o Texto)
    frame_fuente = tk.LabelFrame(root, text="Fuente de enlaces")
    frame_fuente.pack(fill="both", padx=12, pady=8)

    # Radios de fuente
    radios_frame = tk.Frame(frame_fuente)
    radios_frame.pack(fill="x", pady=5)
    tk.Radiobutton(radios_frame, text="CSV", variable=fuente_var, value="CSV").pack(side="left", padx=5)
    tk.Radiobutton(radios_frame, text="Pegar texto", variable=fuente_var, value="TEXTO").pack(side="left", padx=5)

    # Selección CSV
    frame_csv = tk.Frame(frame_fuente)
    frame_csv.pack(fill="x", pady=5)
    def on_seleccionar_csv():
        file = seleccionar_csv()
        if file:
            csv_file_var.set(file)
    tk.Button(frame_csv, text="Seleccionar archivo CSV...", command=on_seleccionar_csv, width=30).pack(pady=5)
    tk.Label(frame_csv, textvariable=csv_file_var, wraplength=460, fg="blue").pack(pady=2)

    # Campo de texto para pegar URLs (una por línea)
    frame_texto = tk.Frame(frame_fuente)
    frame_texto.pack(fill="both", pady=5)
    tk.Label(frame_texto, text="Pega aquí los enlaces (uno por línea):").pack(anchor="w")
    texto_urls = tk.Text(frame_texto, height=8, wrap="word")
    texto_urls.pack(fill="both", padx=2, pady=4)

    # Mostrar/ocultar según fuente
    def actualizar_visibilidad_fuente(*args):
        if fuente_var.get() == "CSV":
            frame_csv.pack(fill="x", pady=5)
            frame_texto.pack_forget()
        else:
            frame_texto.pack(fill="both", pady=5)
            frame_csv.pack_forget()
    fuente_var.trace_add("write", actualizar_visibilidad_fuente)
    actualizar_visibilidad_fuente()

    # Sección: formato de salida
    frame_formato = tk.LabelFrame(root, text="Formato de salida")
    frame_formato.pack(fill="x", padx=12, pady=8)
    tk.Radiobutton(frame_formato, text="MP3 (audio)", variable=formato_var, value="MP3").pack(side="left", padx=8, pady=5)
    tk.Radiobutton(frame_formato, text="MP4 (video)", variable=formato_var, value="MP4").pack(side="left", padx=8, pady=5)

    # Botón descargar
    def on_descargar():
        carpeta = carpeta_var.get()
        if not carpeta or not os.path.isdir(carpeta):
            messagebox.showerror("Error", "Por favor, selecciona una carpeta válida de descarga.")
            return

        # Construir lista de URLs según fuente
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

        # Descargar
        ok, err, inval = descargar_desde_fuente(urls, carpeta, formato_var.get())

        # Mensaje final con opción de abrir carpeta
        msg = (
            f"Descarga finalizada.\n\n"
            f"Correctas: {ok}\n"
            f"Con error: {err}\n"
            f"Inválidas: {inval}\n\n"
            f"¿Quieres abrir la carpeta de descarga?"
        )
        abrir = messagebox.askyesno("Finalizado", msg)
        if abrir:
            abrir_carpeta(carpeta)

    tk.Button(root, text="Descargar", command=on_descargar, width=30, bg="green", fg="white").pack(pady=12)

    # Nota legal
    tk.Label(root, text="Usa este programa respetando los términos de YouTube y derechos de autor.", fg="gray").pack(pady=6)

    root.mainloop()

if __name__ == "__main__":
    main()
