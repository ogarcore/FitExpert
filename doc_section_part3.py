"""
doc_section_part3.py
====================
Contenido y redacción formal para los Capítulos 11 al 16:
  11. Principales Módulos del Sistema
  12. Interfaz y Experiencia de Usuario
  13. Información y Datos que Maneja el Sistema
  14. Tecnologías Utilizadas
  15. Funcionamiento Interno a Nivel General (con diagrama de arquitectura)
  16. Seguridad y Control de Acceso
"""

import os
import docx
from doc_builder_core import (
    add_title_header, add_p, add_bullet, add_callout, add_table_data,
    add_figure, HEX_NAVY_DARK, HEX_BG_LIGHT
)


def build_chapters_11_to_16(doc: docx.Document):
    """Construye los capítulos 11 al 16 con rigor conceptual y arquitectónico."""

    # ═════════════════════════════════════════════════════════════════════════
    # CAPÍTULO 11: PRINCIPALES MÓDULOS DEL SISTEMA
    # ═════════════════════════════════════════════════════════════════════════
    add_title_header(doc, "11. Principales Módulos del Sistema", level=1)
    add_p(doc, "FitExpert está concebido bajo una arquitectura modular desacoplada, donde cada componente funcional encapsula una responsabilidad específica del dominio sin interferir con las capas visuales ni de almacenamiento. A continuación se analizan los ocho módulos principales que dan vida al sistema:")

    add_title_header(doc, "11.1 Desglose Modular Funcional", level=2)

    add_p(doc, "Responsable del registro, validación y verificación de identidades. Administra la emisión de identificadores UUIDv4 y garantiza que las credenciales permanezcan cifradas localmente.", bold_prefix="1. Módulo de Autenticación y Perfil (`auth.py`, `user_profile.py`):")
    add_bullet(doc, "Gestiona el ciclo de vida de la sesión activa y mantiene la entidad central `UserProfile` que sirve como repositorio temporal unificado de hechos.", bold_prefix="• Función Operativa:")

    add_p(doc, "Encargado de ejecutar las operaciones aritméticas continuas basadas en la literatura médica.", bold_prefix="2. Módulo de Cálculo Fisiológico y Metabólico (`calculations.py`):")
    add_bullet(doc, "Resuelve las fórmulas de Mifflin-St Jeor para la Tasa Metabólica Basal, aplica los coeficientes multiplicadores de actividad física, clasifica el IMC según los baremos de la OMS y calcula la partición óptima de macronutrientes en gramos.", bold_prefix="• Función Operativa:")

    add_p(doc, "El núcleo cognitivo de inteligencia artificial del sistema.", bold_prefix="3. Módulo de Inferencia y Base de Conocimiento (`inference_engine.py`, `knowledge_base.py`):")
    add_bullet(doc, "Alberga 69 reglas de producción estructuradas mediante el formalismo Objeto-Atributo-Valor. El motor ejecuta un algoritmo determinista por encadenamiento hacia adelante que evalúa las condiciones del perfil del usuario, activando deducciones y generando las explicaciones clínicas pertinentes.", bold_prefix="• Función Operativa:")

    add_p(doc, "Generador de planes alimentarios equilibrados adaptados a preferencias éticas o de salud.", bold_prefix="4. Módulo de Nutrición y Filtros Culinarios (`nutrition.py`):")
    add_bullet(doc, "Combina catálogos alimentarios para dietas omnívoras, vegetarianas, veganas y pescetarianas, aplicando un analizador sintáctico de palabras clave que excluye de forma rigurosa ingredientes con lactosa, gluten, frutos secos, soya o huevo.", bold_prefix="• Función Operativa:")

    add_p(doc, "Diseñador de microciclos semanales de ejercicio físico.", bold_prefix="5. Módulo de Programación Biomecánica del Entrenamiento (`training.py`):")
    add_bullet(doc, "Administra una biblioteca especializada de movimientos clasificados por grupo muscular, requerimientos de equipo y contraindicaciones articulares. Selecciona la plantilla semanal idónea y sustituye automáticamente ejercicios peligrosos por variantes guiadas seguras.", bold_prefix="• Función Operativa:")

    add_p(doc, "Subsistema de transparencia y auditoría cognitiva.", bold_prefix="6. Módulo de Explicabilidad y Pedagogía Clínica:")
    add_bullet(doc, "Recopila los argumentos biomédicos de cada regla disparada, traduciéndolos a una narrativa pedagógica en español neutro comprensible para cualquier persona no versada en medicina o ciencias del deporte.", bold_prefix="• Función Operativa:")

    add_p(doc, "Capa de persistencia y análisis longitudinal.", bold_prefix="7. Módulo de Persistencia y Analítica Histórica (`database.py`, `usuarios.json`):")
    add_bullet(doc, "Implementa el patrón de Acceso a Datos (DAO), permitiendo almacenar consultas sucesivas por usuario, calcular métricas de variación neta de peso corporal y alimentar los tableros gráficos de evolución.", bold_prefix="• Función Operativa:")

    add_p(doc, "Generador de expedientes portables e imprimibles.", bold_prefix="8. Módulo de Generación Documental y Visualización (`pdf_exporter.py`, `matplotlib`):")
    add_bullet(doc, "Ensambla informes clínicos estructurados en formato PDF mediante la biblioteca ReportLab y proyecta gráficos vectoriales interactivos embebidos en la interfaz gráfica del usuario.", bold_prefix="• Función Operativa:")

    # ═════════════════════════════════════════════════════════════════════════
    # CAPÍTULO 12: INTERFAZ Y EXPERIENCIA DE USUARIO
    # ═════════════════════════════════════════════════════════════════════════
    add_title_header(doc, "12. Interfaz y Experiencia de Usuario", level=1)
    add_p(doc, "La experiencia del usuario ha sido cuidada con el máximo rigor estético y ergonómico. Reconociendo que diferentes usuarios operan en distintos entornos tecnológicos, FitExpert ofrece una arquitectura tri-modal versátil, donde una misma lógica de inteligencia artificial puede consumirse a través de tres canales de interacción desacoplados:")

    add_title_header(doc, "12.1 Aplicación Nativa de Escritorio Premium (CustomTkinter)", level=2)
    add_p(doc, "Es el canal principal y recomendado para el usuario final en entornos de escritorio modernos (Windows, macOS y Linux). Diseñada íntegramente con la biblioteca CustomTkinter, prescinde por completo de ventanas de consola secundarias al ejecutarse como proceso silencioso (`pythonw app_desktop.pyw`).", bold_prefix="Canal de Escritorio:")
    add_bullet(doc, "Utiliza una cuidada paleta en tonos pizarra oscura (Slate 900 `#0F172A` y Slate 800 `#1E293B`) con acentos esmeralda (`#10B981`), minimizando la fatiga visual durante sesiones prolongadas.", bold_prefix="• Paleta 'Dark Mode' Moderna:")
    add_bullet(doc, "Menú lateral intuitivo con accesos directos a 'Mi Perfil', 'Nueva Evaluación', 'Plan Actual', 'Historial' y 'Acerca de'.", bold_prefix="• Navegación Lateral Ergonómica:")
    add_bullet(doc, "Cuadros de entrada inteligentes que filtran caracteres no válidos (rechazo de letras en campos de peso o edad), selectores desplegables armonizados y casillas de verificación reactivas.", bold_prefix="• Formularios Validados:")
    add_bullet(doc, "En el panel general, la interfaz proyecta un lienzo interactivo de Matplotlib que dibuja la curva de pesaje histórico del usuario sin recargar la pantalla.", bold_prefix="• Lienzo Gráfico Embebido:")

    add_title_header(doc, "12.2 Panel Web Reactivo (Streamlit)", level=2)
    add_p(doc, "Ideal para entornos donde se prefiera el acceso mediante navegador web o despliegues en servidores locales de intranet (`streamlit run gui.py`). Ofrece una disposición fluida en múltiples columnas con controles deslizantes para medidas corporales, pestañas reactivas para los planes y visualización instantánea de la base de hechos en formato Objeto-Atributo-Valor.", bold_prefix="Canal Web:")

    add_title_header(doc, "12.3 Interfaz de Consola Avanzada (Rich CLI)", level=2)
    add_p(doc, "Diseñada para servidores remotos, administradores de sistemas o terminales de bajo consumo de recursos (`python main.py`). Mediante la biblioteca `rich`, la consola despliega un entorno visual estilizado con paneles redondeados, tablas con bordes cyan, árboles de hechos jerárquicos y resaltado de sintaxis en tiempo real, demostrando que la terminal puede ofrecer una experiencia estética de primer nivel.", bold_prefix="Canal Consola:")

    # ═════════════════════════════════════════════════════════════════════════
    # CAPÍTULO 13: INFORMACIÓN Y DATOS QUE MANEJA EL SISTEMA
    # ═════════════════════════════════════════════════════════════════════════
    add_title_header(doc, "13. Información y Datos que Maneja el Sistema", level=1)
    add_p(doc, "FitExpert gestiona un ecosistema informativo enriquecido que va mucho más allá de un simple registro de nombres y números. La información administrada se clasifica en las siguientes categorías funcionales:")

    add_table_data(doc,
        headers=["Categoría de Información", "Datos Específicos que Administra", "Propósito Funcional en el Sistema"],
        data=[
            ["Identidad y Seguridad", "Nombre de usuario, firma hash SHA-256 de la contraseña, UUIDv4 de sesión.", "Autenticar al usuario y aislar su historial clínico de otros usuarios."],
            ["Biometría y Antropometría", "Edad (años), sexo biológico, peso (kg), estatura (cm), % de grasa corporal.", "Alimentar las ecuaciones metabólicas de Mifflin-St Jeor y clasificación del IMC según la OMS."],
            ["Hábitos y Nivel de Actividad", "Nivel de sedentarismo o actividad física diaria (1.2 a 1.9), experiencia atlética previa.", "Calcular el Gasto Energético Total Diario (TDEE) y calibrar la frecuencia del microciclo."],
            ["Metas Fisiológicas", "Pérdida de grasa, hipertrofia muscular, definición, recomposición corporal, mantenimiento.", "Determinar el déficit (-500 kcal), superávit (+400 kcal) o balance neutro diana."],
            ["Restricciones Osteoarticulares", "Molestias o lesiones previas en zona lumbar, rodillas o articulaciones del hombro.", "Activar filtros de seguridad biomecánica que sustituyen ejercicios lesivos por variantes guiadas."],
            ["Preferencias y Alergias", "Patrón dietético (omnívoro, vegano, etc.), frecuencia de ingestas (3-5), alergias (lactosa, gluten, etc.).", "Filtrar el catálogo culinario, purgar alérgenos y ensamblar las comidas del día."],
            ["Recursos Espaciales y Equipo", "Entorno (hogar o gimnasio), inventario disponible (mancuernas, bandas, barras, kettlebell).", "Adaptar la selección de ejercicios a los implementos reales del usuario."],
            ["Historial Longitudinal", "Fecha de cada sesión, pesos históricos, cambios calóricos acumulados, evolución neta.", "Monitorear el progreso temporal, detectar estancamientos y graficar la tendencia."],
        ],
        col_widths=[1.8, 2.5, 2.2]
    )

    # ═════════════════════════════════════════════════════════════════════════
    # CAPÍTULO 14: TECNOLOGÍAS UTILIZADAS
    # ═════════════════════════════════════════════════════════════════════════
    add_title_header(doc, "14. Tecnologías Utilizadas", level=1)
    add_p(doc, "La selección tecnológica de FitExpert obedeció a principios estrictos de robustez, portabilidad, bajo consumo de recursos y facilidad de mantenimiento. Cada componente desempeña una labor irremplazable dentro del ecosistema:")

    add_bullet(doc, "Lenguaje de programación de alto nivel que sirve como soporte universal para toda la lógica matemática, los motores de reglas y las interfaces. Su tipado dinámico pero estricto mediante `dataclasses` y `NamedTuple` asegura un código legible y altamente mantenible.", bold_prefix="• Python 3 (v3.10 a v3.14):")
    add_bullet(doc, "Framework visual moderno para interfaces gráficas de escritorio sobre Tkinter. Proporciona componentes nativos renderizados con soporte 'Dark Mode', animaciones fluidas, esquinas redondeadas y escalado automático según los ppp de la pantalla.", bold_prefix="• CustomTkinter (v5.2):")
    add_bullet(doc, "Plataforma de desarrollo ágil de aplicaciones web analíticas. Facilita la generación reactiva de interfaces web sin necesidad de escribir código JavaScript, permitiendo el despliegue inmediato en redes locales.", bold_prefix="• Streamlit (v1.58):")
    add_bullet(doc, "Biblioteca líder en formateo estilizado para terminales de comandos. Permite renderizar tablas enriquecidas, árboles de datos y texto enriquecido con paletas hexadecimales completas.", bold_prefix="• Rich (v15.0):")
    add_bullet(doc, "Biblioteca de cálculo visual y generación gráfica. Utilizada para procesar y renderizar lienzos vectoriales con las tendencias temporales de masa corporal e indicadores de composición.", bold_prefix="• Matplotlib (v3.10):")
    add_bullet(doc, "Motor industrial para la creación programática de documentos PDF. Permite generar expedientes médicos y deportivos de alta resolución con tipografías vectoriales, tablas con flujos automáticos de página y diseño editorial profesional.", bold_prefix="• ReportLab (v5.0):")
    add_bullet(doc, "Módulos nativos de la biblioteca estándar de Python utilizados para la generación de firmas criptográficas SHA-256 e identificadores de sesión universalmente únicos.", bold_prefix="• Hashlib y UUID:")
    add_bullet(doc, "Estándar semiestructurado de texto plano utilizado para el almacenamiento persistente de credenciales y registros históricos, garantizando total portabilidad sin dependencias de motores de bases de datos pesados.", bold_prefix="• JSON:")

    # Inserción de Gráfica de Macros
    img_macros = os.path.join("doc_assets", "distribucion_macros.png")
    add_figure(doc, img_macros, "Figura 2. Partición porcentual de macronutrientes por objetivo fisiológico calculada por FitExpert.", width_in=5.8)

    # ═════════════════════════════════════════════════════════════════════════
    # CAPÍTULO 15: FUNCIONAMIENTO INTERNO A NIVEL GENERAL
    # ═════════════════════════════════════════════════════════════════════════
    add_title_header(doc, "15. Funcionamiento Interno a Nivel General", level=1)
    add_p(doc, "Para comprender cómo opera FitExpert bajo el capó sin necesidad de descifrar líneas de código complejas, es fundamental analizar su arquitectura conceptual en capas desacopladas y el ciclo de inferencia por encadenamiento hacia adelante:")

    # Inserción del Diagrama de Arquitectura
    img_arq = os.path.join("doc_assets", "diagrama_arquitectura.png")
    add_figure(doc, img_arq, "Figura 3. Arquitectura conceptual en capas desacopladas de FitExpert v2.0.", width_in=6.2)

    add_title_header(doc, "15.1 El Modelo Objeto-Atributo-Valor (OAV)", level=2)
    add_p(doc, "En la Inteligencia Artificial Simbólica, el conocimiento y los hechos del mundo deben estructurarse de forma formal. FitExpert utiliza el modelo clásico Objeto-Atributo-Valor. En este esquema, el objeto central es el `Usuario`, cuyos atributos corresponden a propiedades medibles (`Peso`, `Objetivo`, `Lesiones`), los cuales adquieren valores específicos (`75 kg`, `pérdida_grasa`, `['lumbar']`). Esta estructura homogénea permite al motor de inferencia evaluar premisas lógicas de manera determinista y predecible.")

    add_title_header(doc, "15.2 El Ciclo de Encadenamiento hacia Adelante (Forward Chaining)", level=2)
    add_p(doc, "A diferencia de los sistemas que operan por encadenamiento hacia atrás (que parten de una hipótesis para buscar evidencia), FitExpert parte de los hechos comprobados y avanza deductivamente hacia las conclusiones:", bold_prefix="Ciclo Deductivo:")
    add_bullet(doc, "El usuario completa su perfil; las ecuaciones numéricas completan las variables metabólicas cuantitativas iniciales.", bold_prefix="1. Carga de Hechos:")
    add_bullet(doc, "El motor recorre de forma secuencial las 69 reglas declaradas en `knowledge_base.py`. Para cada regla, evalúa su función condicional (ej. `¿El objetivo es pérdida de grasa?` o `¿Presenta molestia lumbar?`).", bold_prefix="2. Cotejo de Premisas:")
    add_bullet(doc, "Si la premisa es verdadera, la regla se activa (FIRE). Su conclusión se anexa a la lista de prescripciones del perfil y su explicación didáctica se almacena en el vector explicativo.", bold_prefix="3. Disparo de Reglas:")
    add_bullet(doc, "Las conclusiones alimentan directamente a los módulos de nutrición y entrenamiento para filtrar alimentos y sustituir ejercicios lesivos.", bold_prefix="4. Aplicación Práctica:")

    # ═════════════════════════════════════════════════════════════════════════
    # CAPÍTULO 16: SEGURIDAD Y CONTROL DE ACCESO
    # ═════════════════════════════════════════════════════════════════════════
    add_title_header(doc, "16. Seguridad y Control de Acceso", level=1)
    add_p(doc, "La gestión de datos sobre la salud, medidas corporales y patologías osteoarticulares exige estándares rigurosos de seguridad y privacidad. FitExpert implementa una política de privacidad por diseño ('Privacy by Design'):")

    add_bullet(doc, "FitExpert no transmite un solo byte de información a servidores remotos, nubes públicas o servicios de telemetría de terceros. Todo el procesamiento matemático, la inferencia de reglas y el almacenamiento se ejecutan exclusivamente en la memoria local de la máquina del usuario.", bold_prefix="• Residencia Local Absoluta:")
    add_bullet(doc, "Las contraseñas de acceso nunca se almacenan en texto claro. El módulo `auth.py` aplica el estándar criptográfico SHA-256 para transformar la clave en una cadena hexadecimal irreversible de 64 caracteres antes de guardarla en `auth_db.json`.", bold_prefix="• Cifrado Unidireccional SHA-256:")
    add_bullet(doc, "Cada usuario registrado recibe un identificador universalmente único (UUID versión 4). Las sesiones históricas de peso y consultas se enlazan mediante dicho identificador, evitando colisiones o cruces accidentales de datos si dos usuarios comparten el mismo nombre en la máquina.", bold_prefix="• Aislamiento por Identificador Único:")
    add_bullet(doc, "Los formularios de entrada incorporan expresiones regulares y validadores que rechazan caracteres maliciosos, inyecciones de código o valores fisiológicamente absurdos (como pesos negativos o estaturas de cero centímetros).", bold_prefix="• Sanitización y Tipado Robusto:")

    doc.add_page_break()
