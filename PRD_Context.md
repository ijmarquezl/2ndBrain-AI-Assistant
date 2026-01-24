📋 Contexto del Proyecto 2ndBrain
Instrucción: Actúa como un Arquitecto de Software Senior y experto en Producto. Iniciaremos el desarrollo del proyecto "Segundo Cerebro Personal" bajo la metodología SecWeb 2.0.

A continuación, te presento los Requerimientos Funcionales (RF) iniciales del MVP. Tu tarea es analizar estos requerimientos y, posteriormente, generar el plan de implementación, investigar las librerías necesarias y definir la arquitectura de solución (considerando un entorno serverless gratuito como Streamlit Cloud + APIs).

Objetivo del Sistema: Crear un asistente inteligente conversacional que optimice mi rendimiento cognitivo, gestione mi estado emocional y alinee mis tareas con mis ritmos biológicos.

Requerimientos Funcionales Detallados:

RF1: Módulo de Sincronización Biológica (Bio-Sync)

El sistema debe conocer mi horario de Ayuno Intermitente (Ventana de ayuno: 20:00 a 11:00 horas).

El sistema debe identificar mi "Ventana de Cetosis" (08:00 a 11:00 horas) como el periodo de máximo rendimiento cognitivo.

Acción: Si intento agendar tareas administrativas o de baja energía durante la "Ventana de Cetosis", el sistema debe sugerir moverlas y priorizar trabajo creativo/estratégico.

Acción: Si consulto sobre comida fuera del horario de alimentación, el sistema debe recordarme el tiempo restante de ayuno para motivarme.

RF2: Coach Socrático de Tareas (Input)

Al ingresar una nueva tarea o proyecto, el sistema no debe aceptarla pasivamente.

Acción: El sistema debe iniciar un diálogo socrático (técnica de los "5 Porqués") para indagar la motivación real detrás de la tarea.

Solo cuando la motivación raíz es clara, la tarea se guarda en la base de datos.

RF3: Monitor de "Hackeo Mental" (Estado Emocional)

El sistema debe permitir "Check-ins" emocionales rápidos mediante chat.

Acción: Analizar mis entradas buscando patrones de estrés o "historias falsas" (basado en principios de Mind Hacking Happiness y Estoicismo).

Acción: Proveer re-encuadres (reframing) inmediatos basados en filosofía estoica o principios de Aikido (ej. usar la fuerza del problema a mi favor) para recuperar la neutralidad emocional.

RF4: Contexto de Conocimiento Personalizado

El sistema debe responder consultas y dar consejos utilizando una base de conocimiento restringida a mis temas de interés: Filosofía Estoica, Aikido, y los libros The Achievement Habit, Atomic Habits y Brain Rules.

Siguiente paso: Confirma que has entendido estos requerimientos funcionales y procede a determinar qué información adicional (no funcional) necesitas o qué stack técnico sugieres para cumplir con esto a costo cero.