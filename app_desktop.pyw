"""
app_desktop.pyw
===============
Cliente de escritorio de FitExpert — identidad "clínica de precisión digital".

Reescritura de fase 2 bajo el sistema de diseño compartido (design_system):
paleta navy profundo + turquesa de marca, iconografía Segoe Fluent
(sin emoticonos), sidebar agrupada con estados activos, asistente guiado
en 5 pasos con errores inline (nunca MessageBox), dashboard con métricas
y gráfica, plan con pestañas, historial, progreso, explicabilidad,
perfil con cambio de contraseña y exportación a PDF.

Misma lógica de negocio que la Web y la consola: validate_evaluation +
InferenceEngine + generate_nutrition_plan + generate_training_plan.
"""

from __future__ import annotations

import json
import os
import platform
import subprocess
from pathlib import Path

import customtkinter as ctk
from tkinter import filedialog
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

import design_system as DS
from auth import login, register, validate_session, change_password
from database import (
    save_profile, get_user_history, get_progress_summary, get_last_session,
)
from user_profile import (
    UserProfile, OBJECTIVE_LABELS, ACTIVITY_LABELS, EXPERIENCE_LABELS,
    DIET_TYPES, TRAINING_PLACE_LABELS, SEX_OPTIONS, ALLERGY_OPTIONS,
    INJURY_OPTIONS, INJURY_SEVERITY_OPTIONS, EQUIPMENT_OPTIONS,
    INTOLERANCE_OPTIONS, PREFERENCE_OPTIONS, INJURY_RED_FLAGS,
    LEGACY_ALLERGY_MAP,
)
from validation import validate_evaluation
from knowledge_base import RULES, TIER_LABELS
from inference_engine import InferenceEngine
from nutrition import generate_nutrition_plan
from training import generate_training_plan
from pdf_exporter import export_pdf

# ──────────────────────────────────────────────────────────────
#  Ajustes de entorno (identidad compartida)
# ──────────────────────────────────────────────────────────────

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

FONT_UI    = "Segoe UI Variable"
FONT_ICON  = DS.FONT_ICON_FLUENT      # "Segoe Fluent Icons"
FONT_MONO  = "Cascadia Code"

# Ruta ABSOLUTA de la sesión local independiente del CWD de lanzamiento
SESSION_DIR   = Path(__file__).resolve().parent
SESSION_FILE  = SESSION_DIR / "local_session.json"

# Alias de paleta (mantiene el código legible)
BG            = DS.BG
BG_ELEV       = DS.BG_ELEV
BG_ELEV_2     = DS.BG_ELEV_2
BG_ELEV_3     = DS.BG_ELEV_3
BORDER        = DS.BORDER
BORDER_STRONG = DS.BORDER_STRONG
PRIMARY       = DS.PRIMARY
PRIMARY_HOV   = DS.PRIMARY_HOV
PRIMARY_SOFT  = DS.PRIMARY_SOFT
ACCENT        = DS.ACCENT
SUCCESS       = DS.SUCCESS
WARNING       = DS.WARNING
DANGER        = DS.DANGER
CRITICAL      = DS.CRITICAL
VIOLET        = DS.VIOLET
TEXT          = DS.TEXT
TEXT_MUTED    = DS.TEXT_MUTED
TEXT_FAINT    = DS.TEXT_FAINT

# Alergias/Intolerancias mostradas en el asistente (claves legadas migradas)
ALERGIA_UI = {
    "lactosa": "Lactosa (intolerancia)",
    "gluten":  "Gluten / celiaquía",
    "nueces":  "Frutos secos (nuez, almendra, avellana)",
    "soya":    "Soja",
    "huevo":   "Huevo",
}

# Navegación agrupada (icono Fluent, clave de página, etiqueta, descripción)
NAV_GROUPS = [
    ("Planificación", [
        ("evaluacion", "nueva",     "Nueva evaluación", "Crea o actualiza tu plan en 5 pasos"),
        ("plan",       "plan",      "Plan actual",       "Nutrición, entrenamiento y decisiones del motor"),
    ]),
    ("Seguimiento", [
        ("inicio",    "panel",      "Panel general",     "Resumen de tu estado y accesos rápidos"),
        ("historial", "historial",  "Historial",         "Tus evaluaciones registradas"),
        ("progreso",  "progreso",   "Progreso",          "Evolución de peso, IMC y calorías"),
    ]),
    ("Transparencia", [
        ("explicacion", "explicacion", "Explicabilidad", "Qué reglas activó el motor y por qué"),
    ]),
    ("Cuenta", [
        ("perfil", "perfil", "Mi perfil",  "Datos de la cuenta y cambio de contraseña"),
        ("libro",  "acerca", "Acerca de",  "Información del sistema y fuentes"),
    ]),
]

# Campos que valida cada paso del asistente (claves canónicas del esquema)
STEP_FIELDS = {
    1: ["age", "sex", "weight", "height", "body_fat_pct"],
    2: ["objective", "activity_level", "experience", "meal_frequency",
        "training_place", "equipment"],
    3: ["injuries", "injury_severity", "balance_issues", "red_flags"],
    4: ["diet_type", "allergies", "intolerances", "preferences"],
}

STEP_TITLES = [
    "Datos personales", "Objetivo y preparación", "Salud y seguridad",
    "Nutrición", "Revisión final",
]
STEP_ICONS  = ["perfil", "evaluacion", "escudo", "nutricion", "check_circulo"]


def _safe_remove(path: Path) -> None:
    """Elimina un archivo sin propagar excepciones de sistema."""
    try:
        path.unlink(missing_ok=True)
    except OSError:
        pass


def _fw(size: int, weight: str = "normal") -> ctk.CTkFont:
    """Fuente de UI estándar (customtkinter exige tamaños enteros)."""
    return ctk.CTkFont(family=FONT_UI, size=size, weight=weight)


def _icon(key: str, size: int = 14, color: str = TEXT) -> ctk.CTkFont:
    """Fuente de iconos Fluent (la familia se aplica en el widget)."""
    return ctk.CTkFont(family=FONT_ICON, size=size, weight="normal")


