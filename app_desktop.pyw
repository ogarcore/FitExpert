import customtkinter as ctk
from tkinter import messagebox, filedialog
import os
import json
from pathlib import Path
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import platform
import subprocess

from auth import login, register, validate_session
from database import save_profile, get_user_history, get_progress_summary, get_last_session
from user_profile import (
    UserProfile, OBJECTIVE_LABELS, ACTIVITY_LABELS,
    DIET_TYPES, ALLERGY_OPTIONS, INJURY_OPTIONS, EQUIPMENT_OPTIONS,
    INJURY_SEVERITY_OPTIONS, INTOLERANCE_OPTIONS, PREFERENCE_OPTIONS,
    INJURY_RED_FLAGS, LEGACY_ALLERGY_MAP,
)
from validation import validate_evaluation
from knowledge_base import RULES, TIER_LABELS
from inference_engine import InferenceEngine
from nutrition import generate_nutrition_plan
from training import generate_training_plan
from pdf_exporter import export_pdf

# Configuración premium
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("green")

# Paleta de colores personalizada
BG_COLOR = "#0F172A"       # Slate 900
CARD_COLOR = "#1E293B"     # Slate 800
ACCENT_COLOR = "#10B981"   # Emerald 500
ACCENT_HOVER = "#059669"   # Emerald 600
TEXT_MAIN = "#F8FAFC"      # Slate 50
TEXT_MUTED = "#94A3B8"     # Slate 400
DANGER = "#EF4444"         # Red 500
WARN = "#F59E0B"           # Amber 500

# Ruta ABSOLUTA del archivo de sesión: es independiente del directorio de
# trabajo desde el que se lance la app (la v2 usaba una ruta relativa al CWD).
SESSION_DIR = Path(__file__).resolve().parent
SESSION_FILE = SESSION_DIR / "local_session.json"


