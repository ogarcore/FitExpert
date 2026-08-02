import streamlit as st
import pandas as pd
from datetime import datetime

# Importar los módulos del Sistema Experto
from user_profile import (
    UserProfile, OBJECTIVES, OBJECTIVE_LABELS,
    ACTIVITY_LEVELS, ACTIVITY_LABELS,
    EXPERIENCE_LEVELS, TRAINING_PLACES, SEX_OPTIONS
)
from inference_engine import InferenceEngine
from nutrition import generate_nutrition_plan
from training import generate_training_plan
from database import save_profile, list_users, db_stats
from knowledge_base import RULES

# Configuración de la página
st.set_page_config(
    page_title="Sistema Experto Fitness",
    page_icon="💪",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Estilos CSS personalizados
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1E88E5;
        font-weight: 700;
        margin-bottom: 0px;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #757575;
        margin-bottom: 30px;
    }
    .metric-card {
        background-color: #f8f9fa;
        border-radius: 10px;
        padding: 20px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        text-align: center;
    }
    .dark .metric-card {
        background-color: #1e1e1e;
        box-shadow: 0 4px 6px rgba(255,255,255,0.05);
    }
    .rule-card {
        border-left: 5px solid #1E88E5;
        padding: 10px 15px;
        margin: 10px 0;
        background-color: rgba(30, 136, 229, 0.1);
        border-radius: 0 5px 5px 0;
    }
