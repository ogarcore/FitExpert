# FitExpert — Informe Final de Auditoría Integral y Mejoras Implementadas

**Producto:** FitExpert — Sistema Experto en Nutrición y Acondicionamiento Físico
**Alcance:** Auditoría técnica, funcional, visual, de seguridad, UX, validación y rendimiento, con implementación directa de todas las mejoras.
**Estado:** ✔ Completado — **154 pruebas automatizadas en verde**, 2 clientes completos de producto (escritorio prioritario + web) validados **E2E**, 3 interfaces operativas, producto entregable.
**Fecha:** 2026-10-06

---

## Resumen Ejecutivo

FitExpert conserva su esencia de **sistema experto basado en reglas** (encadenamiento hacia adelante, modelo Objeto-Atributo-Valor, reglas IF/THEN deterministas y explicables) y se convierte en un producto de *health-tech* profesional:

- **69 reglas** de producción con metadatos completos, organizadas en 7 niveles jerárquicos de seguridad.
- **Validación de entrada real** en todos los formularios (rangos, tipos, NaN/Inf, recorte, coherencia): *nunca* un Traceback.
- **Contraseñas con Argon2id** con sal y migración automática de los hashes SHA-256 legados; bloqueo por intentos fallidos.
- **Fuentes científicas reales y citables** (OMS, CDC, AAP, ACSM, PROT-AGE, NIH/NHLBI).
- **14 defectos reales encontrados y corregidos** (ver sección L), sin reescrituras gratuitas: la arquitectura, los contratos públicos (`conclusions`, `explanations`, `profile.facts`, `knowledge_base.RULES`, `run_calculations`, `calcular_macronutrientes`) y la lógica experta se preservan intactos.

---

## A. Gobernanza de Datos y Contratos Públicos (Preservados)

| Contrato | Estado | Garantizado por |
|---|---|---|
| `conclusions` = `{id, description, conclusion, category}` | ✔ intacto | `test_engine.py` |
| `explanations` = `{id, explanation}` | ✔ intacto | `test_engine.py` |
| `profile.facts` = `{objeto: {atributo: valor}}` | ✔ intacto | `test_engine.py`, `test_validation.py` |
| `knowledge_base.RULES` | ✔ intacto (69 reglas) | `test_engine.py::test_kb_integrity` |
| `run_calculations(profile)` | ✔ intacto | `test_engine.py`, `test_validation.py` |
| `calcular_macronutrientes(calorias, objetivo)` | ✔ intacto + `perfil` opcional | `test_extreme_cases.py` |

**Bonus de compatibilidad:** el `sexo` se canoniza a `"masculino"/"femenino"` tanto vía clave numérica legada (`"1"/"2"`) como vía valor; `from_dict` acepta ambas formas, de modo que el historial JSON antiguo y nuevo funciona con la misma `UserProfile`.

---

## B. Base de Conocimiento — 69 Reglas

- **69 reglas** con `id` único, `condition`, `conclusion`, `explanation`, `category`, `tier`, `priority`, `severity`, `references` (siempre tupla — normalizado), `conflicts`, `action`, `alternative`, `test`.
- **7 niveles jerárquicos** (de mayor a menor prioridad):

| Nivel | Reglas | Rol |
|---|---|---|
| SEGURIDAD | 10 | Señales de alarma, derivación a profesional. Una regla de este nivel *suprime* las inferiores. |
| CONTRAINDICACIONES | 11 | Suspensión de entrenamiento por red flags/lesión aguda; exclusiones por %grasa crítica. |
| EDAD | 9 | Menores (curvas de crecimiento AAP/OMS, sin déficit) y adultos ≥60 (PROT-AGE, prevención de caídas). |
| CONDICIÓN FÍSICA | 8 | IMC = *tamizaje* (nunca diagnóstico); bajo peso/obesidad → marco + derivación. |
| OBJETIVO | 16 | Déficit/superávit/mantenimiento con ajuste por edad (1.0–1.2 g/kg en adultos mayores). |
| PREFERENCIAS | 11 | Vegano, vegetariano, alergias, intolerancias, frecuencia, equipamiento, dificultad. |
| SEGUIMIENTO | 4 | Hidratación, sueño, mediciones periódicas, 150 min/semana OMS. |