class App(ctk.CTk):
    """Aplicación de escritorio FitExpert."""

    # ──────────────────────────────────────────────────────────
    #  Ciclo de vida y sesión
    # ──────────────────────────────────────────────────────────

    def __init__(self) -> None:
        super().__init__()
        self.title("FitExpert — Nutrición y entrenamiento que se explican")
        self.geometry("1180x800")
        self.minsize(1020, 700)
        self.configure(fg_color=BG)

        self.session = None
        self.current_results = None   # {"perfil","plan","rutina","warnings","ts"}
        self._graph_canvas = None     # evita fugas de figuras Matplotlib
        self.wz_step = 1
        self.wz_values: dict = {}
        self.wz_widgets: dict = {}
        self.wz_err_lbl = None
        self.page_buttons: dict = {}
        self.pdf_last_path = None

        self._check_local_session()
        if not self.session:
            self._show_login_screen()

    # ── Sesión local ──────────────────────────────────────────

    def _check_local_session(self) -> None:
        if SESSION_FILE.exists():
            try:
                data = json.loads(SESSION_FILE.read_text(encoding="utf-8"))
            except Exception:
                _safe_remove(SESSION_FILE)
                return
            valid = validate_session(data)
            if valid:
                self.session = valid
                self._build_main_app()

    def _save_local_session(self) -> None:
        if self.session:
            try:
                SESSION_FILE.write_text(
                    json.dumps(self.session, ensure_ascii=False, indent=2),
                    encoding="utf-8")
            except OSError:
                pass

    def _clear_local_session(self) -> None:
        _safe_remove(SESSION_FILE)

    # ──────────────────────────────────────────────────────────
    #  Helpers visuales compartidos
    # ──────────────────────────────────────────────────────────

    def _glyph_label(self, parent, key: str, size: int = 14,
                     color: str = TEXT, **kw) -> ctk.CTkLabel:
        """Etiqueta de icono Fluent (sin emoticonos)."""
        return ctk.CTkLabel(parent, text=DS.FLUENT[key],
                            font=_icon(key, size), text_color=color, **kw)

    def _page_header(self, parent, icon: str, title: str, subtitle: str) -> None:
        head = ctk.CTkFrame(parent, fg_color="transparent")
        head.pack(fill="x", pady=(0, 18))
        chip = ctk.CTkFrame(head, width=46, height=46, corner_radius=14,
                            fg_color=PRIMARY_SOFT, border_width=1,
                            border_color=PRIMARY)
        chip.pack(side="left", padx=(0, 14))
        chip.pack_propagate(False)
        self._glyph_label(chip, icon, size=20, color=PRIMARY).place(
            relx=.5, rely=.5, anchor="center")
        txt = ctk.CTkFrame(head, fg_color="transparent")
        txt.pack(side="left", fill="x", expand=True)
        ctk.CTkLabel(txt, text=title, font=_fw(22, "bold"),
                     text_color=TEXT, anchor="w").pack(anchor="w")
        ctk.CTkLabel(txt, text=subtitle, font=_fw(12),
                     text_color=TEXT_MUTED, anchor="w").pack(anchor="w", pady=(1, 0))

    def _inline_error(self, parent, text: str | None = None) -> ctk.CTkLabel:
        lbl = ctk.CTkLabel(parent, text=text or "", font=_fw(12, "bold"),
                           text_color=DANGER, anchor="w", justify="left",
                           wraplength=640)
        lbl.pack(fill="x", padx=1, pady=(6, 0))
        return lbl

    def _metric_card(self, parent, title: str, main: str, sub: str,
                     color: str = TEXT, accent_glyph: str | None = None) -> ctk.CTkFrame:
        card = ctk.CTkFrame(parent, corner_radius=DS.RADII["card"], fg_color=BG_ELEV,
                            border_width=1, border_color=BORDER)
        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="x", padx=16, pady=(14, 12))
        if accent_glyph:
            self._glyph_label(inner, accent_glyph, size=14, color=color).pack(anchor="w")
        ctk.CTkLabel(inner, text=title.upper(), font=_fw(11, "bold"),
                     text_color=TEXT_FAINT).pack(anchor="w", pady=(2, 4))
        ctk.CTkLabel(inner, text=main, font=_fw(26, "bold"),
                     text_color=color, anchor="w").pack(anchor="w")
        ctk.CTkLabel(inner, text=sub, font=_fw(12), text_color=TEXT_MUTED,
                     anchor="w").pack(anchor="w", pady=(1, 0))
        return card

    def _section_title(self, parent, icon: str, title: str, color: str = PRIMARY) -> None:
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", pady=(14, 6))
        self._glyph_label(row, icon, size=14, color=color).pack(side="left", padx=(0, 8))
        ctk.CTkLabel(row, text=title, font=_fw(15, "bold"),
                     text_color=TEXT, anchor="w").pack(side="left")
        ctk.CTkFrame(parent, height=1, fg_color=BORDER).pack(fill="x", pady=(0, 4))

    # ──────────────────────────────────────────────────────────
    #  PANTALLA DE ACCESO (login / registro)
    # ──────────────────────────────────────────────────────────

    def _show_login_screen(self) -> None:
        for w in self.winfo_children():
            w.destroy()
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        outer = ctk.CTkFrame(self, fg_color="transparent")
        outer.grid(row=0, column=0, sticky="nsew", padx=56, pady=44)
        outer.grid_rowconfigure(0, weight=1)
        outer.grid_columnconfigure(0, weight=5, uniform="lg")
        outer.grid_columnconfigure(1, weight=4, uniform="lg")

        self._build_auth_brand(outer)
        self._build_auth_card(outer)

    def _build_auth_brand(self, parent) -> None:
        col = ctk.CTkFrame(parent, fg_color="transparent")
        col.grid(row=0, column=0, sticky="nsew", padx=(0, 34))

        # Monograma + wordmark
        brand = ctk.CTkFrame(col, fg_color="transparent")
        brand.pack(anchor="w", pady=(0, 18))
        mark = ctk.CTkFrame(brand, width=52, height=52, corner_radius=16,
                            fg_color=PRIMARY_SOFT, border_width=1,
                            border_color=PRIMARY)
        mark.pack(side="left", padx=(0, 14))
        mark.pack_propagate(False)
        ctk.CTkLabel(mark, text="FX", font=_fw(20, "bold"),
                     text_color=PRIMARY).place(relx=.5, rely=.5, anchor="center")
        word = ctk.CTkFrame(brand, fg_color="transparent")
        word.pack(side="left")
        ctk.CTkLabel(word, text="Fit", font=_fw(26, "bold"),
                     text_color=TEXT, anchor="w").pack(anchor="w")
        ctk.CTkLabel(word, text="Expert", font=_fw(26, "bold"),
                     text_color=PRIMARY, anchor="w").pack(anchor="w")

        ctk.CTkLabel(col, text="CLÍNICA DE PRECISIÓN DIGITAL",
                     font=_fw(11, "bold"), text_color=PRIMARY).pack(anchor="w", pady=(4, 8))
        ctk.CTkLabel(col, text=(
            "Evaluación guiada por un motor de reglas IF/THEN con trazabilidad "
            "completa: cada recomendación explica la regla que la activó."),
            font=_fw(15), text_color=TEXT_MUTED, justify="left", wraplength=460,
            anchor="w").pack(anchor="w", pady=(0, 30))

        # Puntos de valor de la identidad
        for icon, title, body in (
            ("escudo", "Salud ante todo",
             "Las señales de alarma suspenden la prescripción y derivan a consulta profesional."),
            ("calculadora", "Metabólico trazable",
             "Estimaciones con fórmulas aceptadas por la comunidad científica, sin cajas negras."),
            ("explicacion", "Transparencia total",
             "Reglas activadas, suprimidas y errores del motor visibles en pantalla."),
        ):
            feat = ctk.CTkFrame(col, fg_color="transparent")
            feat.pack(fill="x", pady=7)
            badge = ctk.CTkFrame(feat, width=38, height=38, corner_radius=12,
                                 fg_color=BG_ELEV, border_width=1,
                                 border_color=BORDER)
            badge.pack(side="left", padx=(0, 12))
            badge.pack_propagate(False)
            self._glyph_label(badge, icon, size=16, color=PRIMARY).place(
                relx=.5, rely=.5, anchor="center")
            ftxt = ctk.CTkFrame(feat, fg_color="transparent")
            ftxt.pack(side="left", fill="x", expand=True)
            ctk.CTkLabel(ftxt, text=title, font=_fw(13, "bold"),
                         text_color=TEXT, anchor="w").pack(anchor="w")
            ctk.CTkLabel(ftxt, text=body, font=_fw(12),
                         text_color=TEXT_MUTED, justify="left",
                         wraplength=420, anchor="w").pack(anchor="w", pady=(1, 0))

        ctk.CTkFrame(col, height=1, fg_color=BORDER).pack(fill="x", pady=(26, 14))
        ctk.CTkLabel(col, text=(
            f"Motor de conocimiento: {len(RULES)} reglas IF/THEN · "
            f"Fuentes: WHO · CDC · AAP · ACSM"),
            font=_fw(11), text_color=TEXT_FAINT, anchor="w").pack(anchor="w")
        ctk.CTkLabel(col, text=(
            "Información orientativa. No sustituye el consejo de un profesional "
            "de la salud."),
            font=_fw(11), text_color=TEXT_FAINT, anchor="w",
            wraplength=460, justify="left").pack(anchor="w", pady=(3, 0))

    def _build_auth_card(self, parent) -> None:
        col = ctk.CTkFrame(parent, fg_color=BG_ELEV, corner_radius=DS.RADII["sheet"],
                           border_width=1, border_color=BORDER)
        col.grid(row=0, column=1, sticky="nsew")

        # Cabecera con selector de modo (sin tabs pesadas)
        self.auth_mode = "login"
        mode_row = ctk.CTkFrame(col, fg_color="transparent")
        mode_row.pack(fill="x", padx=34, pady=(30, 18))
        self.auth_btn_login = ctk.CTkButton(
            mode_row, text="Entrar", width=118, height=38, corner_radius=10,
            font=_fw(14, "bold"), fg_color=PRIMARY_SOFT, hover_color=BG_ELEV_2,
            text_color=PRIMARY, command=lambda: self._set_auth_mode("login"))
        self.auth_btn_login.pack(side="left", padx=(0, 10))
        self.auth_btn_reg = ctk.CTkButton(
            mode_row, text="Crear cuenta", width=118, height=38, corner_radius=10,
            font=_fw(14, "bold"), fg_color="transparent", hover_color=BG_ELEV_2,
            text_color=TEXT_MUTED, command=lambda: self._set_auth_mode("register"))
        self.auth_btn_reg.pack(side="left")

        self.auth_card_body = ctk.CTkFrame(col, fg_color="transparent")
        self.auth_card_body.pack(fill="both", expand=True, padx=34, pady=(0, 30))
        self._build_login_form()

    def _set_auth_mode(self, mode: str) -> None:
        self.auth_mode = mode
        for w in self.auth_card_body.winfo_children():
            w.destroy()
        if mode == "login":
            self._build_login_form()
            self.auth_btn_login.configure(fg_color=PRIMARY_SOFT, text_color=PRIMARY)
            self.auth_btn_reg.configure(fg_color="transparent", text_color=TEXT_MUTED)
        else:
            self._build_register_form()
            self.auth_btn_reg.configure(fg_color=PRIMARY_SOFT, text_color=PRIMARY)
            self.auth_btn_login.configure(fg_color="transparent", text_color=TEXT_MUTED)

    def _password_frame(self, parent, placeholder: str) -> tuple[ctk.CTkFrame, ctk.StringVar]:
        """Entrada de contraseña con visibilidad conmutable (sin emojis)."""
        f = ctk.CTkFrame(parent, fg_color="transparent")
        var = ctk.StringVar()
        ent = ctk.CTkEntry(f, textvariable=var, placeholder_text=placeholder,
                           show="\u2022", height=42, corner_radius=DS.RADII["input"],
                           font=_fw(14), fg_color=BG_ELEV_2,
                           border_color=BORDER, border_width=1,
                           text_color=TEXT, placeholder_text_color=TEXT_FAINT)
        ent.pack(side="left", fill="x", expand=True)
        self._pw_ent = ent
        togg = ctk.CTkButton(f, width=46, height=42, corner_radius=DS.RADII["input"],
                             font=_icon("ver", 15), text=DS.FLUENT["ver"],
                             fg_color=BG_ELEV_2, hover_color=BG_ELEV_3,
                             text_color=TEXT_MUTED)
        togg.pack(side="left", padx=(8, 0))

        def _toggle() -> None:
            if ent.cget("show") == "\u2022":
                ent.configure(show="")
                togg.configure(text=DS.FLUENT["ocultar"], text_color=PRIMARY)
            else:
                ent.configure(show="\u2022")
                togg.configure(text=DS.FLUENT["ver"], text_color=TEXT_MUTED)

        togg.configure(command=_toggle)
        return f, var

    def _build_login_form(self) -> None:
        body = self.auth_card_body
        ctk.CTkLabel(body, text="Bienvenido de nuevo", font=_fw(21, "bold"),
                     text_color=TEXT, anchor="w").pack(anchor="w")
        ctk.CTkLabel(body, text="Accede a tu panel y reevalúa tu plan cuando quieras.",
                     font=_fw(13), text_color=TEXT_MUTED, anchor="w",
                     justify="left", wraplength=420).pack(anchor="w", pady=(2, 22))

        ctk.CTkLabel(body, text="USUARIO", font=_fw(11, "bold"),
                     text_color=TEXT_FAINT, anchor="w").pack(anchor="w", pady=(0, 5))
        self.auth_user = ctk.StringVar()
        vcmd = (self.register(self._validate_username), "%P")
        ctk.CTkEntry(body, textvariable=self.auth_user,
                     placeholder_text="Tu nombre de usuario", height=42,
                     corner_radius=DS.RADII["input"], font=_fw(14),
                     fg_color=BG_ELEV_2, border_color=BORDER, border_width=1,
                     text_color=TEXT, placeholder_text_color=TEXT_FAINT,
                     validate="key", validatecommand=vcmd).pack(fill="x", pady=(0, 14))

        ctk.CTkLabel(body, text="CONTRASEÑA", font=_fw(11, "bold"),
                     text_color=TEXT_FAINT, anchor="w").pack(anchor="w", pady=(0, 5))
        pwf, self.auth_pass = self._password_frame(body, "Tu contraseña")
        pwf.pack(fill="x", pady=(0, 14))

        self.auth_err = self._inline_error(body)

        btn = ctk.CTkFrame(body, fg_color="transparent")
        btn.pack(fill="x", pady=(12, 0))
        ctk.CTkButton(btn, text="Acceder al panel", height=46,
                      corner_radius=DS.RADII["button"], font=_fw(15, "bold"),
                      fg_color=PRIMARY, hover_color=PRIMARY_HOV,
                      text_color="#04161A", command=self._do_login).pack(
                          side="left", fill="x", expand=True)

        ctk.CTkLabel(body, text=(
            "Tus datos se almacenan solo en este equipo · "
            "Autenticación con Argon2id · Contraseñas nunca en texto plano."),
            font=_fw(11), text_color=TEXT_FAINT, anchor="w",
            justify="left", wraplength=420).pack(anchor="w", pady=(18, 0))

    def _build_register_form(self) -> None:
        body = self.auth_card_body
        ctk.CTkLabel(body, text="Crear tu cuenta", font=_fw(21, "bold"),
                     text_color=TEXT, anchor="w").pack(anchor="w")
        ctk.CTkLabel(body, text="Registro con hash Argon2id y verificación estricta de usuario.",
                     font=_fw(13), text_color=TEXT_MUTED, anchor="w",
                     justify="left", wraplength=420).pack(anchor="w", pady=(2, 20))

        ctk.CTkLabel(body, text="NOMBRE DE USUARIO", font=_fw(11, "bold"),
                     text_color=TEXT_FAINT, anchor="w").pack(anchor="w", pady=(0, 5))
        self.reg_user = ctk.StringVar()
        vcmd = (self.register(self._validate_username), "%P")
        ctk.CTkEntry(body, textvariable=self.reg_user,
                     placeholder_text="Sin espacios · mínimo 3 caracteres", height=42,
                     corner_radius=DS.RADII["input"], font=_fw(14),
                     fg_color=BG_ELEV_2, border_color=BORDER, border_width=1,
                     text_color=TEXT, placeholder_text_color=TEXT_FAINT,
                     validate="key", validatecommand=vcmd).pack(fill="x", pady=(0, 14))

        ctk.CTkLabel(body, text="CONTRASEÑA", font=_fw(11, "bold"),
                     text_color=TEXT_FAINT, anchor="w").pack(anchor="w", pady=(0, 5))
        pwf, self.reg_pass = self._password_frame(body, "Mínimo 4 caracteres")
        pwf.pack(fill="x", pady=(0, 14))

        pwf2, self.reg_pass2 = self._password_frame(body, "Repite tu contraseña")
        pwf2.pack(fill="x", pady=(0, 14))

        self.reg_err = self._inline_error(body)

        ctk.CTkButton(body, text="Crear cuenta", height=46,
                      corner_radius=DS.RADII["button"], font=_fw(15, "bold"),
                      fg_color=PRIMARY, hover_color=PRIMARY_HOV,
                      text_color="#04161A", command=self._do_register).pack(
                          fill="x", pady=(14, 0))

    def _validate_username(self, value: str) -> bool:
        allowed = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_")
        return all(c in allowed for c in value) or value == ""

    def _do_login(self) -> None:
        u = self.auth_user.get().strip()
        p = self.auth_pass.get()
        resultado = login(u, p)
        if resultado["ok"]:
            self.session = resultado
            self._save_local_session()
            self._build_main_app()
        else:
            self.auth_err.configure(text=resultado["error"])

    def _do_register(self) -> None:
        u  = self.reg_user.get().strip()
        p  = self.reg_pass.get()
        p2 = self.reg_pass2.get()
        if p != p2:
            self.reg_err.configure(text="Las contraseñas no coinciden.")
            return
        resultado = register(u, p)
        if resultado["ok"]:
            # Éxito: volver a Entrar con el usuario prellenado
            self._set_auth_mode("login")
            self.auth_user.set(resultado["username"])
            self.auth_pass.set("")
            self.auth_err.configure(
                text="Cuenta creada correctamente. Ya puedes iniciar sesión.",
                text_color=SUCCESS)
        else:
            self.reg_err.configure(text=resultado["error"])

    # ──────────────────────────────────────────────────────────
    #  SHELL PRINCIPAL (post-login)
    # ──────────────────────────────────────────────────────────

    def _build_main_app(self) -> None:
        for w in self.winfo_children():
            w.destroy()
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure(0, minsize=268)

        # Barra lateral con identidad
        self.sidebar = ctk.CTkFrame(self, width=268, corner_radius=0,
                                    fg_color=BG_ELEV, border_width=0)
        self.sidebar.grid(row=0, column=0, sticky="nsw")
        self.sidebar.grid_propagate(False)
        self.sidebar.grid_columnconfigure(0, weight=1)
        self.sidebar.grid_rowconfigure(100, weight=1)   # empuje del footer

        # Marca
        brand = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        brand.grid(row=0, column=0, padx=18, pady=(22, 4), sticky="ew")
        mark = ctk.CTkFrame(brand, width=36, height=36, corner_radius=11,
                            fg_color=PRIMARY_SOFT, border_width=1,
                            border_color=PRIMARY)
        mark.pack(side="left", padx=(0, 10))
        mark.pack_propagate(False)
        ctk.CTkLabel(mark, text="FX", font=_fw(14, "bold"),
                     text_color=PRIMARY).place(relx=.5, rely=.5, anchor="center")
        wm = ctk.CTkFrame(brand, fg_color="transparent")
        wm.pack(side="left")
        ctk.CTkLabel(wm, text="Fit", font=_fw(18, "bold"),
                     text_color=TEXT, anchor="w").pack(anchor="w")
        ctk.CTkLabel(wm, text="Expert", font=_fw(18, "bold"),
                     text_color=PRIMARY, anchor="w").pack(anchor="w")

        # Navegación agrupada
        row = 1
        self.page_buttons = {}
        for group, items in NAV_GROUPS:
            ctk.CTkLabel(self.sidebar, text=group.upper(),
                         font=_fw(10, "bold"),
                         text_color=TEXT_FAINT, anchor="w").grid(
                             row=row, column=0, padx=22, pady=(18, 4), sticky="ew")
            row += 1
            for icon, page, label, _tip in items:
                self._nav_item(row, icon, page, label)
                row += 1

        # Pie: usuario + cierre de sesión
        foot = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        foot.grid(row=100, column=0, padx=16, pady=(0, 18), sticky="ew")
        chip = ctk.CTkFrame(foot, fg_color=BG_ELEV_2, corner_radius=14,
                            border_width=1, border_color=BORDER)
        chip.pack(fill="x", pady=(0, 10))
        av = ctk.CTkFrame(chip, width=34, height=34, corner_radius=17,
                          fg_color=PRIMARY_SOFT)
        av.pack(side="left", padx=(10, 10), pady=8)
        av.pack_propagate(False)
        ctk.CTkLabel(av, text=(self.session["username"][:1].upper() or "?"),
                     font=_fw(14, "bold"),
                     text_color=PRIMARY).place(relx=.5, rely=.5, anchor="center")
        ubox = ctk.CTkFrame(chip, fg_color="transparent")
        ubox.pack(side="left", fill="x", expand=True, pady=8)
        ctk.CTkLabel(ubox, text=self.session["username"], font=_fw(13, "bold"),
                     text_color=TEXT, anchor="w").pack(anchor="w")
        ctk.CTkLabel(ubox, text="Sesión activa", font=_fw(11),
                     text_color=SUCCESS, anchor="w").pack(anchor="w")
        ctk.CTkButton(foot, text="  Cerrar sesión", height=40,
                      corner_radius=10, font=_fw(13, "bold"),
                      fg_color="transparent", hover_color=BG_ELEV_2,
                      text_color=DANGER, border_width=1,
                      border_color=BORDER, command=self._logout).pack(
                          fill="x")

        # Contenedor de páginas
        self.pages = {}
        todas = (NAV_GROUPS[0][1] + NAV_GROUPS[1][1] +
                 NAV_GROUPS[2][1] + NAV_GROUPS[3][1])
        for _iconk, page, _label, _tip in todas:
            frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
            self.pages[page] = frame
        for page, frame in self.pages.items():
            frame.grid(row=0, column=1, sticky="nsew", padx=34, pady=26)
            frame.grid_forget()

        # Vista inicial del usuario
        self.show_page("panel")

    def _nav_item(self, row: int, icon: str, page: str, label: str) -> None:
        btn = ctk.CTkButton(self.sidebar, text=f"   {label}", height=40,
                            corner_radius=10, anchor="w",
                            font=_fw(13, "bold"), compound="left",
                            fg_color="transparent", text_color=TEXT_MUTED,
                            hover_color=BG_ELEV_2, command=lambda: self.show_page(page))
        btn.grid(row=row, column=0, padx=12, pady=2, sticky="ew")
        self.page_buttons[page] = btn

    def _set_active(self, page: str) -> None:
        for key, btn in self.page_buttons.items():
            if key == page:
                btn.configure(text_color=PRIMARY, fg_color=PRIMARY_SOFT)
            else:
                btn.configure(text_color=TEXT_MUTED, fg_color="transparent")

    def show_page(self, page: str) -> None:
        self._set_active(page)
        for p, frame in self.pages.items():
            if p == page:
                frame.grid(row=0, column=1, sticky="nsew", padx=34, pady=26)
                for w in frame.winfo_children():
                    w.destroy()
                getattr(self, f"_render_{page}")(frame)
            else:
                frame.grid_forget()

    # ══════════════════════════════════════════════════════════
    #  PANEL GENERAL
    # ══════════════════════════════════════════════════════════

    def _render_panel(self, frame) -> None:
        self._page_header(frame, "inicio", "Panel general",
                          "Tu estado, tus accesos y los siguientes pasos.")
        last = get_last_session(self.session["user_id"])

        if not last:
            empty = ctk.CTkFrame(frame, fg_color=BG_ELEV, corner_radius=DS.RADII["card"],
                                 border_width=1, border_color=BORDER)
            empty.pack(fill="x", pady=(8, 16))
            self._glyph_label(empty, "evaluacion", size=22, color=PRIMARY).pack(pady=(26, 6))
            ctk.CTkLabel(empty, text="Aún no hay datos", font=_fw(18, "bold"),
                         text_color=TEXT).pack()
            ctk.CTkLabel(empty, text=(
                "Inicia tu transformación con una evaluación guiada de 5 pasos: "
                "el motor construirá tu plan con total transparencia."),
                font=_fw(13), text_color=TEXT_MUTED, justify="left",
                wraplength=560).pack(pady=(4, 18))
            ctk.CTkButton(empty, text="  Nueva evaluación", height=44,
                          corner_radius=10, font=_fw(14, "bold"),
                          fg_color=PRIMARY, hover_color=PRIMARY_HOV,
                          text_color="#04161A",
                          command=lambda: self.show_page("nueva")).pack(
                              pady=(0, 26))
            return

        progress = get_progress_summary(self.session["user_id"])
        suits = ctk.CTkFrame(frame, fg_color="transparent")
        suits.pack(fill="x", pady=(4, 18))
        delta_p = progress["delta_peso_kg"]
        p_color = SUCCESS if delta_p <= 0 else WARNING
        for col, card in enumerate([
            self._metric_card(suits, "Evaluaciones", str(progress["sesiones"]),
                              "registradas", ACCENT, "historial"),
            self._metric_card(suits, "Cambio de peso",
                              f"{'+' if delta_p > 0 else ''}{delta_p:.1f} kg",
                              "desde la primera", p_color, "grafico"),
            self._metric_card(suits, "Ajuste calórico",
                              f"{'+' if progress['delta_calorias'] > 0 else ''}"
                              f"{progress['delta_calorias']:.0f} kcal",
                              "variación objetivo", VIOLET, "calculadora"),
        ]):
            card.grid(row=0, column=col, padx=(0 if col == 0 else 10, 0),
                      sticky="nsew")
        for col in range(3):
            suits.grid_columnconfigure(col, weight=1)

        cols = ctk.CTkFrame(frame, fg_color="transparent")
        cols.pack(fill="both", expand=True)
        cols.grid_columnconfigure(0, weight=2)
        cols.grid_columnconfigure(1, weight=3)

        info = ctk.CTkFrame(cols, fg_color=BG_ELEV, corner_radius=DS.RADII["card"],
                            border_width=1, border_color=BORDER)
        info.grid(row=0, column=0, sticky="nsew", padx=(0, 12))
        self._section_title(info, "perfil", "Métricas actuales")
        filas = [
            ("Edad",   f"{last.get('age', 0)} años"),
            ("Peso",   f"{last.get('weight', 0):.1f} kg"),
            ("Estatura", f"{last.get('height', 0):.0f} cm"),
            ("Grasa",  (f"{last.get('body_fat_pct', 0):.1f} %"
                        if last.get("body_fat_pct", 0) else "—")),
            ("IMC",    f"{last.get('imc', 0):.1f}"),
            ("Objetivo", OBJECTIVE_LABELS.get(last.get("objective", ""), "—")),
            ("Meta calórica", f"{last.get('target_calories', 0):.0f} kcal/día"),
        ]
        for label, valor in filas:
            row = ctk.CTkFrame(info, fg_color="transparent")
            row.pack(fill="x", padx=18, pady=5)
            ctk.CTkLabel(row, text=label.upper(), font=_fw(11, "bold"),
                         text_color=TEXT_FAINT).pack(side="left")
            ctk.CTkLabel(row, text=valor, font=_fw(13, "bold"),
                         text_color=TEXT).pack(side="right")

        graph = ctk.CTkFrame(cols, fg_color=BG_ELEV, corner_radius=DS.RADII["card"],
                             border_width=1, border_color=BORDER)
        graph.grid(row=0, column=1, sticky="nsew", padx=(12, 0))
        self._section_title(graph, "grafico", "Evolución de peso")
        self._render_graph(graph)

    def _render_graph(self, parent) -> None:
        history = get_user_history(self.session["user_id"])
        if len(history) < 2:
            ctk.CTkLabel(parent, text=(
                "Necesitas al menos 2 evaluaciones para visualizar la evolución."),
                font=_fw(12), text_color=TEXT_MUTED).pack(pady=(24, 24))
            return
        if self._graph_canvas is not None:
            try:
                self._graph_canvas.get_tk_widget().destroy()
                plt.close(self._graph_canvas.figure)
            except Exception:
                pass
            self._graph_canvas = None

        fechas = [h.get("saved_at", "").split(" ")[0] for h in history]
        pesos  = [h.get("weight", 0) for h in history]
        fig, ax = plt.subplots(figsize=(5.6, 2.9), dpi=100)
        fig.patch.set_facecolor(BG_ELEV)
        ax.set_facecolor(BG_ELEV)
        ax.plot(fechas, pesos, color=PRIMARY, marker="o", linewidth=2,
                markersize=5.5, markerfacecolor=BG_ELEV_2,
                markeredgecolor=PRIMARY, markeredgewidth=1.4)
        ax.fill_between(range(len(pesos)), pesos, color=PRIMARY, alpha=.08)
        ax.tick_params(colors=TEXT_MUTED, labelsize=9)
        for spine in ax.spines.values():
            spine.set_color(BORDER)
        ax.yaxis.grid(True, color=BORDER, linewidth=.7, alpha=.6)
        ax.set_ylabel("Peso (kg)", color=TEXT_MUTED, fontsize=9)
        plt.xticks(rotation=18)
        plt.tight_layout()
        canvas = FigureCanvasTkAgg(fig, master=parent)
        self._graph_canvas = canvas
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=14, pady=(4, 14))

    # ══════════════════════════════════════════════════════════
    #  NUEVA EVALUACIÓN (asistente en 5 pasos)
    # ══════════════════════════════════════════════════════════

    def _render_nueva(self, frame) -> None:
        self._page_header(frame, "evaluacion", "Nueva evaluación",
                          "Cinco pasos guiados con validación en cada uno. "
                          "Nada se pierde si cambias de página.")
        self.wz_step = max(1, min(5, self.wz_step))
        if not self.wz_values:
            self._wz_seed_defaults()
        self._wz_build_step(frame)

    def _wz_seed_defaults(self, entry: dict | None = None) -> None:
        """Siembra el borrador del asistente con una sesión guardada (o la última)."""
        last = entry or get_last_session(self.session["user_id"]) or {}
        self.wz_values = {
            "age": last.get("age", 25),
            "sex": "femenino" if last.get("sex") == "femenino" else "masculino",
            "weight": float(last.get("weight", 70.0)),
            "height": float(last.get("height", 172.0)),
            "body_fat_pct": float(last.get("body_fat_pct", 0) or 0.0),
            "objective": last.get("objective", "mantenimiento"),
            "activity_level": last.get("activity_level", "ligero"),
            "experience": last.get("experience", "principiante"),
            "meal_frequency": last.get("meal_frequency", 3),
            "training_place": last.get("training_place", "casa"),
            "equipment": list(last.get("equipment", []) or []),
            "injuries": list(last.get("injuries", []) or []),
            "injury_severity": last.get("injury_severity", "ninguna"),
            "balance_issues": bool(last.get("balance_issues", False)),
            "red_flags": list(last.get("red_flags", []) or []),
            "notes": last.get("notes", ""),
            "diet_type": last.get("diet_type", "omnivoro"),
            "allergies": list(last.get("allergies", []) or []),
            "intolerances": list(last.get("intolerances", []) or []),
            "preferences": list(last.get("preferences", []) or []),
        }

    def _wz_stepper(self, parent) -> None:
        bar = ctk.CTkFrame(parent, fg_color="transparent")
        bar.pack(fill="x", pady=(4, 16))
        for i, title in enumerate(STEP_TITLES, start=1):
            estado = "active" if i == self.wz_step else (
                "done" if i < self.wz_step else "todo")
            seg = ctk.CTkFrame(bar, fg_color=
                               (PRIMARY_SOFT if estado == "active" else
                                (BG_ELEV if estado == "done" else "transparent")),
                               corner_radius=10, border_width=1,
                               border_color=(PRIMARY if estado == "active" else
                                             (BORDER if estado == "done" else BORDER)))
            seg.pack(side="left", fill="x", expand=True,
                     padx=(0 if i == 1 else 6, 0))
            color = PRIMARY if estado == "active" else (
                SUCCESS if estado == "done" else TEXT_FAINT)
            num = self._glyph_label(seg, STEP_ICONS[i - 1], size=13, color=color)
            num.pack(side="left", padx=(10, 6), pady=9)
            txt = ctk.CTkLabel(seg, text=title[:16], font=_fw(11, "bold"),
                               text_color=color)
            txt.pack(side="left", pady=9)
            if i < self.wz_step:
                seg.bind("<Button-1>",
                         lambda _e, s=i: self._wz_jump_to(s, parent))
                num.bind("<Button-1>",
                         lambda _e, s=i: self._wz_jump_to(s, parent))
                txt.bind("<Button-1>",
                         lambda _e, s=i: self._wz_jump_to(s, parent))

    # ── Construcción de cada paso ─────────────────────────────

    def _wz_build_step(self, frame: ctk.CTkScrollableFrame) -> None:
        for w in frame.winfo_children():
            w.destroy()
        self.wz_error = None
        self._wz_stepper(frame)

        card = ctk.CTkFrame(frame, fg_color=BG_ELEV, corner_radius=DS.RADII["card"],
                            border_width=1, border_color=BORDER)
        card.pack(fill="x", pady=(0, 14))
        self._section_title(card, STEP_ICONS[self.wz_step - 1],
                            f"Paso {self.wz_step} de 5 · {STEP_TITLES[self.wz_step - 1]}")
        self.wz_widgets = {}
        getattr(self, f"_wz_paso_{self.wz_step}")(card)
        self.wz_err_lbl = self._inline_error(card)

        # Navegación
        nav = ctk.CTkFrame(frame, fg_color="transparent")
        nav.pack(fill="x", pady=(8, 0))
        if self.wz_step > 1:
            ctk.CTkButton(nav, text="  Volver", height=44, corner_radius=10,
                          font=_fw(14, "bold"), fg_color=BG_ELEV_2,
                          hover_color=BG_ELEV_3, text_color=TEXT,
                          compound="left",
                          command=lambda: self._wz_go(-1, frame)).pack(
                              side="left")
        else:
            ctk.CTkButton(nav, text="  Cancelar", height=44, corner_radius=10,
                          font=_fw(14, "bold"), fg_color="transparent",
                          hover_color=BG_ELEV_2, text_color=TEXT_MUTED,
                          border_width=1, border_color=BORDER,
                          command=lambda: self.show_page("panel")).pack(
                              side="left")
        if self.wz_step < 5:
            ctk.CTkButton(nav, text="Continuar  ", height=44, corner_radius=10,
                          font=_fw(14, "bold"), fg_color=PRIMARY,
                          hover_color=PRIMARY_HOV, text_color="#04161A",
                          compound="right",
                          command=lambda: self._wz_go(1, frame)).pack(
                              side="right", padx=(10, 0))
        else:
            ctk.CTkButton(nav, text="  Generar plan", height=44,
                          corner_radius=10, font=_fw(14, "bold"),
                          fg_color=PRIMARY, hover_color=PRIMARY_HOV,
                          text_color="#04161A",
                          command=lambda: self._generar_plan(frame)).pack(
                              side="right", padx=(10, 0))

    def _wz_go(self, delta: int, frame) -> None:
        self._wz_absorb()
        destino = self.wz_step + delta
        if destino < 1:
            destino = 1
        if destino > 5:
            destino = 5
        if delta > 0:
            errores = self._wz_validate_step(self.wz_step)
            if errores:
                self.wz_err_lbl.configure(
                    text="Revisa los siguientes campos:\n"
                    + "\n".join(f"• {campo}: {msj}"
                                for campo, msj in errores.items()))
                return
        self.wz_step = destino
        self._wz_build_step(frame)

    def _wz_jump_to(self, destino: int, frame) -> None:
        """Saltar a un paso completado conserva los valores absorbidos."""
        self._wz_absorb()
        self.wz_step = destino
        self._wz_build_step(frame)

    def _wz_absorb(self) -> None:
        """Copia los widgets del paso actual al borrador durable wz_values."""
        w = self.wz_widgets
        step = self.wz_step
        if step == 1:
            self.wz_values.update({
                "age": self._wz_int(w.get("age")),
                "sex": ("femenino" if w["sex"].get() == "Femenino"
                        else "masculino"),
                "weight": self._wz_float(w.get("weight")),
                "height": self._wz_float(w.get("height")),
                "body_fat_pct": self._wz_float(w.get("bodyfat"), 0.0),
            })
        elif step == 2:
            self.wz_values.update({
                "objective": self._rev(OBJECTIVE_LABELS, w["objective"].get()),
                "activity_level": self._rev(ACTIVITY_LABELS, w["activity"].get()),
                "experience": self._rev(EXPERIENCE_LABELS, w["exp"].get()),
                "meal_frequency": self._freq_val(w.get("freq")),
                "training_place": self._rev(TRAINING_PLACE_LABELS, w["place"].get()),
                "equipment": [k for k, v in w["equip"].items() if v.get()],
            })
        elif step == 3:
            self.wz_values.update({
                "injuries": [k for k, v in w["inj"].items() if v.get()],
                "injury_severity": self._rev(INJURY_SEVERITY_OPTIONS,
                                             w["sev"].get()),
                "balance_issues": bool(w["bal"].get()),
                "red_flags": [k for k, v in w["rf"].items() if v.get()],
            })
            tb = w.get("notes_tb")
            if tb is not None:
                self.wz_values["notes"] = tb.get("0.0", "end").strip()
        elif step == 4:
            self.wz_values.update({
                "diet_type": self._rev(DIET_TYPES, w["diet"].get()),
                "preferences": [k for k, v in w["pref"].items() if v.get()],
            })
            al, it = [], []
            for k, var in w["alg"].items():
                if not var.get():
                    continue
                mp = LEGACY_ALLERGY_MAP.get(k)
                if mp:
                    (al if mp[0] == "allergies" else it).append(mp[1])
                else:
                    al.append(k)
            self.wz_values["allergies"] = al
            self.wz_values["intolerances"] = it
        elif step == 5:
            tb = w.get("notes_tb")
            if tb is not None:
                self.wz_values["notes"] = tb.get("0.0", "end").strip()
        self.wz_values.setdefault("meal_frequency", 3)
        self.wz_values.setdefault("training_place", "casa")

    # ── Paso 1: datos personales ──────────────────────────────

    def _wz_paso_1(self, card) -> None:
        w = self.wz_widgets
        g = ctk.CTkFrame(card, fg_color="transparent")
        g.pack(fill="x", padx=18, pady=(14, 16))
        g.grid_columnconfigure((0, 1), weight=1)
        w["age"] = self._add_entry(g, 0, 0, "EDAD (AÑOS)", "Ej: 34",
                                   self.wz_values["age"], "int")
        w["sex"] = self._add_option(g, 0, 1, "SEXO",
                                    ["Masculino", "Femenino"],
                                    "Masculino" if self.wz_values["sex"] == "masculino"
                                    else "Femenino")
        w["weight"] = self._add_entry(g, 1, 0, "PESO (KG)", "Ej: 88.2",
                                      self.wz_values["weight"], "float")
        w["height"] = self._add_entry(g, 1, 1, "ESTATURA (CM)", "Ej: 175",
                                      self.wz_values["height"], "float")
        w["bodyfat"] = self._add_entry(g, 2, 0, "% GRASA CORPORAL (OPCIONAL)",
                                       "0 si lo desconoces",
                                       (self.wz_values["body_fat_pct"] or 0.0),
                                       "float")
        ctk.CTkLabel(g, text=(
            "El porcentaje de grasa se usa para refinar el cálculo metabólico. "
            "Si lo desconoces, déjalo en 0."),
            font=_fw(11), text_color=TEXT_FAINT, justify="left",
            wraplength=620, anchor="w").grid(row=3, column=0, columnspan=2,
                                             sticky="w", pady=(10, 0))

    # ── Paso 2: objetivo y preparación ────────────────────────

    def _wz_paso_2(self, card) -> None:
        w = self.wz_widgets
        g = ctk.CTkFrame(card, fg_color="transparent")
        g.pack(fill="x", padx=18, pady=(14, 16))
        g.grid_columnconfigure((0, 1), weight=1)
        w["objective"] = self._add_option(
            g, 0, 0, "OBJETIVO PRINCIPAL", list(OBJECTIVE_LABELS.values()),
            OBJECTIVE_LABELS.get(self.wz_values["objective"],
                                 list(OBJECTIVE_LABELS.values())[4]))
        w["exp"] = self._add_option(
            g, 0, 1, "EXPERIENCIA", list(EXPERIENCE_LABELS.values()),
            EXPERIENCE_LABELS.get(self.wz_values["experience"],
                                  list(EXPERIENCE_LABELS.values())[0]))
        w["freq"] = self._add_option(
            g, 1, 0, "COMIDAS AL DÍA", ["3 comidas", "4 comidas", "5 comidas"],
            f"{self.wz_values.get('meal_frequency', 3)} comidas")
        w["activity"] = self._add_option(
            g, 1, 1, "NIVEL DE ACTIVIDAD DIARIA", list(ACTIVITY_LABELS.values()),
            ACTIVITY_LABELS.get(self.wz_values["activity_level"],
                                list(ACTIVITY_LABELS.values())[1]))
        w["place"] = self._add_option(
            g, 2, 0, "LUGAR DE ENTRENAMIENTO", list(TRAINING_PLACE_LABELS.values()),
            TRAINING_PLACE_LABELS.get(self.wz_values["training_place"],
                                      TRAINING_PLACE_LABELS["casa"]))

        ctk.CTkLabel(g, text="EQUIPO DISPONIBLE (SI ENTRENAS EN CASA)",
                     font=_fw(11, "bold"), text_color=TEXT_FAINT,
                     anchor="w").grid(row=3, column=0, columnspan=2,
                                      sticky="w", pady=(16, 6))
        eqrow = ctk.CTkFrame(g, fg_color="transparent")
        eqrow.grid(row=4, column=0, columnspan=2, sticky="ew")
        w["equip"] = {}
        for i, (key, lbl) in enumerate(EQUIPMENT_OPTIONS.items()):
            var = ctk.BooleanVar(value=key in (self.wz_values.get("equipment") or []))
            ck = ctk.CTkCheckBox(eqrow, text=lbl, variable=var,
                                 font=_fw(12), text_color=TEXT_MUTED,
                                 fg_color=PRIMARY, hover_color=PRIMARY_HOV,
                                 border_color=BORDER_STRONG,
                                 checkbox_width=18, checkbox_height=18)
            ck.grid(row=i // 2, column=i % 2, sticky="w", padx=(0, 24), pady=4)
            w["equip"][key] = var
        eqrow.grid_columnconfigure((0, 1), weight=1)
        ctk.CTkLabel(g, text=(
            "Si eliges 'Gimnasio', el equipo de casa se ignora en la rutina."),
            font=_fw(11), text_color=TEXT_FAINT, justify="left",
            anchor="w").grid(row=5, column=0, columnspan=2, sticky="w",
                             pady=(8, 0))

    # ── Paso 3: salud y seguridad ─────────────────────────────

    def _wz_paso_3(self, card) -> None:
        w = self.wz_widgets
        g = ctk.CTkFrame(card, fg_color="transparent")
        g.pack(fill="x", padx=18, pady=(14, 6))

        ctk.CTkLabel(g, text="ZONAS CON MOLESTIA O LESIÓN",
                     font=_fw(11, "bold"), text_color=TEXT_FAINT,
                     anchor="w").pack(anchor="w", pady=(4, 6))
        w["inj"] = {}
        injrow = ctk.CTkFrame(g, fg_color="transparent")
        injrow.pack(fill="x")
        _sel = set(self.wz_values.get("injuries") or [])
        for i, (key, lbl) in enumerate(INJURY_OPTIONS.items()):
            var = ctk.BooleanVar(value=key in _sel)
            ck = ctk.CTkCheckBox(injrow, text=lbl, variable=var,
                                 font=_fw(12), text_color=TEXT_MUTED,
                                 fg_color=PRIMARY, hover_color=PRIMARY_HOV,
                                 border_color=BORDER_STRONG,
                                 checkbox_width=18, checkbox_height=18)
            ck.grid(row=i // 2, column=i % 2, sticky="w", padx=(0, 24), pady=5)
            w["inj"][key] = var
        injrow.grid_columnconfigure((0, 1), weight=1)

        sev = ctk.CTkFrame(g, fg_color="transparent")
        sev.pack(fill="x", pady=(10, 4))
        ctk.CTkLabel(sev, text="INTENSIDAD DE LAS MOLESTIAS",
                     font=_fw(11, "bold"), text_color=TEXT_FAINT,
                     anchor="w").pack(anchor="w", pady=(2, 4))
        w["sev"] = ctk.StringVar(value=INJURY_SEVERITY_OPTIONS.get(
            self.wz_values["injury_severity"],
            list(INJURY_SEVERITY_OPTIONS.values())[0]))
        ctk.CTkOptionMenu(sev, variable=w["sev"],
                          values=list(INJURY_SEVERITY_OPTIONS.values()),
                          height=40, corner_radius=DS.RADII["input"],
                          font=_fw(13), fg_color=BG_ELEV_2,
                          button_color=BG_ELEV_3, button_hover_color=PRIMARY_SOFT,
                          dropdown_fg_color=BG_ELEV_3,
                          dropdown_hover_color=PRIMARY_SOFT,
                          dropdown_text_color=TEXT,
                          text_color=TEXT).pack(fill="x")

        w["bal"] = ctk.BooleanVar(value=bool(self.wz_values["balance_issues"]))
        ctk.CTkCheckBox(g, text="Problemas de equilibrio / historial de caídas",
                        variable=w["bal"], font=_fw(12), text_color=TEXT_MUTED,
                        fg_color=PRIMARY, hover_color=PRIMARY_HOV,
                        border_color=BORDER_STRONG,
                        checkbox_width=18, checkbox_height=18).pack(
                            anchor="w", pady=(10, 4))

        alerta = ctk.CTkFrame(g, fg_color="#2A0E0E", corner_radius=10,
                              border_width=1, border_color=CRITICAL)
        alerta.pack(fill="x", pady=(6, 8))
        self._glyph_label(alerta, "critico", size=15, color=CRITICAL).pack(
            side="left", padx=(14, 10), pady=12)
        ctk.CTkLabel(alerta, text=(
            "Señales de alarma: si marcas alguna, FitExpert suspende la "
            "prescripción de ejercicio y te deriva a evaluación profesional."),
            font=_fw(12), text_color="#FECACA", justify="left",
            wraplength=560, anchor="w").pack(side="left", pady=12)

        ctk.CTkLabel(g, text="SEÑALES DE ALARMA",
                     font=_fw(11, "bold"), text_color=CRITICAL,
                     anchor="w").pack(anchor="w", pady=(4, 4))
        w["rf"] = {}
        rfrow = ctk.CTkFrame(g, fg_color="transparent")
        rfrow.pack(fill="x", pady=(0, 6))
        _sel_rf = set(self.wz_values.get("red_flags") or [])
        for i, (key, lbl) in enumerate(INJURY_RED_FLAGS.items()):
            var = ctk.BooleanVar(value=key in _sel_rf)
            ck = ctk.CTkCheckBox(rfrow, text=lbl, variable=var,
                                 font=_fw(12), text_color="#FCA5A5",
                                 fg_color=CRITICAL, hover_color=DANGER,
                                 border_color="#5C2A2A",
                                 checkbox_width=18, checkbox_height=18)
            ck.grid(row=i, column=0, sticky="w", pady=4)
            w["rf"][key] = var

        ctk.CTkLabel(g, text="OBSERVACIONES (OPCIONAL)",
                     font=_fw(11, "bold"), text_color=TEXT_FAINT,
                     anchor="w").pack(anchor="w", pady=(10, 4))
        w["notes_tb"] = ctk.CTkTextbox(g, height=64, wrap="word",
                                       font=_fw(12), fg_color=BG_ELEV_2,
                                       text_color=TEXT, border_color=BORDER,
                                       border_width=1, corner_radius=10)
        w["notes_tb"].insert("0.0", self.wz_values.get("notes", "") or "")
        w["notes_tb"].pack(fill="x", pady=(0, 14))

    # ── Paso 4: nutrición ─────────────────────────────────────

    def _wz_paso_4(self, card) -> None:
        w = self.wz_widgets
        g = ctk.CTkFrame(card, fg_color="transparent")
        g.pack(fill="x", padx=18, pady=(14, 10))
        g.grid_columnconfigure((0, 1), weight=1)
        w["diet"] = self._add_option(
            g, 0, 0, "TIPO DE DIETA", list(DIET_TYPES.values()),
            DIET_TYPES.get(self.wz_values["diet_type"],
                           list(DIET_TYPES.values())[0]))

        ctk.CTkLabel(g, text="ALERGIAS (EXCLUSIÓN ESTRICTA)",
                     font=_fw(11, "bold"), text_color=TEXT_FAINT,
                     anchor="w").grid(row=1, column=0, sticky="w", pady=(14, 6))
        ctk.CTkLabel(g, text="PREFERENCIAS DE CONSUMO",
                     font=_fw(11, "bold"), text_color=TEXT_FAINT,
                     anchor="w").grid(row=1, column=1, sticky="w", pady=(14, 6))

        alg_box = ctk.CTkFrame(g, fg_color="transparent")
        alg_box.grid(row=2, column=0, sticky="nw", padx=(0, 20))
        w["alg"] = {}
        _sel_alg = set()
        for k in ALERGIA_UI:
            mp = LEGACY_ALLERGY_MAP.get(k)
            if mp:
                cont = (self.wz_values.get("allergies") or []
                        if mp[0] == "allergies"
                        else self.wz_values.get("intolerances") or [])
                if mp[1] in cont:
                    _sel_alg.add(k)
        for i, (key, lbl) in enumerate(ALERGIA_UI.items()):
            var = ctk.BooleanVar(value=key in _sel_alg)
            ck = ctk.CTkCheckBox(alg_box, text=lbl, variable=var,
                                 font=_fw(12), text_color=TEXT_MUTED,
                                 fg_color=PRIMARY, hover_color=PRIMARY_HOV,
                                 border_color=BORDER_STRONG,
                                 checkbox_width=18, checkbox_height=18)
            ck.pack(anchor="w", pady=4)
            w["alg"][key] = var

        pref_box = ctk.CTkFrame(g, fg_color="transparent")
        pref_box.grid(row=2, column=1, sticky="nw")
        w["pref"] = {}
        _sel_pref = set(self.wz_values.get("preferences") or [])
        for i, (key, lbl) in enumerate(PREFERENCE_OPTIONS.items()):
            var = ctk.BooleanVar(value=key in _sel_pref)
            ck = ctk.CTkCheckBox(pref_box, text=lbl, variable=var,
                                 font=_fw(12), text_color=TEXT_MUTED,
                                 fg_color=PRIMARY, hover_color=PRIMARY_HOV,
                                 border_color=BORDER_STRONG,
                                 checkbox_width=18, checkbox_height=18)
            ck.pack(anchor="w", pady=4)
            w["pref"][key] = var

        ctk.CTkLabel(g, text=(
            "Las alergias excluyen la familia completa y sus derivados; las "
            "intolerancias evitan las fuentes principales. El sistema nunca "
            "afirma \"100% seguro\"."),
            font=_fw(11), text_color=TEXT_FAINT, justify="left",
            wraplength=620, anchor="w").grid(row=3, column=0, columnspan=2,
                                             sticky="w", pady=(12, 0))

    # ── Paso 5: revisión final ────────────────────────────────

    def _wz_paso_5(self, card) -> None:
        w = self.wz_widgets
        self._wz_absorb()
        resumen = ctk.CTkFrame(card, fg_color="transparent")
        resumen.pack(fill="x", padx=18, pady=(14, 12))
        v = self.wz_values
        filas = [
            ("Perfil",    f"Edad {v['age']} · {v['sex'].capitalize()} · "
                          f"{v['weight']:.1f} kg · {v['height']:.1f} cm"),
            ("Objetivo",  OBJECTIVE_LABELS.get(v["objective"], v["objective"])),
            ("Actividad", ACTIVITY_LABELS.get(v["activity_level"], v["activity_level"])),
            ("Experiencia", EXPERIENCE_LABELS.get(v["experience"], v["experience"])),
            ("Lugar",     TRAINING_PLACE_LABELS.get(v["training_place"], v["training_place"])),
            ("Dieta",     DIET_TYPES.get(v["diet_type"], v["diet_type"])),
            ("Comidas",   f"{v.get('meal_frequency', 3)} al día"),
            ("Lesiones",  ", ".join(INJURY_OPTIONS.get(k, k)
                                    for k in (v.get("injuries") or [])) or "Ninguna"),
            ("Alergias",  ", ".join(ALLERGY_OPTIONS.get(k, k)
                                    for k in (v.get("allergies") or [])) or "Ninguna"),
            ("Intolerancias", ", ".join(INTOLERANCE_OPTIONS.get(k, k)
                                        for k in (v.get("intolerances") or [])) or "Ninguna"),
        ]
        for label, valor in filas:
            row = ctk.CTkFrame(resumen, fg_color=BG_ELEV_2, corner_radius=8)
            row.pack(fill="x", pady=3)
            ctk.CTkLabel(row, text=label.upper(), font=_fw(11, "bold"),
                         text_color=TEXT_FAINT, width=130, anchor="w").pack(
                             side="left", padx=(14, 8), pady=9)
            ctk.CTkLabel(row, text=valor, font=_fw(12),
                         text_color=TEXT, anchor="w").pack(side="left", pady=9)

        if v.get("red_flags"):
            rf = ctk.CTkFrame(card, fg_color="#2A0E0E", corner_radius=10,
                              border_width=1, border_color=CRITICAL)
            rf.pack(fill="x", padx=18, pady=(0, 12))
            ctk.CTkLabel(rf, text=(
                "Se han marcado señales de alarma: el plan NO incluirá "
                "prescripción de ejercicio y recomendará evaluación profesional."),
                font=_fw(12, "bold"), text_color="#FECACA", justify="left",
                wraplength=600, anchor="w").pack(anchor="w", padx=16, pady=12)

        ctk.CTkLabel(card, text="OBSERVACIONES FINALES (OPCIONAL)",
                     font=_fw(11, "bold"), text_color=TEXT_FAINT,
                     anchor="w").pack(anchor="w", padx=18, pady=(6, 4))
        w["notes_tb"] = ctk.CTkTextbox(card, height=70, wrap="word",
                                       font=_fw(12), fg_color=BG_ELEV_2,
                                       text_color=TEXT, border_color=BORDER,
                                       border_width=1, corner_radius=10)
        w["notes_tb"].insert("0.0", v.get("notes", "") or "")
        w["notes_tb"].pack(fill="x", padx=18, pady=(0, 10))

    # ── Widgets del asistente ─────────────────────────────────

    def _add_entry(self, parent, row: int, col: int, label: str,
                   placeholder: str, valor, tipo: str) -> ctk.StringVar:
        f = ctk.CTkFrame(parent, fg_color="transparent")
        f.grid(row=row, column=col, sticky="ew", padx=(0, 14), pady=8)
        ctk.CTkLabel(f, text=label, font=_fw(11, "bold"), text_color=TEXT_FAINT,
                     anchor="w").pack(anchor="w", pady=(0, 4))
        var = ctk.StringVar(value=self._fmt(valor))
        vcmd_cb = self._vi if tipo == "int" else self._vf
        ctk.CTkEntry(f, textvariable=var, placeholder_text=placeholder, height=42,
                     corner_radius=DS.RADII["input"], font=_fw(14),
                     fg_color=BG_ELEV_2, border_color=BORDER, border_width=1,
                     text_color=TEXT, placeholder_text_color=TEXT_FAINT,
                     validate="key",
                     validatecommand=(self.register(vcmd_cb), "%P")).pack(
                         fill="x")
        parent.columnconfigure(col, weight=1)
        return var

    def _add_option(self, parent, row: int, col: int, label: str, values: list,
                    default: str, command=None) -> ctk.StringVar:
        f = ctk.CTkFrame(parent, fg_color="transparent")
        f.grid(row=row, column=col, sticky="ew", padx=(0, 14), pady=8)
        if label:
            ctk.CTkLabel(f, text=label, font=_fw(11, "bold"),
                         text_color=TEXT_FAINT,
                         anchor="w").pack(anchor="w", pady=(0, 4))
        var = ctk.StringVar(value=default)
        ctk.CTkOptionMenu(f, variable=var, values=values, height=42,
                          corner_radius=DS.RADII["input"], font=_fw(13),
                          fg_color=BG_ELEV_2, button_color=BG_ELEV_3,
                          button_hover_color=PRIMARY_SOFT,
                          dropdown_fg_color=BG_ELEV_3,
                          dropdown_hover_color=PRIMARY_SOFT,
                          dropdown_text_color=TEXT, text_color=TEXT,
                          command=command).pack(fill="x")
        if col is not None:
            parent.columnconfigure(col, weight=1)
        return var

    def _wz_int(self, var):
        try:
            return int(float(str(var.get())))
        except (TypeError, ValueError, AttributeError):
            return None

    def _wz_float(self, var, default=None):
        try:
            return float(str(var.get()).replace(",", "."))
        except (TypeError, ValueError, AttributeError):
            return default

    def _fmt(self, valor) -> str:
        if valor is None:
            return ""
        if isinstance(valor, float):
            if valor == int(valor):
                return str(int(valor))
            return f"{valor:.1f}"
        return str(valor)

    def _vi(self, value: str) -> bool:
        """Validación de teclado para enteros (vacío permitido)."""
        if value == "":
            return True
        return value.isdigit() and int(value) <= 250

    def _vf(self, value: str) -> bool:
        """Validación de teclado para decimales (vacío permitido)."""
        if value == "":
            return True
        try:
            return 0.0 <= float(value.replace(",", ".")) <= 500.0
        except ValueError:
            return False

    def _freq_val(self, var) -> int | None:
        """'3 comidas' → 3 (parsing robusto del menú de frecuencia)."""
        try:
            return int(str(var.get()).split()[0])
        except (TypeError, ValueError, AttributeError):
            return None

    def _rev(self, domain: dict, label: str) -> str:
        """Etiqueta humana → clave canónica."""
        for k, v in domain.items():
            if v == label:
                return k
        return label

    def _wz_payload(self) -> dict:
        self._wz_absorb()
        v = self.wz_values
        return {
            "name": self.session["username"],
            "age": v.get("age", ""),
            "sex": v.get("sex", "masculino"),
            "weight": v.get("weight", ""),
            "height": v.get("height", ""),
            "body_fat_pct": v.get("body_fat_pct", 0.0),
            "objective": v.get("objective", "mantenimiento"),
            "activity_level": v.get("activity_level", "ligero"),
            "experience": v.get("experience", "principiante"),
            "training_place": v.get("training_place", "casa"),
            "diet_type": v.get("diet_type", "omnivoro"),
            "meal_frequency": v.get("meal_frequency", 3),
            "injuries": v.get("injuries", []),
            "injuries_labels": [],
            "injury_severity": v.get("injury_severity", "ninguna"),
            "balance_issues": bool(v.get("balance_issues", False)),
            "red_flags": v.get("red_flags", []),
            "equipment": (v.get("equipment", [])
                          if v.get("training_place", "casa") == "casa" else []),
            "allergies": v.get("allergies", []),
            "intolerances": v.get("intolerances", []),
            "preferences": v.get("preferences", []),
            "notes": v.get("notes", ""),
        }

    def _wz_validate_step(self, step: int) -> dict:
        data = self._wz_payload()
        _v, errores, _w = validate_evaluation(data)
        filtrado = {c: m for c, m in errores.items()
                    if c in STEP_FIELDS.get(step, [])}
        return filtrado

    def _wz_field_list(self, errores: dict) -> str:
        return "\n".join(f"• {c.capitalize()}: {m}"
                         for c, m in errores.items())

    def _generar_plan(self, frame) -> None:
        self._wz_absorb()
        data = self._wz_payload()
        valores, errores, advertencias = validate_evaluation(data)
        if errores:
            # Salta al primer paso con campos pendientes y muestra el error allí
            pasos = [s for s, campos in STEP_FIELDS.items()
                     if any(c in errores for c in campos)]
            if pasos:
                destino = min(pasos)
                if destino != self.wz_step:
                    self.wz_step = destino
                    self._wz_build_step(frame)
                    self.wz_err_lbl.configure(
                        text="Hay campos pendientes en este paso:\n"
                        + self._wz_field_list(errores))
                    return
            self.wz_err_lbl.configure(
                text="Datos incompletos:\n" + self._wz_field_list(errores))
            return

        perfil = UserProfile(**valores)
        perfil.user_id = self.session["user_id"]
        perfil.name = self.session["username"]

        motor = InferenceEngine()
        motor.run(perfil)
        rutina = generate_training_plan(perfil)
        plan = generate_nutrition_plan(perfil)
        save_profile(perfil)

        self.current_results = {
            "perfil": perfil, "plan": plan, "rutina": rutina,
            "warnings": advertencias or [],
            "ts": perfil.created_at,
        }
        self.show_page("plan")

    # ══════════════════════════════════════════════════════════
    #  PLAN ACTUAL
    # ══════════════════════════════════════════════════════════

    def _render_plan(self, frame) -> None:
        self._page_header(frame, "plan", "Plan actual",
                          "Nutrición, entrenamiento y decisiones del motor.")
        if not self.current_results:
            empty = ctk.CTkFrame(frame, fg_color=BG_ELEV,
                                 corner_radius=DS.RADII["card"],
                                 border_width=1, border_color=BORDER)
            empty.pack(fill="x", pady=(8, 8))
            self._glyph_label(empty, "plan", size=22, color=PRIMARY).pack(pady=(26, 6))
            ctk.CTkLabel(empty, text="Aún no tienes un plan activo",
                         font=_fw(17, "bold"), text_color=TEXT).pack()
            ctk.CTkLabel(empty, text=(
                "Crea tu primera evaluación guiada: el motor generará el plan "
                "nutricional y el microciclo semanal en segundos."),
                font=_fw(13), text_color=TEXT_MUTED, justify="left",
                wraplength=560).pack(pady=(4, 18))
            ctk.CTkButton(empty, text="  Nueva evaluación", height=44,
                          corner_radius=10, font=_fw(14, "bold"),
                          fg_color=PRIMARY, hover_color=PRIMARY_HOV,
                          text_color="#04161A",
                          command=lambda: self.show_page("nueva")).pack(
                              pady=(0, 26))
            return

        res = self.current_results
        p = res["perfil"]
        plan = res["plan"]
        rutina = res["rutina"]

        # Banners de estado
        if p.red_flags or p.injury_severity == "aguda":
            susp = ctk.CTkFrame(frame, fg_color="#2A0E0E", corner_radius=10,
                                border_width=1, border_color=CRITICAL)
            susp.pack(fill="x", pady=(4, 12))
            self._glyph_label(susp, "critico", size=16, color=CRITICAL).pack(
                side="left", padx=(16, 10), pady=14)
            ctk.CTkLabel(susp, text=(
                "SUSPENSIÓN DE PRESCRIPCIÓN: por señales de alarma o lesión "
                "aguda, FitExpert no prescribe ejercicio. Consulta a un "
                "profesional de la salud antes de retomar la actividad física."),
                font=_fw(13, "bold"), text_color="#FECACA", justify="left",
                wraplength=680, anchor="w").pack(side="left", pady=12)
        elif res["warnings"]:
            warn = ctk.CTkFrame(frame, fg_color="#332409", corner_radius=10,
                                border_width=1, border_color=WARNING)
            warn.pack(fill="x", pady=(4, 12))
            self._glyph_label(warn, "alerta", size=16, color=WARNING).pack(
                side="left", padx=(16, 10), pady=12)
            txt = "\n".join(f"• {w}" for w in res["warnings"])
            ctk.CTkLabel(warn, text="Consideraciones:\n" + txt,
                         font=_fw(12), text_color="#FDE68A", justify="left",
                         wraplength=680, anchor="w").pack(side="left", pady=10)

        head = ctk.CTkFrame(frame, fg_color="transparent")
        head.pack(fill="x", pady=(0, 14))
        info = ctk.CTkFrame(head, fg_color="transparent")
        info.pack(side="left")
        ctk.CTkLabel(info, text=f"{p.name} · {p.created_at}",
                     font=_fw(12), text_color=TEXT_MUTED, anchor="w").pack(
                         anchor="w")
        acciones = ctk.CTkFrame(head, fg_color="transparent")
        acciones.pack(side="right")
        ctk.CTkButton(acciones, text="  Explicabilidad", height=40,
                      corner_radius=10, font=_fw(13, "bold"),
                      fg_color=BG_ELEV_2, hover_color=BG_ELEV_3,
                      text_color=VIOLET, border_width=1, border_color=BORDER,
                      command=lambda: self.show_page("explicacion")).pack(
                          side="left", padx=(0, 10))
        ctk.CTkButton(acciones, text="  Descargar PDF", height=40,
                      corner_radius=10, font=_fw(13, "bold"),
                      fg_color=PRIMARY_SOFT, hover_color=BG_ELEV_3,
                      text_color=PRIMARY, border_width=1, border_color=PRIMARY,
                      command=self._export_pdf).pack(side="left")

        # Banda de KPIs
        kpi = ctk.CTkFrame(frame, fg_color="transparent")
        kpi.pack(fill="x", pady=(0, 16))
        imc_color = (SUCCESS if 18.5 <= p.imc <= 24.9 else
                     (WARNING if p.imc < 18.5 else DANGER))
        for col, card in enumerate([
            self._metric_card(kpi, "IMC", f"{p.imc:.1f}", p.imc_category,
                              imc_color, "diagnostico"),
            self._metric_card(kpi, "TMB", f"{p.tmb:.0f}", "kcal en reposo",
                              TEXT, "corazon"),
            self._metric_card(kpi, "TDEE", f"{p.tdee:.0f}", "kcal de gasto",
                              ACCENT, "grafico"),
            self._metric_card(kpi, "Meta diaria", f"{p.target_calories:.0f}",
                              "kcal objetivo", PRIMARY, "calculadora"),
        ]):
            card.grid(row=0, column=col, padx=(0 if col == 0 else 10, 0),
                      sticky="nsew")
        for col in range(4):
            kpi.grid_columnconfigure(col, weight=1)

        # Pestañas Nutrición / Entrenamiento
        tabs = ctk.CTkTabview(frame, height=430,
                              fg_color=BG_ELEV, corner_radius=DS.RADII["card"],
                              border_width=1, border_color=BORDER,
                              segmented_button_fg_color=BG_ELEV_2,
                              segmented_button_selected_color=PRIMARY_SOFT,
                              segmented_button_selected_hover_color=BG_ELEV_3,
                              segmented_button_unselected_color=BG_ELEV_2,
                              segmented_button_unselected_hover_color=BG_ELEV_3,
                              text_color=TEXT_MUTED)
        tabs.pack(fill="both", expand=True)
        tabs.add("  Nutrición")
        tabs.add("  Entrenamiento")
        self._plan_nut(tabs.tab("  Nutrición"), plan)
        self._plan_trn(tabs.tab("  Entrenamiento"), rutina)

    def _plan_nut(self, tab, plan) -> None:
        m = plan["macros"]
        band = ctk.CTkFrame(tab, fg_color=BG_ELEV_2, corner_radius=10)
        band.pack(fill="x", padx=16, pady=16)
        for col, (glyph, nombre, valor, pct) in enumerate([
            ("nutricion", "Proteínas", f"{m['proteinas']} g", f"{m['p_pct']}%"),
            ("entrenamiento", "Carbohidratos", f"{m['carbohidratos']} g", f"{m['c_pct']}%"),
            ("corazon", "Grasas", f"{m['grasas']} g", f"{m['g_pct']}%"),
        ]):
            cell = ctk.CTkFrame(band, fg_color="transparent")
            cell.grid(row=0, column=col, padx=10, pady=12, sticky="nsew")
            self._glyph_label(cell, glyph, size=15, color=PRIMARY).pack()
            ctk.CTkLabel(cell, text=nombre, font=_fw(11, "bold"),
                         text_color=TEXT_MUTED).pack(pady=(3, 1))
            ctk.CTkLabel(cell, text=valor, font=_fw(17, "bold"),
                         text_color=TEXT).pack()
            ctk.CTkLabel(cell, text=pct, font=_fw(11),
                         text_color=TEXT_FAINT).pack()
        for col in range(3):
            band.grid_columnconfigure(col, weight=1)

        tb = ctk.CTkTextbox(tab, wrap="word", font=_fw(13),
                            fg_color="transparent", text_color=TEXT,
                            border_width=0)
        tb.pack(fill="both", expand=True, padx=16, pady=(0, 16))
        txt = ""
        for label in ("DESAYUNO", "ALMUERZO", "CENA", "SNACKS"):
            key = label.lower().replace("á", "a")
            if plan["plan"].get(key):
                txt += f"{label}\n" + "\n".join(
                    f"  • {x}" for x in plan["plan"][key]) + "\n\n"
        txt += f"HIDRATACIÓN: {plan['plan'].get('hidratacion', '')}"
        if plan.get("sustituciones"):
            txt += "\n\nSUSTITUCIONES POR ALERGIAS:\n"
            for s in plan["sustituciones"]:
                al = ALLERGY_OPTIONS.get(s.get("alergeno", ""),
                                         s.get("alergeno", ""))
                txt += f"  • {al}: {s.get('substitucion', '')}\n"
            txt += ("\nLa seguridad frente a contaminación cruzada depende de "
                    "leer las etiquetas de cada producto.\n")
        tb.insert("0.0", txt)
        tb.configure(state="disabled")

    def _plan_trn(self, tab, rutina) -> None:
        cab = ctk.CTkFrame(tab, fg_color=BG_ELEV_2, corner_radius=10)
        cab.pack(fill="x", padx=16, pady=16)
        self._glyph_label(cab, "entrenamiento", size=16, color=PRIMARY).pack(
            pady=(12, 2))
        ctk.CTkLabel(cab, text=rutina["nombre"].upper(), font=_fw(15, "bold"),
                     text_color=TEXT).pack()
        ctk.CTkLabel(cab, text=f"{rutina['tipo']}  ·  {rutina['dias']}",
                     font=_fw(12), text_color=TEXT_MUTED).pack(pady=(0, 12))

        tb = ctk.CTkTextbox(tab, wrap="word", font=_fw(13),
                            fg_color="transparent", text_color=TEXT,
                            border_width=0)
        tb.pack(fill="both", expand=True, padx=16, pady=(0, 16))
        trn = ""
        for day in rutina.get("semana", []):
            if day["descanso"]:
                trn += f"■ {day['dia'].upper()} — Descanso\n\n"
            else:
                trn += f"■ {day['dia'].upper()} — {day['grupo']}\n"
                for ej in day.get("ejercicios", []):
                    trn += f"    • {ej[0]}: {ej[1]} [{ej[2]}]\n"
                trn += f"    (descanso entre series: {day['descanso_entre_series']})\n\n"
        if rutina.get("lesiones_consideradas"):
            trn += ("Restricciones por lesión: " +
                    ", ".join(rutina["lesiones_consideradas"]) + "\n\n")
        if rutina.get("alternativas_aplicadas"):
            trn += ("SUSTITUCIONES POR LESIÓN:\n" +
                    "\n".join(f"    • {a}" for a in rutina["alternativas_aplicadas"]) +
                    "\n\n")
        if rutina.get("cardio_extra"):
            trn += f"Cardio complementario: {rutina['cardio_extra']}\n"
        tb.insert("0.0", trn)
        tb.configure(state="disabled")

    def _export_pdf(self) -> None:
        if not self.current_results:
            return
        res = self.current_results
        default_name = (f"Plan_FitExpert_{res['perfil'].name.replace(' ', '_')}"
                        f"_{res['ts'].split(' ')[0]}.pdf")
        path = filedialog.asksaveasfilename(
            defaultextension=".pdf", filetypes=[("PDF", "*.pdf")],
            initialfile=default_name, title="Guardar PDF del plan")
        if not path:
            return
        try:
            export_pdf(res["perfil"], res["plan"], res["rutina"], path)
            self.pdf_last_path = path
            self._open_pdf(path)
        except Exception as e:
            # No exponer tracebacks: banner inline
            msg = ctk.CTkToplevel(self)
            msg.geometry("460x180")
            msg.configure(fg_color=BG)
            ctk.CTkLabel(msg, text="No se pudo generar el PDF",
                         font=_fw(16, "bold"), text_color=DANGER).pack(pady=(24, 8))
            ctk.CTkLabel(msg, text=(
                "Ocurrió un error al exportar el documento. "
                f"Detalle: {e}"), font=_fw(12), text_color=TEXT_MUTED,
                wraplength=400, justify="left").pack(pady=(0, 14))
            ctk.CTkButton(msg, text="Cerrar", width=120, height=36,
                          fg_color=PRIMARY, hover_color=PRIMARY_HOV,
                          text_color="#04161A", command=msg.destroy).pack()

    def _open_pdf(self, path: str) -> None:
        try:
            if platform.system() == "Darwin":
                subprocess.call(("open", path))
            elif platform.system() == "Windows":
                os.startfile(path)
            else:
                subprocess.call(("xdg-open", path))
        except Exception:
            pass

    # ══════════════════════════════════════════════════════════
    #  HISTORIAL
    # ══════════════════════════════════════════════════════════

    def _render_historial(self, frame) -> None:
        self._page_header(frame, "historial", "Historial",
                          "Todas tus evaluaciones, de la más reciente a la primera.")
        history = get_user_history(self.session["user_id"])
        if not history:
            empty = ctk.CTkFrame(frame, fg_color=BG_ELEV,
                                 corner_radius=DS.RADII["card"],
                                 border_width=1, border_color=BORDER)
            empty.pack(fill="x", pady=(8, 8))
            self._glyph_label(empty, "historial", size=22, color=PRIMARY).pack(
                pady=(26, 6))
            ctk.CTkLabel(empty, text="No tienes evaluaciones registradas",
                         font=_fw(17, "bold"), text_color=TEXT).pack()
            ctk.CTkLabel(empty, text=(
                "Completa la evaluación guiada: cada plan generado se guarda "
                "en este historial."),
                font=_fw(13), text_color=TEXT_MUTED).pack(pady=(4, 18))
            ctk.CTkButton(empty, text="  Nueva evaluación", height=44,
                          corner_radius=10, font=_fw(14, "bold"),
                          fg_color=PRIMARY, hover_color=PRIMARY_HOV,
                          text_color="#04161A",
                          command=lambda: self.show_page("nueva")).pack(
                              pady=(0, 26))
            return

        # Cabecera de tabla
        tabla = ctk.CTkFrame(frame, fg_color=BG_ELEV, corner_radius=DS.RADII["card"],
                             border_width=1, border_color=BORDER)
        tabla.pack(fill="x", pady=(4, 14))
        ctk.CTkLabel(tabla, text="FECHA", font=_fw(11, "bold"),
                     text_color=TEXT_FAINT, width=150, anchor="w").grid(
                         row=0, column=0, padx=(16, 6), pady=10, sticky="w")
        for col, txt in enumerate(["PESO", "IMC", "OBJETIVO", "KCAL"],
                                  start=1):
            ctk.CTkLabel(tabla, text=txt, font=_fw(11, "bold"),
                         text_color=TEXT_FAINT, width=110, anchor="w").grid(
                             row=0, column=col, padx=6, pady=10, sticky="w")
        ctk.CTkFrame(tabla, height=1, fg_color=BORDER).grid(
            row=1, column=0, columnspan=5, sticky="ew", padx=12)

        for i, s in enumerate(reversed(history)):
            r = i + 2
            sel = s is history[-1]
            fila = ctk.CTkFrame(tabla, fg_color=(
                PRIMARY_SOFT if sel else "transparent"), corner_radius=6)
            fila.grid(row=r, column=0, columnspan=5, sticky="ew", padx=8, pady=2)
            ctk.CTkLabel(fila, text=str(s.get("saved_at", "")), font=_fw(12),
                         text_color=TEXT_MUTED, width=150, anchor="w").grid(
                             row=0, column=0, padx=(8, 6), pady=8, sticky="w")
            peso = s.get("weight", 0)
            for col, (txt, color) in enumerate([
                (f"{peso:.1f} kg", TEXT), (f"{s.get('imc', 0):.1f}", TEXT),
                (OBJECTIVE_LABELS.get(s.get("objective", ""), "—"), TEXT),
                (f"{s.get('target_calories', 0):.0f} kcal", PRIMARY),
            ], start=1):
                ctk.CTkLabel(fila, text=txt, font=_fw(12, "bold"),
                             text_color=color, width=110, anchor="w").grid(
                                 row=0, column=col, padx=6, pady=8, sticky="w")

        # Acciones sobre la sesión seleccionada (la más reciente)
        ultima = history[-1]
        act = ctk.CTkFrame(frame, fg_color="transparent")
        act.pack(fill="x", pady=(0, 16))
        ctk.CTkLabel(act, text="Última evaluación:", font=_fw(13, "bold"),
                     text_color=TEXT_MUTED).pack(side="left", padx=(0, 12))
        ctk.CTkButton(act, text="  Usar como base", height=40, corner_radius=10,
                      font=_fw(13, "bold"), fg_color=BG_ELEV_2,
                      hover_color=BG_ELEV_3, text_color=TEXT,
                      border_width=1, border_color=BORDER,
                      command=lambda: self._hist_base(ultima)).pack(side="left")
        ctk.CTkButton(act, text="  Exportar PDF", height=40, corner_radius=10,
                      font=_fw(13, "bold"), fg_color=PRIMARY_SOFT,
                      hover_color=BG_ELEV_3, text_color=PRIMARY,
                      border_width=1, border_color=PRIMARY,
                      command=lambda: self._hist_pdf(ultima)).pack(side="left",
                                                                   padx=(10, 0))

    def _hist_base(self, entry: dict) -> None:
        """Vuelca la sesión guardada al borrador del asistente."""
        self._wz_seed_defaults(entry)
        self.wz_step = 1
        self.show_page("nueva")

    def _hist_pdf(self, entry: dict) -> None:
        try:
            datos = self._entry_to_dataset(entry)
            valores, errores, _adv = validate_evaluation(datos)
            if errores:
                raise ValueError("La sesión guardada no es reproducible.")
            perfil = UserProfile(**valores)
            perfil.user_id = self.session["user_id"]
            motor = InferenceEngine()
            motor.run(perfil)
            rutina = generate_training_plan(perfil)
            plan = generate_nutrition_plan(perfil)
            default = (f"Plan_FitExpert_{entry.get('saved_at', 'historial')}"
                       f".pdf".replace(":", "-").replace(" ", "_"))
            path = filedialog.asksaveasfilename(
                defaultextension=".pdf", filetypes=[("PDF", "*.pdf")],
                initialfile=default, title="Guardar PDF del historial")
            if path:
                export_pdf(perfil, plan, rutina, path)
                self._open_pdf(path)
        except Exception as e:
            msg = ctk.CTkToplevel(self)
            msg.geometry("460x180")
            msg.configure(fg_color=BG)
            ctk.CTkLabel(msg, text="No se pudo exportar esta sesión",
                         font=_fw(16, "bold"), text_color=DANGER).pack(pady=(24, 8))
            ctk.CTkLabel(msg, text=f"Detalle: {e}", font=_fw(12),
                         text_color=TEXT_MUTED, wraplength=400).pack(pady=(0, 14))
            ctk.CTkButton(msg, text="Cerrar", width=120, height=36,
                          fg_color=PRIMARY, hover_color=PRIMARY_HOV,
                          text_color="#04161A", command=msg.destroy).pack()

    def _entry_to_dataset(self, entry: dict) -> dict:
        return {
            "name": self.session["username"],
            "age": entry.get("age", ""),
            "sex": entry.get("sex", "masculino"),
            "weight": entry.get("weight", ""),
            "height": entry.get("height", ""),
            "body_fat_pct": entry.get("body_fat_pct", 0.0),
            "objective": entry.get("objective", "mantenimiento"),
            "activity_level": entry.get("activity_level", "ligero"),
            "experience": entry.get("experience", "principiante"),
            "training_place": entry.get("training_place", "casa"),
            "diet_type": entry.get("diet_type", "omnivoro"),
            "meal_frequency": entry.get("meal_frequency", 3),
            "injuries": entry.get("injuries", []),
            "injuries_labels": [],
            "injury_severity": entry.get("injury_severity", "ninguna"),
            "balance_issues": bool(entry.get("balance_issues", False)),
            "red_flags": entry.get("red_flags", []),
            "equipment": entry.get("equipment", []) or [],
            "allergies": entry.get("allergies", []),
            "intolerances": entry.get("intolerances", []),
            "preferences": entry.get("preferences", []) or [],
            "notes": entry.get("notes", ""),
        }

    # ══════════════════════════════════════════════════════════
    #  PROGRESO
    # ══════════════════════════════════════════════════════════

    def _render_progreso(self, frame) -> None:
        self._page_header(frame, "progreso", "Progreso",
                          "Evolución de tus métricas entre evaluaciones.")
        history = get_user_history(self.session["user_id"])
        if len(history) < 1:
            empty = ctk.CTkFrame(frame, fg_color=BG_ELEV,
                                 corner_radius=DS.RADII["card"],
                                 border_width=1, border_color=BORDER)
            empty.pack(fill="x", pady=(8, 8))
            ctk.CTkLabel(empty, text="Sin datos suficientes", font=_fw(17, "bold"),
                         text_color=TEXT).pack(pady=(28, 8))
            ctk.CTkLabel(empty, text=(
                "Completa al menos una evaluación para empezar a medir tu "
                "evolución."), font=_fw(13), text_color=TEXT_MUTED).pack(
                    pady=(0, 28))
            return

        pr = get_progress_summary(self.session["user_id"])
        kpi = ctk.CTkFrame(frame, fg_color="transparent")
        kpi.pack(fill="x", pady=(4, 16))
        delta_p = pr["delta_peso_kg"]
        p_color = SUCCESS if delta_p <= 0 else WARNING
        for col, card in enumerate([
            self._metric_card(kpi, "Sesiones", str(pr["sesiones"]),
                              "evaluaciones", ACCENT, "historial"),
            self._metric_card(kpi, "Δ Peso",
                              f"{'+' if delta_p > 0 else ''}{delta_p:.1f} kg",
                              "respecto a la primera", p_color, "grafico"),
            self._metric_card(kpi, "Δ Calórico",
                              f"{'+' if pr['delta_calorias'] > 0 else ''}"
                              f"{pr['delta_calorias']:.0f} kcal",
                              "variación objetivo", VIOLET, "calculadora"),
        ]):
            card.grid(row=0, column=col, padx=(0 if col == 0 else 10, 0),
                      sticky="nsew")
        for col in range(3):
            kpi.grid_columnconfigure(col, weight=1)

        graph = ctk.CTkFrame(frame, fg_color=BG_ELEV, corner_radius=DS.RADII["card"],
                             border_width=1, border_color=BORDER)
        graph.pack(fill="x", pady=(0, 14))
        self._section_title(graph, "grafico", "Evolución de peso")
        self._render_graph(graph)

    # ══════════════════════════════════════════════════════════
    #  EXPLICABILIDAD
    # ══════════════════════════════════════════════════════════

    def _render_explicacion(self, frame) -> None:
        self._page_header(frame, "explicacion", "Explicabilidad",
                          "Qué reglas activó el motor, cuáles descartó y por qué.")
        res = self.current_results
        if not res:
            empty = ctk.CTkFrame(frame, fg_color=BG_ELEV,
                                 corner_radius=DS.RADII["card"],
                                 border_width=1, border_color=BORDER)
            empty.pack(fill="x", pady=(8, 8))
            self._glyph_label(empty, "explicacion", size=22, color=PRIMARY).pack(
                pady=(26, 6))
            ctk.CTkLabel(empty, text="Aún no hay un plan que explicar",
                         font=_fw(17, "bold"), text_color=TEXT).pack()
            ctk.CTkLabel(empty, text=(
                "Genera un plan para ver las reglas activadas, suprimidas y "
                "los errores internos del motor."),
                font=_fw(13), text_color=TEXT_MUTED).pack(pady=(4, 18))
            ctk.CTkButton(empty, text="  Ir al plan", height=44, corner_radius=10,
                          font=_fw(14, "bold"), fg_color=PRIMARY,
                          hover_color=PRIMARY_HOV, text_color="#04161A",
                          command=lambda: self.show_page("plan")).pack(
                              pady=(0, 26))
            return

        p = res["perfil"]
        summ = ctk.CTkFrame(frame, fg_color="transparent")
        summ.pack(fill="x", pady=(4, 14))
        datos = [
            ("Reglas evaluadas", f"{len(RULES)}"),
            ("Activadas", f"{len(p.conclusions)}"),
            ("Suprimidas", f"{len(p.suppressed)}"),
            ("Errores internos", f"{len(p.engine_errors)}"),
        ]
        for col, (titulo, valor) in enumerate(datos):
            cell = ctk.CTkFrame(summ, fg_color=BG_ELEV,
                                corner_radius=DS.RADII["card"],
                                border_width=1, border_color=BORDER)
            cell.grid(row=0, column=col, padx=(0 if col == 0 else 10, 0),
                      sticky="nsew")
            ctk.CTkLabel(cell, text=titulo.upper(), font=_fw(11, "bold"),
                         text_color=TEXT_FAINT).pack(pady=(14, 2))
            ctk.CTkLabel(cell, text=valor, font=_fw(22, "bold"),
                         text_color=PRIMARY if col != 0 else TEXT).pack(
                             pady=(0, 14))
        for col in range(4):
            summ.grid_columnconfigure(col, weight=1)

        tb = ctk.CTkTextbox(frame, wrap="word", font=ctk.CTkFont(
            family=FONT_MONO, size=12), fg_color=BG_ELEV, text_color=TEXT,
            border_width=1, border_color=BORDER, corner_radius=12)
        tb.pack(fill="both", expand=True)

        _sev = {"critica": 0, "alta": 1, "media": 2, "baja": 3, "info": 4}
        txt = ""
        if p.red_flags or p.injury_severity == "aguda":
            txt += ("SUSPENSIÓN POR SEÑALES DE ALARMA / LESIÓN AGUDA\n"
                    "   -> Deriva a consulta profesional: no se prescribe "
                    "ejercicio.\n\n")
        for c in sorted(p.conclusions,
                        key=lambda c: _sev.get(c.get("severity", "info"), 9)):
            rid = c["id"]
            exp = next((e["explanation"] for e in p.explanations
                        if e["id"] == rid), "")
            txt += (f"[{rid}] ({c.get('severity', 'info').upper()}) "
                    f"{c['conclusion']}\n    -> {exp}\n\n")
        if not p.conclusions:
            txt += "No se activaron reglas específicas para este perfil.\n\n"
        if p.suppressed:
            txt += "REGLAS SUPRIMIDAS POR JERARQUÍA:\n"
            for s in p.suppressed:
                txt += (f"   * [{s.get('id', '')}] suprimida por "
                        f"[{s.get('suppressed_by', '')}] — "
                        f"{s.get('reason', '')}\n")
            txt += "\n"
        if p.engine_errors:
            txt += "ERRORES INTERNOS DE EVALUACIÓN:\n"
            for e in p.engine_errors:
                txt += f"   * [{e.get('id', '')}] {e.get('error', '')}\n"
        tb.insert("0.0", txt)
        tb.configure(state="disabled")

    # ══════════════════════════════════════════════════════════
    #  PERFIL
    # ══════════════════════════════════════════════════════════

    def _render_perfil(self, frame) -> None:
        self._page_header(frame, "perfil", "Mi perfil",
                          "Datos de tu cuenta y cambio de contraseña.")

        ident = ctk.CTkFrame(frame, fg_color=BG_ELEV, corner_radius=DS.RADII["card"],
                             border_width=1, border_color=BORDER)
        ident.pack(fill="x", pady=(4, 14))
        av = ctk.CTkFrame(ident, width=56, height=56, corner_radius=28,
                          fg_color=PRIMARY_SOFT, border_width=1,
                          border_color=PRIMARY)
        av.pack(side="left", padx=(20, 16), pady=18)
        av.pack_propagate(False)
        ctk.CTkLabel(av, text=(self.session["username"][:1].upper() or "?"),
                     font=_fw(22, "bold"),
                     text_color=PRIMARY).place(relx=.5, rely=.5, anchor="center")
        b = ctk.CTkFrame(ident, fg_color="transparent")
        b.pack(side="left", fill="x", expand=True, pady=18)
        ctk.CTkLabel(b, text=self.session["username"], font=_fw(16, "bold"),
                     text_color=TEXT, anchor="w").pack(anchor="w")
        ctk.CTkLabel(b, text="Cuenta verificada · Argon2id · Datos en este equipo",
                     font=_fw(12), text_color=SUCCESS, anchor="w").pack(
                         anchor="w", pady=(3, 0))
        last = get_last_session(self.session["user_id"])
        if last:
            ctk.CTkLabel(b, text=(
                f"Última evaluación: {last.get('saved_at', '—')} · "
                f"Meta {last.get('target_calories', 0):.0f} kcal/día"),
                font=_fw(12), text_color=TEXT_MUTED, anchor="w").pack(
                    anchor="w", pady=(3, 0))

        # Cambio de contraseña
        sec = ctk.CTkFrame(frame, fg_color=BG_ELEV, corner_radius=DS.RADII["card"],
                           border_width=1, border_color=BORDER)
        sec.pack(fill="x", pady=(0, 14))
        self._section_title(sec, "candado", "Cambiar contraseña")

        g = ctk.CTkFrame(sec, fg_color="transparent")
        g.pack(fill="x", padx=18, pady=(8, 14))
        g.grid_columnconfigure(0, weight=1)
        g.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(g, text="CONTRASEÑA ACTUAL", font=_fw(11, "bold"),
                     text_color=TEXT_FAINT, anchor="w").grid(
                         row=0, column=0, sticky="w", padx=(0, 12), pady=(0, 4))
        self.pf_old = ctk.StringVar()
        ctk.CTkEntry(g, textvariable=self.pf_old, show="\u2022", height=42,
                     corner_radius=DS.RADII["input"], font=_fw(14),
                     fg_color=BG_ELEV_2, border_color=BORDER, border_width=1,
                     text_color=TEXT).grid(row=1, column=0, sticky="ew",
                                           padx=(0, 12), pady=(0, 10))
        ctk.CTkLabel(g, text="NUEVA CONTRASEÑA", font=_fw(11, "bold"),
                     text_color=TEXT_FAINT, anchor="w").grid(
                         row=0, column=1, sticky="w", pady=(0, 4))
        self.pf_new = ctk.StringVar()
        ctk.CTkEntry(g, textvariable=self.pf_new, show="\u2022", height=42,
                     corner_radius=DS.RADII["input"], font=_fw(14),
                     fg_color=BG_ELEV_2, border_color=BORDER, border_width=1,
                     text_color=TEXT).grid(row=1, column=1, sticky="ew",
                                           pady=(0, 10))

        ctk.CTkLabel(g, text="CONFIRMAR NUEVA CONTRASEÑA", font=_fw(11, "bold"),
                     text_color=TEXT_FAINT, anchor="w").grid(
                         row=2, column=0, columnspan=2, sticky="w", pady=(0, 4))
        self.pf_new2 = ctk.StringVar()
        ctk.CTkEntry(g, textvariable=self.pf_new2, show="\u2022", height=42,
                     corner_radius=DS.RADII["input"], font=_fw(14),
                     fg_color=BG_ELEV_2, border_color=BORDER, border_width=1,
                     text_color=TEXT).grid(row=3, column=0, columnspan=2,
                                           sticky="ew", pady=(0, 12))

        self.pf_msg = ctk.CTkLabel(g, text="", font=_fw(12, "bold"),
                                   text_color=DANGER, anchor="w", justify="left",
                                   wraplength=560)
        self.pf_msg.grid(row=4, column=0, columnspan=2, sticky="w")

        ctk.CTkButton(g, text="  Actualizar contraseña", height=44,
                      corner_radius=10, font=_fw(14, "bold"),
                      fg_color=PRIMARY, hover_color=PRIMARY_HOV,
                      text_color="#04161A", command=self._pf_submit).grid(
                          row=5, column=0, columnspan=2, sticky="w", pady=(8, 0))

        ctk.CTkLabel(sec, text=(
            "Tras cambiarla, se re-hashea la contraseña con Argon2id y la "
            "sesión local continúa vigente."),
            font=_fw(11), text_color=TEXT_FAINT, anchor="w", justify="left",
            wraplength=600).pack(anchor="w", padx=20, pady=(0, 14))

    def _pf_submit(self) -> None:
        if not getattr(self, "pf_msg", None):
            return
        old = self.pf_old.get()
        new = self.pf_new.get()
        new2 = self.pf_new2.get()
        if not old or not new:
            self.pf_msg.configure(text="Completa los tres campos.")
            return
        if new != new2:
            self.pf_msg.configure(text="Las nuevas contraseñas no coinciden.")
            return
        res = change_password(self.session["username"], old, new)
        if res.get("ok"):
            self.pf_msg.configure(text="Contraseña actualizada correctamente.",
                                  text_color=SUCCESS)
            self.pf_old.set("")
            self.pf_new.set("")
            self.pf_new2.set("")
        else:
            self.pf_msg.configure(text=res.get("error", "No se pudo actualizar."))

    # ══════════════════════════════════════════════════════════
    #  ACERCA
    # ══════════════════════════════════════════════════════════

    def _render_acerca(self, frame) -> None:
        self._page_header(frame, "libro", "Acerca de FitExpert",
                          "El sistema, su arquitectura y sus fuentes.")

        por_tier: dict = {}
        for r in RULES:
            tier = getattr(r, "tier", "OBJETIVO") or "OBJETIVO"
            por_tier[tier] = por_tier.get(tier, 0) + 1

        card = ctk.CTkFrame(frame, fg_color=BG_ELEV, corner_radius=DS.RADII["card"],
                            border_width=1, border_color=BORDER)
        card.pack(fill="x", pady=(4, 14))
        self._section_title(card, "explicacion", "Arquitectura técnica")
        texto = (
            f"FitExpert v3.0 — Sistema Experto Basado en Reglas (IA simbólica) "
            "para la generación de planes de fitness y nutrición con "
            "trazabilidad completa.\n\n"
            "  • Inferencia: encadenamiento hacia adelante (forward chaining)\n"
            "  • Conocimiento: " + f"{len(RULES)} reglas IF/THEN en " +
            f"{len(TIER_LABELS)} jerarquías\n"
            "  • Representación: objeto-atributo-valor (O-A-V)\n"
            "  • Seguridad: Argon2id con migración automática de hashes legados\n"
            "  • Reportes: exportación a PDF con justificación por regla\n"
        )
        ctk.CTkLabel(card, text=texto, font=_fw(13), text_color=TEXT,
                     justify="left", wraplength=680, anchor="w").pack(
                         anchor="w", padx=20, pady=(4, 18))

        tier_box = ctk.CTkFrame(frame, fg_color="transparent")
        tier_box.pack(fill="x", pady=(0, 14))
        for col, (tier, n) in enumerate(sorted(
                por_tier.items(), key=lambda kv: -kv[1])):
            cell = ctk.CTkFrame(tier_box, fg_color=BG_ELEV,
                                corner_radius=DS.RADII["card"],
                                border_width=1, border_color=BORDER)
            cell.grid(row=0, column=col, padx=(0 if col == 0 else 10, 0),
                      sticky="nsew")
            color = DS.tier_style(tier).get("color", TEXT_MUTED)
            ctk.CTkLabel(cell, text=TIER_LABELS.get(tier, tier),
                         font=_fw(11, "bold"),
                         text_color=color).pack(pady=(14, 2))
            ctk.CTkLabel(cell, text=str(n), font=_fw(20, "bold"),
                         text_color=TEXT).pack(pady=(0, 14))
        for col in range(len(por_tier)):
            tier_box.grid_columnconfigure(col, weight=1)

        aviso = ctk.CTkFrame(frame, fg_color="#2A0E0E", corner_radius=10,
                             border_width=1, border_color=CRITICAL)
        aviso.pack(fill="x", pady=(0, 14))
        self._glyph_label(aviso, "salud", size=15, color=CRITICAL).pack(
            side="left", padx=(16, 10), pady=12)
        ctk.CTkLabel(aviso, text=(
            "Herramienta informativa y académica. No sustituye la consulta con "
            "nutricionistas, médicos ni entrenadores certificados."),
            font=_fw(12), text_color="#FECACA", justify="left",
            wraplength=640, anchor="w").pack(side="left", pady=12)

        fuentes = ctk.CTkFrame(frame, fg_color=BG_ELEV,
                               corner_radius=DS.RADII["card"],
                               border_width=1, border_color=BORDER)
        fuentes.pack(fill="x", pady=(0, 8))
        self._section_title(fuentes, "libro", "Fuentes de la base de conocimiento")
        ctk.CTkLabel(fuentes, text=(
            "Fórmulas y criterios procedentes exclusivamente de "
            "WHO · CDC · AAP · ACSM. Sin recomendaciones de fuentes no "
            "contrastadas."),
            font=_fw(12), text_color=TEXT_MUTED, justify="left",
            wraplength=680, anchor="w").pack(anchor="w", padx=20, pady=(4, 16))

    # ──────────────────────────────────────────────────────────
    #  Cierre de sesión
    # ──────────────────────────────────────────────────────────

    def _logout(self) -> None:
        self.session = None
        self.current_results = None
        self.wz_values = {}
        self.wz_step = 1
        self._clear_local_session()
        self._show_login_screen()


if __name__ == "__main__":
    app = App()
    app.mainloop()