</style>
""", unsafe_allow_html=True)

# ─── NAVEGACIÓN ────────────────────────────────────────────────────────────

st.sidebar.image("https://cdn-icons-png.flaticon.com/512/2964/2964514.png", width=100)
st.sidebar.title("Sistema Experto")
st.sidebar.markdown("Nutrición y Acondicionamiento Físico")

page = st.sidebar.radio(
    "Navegación",
    ["Nueva Consulta", "Historial de Usuarios", "Acerca del Sistema"]
)

st.sidebar.divider()
st.sidebar.caption("Proyecto Académico - Inteligencia Artificial")


# ─── PÁGINA: NUEVA CONSULTA ───────────────────────────────────────────────

if page == "Nueva Consulta":
    st.markdown('<p class="main-header">Evaluación Física Personalizada</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Ingresa tus datos para generar recomendaciones expertas.</p>', unsafe_allow_html=True)

    with st.form("evaluacion_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Datos Personales")
            nombre = st.text_input("Nombre", value="Usuario")
            
            subcol1, subcol2 = st.columns(2)
            with subcol1:
                edad = st.number_input("Edad", min_value=10, max_value=100, value=25)
                peso = st.number_input("Peso (kg)", min_value=30.0, max_value=300.0, value=70.0, step=0.1)
            with subcol2:
                sexo_label = st.selectbox("Sexo", ["Masculino", "Femenino"])
                sexo = "masculino" if sexo_label == "Masculino" else "femenino"
                altura = st.number_input("Altura (cm)", min_value=100.0, max_value=250.0, value=170.0, step=0.1)

        with col2:
            st.subheader("Objetivos y Experiencia")
            
            # Mapeos inversos para los selectbox
            obj_options = list(OBJECTIVE_LABELS.values())
            obj_label = st.selectbox("Objetivo Corporal", obj_options)
            objetivo = list(OBJECTIVE_LABELS.keys())[obj_options.index(obj_label)]
            
            act_options = list(ACTIVITY_LABELS.values())
            act_label = st.selectbox("Nivel de Actividad", act_options)
            actividad = list(ACTIVITY_LABELS.keys())[act_options.index(act_label)]
            
            exp_options = ["Principiante (menos de 6 meses)", "Intermedio (6 meses - 2 años)", "Avanzado (más de 2 años)"]
            exp_label = st.selectbox("Experiencia", exp_options)
            experiencia = "principiante" if "Principiante" in exp_label else "intermedio" if "Intermedio" in exp_label else "avanzado"
            
            lugar_label = st.selectbox("Lugar de Entrenamiento", ["Gimnasio", "Entrenamiento en Casa"])
            lugar = "gimnasio" if lugar_label == "Gimnasio" else "casa"

        submit = st.form_submit_button("Generar Recomendaciones Expertas 🚀", use_container_width=True)

    if submit:
        # Procesar datos
        with st.spinner("El Motor de Inferencia está analizando los datos..."):
            perfil = UserProfile(
                name=nombre, age=edad, sex=sexo, weight=peso, height=altura,
                activity_level=actividad, objective=objetivo, experience=experiencia, training_place=lugar
            )
            
            motor = InferenceEngine()
            motor.run(perfil)
            
            save_profile(perfil)
            
        st.success(f"Evaluación completada con éxito. Se activaron {len(motor.fired_rules)} reglas de conocimiento.")
        
        # ─── RESULTADOS ─────────────────────────────────────────
        st.divider()
        st.header("📊 Resultados del Análisis")
        
        # Métricas
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("IMC", f"{perfil.imc:.1f}", perfil.imc_category, delta_color="off")
        m2.metric("TMB (Reposo)", f"{perfil.tmb:.0f} kcal")
        m3.metric("TDEE (Gasto Total)", f"{perfil.tdee:.0f} kcal")
        m4.metric("Objetivo Diario", f"{perfil.target_calories:.0f} kcal")

        # Tabs de contenido
        tab_nutricion, tab_entreno, tab_expert, tab_hechos = st.tabs([
            "🥗 Plan Nutricional", 
            "🏋️ Plan de Entrenamiento", 
            "💡 Recomendaciones del Sistema (Reglas)",
            "🗂️ Base de Hechos (O-A-V)"
        ])
        
        # TAB 1: Nutrición
        with tab_nutricion:
            plan_nutricional = generate_nutrition_plan(perfil)
            macros = plan_nutricional["macros"]
            
            st.subheader("Distribución de Macronutrientes")
            c1, c2, c3 = st.columns(3)
            c1.info(f"**Proteínas:** {macros['proteinas']}g ({macros['p_pct']}%)")
            c2.warning(f"**Carbohidratos:** {macros['carbohidratos']}g ({macros['c_pct']}%)")
            c3.error(f"**Grasas:** {macros['grasas']}g ({macros['g_pct']}%)")
            
            st.subheader("Sugerencia de Comidas")
            meals = plan_nutricional["plan"]
            
            col_a, col_b = st.columns(2)
            with col_a:
                with st.expander("🌅 Desayuno", expanded=True):
                    for option in meals["desayuno"]:
                        st.markdown(f"- {option}")
                with st.expander("☀️ Almuerzo", expanded=True):
                    for option in meals["almuerzo"]:
                        st.markdown(f"- {option}")
            with col_b:
                with st.expander("🌙 Cena", expanded=True):
                    for option in meals["cena"]:
                        st.markdown(f"- {option}")
                with st.expander("🍎 Snacks", expanded=True):
                    for option in meals["snacks"]:
                        st.markdown(f"- {option}")
                        
            st.info(f"💧 **Hidratación:** {meals['hidratacion']}")

        # TAB 2: Entrenamiento
        with tab_entreno:
            rutina = generate_training_plan(perfil)
            st.subheader(rutina["nombre"])
            st.caption(f"**Días:** {rutina['dias']} | **Tipo:** {rutina['tipo']}")
            
            for session in rutina.get("sesiones", []):
                with st.expander(f"📋 {session['nombre']}", expanded=True):
                    df_ejercicios = pd.DataFrame(
                        session["ejercicios"],
                        columns=["Ejercicio", "Series/Reps", "Músculo"]
                    )
                    st.dataframe(df_ejercicios, use_container_width=True, hide_index=True)
                    st.caption(f"⏱️ Descanso: {session.get('descanso', '-')} | ⌛ Duración: {session.get('duracion', '-')}")

            if rutina.get("cardio_extra"):
                st.info(f"🏃 **Cardio Adicional:** {rutina['cardio_extra']}")
            if rutina.get("notas"):
                st.warning(f"💡 **Nota del entrenador:** {rutina['notas']}")

        # TAB 3: Módulo de Explicación (Expert System Core)
        with tab_expert:
            st.subheader("Módulo de Explicación")
            st.write("El sistema experto ha deducido las siguientes recomendaciones basadas en tus datos (Encadenamiento hacia adelante):")
            
            if perfil.conclusions:
                for idx, c in enumerate(perfil.conclusions):
                    rule_id = c["id"]
                    explicacion = next((e["explanation"] for e in perfil.explanations if e["id"] == rule_id), "")
                    
                    st.markdown(f"""
                    <div class="rule-card">
                        <b>Regla Activada [{rule_id}]:</b> {c["conclusion"]}<br>
                        <span style="color: gray; font-size: 0.9em;"><i>Razonamiento:</i> {explicacion}</span>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("No se activaron reglas específicas para este perfil.")

        # TAB 4: Hechos
        with tab_hechos:
            st.subheader("Base de Hechos (Representación OAV)")
            st.write("Datos procesados por el motor de inferencia:")
            st.json(perfil.facts)