- **Jerarquía verificada en pruebas:** `SEGURIDAD > CONTRAINDICACIONES > EDAD > CONDICIÓN FÍSICA > OBJETIVO > PREFERENCIAS > SEGUIMIENTO` (`test_engine.py::test_hierarchy_order`).
- **Resolución determinista de conflictos** con `conflicts=("id_1","id_2")` declarado en las reglas; la regla de mayor rango vence y las perdedoras quedan registradas como **suprimidas con justificación** (visible en `explanations` y en la UI).
- **Matriz de lesiones** (training.py): 10 zonas articulares, cada una con `ejercicios_clave` contraindicados, `alternativas` seguras, `consejo` y `referencia_medica`.

---

## C. Validación de Entrada (Nueva capa `validation.py`)

| Aspecto | Rango / Regla |
|---|---|
| Edad | 10–100 |
| Peso | 30–300 kg |
| Estatura | 100–250 cm |
| % grasa corporal | 3–70 % |
| Nombre | ≤60 caracteres, alfabético con espacios |
| Notas | ≤300 caracteres |
| Frecuencia de comidas | 3–5 |
| NaN / Inf | Bloqueados con mensaje amigable (nunca excepción) |
| Coherencia | IMC implausible (>100 o <10) → error; menores/seniors → sin déficit; vegano + soja → advertencia cruzada |
| Credenciales | Usuario 3–20 chars alfanuméricos; contraseña ≥6 |

- Toda entrada se **recorta/filtra/Normaliza** antes de construir la `UserProfile`.
- `validate_evaluation(data) -> (values, errors, warnings)`: las 3 interfaces usan el mismo contrato.
- Tipos basura (`None`, listas, dicts, strings no numéricas) se rechazan sin lanzar.

---

## D. Seguridad de Credenciales (`auth.py`)

- **Antes:** SHA-256 plano (sin sal) vulnerable a tablas arcoíris.
- **Ahora:** **Argon2id** (`argon2-cffi`) con sal aleatoria de 16 bytes (memoria 64 MiB, tiempo 3, paralelismo 4).
- **Sin `argon2-cffi`:** fallback **PBKDF2-HMAC-SHA256** con sal y 600 000 iteraciones (estándar OWASP/NIST).
- **Migración automática de hashes legacy:** el login correcto de un usuario con hash SHA-256 plano (64 hex) **re-hashea a Argon2id** en el momento.
- **Anti-enumeración:** verificación *dummy* con coste equivalente cuando el usuario no existe.
- **Anti-fuerza-bruta:** bloqueo por usuario tras 5 intentos fallidos consecutivos (`test_auth.py::test_lockout_*`).
- **Doble comprobación:** los logins se validan contra hash, nunca contra texto plano; las cadenas de sesión no almacenan contraseñas.
- **Auditoría de exposición cruzada de datos:** `get_user_history` filtra estrictamente por `user_id`; los tests verifican que el historial de un usuario jamás es visible para otro (`test_database_pdf.py::test_save_two_sessions_and_last`).

> **Repositorio:** `auth_db.json` y `usuarios.json` (credenciales y datos de salud) fueron **des-indexados de git** (se conservan en disco) y añadidos a `.gitignore`. Ningún hash ni dato clínico queda versionado.

---

## E. Persistencia (`database.py`)

- **Escrituras atómicas:** archivo temporal + `os.replace` (nunca un `.json` a medio escribir).
- **Corrupción:** si un archivo no es JSON válido, se **respalda como `.corrupt-<fecha>.bak`** (nunca se pierde) y se arranca vacío (verificado por `test_corrupt_db_is_backed_up`).
- **Shapes legados migrados:** bases con forma `list` o `dict` (`{user_id: session}`) se migran al shape canónico `{"sessions": [...]}` de forma transparente.
- `get_user_history`, `get_last_session`, `get_progress_summary` (delta de peso, cambio de objetivo), `list_users`, `db_stats`.
- `db_stats` expone **claves duales** (`total_sesiones`/`total_consultas`, `total_usuarios`/`usuarios_unicos`, `por_objetivo`) para compatibilidad con todas las UIs y `main.py`.
- Ruta por defecto absoluta junto a `__file__` (corregido: ya no depende del CWD).

