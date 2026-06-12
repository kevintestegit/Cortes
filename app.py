import json
import os
import subprocess
import sys
import threading

try:
    import tkinter as tk
    from tkinter import filedialog, messagebox, scrolledtext, ttk
    TKINTER_AVAILABLE = True
except ModuleNotFoundError:
    tk = None
    filedialog = None
    messagebox = None
    scrolledtext = None
    ttk = None
    TKINTER_AVAILABLE = False

from src.platform_utils import default_parrot_dir, find_project_python, open_path


class ShortsCutterGUI:
    def __init__(self, root):
        self.root = root
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.root.title("Shorts Auto Cutter - Interface Interativa")
        self.root.geometry("820x740")
        self.root.configure(padx=15, pady=15)

        self.video_path = tk.StringVar()
        self.preset = tk.StringVar(value="funny")
        self.theme = tk.StringVar(value="funny")
        self.max_shorts = tk.IntVar(value=5)
        self.add_subtitles = tk.BooleanVar(value=True)
        self.use_llm_ranking = tk.BooleanVar(value=False)
        self.copy_to_drive = tk.BooleanVar(value=False)
        self.delete_local_after_drive = tk.BooleanVar(value=False)
        self.blur_watermark = tk.BooleanVar(value=False)
        self.use_cache = tk.BooleanVar(value=True)
        self.refresh_cache = tk.BooleanVar(value=False)
        self.drive_output_dir = tk.StringVar(value="")
        self.parrot_dir = tk.StringVar(value=default_parrot_dir(self.base_dir))

        self.create_widgets()

    def create_widgets(self):
        tk.Label(self.root, text="Shorts Auto Cutter", font=("Segoe UI", 16, "bold")).pack(pady=(0, 15))

        frame_input = tk.LabelFrame(self.root, text="1. Selecione o video", padx=10, pady=10, font=("Segoe UI", 10))
        frame_input.pack(fill=tk.X, pady=5)

        tk.Entry(frame_input, textvariable=self.video_path, width=66, state="readonly", font=("Segoe UI", 9)).pack(side=tk.LEFT, padx=(0, 10))
        tk.Button(frame_input, text="Procurar...", command=self.browse_file, cursor="hand2").pack(side=tk.LEFT)

        frame_opts = tk.LabelFrame(self.root, text="2. Configuracoes", padx=10, pady=10, font=("Segoe UI", 10))
        frame_opts.pack(fill=tk.X, pady=10)

        row1 = tk.Frame(frame_opts)
        row1.pack(fill=tk.X)
        tk.Label(row1, text="Preset:", font=("Segoe UI", 9)).pack(side=tk.LEFT)
        presets = ["funny", "fails", "animals", "football", "podcast", "curiosities"]
        ttk.Combobox(row1, textvariable=self.preset, values=presets, width=12, state="readonly").pack(side=tk.LEFT, padx=5)

        tk.Label(row1, text="Tema:", font=("Segoe UI", 9)).pack(side=tk.LEFT)
        temas = ["funny", "fails", "fishing", "animals", "money", "football", "podcast", "curiosities"]
        ttk.Combobox(row1, textvariable=self.theme, values=temas, width=15, state="readonly").pack(side=tk.LEFT, padx=5)

        tk.Label(row1, text="Maximo de Shorts:", font=("Segoe UI", 9)).pack(side=tk.LEFT, padx=(20, 0))
        tk.Spinbox(row1, from_=1, to=20, textvariable=self.max_shorts, width=5, font=("Segoe UI", 9)).pack(side=tk.LEFT, padx=5)

        tk.Checkbutton(row1, text="Legendas automaticas", variable=self.add_subtitles, font=("Segoe UI", 9)).pack(side=tk.LEFT, padx=(20, 0))

        row2 = tk.Frame(frame_opts)
        row2.pack(fill=tk.X, pady=(10, 0))
        tk.Checkbutton(row2, text="Ranking com IA", variable=self.use_llm_ranking, font=("Segoe UI", 9)).pack(side=tk.LEFT)
        tk.Checkbutton(row2, text="Enviar para Google Drive", variable=self.copy_to_drive, font=("Segoe UI", 9)).pack(side=tk.LEFT, padx=(20, 0))
        tk.Checkbutton(row2, text="Apagar copia local apos Drive", variable=self.delete_local_after_drive, font=("Segoe UI", 9)).pack(side=tk.LEFT, padx=(20, 0))

        row3 = tk.Frame(frame_opts)
        row3.pack(fill=tk.X, pady=(10, 0))
        tk.Checkbutton(row3, text="Borrar marca d'agua", variable=self.blur_watermark, font=("Segoe UI", 9)).pack(side=tk.LEFT)

        row4 = tk.Frame(frame_opts)
        row4.pack(fill=tk.X, pady=(10, 0))
        tk.Checkbutton(row4, text="Usar cache da analise", variable=self.use_cache, font=("Segoe UI", 9)).pack(side=tk.LEFT)
        tk.Checkbutton(row4, text="Reanalisar video", variable=self.refresh_cache, font=("Segoe UI", 9)).pack(side=tk.LEFT, padx=(20, 0))

        row5 = tk.Frame(frame_opts)
        row5.pack(fill=tk.X, pady=(10, 0))
        tk.Label(row5, text="Pasta papagaio:", font=("Segoe UI", 9)).pack(side=tk.LEFT)
        tk.Entry(row5, textvariable=self.parrot_dir, width=52, font=("Segoe UI", 9)).pack(side=tk.LEFT, padx=(5, 5))
        tk.Button(row5, text="Escolher...", command=self.browse_parrot_dir, cursor="hand2").pack(side=tk.LEFT)

        row6 = tk.Frame(frame_opts)
        row6.pack(fill=tk.X, pady=(10, 0))
        tk.Label(row6, text="Pasta Drive opcional:", font=("Segoe UI", 9)).pack(side=tk.LEFT)
        tk.Entry(row6, textvariable=self.drive_output_dir, width=52, font=("Segoe UI", 9)).pack(side=tk.LEFT, padx=(5, 5))
        tk.Button(row6, text="Escolher...", command=self.browse_drive_dir, cursor="hand2").pack(side=tk.LEFT)

        self.btn_run = tk.Button(
            self.root,
            text="GERAR PACOTE VIRAL",
            command=self.start_processing,
            bg="#28a745",
            fg="white",
            font=("Segoe UI", 12, "bold"),
            pady=8,
            cursor="hand2",
        )
        self.btn_run.pack(fill=tk.X, pady=15)

        frame_actions = tk.Frame(self.root)
        frame_actions.pack(fill=tk.X, pady=(0, 10))
        tk.Button(frame_actions, text="Abrir relatorio", command=self.open_last_report, cursor="hand2").pack(side=tk.LEFT)
        tk.Button(frame_actions, text="Abrir pasta de saida", command=self.open_output_dir, cursor="hand2").pack(side=tk.LEFT, padx=(8, 0))

        tk.Label(self.root, text="Console de Execucao:", font=("Segoe UI", 9, "bold")).pack(anchor=tk.W)
        self.log_area = scrolledtext.ScrolledText(
            self.root,
            height=13,
            state="disabled",
            bg="#1e1e1e",
            fg="#00ff00",
            font=("Consolas", 9),
        )
        self.log_area.pack(fill=tk.BOTH, expand=True, pady=(5, 0))

    def browse_file(self):
        filepath = filedialog.askopenfilename(
            title="Selecione o video",
            filetypes=(("Videos MP4", "*.mp4"), ("Todos os arquivos", "*.*")),
        )
        if filepath:
            self.video_path.set(filepath)

    def browse_drive_dir(self):
        directory = filedialog.askdirectory(title="Escolha a pasta do Google Drive")
        if directory:
            self.drive_output_dir.set(directory)

    def browse_parrot_dir(self):
        directory = filedialog.askdirectory(title="Escolha a pasta dos videos do papagaio")
        if directory:
            self.parrot_dir.set(directory)

    def log(self, message):
        self.log_area.config(state="normal")
        self.log_area.insert(tk.END, message)
        self.log_area.see(tk.END)
        self.log_area.config(state="disabled")

    def start_processing(self):
        if not self.video_path.get():
            messagebox.showwarning("Atencao", "Selecione um arquivo de video primeiro.")
            return

        self.btn_run.config(state=tk.DISABLED, text="GERANDO PACOTE...", bg="#6c757d")
        self.log_area.config(state="normal")
        self.log_area.delete(1.0, tk.END)
        self.log_area.config(state="disabled")

        thread = threading.Thread(target=self.run_script)
        thread.daemon = True
        thread.start()

    def _python_exe(self):
        return find_project_python(self.base_dir, current_python=sys.executable)

    def _last_report_path(self):
        last_run_path = os.path.join(self.base_dir, "output", "last_run.json")
        try:
            with open(last_run_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            report_path = data.get("report_path")
            if report_path and os.path.exists(report_path):
                return report_path
        except (OSError, json.JSONDecodeError):
            pass
        fallback = os.path.join(self.base_dir, "output", "reports", "index.html")
        return fallback if os.path.exists(fallback) else None

    def _last_output_dir(self):
        last_run_path = os.path.join(self.base_dir, "output", "last_run.json")
        try:
            with open(last_run_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            shorts_dir = data.get("local_shorts_dir")
            if shorts_dir and os.path.isdir(shorts_dir):
                return shorts_dir
        except (OSError, json.JSONDecodeError):
            pass
        fallback = os.path.join(self.base_dir, "output")
        return fallback if os.path.isdir(fallback) else self.base_dir

    def open_last_report(self):
        report_path = self._last_report_path()
        if not report_path:
            messagebox.showinfo("Relatorio", "Nenhum relatorio foi gerado ainda.")
            return
        open_path(report_path)

    def open_output_dir(self):
        open_path(self._last_output_dir())

    def run_script(self):
        cmd = [
            self._python_exe(),
            "-m",
            "src.main",
            "--input",
            self.video_path.get(),
            "--preset",
            self.preset.get(),
            "--theme",
            self.theme.get(),
            "--max-shorts",
            str(self.max_shorts.get()),
            "--add-subtitles",
            str(self.add_subtitles.get()).lower(),
            "--use-llm-ranking",
            str(self.use_llm_ranking.get()).lower(),
            "--copy-to-drive",
            str(self.copy_to_drive.get()).lower(),
            "--delete-local-after-drive",
            str(self.delete_local_after_drive.get()).lower(),
            "--blur-watermark",
            str(self.blur_watermark.get()).lower(),
            "--use-cache",
            str(self.use_cache.get()).lower(),
            "--refresh-cache",
            str(self.refresh_cache.get()).lower(),
            "--add-parrot",
            "true",
            "--parrot-dir",
            self.parrot_dir.get().strip() or default_parrot_dir(self.base_dir),
            "--add-hook",
            "true",
            "--generate-thumbnail",
            "true",
        ]
        if self.drive_output_dir.get().strip():
            cmd.extend(["--drive-output-dir", self.drive_output_dir.get().strip()])

        self.log(f"Iniciando processamento...\nArquivo: {self.video_path.get()}\n\n")

        try:
            creationflags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
            env = os.environ.copy()
            env["PYTHONIOENCODING"] = "utf-8"

            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
                bufsize=1,
                env=env,
                creationflags=creationflags,
                cwd=self.base_dir,
            )

            for line in process.stdout:
                self.root.after(0, self.log, line)

            process.wait()

            if process.returncode == 0:
                report_path = self._last_report_path()
                self.log("\nConcluido com sucesso.\n")
                self.root.after(
                    0,
                    lambda: messagebox.showinfo(
                        "Sucesso",
                        "Shorts gerados com sucesso. O relatorio foi aberto no final do processo.",
                    ),
                )
                if report_path:
                    open_path(report_path)
            else:
                self.log("\nProcesso terminou com erro.\n")
                self.root.after(
                    0,
                    lambda: messagebox.showerror(
                        "Erro",
                        "Ocorreu um erro durante o processamento. Verifique o console de execucao.",
                    ),
                )
        except Exception as exc:
            self.root.after(0, self.log, f"\nErro critico: {exc}\n")
        finally:
            self.root.after(0, self.reset_button)

    def reset_button(self):
        self.btn_run.config(state=tk.NORMAL, text="GERAR PACOTE VIRAL", bg="#28a745")


if __name__ == "__main__":
    if not TKINTER_AVAILABLE:
        print(
            "Tkinter nao esta instalado. No Ubuntu/Debian, instale com: "
            "sudo apt install python3-tk"
        )
        sys.exit(1)

    root = tk.Tk()
    try:
        root.iconbitmap(default="")
    except Exception:
        pass
    app = ShortsCutterGUI(root)
    root.mainloop()
