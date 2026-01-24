# 🧠 Segundo Cerebro IA (2ndBrain)

¡Bienvenido a tu **Sistema Operativo Personal de Productividad**!
Esta aplicación no es solo un chat; es un ecosistema integrado que combina **Gestión de Tareas**, **Filosofía Estoica** y **Base de Conocimiento Personal** (RAG) para ayudarte a pensar mejor y actuar con propósito.

## ✨ Características Principales

### 1. 🤖 Coach Socrático
Olvídate de las listas de tareas muertas.
- **Planificación Activa**: El agente te ayuda a definir tareas claras interrogándote sobre el *Para qué* y el *Cómo*.
- **Validación Inteligente**: No te deja guardar tareas vagas o sin fecha (si es necesario).
- **Filosofía Estoica**: Respuestas inspiradas en Marco Aurelio y Séneca.

### 2. 📚 Base de Conocimiento (RAG)
Consulta tu biblioteca personal.
- **Libros Indexados**: Hábitos Atómicos, Brain Rules, Estoicismo Moderno, etc.
- **RAG Local**: El sistema busca fragmentos relevantes de tus libros para responder tus dudas con sabiduría curada, no alucinaciones.

### 3. ✍️ Diario y Reflexión
- **Modo Journaling**: Un espacio guiado donde el agente analiza tu día (qué tareas completaste, cuáles fallaron) y te hace **3 preguntas profundas** para mejorar mañana.
- **Sabiduría del Día**: Frases estoicas generadas contextualmente en la barra lateral.

### 4. 🔔 Notificaciones Inteligentes (Telegram)
Tu cerebro te avisa dónde estés.
- **Recordatorios Puntuales**: Si una tarea tiene hora (ej: "14:30"), te llega un mensaje.
- **Hábitos**: Recordatorios diarios fijos.
- **Cero Spam**: Solo un aviso por tarea al día.

---

## 🚀 Cómo Interactuar

### En la App (Streamlit)
1.  **Chat Principal**:
    - *"Quiero leer 10 páginas hoy".* -> El Coach te ayudará a definir hora y libro.
    - *"¿Qué dice el estoicismo sobre la ansiedad?"* -> El RAG consultará tus libros.
    - *"¿Qué tareas tengo hoy?"* -> El agente leerá tu DB.

2.  **Barra Lateral**:
    - **Nueva Frase**: Recibe una dosis de motivación.
    - **Iniciar Reflexión (Journaling)**: Úsalo al final del día para cerrar ciclos.

### En Telegram
- Solo espera. El bot (@TuBot) te escribirá cuando sea el momento de actuar.

---

## 🛠️ Stack Tecnológico
- **Frontend**: Streamlit.
- **IA Generativa**: Groq (Llama 3.3 70B).
- **Vectores/Embeddings**: HuggingFace (Local) + Supabase (pgvector).
- **Base de Datos**: Supabase (PostgreSQL).
- **Backend**: Python (Notificadores asíncronos).

---

## ☁️ Instalación (Local)

1. **Clonar Repo**:
   ```bash
   git clone https://github.com/ijmarquezl/2ndBrain-AI-Assistant.git
   cd 2ndBrain-AI-Assistant
   ```

2. **Entorno Virtual**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Variables de Entorno (.env)**:
   Configura tus claves de API (Groq, Supabase, Telegram).

4. **Ejecutar**:
   ```bash
   # App
   streamlit run app.py
   
   # Notificador (Segundo plano)
   python scripts/notifier.py
   ```