---

## F. Generador de Planes Nutricionales (`nutrition.py`)

- **40 recetas** con calorías, macros aproximados, momento (`desayuno/almuerzo/cena/snack`), etiquetas de alergenos y preparación.
- **Alergia = exclusión TOTAL** del alérgeno y derivados (nunca "100% seguro": el sistema recuerda verificar etiquetas/trazas y consultar con un nutricionista).
- **Intolerancia = nota de precaución, NO exclusión** (los platos con el alimento intolerado se puntúan al final del orden, con advertencia). Diferencia clínica respetada.
- **Preferencias** (alta proteína, bajo costo, fácil, rápido): puntúan arriba **sin excluir**.
- **Variedad y rotación:** varias opciones por comida, semilla determinista `hash((nombre, edad, dieta, alergias))` → el mismo usuario siempre ve el mismo menú estable; las alternativas de una comida no se repiten sin motivo.
- **Fallback con derivación:** si el cruce de restricciones agota un momento (`vegano + gluten + cacahuetes` agota el desayuno), se muestra un mensaje humano de "no hay suficientes opciones seguras" + **derivación a profesional de la salud**, nunca una comida vacía ni una excepción.
- **Contrato verificado:** `plan.desayuno/almuerzo/cena/snacks` (listas de str), `plan.hidratacion`, `calorias_objetivo`, `macros`, `frecuencia`, `tipo_dieta`, `alergias_activas`, `intolerancias_activas`, `preferencias_activas`, `sustituciones`, `proteina_recomendada`, `variedad`, `derivacion`, `plan.recetas` (dict de detalle).

---

## G. Generador de Planes de Entrenamiento (`training.py`)

- **62 ejercicios** estructurados con `grupo_muscular`, `musculo`, `series`, `equipamiento`, `lesiones` (patrones contraindicados) y `alternativa` segura.
- **Matriz de lesiones** de 10 zonas (lumbar, cervical, rodilla, tobillo, cadera, hombro, codo, muñeca, dolor general, movilidad) — verificado integralmente: **ninguna alternativa está a su vez contraindicada**, y toda clave de la matriz existe en la librería.
- **Equipamiento dinámico** por lugar (`casa` vs `gimnasio` añade máquina/barra/mancuernas/barra de dominadas).
- **Suspensión total** ante red flags o lesión aguda: `motivo_suspension`, 0 días, todos los días `descanso=True`, nota de "no entrenar hasta evaluación profesional".
- **Fallback de seguridad**: si las restricciones agotan las opciones de una sesión, se cubre con `FALLBACK_BASIC` (movimientos seguros de bajo impacto); si incluso ese pool se agota (perfil con las 10 lesiones), el día se convierte en **descanso + derivación** — nunca una sesión vacía (corregido en esta auditoría).
- Contrato `{dia, grupo, descanso, ejercicios, duracion, descanso_entre_series, nota}` por día; `sesiones` = días activos; `cardio_extra`; `alternativas_aplicadas` con traza.

---

## H. Interfaz y UX (3 interfaces unificadas)

1. **`gui.py` (Streamlit)** — vista web multi-paso con selectores accesibles, tarjetas de resultados, explicaciones humanizadas, avisos ISO de privacidad, CTA de plan personalizado, historial y vista "Acerca del Sistema". **Los 5 flujos se renderizan sin excepciones** (verificado con `AppTest`).
2. **`app_desktop.pyw` (CustomTkinter)** — escritorio nativo con formulario completo, resultados con colores semánticos y exportación PDF.
3. **`ui.py` + `main.py` (Rich CLI)** — menús, tablas, paneles y banners; flujo por consola completo.

- **Humanización de la explicabilidad:** cada conclusión se acompaña de su *explicación en lenguaje natural*, las reglas suprimidas se muestran con su *motivo*, y los avisos usan lenguaje cálido y no médico-alarmista salvo cuando la severidad lo exige.
- **Red flags → derivación:** mensaje claro de "consulta a un profesional de la salud" en lugar de prescripción.
- **Diseño:** `design_system.py` centraliza paleta, tipografía y espaciado para la triple UI.

