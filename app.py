import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk
import subprocess
import threading
import os
import sys

class ShortsCutterGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Shorts Auto Cutter - Interface Interativa")
        self.root.geometry("750x650")  # Made wider for thumbnail
        self.root.configure(padx=15, pady=15)
        
        # Variáveis da Interface
        self.video_path = tk.StringVar()
        self.theme = tk.StringVar(value="funny")
        self.max_shorts = tk.IntVar(value=5)
        self.add_subtitles = tk.BooleanVar(value=False)
        self.thumbnail_image = None  # To keep reference to prevent garbage collection
        
        self.create_widgets()
        
    def create_widgets(self):
        # Título
        tk.Label(self.root, text="✂️ Shorts Auto Cutter", font=("Segoe UI", 16, "bold")).pack(pady=(0, 15))

        # --- Frame de Entrada de Arquivo ---
        frame_input = tk.LabelFrame(self.root, text="1. Selecione o Vídeo", padx=10, pady=10, font=("Segoe UI", 10))
        frame_input.pack(fill=tk.X, pady=5)
        
        tk.Entry(frame_input, textvariable=self.video_path, width=60, state='readonly', font=("Segoe UI", 9)).pack(side=tk.LEFT, padx=(0, 10))
        tk.Button(frame_input, text="📂 Procurar...", command=self.browse_file, cursor="hand2").pack(side=tk.LEFT)
        
        # --- Frame de Configurações ---
        frame_opts = tk.LabelFrame(self.root, text="2. Configurações", padx=10, pady=10, font=("Segoe UI", 10))
        frame_opts.pack(fill=tk.X, pady=10)
        
        tk.Label(frame_opts, text="Tema (Títulos):", font=("Segoe UI", 9)).pack(side=tk.LEFT)
        temas = ["funny", "fails", "fishing", "animals", "money"]
        cb_tema = ttk.Combobox(frame_opts, textvariable=self.theme, values=temas, width=15, state="readonly")
        cb_tema.pack(side=tk.LEFT, padx=5)
        
        tk.Label(frame_opts, text="Máximo de Shorts:", font=("Segoe UI", 9)).pack(side=tk.LEFT, padx=(20, 0))
        tk.Spinbox(frame_opts, from_=1, to=20, textvariable=self.max_shorts, width=5, font=("Segoe UI", 9)).pack(side=tk.LEFT, padx=5)
        
        tk.Checkbutton(frame_opts, text="Legendas automáticas", variable=self.add_subtitles, font=("Segoe UI", 9)).pack(side=tk.LEFT, padx=(20, 0))
        
        # --- Botão Iniciar ---
        self.btn_run = tk.Button(
            self.root, text="🚀 GERAR SHORTS", command=self.start_processing, 
            bg="#28a745", fg="white", font=("Segoe UI", 12, "bold"), pady=8, cursor="hand2"
        )
        self.btn_run.pack(fill=tk.X, pady=15)
        
        # --- Log Console ---
        tk.Label(self.root, text="Console de Execução:", font=("Segoe UI", 9, "bold")).pack(anchor=tk.W)
        self.log_area = scrolledtext.ScrolledText(self.root, height=12, state='disabled', bg="#1e1e1e", fg="#00ff00", font=("Consolas", 9))
        self.log_area.pack(fill=tk.BOTH, expand=True, pady=(5, 0))

    def browse_file(self):
        filepath = filedialog.askopenfilename(
            title="Selecione o Vídeo",
            filetypes=(("Vídeos MP4", "*.mp4"), ("Todos os arquivos", "*.*"))
        )
        if filepath:
            self.video_path.set(filepath)
            
    def log(self, message):
        self.log_area.config(state='normal')
        self.log_area.insert(tk.END, message)
        self.log_area.see(tk.END)
        self.log_area.config(state='disabled')
        
    def start_processing(self):
        if not self.video_path.get():
            messagebox.showwarning("Atenção", "Por favor, selecione um arquivo de vídeo primeiro!")
            return
            
        self.btn_run.config(state=tk.DISABLED, text="⏳ PROCESSANDO...", bg="#6c757d")
        self.log_area.config(state='normal')
        self.log_area.delete(1.0, tk.END)
        self.log_area.config(state='disabled')
        
        # Roda em uma thread separada para não congelar a janela visual
        thread = threading.Thread(target=self.run_script)
        thread.daemon = True
        thread.start()
        
    def run_script(self):
        python_exe = sys.executable
        # Se existir o ambiente virtual na pasta, prioriza ele
        venv_python = os.path.join(".venv", "Scripts", "python.exe")
        if os.path.exists(venv_python):
            python_exe = venv_python
            
        cmd = [
            python_exe, "-m", "src.main",
            "--input", self.video_path.get(),
            "--theme", self.theme.get(),
            "--max-shorts", str(self.max_shorts.get()),
            "--add-subtitles", str(self.add_subtitles.get()).lower()
        ]
        
        self.log(f"Iniciando processamento...\nArquivo: {self.video_path.get()}\n\n")
        
        try:
            # Cria flags para não abrir a janela preta do terminal do windows
            creationflags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            env = os.environ.copy()
            env["PYTHONIOENCODING"] = "utf-8"
            
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding='utf-8',
                errors='replace',
                bufsize=1,
                env=env,
                creationflags=creationflags
            )
            
            for line in process.stdout:
                # O root.after garante que a atualização da interface ocorra na Thread Principal
                self.root.after(0, self.log, line)
                
            process.wait()
            
            if process.returncode == 0:
                self.log("\n✅ Concluído com Sucesso!\n")
                self.root.after(0, lambda: messagebox.showinfo("Sucesso", "Shorts gerados com sucesso!\nVerifique a pasta 'output/shorts'."))
                
                # Opcional: abre a pasta automaticamente
                try:
                    os.startfile(os.path.abspath("output/reports/index.html"))
                except:
                    pass
            else:
                self.log("\n❌ Processo terminou com erro.\n")
                self.root.after(0, lambda: messagebox.showerror("Erro", "Ocorreu um erro durante o processamento. Verifique o console de execução."))
                
        except Exception as e:
            self.root.after(0, self.log, f"\nErro Crítico: {str(e)}\n")
            
        finally:
            self.root.after(0, self.reset_button)

    def reset_button(self):
        self.btn_run.config(state=tk.NORMAL, text="🚀 GERAR SHORTS", bg="#28a745")

if __name__ == "__main__":
    root = tk.Tk()
    # Tenta usar o ícone padrão do Windows para não ficar a "pena" do Tkinter
    try:
        root.iconbitmap(default='')
    except:
        pass
    app = ShortsCutterGUI(root)
    root.mainloop()
