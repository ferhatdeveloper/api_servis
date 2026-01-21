import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
import sys
import platform
import socket
import subprocess
import json
import threading
import psutil
import requests
import time

def show_error_and_wait(type, value, traceback):
    import traceback as tb
    err_msg = "".join(tb.format_exception(type, value, traceback))
    print(err_msg)
    try:
        from tkinter import messagebox
        messagebox.showerror("Kritik Hata", f"Uygulama başlatılırken bir hata oluştu:\n\n{value}\n\nDetaylar konsolda.")
    except: pass
    input("\nProgram hatadan dolayı durdu. Kapatmak için ENTER'a basın...")

sys.excepthook = show_error_and_wait

try:
    import psycopg2
except ImportError:
    psycopg2 = None

try:
    import pymssql
except ImportError:
    pymssql = None

class SetupWizard(tk.Tk):
    def __init__(self):
        super().__init__()
        
        # Hide Console if on Windows
        try:
            import ctypes
            import platform
            if platform.system() == "Windows":
                # Check if we are hosted in a console
                kernel32 = ctypes.WinDLL('kernel32')
                user32 = ctypes.WinDLL('user32')
                hwnd = kernel32.GetConsoleWindow()
                if hwnd:
                    # Check if this console was spawned specifically for us (heuristic)
                    # Or just force hide as requested.
                    # SW_HIDE = 0
                    user32.ShowWindow(hwnd, 0)
        except:
            pass
            
        # Windows High-DPI support
        try:
            from ctypes import windll
            windll.shcore.SetProcessDpiAwareness(1)
        except:
            pass

        self.title("EXFIN OPS API System Setup Wizard")
        
        # Center the window
        w, h = 1000, 750
        ws = self.winfo_screenwidth()
        hs = self.winfo_screenheight()
        x = (ws/2) - (w/2)
        y = (hs/2) - (h/2)
        self.geometry('%dx%d+%d+%d' % (w, h, x, y))
        
        self.configure(bg="#f8fafc")
        
        self.current_step = 0
        self.steps = []
        self.setup_mode = None  # wizard or local
        
        # Load existing config if possible
        self.config_data = self.load_existing_config()
        
        self.configure_styles()
        self.setup_ui()
        self.show_step(0)

    def configure_styles(self):
        style = ttk.Style()
        try:
             style.theme_use('clam')
        except: pass
        
        # Colors (Slate Palette)
        BG_COLOR = "#f8fafc"
        PRIMARY = "#1e40af"
        SECONDARY = "#64748b"
        TEXT = "#0f172a"
        WHITE = "#ffffff"
        
        # General Defaults
        style.configure(".", background=BG_COLOR, foreground=TEXT, font=("Segoe UI", 10))
        
        # TFrame
        style.configure("TFrame", background=BG_COLOR)
        style.configure("Card.TFrame", background=WHITE, relief="solid", borderwidth=1)
        
        # TButton
        style.configure("TButton", 
                        font=("Segoe UI", 9, "bold"), 
                        padding=10, 
                        background=PRIMARY, 
                        foreground=WHITE,
                        borderwidth=0)
        style.map("TButton",
                  background=[('active', '#1e3a8a'), ('disabled', '#cbd5e1')])
                  
        # TEntry
        style.configure("TEntry", padding=5, relief="flat", fieldbackground=WHITE)
        
        # TLabel
        style.configure("TLabel", background=BG_COLOR, foreground=TEXT)
        style.configure("Header.TLabel", font=("Segoe UI", 16, "bold"), foreground=PRIMARY, background=BG_COLOR)
        style.configure("SubHeader.TLabel", font=("Segoe UI", 11, "bold"), foreground=SECONDARY, background=BG_COLOR)
        style.configure("CardTitle.TLabel", font=("Segoe UI", 12, "bold"), background=WHITE, foreground=TEXT)
        
        # Treeview
        style.configure("Treeview", rowheight=25, font=("Segoe UI", 9))
        style.configure("Treeview.Heading", font=("Segoe UI", 9, "bold"))

    def load_existing_config(self):
        default_config = {
            "api_path": "C:\\ExfinApi",
            "pg_host": "localhost",
            "pg_port": "5432",
            "pg_user": "postgres",
            "pg_pass": "",
            "pg_db": "EXFINOPS",
            "ms_host": ".",
            "ms_user": "sa",
            "ms_pass": "",
            "ms_db": "LOGODB",
            "ms_firma": "001",
            "ms_donem": "01",
            "api_port": "8000"
        }
        
        if os.path.exists("db_config.json"):
            try:
                with open("db_config.json", "r", encoding="utf-8") as f:
                    data = json.load(f)
                    # Extract values from the json structure we saw earlier
                    for item in data:
                        if item.get("Type") == "PostgreSQL":
                            default_config["pg_host"] = item.get("Server", "localhost")
                            default_config["pg_user"] = item.get("Username", "postgres")
                            default_config["pg_pass"] = item.get("Password", "")
                            default_config["pg_db"] = item.get("Database", "EXFINOPS")
                            default_config["pg_port"] = str(item.get("Port", 5432))
                        elif item.get("Type") == "MSSQL" and item.get("Name") == "LOGO_Database":
                            default_config["ms_host"] = item.get("Server", ".")
                            default_config["ms_user"] = item.get("Username", "sa")
                            default_config["ms_pass"] = item.get("Password", "")
                            default_config["ms_db"] = item.get("Database", "LOGODB")
                            default_config["ms_firma"] = item.get("FirmaNo", "001")
                            default_config["ms_donem"] = item.get("DonemNo", "01")
                            default_config["ms_conn_type"] = item.get("ConnectionType", "Direct Database")
                            default_config["ms_conn_type"] = item.get("ConnectionType", "Direct Database")
                            default_config["firma"] = item.get("FirmaNo", "001")
                            default_config["donem"] = item.get("DonemNo", "01")
            except:
                pass
        return default_config

    def setup_ui(self):
        # 1. Header (TOP)
        header = tk.Frame(self, bg="#1e40af", height=100)
        header.pack(fill="x", side="top")
        
        title_lbl = tk.Label(header, text="EXFIN OPS API SETUP WIZARD", fg="white", bg="#1e40af", font=("Segoe UI", 18, "bold"))
        title_lbl.pack(pady=(20, 5))
        
        version_lbl = tk.Label(header, text="v5.2 Enterprise Deployment", fg="#93c5fd", bg="#1e40af", font=("Segoe UI", 10))
        version_lbl.pack(pady=(0, 20))

        # 2. Footer (BOTTOM)
        footer = tk.Frame(self, bg="#f8fafc", height=80)
        footer.pack(fill="x", side="bottom")

        style = ttk.Style()
        style.configure("Footer.TButton", font=("Segoe UI", 10), padding=5)

        self.btn_back = ttk.Button(footer, text="Geri", command=self.prev_step, style="Footer.TButton")
        self.btn_back.pack(side="left", padx=40, pady=20)

        self.btn_next = ttk.Button(footer, text="İleri", command=self.next_step, style="Footer.TButton")
        self.btn_next.pack(side="right", padx=40, pady=20)

        # 3. Progress (BELOW HEADER)
        self.progress_frame = tk.Frame(self, bg="#f8fafc")
        self.progress_frame.pack(fill="x", side="top", pady=10)
        
        # 4. Main Content (REMAINING SPACE)
        self.container = tk.Frame(self, bg="white", highlightbackground="#e2e8f0", highlightthickness=1)
        self.container.pack(fill="both", expand=True, padx=40, pady=10)

        # Define Steps
        self.steps = [
            self.create_step_welcome,
            self.create_step_requirements,
            self.create_step_dependencies,
            self.create_step_path_network,
            self.create_step_db_config,
            self.create_step_data_transfer,
            self.create_step_security, # NEW STEP
            self.create_step_service_install,
            self.create_step_finish
        ]

    def show_step(self, step_index):
        for widget in self.container.winfo_children():
            widget.destroy()
        
        self.current_step = step_index
        self.steps[step_index]()
        
        self.btn_back.config(state="normal" if step_index > 0 else "disabled")
        
        # Disable Next for Welcome step if mode not selected
        next_state = "normal"
        if step_index == 0 and self.setup_mode is None:
            next_state = "disabled"
            
        if step_index == len(self.steps) - 1:
            self.btn_next.config(text="Tamamla", command=self.finish_setup, state=next_state)
        else:
            self.btn_next.config(text="İleri", command=self.next_step, state=next_state)

    def next_step(self):
        # Save data from current step
        if self.current_step == 3: # Path Step
            if hasattr(self, 'ent_path') and self.ent_path.winfo_exists():
                self.config_data["api_path"] = self.ent_path.get()
            if hasattr(self, 'ent_port') and self.ent_port.winfo_exists():
                self.config_data["api_port"] = self.ent_port.get()
        
        if self.current_step == 4: # DB Config Step
            # Save all entries from DB step
            for key, ent in self.ui_entries.items():
                if ent.winfo_exists():
                    self.config_data[key] = ent.get()
        
        if self.current_step < len(self.steps) - 1:
            self.show_step(self.current_step + 1)

    def prev_step(self):
        if self.current_step > 0:
            self.show_step(self.current_step - 1)

    # --- STEP UI METHODS ---

    def create_step_welcome(self):
        content = tk.Frame(self.container, bg="white")
        content.pack(fill="both", expand=True, padx=20, pady=20)
        
        tk.Label(content, text="EXFIN OPS Platform", font=("Segoe UI", 16, "bold"), bg="white", fg="#1e293b").pack(anchor="w")
        tk.Label(content, text="Yükleme ve Yapılandırma Seçenekleri", font=("Segoe UI", 12), bg="white", fg="#64748b").pack(anchor="w", pady=(0, 20))
        
        # Mode Selection Buttons
        frame_modes = tk.Frame(content, bg="white")
        frame_modes.pack(fill="x", pady=10)

        # Style for big buttons
        style = ttk.Style()
        style.configure("Mode.TButton", font=("Segoe UI", 11, "bold"), padding=10)

        self.btn_mode_wizard = ttk.Button(frame_modes, text="🚀  Sistemi Kur / Güncelle (Full Wizard)", 
                             style="Mode.TButton", command=lambda: self.select_mode("wizard"))
        self.btn_mode_wizard.pack(fill="x", pady=5)

        self.btn_mode_local = ttk.Button(frame_modes, text="📂  Bulunulan Dizine Dosyaları Yükle (Local Sync)", 
                              style="Mode.TButton", command=lambda: self.select_mode("local"))
        self.btn_mode_local.pack(fill="x", pady=5)

        # Info Box
        box = tk.LabelFrame(content, text=" Bilgi ", bg="white", font=("Segoe UI", 10, "bold"), fg="#1e40af")
        box.pack(fill="x", pady=20)
        self.lbl_welcome_info = tk.Label(box, text="Lütfen yukarıdaki seçeneklerden birini seçerek devam ediniz.", 
                  bg="white", justify="left", wraplength=550, padx=10, pady=10)
        self.lbl_welcome_info.pack(anchor="w")

    def select_mode(self, mode):
        self.setup_mode = mode
        if mode == "wizard":
            info_text = "Sistem Uzmanı rehberliğinde tüm adımlar (Gereksinimler, Veritabanı, Servis) yapılandırılacaktır."
        else:
            # When in local mode, default the path to parent of scripts folder (project root)
            self.config_data["api_path"] = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
            info_text = f"Kodlar mevcut dizine ({self.config_data['api_path']}) indirilecek/güncellenecektir."
        
        self.lbl_welcome_info.config(text=info_text)
        self.btn_next.config(state="normal")

    def create_step_requirements(self):
        content = tk.Frame(self.container, bg="white", padx=20, pady=20)
        content.pack(fill="both", expand=True)
        
        tk.Label(content, text="Sistem Gereksinimleri ve Port Analizi", font=("Segoe UI", 14, "bold"), bg="white").pack(anchor="w")
        
        self.txt_log = tk.Text(content, bg="#0f172a", fg="#10b981", font=("Consolas", 10), height=15)
        self.txt_log.pack(fill="both", expand=True, pady=10)
        
        btn_run = ttk.Button(content, text="Kontrolleri Başlat", command=self.run_checks)
        btn_run.pack(pady=5)

    def run_checks(self):
        self.txt_log.delete("1.0", tk.END)
        self.log("Sistem analizi başlatılıyor...")
        
        # OS
        self.log(f"İşletim Sistemi: {platform.system()} {platform.release()}")
        
        # RAM
        ram = psutil.virtual_memory().total / (1024**3)
        status = "OK" if ram >= 4 else "YETERSİZ (Min 4GB)"
        self.log(f"Bellek (RAM): {ram:.2f} GB - {status}")
        
        # External Connectivity & Port 8000
        
        # CPU Info
        cpu = platform.processor()
        self.log(f"İşlemci: {cpu}")

    def log(self, msg):
        if hasattr(self, 'txt_log') and self.txt_log.winfo_exists():
            self.txt_log.insert(tk.END, f"> {msg}\n")
            self.txt_log.see(tk.END)

    def safe_str(self, e):
        """Safely convert exception to string, handling Unicode issues."""
        try:
            return str(e)
        except UnicodeDecodeError:
            try:
                if hasattr(e, 'args') and e.args:
                    msg = e.args[0]
                    if isinstance(msg, bytes):
                        return msg.decode('cp1254', errors='replace')
                    return str(msg)
                return repr(e)
            except:
                return "Karakter Kodlama Hatası (Türkçe karakter sorunu)"
        except Exception:
            try:
                return repr(e)
            except:
                return "Bilinmeyen Hata"

    def create_step_dependencies(self):
        content = tk.Frame(self.container, bg="white", padx=20, pady=20)
        content.pack(fill="both", expand=True)
        
        tk.Label(content, text="Bağımlılık Kontrolü", font=("Segoe UI", 14, "bold"), bg="white").pack(anchor="w")
        
        self.dep_list = tk.Frame(content, bg="white")
        self.dep_list.pack(fill="x", pady=20)
        
        self.add_dep_row("Git SCM", cmd="git --version")
        self.add_dep_row("PostgreSQL 15+", check_func=self.check_postgres_version)
        self.add_dep_row("Python 3.10+", cmd="python --version")

    def add_dep_row(self, name, cmd=None, check_func=None):
        row = tk.Frame(self.dep_list, bg="white", pady=5)
        row.pack(fill="x")
        
        tk.Label(row, text=name, bg="white", width=20, anchor="w", font=("Segoe UI", 10)).pack(side="left")
        
        status_lbl = tk.Label(row, text="Kontrol ediliyor...", bg="white", width=25, anchor="w")
        status_lbl.pack(side="left")
        
        def check():
            if check_func:
                success, text = check_func()
                bg_color = "green" if success else "red"
                status_lbl.after(0, lambda: status_lbl.config(text=text, fg=bg_color))
            else:
                try:
                    res = subprocess.run(cmd, shell=True, capture_output=True)
                    if res.returncode == 0:
                        status_lbl.after(0, lambda: status_lbl.config(text="KURULU ✅", fg="green"))
                    else:
                        status_lbl.after(0, lambda: status_lbl.config(text="EKSİK ❌", fg="red"))
                except:
                    status_lbl.after(0, lambda: status_lbl.config(text="EKSİK ❌", fg="red"))
        
        threading.Thread(target=check, daemon=True).start()

    def check_postgres_version(self):
        # 1. Try psql --version
        try:
            res = subprocess.run("psql --version", shell=True, capture_output=True, text=True)
            if res.returncode == 0:
                # Output: 'psql (PostgreSQL) 16.1'
                out = res.stdout.strip()
                import re
                match = re.search(r"(\d+)\.(\d+)", out)
                if match:
                    major = int(match.group(1))
                    if major >= 15:
                        return True, f"KURULU (v{major}) ✅"
                    else:
                        return False, f"ESKİ SÜRÜM (v{major}) ⚠️"
        except: pass
        
        # 2. Fallback: Check Services for common versions
        for v in [17, 16, 15]:
            try:
                cmd = f"sc query postgresql-x64-{v}"
                res = subprocess.run(cmd, shell=True, capture_output=True)
                if res.returncode == 0:
                    return True, f"SERVİS (v{v}) ✅"
            except: pass
            
        return False, "BULUNAMADI (Min 15) ❌"

    def create_step_path_network(self):
        content = tk.Frame(self.container, bg="white", padx=20, pady=20)
        content.pack(fill="both", expand=True)
        
        tk.Label(content, text="Uygulama Yolu ve Güvenlik Duvarı", font=("Segoe UI", 14, "bold"), bg="white").pack(anchor="w")
        
        tk.Label(content, text="API Kurulum Dizini:", bg="white").pack(anchor="w", pady=(20, 5))
        f_path = tk.Frame(content, bg="white")
        f_path.pack(fill="x")
        self.ent_path = ttk.Entry(f_path)
        self.ent_path.insert(0, self.config_data["api_path"])
        self.ent_path.pack(side="left", fill="x", expand=True)
        ttk.Button(f_path, text="Gözat", command=self.browse).pack(side="right", padx=5)
        
        tk.Label(content, text="Ağ Erişimi ve Port:", bg="white").pack(anchor="w", pady=(20, 5))
        f_port = tk.Frame(content, bg="white")
        f_port.pack(fill="x")
        tk.Label(f_port, text="API Portu:", bg="white", width=12, anchor="w").pack(side="left")
        self.ent_port = ttk.Entry(f_port, width=10)
        self.ent_port.insert(0, self.config_data.get("api_port", "8000"))
        self.ent_port.pack(side="left")
        tk.Label(f_port, text="(Dış erişim için bu portu Firewall'da açmanız gerekir)", bg="white", fg="grey", font=("Segoe UI", 8)).pack(side="left", padx=10)

        ttk.Button(content, text="Seçili Port İçin Güvenlik Duvarı İzni Oluştur", command=self.fix_firewall).pack(anchor="w", pady=(5, 10))

        # GitHub Sync Section
        tk.Label(content, text="Kod Güncelleme (GitHub):", bg="white", font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(10, 5))
        self.btn_sync = ttk.Button(content, text="Kodları GitHub'dan İndir / Güncelle", command=self.run_git_sync)
        self.btn_sync.pack(anchor="w", pady=5)

        self.git_log = tk.Text(content, bg="#1e293b", fg="#f1f5f9", font=("Consolas", 9), height=8)
        self.git_log.pack(fill="both", expand=True, pady=5)

    def browse(self):
        p = filedialog.askdirectory()
        if p:
            self.ent_path.delete(0, tk.END)
            self.ent_path.insert(0, p)
            self.config_data["api_path"] = p

    def fix_firewall(self):
        port = self.ent_port.get() or "8000"
        cmd = f'netsh advfirewall firewall add rule name="EXFIN_API_{port}" dir=in action=allow protocol=TCP localport={port}'
        subprocess.run(cmd, shell=True)
        messagebox.showinfo("Bilgi", f"Port {port} için güvenlik duvarı kuralı oluşturuldu.")

    def run_git_sync(self):
        target_dir = self.ent_path.get()
        if not target_dir:
            messagebox.showwarning("Uyarı", "Lütfen önce bir dizin seçin.")
            return

        def run():
            self.btn_sync.config(state="disabled")
            self.git_log.delete("1.0", tk.END)
            self.append_git_log("> GitHub senkronizasyonu başlatılıyor...\n")
            
            repo_url = "https://github.com/ferhatdeveloper/api_servis.git"
            
            try:
                if not os.path.exists(target_dir):
                    os.makedirs(target_dir)

                # 1. Check if it's a git repo
                git_dir = os.path.join(target_dir, ".git")
                if not os.path.exists(git_dir):
                    self.append_git_log(f"> '{target_dir}' bir Git deposu değil. Başlatılıyor...\n")
                    self.run_cmd("git init", target_dir)
                    self.run_cmd(f"git remote add origin {repo_url}", target_dir)
                else:
                    # Update remote URL just in case
                    self.run_cmd(f"git remote set-url origin {repo_url}", target_dir)

                # 2. Fetch and Reset
                self.append_git_log("> Son değişiklikler indiriliyor (fetch)...\n")
                self.run_cmd("git fetch origin main", target_dir)
                
                self.append_git_log("> Yerel dosyalar GitHub sürümüyle eşitleniyor (hard reset)...\n")
                self.run_cmd("git reset --hard origin/main", target_dir)
                
                self.append_git_log("\n> [BAŞARILI] Kodlar güncellendi! ✅\n")
                messagebox.showinfo("Başarılı", "Kodlar başarıyla indirildi / güncellendi.")
            except Exception as e:
                self.append_git_log(f"\n> [HATA] Senkronizasyon başarısız: {self.safe_str(e)}\n")
            finally:
                self.btn_sync.config(state="normal")

        threading.Thread(target=run).start()

    def run_cmd(self, cmd, cwd):
        try:
            # Use shell=True for Windows command strings
            process = subprocess.Popen(
                cmd, shell=True, cwd=cwd,
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT
            )
            
            # Read output line by line
            while True:
                line = process.stdout.readline()
                if not line:
                    break
                # Try to decode with system locale if utf-8 fails
                try:
                    text = line.decode('utf-8')
                except UnicodeDecodeError:
                    text = line.decode('cp1254', errors='replace')
                
                self.append_git_log(text)
            
            process.wait()
            if process.returncode != 0:
                raise Exception(f"Komut hata ile sonlandı (Exit Code: {process.returncode})")
        except Exception as e:
            self.append_git_log(f"CMD HATASI: {self.safe_str(e)}\n")
            raise

    def append_git_log(self, text):
        # Thread-safe UI update
        if hasattr(self, 'git_log') and self.git_log.winfo_exists():
            self.git_log.insert(tk.END, text)
            self.git_log.see(tk.END)

    def create_step_db_config(self):
        content = tk.Frame(self.container, bg="white", padx=20, pady=10)
        content.pack(fill="both", expand=True)
        
        tk.Label(content, text="Veritabanı Yapılandırması", font=("Segoe UI", 14, "bold"), bg="white").pack(anchor="w")
        
        # Main Container for Side-by-Side
        main_frame = tk.Frame(content, bg="white")
        main_frame.pack(fill="both", expand=True, pady=10)
        
        # PostgreSQL Frame (Left)
        f_pg = tk.LabelFrame(main_frame, text=" 1. EXFINOPS (PostgreSQL) ", bg="white", fg="#1e40af", font=("Segoe UI", 11, "bold"), padx=15, pady=15)
        f_pg.pack(side="left", fill="both", expand=True, padx=(0, 10))
        self.render_db_inputs(f_pg, "pg")
        
        # MSSQL Frame (Right)
        f_ms = tk.LabelFrame(main_frame, text=" 2. LOGO ERP (MSSQL) ", bg="white", fg="#ea580c", font=("Segoe UI", 11, "bold"), padx=15, pady=15)
        f_ms.pack(side="right", fill="both", expand=True, padx=(10, 0))
        self.render_db_inputs(f_ms, "ms")

    def render_db_inputs(self, parent, prefix):
        self.ui_entries = getattr(self, "ui_entries", {})
        
        # Connection Type for Logo
        if prefix == "ms":
            tk.Label(parent, text="Bağlantı Tipi:", bg="white", width=12, anchor="w").grid(row=0, column=0, pady=5)
            conn_type = ttk.Combobox(parent, values=["Direct Database", "Logo Objects (Unity)"], state="readonly")
            saved_type = self.config_data.get("ms_conn_type", "Direct Database")
            conn_type.set(saved_type)
            conn_type.grid(row=0, column=1, sticky="ew", pady=5)
            self.ui_entries["ms_conn_type"] = conn_type
            row_offset = 1
        else:
            row_offset = 0

        labels = [
            ("Sunucu", "host"), 
            ("Port", "port"),
            ("Veritabanı", "db"), 
            ("Kullanıcı", "user"), 
            ("Şifre", "pass")
        ]
        if prefix == "ms":
            # Container for Firma/Dönem that starts HIDDEN
            self.ms_meta_frame = tk.Frame(parent, bg="white")
            # Grid at row 6 to be BELOW the test button at row 5
            self.ms_meta_frame.grid(row=6+row_offset, column=0, columnspan=2, sticky="ew")
            self.ms_meta_frame.grid_remove() # Hide initially
            
            # Sub-labels for Meta
            meta_labels = [("Firma No", "firma"), ("Dönem No", "donem")]
            for mi, (mtxt, mkey) in enumerate(meta_labels):
                tk.Label(self.ms_meta_frame, text=mtxt+":", bg="white", width=12, anchor="w").grid(row=mi, column=0, pady=5)
                ent = ttk.Combobox(self.ms_meta_frame, state="readonly")
                if mkey == "firma":
                    ent.bind("<<ComboboxSelected>>", lambda e: self.update_donem_combo())
                
                config_key = f"ms_{mkey}"
                val = self.config_data.get(config_key, "001" if mkey == "firma" else "01")
                ent.set(val)
                ent.grid(row=mi, column=1, sticky="ew", pady=5)
                self.ui_entries[config_key] = ent
            self.ms_meta_frame.columnconfigure(1, weight=1)
            
            # Remove from main labels list
            pass
        
        for i, (txt, key) in enumerate(labels):
            tk.Label(parent, text=txt+":", bg="white", width=12, anchor="w").grid(row=i+row_offset, column=0, pady=5)
            
            is_pass = (key == "pass")
            if key in ["firma", "donem"] and prefix == "ms":
                ent = ttk.Combobox(parent, state="readonly")
                if key == "firma":
                    ent.bind("<<ComboboxSelected>>", lambda e: self.update_donem_combo())
            else:
                ent = ttk.Entry(parent, show="*" if is_pass else "")
            
            # Get value from config_data
            config_key = f"{prefix}_{key}"
            val = self.config_data.get(config_key, "5432" if key == "port" and prefix == "pg" else "1433" if key == "port" and prefix == "ms" else "")
            
            if isinstance(ent, ttk.Combobox):
                ent.set(val)
            else:
                ent.insert(0, val)
            ent.grid(row=i+row_offset, column=1, sticky="ew", pady=5)
            self.ui_entries[config_key] = ent
        
        # Backup Folder Selection (Only for Postgres for now or global)
        if prefix == "pg":
             tk.Label(parent, text="Yedekleme Klasörü:", bg="white", width=15, anchor="w").grid(row=len(labels)+row_offset, column=0, pady=5)
             
             f_bkp = tk.Frame(parent, bg="white")
             f_bkp.grid(row=len(labels)+row_offset, column=1, sticky="ew", pady=5)
             
             ent_bkp = ttk.Entry(f_bkp)
             ent_bkp.pack(side="left", fill="x", expand=True)
             
             default_bkp = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "backups")
             saved_bkp = self.config_data.get("backup_dir", default_bkp)
             ent_bkp.insert(0, saved_bkp)
             self.ui_entries["backup_dir"] = ent_bkp
             
             def browse_bkp():
                 d = filedialog.askdirectory()
                 if d:
                     ent_bkp.delete(0, tk.END)
                     ent_bkp.insert(0, d)
             
             ttk.Button(f_bkp, text="...", width=3, command=browse_bkp).pack(side="left", padx=(5,0))
             
             # Backup Frequency
             tk.Label(parent, text="Yedekleme Sıklığı:", bg="white", width=15, anchor="w").grid(row=len(labels)+row_offset+1, column=0, pady=5)
             
             # Frame for Frequency options
             f_freq = tk.Frame(parent, bg="white")
             f_freq.grid(row=len(labels)+row_offset+1, column=1, sticky="ew", pady=5)
             
             chk_freq = ttk.Combobox(f_freq, values=["Kapalı", "Saatlik", "Günlük", "Haftalık"], state="readonly")
             saved_interval = self.config_data.get("backup_interval_ui", "Kapalı")
             chk_freq.set(saved_interval)
             chk_freq.pack(side="left", fill="x", expand=True)
             self.ui_entries["backup_interval_ui"] = chk_freq
             
             # Dynamic Options Frame (Time & Days)
             self.f_backup_opts = tk.Frame(parent, bg="white")
             self.f_backup_opts.grid(row=len(labels)+row_offset+2, column=1, sticky="ew")
             
             # Hourly Interval Selection
             self.f_hours = tk.Frame(self.f_backup_opts, bg="white")
             tk.Label(self.f_hours, text="Aralık (Saat):", bg="white").pack(side="left")
             self.ent_backup_hours = ttk.Entry(self.f_hours, width=5)
             self.ent_backup_hours.insert(0, self.config_data.get("backup_hours", "1"))
             self.ent_backup_hours.pack(side="left")
             self.ui_entries["backup_hours"] = self.ent_backup_hours

             # Time Selection (Daily/Weekly)
             self.f_time = tk.Frame(self.f_backup_opts, bg="white")
             tk.Label(self.f_time, text="Saat:", bg="white", width=5).pack(side="left")
             self.ent_backup_time = ttk.Entry(self.f_time, width=8)
             self.ent_backup_time.insert(0, self.config_data.get("backup_time", "23:00"))
             self.ent_backup_time.pack(side="left")
             self.ui_entries["backup_time"] = self.ent_backup_time
             
             # Days Selection (Weekly)
             self.f_days = tk.Frame(self.f_backup_opts, bg="white")
             tk.Label(self.f_days, text="Günler:", bg="white", width=6).pack(side="left", anchor="n")
             
             self.days_vars = {}
             day_map = [("Pzt", "mon"), ("Sal", "tue"), ("Çar", "wed"), ("Per", "thu"), ("Cum", "fri"), ("Cmt", "sat"), ("Paz", "sun")]
             
             f_days_checks = tk.Frame(self.f_days, bg="white")
             f_days_checks.pack(side="left")
             
             saved_days = self.config_data.get("backup_days", [])
             
             for i, (label, val) in enumerate(day_map):
                 var = tk.BooleanVar(value=(val in saved_days))
                 chk = tk.Checkbutton(f_days_checks, text=label, variable=var, bg="white")
                 chk.grid(row=i//4, column=i%4, sticky="w")
                 self.days_vars[val] = var

             def update_backup_ui(event=None):
                 freq = chk_freq.get()
                 # Reset visibility
                 self.f_hours.pack_forget()
                 self.f_time.pack_forget()
                 self.f_days.pack_forget()
                 
                 if freq == "Saatlik":
                     self.f_hours.pack(anchor="w", pady=2)
                 elif freq == "Günlük":
                     self.f_time.pack(anchor="w", pady=2)
                 elif freq == "Haftalık":
                     self.f_time.pack(anchor="w", pady=2)
                     self.f_days.pack(anchor="w", pady=2)
             
             chk_freq.bind("<<ComboboxSelected>>", update_backup_ui)
             update_backup_ui() # init state

    def save_wizard_config(self):
        # Helper to save wizard config to json
        config_path = "wizard_config.json"
        
        # Harvest data
        data = {}
        if hasattr(self, "ui_entries"):
            for key, ent in self.ui_entries.items():
                if isinstance(ent, ttk.Combobox):
                    data[key] = ent.get()
                else:
                    data[key] = ent.get()
        
        # Save to file
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
        
        # Also update backup_config.json specifically for the backup script
        if "backup_dir" in data:
            bkp_config = {"backup_dir": data["backup_dir"]}
            
            # Map UI interval to code
            ui_interval = data.get("backup_interval_ui", "Kapalı")
            
            if ui_interval == "Saatlik": 
                bkp_config["backup_interval"] = "hourly"
                bkp_config["backup_hours"] = data.get("backup_hours", "1")
            elif ui_interval == "Günlük": 
                bkp_config["backup_interval"] = "daily"
                bkp_config["backup_time"] = data.get("backup_time", "23:00")
            elif ui_interval == "Haftalık":
                bkp_config["backup_interval"] = "weekly"
                bkp_config["backup_time"] = data.get("backup_time", "23:00")
                
                # harvest days from self.days_vars if accessible, but we only have 'data' dict here
                # We need to ensure days_vars are captured into 'data' before this point
                pass 
            else: 
                bkp_config["backup_interval"] = "off"
                
            # SPECIAL HANDLE: Since save_wizard_config reads from `self.ui_entries` but days are in `self.days_vars`
            # We need to manually inject them into bkp_config if we can access 'self'
            if hasattr(self, 'days_vars'):
                 selected_days = [d for d, v in self.days_vars.items() if v.get()]
                 bkp_config["backup_days"] = selected_days
            
            # Save it where backup_db.py can find it comfortably (e.g. backend root)
            root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            with open(os.path.join(root_dir, "backup_config.json"), "w", encoding="utf-8") as f:
                json.dump(bkp_config, f, indent=4)
            
            if is_pass:
                # Add Show Password Toggle
                show_var = tk.BooleanVar(value=False)
                def toggle(v=show_var, e=ent):
                    e.config(show="" if v.get() else "*")
                
                chk = tk.Checkbutton(parent, text="Göster", variable=show_var, command=toggle, bg="white", activebackground="white")
                chk.grid(row=i+row_offset, column=2, padx=5)
            
        parent.columnconfigure(1, weight=1)
        
        # Button Frame
        btn_frame = tk.Frame(parent, bg="white")
        btn_frame.grid(row=len(labels)+row_offset, column=0, columnspan=2, pady=15)
        
        # Check Server Button (New)
        ttk.Button(btn_frame, text="Sunucuyu Kontrol Et", 
                   command=lambda p=prefix: self.check_server_connection(p)).pack(side="left", padx=5)

        # Connect/Create DB Button (Existing)
        ttk.Button(btn_frame, text="Veritabanını Bağla/Kur", 
                   command=lambda p=prefix: self.test_connection(p)).pack(side="left", padx=5)

    def test_connection(self, prefix):
        # Gather data
        host = self.ui_entries[f"{prefix}_host"].get()
        port = self.ui_entries[f"{prefix}_port"].get()
        db = self.ui_entries[f"{prefix}_db"].get()
        user = self.ui_entries[f"{prefix}_user"].get()
        pwd = self.ui_entries[f"{prefix}_pass"].get()
        
        try:
            if prefix == "pg":
                if not psycopg2: 
                    messagebox.showwarning("Uyarı", "psycopg2 modülü yüklü değil. Test yapılamıyor.")
                    return
                
                try:
                    # Force UTF8 client encoding to avoid decoding errors from server messages
                    conn = psycopg2.connect(
                        host=host, 
                        port=port,
                        database=db, 
                        user=user, 
                        password=pwd, 
                        connect_timeout=3,
                        options="-c client_encoding=UTF8"
                    )
                    conn.close()
                    messagebox.showinfo("Başarılı", f"PostgreSQL ({db}) bağlantısı kuruldu! ✅\n\nVeritabanı yapısı ve tablolar kontrol ediliyor...")
                    self.setup_postgresql(host, port, user, pwd, db)
                except UnicodeDecodeError as ude:
                    # If we still get a decoding error, it's likely the "Database does not exist" message
                    # containing Turkish characters that psycopg2 failed to handle even with options.
                    if messagebox.askyesno("Veritabanı Kurulumu", f"PostgreSQL bağlantısı sırasında bir kodlama hatası oluştu.\nBu genellikle '{db}' veritabanının henüz mevcut olmamasından kaynaklanır.\n\nVeritabanı otomatik oluşturulsun mu?"):
                        self.setup_postgresql(host, port, user, pwd, db, create_db=True)
                except Exception as e:
                    err_msg = self.safe_str(e)
                    # Check for pgcode 3D000 (Invalid Catalog Name) or fallback to string match
                    if getattr(e, 'pgcode', None) == '3D000' or ("database" in err_msg.lower() and "does not exist" in err_msg.lower()):
                        if messagebox.askyesno("Veritabanı Yok", f"'{db}' veritabanı bulunamadı. Otomatik oluşturulsun mu?"):
                            self.setup_postgresql(host, port, user, pwd, db, create_db=True)
                        else:
                            friendly_err = f"Veritabanı bulunamadı: '{db}'\nLütfen veritabanının Postgres üzerinde oluşturulduğundan emin olun."
                            messagebox.showerror("Hata", friendly_err)
                    elif "password authentication failed" in err_msg.lower():
                        friendly_err = "Kullanıcı adı veya şifre hatalı!"
                        messagebox.showerror("Hata", friendly_err)
                    elif "is not accepting connections" in err_msg.lower() or "timeout" in err_msg.lower():
                        friendly_err = f"Sunucuya ulaşılamıyor: {host}\nLütfen host adresini ve portu (5432) kontrol edin."
                        messagebox.showerror("Hata", friendly_err)
                    else:
                        friendly_err = f"Bağlantı Hatası: {err_msg}"
                        messagebox.showerror("Hata", friendly_err)
            else:
                if not pymssql:
                    messagebox.showwarning("Uyarı", "pymssql modülü yüklü değil. Test yapılamıyor.")
                    return
                
                try:
                    conn = pymssql.connect(
                        server=host, 
                        user=user, 
                        password=pwd, 
                        database=db, 
                        timeout=3
                    )
                    conn.close()
                    messagebox.showinfo("Başarılı", f"LOGO MSSQL ({db}) bağlantısı kuruldu! ✅\n\nFirma ve Dönem listeleri yükleniyor...")
                    if hasattr(self, 'ms_meta_frame'):
                        self.ms_meta_frame.grid() # SHOW Meta Frame
                    self.populate_logo_combos()
                except Exception as e:
                    err_msg = self.safe_str(e)
                    if "Login failed" in err_msg:
                        friendly_err = "Kullanıcı adı veya şifre hatalı! (MSSQL Login Failed)"
                    elif "Could not find database" in err_msg or "cannot be opened" in err_msg:
                        friendly_err = f"Veritabanı bulunamadı: '{db}'"
                    elif "Unknown host" in err_msg or "Adaptive Server is unavailable" in err_msg:
                        friendly_err = f"MSSQL Sunucusuna ulaşılamıyor: {host}\nLütfen SQL Browser servisinin açık olduğunu ve bağlantı izni verildiğini kontrol edin."
                    else:
                        friendly_err = f"Bağlantı Hatası: {err_msg}"
                    messagebox.showerror("Hata", friendly_err)
        except Exception as e:
            messagebox.showerror("Beklenmedik Hata", f"Test sırasında bir hata oluştu: {self.safe_str(e)}")

    def check_server_connection(self, prefix):
        """Checks connection to the Server only (using default DB 'postgres' or 'master')."""
        host = self.ui_entries[f"{prefix}_host"].get()
        port = self.ui_entries[f"{prefix}_port"].get()
        user = self.ui_entries[f"{prefix}_user"].get()
        pwd = self.ui_entries[f"{prefix}_pass"].get()
        
        try:
            if prefix == "pg":
                if not psycopg2:
                    messagebox.showwarning("Uyarı", "psycopg2 modülü yüklü değil.")
                    return
                # Connect to default 'postgres' db
                conn = psycopg2.connect(host=host, port=port, user=user, password=pwd, database="postgres", connect_timeout=5)
                conn.close()
                messagebox.showinfo("Başarılı", f"PostgreSQL Sunucu Erişimi: BAŞARILI ✅\n\nHost: {host}\nKullanıcı: {user}\n\nŞimdi 'Veritabanını Bağla/Kur' diyerek devam edebilirsiniz.")
            else:
                if not pymssql:
                    messagebox.showwarning("Uyarı", "pymssql modülü yüklü değil.")
                    return
                # Connect to default 'master' db
                conn = pymssql.connect(server=host, user=user, password=pwd, database="master", timeout=5)
                conn.close()
                messagebox.showinfo("Başarılı", f"MSSQL Sunucu Erişimi: BAŞARILI ✅\n\nHost: {host}\nKullanıcı: {user}")

        except Exception as e:
            err = self.safe_str(e)
            if "password authentication failed" in err or "Login failed" in err:
                msg = f"Giriş Başarısız! Şifre veya Kullanıcı adı hatalı.\n\nDetay: {err}"
            elif "timeout" in err or "refused" in err or "network" in err.lower():
                msg = f"Sunucuya Ulaşılamıyor!\nIP Adresi ({host}) ve Port ({port}) bilgilerini kontrol edin.\nGüvenlik duvarı ayarlarını gözden geçirin.\n\nDetay: {err}"
            else:
                msg = f"Sunucu Bağlantı Hatası:\n{err}"
            
            messagebox.showerror("Sunucu Erişim Hatası", msg)

    def create_step_data_transfer(self):
        content = tk.Frame(self.container, bg="white", padx=20, pady=20)
        content.pack(fill="both", expand=True)
        
        tk.Label(content, text="Logo ERP Veri Aktarımı", font=("Segoe UI", 14, "bold"), bg="white").pack(anchor="w")
        tk.Label(content, text="Logo veritabanındaki kayıtları EXFIN OPS sistemine aktarın.", bg="white", fg="#64748b").pack(anchor="w", pady=(0, 20))
        
        # Frame for Companies
        frm_comp = tk.LabelFrame(content, text="1. Firma ve Dönemler", bg="white", padx=10, pady=10)
        frm_comp.pack(fill="x", pady=5)
        
        tk.Label(frm_comp, text="L_CAPIFIRM ve L_CAPIPERIOD tablolarından firma/dönem bilgilerini çeker.", bg="white", wraplength=600, anchor="w").pack(fill="x")
        ttk.Button(frm_comp, text="Firmaları Aktar", command=self.transfer_companies).pack(anchor="w", pady=5)
        ttk.Button(frm_comp, text="Firmaları Önizle", command=lambda: self.preview_logo_data("companies")).pack(anchor="w", pady=2)
        
        # Frame for Master Data
        frm_master = tk.LabelFrame(content, text="2. Master Veriler (Kartlar)", bg="white", padx=10, pady=10)
        frm_master.pack(fill="x", pady=5)
        
        tk.Label(frm_master, text="Satış Elemanları (LG_SLSMAN), Ambarlar, Markalar, Birimler vb. aktarır.\nNOT: Satış elemanları için otomatik kullanıcı (User) oluşturulur.", bg="white", wraplength=600, justify="left", anchor="w").pack(fill="x")
        
        frm_pwd = tk.Frame(frm_master, bg="white")
        frm_pwd.pack(fill="x", pady=5)
        tk.Label(frm_pwd, text="Yeni Kullanıcı Varsayılan Şifre:", bg="white").pack(side="left")
        self.ent_user_pwd = ttk.Entry(frm_pwd, width=15)
        self.ent_user_pwd.insert(0, "123456")
        self.ent_user_pwd.pack(side="left", padx=5)
        
        ttk.Button(frm_master, text="Master Verileri Aktar", command=self.transfer_master_data).pack(anchor="w", pady=5)
        ttk.Button(frm_master, text="Master Verileri Önizle", command=lambda: self.preview_logo_data("master")).pack(anchor="w", pady=2)
        
        # Log Area
        tk.Label(content, text="Aktarım Logları:", bg="white").pack(anchor="w", pady=(10,0))
        self.transfer_log = tk.Text(content, bg="#0f172a", fg="#4ade80", font=("Consolas", 9), height=12)
        self.transfer_log.pack(fill="both", expand=True, pady=5)

    def preview_logo_data(self, data_type):
        """Shows a preview of data to be transferred from Logo MSSQL."""
        try:
            # Connect to MSSQL (No PG needed for preview)
            ms_conn = pymssql.connect(
                server=self.config_data["ms_host"],
                user=self.config_data["ms_user"],
                password=self.config_data["ms_pass"],
                database=self.config_data["ms_db"]
            )
            ms_cur = ms_conn.cursor(as_dict=True)
            
            headers = []
            rows = []
            title = ""
            
            if data_type == "companies":
                title = "Logo Firmalar ve Dönemler"
                ms_cur.execute("SELECT NR, NAME, TAXNR, STREET, CITY FROM L_CAPIFIRM ORDER BY NR")
                firms = ms_cur.fetchall()
                headers = ["LogoNr", "Firma Adı", "Vergi No", "Adres"]
                for f in firms:
                    rows.append((f['NR'], f['NAME'], f.get('TAXNR'), f"{f.get('STREET')} / {f.get('CITY')}"))
                    
            elif data_type == "master":
                title = "Logo Master Veriler (Örnek: Satış Elemanları & Ambarlar)"
                # Just show Salesmen and Warehouses as sample
                ms_cur.execute("SELECT TOP 10 CODE, DEFINITION_, EMAILADDR, FIRMNR FROM LG_SLSMAN WHERE ACTIVE=0 ORDER BY CODE")
                sls = ms_cur.fetchall()
                headers = ["TÜR", "KOD", "AÇIKLAMA", "EK BİLGİ"]
                for s in sls:
                    rows.append(("SATIS_ELEMANI", s['CODE'], s['DEFINITION_'], s['EMAILADDR']))
                
                ms_cur.execute("SELECT TOP 10 NR, NAME FROM L_CAPIWHOUSE ORDER BY NR")
                whs = ms_cur.fetchall()
                for w in whs:
                    rows.append(("AMBAR", str(w['NR']), w['NAME'], ""))
            
            ms_conn.close()
            
            # Show in a new window
            top = tk.Toplevel(self)
            top.title(f"Önizleme: {title}")
            top.geometry("800x600")
            top.state('zoomed') # Full screen
            
            tree = ttk.Treeview(top, columns=headers, show="headings")
            for h in headers:
                tree.heading(h, text=h)
                tree.column(h, width=150)
            
            tree.pack(fill="both", expand=True, padx=10, pady=10)
            
            for r in rows:
                tree.insert("", tk.END, values=r)
                
            ttk.Button(top, text="Kapat", command=top.destroy).pack(pady=5)
            
        except Exception as e:
            messagebox.showerror("Önizleme Hatası", f"Veri çekilemedi:\n{e}")

    def transfer_companies(self):
        def run():
            try:
                self.transfer_log.delete(1.0, tk.END)
                self.transfer_log.insert(tk.END, "> Logo Firma/Dönem aktarımı başlıyor...\n")
                
                # Connect to MSSQL
                ms_conn = pymssql.connect(
                    server=self.config_data["ms_host"],
                    user=self.config_data["ms_user"],
                    password=self.config_data["ms_pass"],
                    database=self.config_data["ms_db"]
                )
                ms_cur = ms_conn.cursor(as_dict=True)
                
                # Connect to PG
                pg_conn = psycopg2.connect(
                    host=self.config_data["pg_host"],
                    port=self.config_data["pg_port"],
                    user=self.config_data["pg_user"],
                    password=self.config_data["pg_pass"],
                    database=self.config_data["pg_db"],
                    options="-c client_encoding=UTF8"
                )
                pg_cur = pg_conn.cursor()
                
                # Fetch Firms
                self.transfer_log.insert(tk.END, "> Firmalar (L_CAPIFIRM) çekiliyor...\n")
                ms_cur.execute("SELECT NR, NAME, TAXNR, STREET, CITY FROM L_CAPIFIRM ORDER BY NR")
                firms = ms_cur.fetchall()
                
                for f in firms:
                    nr = f['NR']
                    code = str(nr).zfill(3)
                    name = self.safe_str(f['NAME'])
                    # Insert Company
                    pg_cur.execute("""
                        INSERT INTO companies (logo_nr, code, name, is_default, tax_number, tax_office, address)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (id) DO NOTHING
                    """, (nr, code, name, False, f.get('TAXNR'), None, f"{self.safe_str(f.get('STREET'))} {self.safe_str(f.get('CITY'))}"))
                    
                    # Get ID
                    pg_cur.execute("SELECT id FROM companies WHERE logo_nr=%s", (nr,))
                    cid = pg_cur.fetchone()[0]
                    
                    self.transfer_log.insert(tk.END, f"  + Firma Eklendi: {nr} - {name}\n")
                    
                    # Fetch Periods
                    ms_cur.execute(f"SELECT NR, BEGDATE, ENDDATE FROM L_CAPIPERIOD WHERE FIRMNR={nr} ORDER BY NR")
                    periods = ms_cur.fetchall()
                    for p in periods:
                        pnr = p['NR']
                        pcode = str(pnr).zfill(2)
                        pname = f"{code} - {pcode}. Dönem"
                         # Insert Period
                        pg_cur.execute("""
                            INSERT INTO periods (company_id, logo_period_nr, code, name, start_date, end_date)
                            VALUES (%s, %s, %s, %s, %s, %s)
                        """, (cid, pnr, pcode, pname, p['BEGDATE'], p['ENDDATE']))
                        self.transfer_log.insert(tk.END, f"    - Dönem Eklendi: {pcode}\n")
                        
                pg_conn.commit()
                ms_conn.close()
                pg_conn.close()
                self.transfer_log.insert(tk.END, "\n> Firma aktarımı TAMAMLANDI! ✅\n")
                messagebox.showinfo("Başarılı", "Firma ve Dönem bilgileri aktarıldı.")
            except Exception as e:
                self.transfer_log.insert(tk.END, f"\n[HATA] {e}\n")
                messagebox.showerror("Hata", str(e))
                
        threading.Thread(target=run).start()

    def transfer_master_data(self):
        user_pwd = self.ent_user_pwd.get() or "123456"
        # Bcrypt hash for 123456
        pwd_hash = "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxwKc.6IymCs7CN52old.kSj3jWay"
        
        def run():
            try:
                self.transfer_log.insert(tk.END, "\n> Master Data aktarımı başlıyor...\n")
                
                # DB Connects
                ms_conn = pymssql.connect(
                    server=self.config_data["ms_host"],
                    user=self.config_data["ms_user"],
                    password=self.config_data["ms_pass"],
                    database=self.config_data["ms_db"]
                )
                ms_cur = ms_conn.cursor(as_dict=True)
                
                pg_conn = psycopg2.connect(
                    host=self.config_data["pg_host"],
                    port=self.config_data["pg_port"],
                    user=self.config_data["pg_user"],
                    password=self.config_data["pg_pass"],
                    database=self.config_data["pg_db"],
                    options="-c client_encoding=UTF8"
                )
                pg_cur = pg_conn.cursor()
                
                # 1. SALESMEN (LG_SLSMAN)
                self.transfer_log.insert(tk.END, "> Satış Elemanları (LG_SLSMAN) aktarılıyor...\n")
                # Removed TELNRS1 as it's not standard in LG_SLSMAN
                ms_cur.execute("SELECT CODE, DEFINITION_, EMAILADDR, FIRMNR, ACTIVE FROM LG_SLSMAN WHERE ACTIVE=0 ORDER BY CODE")
                sls = ms_cur.fetchall()
                
                count_user = 0
                for s in sls:
                    code = self.safe_str(s['CODE'])
                    name = self.safe_str(s['DEFINITION_'])
                    email = self.safe_str(s['EMAILADDR']) or f"{code}@example.com"
                    tel = None # self.safe_str(s.get('TELNRS1'))
                    firmnr = s['FIRMNR'] # -1 for all firms usually
                    
                    # Find company ID if specific firm, else assign to first/all? 
                    # For simplicity, let's link to Company with LogoNr=1 as default context or handle null.
                    # Core schema says salesman has company_id. We'll try to find company by logo_nr, else default.
                    
                    pg_cur.execute("SELECT id FROM companies WHERE logo_nr=%s", (1,)) if firmnr == -1 else pg_cur.execute("SELECT id FROM companies WHERE logo_nr=%s", (firmnr,))
                    res = pg_cur.fetchone()
                    if res:
                        cid = res[0]
                        # Insert Salesman
                        pg_cur.execute("""
                            INSERT INTO salesmen (company_id, code, name, email, tel_number)
                            VALUES (%s, %s, %s, %s, %s)
                        """, (cid, code, name, email, tel))
                        
                        # CREATE APP USER
                        # Username: satis.{code}
                        username = f"satis.{code}".lower().replace(" ", "")
                        # Check exist
                        pg_cur.execute("SELECT id FROM users WHERE username=%s", (username,))
                        if not pg_cur.fetchone():
                            pg_cur.execute("""
                                INSERT INTO users (username, password_hash, full_name, role, email, is_active, logo_salesman_code)
                                VALUES (%s, %s, %s, 'salesman', %s, true, %s)
                            """, (username, pwd_hash, name, email, code))
                            count_user += 1
                            self.transfer_log.insert(tk.END, f"  + User Oluşturuldu: {username}\n")
                
                self.transfer_log.insert(tk.END, f"> Toplam {count_user} kullanıcı açıldı.\n")
                
                # 2. WAREHOUSES (L_CAPIWHOUSE)
                # 2. WAREHOUSES (L_CAPIWHOUSE)
                self.transfer_log.insert(tk.END, "> Ambarlar (L_CAPIWHOUSE) aktarılıyor...\n")
                ms_cur.execute("SELECT NR, NAME, FIRMNR FROM L_CAPIWHOUSE ORDER BY NR")
                whs = ms_cur.fetchall()
                for w in whs:
                    nr = w['NR'] # Logo ref
                    name = self.safe_str(w['NAME'])
                    firmnr = w['FIRMNR']
                    
                    pg_cur.execute("SELECT id FROM companies WHERE logo_nr=%s", (firmnr,))
                    res = pg_cur.fetchone()
                    if res:
                        cid = res[0]
                        pg_cur.execute("""
                            INSERT INTO warehouses (company_id, code, name, cost_center, logo_ref)
                            VALUES (%s, %s, %s, %s, %s)
                        """, (cid, str(nr).zfill(2), name, None, nr))

                pg_conn.commit()
                ms_conn.close()
                pg_conn.close()
                self.transfer_log.insert(tk.END, "\n> Master Data aktarımı TAMAMLANDI! ✅\n")
                messagebox.showinfo("Başarılı", "Master veriler ve Kullanıcılar oluşturuldu.")
            except Exception as e:
                self.transfer_log.insert(tk.END, f"\n[HATA] {e}\n")
                messagebox.showerror("Hata", str(e))
                
        threading.Thread(target=run).start()

    def create_step_security(self):
        content = tk.Frame(self.container, bg="white", padx=20, pady=20)
        content.pack(fill="both", expand=True)
        
        tk.Label(content, text="Güvenlik Ayarları (SSL)", font=("Segoe UI", 14, "bold"), bg="white").pack(anchor="w")
        tk.Label(content, text="API iletişimi için HTTPS şifrelemesi ayarlayın.", bg="white", fg="#64748b").pack(anchor="w", pady=(0, 20))
        
        info_frame = tk.LabelFrame(content, text="Otomatik SSL (Self-Signed)", bg="white", padx=15, pady=15)
        info_frame.pack(fill="x", pady=10)
        
        tk.Label(info_frame, text="Bu işlem güvenli iletişim için bir sertifika oluşturur ve ayarlar.", bg="white", justify="left").pack(anchor="w")
        tk.Label(info_frame, text="⚠️ Tarayıcıda 'Güvenli Değil' uyarısı çıkabilir (normaldir), ancak bağlantı şifrelidir.", 
                 bg="white", fg="#e11d48", font=("Segoe UI", 9, "italic")).pack(anchor="w", pady=(5, 10))

        self.ssl_log = tk.Text(content, bg="#0f172a", fg="#22c55e", font=("Consolas", 9), height=10)
        self.ssl_log.pack(fill="both", expand=True, pady=10)

        def run_db_setup():
            self.db_log.delete(1.0, tk.END)
            self.db_log.insert(tk.END, "Veritabanı kontrol ediliyor...\n")
            
            # Save entries to environment/config
            self.save_wizard_config()

        def run_ssl_gen():
            self.ssl_log.delete(1.0, tk.END)
            self.ssl_log.insert(tk.END, "> Sertifika oluşturuluyor...\n")
            try:
                # Add scripts path to sys.path to import
                script_dir = os.path.dirname(os.path.abspath(__file__))
                sys.path.append(script_dir)
                import generate_cert
                
                cert, key = generate_cert.generate_self_signed_cert()
                self.ssl_log.insert(tk.END, f"> Sertifika: {cert}\n")
                self.ssl_log.insert(tk.END, f"> Anahtar: {key}\n")
                
                # Update .env
                env_path = os.path.join(os.path.dirname(script_dir), ".env")
                with open(env_path, "a") as f: # Append or Update? Ideally Update.
                    f.write(f"\nSSL_CERT_FILE={cert}\nSSL_KEY_FILE={key}\n")
                
                self.ssl_log.insert(tk.END, "> .env dosyası güncellendi.\n")
                self.ssl_log.insert(tk.END, "\nBAŞARILI! ✅\n")
                messagebox.showinfo("Başarılı", "SSL Sertifikası oluşturuldu ve aktif edildi.")
                
            except Exception as e:
                self.ssl_log.insert(tk.END, f"\n[HATA] {e}\n")
                messagebox.showerror("Hata", str(e))

        ttk.Button(info_frame, text="🔐 SSL Sertifikası Oluştur ve Etkinleştir", command=run_ssl_gen).pack(anchor="w")

    def create_step_service_install(self):
        content = tk.Frame(self.container, bg="white", padx=20, pady=20)
        content.pack(fill="both", expand=True)
        
        tk.Label(content, text="Windows Servis Kurulumu", font=("Segoe UI", 14, "bold"), bg="white").pack(anchor="w")
        tk.Label(content, text="API servisi arka planda çalışacak şekilde sisteme kaydedilecek.", bg="white", fg="#64748b").pack(anchor="w", pady=(0, 20))
        
        # Service Name Customization Frame
        frm_svc = tk.Frame(content, bg="white")
        frm_svc.pack(fill="x", pady=5)
        
        tk.Label(frm_svc, text="Servis Adı:", bg="white", width=10, anchor="w").pack(side="left")
        
        self.ent_svc_name = ttk.Entry(frm_svc)
        self.ent_svc_name.insert(0, self.config_data.get("service_name", "ExfinOPS_ApiService"))
        self.ent_svc_name.config(state="readonly")
        self.ent_svc_name.pack(side="left", padx=5)
        
        def unlock_svc():
            pwd = tk.simpledialog.askstring("Şifre", "Servis adını değiştirmek için şifre girin:", parent=self)
            if pwd == "1002":
                self.ent_svc_name.config(state="normal")
                messagebox.showinfo("Başarılı", "Servis adı düzenleme aktif!")
            elif pwd:
                messagebox.showerror("Hata", "Hatalı şifre!")
                
        import tkinter.simpledialog
        ttk.Button(frm_svc, text="Değiştir", command=unlock_svc, width=8).pack(side="left")
        
        self.svc_log = tk.Text(content, bg="#0f172a", fg="#38bdf8", font=("Consolas", 9), height=15)
        self.svc_log.pack(fill="both", expand=True, pady=10)
        
        btn_frame = tk.Frame(content, bg="white")
        btn_frame.pack(pady=5)
        
        btn_svc = ttk.Button(btn_frame, text="Servisi Kur ve Başlat", command=self.run_service_setup)
        btn_svc.pack(side="left", padx=5)
        
        ttk.Button(btn_frame, text="Hata Ayıkla (Debug)", command=self.run_service_debug).pack(side="left", padx=5)
        
        # --- NEW ALTERNATIVE STARTUP SECTION ---
        tk.Label(content, text="\n———————— VEYA ————————", bg="white", fg="#888888").pack(pady=(10, 5))
        
        # INCREASED VISIBILITY: Remove white bg from LabelFrame to let system default show, or force black text
        frm_alt = tk.LabelFrame(content, text="Alternatif: Basit Başlangıç (Önerilen)", bg="#f8fafc", fg="black", font=("Segoe UI", 10, "bold"), padx=10, pady=10)
        frm_alt.pack(fill="x", pady=15, padx=5)
        
        tk.Label(frm_alt, text="Windows Servisi sorun çıkarıyorsa bunu kullanın.\nSistem her açıldığında otomatik başlar ve saatin yanında KONTROL SİMGESİ ekler.", 
                 bg="#f8fafc", fg="black", justify="left", font=("Segoe UI", 9)).pack(anchor="w", pady=(0, 10))
                 
        # Button with explicit style or packing
        btn = ttk.Button(frm_alt, text="⚡ BASİT BAŞLANGIÇ KUR (SİMGE)", command=self.setup_simple_startup)
        btn.pack(anchor="w", ipady=5)

        tk.Label(content, text="NOT: Port 8000'i kullanan diğer uvicorn pencerelerini kapatmayı unutmayın.", 
                 bg="white", fg="red", font=("Segoe UI", 9, "italic")).pack(pady=5)

    def run_service_debug(self):
        """Runs the service in debug mode to see errors."""
        try:
            base_path = os.getcwd() # Should be correct if launched from root or handles relative
            if not os.path.exists(os.path.join(base_path, "windows_service.py")):
                # Try finding it if we are in scripts
                if os.path.exists(os.path.join(os.path.dirname(base_path), "windows_service.py")):
                    base_path = os.path.dirname(base_path)
            
            venv_python = os.path.join(base_path, "venv", "Scripts", "python.exe")
            if not os.path.exists(venv_python):
                messagebox.showerror("Hata", f"Python venv bulunamadı:\n{venv_python}")
                return
                
            service_script = os.path.join(base_path, "windows_service.py")
            
            # Open in a new console window to keep it visible
            # 'start "Title"' is required because if the first arg is quoted, start treats it as title
            # We use cmd /k to keep window open
            cmd = f'start "Service Debug" cmd /k ""{venv_python}" "{service_script}" debug"'
            subprocess.run(cmd, shell=True, cwd=base_path)
            
            messagebox.showinfo("Debug Modu", "Debug penceresi açıldı.\n\nEğer pencere hemen kapanıyorsa veya hata mesajı görüyorsanız, lütfen o hatayı paylaşın.")
            
        except Exception as e:
            messagebox.showerror("Hata", str(e))

    def setup_simple_startup(self):
        """Adds the application to Windows Startup folder for current user, using Tray App."""
        try:
            base_path = self.config_data.get("api_path", "")
            if not base_path or not os.path.exists(base_path):
                 base_path = os.getcwd()
            
            # 0. Ensure Dependencies (pystray)
            venv_python = os.path.join(base_path, "venv", "Scripts", "python.exe")
            if os.path.exists(venv_python):
                 self.svc_log.insert(tk.END, "> Sistem Tepsisi (Tray) kütüphaneleri yükleniyor...\n")
                 subprocess.run(f'"{venv_python}" -m pip install pystray Pillow requests pywin32 --quiet', shell=True, cwd=base_path)

            # 1. Target Script: tray_app.py
            tray_script = os.path.join(base_path, "tray_app.py")
            if not os.path.exists(tray_script):
                 self.svc_log.insert(tk.END, "> Tray App bulunamadı, script'lerden kopyalanıyor...\n")
                 # Assuming we are running from scripts/, try to find it
                 src = os.path.join(os.path.dirname(__file__), "..", "tray_app.py")
                 if os.path.exists(src):
                     import shutil
                     shutil.copy2(src, tray_script)
            
            # 2. Create VBS to launch Tray App hidden/detached
            vbs_path = os.path.join(base_path, "run_tray.vbs")
            
            with open(vbs_path, "w") as f:
                f.write('Set WshShell = CreateObject("WScript.Shell")\n')
                # Construct command: "python" "script"
                # We use Chr(34) for every quote to avoid syntax errors in VBS file
                f.write(f'cmd = Chr(34) & "{venv_python}" & Chr(34) & " " & Chr(34) & "{tray_script}" & Chr(34)\n')
                f.write('WshShell.Run cmd, 0\n')
                f.write('Set WshShell = Nothing\n')
            
            self.svc_log.insert(tk.END, f"> VBS Script oluşturuldu: {vbs_path}\n")

            # 3. Create Shortcut in Startup Folder
            startup_folder = os.path.join(os.getenv('APPDATA'), r"Microsoft\Windows\Start Menu\Programs\Startup")
            shortcut_path = os.path.join(startup_folder, "ExfinOPS_Tray.lnk")
            
            self.create_shortcut(vbs_path, shortcut_path, base_path)
            
            self.svc_log.insert(tk.END, f"> Başlangıç kısayolu oluşturuldu: {shortcut_path}\n")
            self.svc_log.insert(tk.END, "> [BAŞARILI] Sistem Tepsisi uygulaması açılışta çalışacak! ✅\n")
            
            # 4. Run Now?
            if messagebox.askyesno("Başlat", "Kurulum başarılı! Kontrol panelini (Tray App) şimdi başlatmak ister misiniz?"):
                 os.startfile(vbs_path)
                 self.svc_log.insert(tk.END, "> Tray App başlatıldı. Saatin yanındaki simgeyi kontrol edin.\n")
                 
            messagebox.showinfo("Başarılı", "Sistem Tepsisi (Tray) kurulumu tamamlandı.\nSaatin yanında uygulamanın durumunu (Yeşil/Kırmızı) görebilirsiniz.")

        except Exception as e:
            self.svc_log.insert(tk.END, f"> [HATA] Startup kurulumu başarısız: {e}\n")
            messagebox.showerror("Hata", f"Startup kurulumu yapılamadı:\n{e}")

    def create_shortcut(self, target, shortcut_path, working_dir):
        """Creates a shortcut using VBScript to avoid pywin32/win32com dependency issues."""
        try:
            vbs_content = f'''
Set oWS = WScript.CreateObject("WScript.Shell")
Set oLink = oWS.CreateShortcut("{shortcut_path}")
oLink.TargetPath = "{target}"
oLink.WorkingDirectory = "{working_dir}"
oLink.IconLocation = "{target}"
oLink.Save
'''
            vbs_file = os.path.join(working_dir, "make_shortcut_temp.vbs")
            with open(vbs_file, "w") as f:
                f.write(vbs_content)
            
            # Execute VBS
            subprocess.run(f'cscript //Nologo "{vbs_file}"', shell=True, check=True)
            
            # Cleanup
            if os.path.exists(vbs_file):
                os.remove(vbs_file)
                
        except Exception as e:
            self.svc_log.insert(tk.END, f"> [HATA] Kısayol oluşturma hatası (VBS): {e}\n")
            # Fallback to Powershell if VBS fails?
            pass


    def log_db1(self, msg):
        # Helper to log to a potentially existing log widget if we had one for DB
        # For now just print to console or try to log to svc_log (even if it's unrelated)
        # to avoid crash
        print(f"[DB LOG] {msg}")
        try:
            if hasattr(self, 'svc_log') and self.svc_log:
                 self.svc_log.insert(tk.END, f"{msg}\n")
                 self.svc_log.see(tk.END)
        except: pass

    def setup_postgresql(self, host, port, user, pwd, db, create_db=False):
        def run():
            try:
                # 1. Create DB if needed
                if create_db:
                    # Connect to 'postgres' default DB to create the new one
                    conn = psycopg2.connect(host=host, port=port, user=user, password=pwd, database="postgres", options="-c client_encoding=UTF8")
                    conn.autocommit = True
                    cur = conn.cursor()
                    cur.execute(f'CREATE DATABASE "{db}" WITH ENCODING = "UTF8"')
                    cur.close()
                    conn.close()
                    self.after(0, lambda: messagebox.showinfo("Bilgi", f"'{db}' veritabanı başarıyla oluşturuldu."))
                
                # 2. Connect to target DB and create tables
                conn = psycopg2.connect(host=host, port=port, user=user, password=pwd, database=db, options="-c client_encoding=UTF8")
                conn.autocommit = True
                cur = conn.cursor()
                
                # Load Schema
                schema_path = os.path.join(os.getcwd(), "sql", "schema", "01_core_schema.sql")
                if os.path.exists(schema_path):
                    self.after(0, lambda: self.log_db("Tablolar oluşturuluyor..."))
                    # Try different encodings for robustness
                    sql = ""
                    for enc in ['utf-8', 'cp1254', 'latin-5']:
                        try:
                            with open(schema_path, "r", encoding=enc) as f:
                                sql = f.read()
                            break
                        except: continue
                    
                    if sql:
                        # Improved SQL Splitter that handles $$ quoted blocks
                        # This regex finds commands ending with ; but ignores ; inside dollar quotes $$...$$
                        import re
                        # Clean Comments
                        sql = re.sub(r'--.*', '', sql)
                        
                        # Custom splitter for Postgres SQL function definitions
                        commands = []
                        current_cmd = []
                        in_dollar_quote = False
                        
                        for line in sql.splitlines():
                            line = line.strip()
                            if not line: continue
                            
                            if '$$' in line:
                                in_dollar_quote = not in_dollar_quote
                            
                            current_cmd.append(line)
                            
                            if line.endswith(';') and not in_dollar_quote:
                                full_cmd = '\n'.join(current_cmd)
                                if full_cmd.strip():
                                    commands.append(full_cmd)
                                current_cmd = []
                        
                        # Add remaining
                        if current_cmd:
                             full_cmd = '\n'.join(current_cmd)
                             if full_cmd.strip(): commands.append(full_cmd)

                        for stmt in commands:
                            if stmt.strip():
                                try:
                                    cur.execute(stmt)
                                except Exception as e:
                                    # Robutness: Ignore "already exists" errors to allow re-runs
                                    err = str(e).lower()
                                    if "already exists" in err:
                                        print(f"SQL Info: Table/Object already exists, skipping. ({err})")
                                    else:
                                        # Log actual errors but don't crash unless critical
                                        print(f"SQL Warn: {e}")
                                        self.after(0, lambda e=e: self.log_db1(f"⚠️ SQL Uyarısı: {str(e)[:100]}..."))

                        self.after(0, lambda: self.log_db("Tablolar ve şema kontrol edildi. ✅"))
                
                # 3. Load Demo Data if requested
                def ask_demo():
                    if messagebox.askyesno("Demo Veriler", "Sisteme deneme (mock) verileri yüklensin mi?\n(Admin kullanıcısı, test firmaları ve örnek kayıtlar kurulacaktır)"):
                        self.load_demo_data(host, port, user, pwd, db)
                
                self.after(0, ask_demo)
                cur.close()
                conn.close()
            except Exception as e:
                err = self.safe_str(e)
                self.after(0, lambda m=err: messagebox.showerror("DB Kurulum Hatası", f"PostgreSQL kurulumu sırasında hata oluştu:\n{m}"))

        threading.Thread(target=run).start()

    def load_demo_data(self, host, port, user, pwd, db):
        def run():
            try:
                conn = psycopg2.connect(host=host, port=port, user=user, password=pwd, database=db)
                conn.autocommit = True
                cur = conn.cursor()
                
                data_path = os.path.join(os.getcwd(), "sql", "data", "01_mock_data.sql")
                if os.path.exists(data_path):
                    with open(data_path, "r", encoding="utf-8") as f:
                        sql = f.read()
                        for stmt in sql.split(";"):
                            if stmt.strip():
                                cur.execute(stmt)
                    self.after(0, lambda: messagebox.showinfo("Başarılı", "Demo veriler başarıyla yüklendi! ✅\n\nVarsayılan kullanıcı: admin / 123456"))
                else:
                    self.after(0, lambda: messagebox.showwarning("Uyarı", "Demo veri dosyası bulunamadı."))
                
                cur.close()
                conn.close()
            except Exception as e:
                conn.rollback()
                err_msg = str(e)
                if "does not exist" in err_msg and "relation" in err_msg:
                    friendly = f"Demo veriler yüklenirken tablo eksik hatası alındı:\n{err_msg}\n\nLütfen '01_core_schema.sql' dosyasının güncel olduğundan emin olun."
                    self.after(0, lambda: messagebox.showerror("Şema Hatası", friendly))
                else:
                    err_val = self.safe_str(e)
                    self.after(0, lambda m=err_val: messagebox.showerror("Hata", f"Demo veriler yüklenirken hata oluştu: {m}"))

        threading.Thread(target=run).start()

    def log_db(self, msg):
        # We can add a temporary log for DB setup if needed
        pass

    def populate_logo_combos(self):
        if not pymssql: return
        host = self.ui_entries["ms_host"].get()
        user = self.ui_entries["ms_user"].get()
        pwd = self.ui_entries["ms_pass"].get()
        db = self.ui_entries["ms_db"].get()
        
        def run():
            try:
                conn = pymssql.connect(server=host, user=user, password=pwd, database=db, timeout=5)
                cursor = conn.cursor()
                cursor.execute("SELECT LTRIM(STR(NR, 3, 0)), NAME FROM L_CAPIFIRM ORDER BY NR")
                firms = [f"{str(row[0]).zfill(3)} - {row[1]}" for row in cursor.fetchall()]
                
                def update_ui():
                    self.ui_entries["ms_firma"]['values'] = firms
                    if firms:
                        current = self.config_data.get("ms_firma", "001")
                        for f in firms:
                            if f.startswith(current):
                                self.ui_entries["ms_firma"].set(f)
                                break
                        else:
                            self.ui_entries["ms_firma"].set(firms[0])
                        self.update_donem_combo(conn)
                self.after(0, update_ui)
            except Exception as e:
                err_msg = self.safe_str(e)
                self.after(0, lambda m=err_msg: messagebox.showerror("Hata", f"Firmalar listelenirken hata oluştu: {m}"))
        threading.Thread(target=run).start()

    def update_donem_combo(self, shared_conn=None):
        firma_str = self.ui_entries["ms_firma"].get()
        if not firma_str: return
        firma_nr = firma_str.split(' - ')[0].strip()
        
        def run():
            try:
                conn = shared_conn
                close_at_end = False
                if conn is None:
                    host = self.ui_entries["ms_host"].get()
                    user = self.ui_entries["ms_user"].get()
                    pwd = self.ui_entries["ms_pass"].get()
                    db = self.ui_entries["ms_db"].get()
                    conn = pymssql.connect(server=host, user=user, password=pwd, database=db, timeout=5)
                    close_at_end = True
                
                cursor = conn.cursor()
                # Use BEGDATE/ENDDATE instead of NAME which might not exist
                cursor.execute(f"SELECT LTRIM(STR(NR, 2, 0)), BEGDATE, ENDDATE FROM L_CAPIPERIOD WHERE FIRMNR = {int(firma_nr)} ORDER BY NR")
                # Format: 01 (01.01.2024 - 31.01.2024)
                periods = []
                for row in cursor.fetchall():
                    nr = str(row[0]).zfill(2)
                    beg = row[1].strftime('%d.%m.%Y') if row[1] else '?'
                    end = row[2].strftime('%d.%m.%Y') if row[2] else '?'
                    periods.append(f"{nr} ({beg} - {end})")
                
                def update_ui():
                    self.ui_entries["ms_donem"]['values'] = periods
                    if periods:
                        current = self.config_data.get("ms_donem", "01")
                        for p in periods:
                            if p.startswith(current):
                                self.ui_entries["ms_donem"].set(p)
                                break
                        else:
                            self.ui_entries["ms_donem"].set(periods[0])
                self.after(0, update_ui)
                if close_at_end: conn.close()
            except Exception as e:
                err_msg = self.safe_str(e)
                self.after(0, lambda m=err_msg: messagebox.showerror("Hata", f"Dönemler listelenirken hata oluştu: {m}"))
        
        if shared_conn: run()
        else: threading.Thread(target=run).start()

    def run_service_setup(self):
        self.svc_log.delete("1.0", tk.END)
        self.svc_log.insert(tk.END, "> Servis kurulumu başlatılıyor...\n")
        
        # USE PERSISTENT CONFIG PATH instead of reading from destroyed widget
        base_path = self.config_data.get("api_path", "")
        if not base_path:
            messagebox.showerror("Hata", "Uygulama yolu bulunamadı! Lütfen bir önceki adımları kontrol edin.")
            return

        # Ensure Directory Exists (Fix for WinError 267)
        if not os.path.exists(base_path):
            try:
                os.makedirs(base_path)
            except Exception as e:
                messagebox.showerror("Hata", f"Hedef dizin oluşturulamadı:\n{base_path}\n\n{e}")
                return

        # Check and Kill conflicting uvicorn threads
        self.svc_log.insert(tk.END, "> Port 8000 çakışmaları kontrol ediliyor...\n")
        killed = self.kill_uvicorns()
        if killed > 0:
            self.svc_log.insert(tk.END, f"> {killed} adet çakışan uvicorn işlemi sonlandırıldı. ✅\n")
        
        venv_python = os.path.join(base_path, "venv", "Scripts", "python.exe")
        service_script = os.path.join(base_path, "windows_service.py")
        
        # Update Service Name in windows_service.py if changed
        current_svc_name = self.ent_svc_name.get().strip()
        if current_svc_name and current_svc_name != "ExfinApiService":
            try:
                self.svc_log.insert(tk.END, f"> Servis adı güncelleniyor: {current_svc_name}...\n")
                with open(service_script, "r", encoding="utf-8") as f:
                    svc_content = f.read()
                
                # Replace SERVICE_NAME variable
                import re
                svc_content = re.sub(r'SERVICE_NAME\s*=\s*".*"', f'SERVICE_NAME = "{current_svc_name}"', svc_content)
                # Replace Display Name as well for consistency
                svc_content = re.sub(r'SERVICE_DISPLAY_NAME\s*=\s*".*"', f'SERVICE_DISPLAY_NAME = "{current_svc_name}"', svc_content)
                
                with open(service_script, "w", encoding="utf-8") as f:
                    f.write(svc_content)
                
                self.config_data["service_name"] = current_svc_name
            except Exception as e:
                self.svc_log.insert(tk.END, f"> Servis adı güncelleme hatası: {e}\n")

        def run():
            try:
                # 0.5 Install Core Dependencies (MOVED TO START)
                self.svc_log.insert(tk.END, "> Gerekli paketler (uvicorn, fastapi, pystray) yükleniyor...\n")
                subprocess.run(f'"{venv_python}" -m pip install uvicorn fastapi python-dotenv requests pymssql psycopg2 pystray Pillow --quiet', shell=True, cwd=base_path)

                # 1. Install pywin32 (MOVED TO START)
                self.svc_log.insert(tk.END, "> pywin32 kontrol ediliyor...\n")
                subprocess.run(f'"{venv_python}" -m pip install pywin32 --quiet', shell=True, cwd=base_path)
                
                # 1.1 Run pywin32 postinstall script
                self.svc_log.insert(tk.END, "> pywin32 sistem konfigürasyonu yapılıyor...\n")
                postinstall = os.path.join(base_path, "venv", "Scripts", "pywin32_postinstall.py")
                subprocess.run(f'"{venv_python}" "{postinstall}" -install', shell=True, capture_output=True, cwd=base_path)
                
                # 1.2 EXPERT DLL FIX: Copy pywin32 DLLs to bin subfolder
                try:
                    self.svc_log.insert(tk.END, "> Kritik DLL dosyaları hazırlanıyor (bin/ dir)...\n")
                    bin_dir = os.path.join(base_path, "bin")
                    if not os.path.exists(bin_dir):
                        os.makedirs(bin_dir)
                        
                    dll_dirs = [
                        os.path.join(base_path, "venv", "Lib", "site-packages", "pywin32_system32"),
                        os.path.join(base_path, "venv", "Lib", "site-packages", "win32")
                    ]
                    for ddir in dll_dirs:
                        if os.path.exists(ddir):
                            for dll in os.listdir(ddir):
                                if dll.endswith(".dll") or dll.endswith(".pyd"):
                                    src = os.path.join(ddir, dll)
                                    import shutil
                                    # Copy to bin (clean organization)
                                    shutil.copy2(src, os.path.join(bin_dir, dll))
                                    # Also copy to Scripts for venv execution
                                    shutil.copy2(src, os.path.join(base_path, "venv", "Scripts", dll))
                except:
                    pass

                # SEARCH AND COPY python*.dll (Explicit fix for 3.14+)
                # Look in base executable dir (e.g. AppData/.../Python314/)
                try:
                    import sys
                    import shutil
                    # Fix: Use sys.base_prefix to find the ORIGINAL python install, not the venv
                    base_exec_dir = sys.base_prefix 
                    venv_scripts = os.path.dirname(venv_python)
                    bin_dir = os.path.join(base_path, "bin") # already created above
                    
                    # Target directories for DLL copying (Shotgun approach for reliability)
                    targets = [
                        venv_scripts,
                        os.path.join(base_path, "venv", "Lib", "site-packages", "win32"),
                        os.path.join(base_path, "venv", "Lib", "site-packages", "pywin32_system32"),
                        bin_dir
                    ]

                    dll_found = False
                    # Check base_prefix and base_prefix/DLLs
                    search_dirs = [base_exec_dir, os.path.join(base_exec_dir, "DLLs")]
                    
                    for s_dir in search_dirs:
                        if not os.path.exists(s_dir): continue
                        for f in os.listdir(s_dir):
                            if f.lower().startswith("python") and f.lower().endswith(".dll"):
                                for target_dir in targets:
                                    if os.path.exists(target_dir):
                                        try: 
                                            shutil.copy2(os.path.join(s_dir, f), os.path.join(target_dir, f))
                                            if target_dir == venv_scripts: # Only log main one to avoid clutter
                                                self.svc_log.insert(tk.END, f"  + Copied {f} to {os.path.basename(target_dir)}/ ✅\n")
                                            dll_found = True
                                        except: pass
                    
                    if not dll_found:
                         self.svc_log.insert(tk.END, "  ! Python DLL ana dizinde bulunamadı, sistem yolları denenecek.\n")
                except Exception as e:
                     self.svc_log.insert(tk.END, f"  ! DLL Copy Error: {e}\n")

                # ==========================================
                # PRE-FLIGHT CHECK (ÖN KONTROL) - MOVED HERE
                # ==========================================
                self.svc_log.insert(tk.END, "> ÖN KONTROL: Servis betiği test ediliyor...\n")
                
                # Check 1: Syntax Error Check
                import py_compile
                try:
                    py_compile.compile(service_script, doraise=True)
                    self.svc_log.insert(tk.END, "  + Syntax OK ✅\n")
                except py_compile.PyCompileError as e:
                    self.svc_log.insert(tk.END, f"  [HATA] Yazım hatası tespit edildi:\n{e}\n")
                    self.svc_log.insert(tk.END, "  ! Kurulum durduruldu. Lütfen kodu düzeltin.\n")
                    return

                # Check 2: Dry-Run Import (Catches Runtime NameErrors & Missing DLLs)
                check_script = os.path.join(base_path, "check_service.py")
                with open(check_script, "w", encoding="utf-8") as f:
                    f.write(f"""
import sys
import os
try:
    sys.path.insert(0, r"{base_path}")
    os.chdir(r"{base_path}")
    import windows_service
    print("IMPORT_SUCCESS")
except Exception as e:
    print(f"IMPORT_ERROR: {{e}}")
    import traceback
    traceback.print_exc()
""")
                
                check_res = subprocess.run(f'"{venv_python}" "{check_script}"', shell=True, capture_output=True, text=True, cwd=base_path)
                if "IMPORT_SUCCESS" in check_res.stdout:
                    self.svc_log.insert(tk.END, "  + Import Test OK (DLLs & Variables) ✅\n")
                    try: os.remove(check_script)
                    except: pass
                else:
                    self.svc_log.insert(tk.END, f"  [KRİTİK HATA] Servis kodu çalıştırılamadı:\n")
                    # Safe decode for error output
                    try: out_err = check_res.stdout + "\n" + check_res.stderr
                    except: out_err = "Decode Error"
                    self.svc_log.insert(tk.END, f"{out_err}\n")
                    self.svc_log.insert(tk.END, "  ! Kurulum, pre-flight check başarısız olduğu için durduruluyor.\n")
                    return # STOP HERE IF PRE-FLIGHT FAILS

                # 1.3 Force Cleanup if needed
                self.svc_log.insert(tk.END, "> Eski servis kalıntıları temizleniyor...\n")
                
                # Cleanup BOTH old and new names to be safe
                targets = ["ExfinApiService", "ExfinOPS_ApiService", current_svc_name]
                if current_svc_name != "ExfinOPS_ApiService":
                    targets = ["ExfinApiService", "ExfinOPS_ApiService", current_svc_name] # Ensure default is always checked
                
                for svc in set(targets):
                    # Stop Service
                    subprocess.run(f'sc stop "{svc}"', shell=True, capture_output=True)
                    # Kill associated process aggressively
                    subprocess.run(f'taskkill /F /FI "SERVICES eq {svc}"', shell=True, capture_output=True)
                    
                    # Retry deletion loop for Error 1072
                    for i in range(5):
                        res_del = subprocess.run(f'sc delete "{svc}"', shell=True, capture_output=True, text=True)
                        out = res_del.stdout or ""
                        err = res_del.stderr or ""
                        
                        if "1072" not in err and ("SUCCESS" in out or "Hizmet yok" in err or "does not exist" in err):
                            break
                            
                        self.svc_log.insert(tk.END, f"> '{svc}' silinmek üzere işaretlenmiş (1072), bekleniyor ({i+1}/5)...\n")
                        self.svc_log.see(tk.END)
                        import time
                        time.sleep(2)
                
                # 2. Install Service
                
                # SAFE SUBPROCESS HELPER to avoid UnicodeDecodeError in threads
                def safe_run(cmd, cwd=None, capture=True):
                    try:
                        kwargs = {"shell": True, "text": True, "cwd": cwd}
                        if capture:
                             kwargs["capture_output"] = True
                        
                        # FORCE UTF-8 with REPLACE to handle any character
                        kwargs["encoding"] = "utf-8" 
                        kwargs["errors"] = "replace"
                        
                        return subprocess.run(cmd, **kwargs)
                    except Exception as e:
                        class MockRes:
                            stdout = ""
                            stderr = str(e)
                            returncode = 1
                        return MockRes()

                # 2. Install Service
                self.svc_log.insert(tk.END, "> New Service kaydediliyor...\n")
                # Use absolute path for service install to ensure SCM finds the script
                res = safe_run(f'"{venv_python}" "{service_script}" install', cwd=base_path)
                self.svc_log.insert(tk.END, f"{self.safe_str(res.stdout)}\n")
                
                if "1072" in res.stderr or "1072" in res.stdout:
                    if messagebox.askyesno("Servis Silme Bekleniyor", "Servis hâlâ silinmek üzere işaretlenmiş (Hata 1072).\n\nLütfen 'Hizmetler' penceresi açıksa KAPATIN ve bilgisayarı yeniden başlatmadan denemek için 'Evet'e basın."):
                        import time
                        time.sleep(3)
                        res = safe_run(f'"{venv_python}" "{service_script}" install', cwd=base_path)
                        self.svc_log.insert(tk.END, f"{self.safe_str(res.stdout)}\n")

                # 3. Set to Auto and Enable (Critical for 'Disabled' error)
                self.svc_log.insert(tk.END, "> Başlangıç modu 'Otomatik' olarak ayarlanıyor...\n")
                safe_run(f'sc config "{current_svc_name}" start= auto', capture=False)
                safe_run(f'"{venv_python}" "{service_script}" --startup auto update', cwd=base_path, capture=False)
                
                # 4. Start Service
                self.svc_log.insert(tk.END, "> Servis başlatılıyor...\n")
                res_start = safe_run(f'"{venv_python}" "{service_script}" start', cwd=base_path)
                
                if "Hizmet başlatılamadı" in res_start.stdout or "Error starting service" in res_start.stdout:
                    if messagebox.askyesno("Hata", "Servis başlatılamadı. Hizmetler penceresini (services.msc) kapatıp tekrar denemek ister misiniz?"):
                        self.svc_log.insert(tk.END, "> Temiz kurulum deneniyor...\n")
                        safe_run(f'sc stop "{current_svc_name}"', capture=False)
                        safe_run(f'sc delete "{current_svc_name}"', capture=False)
                        import time
                        time.sleep(3)
                        safe_run(f'"{venv_python}" "{service_script}" install', cwd=base_path, capture=False)
                        safe_run(f'sc config "{current_svc_name}" start= auto', capture=False)
                        res_start = safe_run(f'"{venv_python}" "{service_script}" start', cwd=base_path)

                self.svc_log.insert(tk.END, f"{res_start.stdout}\n")
                
                # 5. Verify Health
                import time
                time.sleep(3)
                check = subprocess.run(f'sc query "{current_svc_name}"', shell=True, capture_output=True, text=True)
                if "RUNNING" in check.stdout:
                    self.svc_log.insert(tk.END, "> [OK] Servis başarıyla çalışıyor! ✅\n")
                    
                    # 6. Final Connectivity Check (Requested by User)
                    try:
                        self.svc_log.insert(tk.END, "> Dış bağlantı ve Port kontrolü yapılıyor...\n")
                        # Use threading to not freeze UI
                        def check_connectivity():
                            try:
                                import socket
                                ip = requests.get("https://api.ipify.org", timeout=5).text
                                self.svc_log.insert(tk.END, f"> Public IP: {ip}\n")
                                
                                port_check = self.config_data.get("api_port", "8000")
                                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                                s.settimeout(3)
                                if s.connect_ex((ip, int(port_check))) == 0:
                                    self.svc_log.insert(tk.END, f"> PORT {port_check}: AÇIK / ERIŞİLEBİLİR 🌍✅\n")
                                else:
                                    self.svc_log.insert(tk.END, f"> PORT {port_check}: KAPALI (Firewall kontrol edin) ⚠️\n")
                                s.close()
                            except Exception as e:
                                self.svc_log.insert(tk.END, f"> Bağlantı testi hatası: {e}\n")
                            
                            self.svc_log.see(tk.END)
                            messagebox.showinfo("Başarılı", "Servis başarıyla kuruldu, başlatıldı ve kontroller tamamlandı.")
                            
                        threading.Thread(target=check_connectivity).start()
                    except:
                        pass
                else:
                    self.svc_log.insert(tk.END, "> [HATA] Servis başlatılamadı! ❌\n")
                    self.after(0, lambda: self.check_service_errors(base_path))
            except Exception as e:
                self.svc_log.insert(tk.END, f"> Beklenmedik Hata: {self.safe_str(e)}\n")

        threading.Thread(target=run).start()

    def kill_uvicorns(self):
        count = 0
        port = self.config_data.get("api_port", "8000")
        import psutil
        
        # Method 1: Search by Name/Cmdline
        for proc in psutil.process_iter(['name', 'cmdline']):
            try:
                info = proc.info
                cmdline = ' '.join(info['cmdline'] or []).lower()
                if "uvicorn" in cmdline or "main:app" in cmdline:
                    proc.kill()
                    count += 1
            except:
                pass
        
        # Method 2: Search by Port (The sure way)
        try:
            # Find PID using port
            result = subprocess.run(['netstat', '-ano'], capture_output=True, text=True)
            for line in result.stdout.splitlines():
                if f":{port}" in line and "LISTENING" in line:
                    parts = line.split()
                    if len(parts) > 4:
                        pid = int(parts[-1])
                        try:
                            p = psutil.Process(pid)
                            p.kill()
                            count += 1
                        except:
                            pass
        except:
            pass
            
        return count

    def check_service_errors(self, api_path):
        self.svc_log.insert(tk.END, "> Hata logları analiz ediliyor...\n")
        log_dir = os.path.join(api_path, "logs")
        
        # Check service-specific logs first - including boot_trace.log
        for log_name in ["boot_trace.log", "service.log", "service_debug.log", "service_stderr.log", "service_stdout.log", "app.log"]:
            log_path = os.path.join(log_dir, log_name)
            if os.path.exists(log_path):
                try:
                    with open(log_path, "r", encoding="utf-8", errors="replace") as f:
                        lines = f.readlines()
                        # Extract last 15 lines
                        relevant = lines[-20:]
                        if relevant:
                            self.svc_log.insert(tk.END, f"--- {log_name} SON KAYITLAR ---\n")
                            for line in relevant:
                                self.svc_log.insert(tk.END, line)
                except:
                    self.svc_log.insert(tk.END, f"> {log_name} okunamadı.\n")
            else:
                self.svc_log.insert(tk.END, f"> {log_name} bulunamadı.\n")

    def create_step_finish(self):
        content = tk.Frame(self.container, bg="white", padx=20, pady=20)
        content.pack(fill="both", expand=True)
        
        tk.Label(content, text="Kurulum Tamamlandı", font=("Segoe UI", 14, "bold"), bg="white").pack(anchor="w")
        
        summary = ("Tebrikler! EXFIN API kurulumu başarıyla tamamlandı.\n\n"
                   "• Veritabanı yapılandırması kaydedildi.\n"
                   "• .env dosyası oluşturuldu.\n"
                   "• Windows Servisi (ExfinOPS_ApiService) kuruldu ve başlatıldı.\n\n"
                   "Artık EXFIN Ops Transformation platformunu kullanmaya başlayabilirsiniz.")
        
        tk.Label(content, text=summary, bg="white", justify="left", font=("Segoe UI", 10)).pack(anchor="w", pady=20)

    def finish_setup(self):
        # 1. Update Config Data from UI
        for key, ent in self.ui_entries.items():
            val = ent.get()
            if " - " in val and (key.endswith("_firma") or key.endswith("_donem")):
                val = val.split(" - ")[0].strip()
            self.config_data[key] = val
            
        # 2. Save to exfin.db (Single Source of Truth)
        try:
            import sqlite3
            sql_conn = sqlite3.connect("exfin.db")
            sql_cur = sql_conn.cursor()
            sql_cur.execute("CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)")
            sql_cur.execute('''CREATE TABLE IF NOT EXISTS api_connections 
                            (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, url TEXT, 
                             db_type TEXT, db_host TEXT, db_port TEXT, db_name TEXT, 
                             db_user TEXT, db_pwd TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
            
            # Global Settings
            gs = {
                "Api_Port": self.config_data.get("api_port", "8000"),
                "Streamlit_Port": "8501", 
                "DeveloperMode": "True",
                "UseHTTPS": "False",
                "Default": "PostgreSQLDatabase"
            }
            for k, v in gs.items():
                sql_cur.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (k, str(v)))
            
            # Save Connections (ID 1 for Postgres, ID 2 for Logo)
            sql_cur.execute("INSERT OR REPLACE INTO api_connections (id, name, url, db_type, db_host, db_port, db_name, db_user, db_pass) VALUES (1, ?, ?, ?, ?, ?, ?, ?, ?)",
                          ("Postgres_Main", "localhost", "PostgreDatabase", 
                           self.config_data.get("pg_host"), self.config_data.get("pg_port"), 
                           self.config_data.get("pg_db"), self.config_data.get("pg_user"), self.config_data.get("pg_pass")))
            
            sql_cur.execute("INSERT OR REPLACE INTO api_connections (id, name, url, db_type, db_host, db_port, db_name, db_user, db_pass) VALUES (2, ?, ?, ?, ?, ?, ?, ?, ?)",
                          ("LOGO_Database", ".", "MSSQLDatabase", 
                           self.config_data.get("ms_host"), "1433", 
                           self.config_data.get("ms_db"), self.config_data.get("ms_user"), self.config_data.get("ms_pass")))
            
            sql_conn.commit()
            sql_conn.close()
        except Exception as e:
            print(f"SQLite Save Error: {e}")

        # 3. Save db_config.json (Mirror for compatibility)
        try:
            if os.path.exists("db_config.json"):
                with open("db_config.json", "r", encoding="utf-8") as f:
                    db_config = json.load(f)
            else:
                db_config = [{"DeveloperMode": True, "UseHTTPS": False, "Api_Port": 8000, "Default": "PostgreSQLDatabase"}, 
                             {"Type": "PostgreSQL", "Name": "Postgres_Main"}, 
                             {"Type": "MSSQL", "Name": "LOGO_Database"}]
            
            for item in db_config:
                if item.get("Type") == "PostgreSQL":
                    item["Server"] = self.config_data["pg_host"]
                    item["Port"] = int(self.config_data["pg_port"])
                    item["Database"] = self.config_data["pg_db"]
                    item["Username"] = self.config_data["pg_user"]
                    item["Password"] = self.config_data["pg_pass"]
                elif (item.get("Type") == "MSSQL" and item.get("Name") == "LOGO_Database") or item.get("Name") == "LOGO_Database":
                    item["Server"] = self.config_data["ms_host"]
                    item["Database"] = self.config_data["ms_db"]
                    item["Username"] = self.config_data["ms_user"]
                    item["Password"] = self.config_data["ms_pass"]
                    item["FirmaNo"] = self.config_data["ms_firma"]
                    item["DonemNo"] = self.config_data["ms_donem"]
                    item["ConnectionType"] = self.ui_entries["ms_conn_type"].get()
            
            with open("db_config.json", "w", encoding="utf-8") as f:
                json.dump(db_config, f, indent=2, ensure_ascii=False)
            
            # 3. Save .env file
            with open(".env", "w", encoding="utf-8") as f:
                f.write(f"DATABASE_URL=postgresql://{self.config_data['pg_user']}:{self.config_data['pg_pass']}@{self.config_data['pg_host']}:{self.config_data['pg_port']}/{self.config_data['pg_db']}\n")
                f.write("SECRET_KEY=exfin_ops_transformation_v4_secret_key\n")
                f.write("ALGORITHM=HS256\n")
                f.write("ACCESS_TOKEN_EXPIRE_MINUTES=43200\n")
                f.write(f"API_PORT={self.config_data.get('api_port', '8000')}\n")
                f.write(f"LOG_LEVEL=INFO\n")

            messagebox.showinfo("Tamamlandı", "Yapılandırma başarıyla kaydedildi! .env ve db_config.json güncellendi.\n\nEXFIN API çalışmaya hazır.")
            self.destroy()
        except Exception as e:
            messagebox.showerror("Hata", f"Kaydetme sırasında hata oluştu: {self.safe_str(e)}")

if __name__ == "__main__":
    try:
        app = SetupWizard()
        app.mainloop()
    except Exception as e:
        import traceback
        error_msg = traceback.format_exc()
        with open("wizard_crash.log", "w", encoding="utf-8") as f:
            f.write(error_msg)
        # Also try to show message box if tk is available
        try:
            import tkinter.messagebox
            tkinter.messagebox.showerror("Wizard Hatası", f"Sihirbaz başlatılamadı.\nDetaylar wizard_crash.log dosyasında.\n\n{str(e)}")
        except: pass