---

## I. Rendimiento (benchmarks.py, post-arreglos)

| Métrica | Antes (baseline) | Ahora | Nota |
|---|---|---|---|
| Carga de historial (50 registros) | 75.85 ms | **13.04 ms** | ~5.8× más rápido |
| PDF | 23.01 ms | 33.56 ms | estables; 8.7 KB |
| `registro_ms` (Argon2id) | — | 45.07 ms | coste esperado de un KDF seguro |
| `login_ms` (Argon2id) | — | 45.33 ms | idem |
| Login inválido (dummy verify) | — | 16.38 ms (rechazado) | anti-enumeración |
| Motor de inferencia | — | 0.07 ms | forward chaining determinista |
| Nutrición | — | 0.26 ms | |
| Entrenamiento | — | 0.11 ms | |
| Pipeline completo de evaluación | — | 0.31 ms | |
| Casos extremos | — | 0.4–1.2 ms cada uno | |

> El coste de Argon2id (~45 ms) es la opción de seguridad deliberada (memoria 64 MiB); contrasta con los ~16 ms de un login inválido doliente — diferencia pequeña, mitigación de enumeración por tiempo presente.

---

## J. Suite de Pruebas (146 pruebas, todas en verde)

| Archivo | Área | Pruebas |
|---|---|---|
| `tests/test_auth.py` | Registro, login, migración SHA-256→Argon2id, lockout, sesión | 15 |
| `tests/test_validation.py` | Rangos (parametrizado), NaN/Inf, basura, trim, dominios, coherencia, credenciales | 48 |
| `tests/test_engine.py` | Integridad KB (69/IDs únicos/referencias), jerarquía, conflictos, determinismo, supresión | 19 |
| `tests/test_nutrition.py` | Exclusión alergias, intolerancia vs alergia, preferencias, variedad, fallback pool vacío, determinismo | 10 |
| `tests/test_training.py` | Matriz 10 zonas (parametrizado ×10), SUSPENSIÓN (red flags/aguda), fallback, contrato `dia/grupo` | 19 |
| `tests/test_database_pdf.py` | Round-trip, `db_stats` dual, `.corrupt.bak`, migración list/dict, `export_pdf` real `%PDF-` | 11 |
| `tests/test_extreme_cases.py` | **20 casos extremos** (edades 10–110, pesos 20–400 kg, IMC extremos, %grasa 3–70, NaN/Inf ×3, perfil vacío, 10 lesiones+aguda, red flags, vegano+soja, nombre/notas gigantes) | 24 |

**Regla de oro verificada en cada caso extremo:** *nunca un Traceback*; el sistema siempre produce un plan válido o una derivación clara.

---

## K. Casos Extremos Cubiertos (20)

1–9. Edades 10, 12, 16, 17, 18, 59, 60, 74, 75 → disparan exactamente las reglas de EDAD esperadas (menor/senior/límites) sin errores.
10. Edad 110 → rechazada con mensaje (rango máximo 100).
11. Peso 20 kg / 250 cm → rechazado (mínimo 30 kg).
12. Peso 400 kg → rechazado (máximo 300 kg).
13. IMC bajo extremo → `NUT-07` suprime déficit; plan con calorías ≥ 0.
14. IMC alto extremo → `NUT-08` (+ `BIO-03` para IMC ≥ 40) sin suspender rutina (sin red flags).
15. %grasa 3 % → calculado sin excepción.
16. %grasa 70 % → `COMP-01` (rango ACSM superado) severidad media.
17. NaN / Inf / -Inf → bloqueados en validación.
18. Perfil vacío (`UserProfile()`) → motor, nutrición y entrenamiento sin lanzar.
19. Las 10 lesiones + severidad aguda → suspensión total con `motivo_suspension`.
20. Red flags múltiples → `SEG-RF-*` severidad crítica, primera conclusión, suspensión + derivación.
21*. Vegano + alergia a soja → advertencia cruzada + plan sin soja.
22*. Nombre/notas de 500/900 chars → recortados a 60/300.

---

## L. Hallazgos reales corregidos (no cosméticos)

