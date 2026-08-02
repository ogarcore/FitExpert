"""
pdf_exporter.py
===============
Exportación del plan completo a PDF usando ReportLab.

Genera un documento profesional con:
  - Portada con datos del usuario y métricas
  - Plan nutricional con macros y menú del día
  - Microciclo semanal de entrenamiento por días
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from datetime import datetime
from user_profile import UserProfile


# ── Paleta de colores ──────────────────────────────────────────────────────

PRIMARY   = colors.HexColor("#1F6AA5")
ACCENT    = colors.HexColor("#2FA572")
DARK_BG   = colors.HexColor("#1a1a2e")
LIGHT_BG  = colors.HexColor("#f0f4f8")
WARN      = colors.HexColor("#FFA500")
DANGER    = colors.HexColor("#FF4C4C")
TEXT_GRAY = colors.HexColor("#555555")


# ── Estilos ────────────────────────────────────────────────────────────────

def _build_styles():
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle("title", parent=base["Title"],
                                fontSize=26, textColor=colors.white,
                                alignment=TA_CENTER, spaceAfter=4),
        "subtitle": ParagraphStyle("subtitle", parent=base["Normal"],
                                   fontSize=13, textColor=colors.HexColor("#cccccc"),
                                   alignment=TA_CENTER, spaceAfter=2),
        "section": ParagraphStyle("section", parent=base["Heading1"],
                                  fontSize=16, textColor=PRIMARY,
                                  spaceBefore=12, spaceAfter=6),
        "subsection": ParagraphStyle("subsection", parent=base["Heading2"],
                                     fontSize=13, textColor=ACCENT,
                                     spaceBefore=8, spaceAfter=4),
        "body": ParagraphStyle("body", parent=base["Normal"],
                               fontSize=10, textColor=colors.black,
                               leading=14, spaceAfter=4),
        "body_gray": ParagraphStyle("body_gray", parent=base["Normal"],
                                    fontSize=9, textColor=TEXT_GRAY,
                                    leading=13, spaceAfter=3),
        "bold": ParagraphStyle("bold", parent=base["Normal"],
                               fontSize=10, fontName="Helvetica-Bold",
                               textColor=colors.black, spaceAfter=4),
        "note": ParagraphStyle("note", parent=base["Normal"],
                               fontSize=9, textColor=WARN,
                               leading=12, spaceAfter=4),
        "warn": ParagraphStyle("warn", parent=base["Normal"],
                               fontSize=9, textColor=DANGER,
                               leading=12, spaceAfter=4),
        "small": ParagraphStyle("small", parent=base["Normal"],
                                fontSize=8, textColor=TEXT_GRAY, spaceAfter=2),
        "centered": ParagraphStyle("centered", parent=base["Normal"],
                                   fontSize=10, alignment=TA_CENTER, spaceAfter=4),
    }


# ── Utilidades ─────────────────────────────────────────────────────────────

def _hr(color=PRIMARY):
    return HRFlowable(width="100%", thickness=1.5, color=color, spaceAfter=8, spaceBefore=4)


def _table_style(header_bg=PRIMARY, stripe_bg=LIGHT_BG):
    return TableStyle([
        ("BACKGROUND",   (0, 0), (-1,  0), header_bg),
        ("TEXTCOLOR",    (0, 0), (-1,  0), colors.white),
        ("FONTNAME",     (0, 0), (-1,  0), "Helvetica-Bold"),
        ("FONTSIZE",     (0, 0), (-1,  0), 10),
        ("ALIGN",        (0, 0), (-1, -1), "LEFT"),
        ("VALIGN",       (0, 0), (-1, -1), "MIDDLE"),
        ("FONTSIZE",     (0, 1), (-1, -1), 9),
        ("FONTNAME",     (0, 1), (-1, -1), "Helvetica"),
        ("ROWBACKGROUNDS",(0, 1), (-1, -1), [colors.white, stripe_bg]),
        ("GRID",         (0, 0), (-1, -1), 0.4, colors.HexColor("#cccccc")),
        ("LEFTPADDING",  (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING",   (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 5),
        ("ROUNDEDCORNERS", [4]),
    ])


# ── Constructor principal ──────────────────────────────────────────────────

def export_pdf(profile: UserProfile, nutrition_plan: dict, training_plan: dict, output_path: str) -> str:
    """
    Genera el PDF completo y lo guarda en output_path.
    Retorna la ruta del archivo generado.
    """
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )

    styles = _build_styles()
    story  = []

    # ── PORTADA ───────────────────────────────────────────────────────────────

    # Fondo simulado con tabla coloreada
    portada_data = [[Paragraph("FitExpert", styles["title"])]]
    portada_table = Table(portada_data, colWidths=[17 * cm])
    portada_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), DARK_BG),
        ("TOPPADDING",    (0, 0), (-1, -1), 20),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 20),
        ("ROUNDEDCORNERS", [8]),
    ]))
    story.append(portada_table)
    story.append(Spacer(1, 0.3 * cm))
    story.append(Paragraph("Sistema Experto en Nutrición y Fitness", styles["subtitle"]))
    story.append(Paragraph(f"Plan generado el {datetime.now().strftime('%d/%m/%Y a las %H:%M')}", styles["subtitle"]))
    story.append(Spacer(1, 0.5 * cm))
    story.append(_hr())

    # ── DATOS DEL USUARIO ─────────────────────────────────────────────────────

    story.append(Paragraph("Datos del Usuario", styles["section"]))

    from user_profile import OBJECTIVE_LABELS, ACTIVITY_LABELS, DIET_TYPES
    user_data = [
        ["Campo",                "Valor"],
        ["Nombre",               profile.name],
        ["Edad",                 f"{profile.age} años"],
        ["Sexo",                 profile.sex.capitalize()],
        ["Peso corporal",        f"{profile.weight:.1f} kg"],
        ["Altura",               f"{profile.height:.0f} cm"],
        ["Objetivo",             OBJECTIVE_LABELS.get(profile.objective, profile.objective)],
        ["Nivel de actividad",   ACTIVITY_LABELS.get(profile.activity_level, profile.activity_level)],
        ["Experiencia",          profile.experience.capitalize()],
        ["Lugar de entrenamiento", profile.training_place.capitalize()],
        ["Tipo de dieta",        DIET_TYPES.get(profile.diet_type, profile.diet_type)],
        ["Alergias",             ", ".join(profile.allergies) if profile.allergies else "Ninguna"],
        ["Lesiones",             ", ".join(profile.injuries)  if profile.injuries  else "Ninguna"],
        ["Frecuencia alimentaria", f"{profile.meal_frequency} comidas al día"],
    ]
    if profile.body_fat_pct > 0:
        user_data.append(["% Grasa corporal estimado", f"{profile.body_fat_pct:.1f}%"])

    t = Table(user_data, colWidths=[7 * cm, 10 * cm])
    t.setStyle(_table_style())
    story.append(t)
    story.append(Spacer(1, 0.5 * cm))

    # ── MÉTRICAS CALCULADAS ───────────────────────────────────────────────────

    story.append(Paragraph("Métricas Calculadas", styles["section"]))

    imc_color = ACCENT if 18.5 <= profile.imc <= 24.9 else WARN if profile.imc < 18.5 else DANGER

    metrics_data = [
        ["Métrica",          "Valor",                    "Referencia"],
        ["IMC",              f"{profile.imc:.1f}",       profile.imc_category],
        ["TMB (reposo)",     f"{profile.tmb:.0f} kcal",  "Calorías en reposo total"],
        ["TDEE (diario)",    f"{profile.tdee:.0f} kcal", "Gasto energético diario"],
        ["Calorías objetivo",f"{profile.target_calories:.0f} kcal", "Meta calórica diaria"],
    ]

    macros = nutrition_plan.get("macros", {})
    metrics_data += [
        ["Proteínas",        f"{macros.get('proteinas', 0):.0f} g", f"{macros.get('p_pct', 0)}% de las calorías"],
        ["Carbohidratos",    f"{macros.get('carbohidratos', 0):.0f} g", f"{macros.get('c_pct', 0)}% de las calorías"],
        ["Grasas",           f"{macros.get('grasas', 0):.0f} g", f"{macros.get('g_pct', 0)}% de las calorías"],
    ]

    t2 = Table(metrics_data, colWidths=[6 * cm, 5 * cm, 6 * cm])
    t2.setStyle(_table_style(header_bg=ACCENT))
    story.append(t2)

    # Notas de seguridad biomecánica
    if profile.injuries or profile.age > 70 or profile.age < 16 or profile.imc >= 40:
        story.append(Spacer(1, 0.3 * cm))
        story.append(Paragraph("Restricciones detectadas por el motor de inferencia:", styles["warn"]))
        notas_text = training_plan.get("notas", "")
        for nota in notas_text.split(" | "):
            if nota.strip():
                story.append(Paragraph(f"• {nota.strip()}", styles["warn"]))

    story.append(PageBreak())

    # ── PLAN NUTRICIONAL ──────────────────────────────────────────────────────

    story.append(Paragraph("Plan Nutricional", styles["section"]))
    story.append(_hr(ACCENT))

    plan = nutrition_plan.get("plan", {})

    meals = [
        ("Desayuno",   "desayuno"),
        ("Almuerzo",   "almuerzo"),
        ("Cena",       "cena"),
        ("Snacks",     "snacks"),
    ]

    for label, key in meals:
        items = plan.get(key, [])
        if not items:
            continue
        story.append(Paragraph(label, styles["subsection"]))
        meal_rows = [["#", "Opción recomendada"]]
        for i, item in enumerate(items, 1):
            meal_rows.append([str(i), item])
        t = Table(meal_rows, colWidths=[1 * cm, 16 * cm])
        t.setStyle(_table_style(header_bg=PRIMARY))
        story.append(t)
        story.append(Spacer(1, 0.3 * cm))

    story.append(Paragraph(f"Hidratación: {plan.get('hidratacion', '')}", styles["note"]))

    # Alergias activas
    if nutrition_plan.get("alergias_activas"):
        story.append(Spacer(1, 0.2 * cm))
        story.append(Paragraph(
            f"Filtros aplicados: dieta {nutrition_plan.get('tipo_dieta', '')} | "
            f"Alergias excluidas: {', '.join(nutrition_plan['alergias_activas'])}",
            styles["body_gray"]
        ))

    story.append(PageBreak())

    # ── MICROCICLO DE ENTRENAMIENTO ───────────────────────────────────────────

    story.append(Paragraph("Microciclo Semanal de Entrenamiento", styles["section"]))
    story.append(Paragraph(f"{training_plan.get('nombre', '')}  •  {training_plan.get('tipo', '')}", styles["body_gray"]))
    story.append(Paragraph(training_plan.get("dias", ""), styles["bold"]))
    story.append(_hr(PRIMARY))

    semana = training_plan.get("semana", [])

    for day in semana:
        dia    = day.get("dia", "")
        grupo  = day.get("grupo", "")
        es_desc = day.get("descanso", True)

        # Encabezado del día
        day_color = LIGHT_BG if not es_desc else colors.HexColor("#eeeeee")
        day_header = [[
            Paragraph(f"{dia}", styles["bold"]),
            Paragraph(grupo, styles["body_gray"]),
        ]]
        dh_table = Table(day_header, colWidths=[3 * cm, 14 * cm])
        dh_table.setStyle(TableStyle([
            ("BACKGROUND",   (0, 0), (-1, -1), day_color),
            ("TOPPADDING",   (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING",(0, 0), (-1, -1), 6),
            ("LEFTPADDING",  (0, 0), (-1, -1), 8),
            ("GRID",         (0, 0), (-1, -1), 0.3, colors.HexColor("#dddddd")),
        ]))
        story.append(dh_table)

        if es_desc:
            nota = day.get("nota", "Descanso completo.")
            story.append(Paragraph(f"    ↳ {nota}", styles["small"]))
            story.append(Spacer(1, 0.2 * cm))
            continue

        # Ejercicios del día
        ejercicios = day.get("ejercicios", [])
        if ejercicios:
            ej_rows = [["Ejercicio", "Volumen", "Grupo Muscular"]]
            for ej in ejercicios:
                nombre_ej, reps, musculo = ej[0], ej[1], ej[2]
                ej_rows.append([nombre_ej, reps, musculo])

            ej_table = Table(ej_rows, colWidths=[7 * cm, 4 * cm, 6 * cm])
            ej_table.setStyle(_table_style(header_bg=colors.HexColor("#2c3e50")))
            story.append(ej_table)

        # Metadatos de la sesión
        meta = (
            f"Duración: {day.get('duracion', '—')}  |  "
            f"Descanso entre series: {day.get('descanso_entre_series', '—')}"
        )
        story.append(Paragraph(meta, styles["small"]))
        nota_ses = day.get("nota", "")
        if nota_ses:
            story.append(Paragraph(f"Nota: {nota_ses}", styles["small"]))
        story.append(Spacer(1, 0.4 * cm))

    # Notas finales
    if training_plan.get("cardio_extra"):
        story.append(_hr(ACCENT))
        story.append(Paragraph(f"Cardio adicional: {training_plan['cardio_extra']}", styles["note"]))

    # ── PIE DE PÁGINA ─────────────────────────────────────────────────────────

    story.append(Spacer(1, 1 * cm))
    story.append(_hr(TEXT_GRAY))
    footer_text = (
        "Este plan fue generado por un Sistema Experto con fines orientativos. "
        "Consulta con un profesional de la salud antes de iniciar cualquier programa de ejercicio o dieta."
    )
    story.append(Paragraph(footer_text, styles["small"]))
    story.append(Paragraph(
        f"Generado por FitExpert • {datetime.now().strftime('%d/%m/%Y')}",
        ParagraphStyle("footer_right", parent=getSampleStyleSheet()["Normal"],
                       fontSize=8, textColor=TEXT_GRAY, alignment=TA_CENTER)
    ))

    doc.build(story)
    return output_path
