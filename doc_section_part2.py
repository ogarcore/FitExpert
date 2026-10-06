"""
doc_section_part2.py
====================
Contenido y redacción formal para los Capítulos 7 al 10:
  7. Usuarios del Sistema
  8. Funcionamiento General (con diagrama de flujo)
  9. Principales Funcionalidades (con las 6 preguntas para cada una de las 10 funcionalidades)
  10. Recorrido del Usuario (Escenarios reales)
"""

import os
import docx
from doc_builder_core import (
    add_title_header, add_p, add_bullet, add_callout, add_table_data,
    add_figure, HEX_NAVY_DARK, HEX_BG_LIGHT
)


def build_chapters_7_to_10(doc: docx.Document):
    """Construye los capítulos 7 al 10 con máxima profundidad funcional."""

    # ═════════════════════════════════════════════════════════════════════════
    # CAPÍTULO 7: USUARIOS DEL SISTEMA
    # ═════════════════════════════════════════════════════════════════════════
    add_title_header(doc, "7. Usuarios del Sistema", level=1)
    add_p(doc, "FitExpert ha sido diseñado con un enfoque inclusivo y flexible, adaptándose con precisión a diversos perfiles biológicos, niveles de destreza atlética y contextos de aplicación profesional. A continuación se caracterizan los cuatro grupos principales de usuarios contemplados en el diseño del sistema:")

    add_title_header(doc, "7.1 Usuarios Finales y Atletas (Principiantes a Avanzados)", level=2)
    add_p(doc, "Este segmento constituye la base de usuarios más amplia del sistema. Incluye a ciudadanos comunes, jóvenes, trabajadores y entusiastas del fitness que buscan transformar su estilo de vida o maximizar su rendimiento:", bold_prefix="Perfil General:")
    add_bullet(doc, "Individuos sin experiencia previa en entrenamiento de fuerza. Requieren rutinas de iniciación guiadas de 3 días (Full Body o circuitos corporales) que enfaticen la técnica, la adaptación neural y eviten el agotamiento prematuro.", bold_prefix="• Principiantes:")
    add_bullet(doc, "Personas con 6 meses a 2 años de entrenamiento constante. Se benefician de esquemas de división muscular de 4 días (Push-Pull-Legs) que incrementan el volumen de trabajo por grupo muscular y optimizan la hipertrofia.", bold_prefix="• Intermedios:")
    add_bullet(doc, "Atletas con más de 2 años de levantamiento sistemático. Requieren microciclos de alta frecuencia y volumen (PPL doble de 5 a 6 días) con periodización avanzada para romper mesetas de crecimiento muscular y definición estética.", bold_prefix="• Avanzados:")

    add_title_header(doc, "7.2 Poblaciones Especiales y Perfiles Clínicos Preventivos", level=2)
    add_p(doc, "A diferencia de las herramientas estándar del mercado, FitExpert contempla salvaguardas explícitas para grupos poblacionales con requerimientos fisiológicos sensibles:", bold_prefix="Grupos Sensibles:")
    add_bullet(doc, "Personas que presentan antecedentes de hernias discales, condromalacia rotuliana o pinzamiento subacromial. El sistema actúa como un escudo biomecánico, excluyendo ejercicios axiales o sobrecargas articulares directas y ofreciendo variantes cerradas seguras.", bold_prefix="• Personas con Lesiones Osteoarticulares:")
    add_bullet(doc, "Adultos de 50 a 70 años y mayores de 70 años. En ellos, el sistema elimina la pliometría y los saltos de impacto, priorizando el entrenamiento de fuerza suave, la estabilidad unipodal, el equilibrio y la preservación de la masa muscular para combatir activamente la sarcopenia.", bold_prefix="• Adultos Mayores y Tercera Edad:")
    add_bullet(doc, "Jóvenes cuyas placas de crecimiento óseo (epífisis) aún no se han cerrado. El sistema prohíbe levantamientos axiales pesados y orienta la actividad hacia la coordinación motriz, la movilidad y la calistenia ligera.", bold_prefix="• Jóvenes Menores de 16 Años:")
    add_bullet(doc, "Personas con un índice de masa corporal superior a 40 kg/m². En estos casos, las fuerzas de impacto sobre los meniscos pueden cuadruplicar el peso corporal; por ende, el sistema suprime los saltos y orienta el entrenamiento hacia máquinas guiadas y cardio de bajo impacto articular.", bold_prefix="• Individuos con Obesidad Grado III:")

    add_title_header(doc, "7.3 Profesionales de la Salud y Entrenadores Personales", level=2)
    add_p(doc, "Para dietistas, preparadores físicos y entrenadores personales certificados, FitExpert opera como un potente copiloto clínico y de prototipado rápido. Permite a los profesionales ahorrar tiempo valioso en la fase inicial de anamnesis calculando al instante el balance calórico exacto, la distribución de macronutrientes y generando un borrador integral de rutina y menú en menos de 5 segundos. Posteriormente, el profesional puede ajustar o enriquecer el expediente antes de entregarlo al cliente.")

    add_title_header(doc, "7.4 Evaluadores Técnicos y Comunidad Académica", level=2)
    add_p(doc, "Para la comunidad de investigadores, profesores de ciencias de la computación y auditores de software, FitExpert representa un caso de estudio modélico sobre la viabilidad, confiabilidad y rigor de la Inteligencia Artificial Simbólica aplicada al sector salud, demostrando que un motor de reglas determinista supera a los modelos generativos opacos en entornos donde el error puede comprometer la integridad articular de una persona.")

    # ═════════════════════════════════════════════════════════════════════════
    # CAPÍTULO 8: FUNCIONAMIENTO GENERAL
    # ═════════════════════════════════════════════════════════════════════════
    add_title_header(doc, "8. Funcionamiento General", level=1)
    add_p(doc, "El funcionamiento de FitExpert se caracteriza por su fluidez, rigor matemático y determinismo lógico. Desde la perspectiva de una persona que utiliza el software, la experiencia transcurre a lo largo de un proceso de circuito cerrado estructurado en fases claramente definidas:")

    add_p(doc, "1. Fase de Acceso y Control de Identidad:", bold_prefix="Fase 1 · Autenticación:")
    add_p(doc, "El usuario inicia la aplicación (mediante la versión de escritorio de alto rendimiento, el panel web o la consola de comandos). Introduce sus credenciales personales. Si es un nuevo usuario, crea su cuenta de forma instantánea. El sistema procesa la contraseña mediante una función hash criptográfica SHA-256 y verifica la unicidad del nombre de usuario antes de conceder acceso al entorno personalizado.")

    add_p(doc, "2. Fase de Exploración del Perfil y Consulta Histórica:", bold_prefix="Fase 2 · Panel de Control:")
    add_p(doc, "Al ingresar, el usuario accede a su tablero principal ('Mi Perfil'). Si ya cuenta con evaluaciones previas, el sistema carga de inmediato sus indicadores corporales clave, su última meta registrada y una gráfica dinámica con la tendencia temporal de su peso corporal, calculando el diferencial de masa y calorías desde su primera sesión.")

    add_p(doc, "3. Fase de Captura de Datos Antropométricos y Hábitos:", bold_prefix="Fase 3 · Evaluación Integral:")
    add_p(doc, "El usuario selecciona la opción 'Nueva Evaluación'. El sistema despliega un formulario ergonómico estructurado en cuatro bloques temáticos independientes:")
    add_bullet(doc, "Edad, sexo biológico, peso corporal actual (kg), estatura (cm) y porcentaje de grasa corporal estimado (opcional).", bold_prefix="• Bloque Físico:")
    add_bullet(doc, "Meta biológica (pérdida de grasa, hipertrofia, definición, recomposición, mantenimiento), nivel de actividad física diaria y experiencia de entrenamiento.", bold_prefix="• Bloque de Metas:")
    add_bullet(doc, "Lugar de entrenamiento (casa o gimnasio), equipo disponible en el hogar (mancuernas, bandas, barras, kettlebells) y antecedentes de lesiones (rodilla, lumbar, hombro).", bold_prefix="• Bloque Biomecánico:")
    add_bullet(doc, "Tipo de dieta (omnívora, vegetariana, vegana, pescetariana), frecuencia deseada de comidas (3, 4 o 5 al día) y presencia de alergias o intolerancias.", bold_prefix="• Bloque Nutricional:")

    add_p(doc, "4. Fase de Inferencia y Ensamblado Algorítmico:", bold_prefix="Fase 4 · Motor Cognitivo:")
    add_p(doc, "Al pulsar el botón 'Generar Plan Personalizado', el núcleo de inteligencia artificial toma el control en milisegundos: calcula las identidades basales (IMC, TMB, TDEE, balance diana), evalúa las 69 reglas de producción de la base de conocimiento mediante encadenamiento hacia adelante, activa las conclusiones aplicables, ensambla el menú diario excluyendo alérgenos y construye el microciclo semanal seleccionando ejercicios biomecánicamente seguros.")

    add_p(doc, "5. Fase de Presentación de Resultados y Explicabilidad:", bold_prefix="Fase 5 · Visualización y Auditoría:")
    add_p(doc, "El sistema presenta de inmediato los resultados distribuidos en pestañas temáticas de alta legibilidad: tarjetas métricas de calorías y macros, tabla nutricional con comidas desglosadas e hidratación, y microciclo semanal de lunes a domingo. Asimismo, el usuario puede abrir la ventana de 'Lógica de IA' para auditar exactamente por qué el sistema tomó cada una de las decisiones.")

    add_p(doc, "6. Fase de Trazabilidad y Exportación de Documentos:", bold_prefix="Fase 6 · Persistencia y PDF:")
    add_p(doc, "La evaluación queda registrada automáticamente en la base de datos local JSON, actualizando las curvas de progreso. Con un solo clic en 'Descargar PDF', el usuario puede exportar un expediente clínico completo en formato PDF listo para imprimir o compartir.")

    # Inserción de la Figura de Flujo
    img_flujo = os.path.join("doc_assets", "flujo_usuario.png")
    add_figure(doc, img_flujo, "Figura 1. Recorrido funcional del usuario y ciclo operativo integral en FitExpert.", width_in=6.2)

    # ═════════════════════════════════════════════════════════════════════════
    # CAPÍTULO 9: PRINCIPALES FUNCIONALIDADES
    # ═════════════════════════════════════════════════════════════════════════
    add_title_header(doc, "9. Principales Funcionalidades", level=1)
    add_p(doc, "A continuación se realiza un análisis exhaustivo y en profundidad de las diez funcionalidades centrales que componen el sistema FitExpert. Cada funcionalidad es analizada bajo seis dimensiones operativas obligatorias para garantizar una comprensión técnica y práctica absoluta:")

    # FUNCIONALIDAD 1
    add_title_header(doc, "9.1 Control de Identidad y Autenticación Criptográfica Local", level=2)
    add_p(doc, "Un subsistema de seguridad y gestión de sesiones que permite el registro y la validación de usuarios mediante almacenamiento local semiestructurado.", bold_prefix="¿Qué es?")
    add_p(doc, "Garantiza el aislamiento estricto de la información biológica e histórica de cada usuario, impidiendo que personas no autorizadas accedan a los expedientes de otros miembros.", bold_prefix="¿Para qué sirve?")
    add_p(doc, "Cuando el usuario introduce su contraseña, el sistema genera de forma unidireccional un hash mediante el algoritmo SHA-256. Dicho hash se compara con la base de datos `auth_db.json`. Si las firmas coinciden, se emite un identificador global único (UUIDv4) y se persiste el estado en `local_session.json`.", bold_prefix="¿Cómo funciona?")
    add_p(doc, "Registrar nuevas cuentas con validación de nombres de usuario en tiempo real (mínimo 3 caracteres alfanuméricos), iniciar sesión, alternar la visibilidad de la contraseña ('Mostrar/Ocultar') y cerrar sesión de manera segura.", bold_prefix="¿Qué puede hacer el usuario?")
    add_p(doc, "Acceso seguro a un entorno personalizado donde su nombre, historial de pesajes y configuraciones previas se cargan automáticamente sin necesidad de reintroducirlos.", bold_prefix="¿Qué resultado obtiene?")
    add_p(doc, "Proporciona una barrera de privacidad impenetrable sin depender de servicios en la nube, garantizando que los datos biométricos sensibles permanezcan exclusivamente bajo control del usuario.", bold_prefix="¿Por qué es importante?")

    # FUNCIONALIDAD 2
    add_title_header(doc, "9.2 Diagnóstico Antropométrico y Balance Energético Automatizado", level=2)
    add_p(doc, "Un módulo de cálculo fisiológico avanzado que determina la composición corporal y las demandas térmicas del metabolismo humano.", bold_prefix="¿Qué es?")
    add_p(doc, "Establece con precisión matemática cuántas calorías gasta el cuerpo en reposo y en movimiento, fijando la meta calórica exacta requerida para alcanzar el objetivo físico sin riesgo de desnutrición.", bold_prefix="¿Para qué sirve?")
    add_p(doc, "El sistema procesa la estatura y el peso para obtener el IMC (`peso / altura²`). Seguidamente resuelve la TMB mediante la fórmula de Harris-Benedict revisada por Mifflin-St Jeor, considerando las diferencias metabólicas hormonales entre hombres (`+5`) y mujeres (`-161`). Luego multiplica por el factor de actividad (de 1.2 a 1.9) para derivar el TDEE y aplica el ajuste diana (-500 kcal para pérdida, +400 kcal para ganancia).", bold_prefix="¿Cómo funciona?")
    add_p(doc, "Introducir o actualizar sus medidas corporales (edad, sexo, peso, estatura, porcentaje graso) y seleccionar su nivel de actividad cotidiana.", bold_prefix="¿Qué puede hacer el usuario?")
    add_p(doc, "Visualización inmediata de tarjetas métricas con su IMC clasificado por la OMS (bajo peso, normal, sobrepeso, obesidad I, II o III), su TMB, su TDEE y sus calorías objetivo diarias.", bold_prefix="¿Qué resultado obtiene?")
    add_p(doc, "Elimina las conjeturas arbitrarias. Permite al usuario comprender por primera vez el funcionamiento cuantitativo de su propio metabolismo, fundamentando su transformación en leyes físicas inalterables.", bold_prefix="¿Por qué es importante?")

    # FUNCIONALIDAD 3
    add_title_header(doc, "9.3 Prescripción Nutricional Dinámica y Desglose de Macronutrientes", level=2)
    add_p(doc, "Un motor de síntesis dietética que traduce las calorías objetivo en gramos específicos de macronutrientes y confecciona una propuesta diaria de ingestas alimentarias.", bold_prefix="¿Qué es?")
    add_p(doc, "Asegura que el déficit o superávit calórico vaya acompañado de una proporción óptima de nutrientes para preservar el tejido muscular magro, modular las hormonas lipídicas y proporcionar energía glucémica.", bold_prefix="¿Para qué sirve?")
    add_p(doc, "El sistema divide la meta calórica en porcentajes diana (ej. 35% proteína, 40% carbohidrato, 25% grasa en recomposición). Convierte estas calorías a gramos dividiendo entre su densidad energética (4 kcal/g para proteínas y carbohidratos, 9 kcal/g para grasas). Posteriormente consulta el catálogo culinario y selecciona opciones variadas de desayuno, almuerzo, cena y colaciones acordes a la frecuencia seleccionada.", bold_prefix="¿Cómo funciona?")
    add_p(doc, "Definir su preferencia dietética (omnívora, vegetariana, vegana, pescetariana) y graduar la frecuencia diaria entre 3, 4 o 5 ingestas.", bold_prefix="¿Qué puede hacer el usuario?")
    add_p(doc, "Un plan nutricional diario completo con porciones balanceadas, desglose de macronutrientes en gramos y pautas precisas de hidratación en litros diarios.", bold_prefix="¿Qué resultado obtiene?")
    add_p(doc, "Convierte números abstractos en comida real, ofreciendo variedad y practicidad que facilitan una adherencia superior al 90% a largo plazo.", bold_prefix="¿Por qué es importante?")

    # FUNCIONALIDAD 4
    add_title_header(doc, "9.4 Sistema de Filtrado de Alérgenos e Intolerancias Alimentarias", level=2)
    add_p(doc, "Un algoritmo de depuración culinaria que analiza cada ingrediente propuesto contra una matriz de sustancias alérgenas declaradas por el usuario.", bold_prefix="¿Qué es?")
    add_p(doc, "Proteger la integridad gastrointestinal y la vida del usuario, garantizando que ninguna sugerencia contenga alimentos capaces de inducir reacciones alérgicas o inflamación celular.", bold_prefix="¿Para qué sirve?")
    add_p(doc, "El sistema mantiene un diccionario de palabras clave que rastrea derivados lácteos (leche, queso, yogur, kéfir, caseína), gluten (trigo, cebada, centeno, avena convencional), frutos secos, soya y huevo. Si el usuario marca una intolerancia, cualquier opción que contenga dichas palabras clave es purgada y reemplazada por alternativas hipoalergénicas certificadas.", bold_prefix="¿Cómo funciona?")
    add_p(doc, "Marcar una o múltiples casillas de alergias e intolerancias durante el proceso de evaluación.", bold_prefix="¿Qué puede hacer el usuario?")
    add_p(doc, "Un menú diario completamente libre de alérgenos, con sustitutos nutritivos (bebidas vegetales fortificadas, harinas de arroz o maíz, semillas de chía o cáñamo).", bold_prefix="¿Qué resultado obtiene?")
    add_p(doc, "Aporta tranquilidad y seguridad clínica total, convirtiendo a FitExpert en una herramienta confiable para personas celíacas o con intolerancias graves.", bold_prefix="¿Por qué es importante?")

    # FUNCIONALIDAD 5
    add_title_header(doc, "9.5 Planificador Semanal de Microciclos de Entrenamiento", level=2)
    add_p(doc, "Un generador inteligente de cronogramas de acondicionamiento físico distribuidos de lunes a domingo, optimizado para casa o gimnasio.", bold_prefix="¿Qué es?")
    add_p(doc, "Estructurar la distribución temporal de los estímulos mecánicos y los descansos biológicos necesarios para desencadenar adaptaciones musculares y cardiovasculares.", bold_prefix="¿Para qué sirve?")
    add_p(doc, "El módulo analiza la experiencia y el lugar seleccionado. Si es principiante, ensambla un Full Body de 3 días con 48h de recuperación neuromuscular entre sesiones; si es intermedio, asigna un Push-Pull-Legs de 4 días; si es avanzado, estructura un PPL doble de 6 días. Para entrenamientos en el hogar, selecciona variantes ajustadas estrictamente al equipo disponible.", bold_prefix="¿Cómo funciona?")
    add_p(doc, "Indicar su nivel de destreza atlética, seleccionar el entorno de entrenamiento y detallar con qué equipamiento cuenta en casa.", bold_prefix="¿Qué puede hacer el usuario?")
    add_p(doc, "Una rutina detallada día a día con nombres de ejercicios, series, repeticiones diana, tiempos de pausa entre series y sesiones de descanso activo o cardio.", bold_prefix="¿Qué resultado obtiene?")
    add_p(doc, "Evita el sobreentrenamiento y el estancamiento, asegurando que cada sesión tenga un propósito biomecánico claro y un balance de volumen semanal óptimo.", bold_prefix="¿Por qué es importante?")

    # FUNCIONALIDAD 6
    add_title_header(doc, "9.6 Blindaje Biomecánico y Sustitución por Lesiones Articulares", level=2)
    add_p(doc, "Un subsistema de auditoría de seguridad que analiza las contraindicaciones físicas de cada ejercicio y aplica sustituciones seguras ante la presencia de lesiones previas.", bold_prefix="¿Qué es?")
    add_p(doc, "Prevenir la aparición o agravamiento de patologías musculoesqueléticas severas en la columna vertebral, las rodillas y los hombros.", bold_prefix="¿Para qué sirve?")
    add_p(doc, "Cada ejercicio de la biblioteca posee un vector de contraindicaciones. Si el usuario declara molestia lumbar, se activan reglas como `LES-01`, que suprimen de inmediato las sentadillas con barra libre y los pesos muertos convencionales, insertando en su lugar prensas de piernas a 45° con apoyo sacrolumbar guiado. Si hay lesión de hombro (`LES-03`), se eliminan los movimientos overhead (press militar) sustituyéndolos por jalones en polea y remos horizontales.", bold_prefix="¿Cómo funciona?")
    add_p(doc, "Declarar lesiones o molestias en rodillas, columna lumbar o articulaciones del hombro mediante casillas de verificación.", bold_prefix="¿Qué puede hacer el usuario?")
    add_p(doc, "Una rutina completamente adaptada que permite fortalecer la musculatura circundante sin exponer las articulaciones afectadas a fuerzas lesivas de cizallamiento o compresión axial.", bold_prefix="¿Qué resultado obtiene?")
    add_p(doc, "Marca la diferencia fundamental entre un software comercial genérico que lesiona al usuario y un Sistema Experto que cuida de su salud articular.", bold_prefix="¿Por qué es importante?")

    # FUNCIONALIDAD 7
    add_title_header(doc, "9.7 Filtros Protectores por Rango Etario y Obesidad Severa", level=2)
    add_p(doc, "Un conjunto de directivas biomecánicas especializadas que restringen intensidades y patrones motores en poblaciones vulnerables por edad o exceso ponderal crítico.", bold_prefix="¿Qué es?")
    add_p(doc, "Evitar daños irreparables en placas epifisarias de crecimiento en jóvenes y prevenir desgarros o caídas en adultos mayores, así como desgaste acelerado de cartílago en personas con sobrepeso extremo.", bold_prefix="¿Para qué sirve?")
    add_p(doc, "Las reglas `BIO-01` (>70 años), `BIO-02` (<16 años) y `BIO-03` (IMC ≥ 40) evalúan la edad y el índice de masa corporal. Al dispararse, sustituyen automáticamente las plantillas estándar por microciclos de movilidad funcional, equilibrio unipodal, estiramientos y ejercicios de bajo impacto, cancelando cualquier ejercicio pliométrico de salto o levantamiento olímpico.", bold_prefix="¿Cómo funciona?")
    add_p(doc, "Registrar su edad y medidas antropométricas reales en el formulario inicial.", bold_prefix="¿Qué puede hacer el usuario?")
    add_p(doc, "Una prescripción suave, segura y progresiva que respeta los límites fisiológicos propios de su etapa vital o condición ponderal.", bold_prefix="¿Qué resultado obtiene?")
    add_p(doc, "Garantiza una práctica deportiva ética y responsable, extendiendo los beneficios del acondicionamiento físico a sectores históricamente desatendidos.", bold_prefix="¿Por qué es importante?")

    # FUNCIONALIDAD 8
    add_title_header(doc, "9.8 Módulo de Explicabilidad y Razonamiento Transparente", level=2)
    add_p(doc, "Una interfaz de auditoría cognitiva que expone la traza lógica del razonamiento efectuado por el motor de inferencia.", bold_prefix="¿Qué es?")
    add_p(doc, "Dotar al sistema de total transparencia ('Explainable AI'), permitiendo al usuario y a los evaluadores comprender las razones biológicas que respaldan cada conclusión.", bold_prefix="¿Para qué sirve?")
    add_p(doc, "Durante el ciclo de evaluación, cada regla que cumple su premisa (FIRE) registra tanto su conclusión técnica como un texto explicativo detallado. Al pulsar el botón 'Lógica de IA', el sistema abre una ventana modal donde muestra el ratio de reglas activadas y desglosa cada regla con su justificación fisiológica.", bold_prefix="¿Cómo funciona?")
    add_p(doc, "Consultar en cualquier momento la ventana de transparencia del motor para leer por qué le asignaron determinado déficit o por qué se prohibió un ejercicio específico.", bold_prefix="¿Qué puede hacer el usuario?")
    add_p(doc, "Comprensión didáctica del proceso, despejando dudas y aprendiendo principios científicos de nutrición y anatomía aplicada.", bold_prefix="¿Qué resultado obtiene?")
    add_p(doc, "Elimina la desconfianza propia de los algoritmos opacos, construyendo una relación de confianza fundamentada en la evidencia demostrable.", bold_prefix="¿Por qué es importante?")

    # FUNCIONALIDAD 9
    add_title_header(doc, "9.9 Tablero de Control de Evolución Ponderal y Sobrecarga", level=2)
    add_p(doc, "Un módulo analítico y visual que registra y grafica la evolución del peso y las calorías a lo largo de sucesivas consultas en el tiempo.", bold_prefix="¿Qué es?")
    add_p(doc, "Monitorear la respuesta biológica del usuario para detectar estancamientos, verificar la eficacia del plan y aplicar principios de sobrecarga progresiva.", bold_prefix="¿Para qué sirve?")
    add_p(doc, "El controlador de base de datos (`database.py`) recupera las sesiones históricas del usuario, ordena las fechas y renderiza mediante Matplotlib una curva continua de evolución ponderal, calculando KPIs de cambio neto de peso y variación calórica.", bold_prefix="¿Cómo funciona?")
    add_p(doc, "Visualizar en su panel principal el gráfico interactivo de peso, consultar el historial tabulado de sesiones y realizar reevaluaciones periódicas.", bold_prefix="¿Qué puede hacer el usuario?")
    add_p(doc, "Una retroalimentación cuantitativa inmediata que le permite comprobar empíricamente si está perdiendo grasa o ganando masa muscular al ritmo estipulado.", bold_prefix="¿Qué resultado obtiene?")
    add_p(doc, "Es el motor principal de la motivación y la constancia, transformando el esfuerzo diario en datos visibles y medibles.", bold_prefix="¿Por qué es importante?")

    # FUNCIONALIDAD 10
    add_title_header(doc, "9.10 Generación y Exportación de Expedientes en PDF", level=2)
    add_p(doc, "Un subsistema de salida documental que compila toda la evaluación en un documento PDF estructurado de alta calidad tipográfica.", bold_prefix="¿Qué es?")
    add_p(doc, "Permite al usuario llevar consigo su plan en dispositivos móviles sin necesidad de abrir el software, imprimirlo para colocarlo en su cocina o entregarlo a su médico de cabecera.", bold_prefix="¿Para qué sirve?")
    add_p(doc, "El módulo `pdf_exporter.py` utiliza la biblioteca ReportLab para ensamblar un documento formal de múltiples páginas con paleta de colores institucional, tablas estructuradas de métricas, catálogo de comidas, microciclo semanal completo y notas de seguridad.", bold_prefix="¿Cómo funciona?")
    add_p(doc, "Hacer clic en 'Descargar PDF', seleccionar la carpeta de destino en su explorador de archivos y abrir el expediente generado al instante.", bold_prefix="¿Qué puede hacer el usuario?")
    add_p(doc, "Un documento profesional imprimible de presentación impecable con todos los detalles de su programa físico y nutricional.", bold_prefix="¿Qué resultado obtiene?")
    add_p(doc, "Otorga tangibilidad y formalidad profesional al proyecto, facilitando la consulta rápida durante la compra de víveres o en la sala de pesas.", bold_prefix="¿Por qué es importante?")

    # ═════════════════════════════════════════════════════════════════════════
    # CAPÍTULO 10: RECORRIDO DEL USUARIO (CASOS REALES)
    # ═════════════════════════════════════════════════════════════════════════
    add_title_header(doc, "10. Recorrido del Usuario (Casos Reales)", level=1)
    add_p(doc, "Para comprender de manera vívida la experiencia de uso de FitExpert, se presentan a continuación cuatro escenarios reales representativos que ilustran cómo el sistema procesa situaciones humanas heterogéneas:")

    add_title_header(doc, "10.1 Escenario A: Usuario Principiante con Molestias en Rodilla en el Hogar", level=2)
    add_p(doc, "Carlos, un administrativo de 38 años, sedentario, pesa 88 kg midiendo 174 cm (IMC 29.1, sobrepeso). Desea perder grasa pero no puede acudir a un gimnasio por falta de tiempo; entrena en su sala de estar con un par de mancuernas ligeras y reporta dolor crónico en su rodilla derecha tras una antigua torcedura deportiva. Sigue una dieta omnívora con 3 comidas al día.")
    add_p(doc, "Al ingresar sus datos en FitExpert, el sistema calcula una TMB de 1,770 kcal y un TDEE de 2,124 kcal. El motor dispara de inmediato la regla `NUT-01` aplicando un déficit de 500 kcal, fijando su meta en 1,624 kcal diarias. Al procesar el entrenamiento, la regla `TRAIN-CASA-01` selecciona una rutina de cuerpo completo de 3 días adaptada al hogar. Crucialmente, el subsistema biomecánico detecta su lesión de rodilla (`LES-02`): suprime sentadillas profundas, saltos y zancadas dinámicas, asignando puente de glúteos en el suelo, remo con mancuernas, flexiones con manos elevadas y plancha abdominal, protegiendo totalmente la articulación patelofemoral.", bold_prefix="Respuesta de FitExpert:")

    add_title_header(doc, "10.2 Escenario B: Levantador Intermedio con Lesión Lumbar en Gimnasio", level=2)
    add_p(doc, "Valeria, de 26 años, lleva año y medio entrenando en gimnasio comercial. Mide 165 cm y pesa 58 kg. Su meta es la hipertrofia muscular estética, pero recientemente fue diagnosticada con una protusión discal en L5-S1 que le genera lumbalgia al realizar sentadillas pesadas. Es intolerante a la lactosa.")
    add_p(doc, "El sistema calcula un TDEE de 2,200 kcal y, mediante la regla `NUT-02`, asigna un superávit de +400 kcal (2,600 kcal) con alta densidad proteica (30% proteína, 50% carbohidratos). La regla `NUT-11` purga automáticamente todos los quesos, batidos de suero convencionales y yogures del menú, sustituyéndolos por carnes magras, legumbres y bebidas de almendra fortificadas. En el gimnasio, la regla `LES-01` prohíbe la sentadilla libre con barra y el peso muerto convencional, reconfigurando su split Push-Pull-Legs de 4 días (`TRAIN-GYM-03`) para utilizar prensa de piernas guiada con soporte sacrolumbar completo y extensiones de cuádriceps, permitiéndole ganar masa muscular con cero dolor lumbar.", bold_prefix="Respuesta de FitExpert:")

    add_title_header(doc, "10.3 Escenario C: Adulto Mayor en Prevención de Sarcopenia", level=2)
    add_p(doc, "Don Roberto, de 73 años, pesa 66 kg y mide 168 cm. Busca mantenerse activo, conservar su fuerza funcional para subir escaleras de forma autónoma y mejorar su equilibrio. No tiene experiencia atlética previa.")
    add_p(doc, "El motor de inferencia dispara la regla biomecánica `BIO-01` y la regla de seguimiento `SEG-04`. El sistema anula de inmediato cualquier ejercicio de impacto o carga axial, seleccionando la plantilla `movilidad_3d`. Diseña un microciclo de 3 días centrado en movilidad de cadera, sentadillas asistidas tomando un soporte fijo, marcha estática con elevación controlada de rodillas, equilibrio unipodal para prevenir caídas y flexiones suaves contra la pared. En el plano nutricional, la regla `NUT-06` y `NUT-04` aseguran una hidratación de 2.5 litros y un aporte proteico suficiente para frenar la pérdida de masa muscular asociada a la edad.", bold_prefix="Respuesta de FitExpert:")

    add_title_header(doc, "10.4 Escenario D: Reevaluación Periódica tras 4 Semanas de Constancia", level=2)
    add_p(doc, "Tras un mes siguiendo las directivas del sistema, Carlos (el usuario del Escenario A) vuelve a iniciar sesión en FitExpert. Se pesa en ayunas y comprueba que su masa corporal descendió de 88.0 kg a 86.1 kg (-1.9 kg de grasa corporal perdida a un ritmo seguro y constante de ~0.48 kg/semana). Accede a 'Nueva Evaluación', actualiza su peso a 86.1 kg y genera su nuevo plan.")
    add_p(doc, "El sistema recalcula su TMB y TDEE ajustándolos a su nuevo peso corporal menor, evitando el estancamiento metabólico. Al regresar a 'Mi Perfil', la gráfica de Matplotlib se actualiza de forma automática mostrando la curva descendente continua, y el panel de KPIs reporta un 'Cambio de Peso' de -1.9 kg desde el inicio, confirmando la eficacia del método.", bold_prefix="Respuesta de FitExpert:")

    doc.add_page_break()