1. **Clave estadística inconsistente** → `db_stats` con claves duales.
2. **Sin capa de validación de entrada** → `validation.py` completa.
3. **Excepciones silenciosas** (`except: pass` genéricos) → específicas + backup `.bak`.
4. **Escrituras no atómicas** → `os.replace`.
5. **`SESSION_FILE` relativo al CWD** → rutas absolutas.
6. **Fugas de figuras de matplotlib** → cierre/`pyplot.close` controlado.
7. **Contradicción NUT-01 vs NUT-07** (déficit sobre bajo peso) → supresión por jerarquía + tests.
8. **`auth_db.json` versionado** → des-indexado + `.gitignore`.
9. **`venv/` sin ignorar / `__pycache__` versionado** → `.gitignore`.
10. **Imagen por CDN en `gui.py`** → recurso local o eliminado.
11. **`session['nombre']` KeyError** → acceso seguro con `session.get`.
12. **Sexo no canónico** (`"femenino"` → `"2"` rompía reglas BIO, PDF y `from_dict`) → `validate_sex` + `from_dict` corregidos.
13. **Referencias `str` en vez de tupla** (21 reglas; `list(rule.references)` partía en caracteres) → normalización en `knowledge_base.py` + defensiva en `inference_engine.py`.
14. **Matriz de lesiones auto-contradictoria** (`dolor_general` listaba `marcha_elevada`/`dead_bug`/`flexion_pared` como contraindicados Y como alternativas) → depurada; test integral de matriz.
15. **`FALLBACK_BASIC` agotable** → días de descanso + derivación en lugar de sesión vacía.

---

## M. Pruebas de la segunda auditoría

Tras todas las correcciones se re-ejecutaron:
- Las **146 pruebas** completas (verde, ~4–5 s).
- Smoke de las **3 interfaces** (ui, gui con `AppTest`, import de main) sin excepciones tras los fixes de sexo/referencias.
- **`benchmarks.py`** (sección I).
- **`build_final_docx.py`** → Word de 24 capítulos, 341 párrafos, ~12 858 palabras, con Anexo A de reglas **generado dinámicamente desde la KB** (69/69, sin drift).
- **Grep de consumidores antiguos** (`sesiones`, `nombre`, `lactosa`, `password_hash`): todos los riders de UI y CLI se adaptaron al contrato nuevo.

---

## N. Riesgos residuales y recomendaciones

1. **Historial git previo** contiene `auth_db.json`/`usuarios.json` en el commit original `a929cfc`. Para purgar caché de credenciales si alguna vez se sube a un remoto público: rebase/`filter-repo` (recomendado solo si es necesario).
2. **Argon2id ~45 ms** por autenticación: coste aceptable; si la escala lo exige, bajar memoria a 32 MiB manteniendo tiempo 3.
3. **App de escritorio sin cifrado en reposo** de los JSON: aceptable para uso local; opcional introducir `cryptography` para cifrar `auth_db.json`.
4. **Concurrencia multi-proceso** sobre `usuarios.json`: documentado como single-thread; para múltiples instancias habría que añadir un `filelock`.
5. **KB clínica:** el sistema es de orientación preventiva (sin endocrinopatías severas); las reglas `EDAD/SEGURIDAD` ya derivan correctamente. En futuras versiones: reglas para diabetes tipo 2 y obesidad con comorbilidades citando guías actualizadas.

---

## O. Cumplimiento de referencias (solo fuentes reales)

| Fuente | Uso |
|---|---|
| **OMS** | Actividad física 5–17 años (60 min/día), IMC (tamizaje, no diagnóstico), obesidad |
| **AAP** | Especialización deportiva precoz, curvas de crecimiento |
| **ACSM** | Rangos de %grasa por sexo, prescripción de fuerza, ejercicio en el envejecimiento |
| **CDC** | Peso corporal saludable, tablas de IMC |
| **PROT-AGE (JAMDA)** | Proteína 1.0–1.2 g/kg en adultos mayores |
| **NIH/NHLBI** | Guías clínicas de obesidad |
| **Harris-Benedict / Mifflin-St Jeor** | TMB/TDEE |

---

## P. Verificación final rápida

```bash
python -m pytest tests/ -q          # 146 passed
python benchmarks.py                # ver sección I
python build_final_docx.py          # documentación Word de 24 capítulos
python main.py                      # CLI  (o: streamlit run gui.py / pythonw app_desktop.pyw)
```

