# 🤖 Agente Monitor de Empleos en Costa Rica (Alertas a WhatsApp)

Agente inteligente desarrollado en Python para **Luis Diego Agüero Quirós**, diseñado para escanear de forma constante plataformas de empleo (**LinkedIn Costa Rica** y **Computrabajo Costa Rica**) y notificarte al instante a tu WhatsApp personal apenas se publique una vacante.

---

## 🎯 Perfiles Filtrados Automáticamente

1. **📊 Análisis de Datos (Junior / Entry Level):**
   - Vacantes de Analista de Datos Junior, Power BI, SQL, reporting, dashboards.
2. **💻 Soporte TI & Manejo de Tickets (Onsite o Backoffice):**
   - Soporte Técnico L1/L2, Mesa de Ayuda, Help Desk, Service Desk, Desktop Support, Jira, Active Directory, Redes/Cabling.
3. **⛔ Filtros de Exclusión Estricta:**
   - Descarta automáticamente puestos de **Call Center con toma de llamadas / ventas telefónicas / telemercadeo**.
   - Descarta puestos de alta jerarquía o Senior (+5 a 10 años) que no sean relevantes para tu etapa actual.

---

## 📲 Paso 1: Activar tus Notificaciones de WhatsApp (Toma 1 minuto)

Usamos **CallMeBot**, que es 100% gratuito y no requiere crear cuentas complejas en Meta/Facebook:

1. Agrega a los contactos de tu teléfono el número del bot de WhatsApp:
   👉 **+34 911 06 16 35** (Nombre: *CallMeBot*)
2. Ábrele un chat en WhatsApp y envíale exactamente este mensaje:
   `	ext
   I allow callmebot to send me messages
   `
3. En pocos segundos, el bot te responderá con tu **API Key** personal (ej: 1234567).
4. Abre el archivo .env en la carpeta del proyecto y coloca tu API Key:
   `env
   WHATSAPP_PROVIDER=callmebot
   CALLMEBOT_PHONE=50662291039
   CALLMEBOT_API_KEY=tu_api_key_recibida
   `

---

## 🚀 Paso 2: Probar el Envío a WhatsApp

Haz doble clic en:
👉 **	est_whatsapp.bat**

O ejecuta en la terminal:
`powershell
.\.venv\Scripts\python.exe agent.py --test-whatsapp
`
Recibirás un mensaje de bienvenida en tu WhatsApp confirmando que la conexión está activa.

---

## ⚡ Paso 3: Iniciar el Agente

Haz doble clic en:
👉 **un_agent.bat**

O ejecuta en la terminal:
`powershell
.\.venv\Scripts\python.exe agent.py --daemon
`

El agente se quedará monitoreando en segundo plano y cada **15 minutos** revisará las plataformas. Si detecta un puesto nuevo que calce con tu perfil, te enviará la alerta a WhatsApp al instante con el enlace para que seas el primero en postularte.

---

## ⚙️ Personalización (Archivo config.yaml)

Puedes modificar en cualquier momento el archivo config.yaml para:
- Cambiar el intervalo de escaneo (ej: cada 10, 15 o 30 minutos).
- Agregar o quitar palabras clave de búsqueda.
- Ajustar las exclusiones.