# ─── PÁGINA: HISTORIAL ────────────────────────────────────────────────────

elif page == "Historial de Usuarios":
    st.markdown('<p class="main-header">Historial de Consultas</p>', unsafe_allow_html=True)
    
    users = list_users()
    
    if not users:
        st.info("No hay consultas registradas en la base de datos.")
    else:
        # Estadísticas Rápidas
        stats = db_stats()
        c1, c2 = st.columns(2)
        c1.metric("Total Usuarios", stats["total_usuarios"])
        
        # Tabla de usuarios
        df = pd.DataFrame(users)
        
        # Limpiar y formatear DataFrame para mostrar
        if not df.empty:
            df["Objetivo"] = df["objective"].map(OBJECTIVE_LABELS)
            df_display = df[["name", "age", "sex", "imc", "imc_category", "Objetivo", "created_at"]]
            df_display.columns = ["Nombre", "Edad", "Sexo", "IMC", "Categoría", "Objetivo", "Fecha Consulta"]
            
            st.dataframe(df_display, use_container_width=True, hide_index=True)


# ─── PÁGINA: ACERCA DE ────────────────────────────────────────────────────

elif page == "Acerca del Sistema":
    st.markdown('<p class="main-header">Acerca del Sistema Experto</p>', unsafe_allow_html=True)
    
    st.markdown("""
    Este proyecto es un **Sistema Experto Basado en Reglas** orientado al campo de la nutrición y el acondicionamiento físico.
    
    ### Arquitectura del Sistema
    *   **Base de Conocimiento:** Conjunto de 19 reglas lógicas (`IF-THEN`) estructuradas por expertos en el dominio (nutrición y fitness).
    *   **Motor de Inferencia:** Algoritmo de **Encadenamiento hacia Adelante** (*Forward Chaining*) que evalúa los datos del usuario contra la base de reglas.
    *   **Representación del Conocimiento:** Paradigma Objeto-Atributo-Valor.
    *   **Módulo de Explicación:** Justifica de manera transparente el razonamiento (el "por qué") detrás de cada recomendación emitida.
    *   **Interfaz Gráfica:** Construida con `Streamlit` para una presentación web interactiva y moderna.
    
    ### Consideraciones
    > ⚠️ Este software tiene un propósito puramente **académico y demostrativo**. Las recomendaciones nutricionales y de entrenamiento no sustituyen bajo ninguna circunstancia el consejo médico, diagnóstico o tratamiento proporcionado por un profesional de la salud certificado.
    """)
    
    st.divider()
    st.caption("Desarrollado en Python 🐍 con Streamlit")
