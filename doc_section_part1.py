"""
doc_section_part1.py
====================
Contenido y redacción formal para los Capítulos 1 al 6:
  1. Introducción
  2. Descripción General del Proyecto
  3. Antecedentes y Problema
  4. Justificación
  5. Objetivos (General y Específicos)
  6. Alcance del Proyecto
"""

import docx
from doc_builder_core import (
    add_title_header, add_p, add_bullet, add_callout, add_table_data,
    HEX_NAVY_DARK, HEX_BG_LIGHT
)


def build_chapters_1_to_6(doc: docx.Document):
    """Construye los capítulos 1 al 6 con redacción formal, profunda y rigurosa."""

    # ═════════════════════════════════════════════════════════════════════════
    # CAPÍTULO 1: INTRODUCCIÓN
    # ═════════════════════════════════════════════════════════════════════════
    add_title_header(doc, "1. Introducción", level=1)

    add_title_header(doc, "1.1 Contexto de Surgimiento y Motivación", level=2)
    add_p(doc, "En las últimas décadas, la humanidad ha experimentado transformaciones sociolaborales drásticas. La consolidación de la economía digital, la proliferación del trabajo sedentario frente a pantallas y la alteración de los patrones de descanso han derivado en una degradación progresiva de la salud metabólica de la población global. Frente a esta realidad, el deseo individual de adoptar estilos de vida activos y una nutrición equilibrada ha crecido de forma exponencial. Sin embargo, este anhelo se enfrenta de inmediato a un entorno saturado de información contradictoria, modas dietéticas extremas y rutinas de ejercicio estandarizadas que carecen de rigor científico.")

    add_p(doc, "En este contexto contemporáneo nace FitExpert (versión 2.0), una solución de software inteligente concebida como un puente definitivo entre el conocimiento científico formal de la dietética y el acondicionamiento físico, y las necesidades prácticas del ciudadano común. El proyecto surge motivado por la convicción de que la tecnología computacional avanzada no debe reservarse exclusivamente a ámbitos industriales o académicos abstractos, sino que debe ponerse al servicio del bienestar humano tangible, optimizando procesos de prescripción y previniendo activamente el deterioro articular y los desequilibrios metabólicos.")

    add_title_header(doc, "1.2 La Necesidad Social y Sanitaria", level=2)
    add_p(doc, "La Organización Mundial de la Salud (OMS) y diversas entidades sanitarias internacionales advierten de manera continua sobre los riesgos del sedentarismo y los desequilibrios en el balance calórico. No obstante, el acceso a profesionales certificados de la salud física y la dietética personalizada se encuentra gravemente limitado por factores económicos y geográficos. Una consulta privada continuada con un nutricionista clínico y un entrenador personal representa un desembolso mensual inasumible para la mayoría de las familias, jóvenes y estudiantes universitarios.")

    add_p(doc, "Como resultado de esta barrera económica, millones de personas acuden a motores de búsqueda, redes sociales o foros de internet, adoptando pautas genéricas concebidas para culturistas de élite o deportistas de alto rendimiento. Las consecuencias de esta desorientación masiva son alarmantes: lesiones articulares prematuras (hernias discales, desgaste patelofemoral, pinzamientos de hombro), pérdida severa de masa muscular magra por déficits calóricos descontrolados, síndrome de fatiga crónica y el inevitable abandono de la actividad física.")

    add_title_header(doc, "1.3 Propósito del Presente Informe", level=2)
    add_p(doc, "El objetivo primordial del presente informe es exponer y fundamentar el proyecto FitExpert en su totalidad, presentándolo no como un simple conjunto de archivos de código fuente, sino como un producto tecnológico y científico maduro, coherente y de alto impacto. A lo largo de las siguientes secciones, el lector descubrirá qué es el sistema, por qué fue desarrollado, qué principios matemáticos y de inteligencia artificial sustentan sus decisiones, cómo se utiliza en la práctica y cuál es el inmenso valor que aporta a usuarios individuales, entrenadores e instituciones evaluadoras.")

    add_callout(doc,
        "FitExpert es un Sistema Experto Basado en Conocimiento (SBC) perteneciente al paradigma de la Inteligencia Artificial Simbólica. A diferencia de las redes neuronales opacas, cada una de sus recomendaciones está estrictamente respaldada por reglas lógicas transparentes, fórmulas metabólicas científicas y un módulo de explicación que justifica cada conclusión en lenguaje natural.",
        title="PRINCIPIO FUNDACIONAL DEL PROYECTO"
    )

    # ═════════════════════════════════════════════════════════════════════════
    # CAPÍTULO 2: DESCRIPCIÓN GENERAL DEL PROYECTO
    # ═════════════════════════════════════════════════════════════════════════
    add_title_header(doc, "2. Descripción General del Proyecto", level=1)

    add_title_header(doc, "2.1 Definición Conceptual: ¿Qué es FitExpert?", level=2)
    add_p(doc, "FitExpert es un sistema computacional experto autónomo diseñado para emular la capacidad de razonamiento deductivo, diagnóstico antropométrico y prescripción personalizada de un equipo interdisciplinario conformado por un nutricionista clínico y un entrenador biomecánico certificado. El sistema pertenece a la disciplina de los Sistemas Basados en Conocimiento (Knowledge-Based Systems) dentro de la Inteligencia Artificial Simbólica.")

    add_p(doc, "En términos funcionales, FitExpert opera recibiendo un vector completo de hechos declarados por el usuario —que incluye datos biométricos (edad, sexo, peso, estatura, porcentaje graso), metas corporales (pérdida de grasa, hipertrofia, definición, recomposición, mantenimiento), nivel de actividad cotidiana, lugar de entrenamiento disponible (casa o gimnasio), inventario de equipo, restricciones articulares previas (rodilla, zona lumbar, hombro), patrones dietéticos (omnívoro, vegetariano, vegano, pescetariano) e intolerancias alimentarias (lactosa, gluten, nueces, soya, huevo)— y procesando esta información mediante un motor de inferencia determinista por encadenamiento hacia adelante (Forward Chaining).")

    add_title_header(doc, "2.2 Finalidad Primordial y Entorno de Aplicación", level=2)
    add_p(doc, "La finalidad principal de FitExpert es proporcionar una prescripción integral, científicamente validada y biomecánicamente segura, asegurando que cada caloría asignada y cada ejercicio sugerido respeten escrupulosamente las particularidades biológicas y las limitaciones físicas de la persona. El sistema no improvisa ni adivina: ejecuta identidades metabólicas reconocidas mundialmente (fórmulas de Harris-Benedict revisada por Mifflin-St Jeor) y evalúa una base de conocimiento declarativa estructurada en 69 reglas de producción bajo el modelo Objeto-Atributo-Valor (OAV).")

    add_p(doc, "FitExpert está concebido para operar en diversos contextos de uso:", bold_prefix="Ámbitos de Despliegue:")
    add_bullet(doc, "Uso individual doméstico y gimnasio: Para personas que buscan transformar su composición corporal con seguridad absoluta sin incurrir en costes mensuales inasumibles.", bold_prefix="• Sector Personal:")
    add_bullet(doc, "Herramienta de prototipado rápido para profesionales: Para nutricionistas, preparadores físicos y entrenadores personales que requieren automatizar el cálculo basal y generar borradores dietéticos iniciales.", bold_prefix="• Sector Profesional:")
    add_bullet(doc, "Plataforma académica y de auditoría: Para universidades, centros de investigación y evaluadores de software que estudian la aplicación práctica de la Inteligencia Artificial Simbólica y el aseguramiento de la calidad de software bajo la norma ISO/IEC 25010.", bold_prefix="• Sector Académico:")

    add_title_header(doc, "2.3 Actividades Principales que Facilita el Sistema", level=2)
    add_p(doc, "A través de su entorno interactivo, el sistema permite realizar de forma ágil y coordinada las siguientes operaciones esenciales:")
    add_bullet(doc, "Cálculo instantáneo del Índice de Masa Corporal (IMC) con estratificación precisa según los baremos clínicos de la Organización Mundial de la Salud (OMS).", bold_prefix="1. Diagnóstico Antropométrico:")
    add_bullet(doc, "Estimación del gasto calórico basal (TMB), del gasto energético diario total (TDEE) y del balance calórico diana ajustado a la meta biológica del usuario.", bold_prefix="2. Calibración Metabólica Cuantitativa:")
    add_bullet(doc, "Desglose estricto de macronutrientes (gramos de proteínas, carbohidratos y lípidos diarios) optimizado según la meta (hipertrofia, definición, recomposición, mantenimiento).", bold_prefix="3. Partición de Macronutrientes:")
    add_bullet(doc, "Confección automatizada de menús diarios (desayuno, almuerzo, cena y colaciones) con filtrado en tiempo real que excluye alérgenos e ingredientes contraindicados.", bold_prefix="4. Prescripción Nutricional Dinámica:")
    add_bullet(doc, "Diseño de microciclos semanales estructurados de 3 a 6 días (Full Body, Push-Pull-Legs 4 días, PPL Doble 6 días, Movilidad Especializada o Rutina Doméstica Avanzada), respetando descansos musculares de 48 a 72 horas.", bold_prefix="5. Programación Biomecánica Semanal:")
    add_bullet(doc, "Sustitución algorítmica automática de movimientos que involucren riesgo lesivo para la zona lumbar, rodillas u hombros.", bold_prefix="6. Blindaje Articular:")
    add_bullet(doc, "Inspección forense de las reglas disparadas por el motor de inferencia con justificación en lenguaje natural de cada recomendación.", bold_prefix="7. Auditoría Explicativa:")
    add_bullet(doc, "Almacenamiento persistente, trazabilidad temporal mediante gráficos de evolución de peso y exportación formal de expedientes en formato PDF de alta resolución.", bold_prefix="8. Historial y Salida Documental:")

    # ═════════════════════════════════════════════════════════════════════════
    # CAPÍTULO 3: ANTECEDENTES Y PROBLEMA
    # ═════════════════════════════════════════════════════════════════════════
    add_title_header(doc, "3. Antecedentes y Problema", level=1)

    add_title_header(doc, "3.1 La Crisis del Modelo Tradicional de Asesoría", level=2)
    add_p(doc, "Históricamente, cualquier persona interesada en mejorar su condición física o corregir sus hábitos alimentarios dependía de dos caminos excluyentes: contratar los servicios profesionales de un médico nutricionista y un entrenador certificado, o emprender un proceso empírico de ensayo y error basado en libros, revistas o consejos informales. Si bien el acompañamiento profesional representa el estándar de oro, su alto coste financiero y la falta de disponibilidad de especialistas cualificados en todas las regiones geográficas provocan que más del 80% de la población quede desatendida.")

    add_title_header(doc, "3.2 La Trampa de los Planes Masivos y Despersonalizados", level=2)
    add_p(doc, "La masificación de internet y las plataformas digitales intentó democratizar el acceso a la información mediante aplicaciones móviles comerciales y canales de contenido físico. No obstante, este fenómeno introdujo una problemática aún más grave: la estandarización despersonalizada ('one-size-fits-all'). Las aplicaciones comunes y los generadores de dietas automatizados tratan a los usuarios como valores idénticos de una hoja de cálculo, ignorando parámetros críticos como lesiones previas, alergias alimentarias o la disponibilidad de equipo.")

    add_title_header(doc, "3.3 La Epidemia Silenciosa de Lesiones Articulares", level=2)
    add_p(doc, "El mayor peligro de la prescripción física automatizada convencional reside en la ignorancia biomecánica. Una persona que presenta antecedentes de hernia discal L4-L5 o protusión lumbar no puede, bajo ninguna circunstancia médica, ser sometida a ejercicios que introduzcan sobrecargas axiales compresivas severas, tales como sentadillas libres con barra sobre hombros o pesos muertos pesados. Sin embargo, las aplicaciones comerciales genéricas recomiendan estos movimientos de manera indiscriminada, provocando exacerbación de cuadros inflamatorios, lumbalgias agudas e incapacidad funcional.")

    add_p(doc, "De igual manera ocurre con las patologías de rodilla (lesiones de ligamento cruzado anterior, condromalacia o meniscopatías) y hombro (pinzamiento subacromial o desgarros del manguito rotador). La ejecución repetitiva de prensas militares trasnuca o flexiones profundas en personas con molestias articulares previas termina invariablemente en salas de urgencias o tratamientos quirúrgicos.")

    add_title_header(doc, "3.4 Restricciones Alergénicas Ignoradas y Efecto Rebote", level=2)
    add_p(doc, "En el plano nutricional, las dietas de choque que imponen déficits calóricos violentos (superiores a 1,000 kcal diarias) provocan una respuesta fisiológica de alarma en el organismo: reducción drástica de la tasa metabólica basal (termogénesis adaptativa), degradación proteica muscular y una intensa ansiedad psicológica que desemboca en atracones y en el temido 'efecto rebote'.")

    add_p(doc, "Asimismo, la omisión algorítmica de alergias severas (como la intolerancia a la lactosa, la enfermedad celíaca o la alergia a los frutos secos) en los recetarios automatizados puede provocar graves episodios anafilácticos o inflamaciones gastrointestinales crónicas que destruyen la permeabilidad intestinal del usuario. FitExpert surge como la respuesta técnica y científica rigurosa que erradica definitivamente estas deficiencias.")

    # ═════════════════════════════════════════════════════════════════════════
    # CAPÍTULO 4: JUSTIFICACIÓN
    # ═════════════════════════════════════════════════════════════════════════
    add_title_header(doc, "4. Justificación", level=1)

    add_title_header(doc, "4.1 Relevancia e Impacto Social de la Solución", level=2)
    add_p(doc, "El desarrollo de FitExpert se justifica plenamente en la necesidad urgente de democratizar la salud preventiva y el rendimiento físico fundamentado en evidencia científica. Al proporcionar una herramienta gratuita, local, autónoma y accesible, el sistema elimina las barreras económicas que históricamente han marginado a amplios sectores sociales del asesoramiento de calidad.")

    add_title_header(doc, "4.2 Fundamento Científico y Seguridad Biomecánica", level=2)
    add_p(doc, "Frente a las tendencias pseudocientíficas, FitExpert fundamenta toda su arquitectura en consensos médicos y deportivos consolidados internacionalmente:", bold_prefix="Bases de Evidencia:")
    add_bullet(doc, "La cuantificación del gasto energético basal no recurre a estimaciones arbitrarias, sino a la fórmula revisada de Harris-Benedict (Mifflin-St Jeor), validada como la más exacta en sujetos sanos.", bold_prefix="• Fórmulas Metabólicas Validadas:")
    add_bullet(doc, "Las calorías diana se calibran dentro de márgenes sostenibles: un déficit moderado de -500 kcal/día para pérdida de grasa (equivalente a ~0.5 kg de tejido adiposo por semana) y un superávit controlado de +400 kcal/día para hipertrofia, evitando la ganancia innecesaria de tejido graso.", bold_prefix="• Progresión Fisiológica Segura:")
    add_bullet(doc, "Cada ejercicio propuesto pasa por una matriz de filtros que verifica contraindicaciones articulares cruzadas. Si un usuario reporta lesión lumbar, la sentadilla con barra es excluida automáticamente y sustituida por prensa de piernas a 45 grados con apoyo lumbar guiado.", bold_prefix="• Blindaje Articular Determinista:")

    add_title_header(doc, "4.3 Democratización del Acceso y Transparencia Cognitiva", level=2)
    add_p(doc, "Una de las mayores justificaciones de FitExpert frente a los modelos modernos de Inteligencia Artificial basados en redes neuronales profundas (Deep Learning o LLMs) es la explicabilidad total (Explainable AI / XAI). En los sistemas de 'caja negra', es imposible auditar matemáticamente por qué el modelo recomendó un régimen determinado. En FitExpert, el usuario y el evaluador pueden examinar cada deducción realizada en el Módulo de Explicación, comprendiendo la causa biomecánica o metabólica de su plan, lo que fomenta una verdadera alfabetización nutricional.")

    # ═════════════════════════════════════════════════════════════════════════
    # CAPÍTULO 5: OBJETIVOS
    # ═════════════════════════════════════════════════════════════════════════
    add_title_header(doc, "5. Objetivos", level=1)

    add_title_header(doc, "5.1 Objetivo General", level=2)
    add_p(doc, "Diseñar, formalizar, desarrollar y validar un Sistema Experto integral basado en Inteligencia Artificial Simbólica y reglas de producción, capaz de evaluar perfiles humanos heterogéneos para generar prescripciones nutricionales personalizadas y microciclos de acondicionamiento físico semanales, garantizando la total seguridad biomecánica de las articulaciones, la exclusión estricta de alérgenos y la justificación explicativa en lenguaje natural de todas las inferencias realizadas.")

    add_title_header(doc, "5.2 Objetivos Específicos", level=2)
    add_p(doc, "Para asegurar la consecución exitosa del objetivo general, el proyecto se articuló en torno a ocho objetivos específicos exhaustivos y medibles:")

    add_bullet(doc, "Formalizar el conocimiento empírico y científico de la nutrición clínica y la biomecánica en un modelo de representación ontológico Objeto-Atributo-Valor (OAV), consolidando una Base de Conocimiento declarativa con 69 reglas de producción IF-THEN estructuradas.", bold_prefix="1. Formalización Ontológica:")
    add_bullet(doc, "Implementar un Motor de Inferencia determinista por encadenamiento hacia adelante (Forward Chaining) libre de sesgos y con tiempo de ejecución sub-segundo en entornos de cómputo estándar.", bold_prefix="2. Motor de Inferencia Determinista:")
    add_bullet(doc, "Integrar algoritmos matemáticos exactos para el cálculo del Índice de Masa Corporal (IMC), Tasa Metabólica Basal (TMB), Gasto Energético Total Diario (TDEE) y calibración calórica y de macronutrientes según el objetivo biológico.", bold_prefix="3. Calibración Metabólica Cuantitativa:")
    add_bullet(doc, "Desarrollar un catálogo culinario estructurado con filtrado algorítmico reactivo que elimine de forma rigurosa alimentos que contengan alérgenos (lactosa, gluten, frutos secos, soya, huevo) y adapte las fuentes proteicas a patrones omnívoros, vegetarianos, veganos o pescetarianos.", bold_prefix="4. Prescriptor Nutricional Inteligente:")
    add_bullet(doc, "Construir una biblioteca biomecánica de ejercicios con matrices de exclusión por lesión articular (rodilla, lumbar, hombro), edad crítica (<16 años, >70 años) u obesidad severa (IMC ≥ 40), ensamblando microciclos semanales distribuidos de 3 a 6 días.", bold_prefix="5. Programación Biomecánica y Blindaje:")
    add_bullet(doc, "Diseñar e implementar un Módulo de Explicabilidad que provea justificaciones didácticas en lenguaje natural para cada regla activada, permitiendo al usuario auditar el razonamiento de la máquina.", bold_prefix="6. Transparencia y Módulo de Explicación:")
    add_bullet(doc, "Proveer una arquitectura de interacción tri-modal e independiente que ofrezca acceso mediante Línea de Comandos (Rich CLI), Tablero Web (Streamlit) y Aplicación Nativa de Escritorio Premium (CustomTkinter) en modo oscuro.", bold_prefix="7. Arquitectura Multi-Interfaz:")
    add_bullet(doc, "Garantizar la soberanía y privacidad de los datos mediante almacenamiento local transaccional JSON, autenticación criptográfica con SHA-256, tablero de evolución histórica ponderal y generación de expedientes imprimibles en formato PDF de alta resolución.", bold_prefix="8. Persistencia, Seguridad y Reportes PDF:")

    # ═════════════════════════════════════════════════════════════════════════
    # CAPÍTULO 6: ALCANCE DEL PROYECTO
    # ═════════════════════════════════════════════════════════════════════════
    add_title_header(doc, "6. Alcance del Proyecto", level=1)

    add_title_header(doc, "6.1 Cobertura Funcional y Procesos Integrados", level=2)
    add_p(doc, "El alcance funcional de FitExpert abarca de manera integral los procesos que intervienen en la orientación preventiva del acondicionamiento físico y la nutrición:", bold_prefix="Procesos Contemplados:")
    add_bullet(doc, "Captura y validación de hasta 15 variables de entrada entre biométricas, hábitos de estilo de vida, antecedentes osteoarticulares y recursos espaciales.", bold_prefix="• Entrada de Datos:")
    add_bullet(doc, "Evaluación de 5 metas corporales distintas: pérdida de grasa, aumento de masa muscular (hipertrofia), definición muscular, recomposición corporal y mantenimiento.", bold_prefix="• Objetivos Biológicos:")
    add_bullet(doc, "Resolución de microciclos semanales completos para entrenamientos en gimnasio comercial o en el hogar con equipamiento mínimo (bandas, mancuernas, barra de dominadas o peso corporal puro).", bold_prefix="• Contextos Espaciales:")
    add_bullet(doc, "Manejo de patrones culinarios omnívoros, vegetarianos, veganos y pescetarianos, con frecuencias alimentarias configurables de 3, 4 o 5 comidas diarias.", bold_prefix="• Flexibilidad Dietética:")
    add_bullet(doc, "Blindaje especializado para menores de 16 años (protección de placas epifisarias) y mayores de 70 años (prevención de sarcopenia y exclusión de impactos pliométricos).", bold_prefix="• Rangos Etarios Extremos:")

    add_title_header(doc, "6.2 Límites Operativos y Fronteras Médicas del Sistema", level=2)
    add_p(doc, "Con el objetivo de garantizar una conducta ética y responsable en el ámbito de la salud, FitExpert delimita de forma estricta sus fronteras operativas. El sistema estipula con absoluta claridad las áreas que NO forman parte de su alcance:")

    add_bullet(doc, "FitExpert NO diagnostica ni trata patologías médicas graves como diabetes mellitus tipo 1, insuficiencia renal crónica, afecciones cardiovasculares congénitas, dislipidemias severas o enfermedades oncológicas. En presencia de estas condiciones, el sistema emite directivas explícitas de remisión inmediata a supervisión médica hospitalaria.", bold_prefix="1. Exclusión de Diagnóstico Clínico:")
    add_bullet(doc, "El sistema no prescribe fármacos, sustancias ergogénicas dopantes ni terapias hormonales anabólicas. Toda la suplementación sugerida se limita a la ingesta dietética balanceada y recomendaciones de hidratación.", bold_prefix="2. Exclusión Farmacológica:")
    add_bullet(doc, "FitExpert no sustituye la terapia psicológica ni psiquiátrica requerida para el abordaje de trastornos de la conducta alimentaria (anorexia, bulimia, vigorexia).", bold_prefix="3. Exclusión Psicoterapéutica:")
    add_bullet(doc, "La intervención física ante roturas ligamentarias agudas o fases postquirúrgicas inmediatas debe ser conducida por un fisioterapeuta traumatológico presencial; el sistema se enfoca en prevención y adaptación ante molestias crónicas leves o recuperadas.", bold_prefix="4. Exclusión de Fisioterapia Postquirúrgica:")

    doc.add_page_break()