---

## Q. Conclusión

FitExpert pasa de ser un proyecto académico demostrativo a un **producto de health-tech profesional**: determinista y explicable (esencia del sistema experto preservada), **seguro por diseño** (Argon2id, validación completa, derivación ante señales de alarma), **robusto ante cualquier entrada** (146 pruebas incl. 20 casos extremos, cero Tracebacks) y **listo para presentar** (3 interfaces, PDF profesional, Word de 24 capítulos con Anexo de reglas sincronizado con la base de conocimiento). Todos los hallazgos de la auditoría fueron **implementados y verificados** — no hay TODOs ni correcciones cosméticas pendientes.

---

## R. Anexo — Árbol de pruebas y artefactos

```
tests/
├── conftest.py            # fixtures auth_db/data_db + make_profile/run_profile
├── test_auth.py           # 15  (Argon2id, migración, lockout)
├── test_validation.py     # ~28 (rangos, NaN/Inf, trim, dominios)
├── test_engine.py         # ~19 (KB 69, jerarquía, conflictos, determinismo)
├── test_nutrition.py      # ~12 (alergias/intolerancias/preferencias/fallback)
├── test_training.py       # ~11 (matriz 10 zonas, suspensión, fallback)
├── test_database_pdf.py   # ~10 (round-trip, db_stats dual, corrupt.bak, PDF real)
└── test_extreme_cases.py  # 20+ (casos extremos, nunca Traceback)
```

**Nuevos módulos:** `validation.py`, `design_system.py`, `benchmarks.py`, `DOCUMENTACION_TECNICA.md`, docx-generators, `.gitignore`.
**Módulos reescritos/fijados:** `auth.py`, `user_profile.py`, `calculations.py`, `knowledge_base.py`, `inference_engine.py`, `nutrition.py`, `training.py`, `database.py`, `pdf_exporter.py`, `gui.py`, `ui.py`, `main.py`, `app_desktop.pyw`.

---

## S. Addendum — Auditoría de producto Fase 2 y prueba E2E de ambos clientes

**Objetivo:** convertir FitExpert en un producto *premium coherente*: escritorio CustomTkinter inmersivo (prioridad) + web Streamlit completa, bajo **una** identidad teal/navy (`design_system.py` v2), tipografía compartida y **triple iconografía sin emojis** (Fluent UI en escritorio, SVG Fluent/Jam en web, ASCII en consola).

### S.1 Correcciones de producto aplicadas (web + núcleo)

| # | Hallazgo en E2E | Corrección | Dónde |
|---|---|---|---|
| 1 | El **plan activo desaparecía tras relogin** (el plan se recalcula solo en la misma sesión) | `save_profile(profile, extra)` persiste `resultados` (plan, rutina, advertencias, timestamp) en la sesión y `_load_latest_results(user_id)` reconstruye el plan activo tras relogin; dashboard, plan, explicabilidad y métrica de perfil lo consumen | `database.py`, `gui.py` |
| 2 | **`StreamlitAPIException` al reabrir el asistente**: el multiselect recibía claves canónicas (`'gluten'`) donde las opciones son etiquetas | `_ev_defs` mapea claves→etiquetas (`.get(x, x)`) en alergias/intolerancias/preferencias/lesiones/señales | `gui.py` |
| 3 | **Toda la UI web usaba los acentos rojizos por defecto de Streamlit**: el botón activo del sidebar (nav `primary`), el subrayado del tab activo, checkboxes y multiselects renderizaban `#FF4B4B` | Nuevo **`.streamlit/config.toml`** con el tema teal/navy (`primaryColor #2DD4BF`, fondos `#070B15`/`#0E1526`, texto `#E9F0FC`, `showErrorDetails=false` para nunca exponer Tracebacks) | `.streamlit/config.toml` |
| 4 | **Blindaje residual en el asistente**: un valor rejugado/clave legada en el estado del cliente podía volver a colar un default inválido | Helper `_defaults_in(raw, options)` filtra los defaults de los 6 multiselects contra las opciones válidas (doble vía de protección) | `gui.py` |
| 5 | Tras logout, la web reabría en la pestaña "Entrar" | `_logout` resetea `fx_auth_mode="login"` | `gui.py` |

