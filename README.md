# FitExpert — Sistema Experto en Nutrición y Acondicionamiento Físico

> Proyecto académico | Inteligencia Artificial | Sistemas Expertos
> **Producto premium de health-tech**: mismo motor experto, dos clientes completos bajo **una** identidad visual teal/navy.

## Descripción

FitExpert genera planes personalizados de **nutrición y entrenamiento** con **explicabilidad total**: cada recomendación cita la regla, el dato del usuario que la activó y la fuente científica (OMS, CDC, AAP, ACSM, PROT-AGE, NIH/NHLBI). Motor de inferencia por **encadenamiento hacia adelante** (69 reglas IF/THEN en 7 niveles jerárquicos de seguridad), determinista, sin alucinaciones.

## Los dos clientes (misma lógica, misma identidad)

| Cliente | Tecnología | Rol |
|---|---|---|
| **Escritorio** (`app_desktop.pyw`) | CustomTkinter (prioridad) | Experiencia inmersiva: wizard guiado de 5 pasos, sidebar agrupada con iconos Fluent (sin emojis), errores inline (nunca `messagebox`), página de plan, historial, evolución y PDF |
| **Web** (`gui.py`) | Streamlit | Multi-página completa: **login/registro/logout reales** (Argon2id), dashboard, evaluación guiada, resultados, nutrición, entrenamiento, historial, lógica del experto, perfil y evolución |
| Consola (`ui.py` + `main.py`) | Rich CLI | Flujo terminal completo para servidores sin entorno gráfico |

Misma autenticación y las mismas reglas/dominios en ambos clientes: el plan generado en uno puede visualizarse y explicarse en el otro.

## Identidad visual única

`design_system.py` centraliza paleta (**teal `#2DD4BF` / navy `#070B15`**), tipografía (Segoe UI Variable / system), espaciado y doble iconografía (Fluent UI en escritorio, SVG fluent/Jam en web). **Prohibido el emoji como iconografía** (solo en contenido textual). En web, `.streamlit/config.toml` fija el tema teal del framework para que tabs, checkboxes y botones actives nunca tiñan de rojo por defecto.

## Arquitectura

```
FitExpert/
├── knowledge_base.py    ← 69 reglas IF/THEN (metadatos, referencias, jerarquía, conflictos)
├── inference_engine.py  ← Encadenamiento hacia adelante + explicaciones
├── calculations.py      ← IMC, TMB (Mifflin-St Jeor), TDEE, macros
├── nutrition.py         ← Planes por objetivo con exclusión de alergenos (40 recetas)
├── training.py          ← Rutinas casa/gimnasio con matriz de 10 zonas lesivas (62 ejercicios)
├── user_profile.py      ← Modelo de datos + dominios (normalización legada)
├── validation.py        ← Validación de entrada: rangos, NaN/Inf, recorte, coherencia
├── auth.py              ← Argon2id (fallback PBKDF2), migración legada, lockout
├── database.py          ← Persistencia JSON atómica + analítica histórica
├── design_system.py     ← Identidad teal/navy compartida por las UIs
├── gui.py               ← Cliente web Streamlit (autenticación completa)
├── app_desktop.pyw      ← Cliente de escritorio CustomTkinter (prioritario)
├── ui.py / main.py      ← Interfaz de consola Rich
├── .streamlit/config.toml ← Tema teal/navy del framework web
└── tests/               ← 154 pruebas automatizadas
```

## Requisitos

- Python 3.10+ (probado en 3.12 y 3.14)
- `customtkinter`, `streamlit`, `rich`, `matplotlib`, `reportlab`, `pandas`
- `argon2-cffi` (recomendado: Argon2id; sin él se usa PBKDF2-HMAC-SHA256)

```bash
python -m pip install -r requirements.txt   # si existe
python -m pip install rich customtkinter matplotlib reportlab pandas streamlit argon2-cffi
```

## Ejecución

### 1. Escritorio (recomendado — sin terminal de fondo)
```bash
pythonw app_desktop.pyw
```
*(o doble clic en `app_desktop.pyw`). La sesión local previa se borra al cerrar; el registro y login se hacen dentro de la app.*

### 2. Web
```bash
python -m streamlit run gui.py --server.headless true --server.port 8501
```
Abre `http://localhost:8501` — la web tiene su propio registro/login real y aislamiento por usuario.

### 3. Consola
```bash
python main.py
```

## Funcionalidades

- [x] Registro / login / logout **reales** en web y escritorio (Argon2id, migración legada)
- [x] Aislamiento por usuario (nadie ve historial ajeno)
- [x] Evaluación guiada (wizard de 5 pasos) con validación inline
- [x] IMC, TMB, TDEE, calorías objetivo y macros (25/50/25 % por defecto)
- [x] Plan alimenticio con exclusión estricta de alergenos y preferencias puntuadas
- [x] Rutinas casa/gimnasio × 3 niveles × 5 objetivos, con matriz de lesiones
- [x] Motor de inferencia: 69 reglas, jerarquía y supresión justificada
- [x] Explicabilidad: "Lógica del experto" (web), página de explicaciones (escritorio)
- [x] Historial, evolución ponderal y **persistencia del plan activo tras relogin**
- [x] Exportación de plan a PDF con justificación por regla
- [x] Identidad teal/navy unificada, sin emojis como iconografía
- [x] 154 pruebas en verde (incl. 20 casos extremos: nunca un Traceback)

## Pruebas

```bash
python -m pytest -q            # 154 passed
```

## Limitaciones

> Orientación general basada en principios establecidos. **No reemplaza** la consulta con nutricionistas, médicos ni entrenadores certificados (el propio sistema deriva a un profesional ante señales de alarma).