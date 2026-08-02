"""
app_desktop.pyw
===============
Interfaz gráfica nativa de escritorio — FitExpert

Pantallas:
  1. Login / Registro
  2. Mi Perfil (historial + progreso del usuario autenticado)
  3. Nueva Consulta (formulario ampliado autocompletado)
  4. Resultados (métricas + nutrición + microciclo + PDF)
  5. Acerca del Sistema
"""

import customtkinter as ctk
from tkinter import messagebox, filedialog
import os
from pathlib import Path

from auth import login, register
from database import save_profile, get_user_history, get_progress_summary, get_last_session
from user_profile import (
    UserProfile, OBJECTIVE_LABELS, ACTIVITY_LABELS,
    DIET_TYPES, ALLERGY_OPTIONS, INJURY_OPTIONS, EQUIPMENT_OPTIONS
)
from inference_engine import InferenceEngine
from nutrition import generate_nutrition_plan
from training import generate_training_plan
from pdf_exporter import export_pdf

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("FitExpert — Sistema Experto")
        self.geometry("1050x720")
        self.minsize(900, 620)

        # Estado de sesión
        self.session = None   # {"user_id": ..., "username": ...}
        self.current_profile = None
        self.current_motor   = None
        self.current_rutina  = None
        self.current_plan    = None

        # Empezar en pantalla de login
        self._show_login_screen()

    # ══════════════════════════════════════════════════════════════════
    # PANTALLA DE LOGIN / REGISTRO
    # ══════════════════════════════════════════════════════════════════

    def _show_login_screen(self):
        for w in self.winfo_children():
            w.destroy()

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        outer = ctk.CTkFrame(self, fg_color="transparent")
        outer.grid(sticky="nsew", padx=60, pady=60)
        outer.grid_rowconfigure(0, weight=1)
        outer.grid_columnconfigure(0, weight=1)

        card = ctk.CTkFrame(outer, corner_radius=20, width=420)
        card.grid(row=0, column=0)
        card.grid_columnconfigure(0, weight=1)

        # Logo
        ctk.CTkLabel(card, text="FitExpert", font=ctk.CTkFont(size=32, weight="bold")).grid(row=0, column=0, pady=(40, 5))
        ctk.CTkLabel(card, text="Sistema Experto en Nutrición y Fitness",
                     font=ctk.CTkFont(size=14), text_color="gray").grid(row=1, column=0, pady=(0, 20))

        # Tabs Login / Registro
        self.login_tabview = ctk.CTkTabview(card, width=360)
        self.login_tabview.grid(row=2, column=0, padx=30, pady=(0, 20))
        self.login_tabview.add("Iniciar Sesión")
        self.login_tabview.add("Registrarse")

        self._build_login_tab(self.login_tabview.tab("Iniciar Sesión"))
        self._build_register_tab(self.login_tabview.tab("Registrarse"))

    def _build_login_tab(self, tab):
        vcmd_user = (self.register(self._validate_username), '%P')

        ctk.CTkLabel(tab, text="Usuario:", font=ctk.CTkFont(size=13)).pack(anchor="w", pady=(10, 0))
        self.login_user = ctk.CTkEntry(tab, placeholder_text="Tu nombre de usuario", height=36,
                                       validate="key", validatecommand=vcmd_user)
        self.login_user.pack(fill="x", pady=(2, 10))

        ctk.CTkLabel(tab, text="Contraseña:", font=ctk.CTkFont(size=13)).pack(anchor="w")
        self.login_pass = ctk.CTkEntry(tab, placeholder_text="Tu contraseña", show="*", height=36)
        self.login_pass.pack(fill="x", pady=(2, 15))

        ctk.CTkButton(tab, text="Iniciar Sesión", height=40,
                      font=ctk.CTkFont(size=14, weight="bold"),
                      command=self._do_login).pack(fill="x")

    def _build_register_tab(self, tab):
        vcmd_user = (self.register(self._validate_username), '%P')

        ctk.CTkLabel(tab, text="Elige un nombre de usuario:", font=ctk.CTkFont(size=13)).pack(anchor="w", pady=(10, 0))
        self.reg_user = ctk.CTkEntry(tab, placeholder_text="Min. 3 caracteres (sin espacios)", height=36,
                                     validate="key", validatecommand=vcmd_user)
        self.reg_user.pack(fill="x", pady=(2, 10))

        ctk.CTkLabel(tab, text="Contraseña:", font=ctk.CTkFont(size=13)).pack(anchor="w")
        self.reg_pass = ctk.CTkEntry(tab, placeholder_text="Min. 4 caracteres", show="*", height=36)
        self.reg_pass.pack(fill="x", pady=(2, 10))

        ctk.CTkLabel(tab, text="Confirmar contraseña:", font=ctk.CTkFont(size=13)).pack(anchor="w")
        self.reg_pass2 = ctk.CTkEntry(tab, placeholder_text="Repite tu contraseña", show="*", height=36)
        self.reg_pass2.pack(fill="x", pady=(2, 15))

        ctk.CTkButton(tab, text="Crear Cuenta", height=40,
                      font=ctk.CTkFont(size=14, weight="bold"),
                      fg_color=["#2FA572", "#1a7a50"],
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
            self._build_main_app()
        else:
            messagebox.showerror("Error de inicio de sesión", result["error"])

    def _do_register(self):
        u  = self.reg_user.get().strip()
        p  = self.reg_pass.get()
        p2 = self.reg_pass2.get()
        if p != p2:
            messagebox.showerror("Error", "Las contraseñas no coinciden.")
            return
        result = register(u, p)
        if result["ok"]:
            messagebox.showinfo("Cuenta creada", f"Bienvenido, {result['username']}! Ya puedes iniciar sesión.")
            self.login_tabview.set("Iniciar Sesión")
        else:
            messagebox.showerror("Error al registrarse", result["error"])

    # ══════════════════════════════════════════════════════════════════
    # APLICACIÓN PRINCIPAL (POST-LOGIN)
    # ══════════════════════════════════════════════════════════════════

    def _build_main_app(self):
        for w in self.winfo_children():
            w.destroy()

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # ─── BARRA LATERAL ───────────────────────────────────────────
        self.sidebar = ctk.CTkFrame(self, width=220, corner_radius=0, fg_color="#111111")
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_rowconfigure(7, weight=1)
        self.sidebar.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(self.sidebar, text="FitExpert",
                     font=ctk.CTkFont(size=24, weight="bold")).grid(row=0, column=0, padx=20, pady=(25, 10))
        ctk.CTkLabel(self.sidebar, text=f"Usuario: {self.session['username']}",
                     font=ctk.CTkFont(size=12), text_color="gray").grid(row=1, column=0, padx=20, pady=(0, 25))

        self._sidebar_btns = {}
        nav_items = [
            ("perfil",    "Mi Perfil",             self.show_perfil),
            ("nueva",     "Nueva Consulta",        self.show_nueva),
            ("resultados","Mi Plan Actual",        self.show_resultados_actual),
            ("historial", "Historial",             self.show_historial),
            ("acerca",    "Acerca del Sistema",    self.show_acerca),
        ]
        for i, (key, label, cmd) in enumerate(nav_items, start=2):
            btn = ctk.CTkButton(self.sidebar, text=label, height=40, anchor="w",
                                font=ctk.CTkFont(size=13),
                                fg_color="transparent", border_width=1,
                                command=cmd)
            btn.grid(row=i, column=0, padx=15, pady=5, sticky="ew")
            self._sidebar_btns[key] = btn

        ctk.CTkButton(self.sidebar, text="Cerrar sesión", height=36,
                      font=ctk.CTkFont(size=12), fg_color="#2d2d2d",
                      hover_color="#444444",
                      command=self._logout).grid(row=8, column=0, padx=15, pady=20, sticky="ew")

        # ─── CONTENEDOR PRINCIPAL ─────────────────────────────────────
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
        self._show_login_screen()

    def _set_active_btn(self, key):
        for k, btn in self._sidebar_btns.items():
            if k == key:
                btn.configure(fg_color=["#1F6AA5", "#144a7a"], border_width=0)
            else:
                btn.configure(fg_color="transparent", border_width=1)

    def _show_frame(self, key):
        for frame in self.frames.values():
            frame.grid_forget()
        self.frames[key].grid(row=0, column=1, sticky="nsew", padx=25, pady=25)

    # ── Navegación ────────────────────────────────────────────────────

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
            messagebox.showinfo("Sin resultados", "Genera primero una evaluación en 'Nueva Consulta'.")
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

        ctk.CTkLabel(frame, text=f"Perfil de {self.session['username']}",
                     font=ctk.CTkFont(size=28, weight="bold")).pack(anchor="w", pady=(0, 5))

        last = get_last_session(self.session["user_id"])
        
        if not last:
            ctk.CTkLabel(frame, text="Aun no tienes datos registrados. Genera una Nueva Consulta para comenzar.",
                         font=ctk.CTkFont(size=14), text_color="gray").pack(anchor="w", pady=(0, 20))
            return

        ctk.CTkLabel(frame, text="Resumen de tu estado físico actual y progreso.",
                     font=ctk.CTkFont(size=14), text_color="gray").pack(anchor="w", pady=(0, 20))

        # Tarjeta de Datos Personales Actuales
        info_card = ctk.CTkFrame(frame, corner_radius=12)
        info_card.pack(fill="x", pady=(0, 20))

        ctk.CTkLabel(info_card, text="Datos Físicos (Ultima evaluación)", font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", padx=20, pady=(15, 10))
        
        info_grid = ctk.CTkFrame(info_card, fg_color="transparent")
        info_grid.pack(fill="x", padx=20, pady=(0, 15))

        fields = [
            ("Edad", f"{last.get('age', 0)} años"),
            ("Sexo", last.get("sex", "").capitalize()),
            ("Peso", f"{last.get('weight', 0):.1f} kg"),
            ("Altura", f"{last.get('height', 0):.0f} cm"),
            ("Grasa Corporal", f"{last.get('body_fat_pct', 0):.1f} %" if last.get('body_fat_pct', 0) > 0 else "No registrado"),
        ]

        for i, (label, val) in enumerate(fields):
            ctk.CTkLabel(info_grid, text=f"{label}:", font=ctk.CTkFont(size=13, weight="bold"), text_color="gray").grid(row=i//2, column=(i%2)*2, sticky="w", pady=4, padx=(0, 10))
            ctk.CTkLabel(info_grid, text=val, font=ctk.CTkFont(size=13)).grid(row=i//2, column=(i%2)*2 + 1, sticky="w", pady=4, padx=(0, 40))

        progress = get_progress_summary(self.session["user_id"])

        # Tarjetas de progreso
        metrics_frame = ctk.CTkFrame(frame, fg_color="transparent")
        metrics_frame.pack(fill="x", pady=10)

        self._metric_card(metrics_frame, "Sesiones", str(progress["sesiones"]), "Evaluaciones totales").pack(
            side="left", expand=True, padx=(0, 5))

        delta_p = progress["delta_peso_kg"]
        peso_color = "#2FA572" if delta_p <= 0 else "#FFA500"
        self._metric_card(metrics_frame, "Cambio de Peso",
                          f"{'+' if delta_p > 0 else ''}{delta_p:.1f} kg", "Desde primera sesión",
                          main_color=peso_color).pack(side="left", expand=True, padx=5)

        delta_c = progress["delta_calorias"]
        self._metric_card(metrics_frame, "Ajuste Calórico",
                          f"{'+' if delta_c > 0 else ''}{delta_c:.0f} kcal", "En meta calorica").pack(
            side="left", expand=True, padx=(5, 0))

        # Fechas
        ctk.CTkLabel(frame, text=f"Primera sesion: {progress['primera_sesion']}  |  Ultima sesion: {progress['ultima_sesion']}",
                     text_color="gray", font=ctk.CTkFont(size=12)).pack(anchor="w", pady=(15, 0))


    def _metric_card(self, parent, title, main_val, sub_val, main_color="white"):
        card = ctk.CTkFrame(parent, corner_radius=10, fg_color="#1e1e2e")
        ctk.CTkLabel(card, text=title, font=ctk.CTkFont(size=12, weight="bold"),
                     text_color="gray").pack(pady=(12, 0))
        ctk.CTkLabel(card, text=main_val, font=ctk.CTkFont(size=22, weight="bold"),
                     text_color=main_color).pack(pady=(4, 0))
        ctk.CTkLabel(card, text=sub_val, font=ctk.CTkFont(size=11)).pack(pady=(0, 12))
        return card

    # ══════════════════════════════════════════════════════════════════
    # NUEVA CONSULTA
    # ══════════════════════════════════════════════════════════════════

    def _setup_nueva(self):
        frame = self.frames["nueva"]

        ctk.CTkLabel(frame, text="Nueva Evaluación",
                     font=ctk.CTkFont(size=28, weight="bold")).pack(anchor="w", pady=(0, 5))
        ctk.CTkLabel(frame, text="Modifica los datos que hayan cambiado desde tu ultima sesión.",
                     font=ctk.CTkFont(size=13), text_color="gray").pack(anchor="w", pady=(0, 20))

        # ── SECCIÓN 1: Datos Personales ───────────────────────────────
        self._section_label(frame, "Datos Personales")
        col1_frame = ctk.CTkFrame(frame, fg_color="transparent")
        col1_frame.pack(fill="x", pady=(0, 15))
        col1_frame.columnconfigure(0, weight=1)
        col1_frame.columnconfigure(1, weight=1)

        vcmd_int   = (self.register(self._vi), '%P')
        vcmd_float = (self.register(self._vf), '%P')

        # Edad / Sexo
        f_edad = ctk.CTkFrame(col1_frame, fg_color="transparent")
        f_edad.grid(row=0, column=0, sticky="ew", padx=(0, 8), pady=4)
        ctk.CTkLabel(f_edad, text="Edad (años):", font=ctk.CTkFont(size=12)).pack(anchor="w")
        self.ent_edad = ctk.CTkEntry(f_edad, placeholder_text="Ej: 25", height=34,
                                     validate="key", validatecommand=vcmd_int)
        self.ent_edad.pack(fill="x")

        f_sexo = ctk.CTkFrame(col1_frame, fg_color="transparent")
        f_sexo.grid(row=0, column=1, sticky="ew", padx=(8, 0), pady=4)
        ctk.CTkLabel(f_sexo, text="Sexo:", font=ctk.CTkFont(size=12)).pack(anchor="w")
        self.opt_sexo = ctk.CTkOptionMenu(f_sexo, values=["Masculino", "Femenino"], height=34)
        self.opt_sexo.pack(fill="x")

        # Peso / Altura
        f_peso = ctk.CTkFrame(col1_frame, fg_color="transparent")
        f_peso.grid(row=1, column=0, sticky="ew", padx=(0, 8), pady=4)
        ctk.CTkLabel(f_peso, text="Peso corporal:", font=ctk.CTkFont(size=12)).pack(anchor="w")
        
        peso_row = ctk.CTkFrame(f_peso, fg_color="transparent")
        peso_row.pack(fill="x")
        self.ent_peso = ctk.CTkEntry(peso_row, placeholder_text="Ej: 75.5", height=34,
                                     validate="key", validatecommand=vcmd_float)
        self.ent_peso.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self.seg_peso = ctk.CTkSegmentedButton(peso_row, values=["kg", "lbs"], height=34)
        self.seg_peso.set("kg")
        self.seg_peso.pack(side="right")

        f_alt = ctk.CTkFrame(col1_frame, fg_color="transparent")
        f_alt.grid(row=1, column=1, sticky="ew", padx=(8, 0), pady=4)
        ctk.CTkLabel(f_alt, text="Altura (cm):", font=ctk.CTkFont(size=12)).pack(anchor="w")
        self.ent_altura = ctk.CTkEntry(f_alt, placeholder_text="Ej: 175", height=34,
                                       validate="key", validatecommand=vcmd_int)
        self.ent_altura.pack(fill="x")

        # % Grasa corporal (opcional)
        f_grasa = ctk.CTkFrame(col1_frame, fg_color="transparent")
        f_grasa.grid(row=2, column=0, sticky="ew", padx=(0, 8), pady=4)
        ctk.CTkLabel(f_grasa, text="% Grasa corporal (opcional):", font=ctk.CTkFont(size=12)).pack(anchor="w")
        self.ent_grasa = ctk.CTkEntry(f_grasa, placeholder_text="Ej: 18.5", height=34,
                                      validate="key", validatecommand=vcmd_float)
        self.ent_grasa.pack(fill="x")

        # ── SECCIÓN 2: Objetivos ──────────────────────────────────────
        self._section_label(frame, "Objetivos y Experiencia")
        obj_frame = ctk.CTkFrame(frame, fg_color="transparent")
        obj_frame.pack(fill="x", pady=(0, 15))
        obj_frame.columnconfigure(0, weight=1)
        obj_frame.columnconfigure(1, weight=1)

        f_obj = ctk.CTkFrame(obj_frame, fg_color="transparent")
        f_obj.grid(row=0, column=0, sticky="ew", padx=(0, 8), pady=4)
        ctk.CTkLabel(f_obj, text="Objetivo principal:", font=ctk.CTkFont(size=12)).pack(anchor="w")
        self.obj_vals = list(OBJECTIVE_LABELS.values())
        self.opt_obj  = ctk.CTkOptionMenu(f_obj, values=self.obj_vals, height=34)
        self.opt_obj.pack(fill="x")

        f_act = ctk.CTkFrame(obj_frame, fg_color="transparent")
        f_act.grid(row=0, column=1, sticky="ew", padx=(8, 0), pady=4)
        ctk.CTkLabel(f_act, text="Nivel de actividad diaria:", font=ctk.CTkFont(size=12)).pack(anchor="w")
        self.act_vals = list(ACTIVITY_LABELS.values())
        self.opt_act  = ctk.CTkOptionMenu(f_act, values=self.act_vals, height=34)
        self.opt_act.pack(fill="x")

        f_exp = ctk.CTkFrame(obj_frame, fg_color="transparent")
        f_exp.grid(row=1, column=0, sticky="ew", padx=(0, 8), pady=4)
        ctk.CTkLabel(f_exp, text="Experiencia entrenando:", font=ctk.CTkFont(size=12)).pack(anchor="w")
        self.opt_exp = ctk.CTkOptionMenu(f_exp, values=["Principiante", "Intermedio", "Avanzado"], height=34)
        self.opt_exp.pack(fill="x")

        f_lug = ctk.CTkFrame(obj_frame, fg_color="transparent")
        f_lug.grid(row=1, column=1, sticky="ew", padx=(8, 0), pady=4)
        ctk.CTkLabel(f_lug, text="Lugar de entrenamiento:", font=ctk.CTkFont(size=12)).pack(anchor="w")
        self.opt_lugar = ctk.CTkOptionMenu(f_lug, values=["Gimnasio", "Casa"], height=34, command=self._on_lugar_change)
        self.opt_lugar.pack(fill="x")

        # ── SECCIÓN 3: Lesiones ───────────────────────────────────────
        self._section_label(frame, "Lesiones o Molestias Articulares")
        les_frame = ctk.CTkFrame(frame, fg_color="transparent")
        les_frame.pack(fill="x", pady=(0, 15))

        self.inj_vars = {}
        labels_lesiones = {"rodilla": "Rodilla", "lumbar": "Zona lumbar (espalda baja)", "hombro": "Hombros"}
        for key, label in labels_lesiones.items():
            var = ctk.BooleanVar()
            self.inj_vars[key] = var
            ctk.CTkCheckBox(les_frame, text=label, variable=var,
                            font=ctk.CTkFont(size=13)).pack(side="left", padx=15, pady=5)

        # ── SECCIÓN 4: Equipamiento ───────────────────────────────────
        self._section_label(frame, "Equipamiento Disponible en Casa")
        eq_frame = ctk.CTkFrame(frame, fg_color="transparent")
        eq_frame.pack(fill="x", pady=(0, 15))

        self.eq_vars = {}
        self.eq_checkboxes = []
        labels_eq = {
            "mancuernas":        "Mancuernas",
            "bandas_elásticas":  "Bandas elásticas",
            "barra_dominadas":   "Barra de dominadas",
            "kettlebell":        "Kettlebell",
            "solo_peso_corporal":"Solo peso corporal",
        }
        for i, (key, label) in enumerate(labels_eq.items()):
            var = ctk.BooleanVar()
            self.eq_vars[key] = var
            row_idx = i // 3
            col_idx = i % 3
            if col_idx == 0:
                eq_sub = ctk.CTkFrame(eq_frame, fg_color="transparent")
                eq_sub.pack(fill="x")
            cb = ctk.CTkCheckBox(eq_sub, text=label, variable=var,
                            font=ctk.CTkFont(size=13))
            cb.pack(side="left", padx=12, pady=4)
            self.eq_checkboxes.append(cb)

        # ── SECCIÓN 5: Nutrición y Estilo de Vida ─────────────────────
        self._section_label(frame, "Nutrición y Estilo de Vida")
        nut_frame = ctk.CTkFrame(frame, fg_color="transparent")
        nut_frame.pack(fill="x", pady=(0, 15))
        nut_frame.columnconfigure(0, weight=1)
        nut_frame.columnconfigure(1, weight=1)

        # Tipo de dieta
        f_diet = ctk.CTkFrame(nut_frame, fg_color="transparent")
        f_diet.grid(row=0, column=0, sticky="ew", padx=(0, 8), pady=4)
        ctk.CTkLabel(f_diet, text="Tipo de dieta:", font=ctk.CTkFont(size=12)).pack(anchor="w")
        self.diet_vals  = list(DIET_TYPES.keys())
        self.diet_labels = list(DIET_TYPES.values())
        self.opt_diet = ctk.CTkOptionMenu(f_diet, values=self.diet_labels, height=34)
        self.opt_diet.pack(fill="x")

        # Frecuencia alimentaria
        f_freq = ctk.CTkFrame(nut_frame, fg_color="transparent")
        f_freq.grid(row=0, column=1, sticky="ew", padx=(8, 0), pady=4)
        ctk.CTkLabel(f_freq, text="Comidas al dia:", font=ctk.CTkFont(size=12)).pack(anchor="w")
        self.opt_freq = ctk.CTkOptionMenu(f_freq, values=["3 comidas", "4 comidas", "5 comidas"], height=34)
        self.opt_freq.set("3 comidas")
        self.opt_freq.pack(fill="x")

        # Alergias / intolerancias
        ctk.CTkLabel(nut_frame, text="Alergias / Intolerancias alimentarias:",
                     font=ctk.CTkFont(size=12)).grid(row=1, column=0, columnspan=2, sticky="w", pady=(12, 4))
        alg_frame = ctk.CTkFrame(nut_frame, fg_color="transparent")
        alg_frame.grid(row=2, column=0, columnspan=2, sticky="ew")

        self.alg_vars = {}
        labels_alg = {
            "lactosa": "Lactosa",
            "gluten":  "Gluten / Celiaquía",
            "nueces":  "Nueces / Frutos secos",
            "soya":    "Soya / Tofu",
            "huevo":   "Huevo",
        }
        for key, label in labels_alg.items():
            var = ctk.BooleanVar()
            self.alg_vars[key] = var
            ctk.CTkCheckBox(alg_frame, text=label, variable=var,
                            font=ctk.CTkFont(size=13)).pack(side="left", padx=12, pady=4)

        # ── Botón principal ───────────────────────────────────────────
        self._on_lugar_change(self.opt_lugar.get())
        ctk.CTkButton(frame, text="Generar Plan Personalizado",
                      height=50, font=ctk.CTkFont(size=16, weight="bold"),
                      command=self._procesar).pack(fill="x", pady=(30, 20))

    def _section_label(self, parent, text):
        ctk.CTkLabel(parent, text=text, font=ctk.CTkFont(size=16, weight="bold")).pack(
            anchor="w", pady=(18, 4))
        ctk.CTkFrame(parent, height=2, fg_color="#1F6AA5").pack(fill="x", pady=(0, 8))

    def _on_lugar_change(self, choice):
        estado = "normal" if choice == "Casa" else "disabled"
        for checkbox in self.eq_checkboxes:
            checkbox.configure(state=estado)
            if choice == "Gimnasio":
                checkbox.deselect()

    def _prefill_nueva_consulta(self):
        last = get_last_session(self.session["user_id"])
        if not last:
            return

        # Vaciar y rellenar campos de texto
        self.ent_edad.delete(0, "end")
        self.ent_edad.insert(0, str(last.get("age", "")))
        
        self.ent_peso.delete(0, "end")
        self.ent_peso.insert(0, str(last.get("weight", "")))

        self.ent_altura.delete(0, "end")
        self.ent_altura.insert(0, str(last.get("height", "")))

        self.ent_grasa.delete(0, "end")
        grasa = last.get("body_fat_pct", 0)
        if grasa > 0:
            self.ent_grasa.insert(0, str(grasa))

        # Menús desplegables
        sex_val = "Masculino" if last.get("sex", "masculino") == "masculino" else "Femenino"
        self.opt_sexo.set(sex_val)

        obj_key = last.get("objective", "mantenimiento")
        if obj_key in OBJECTIVE_LABELS:
            self.opt_obj.set(OBJECTIVE_LABELS[obj_key])

        act_key = last.get("activity_level", "sedentario")
        if act_key in ACTIVITY_LABELS:
            self.opt_act.set(ACTIVITY_LABELS[act_key])

        self.opt_exp.set(last.get("experience", "principiante").capitalize())
        
        lugar = "Gimnasio" if last.get("training_place", "gimnasio") == "gimnasio" else "Casa"
        self.opt_lugar.set(lugar)
        self._on_lugar_change(lugar)

        diet_key = last.get("diet_type", "omnivoro")
        if diet_key in DIET_TYPES:
            self.opt_diet.set(DIET_TYPES[diet_key])

        freq = last.get("meal_frequency", 3)
        self.opt_freq.set(f"{freq} comidas")

        # Checkboxes
        injuries = last.get("injuries", [])
        for k, v in self.inj_vars.items():
            v.set(k in injuries)

        equipment = last.get("equipment", [])
        for k, v in self.eq_vars.items():
            v.set(k in equipment)

        allergies = last.get("allergies", [])
        for k, v in self.alg_vars.items():
            v.set(k in allergies)

    # ── Validadores ───────────────────────────────────────────────────

    def _vi(self, P):
        return P == "" or P.isdigit()

    def _vf(self, P):
        if P in ("", "."):
            return True
        try:
            float(P)
            return True
        except ValueError:
            return False

    # ── Procesamiento del formulario ──────────────────────────────────

    def _procesar(self):
        try:
            nombre = self.session["username"]

            edad_s = self.ent_edad.get()
            if not edad_s:
                raise ValueError("La edad es requerida.")
            edad = int(edad_s)

            peso_s = self.ent_peso.get()
            if not peso_s:
                raise ValueError("El peso es requerido.")
            peso = float(peso_s)
            if self.seg_peso.get() == "lbs":
                peso = peso * 0.453592

            alt_s = self.ent_altura.get()
            if not alt_s:
                raise ValueError("La altura es requerida.")
            altura = float(alt_s)

            grasa_s = self.ent_grasa.get()
            grasa = float(grasa_s) if grasa_s else 0.0

            sexo = "masculino" if self.opt_sexo.get() == "Masculino" else "femenino"

            obj_label = self.opt_obj.get()
            objetivo  = list(OBJECTIVE_LABELS.keys())[self.obj_vals.index(obj_label)]

            act_label = self.opt_act.get()
            actividad = list(ACTIVITY_LABELS.keys())[self.act_vals.index(act_label)]

            experiencia = self.opt_exp.get().lower()
            lugar       = "gimnasio" if self.opt_lugar.get() == "Gimnasio" else "casa"

            lesiones  = [k for k, v in self.inj_vars.items() if v.get()]
            equipment = [k for k, v in self.eq_vars.items() if v.get()]
            if lugar == "gimnasio":
                equipment = []

            diet_label = self.opt_diet.get()
            diet_key   = self.diet_vals[self.diet_labels.index(diet_label)]

            freq = int(self.opt_freq.get()[0])
            alergias = [k for k, v in self.alg_vars.items() if v.get()]

            perfil = UserProfile(
                user_id=self.session["user_id"],
                name=nombre,
                age=edad,
                sex=sexo,
                weight=peso,
                height=altura,
                body_fat_pct=grasa,
                activity_level=actividad,
                objective=objetivo,
                experience=experiencia,
                training_place=lugar,
                equipment=equipment,
                injuries=lesiones,
                diet_type=diet_key,
                allergies=alergias,
                meal_frequency=freq,
            )

            motor  = InferenceEngine()
            motor.run(perfil)
            rutina = generate_training_plan(perfil)
            plan   = generate_nutrition_plan(perfil)
            save_profile(perfil)

            self.current_profile = perfil
            self.current_motor   = motor
            self.current_rutina  = rutina
            self.current_plan    = plan

            self._render_resultados()
            self._set_active_btn("resultados")
            self._show_frame("resultados")

        except Exception as e:
            messagebox.showerror("Error al generar", str(e) or
                                 "Ha ocurrido un error inesperado. Revisa que todos los campos numericos sean correctos.")

    # ══════════════════════════════════════════════════════════════════
    # RESULTADOS
    # ══════════════════════════════════════════════════════════════════

    def _render_resultados(self):
        frame = self.frames["resultados"]
        for w in frame.winfo_children():
            w.destroy()

        p = self.current_profile
        plan   = self.current_plan
        rutina = self.current_rutina
        motor  = self.current_motor

        # Header
        header = ctk.CTkFrame(frame, fg_color="transparent")
        header.pack(fill="x", pady=(0, 20))
        header.columnconfigure(0, weight=1)

        ctk.CTkLabel(header, text="Plan Generado",
                     font=ctk.CTkFont(size=26, weight="bold"),
                     text_color="#2FA572").grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(header, text=f"Plan para {p.name}  |  {p.created_at}",
                     font=ctk.CTkFont(size=13), text_color="gray").grid(row=1, column=0, sticky="w")

        # Botones de acción
        btns = ctk.CTkFrame(header, fg_color="transparent")
        btns.grid(row=0, column=1, rowspan=2, sticky="e")
        ctk.CTkButton(btns, text="Lógica del Motor", width=150,
                      fg_color="#2d2d2d", hover_color="#444444",
                      command=self._show_motor_window).pack(side="left", padx=(0, 8))
        ctk.CTkButton(btns, text="Exportar PDF", width=140,
                      fg_color=["#c0392b", "#922b21"],
                      command=self._export_pdf).pack(side="left")

        # Métricas
        mf = ctk.CTkFrame(frame, fg_color="transparent")
        mf.pack(fill="x", pady=(0, 20))
        imc_color = "#2FA572" if 18.5 <= p.imc <= 24.9 else "#FFA500" if p.imc < 18.5 else "#FF4C4C"
        self._metric_card(mf, "IMC", f"{p.imc:.1f}", p.imc_category, imc_color).pack(
            side="left", fill="x", expand=True, padx=(0, 4))
        self._metric_card(mf, "TMB",  f"{p.tmb:.0f}", "kcal / reposo").pack(
            side="left", fill="x", expand=True, padx=4)
        self._metric_card(mf, "TDEE", f"{p.tdee:.0f}", "kcal / gasto total").pack(
            side="left", fill="x", expand=True, padx=4)
        self._metric_card(mf, "Meta", f"{p.target_calories:.0f}", "kcal objetivo",
                          "#1E90FF").pack(side="left", fill="x", expand=True, padx=(4, 0))

        # Tabs de contenido
        tabs = ctk.CTkTabview(frame, height=420)
        tabs.pack(fill="both", expand=True)
        tabs.add("Plan Nutriciónal")
        tabs.add("Microciclo Semanal")

        # ── TAB NUTRICIÓN ─────────────────────────────────────────────
        tab_nut = tabs.tab("Plan Nutriciónal")
        macros  = plan["macros"]
        ctk.CTkLabel(tab_nut,
                     text=f"Proteinas {macros['proteinas']}g ({macros['p_pct']}%)  |  "
                          f"Carbos {macros['carbohidratos']}g ({macros['c_pct']}%)  |  "
                          f"Grasas {macros['grasas']}g ({macros['g_pct']}%)",
                     font=ctk.CTkFont(weight="bold", size=13)).pack(pady=(8, 12), anchor="w", padx=10)

        if plan.get("alergias_activas"):
            ctk.CTkLabel(tab_nut,
                         text=f"Filtros activos: dieta {plan['tipo_dieta']} | "
                              f"alergias excluidas: {', '.join(plan['alergias_activas'])}",
                         font=ctk.CTkFont(size=11), text_color="#2FA572").pack(anchor="w", padx=10)

        tb_nut = ctk.CTkTextbox(tab_nut, wrap="word", font=ctk.CTkFont(size=13))
        tb_nut.pack(fill="both", expand=True, padx=10, pady=(8, 10))
        plan_d = plan["plan"]
        txt = ""
        meals = [("DESAYUNO", "desayuno"), ("ALMUERZO", "almuerzo"),
                 ("CENA", "cena"), ("SNACKS / MERIENDAS", "snacks")]
        for label, key in meals:
            items = plan_d.get(key, [])
            if items:
                txt += f"{label}:\n" + "\n".join([f"  - {x}" for x in items]) + "\n\n"
        txt += f"HIDRATACION: {plan_d.get('hidratacion', '')}"
        tb_nut.insert("0.0", txt)
        tb_nut.configure(state="disabled")

        # ── TAB ENTRENAMIENTO (Microciclo) ────────────────────────────
        tab_train = tabs.tab("Microciclo Semanal")
        ctk.CTkLabel(tab_train, text=f"{rutina['nombre']}",
                     font=ctk.CTkFont(weight="bold", size=15), text_color="#1E90FF").pack(
            pady=(8, 2), anchor="w", padx=10)
        ctk.CTkLabel(tab_train, text=f"{rutina['tipo']}  |  {rutina['dias']}",
                     font=ctk.CTkFont(size=12), text_color="gray").pack(anchor="w", padx=10)

        if rutina.get("notas"):
            ctk.CTkLabel(tab_train, text=rutina["notas"],
                         font=ctk.CTkFont(size=11), text_color="#FFA500",
                         wraplength=700).pack(anchor="w", padx=10, pady=(4, 6))

        tb_train = ctk.CTkTextbox(tab_train, wrap="word", font=ctk.CTkFont(size=13))
        tb_train.pack(fill="both", expand=True, padx=10, pady=(4, 10))
        train_txt = ""
        for day in rutina.get("semana", []):
            dia   = day["dia"]
            grupo = day["grupo"]
            if day["descanso"]:
                train_txt += f"--- {dia.upper()} : {grupo} ---\n"
                train_txt += f"    {day.get('nota', 'Descanso.')}\n\n"
            else:
                train_txt += f"--- {dia.upper()} : {grupo} ---\n"
                for ej in day.get("ejercicios", []):
                    train_txt += f"    - {ej[0]}:  {ej[1]}  [{ej[2]}]\n"
                train_txt += (f"    Duracion: {day['duracion']}  |  "
                              f"Descanso: {day['descanso_entre_series']}\n")
                if day.get("nota"):
                    train_txt += f"    Nota: {day['nota']}\n"
                train_txt += "\n"
        if rutina.get("cardio_extra"):
            train_txt += f"Cardio adicional: {rutina['cardio_extra']}\n"
        tb_train.insert("0.0", train_txt)
        tb_train.configure(state="disabled")

    def _show_motor_window(self):
        if not self.current_motor:
            return
        top = ctk.CTkToplevel(self)
        top.title("Motor de Inferencia")
        top.geometry("640x520")
        top.attributes('-topmost', True)
        ctk.CTkLabel(top, text="Transparencia del Sistema Experto",
                     font=ctk.CTkFont(size=18, weight="bold")).pack(pady=10)
        ctk.CTkLabel(top,
                     text=f"Reglas activadas: {len(self.current_motor.fired_rules)} / {len(self.current_motor.rules)}",
                     text_color="gray", font=ctk.CTkFont(size=12)).pack(pady=(0, 8))
        tb = ctk.CTkTextbox(top, wrap="word", font=ctk.CTkFont(size=12))
        tb.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        txt = ""
        for c in self.current_profile.conclusions:
            rid = c["id"]
            txt += f"[{rid}] {c['conclusion']}\n"
            exp = next((e["explanation"] for e in self.current_profile.explanations
                        if e["id"] == rid), "")
            txt += f"   - {exp}\n{'-'*55}\n\n"
        tb.insert("0.0", txt)
        tb.configure(state="disabled")

    def _export_pdf(self):
        if not self.current_profile:
            return
        default_name = f"plan_{self.current_profile.name.replace(' ', '_')}.pdf"
        path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF", "*.pdf")],
            initialfile=default_name,
            title="Guardar Plan como PDF"
        )
        if not path:
            return
        try:
            export_pdf(self.current_profile, self.current_plan, self.current_rutina, path)
            messagebox.showinfo("PDF generado", f"Tu plan fue guardado en:\n{path}")
        except Exception as e:
            messagebox.showerror("Error al generar PDF", str(e))

    # ══════════════════════════════════════════════════════════════════
    # HISTORIAL
    # ══════════════════════════════════════════════════════════════════

    def _setup_historial(self):
        frame = self.frames["historial"]
        ctk.CTkLabel(frame, text="Historial de Consultas",
                     font=ctk.CTkFont(size=24, weight="bold")).pack(anchor="w", pady=(0, 15))
        self.hist_tb = ctk.CTkTextbox(frame, font=ctk.CTkFont(family="Consolas", size=12))
        self.hist_tb.pack(fill="both", expand=True)

    def _update_historial(self):
        self.hist_tb.configure(state="normal")
        self.hist_tb.delete("0.0", "end")
        history = get_user_history(self.session["user_id"])
        if not history:
            self.hist_tb.insert("0.0", "No tienes evaluaciónes registradas aun.")
        else:
            header = f"{'FECHA':<20} {'PESO':>8} {'IMC':>6}  {'OBJETIVO':<28} {'KCAL':>6}\n"
            header += "-" * 75 + "\n"
            self.hist_tb.insert("end", header)
            for s in reversed(history):
                obj = OBJECTIVE_LABELS.get(s.get("objective", ""), "—")[:26]
                line = (f"{s.get('saved_at',''):<20} "
                        f"{s.get('weight',0):>7.1f}  "
                        f"{s.get('imc',0):>5.1f}  "
                        f"{obj:<28} "
                        f"{s.get('target_calories',0):>6.0f}\n")
                self.hist_tb.insert("end", line)
        self.hist_tb.configure(state="disabled")

    # ══════════════════════════════════════════════════════════════════
    # ACERCA DE
    # ══════════════════════════════════════════════════════════════════

    def _setup_acerca(self):
        frame = self.frames["acerca"]
        ctk.CTkLabel(frame, text="Acerca del Sistema",
                     font=ctk.CTkFont(size=24, weight="bold")).pack(anchor="w", pady=(0, 20))
        card = ctk.CTkFrame(frame, corner_radius=15)
        card.pack(fill="x")
        texto = (
            "FitExpert es una aplicación de Inteligencia Artificial que implementa\n"
            "un Sistema Experto Basado en Reglas.\n\n"
            "Arquitectura del Sistema:\n"
            "  - Base de Conocimiento: 30+ reglas logicas IF-THEN\n"
            "  - Motor de Inferencia: Encadenamiento hacia adelante\n"
            "  - Representación: Modelo Objeto-Atributo-Valor (OAV)\n"
            "  - Modulo de Explicacion: Justificacion de cada regla activada\n"
            "  - Autenticación: Login/Registro con contraseña hasheada\n"
            "  - Seguimiento: Historial individual y deteccion de progreso\n"
            "  - Exportación: Generacion de PDF profesional\n\n"
            "Desarrollado como proyecto académico para demostrar el diseño,\n"
            "la implementacion y el funcionamiento de los Sistemas Expertos."
        )
        ctk.CTkLabel(card, text=texto, justify="left",
                     font=ctk.CTkFont(size=14)).pack(anchor="w", padx=30, pady=30)


if __name__ == "__main__":
    app = App()
    app.mainloop()