def _safe_remove(path: Path) -> None:
    """Elimina un archivo sin propagar excepciones de sistema."""
    try:
        path.unlink(missing_ok=True)
    except OSError:
        pass

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("FitExpert — Sistema Experto Fitness")
        self.geometry("1100x760")
        self.minsize(960, 680)
        self.configure(fg_color=BG_COLOR)
        
        self.session = None
        self.current_profile = None
        self.current_motor   = None
        self.current_rutina  = None
        self.current_plan    = None
        self.current_warnings = []
        self._graph_canvas   = None  # evita fugas de figuras Matplotlib
        
        self._check_local_session()
        
        if not self.session:
            self._show_login_screen()

    def _check_local_session(self):
        # La sesión guardada se valida estructuralmente (auth.validate_session):
        # evita que un archivo corrupto o manipulado deje sesiones rotas.
        if SESSION_FILE.exists():
            try:
                data = json.loads(SESSION_FILE.read_text(encoding="utf-8"))
            except Exception:
                _safe_remove(SESSION_FILE)  # archivo corrupto: descartar
                return
            valid = validate_session(data)
            if valid:
                self.session = valid
                self._build_main_app()

    def _save_local_session(self):
        if self.session:
            try:
                SESSION_FILE.write_text(
                    json.dumps(self.session, ensure_ascii=False, indent=2),
                    encoding="utf-8",
                )
            except OSError:
                pass

    def _clear_local_session(self):
        _safe_remove(SESSION_FILE)
            
    # ══════════════════════════════════════════════════════════════════
    # UI HELPER: TOGGLE PASSWORD
    # ══════════════════════════════════════════════════════════════════
    def _create_password_entry(self, parent, placeholder):
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.columnconfigure(0, weight=1)
        
        entry = ctk.CTkEntry(frame, placeholder_text=placeholder, show="*", height=40, font=ctk.CTkFont(size=14))
        entry.grid(row=0, column=0, sticky="ew")
        
        def toggle():
            if entry.cget("show") == "*":
                entry.configure(show="")
                btn.configure(text="Ocultar", text_color=ACCENT_COLOR)
            else:
                entry.configure(show="*")
                btn.configure(text="Mostrar", text_color=TEXT_MUTED)
                
        btn = ctk.CTkButton(frame, text="Mostrar", width=60, height=40, 
                            fg_color=CARD_COLOR, hover_color="#334155", 
                            text_color=TEXT_MUTED, font=ctk.CTkFont(size=13, weight="bold"),
                            command=toggle)
        btn.grid(row=0, column=1, padx=(5, 0))
        return frame, entry

    # ══════════════════════════════════════════════════════════════════
    # PANTALLA DE LOGIN / REGISTRO
    # ══════════════════════════════════════════════════════════════════

    def _show_login_screen(self):
        for w in self.winfo_children():
            w.destroy()

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        outer = ctk.CTkFrame(self, fg_color="transparent")
        outer.grid(sticky="nsew")
        outer.grid_rowconfigure(0, weight=1)
        outer.grid_columnconfigure(0, weight=1)

        card = ctk.CTkFrame(outer, corner_radius=24, width=460, fg_color=CARD_COLOR)
        card.grid(row=0, column=0)
        card.grid_columnconfigure(0, weight=1)
        card.grid_propagate(False)
        card.configure(height=600)

        # Logo / Header
        header = ctk.CTkFrame(card, fg_color="transparent")
        header.grid(row=0, column=0, pady=(40, 20))
        ctk.CTkLabel(header, text="FitExpert", font=ctk.CTkFont(size=36, weight="bold", family="Helvetica")).pack()
        ctk.CTkLabel(header, text="Nutrición y Fitness Inteligente",
                     font=ctk.CTkFont(size=14), text_color=ACCENT_COLOR).pack(pady=(4, 0))

        # Tabs
        self.login_tabview = ctk.CTkTabview(card, width=380, height=400, 
                                            fg_color="transparent",
                                            segmented_button_selected_color=ACCENT_COLOR,
                                            segmented_button_selected_hover_color=ACCENT_HOVER,
                                            segmented_button_unselected_color=CARD_COLOR)
        self.login_tabview.grid(row=1, column=0, padx=30, pady=(0, 20))
        self.login_tabview.add("Iniciar Sesión")
        self.login_tabview.add("Registrarse")

        self._build_login_tab(self.login_tabview.tab("Iniciar Sesión"))
        self._build_register_tab(self.login_tabview.tab("Registrarse"))

    def _build_login_tab(self, tab):
        vcmd_user = (self.register(self._validate_username), '%P')
        
        form = ctk.CTkFrame(tab, fg_color="transparent")
        form.pack(fill="both", expand=True, pady=10)

        ctk.CTkLabel(form, text="Usuario", font=ctk.CTkFont(size=13, weight="bold"), text_color=TEXT_MUTED).pack(anchor="w", pady=(10, 4))
        self.login_user = ctk.CTkEntry(form, placeholder_text="Tu nombre de usuario", height=40,
                                       validate="key", validatecommand=vcmd_user, font=ctk.CTkFont(size=14))
        self.login_user.pack(fill="x", pady=(0, 15))

        ctk.CTkLabel(form, text="Contraseña", font=ctk.CTkFont(size=13, weight="bold"), text_color=TEXT_MUTED).pack(anchor="w", pady=(0, 4))
        _, self.login_pass = self._create_password_entry(form, "Tu contraseña")
        _.pack(fill="x", pady=(0, 25))

        ctk.CTkButton(form, text="Acceder al Panel", height=45, corner_radius=8,
                      font=ctk.CTkFont(size=15, weight="bold"),
                      fg_color=ACCENT_COLOR, hover_color=ACCENT_HOVER,
                      command=self._do_login).pack(fill="x", pady=(10, 0))

    def _build_register_tab(self, tab):
        vcmd_user = (self.register(self._validate_username), '%P')
        
        form = ctk.CTkFrame(tab, fg_color="transparent")
        form.pack(fill="both", expand=True, pady=10)

        ctk.CTkLabel(form, text="Nombre de usuario", font=ctk.CTkFont(size=13, weight="bold"), text_color=TEXT_MUTED).pack(anchor="w", pady=(5, 4))
        self.reg_user = ctk.CTkEntry(form, placeholder_text="Sin espacios (min 3 chars)", height=40,
                                     validate="key", validatecommand=vcmd_user, font=ctk.CTkFont(size=14))
        self.reg_user.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(form, text="Contraseña", font=ctk.CTkFont(size=13, weight="bold"), text_color=TEXT_MUTED).pack(anchor="w", pady=(0, 4))
        _, self.reg_pass = self._create_password_entry(form, "Mín. 4 caracteres")
        _.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(form, text="Confirmar contraseña", font=ctk.CTkFont(size=13, weight="bold"), text_color=TEXT_MUTED).pack(anchor="w", pady=(0, 4))
        _, self.reg_pass2 = self._create_password_entry(form, "Repite tu contraseña")
        _.pack(fill="x", pady=(0, 20))

        ctk.CTkButton(form, text="Crear Cuenta", height=45, corner_radius=8,
                      font=ctk.CTkFont(size=15, weight="bold"),
                      fg_color=ACCENT_COLOR, hover_color=ACCENT_HOVER,
                      command=self._do_register).pack(fill="x")

    def _validate_username(self, P):
        allowed = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_")
        return all(c in allowed for c in P) or P == ""

    def _do_login(self):
        u = self.login_user.get().strip()
        p = self.login_pass.get()
        result = login(u, p)
        if result["ok"]:
            self.session = result
            self._save_local_session()
            try:
                self._build_main_app()
            except Exception as e:
                # Nunca exponer traceback al usuario final (auditoría de UX).
                messagebox.showerror(
                    "Error de interfaz",
                    "No se pudo cargar el panel. Reinicia la aplicación "
                    f"e inténtalo de nuevo.\nDetalle: {e}",
                )
        else:
            messagebox.showerror("Error", result["error"])

    def _do_register(self):
        u  = self.reg_user.get().strip()
        p  = self.reg_pass.get()
        p2 = self.reg_pass2.get()
        if p != p2:
            messagebox.showerror("Error", "Las contraseñas no coinciden.")
            return
        result = register(u, p)
        if result["ok"]:
            messagebox.showinfo("Éxito", f"¡Bienvenido, {result['username']}! Ya puedes iniciar sesión.")
            self.login_tabview.set("Iniciar Sesión")
        else:
            messagebox.showerror("Error", result["error"])

    # ══════════════════════════════════════════════════════════════════
    # APP PRINCIPAL (POST-LOGIN)
    # ══════════════════════════════════════════════════════════════════

    def _build_main_app(self):
        for w in self.winfo_children():
            w.destroy()

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # Barra Lateral Premium
        self.sidebar = ctk.CTkFrame(self, width=240, corner_radius=0, fg_color=CARD_COLOR)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_rowconfigure(7, weight=1)
        self.sidebar.grid_columnconfigure(0, weight=1)

        # Header Sidebar
        brand = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        brand.grid(row=0, column=0, padx=20, pady=(30, 20), sticky="ew")
        ctk.CTkLabel(brand, text="FitExpert", font=ctk.CTkFont(size=26, weight="bold"), text_color=TEXT_MAIN).pack(anchor="w")
        
        user_info = ctk.CTkFrame(brand, fg_color="#334155", corner_radius=8)
        user_info.pack(fill="x", pady=(15, 0))
        ctk.CTkLabel(user_info, text="👤", font=ctk.CTkFont(size=18)).pack(side="left", padx=(10, 5), pady=8)
        ctk.CTkLabel(user_info, text=self.session['username'], font=ctk.CTkFont(size=14, weight="bold")).pack(side="left", pady=8)

        self._sidebar_btns = {}
        nav_items = [
            ("perfil",    "📊 Mi Perfil",            self.show_perfil),
            ("nueva",     "⚡ Nueva Evaluación",     self.show_nueva),
            ("resultados","🎯 Plan Actual",          self.show_resultados_actual),
            ("historial", "🕒 Historial",            self.show_historial),
            ("acerca",    "ℹ️ Acerca de",            self.show_acerca),
        ]
        
        for i, (key, label, cmd) in enumerate(nav_items, start=2):
            btn = ctk.CTkButton(self.sidebar, text=label, height=42, anchor="w",
                                font=ctk.CTkFont(size=14, weight="bold"),
                                corner_radius=8,
                                fg_color="transparent", text_color=TEXT_MUTED,
                                hover_color="#334155",
                                command=cmd)
            btn.grid(row=i, column=0, padx=15, pady=6, sticky="ew")
            self._sidebar_btns[key] = btn

        ctk.CTkButton(self.sidebar, text="Cerrar sesión", height=40,
                      font=ctk.CTkFont(size=13, weight="bold"),
                      fg_color="transparent", border_width=1, border_color="#334155",
                      text_color=DANGER, hover_color="#334155",
                      command=self._logout).grid(row=8, column=0, padx=20, pady=30, sticky="ew")

        # Contenedor Principal
        self.frames = {}
        self.frames["perfil"]     = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.frames["nueva"]      = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.frames["resultados"] = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.frames["historial"]  = ctk.CTkFrame(self, fg_color="transparent")
        self.frames["acerca"]     = ctk.CTkFrame(self, fg_color="transparent")

        self._setup_nueva()
        self._setup_historial()
        self._setup_acerca()

        self.show_perfil()

    def _logout(self):
        self.session = None
        self.current_profile = None
        self._clear_local_session()
        self._show_login_screen()

    def _set_active_btn(self, key):
        for k, btn in self._sidebar_btns.items():
            if k == key:
                btn.configure(fg_color="#334155", text_color=ACCENT_COLOR)
            else:
                btn.configure(fg_color="transparent", text_color=TEXT_MUTED)

    def _show_frame(self, key):
        for frame in self.frames.values():
            frame.grid_forget()
        self.frames[key].grid(row=0, column=1, sticky="nsew", padx=30, pady=30)

    # ── Rutas ─────────────────────────────────────────────────────────

    def show_perfil(self):
        self._set_active_btn("perfil")
        self._render_perfil()
        self._show_frame("perfil")

    def show_nueva(self):
        self._set_active_btn("nueva")
        self._prefill_nueva_consulta()
        self._show_frame("nueva")

    def show_resultados_actual(self):
        if self.current_profile is None:
            messagebox.showinfo("Sin plan activo", "Debes generar una Nueva Evaluación primero para ver tu plan.")
            return
        self._set_active_btn("resultados")
        self._show_frame("resultados")

    def show_historial(self):
        self._set_active_btn("historial")
        self._update_historial()
        self._show_frame("historial")

    def show_acerca(self):
        self._set_active_btn("acerca")
        self._show_frame("acerca")

    # ══════════════════════════════════════════════════════════════════
    # MI PERFIL
    # ══════════════════════════════════════════════════════════════════

    def _render_perfil(self):
        frame = self.frames["perfil"]
        for w in frame.winfo_children():
            w.destroy()

        header = ctk.CTkFrame(frame, fg_color="transparent")
        header.pack(fill="x", pady=(0, 25))
        ctk.CTkLabel(header, text="Panel General", font=ctk.CTkFont(size=32, weight="bold")).pack(anchor="w")
        ctk.CTkLabel(header, text="Resumen de tu progreso y estado físico.",
                     font=ctk.CTkFont(size=14), text_color=TEXT_MUTED).pack(anchor="w")

        last = get_last_session(self.session["user_id"])
        
        if not last:
            card = ctk.CTkFrame(frame, corner_radius=12, fg_color=CARD_COLOR)
            card.pack(fill="x", pady=20)
            ctk.CTkLabel(card, text="Aún no hay datos", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=(30,5))
            ctk.CTkLabel(card, text="Inicia tu transformación creando una nueva evaluación.",
                         text_color=TEXT_MUTED, font=ctk.CTkFont(size=14)).pack(pady=(0,20))
            ctk.CTkButton(card, text="Nueva Evaluación", fg_color=ACCENT_COLOR, hover_color=ACCENT_HOVER,
                          command=self.show_nueva).pack(pady=(0, 30))
            return

        # KPIs Rápidos
        progress = get_progress_summary(self.session["user_id"])
        kpi_frame = ctk.CTkFrame(frame, fg_color="transparent")
        kpi_frame.pack(fill="x", pady=(0, 20))
        
        delta_p = progress["delta_peso_kg"]
        p_color = ACCENT_COLOR if delta_p <= 0 else WARN
        delta_c = progress["delta_calorias"]
        
        self._metric_card(kpi_frame, "Evaluaciones", str(progress["sesiones"]), "Totales", "#3B82F6").pack(side="left", expand=True, padx=(0, 5))
        self._metric_card(kpi_frame, "Cambio de Peso", f"{'+' if delta_p > 0 else ''}{delta_p:.1f} kg", "Desde inicio", p_color).pack(side="left", expand=True, padx=5)
        self._metric_card(kpi_frame, "Ajuste Calórico", f"{'+' if delta_c > 0 else ''}{delta_c:.0f} kcal", "Variación", "#8B5CF6").pack(side="left", expand=True, padx=(5, 0))

        # Layout Columnas (Info Actual | Grafica)
        col_frame = ctk.CTkFrame(frame, fg_color="transparent")
        col_frame.pack(fill="both", expand=True)
        col_frame.columnconfigure(0, weight=1)
        col_frame.columnconfigure(1, weight=2)

        # Info Actual
        info_card = ctk.CTkFrame(col_frame, corner_radius=12, fg_color=CARD_COLOR)
        info_card.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        
        ctk.CTkLabel(info_card, text="Métricas Actuales", font=ctk.CTkFont(size=18, weight="bold")).pack(anchor="w", padx=25, pady=(25, 15))
        
        fields = [
            ("Edad", f"{last.get('age', 0)} años"),
            ("Peso", f"{last.get('weight', 0):.1f} kg"),
            ("Altura", f"{last.get('height', 0):.0f} cm"),
            ("Grasa", f"{last.get('body_fat_pct', 0):.1f} %" if last.get('body_fat_pct', 0) > 0 else "—"),
            ("IMC", f"{last.get('imc', 0):.1f}"),
        ]

        for label, val in fields:
            row = ctk.CTkFrame(info_card, fg_color="transparent")
            row.pack(fill="x", padx=25, pady=8)
            ctk.CTkLabel(row, text=label, font=ctk.CTkFont(size=14, weight="bold"), text_color=TEXT_MUTED).pack(side="left")
            ctk.CTkLabel(row, text=val, font=ctk.CTkFont(size=15, weight="bold"), text_color=TEXT_MAIN).pack(side="right")

        # Gráfica Matplotlib
        graph_card = ctk.CTkFrame(col_frame, corner_radius=12, fg_color=CARD_COLOR)
        graph_card.grid(row=0, column=1, sticky="nsew", padx=(10, 0))
        
        ctk.CTkLabel(graph_card, text="Evolución de Peso", font=ctk.CTkFont(size=18, weight="bold")).pack(anchor="w", padx=25, pady=(25, 10))
        
        self._render_graph(graph_card)

    def _render_graph(self, parent):
        history = get_user_history(self.session["user_id"])
        if len(history) < 2:
            ctk.CTkLabel(parent, text="Necesitas al menos 2 evaluaciones para visualizar la gráfica.", 
                         text_color=TEXT_MUTED).pack(expand=True, pady=40)
            return

        # Cerrar la figura anterior ANTES de crear una nueva: evita fugas de
        # memoria por figuras Matplotlib acumuladas en cada re-render (auditoría).
        if self._graph_canvas is not None:
            try:
                self._graph_canvas.get_tk_widget().destroy()
                plt.close(self._graph_canvas.figure)
            except Exception:
                pass
            self._graph_canvas = None

        fechas = [h.get("saved_at", "").split(" ")[0] for h in history]
        pesos = [h.get("weight", 0) for h in history]

        fig, ax = plt.subplots(figsize=(5, 3), dpi=100)
        fig.patch.set_facecolor(CARD_COLOR)
        ax.set_facecolor(CARD_COLOR)
        
        ax.plot(fechas, pesos, color=ACCENT_COLOR, marker='o', linewidth=2, markersize=6)
        ax.tick_params(colors=TEXT_MUTED, labelsize=9)
        for spine in ax.spines.values():
            spine.set_color('#334155')
        
        ax.set_ylabel("Peso (kg)", color=TEXT_MUTED, fontsize=10)
        plt.xticks(rotation=15)
        plt.tight_layout()

        canvas = FigureCanvasTkAgg(fig, master=parent)
        self._graph_canvas = canvas
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=15, pady=(0, 15))


    def _metric_card(self, parent, title, main_val, sub_val, main_color="white"):
        card = ctk.CTkFrame(parent, corner_radius=12, fg_color=CARD_COLOR)
        ctk.CTkLabel(card, text=title, font=ctk.CTkFont(size=13, weight="bold"),
                     text_color=TEXT_MUTED).pack(pady=(16, 0))
        ctk.CTkLabel(card, text=main_val, font=ctk.CTkFont(size=28, weight="bold"),
                     text_color=main_color).pack(pady=(2, 0))
        ctk.CTkLabel(card, text=sub_val, font=ctk.CTkFont(size=12), text_color=TEXT_MUTED).pack(pady=(0, 16))
        return card

    # ══════════════════════════════════════════════════════════════════
    # NUEVA CONSULTA
    # ══════════════════════════════════════════════════════════════════

    def _setup_nueva(self):
        frame = self.frames["nueva"]

        header = ctk.CTkFrame(frame, fg_color="transparent")
        header.pack(fill="x", pady=(0, 20))
        ctk.CTkLabel(header, text="Nueva Evaluación", font=ctk.CTkFont(size=32, weight="bold")).pack(anchor="w")
        ctk.CTkLabel(header, text="Actualiza tus datos para generar un nuevo plan ajustado a ti.",
                     font=ctk.CTkFont(size=14), text_color=TEXT_MUTED).pack(anchor="w")

        vcmd_int   = (self.register(self._vi), '%P')
        vcmd_float = (self.register(self._vf), '%P')

        # ── SECCIÓN 1: Datos Físicos
        card1 = self._section_card(frame, "Datos Físicos")
        row1 = ctk.CTkFrame(card1, fg_color="transparent")
        row1.pack(fill="x", pady=10)
        
        self.ent_edad = self._add_input(row1, "Edad (años)", "Ej: 25", vcmd_int, side="left")
        self.opt_sexo = self._add_dropdown(row1, "Sexo", ["Masculino", "Femenino"], side="right")

        row2 = ctk.CTkFrame(card1, fg_color="transparent")
        row2.pack(fill="x", pady=10)
        
        self.ent_peso = self._add_input(row2, "Peso (kg)", "Ej: 75.5", vcmd_float, side="left")
        self.ent_altura = self._add_input(row2, "Altura (cm)", "Ej: 175", vcmd_int, side="right")

        row3 = ctk.CTkFrame(card1, fg_color="transparent")
        row3.pack(fill="x", pady=10)
        self.ent_grasa = self._add_input(row3, "% Grasa corporal (opcional)", "Ej: 18.5", vcmd_float, side="left")

        # ── SECCIÓN 2: Objetivos y Entrenamiento
        card2 = self._section_card(frame, "Objetivo y Entrenamiento")
        r2_1 = ctk.CTkFrame(card2, fg_color="transparent")
        r2_1.pack(fill="x", pady=10)
        
        self.obj_vals = list(OBJECTIVE_LABELS.values())
        self.opt_obj = self._add_dropdown(r2_1, "Objetivo", self.obj_vals, side="left")
        self.act_vals = list(ACTIVITY_LABELS.values())
        self.opt_act = self._add_dropdown(r2_1, "Actividad Diaria", self.act_vals, side="right")

        r2_2 = ctk.CTkFrame(card2, fg_color="transparent")
        r2_2.pack(fill="x", pady=10)
        self.opt_exp = self._add_dropdown(r2_2, "Experiencia", ["Principiante", "Intermedio", "Avanzado"], side="left")
        self.opt_lugar = self._add_dropdown(r2_2, "Lugar de Entrenamiento", ["Gimnasio", "Casa"], side="right", command=self._on_lugar_change)

        # ── SECCIÓN 3: Lesiones y Equipo
        card3 = self._section_card(frame, "Consideraciones Físicas y Equipo")
        ctk.CTkLabel(card3, text="Zonas con molestia o lesión:", font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w", pady=(10, 5))

        les_f1 = ctk.CTkFrame(card3, fg_color="transparent")
        les_f1.pack(fill="x", pady=(2, 2))
        les_f2 = ctk.CTkFrame(card3, fg_color="transparent")
        les_f2.pack(fill="x", pady=(2, 8))
        self.inj_vars = {}
        _inj_items = list(INJURY_OPTIONS.items())
        for i, (key, lbl) in enumerate(_inj_items):
            var = ctk.BooleanVar()
            self.inj_vars[key] = var
            row = les_f1 if i < (len(_inj_items) + 1) // 2 else les_f2
            ctk.CTkCheckBox(row, text=lbl, variable=var, fg_color=ACCENT_COLOR).pack(side="left", padx=(0, 12))

        sev_row = ctk.CTkFrame(card3, fg_color="transparent")
        sev_row.pack(fill="x", pady=(0, 8))
        ctk.CTkLabel(sev_row, text="Intensidad de las molestias:", font=ctk.CTkFont(size=13, weight="bold"), text_color=TEXT_MUTED).pack(side="left", padx=(0, 12))
        self.sev_vals = list(INJURY_SEVERITY_OPTIONS.values())
        self.opt_sev = ctk.CTkOptionMenu(sev_row, values=self.sev_vals, height=32,
                                         font=ctk.CTkFont(size=13), fg_color="#334155",
                                         button_color="#475569", button_hover_color=ACCENT_COLOR)
        self.opt_sev.pack(side="left")
        self.opt_sev.set("Ninguna")

        self.chk_balance = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(card3, text="Problemas de equilibrio / historial de caídas",
                        variable=self.chk_balance, fg_color=ACCENT_COLOR).pack(anchor="w", pady=(0, 10))

        ctk.CTkLabel(card3, text="Señales de alarma (suspenden la prescripción de ejercicio):",
                     font=ctk.CTkFont(size=13, weight="bold"), text_color=DANGER).pack(anchor="w", pady=(10, 5))
        rf_f1 = ctk.CTkFrame(card3, fg_color="transparent")
        rf_f1.pack(fill="x", pady=(2, 2))
        rf_f2 = ctk.CTkFrame(card3, fg_color="transparent")
        rf_f2.pack(fill="x", pady=(2, 10))
        self.rf_vars = {}
        _rf_items = list(INJURY_RED_FLAGS.items())
        for i, (key, lbl) in enumerate(_rf_items):
            var = ctk.BooleanVar()
            self.rf_vars[key] = var
            row = rf_f1 if i < (len(_rf_items) + 1) // 2 else rf_f2
            ctk.CTkCheckBox(row, text=lbl, variable=var, fg_color=ACCENT_COLOR).pack(side="left", padx=(0, 12))

        ctk.CTkLabel(card3, text="Equipo en casa:", font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w", pady=(10, 5))
        eq_f = ctk.CTkFrame(card3, fg_color="transparent")
        eq_f.pack(fill="x", pady=(0, 10))
        self.eq_vars = {}
        self.eq_checkboxes = []
        # Clave normalizada "bandas_elasticas" (la v2 usaba "bandas_elásticas").
        for key, lbl in {"mancuernas": "Mancuernas", "bandas_elasticas": "Bandas elásticas",
                         "barra_dominadas": "Barra de dominadas", "kettlebell": "Kettlebell"}.items():
            var = ctk.BooleanVar()
            self.eq_vars[key] = var
            cb = ctk.CTkCheckBox(eq_f, text=lbl, variable=var, fg_color=ACCENT_COLOR)
            cb.pack(side="left", padx=(0, 15))
            self.eq_checkboxes.append(cb)

        # ── SECCIÓN 4: Nutrición
        card4 = self._section_card(frame, "Nutrición")
        r4_1 = ctk.CTkFrame(card4, fg_color="transparent")
        r4_1.pack(fill="x", pady=10)
        
        self.diet_vals = list(DIET_TYPES.keys())
        self.diet_labels = list(DIET_TYPES.values())
        self.opt_diet = self._add_dropdown(r4_1, "Tipo de dieta", self.diet_labels, side="left")
        self.opt_freq = self._add_dropdown(r4_1, "Comidas al día", ["3 comidas", "4 comidas", "5 comidas"], side="right")
        self.opt_freq.set("3 comidas")

        ctk.CTkLabel(card4, text="Alergias / Intolerancias:", font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w", pady=(10, 5))
        alg_f = ctk.CTkFrame(card4, fg_color="transparent")
        alg_f.pack(fill="x", pady=(0, 10))
        # Muestra claves legadas (migradas por LEGACY_ALLERGY_MAP a alergias
        # reales / intolerancias; p. ej. "lactosa" es intolerancia, no alergia).
        self.alg_vars = {}
        ALERGIA_UI = {
            "lactosa": "Lactosa (intolerancia)",
            "gluten": "Gluten / celiaquía",
            "nueces": "Frutos secos",
            "soya": "Soja",
            "huevo": "Huevo",
        }
        for key, lbl in ALERGIA_UI.items():
            var = ctk.BooleanVar()
            self.alg_vars[key] = var
            ctk.CTkCheckBox(alg_f, text=lbl, variable=var, fg_color=ACCENT_COLOR).pack(side="left", padx=(0, 12))

        ctk.CTkLabel(card4, text="Preferencias de consumo:", font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w", pady=(10, 5))
        pref_f = ctk.CTkFrame(card4, fg_color="transparent")
        pref_f.pack(fill="x", pady=(0, 10))
        self.pref_vars = {}
        for key, lbl in PREFERENCE_OPTIONS.items():
            var = ctk.BooleanVar()
            self.pref_vars[key] = var
            ctk.CTkCheckBox(pref_f, text=lbl, variable=var, fg_color=ACCENT_COLOR).pack(side="left", padx=(0, 12))

        # ── Botón
        self._on_lugar_change(self.opt_lugar.get())
        self.btn_generar = ctk.CTkButton(frame, text="✨ Generar Plan Personalizado",
                      height=55, corner_radius=12,
                      font=ctk.CTkFont(size=16, weight="bold"),
                      fg_color=ACCENT_COLOR, hover_color=ACCENT_HOVER,
                      command=self._procesar)
        self.btn_generar.pack(fill="x", pady=(20, 40))

    def _section_card(self, parent, title):
        card = ctk.CTkFrame(parent, corner_radius=12, fg_color=CARD_COLOR)
        card.pack(fill="x", pady=10)
        header = ctk.CTkFrame(card, fg_color="transparent")
        header.pack(fill="x", padx=25, pady=(20, 5))
        ctk.CTkLabel(header, text=title, font=ctk.CTkFont(size=18, weight="bold"), text_color=TEXT_MAIN).pack(anchor="w")
        ctk.CTkFrame(card, height=1, fg_color="#334155").pack(fill="x", padx=25, pady=(5, 10))
        content = ctk.CTkFrame(card, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=25, pady=(0, 20))
        return content

    def _add_input(self, parent, label, placeholder, vcmd, side):
        f = ctk.CTkFrame(parent, fg_color="transparent")
        f.pack(side=side, fill="x", expand=True, padx=(0 if side=="left" else 10, 10 if side=="left" else 0))
        ctk.CTkLabel(f, text=label, font=ctk.CTkFont(size=13, weight="bold"), text_color=TEXT_MUTED).pack(anchor="w", pady=(0, 4))
        ent = ctk.CTkEntry(f, placeholder_text=placeholder, height=40, font=ctk.CTkFont(size=14), validate="key", validatecommand=vcmd)
        ent.pack(fill="x")
        return ent

    def _add_dropdown(self, parent, label, values, side, command=None):
        f = ctk.CTkFrame(parent, fg_color="transparent")
        f.pack(side=side, fill="x", expand=True, padx=(0 if side=="left" else 10, 10 if side=="left" else 0))
        ctk.CTkLabel(f, text=label, font=ctk.CTkFont(size=13, weight="bold"), text_color=TEXT_MUTED).pack(anchor="w", pady=(0, 4))
        opt = ctk.CTkOptionMenu(f, values=values, height=40, font=ctk.CTkFont(size=14), fg_color="#334155", button_color="#475569", button_hover_color=ACCENT_COLOR, command=command)
        opt.pack(fill="x")
        return opt

    def _on_lugar_change(self, choice):
        estado = "normal" if choice == "Casa" else "disabled"
        for checkbox in self.eq_checkboxes:
            checkbox.configure(state=estado)
            if choice == "Gimnasio":
                checkbox.deselect()

    def _prefill_nueva_consulta(self):
        last = get_last_session(self.session["user_id"])
        if not last: return
        self.ent_edad.delete(0, "end")
        self.ent_edad.insert(0, str(last.get("age", "")))
        self.ent_peso.delete(0, "end")
        self.ent_peso.insert(0, str(last.get("weight", "")))
        self.ent_altura.delete(0, "end")
        self.ent_altura.insert(0, str(last.get("height", "")))
        self.ent_grasa.delete(0, "end")
        if last.get("body_fat_pct", 0) > 0:
            self.ent_grasa.insert(0, str(last.get("body_fat_pct")))

        self.opt_sexo.set("Masculino" if last.get("sex", "masculino") == "masculino" else "Femenino")
        if last.get("objective") in OBJECTIVE_LABELS: self.opt_obj.set(OBJECTIVE_LABELS[last.get("objective")])
        if last.get("activity_level") in ACTIVITY_LABELS: self.opt_act.set(ACTIVITY_LABELS[last.get("activity_level")])
        self.opt_exp.set(last.get("experience", "principiante").capitalize())
        lugar = "Gimnasio" if last.get("training_place", "gimnasio") == "gimnasio" else "Casa"
        self.opt_lugar.set(lugar)
        self._on_lugar_change(lugar)
        if last.get("diet_type") in DIET_TYPES: self.opt_diet.set(DIET_TYPES[last.get("diet_type")])
        self.opt_freq.set(f"{last.get('meal_frequency', 3)} comidas")

        for k, v in self.inj_vars.items(): v.set(k in last.get("injuries", []))
        sev = last.get("injury_severity", "ninguna")
        if sev in INJURY_SEVERITY_OPTIONS:
            self.opt_sev.set(INJURY_SEVERITY_OPTIONS[sev])
        self.chk_balance.set(bool(last.get("balance_issues", False)))
        for k, v in self.rf_vars.items(): v.set(k in last.get("red_flags", []))
        for k, v in self.eq_vars.items(): v.set(k in last.get("equipment", []))
        for k, v in self.alg_vars.items():
            mapped = LEGACY_ALLERGY_MAP.get(k)
            if not mapped:
                continue
            kind, key = mapped
            contenedor = last.get("allergies", []) if kind == "allergies" else last.get("intolerances", [])
            v.set(key in contenedor)
        for k, v in self.pref_vars.items(): v.set(k in last.get("preferences", []))

    def _vi(self, P): return P == "" or P.isdigit()
    def _vf(self, P):
        if P in ("", "."): return True
        try: float(P); return True
        except ValueError: return False

    def _procesar(self):
        # Estado de carga (micro-interacción): botón deshabilitado mientras se infiere
        self.btn_generar.configure(state="disabled", text="⏳ Analizando perfil con el motor…")
        self.btn_generar.update_idletasks()
        try:
            nombre = self.session["username"]

            data = {
                "name": nombre,
                "age": self.ent_edad.get() or "",
                "sex": "masculino" if self.opt_sexo.get() == "Masculino" else "femenino",
                "weight": self.ent_peso.get() or "",
                "height": self.ent_altura.get() or "",
                "body_fat_pct": self.ent_grasa.get() or "",
                "objective": list(OBJECTIVE_LABELS.keys())[self.obj_vals.index(self.opt_obj.get())],
                "activity_level": list(ACTIVITY_LABELS.keys())[self.act_vals.index(self.opt_act.get())],
                "experience": self.opt_exp.get().lower(),
                "training_place": "gimnasio" if self.opt_lugar.get() == "Gimnasio" else "casa",
                "diet_type": self.diet_vals[self.diet_labels.index(self.opt_diet.get())],
                "meal_frequency": int(self.opt_freq.get()[0]),
                "injuries": [k for k, v in self.inj_vars.items() if v.get()],
                "injuries_labels": [],
                "injury_severity": list(INJURY_SEVERITY_OPTIONS.keys())[self.sev_vals.index(self.opt_sev.get())],
                "balance_issues": bool(self.chk_balance.get()),
                "red_flags": [k for k, v in self.rf_vars.items() if v.get()],
                "equipment": [k for k, v in self.eq_vars.items() if v.get()],
                "allergies": [],
                "intolerances": [],
                "preferences": [k for k, v in self.pref_vars.items() if v.get()],
            }
            if data["training_place"] == "gimnasio":
                data["equipment"] = []

            # Migración de claves legadas → alergias reales / intolerancias
            for k, v in self.alg_vars.items():
                if not v.get():
                    continue
                mapped = LEGACY_ALLERGY_MAP.get(k)
                if mapped:
                    kind, key = mapped
                    (data["allergies"] if kind == "allergies" else data["intolerances"]).append(key)
                else:
                    data["allergies"].append(k)

            values, errores, advertencias = validate_evaluation(data)
            if errores:
                detalle = "\n".join(f"• {campo.capitalize()}: {msg}" for campo, msg in errores.items())
                messagebox.showerror(
                    "Datos no válidos",
                    "Revisa los siguientes campos:\n\n" + detalle,
                )
                return

            perfil = UserProfile(**values)
            perfil.user_id = self.session["user_id"]

            motor  = InferenceEngine()
            motor.run(perfil)
            rutina = generate_training_plan(perfil)
            plan   = generate_nutrition_plan(perfil)
            save_profile(perfil)

            self.current_profile = perfil
            self.current_motor   = motor
            self.current_rutina  = rutina
            self.current_plan    = plan
            self.current_warnings = advertencias

            self._render_resultados()
            self._set_active_btn("resultados")
            self._show_frame("resultados")

        except Exception as e:
            # Nunca mostrar un traceback: mensaje amigable y reproducible.
            messagebox.showerror(
                "Error inesperado",
                f"Ocurrió un error al generar el plan.\nDetalle: {e}",
            )
        finally:
            self.btn_generar.configure(state="normal", text="✨ Generar Plan Personalizado")

    # ══════════════════════════════════════════════════════════════════
    # RESULTADOS
    # ══════════════════════════════════════════════════════════════════

    def _render_resultados(self):
        frame = self.frames["resultados"]
        for w in frame.winfo_children(): w.destroy()

        p = self.current_profile
        plan = self.current_plan
        rutina = self.current_rutina

        # Header interactivo
        header = ctk.CTkFrame(frame, fg_color="transparent")
        header.pack(fill="x", pady=(0, 25))
        header.columnconfigure(0, weight=1)

        ctk.CTkLabel(header, text="Plan Generado", font=ctk.CTkFont(size=32, weight="bold"), text_color=ACCENT_COLOR).grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(header, text=f"{p.name} • {p.created_at}", font=ctk.CTkFont(size=14), text_color=TEXT_MUTED).grid(row=1, column=0, sticky="w")

        btns = ctk.CTkFrame(header, fg_color="transparent")
        btns.grid(row=0, column=1, rowspan=2, sticky="e")
        ctk.CTkButton(btns, text="⚙️ Lógica de IA", width=140, height=40, fg_color="#334155", hover_color="#475569", command=self._show_motor_window).pack(side="left", padx=(0, 10))
        ctk.CTkButton(btns, text="📄 Descargar PDF", width=140, height=40, fg_color="#EF4444", hover_color="#DC2626", font=ctk.CTkFont(weight="bold"), command=self._export_pdf).pack(side="left")

        # Suspensión por señales de alarma / lesión aguda (máxima prominencia)
        if p.red_flags or p.injury_severity == "aguda":
            susp = ctk.CTkFrame(frame, fg_color="#450A0A", corner_radius=8)
            susp.pack(fill="x", pady=(0, 15))
            ctk.CTkLabel(
                susp,
                text="🛑 SUSPENSIÓN DE PRESCRIPCIÓN: por señales de alarma o lesión "
                     "aguda, FitExpert no prescribe ejercicio. Consulta a un profesional "
                     "de la salud antes de retomar la actividad física.",
                text_color="#FECACA", font=ctk.CTkFont(size=13, weight="bold"),
                wraplength=820,
            ).pack(pady=10)

        # Advertencias de validación cruzada (IMC, franja de edad, etc.)
        if self.current_warnings:
            warn = ctk.CTkFrame(frame, fg_color="#78350F", corner_radius=8)
            warn.pack(fill="x", pady=(0, 15))
            warned_texto = "ℹ️ Consideraciones:\n" + "\n".join("  • " + w for w in self.current_warnings)
            ctk.CTkLabel(warn, text=warned_texto, text_color="#FDE68A",
                         font=ctk.CTkFont(size=12), justify="left").pack(anchor="w", pady=8, padx=12)

        # KPIs
        mf = ctk.CTkFrame(frame, fg_color="transparent")
        mf.pack(fill="x", pady=(0, 25))
        imc_color = ACCENT_COLOR if 18.5 <= p.imc <= 24.9 else WARN if p.imc < 18.5 else DANGER
        self._metric_card(mf, "IMC", f"{p.imc:.1f}", p.imc_category, imc_color).pack(side="left", fill="x", expand=True, padx=(0, 5))
        self._metric_card(mf, "TMB", f"{p.tmb:.0f}", "kcal (reposo)").pack(side="left", fill="x", expand=True, padx=5)
        self._metric_card(mf, "TDEE", f"{p.tdee:.0f}", "kcal (gasto)").pack(side="left", fill="x", expand=True, padx=5)
        self._metric_card(mf, "Meta Diaria", f"{p.target_calories:.0f}", "kcal objetivo", "#3B82F6").pack(side="left", fill="x", expand=True, padx=(5, 0))

        # Tabs Content
        tabs = ctk.CTkTabview(frame, height=500, fg_color=CARD_COLOR, 
                              segmented_button_selected_color=ACCENT_COLOR,
                              segmented_button_selected_hover_color=ACCENT_HOVER,
                              segmented_button_unselected_color="#334155")
        tabs.pack(fill="both", expand=True)
        tabs.add("🍏 Nutrición")
        tabs.add("💪 Entrenamiento")

        # NUTRICION
        t_nut = tabs.tab("🍏 Nutrición")
        m = plan["macros"]
        m_frame = ctk.CTkFrame(t_nut, fg_color="#334155", corner_radius=8)
        m_frame.pack(fill="x", padx=15, pady=15)
        ctk.CTkLabel(m_frame, text=f"🥩 Proteínas: {m['proteinas']}g ({m['p_pct']}%)   |   🍞 Carbohidratos: {m['carbohidratos']}g ({m['c_pct']}%)   |   🥑 Grasas: {m['grasas']}g ({m['g_pct']}%)",
                     font=ctk.CTkFont(size=14, weight="bold")).pack(pady=10)

        tb_nut = ctk.CTkTextbox(t_nut, wrap="word", font=ctk.CTkFont(size=14, family="Helvetica"), fg_color="transparent")
        tb_nut.pack(fill="both", expand=True, padx=15, pady=(0, 15))
        
        txt = ""
        for label, key in [("🍳 DESAYUNO", "desayuno"), ("🍱 ALMUERZO", "almuerzo"), ("🍽️ CENA", "cena"), ("🍎 SNACKS", "snacks")]:
            if plan["plan"].get(key):
                txt += f"{label}\n" + "\n".join([f" • {x}" for x in plan["plan"][key]]) + "\n\n"
        txt += f"💧 HIDRATACIÓN: {plan['plan'].get('hidratacion', '')}"
        if plan.get("sustituciones"):
            txt += "\n\n🔁 SUSTITUCIONES POR ALERGIAS:\n"
            for s in plan["sustituciones"]:
                al = ALLERGY_OPTIONS.get(s.get("alergeno", ""), s.get("alergeno", ""))
                txt += f" • {al}: {s.get('substitucion', '')}\n"
            txt += "⚠️ La seguridad frente a contaminación cruzada depende de leer las etiquetas.\n"
        tb_nut.insert("0.0", txt)
        tb_nut.configure(state="disabled")

        # ENTRENAMIENTO
        t_trn = tabs.tab("💪 Entrenamiento")
        t_header = ctk.CTkFrame(t_trn, fg_color="#334155", corner_radius=8)
        t_header.pack(fill="x", padx=15, pady=15)
        ctk.CTkLabel(t_header, text=f"{rutina['nombre'].upper()}", font=ctk.CTkFont(size=16, weight="bold"), text_color="#60A5FA").pack(pady=(10, 2))
        ctk.CTkLabel(t_header, text=f"{rutina['tipo']}  •  {rutina['dias']}", font=ctk.CTkFont(size=13)).pack(pady=(0, 10))

        tb_trn = ctk.CTkTextbox(t_trn, wrap="word", font=ctk.CTkFont(size=14, family="Helvetica"), fg_color="transparent")
        tb_trn.pack(fill="both", expand=True, padx=15, pady=(0, 15))
        
        trn_txt = ""
        for day in rutina.get("semana", []):
            if day["descanso"]:
                trn_txt += f"■ {day['dia'].upper()} - Descanso\n\n"
            else:
                trn_txt += f"■ {day['dia'].upper()} - {day['grupo']}\n"
                for ej in day.get("ejercicios", []):
                    trn_txt += f"  • {ej[0]}: {ej[1]} [{ej[2]}]\n"
                trn_txt += f"  (⏱ {day['descanso_entre_series']} descanso)\n\n"
        if rutina.get("lesiones_consideradas"):
            trn_txt += "🩹 Restricciones por lesión: " + ", ".join(rutina["lesiones_consideradas"]) + "\n\n"
        if rutina.get("alternativas_aplicadas"):
            trn_txt += "🔁 SUSTITUCIONES POR LESIÓN:\n" + "\n".join(f" • {a}" for a in rutina["alternativas_aplicadas"]) + "\n\n"
        if rutina.get("cardio_extra"):
            trn_txt += f"🏃 Cardio: {rutina['cardio_extra']}\n"
        tb_trn.insert("0.0", trn_txt)
        tb_trn.configure(state="disabled")

    def _show_motor_window(self):
        if not self.current_motor: return
        top = ctk.CTkToplevel(self)
        top.title("Inteligencia Artificial - Motor de Inferencia")
        top.geometry("780x600")
        top.configure(fg_color=BG_COLOR)
        top.attributes('-topmost', True)
        
        ctk.CTkLabel(top, text="Transparencia del Sistema Experto", font=ctk.CTkFont(size=22, weight="bold")).pack(pady=(20, 5))
        resumen = (f"Reglas activadas: {len(self.current_motor.fired_rules)} / "
                   f"{len(self.current_motor.rules)}  ·  Suprimidas: "
                   f"{len(self.current_profile.suppressed)}  ·  Errores: "
                   f"{len(self.current_profile.engine_errors)}")
        ctk.CTkLabel(top, text=resumen, text_color=ACCENT_COLOR).pack(pady=(0, 20))
        
        tb = ctk.CTkTextbox(top, wrap="word", font=ctk.CTkFont(size=13, family="Consolas"), fg_color=CARD_COLOR, corner_radius=12)
        tb.pack(fill="both", expand=True, padx=25, pady=(0, 25))

        _sev_order = {"critica": 0, "alta": 1, "media": 2, "baja": 3, "info": 4}
        txt = ""

        if self.current_profile.red_flags or self.current_profile.injury_severity == "aguda":
            txt += "🛑 SUSPENSIÓN POR SEÑALES DE ALARMA / LESIÓN AGUDA\n"
            txt += "   → Deriva a consulta profesional: no se prescribe ejercicio.\n\n"

        for c in sorted(self.current_profile.conclusions,
                        key=lambda c: _sev_order.get(c.get("severity", "info"), 9)):
            rid = c["id"]
            exp = next((e["explanation"] for e in self.current_profile.explanations if e["id"] == rid), "")
            sev = c.get("severity", "info").upper()
            txt += f"[{rid}] ({sev}) {c['conclusion']}\n    ↳ {exp}\n\n"
        if not self.current_profile.conclusions:
            txt += "No se activaron reglas específicas para este perfil.\n"

        if self.current_profile.suppressed:
            txt += "\n🚫 REGLAS SUPRIMIDAS POR JERARQUÍA:\n"
            for s in self.current_profile.suppressed:
                txt += f"   • [{s.get('id','')}] suprimida por [{s.get('suppressed_by','')}] — {s.get('reason','')}\n"

        if self.current_profile.engine_errors:
            txt += "\n🔧 ERRORES INTERNOS DE EVALUACIÓN:\n"
            for e in self.current_profile.engine_errors:
                txt += f"   • [{e.get('id','')}] {e.get('error','')}\n"

        tb.insert("0.0", txt)
        tb.configure(state="disabled")

    def _export_pdf(self):
        if not self.current_profile: return
        default_name = f"Plan_FitExpert_{self.current_profile.name.replace(' ', '_')}.pdf"
        path = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF", "*.pdf")], initialfile=default_name, title="Guardar PDF")
        if not path: return
        try:
            export_pdf(self.current_profile, self.current_plan, self.current_rutina, path)
            resp = messagebox.askyesno("Éxito", f"PDF generado correctamente en:\n{path}\n\n¿Deseas abrirlo ahora?")
            if resp:
                if platform.system() == 'Darwin':       subprocess.call(('open', path))
                elif platform.system() == 'Windows':    os.startfile(path)
                else:                                   subprocess.call(('xdg-open', path))
        except Exception as e:
            messagebox.showerror("Error", str(e))

    # ══════════════════════════════════════════════════════════════════
    # HISTORIAL & ACERCA
    # ══════════════════════════════════════════════════════════════════

    def _setup_historial(self):
        frame = self.frames["historial"]
        ctk.CTkLabel(frame, text="Historial de Evaluaciones", font=ctk.CTkFont(size=32, weight="bold")).pack(anchor="w", pady=(0, 20))
        self.hist_tb = ctk.CTkTextbox(frame, font=ctk.CTkFont(family="Consolas", size=14), fg_color=CARD_COLOR, corner_radius=12)
        self.hist_tb.pack(fill="both", expand=True)

    def _update_historial(self):
        self.hist_tb.configure(state="normal")
        self.hist_tb.delete("0.0", "end")
        history = get_user_history(self.session["user_id"])
        if not history:
            self.hist_tb.insert("0.0", "No tienes evaluaciones registradas.")
        else:
            header = f"{'FECHA':<22} {'PESO':>8} {'IMC':>7}  {'OBJETIVO':<24} {'KCAL':>7}\n"
            header += "═" * 75 + "\n"
            self.hist_tb.insert("end", header)
            for s in reversed(history):
                obj = OBJECTIVE_LABELS.get(s.get("objective", ""), "—")[:22]
                line = (f"{s.get('saved_at',''):<22} "
                        f"{s.get('weight',0):>7.1f}  "
                        f"{s.get('imc',0):>6.1f}  "
                        f"{obj:<24} "
                        f"{s.get('target_calories',0):>7.0f}\n")
                self.hist_tb.insert("end", line)
        self.hist_tb.configure(state="disabled")

    def _setup_acerca(self):
        frame = self.frames["acerca"]
        ctk.CTkLabel(frame, text="Acerca del Sistema", font=ctk.CTkFont(size=32, weight="bold")).pack(anchor="w", pady=(0, 20))
        
        card = ctk.CTkFrame(frame, corner_radius=16, fg_color=CARD_COLOR)
        card.pack(fill="x")
        
        texto = (
            f"FitExpert v3.0\n\n"
            "Sistema Experto Basado en Reglas (IA simbólica) para la generación "
            "de planes de fitness y nutrición con trazabilidad completa.\n\n"
            "Arquitectura Técnica:\n"
            " • Inferencia: Encadenamiento hacia adelante (Forward Chaining)\n"
            " • Conocimiento: Matriz de reglas lógicas IF/THEN con metadatos\n"
            f"   (este perfil evalúa contra {len(RULES)} reglas en "
            f"{len(TIER_LABELS)} jerarquías)\n"
            " • Representación: Objeto-Atributo-Valor (O-A-V)\n"
            " • Seguridad: contraseñas con Argon2id (función de derivación de\n"
            "   clave) y migración automática de hashes legados\n"
            " • Visualización: Gráficos interactivos Matplotlib y UI Moderna\n"
            " • Reportes: Exportación automatizada a formato PDF\n\n"
            "Aviso sanitario: herramienta informativa y académica. No sustituye "
            "la consulta con nutricionistas, médicos ni entrenadores certificados."
        )
        ctk.CTkLabel(card, text=texto, justify="left", font=ctk.CTkFont(size=15)).pack(anchor="w", padx=40, pady=40)

if __name__ == "__main__":
    app = App()
    app.mainloop()