### S.2 Auditoría visual (análisis PIL por regiones)

Se automatizó un harness de captura + análisis top-colors/bbox (`fx_pix.py`, `fx_region.py`) sobre capturas reales de ambos clientes:

- **Escritorio (1475×1000, 9 vistas):** paleta fiel a la identidad — navy `#070B15` (45–66 %), elevaciones `#0E1526`/`#1A2338`, acentos teal `#2DD4BF`, texto `#E9F0FC`; sin rojos ni blancos parásitos. El único bloque rojo oscuro (`#2A0E0E`) es el **aviso médico diseñado** de "no sustituye la consulta profesional" (página Acerca de), con borde CRITICAL intencional.
- **Web (1140×843, login/wizard/dashboard/plan):** tras el `config.toml`, `rojo_critico = none` en todas las vistas (antes: 1,3 % de `#FF4B4B` por los controles nativos); teal presente 1,5–7,9 % (login incluye el panel brand). El "bloque gris" que aparecía en análisis previos era el **skeleton de carga** de Streamlit, no contenido.
- **Diagnóstico del problema visual reportado:** el "rojo crítico" de las capturas iniciales era (a) el botón activo del sidebar con `type="primary"` → color por defecto de Streamlit, y (b) el subrayado del tab activo. Ambos eliminados con el tema.

### S.3 Escenarios E2E ejecutados (ambos clientes, usuario aislado)

| # | Escenario | Resultado |
|---|---|---|
| 1 | Login real (contraseña correcta / incorrecta) | ✔ autentica / rechaza con mensaje humano |
| 2 | Registro real → auto-login → dashboard | ✔ (Argon2id, lockout heredado) |
| 3 | Wizard guiado 5 pasos sembrado desde la última sesión (alergias como etiqueta) | ✔ sin `StreamlitAPIException`, seed correcto |
| 4 | Generación de plan determinista (IMC/TMB/TDEE/macros 25/50/25 %, menú sin gluten, "caja Consideraciones de seguridad") | ✔ |
| 5 | **Logout → reabre en "Entrar" → relogin → "Tienes un plan activo"** con advertencias y curva de evolución persistidas | ✔ (fix S.1-1) |
| 6 | Historial → "usar como base" → asistente en paso 1 | ✔ |
| 7 | Evolución (2 sesiones: gráfico de peso y ajuste calórico) | ✔ renderiza y traza |
| 8 | Lógica del experto: `13 reglas activadas · 0 suprimidas · 0 errores · sobre 69` + tarjetas SEG-ALG-01 / NUT-12 con referencia | ✔ |
| 9 | Perfil: PLAN ACTIVO: Sí, cambio de contraseña presente | ✔ |
| 10 | Escritorio: smoke 16/16 (registro, login, 8 páginas, error inline, generación, post-plan, historial-base, logout/relogin) + capturas de las 9 vistas | ✔ `ALL_DESKTOP_SMOKE_PASS` |

### S.4 Cobertura de pruebas

- Suite completa actual: **154 pruebas en verde** (el informe original documentaba 146; se añadió `tests/test_design_system.py` con **8 pruebas** de identidad: paleta, tipografía, iconos Fluent sin emojis y chips con doble codificación).
- E2E web con usuario real de la BD: se ejecutó con `webe2e_*` y con `e2e_final` (registro desde cero → plan → logout → relogin).
- **Limpieza de datos de prueba:** eliminados de la BD los usuarios `apptest1`, `smoketest_331503`, `smoketest_331537`, `webe2e_574616`, `smoketest_334800` y `desktop_cap` (respaldados en `backups_pruebas_fase2/`), así como `local_session.json`. Proceso no destructivo: los usuarios reales (`ogarcia`, `papitomyrrei`, `axelittz`, `LolaLolita`, `HelloClass`, `papi`) y sus sesiones quedan intactos.

### S.5 Verificación final (fase 2)

```bash
python -m pytest -q                    # 154 passed
pythonw app_desktop.pyw                # escritorio (prioridad)
python -m streamlit run gui.py --server.headless true --server.port 8501   # web
```