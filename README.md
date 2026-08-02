# Sistema Experto — Nutrición y Acondicionamiento Físico

> Proyecto académico | Inteligencia Artificial | Sistemas Expertos

## Descripción

Sistema Experto desarrollado en Python que proporciona **asesoramiento personalizado** en nutrición y entrenamiento físico. El sistema utiliza reglas de producción (IF-THEN), un motor de inferencia por encadenamiento hacia adelante y un módulo de explicación para justificar cada recomendación.

---

## Arquitectura del Sistema

```
examen/
├── main.py              ← Punto de entrada y orquestador principal
├── knowledge_base.py    ← Base de conocimiento (reglas IF-THEN)
├── inference_engine.py  ← Motor de inferencia (forward chaining)
├── calculations.py      ← Cálculos: IMC, TMB, TDEE, macros
├── nutrition.py         ← Planes alimenticios por objetivo
├── training.py          ← Rutinas de entrenamiento (casa/gimnasio)
├── user_profile.py      ← Modelo de datos del usuario
├── database.py          ← Persistencia JSON local
├── ui.py                ← Interfaz de consola (CLI)
├── gui.py               ← Interfaz web (Streamlit)
└── app_desktop.pyw      ← Interfaz nativa de escritorio (CustomTkinter)
```

---

## Componentes Principales

### Base de Conocimiento
- **19 reglas de producción** organizadas por categoría: nutrición, entrenamiento, seguimiento y alertas.
- Representación **Objeto-Atributo-Valor** (OAV).

### Motor de Inferencia
- Estrategia: **Encadenamiento hacia adelante (Forward Chaining)**.
- Evalúa todas las reglas y activa las que cumplen la condición del perfil.

### Cálculos Automáticos
| Indicador | Fórmula |
|-----------|---------|
| IMC | `peso / altura²` |
| TMB | Mifflin-St Jeor |
| TDEE | `TMB × factor_actividad` |
| Calorías objetivo | `TDEE ± ajuste_por_meta` |

### Módulo de Explicación
Cada regla incluye una explicación en lenguaje natural del razonamiento del sistema.

---

## Requisitos

- Python 3.10+
- `rich` (para la versión de consola)
- `customtkinter` (para la interfaz de escritorio)

```bash
python -m pip install rich customtkinter
```

---

## Ejecución

### 1. Interfaz Nativa de Escritorio (Recomendado)
Esta opción abrirá una ventana profesional sin mostrar ninguna terminal de fondo.
```bash
pythonw app_desktop.pyw
```
*(También puedes simplemente hacer **doble clic** sobre el archivo `app_desktop.pyw` desde el explorador de archivos de Windows).*

### 2. Interfaz Web (Streamlit)
```bash
streamlit run gui.py
```

### 3. Interfaz de Consola (CLI)
Para ejecutar la versión de terminal (útil para servidores sin entorno gráfico):
```bash
python main.py
```

---

## Funcionalidades

- [x] Registro de usuario con validación de datos
- [x] Cálculo de IMC, TMB, TDEE y calorías objetivo
- [x] Distribución de macronutrientes por objetivo
- [x] Plan alimenticio diario (desayuno, almuerzo, cena, snacks)
- [x] Rutinas de entrenamiento (casa / gimnasio × 3 niveles × 5 objetivos)
- [x] Motor de inferencia con 19 reglas activas
- [x] Módulo de explicación del razonamiento
- [x] Historial de consultas (JSON local)
- [x] Estadísticas del sistema

---

## Limitaciones del Sistema

> El sistema proporciona orientación general basada en principios establecidos.
> **No reemplaza** la consulta con profesionales de salud, nutricionistas ni entrenadores certificados.
> En casos de enfermedades crónicas o condiciones médicas especiales, se recomienda supervisión profesional.
