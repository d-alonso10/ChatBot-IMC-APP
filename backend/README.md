# Backend - API IMC Pediátrico

API REST desarrollada con FastAPI para calcular el Índice de Masa Corporal (IMC) en niños de 1 a 12 años y proporcionar recomendaciones personalizadas.

## 🚀 Características

- Cálculo de IMC pediátrico con clasificación por percentiles
- Generación de gráficos personalizados comparando el IMC del niño con percentiles saludables
- Chatbot conversacional que guía al usuario paso a paso
- Manejo robusto de errores con mensajes específicos
- Soporte para múltiples usuarios simultáneos con gráficos únicos (UUID)
- Type hints completos para mejor mantenibilidad del código

## 📋 Requisitos

- Python 3.10 o superior
- pip (gestor de paquetes de Python)

## 🔧 Instalación

1. **Navegar al directorio del backend:**
```bash
cd backend
```

2. **Crear un entorno virtual (recomendado):**
```bash
python -m venv venv
```

3. **Activar el entorno virtual:**
- Windows:
```bash
venv\Scripts\activate
```
- Linux/Mac:
```bash
source venv/bin/activate
```

4. **Instalar dependencias:**
```bash
pip install -r requirements.txt
```

## ▶️ Ejecución

### Modo desarrollo:
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Modo producción:
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

La API estará disponible en: `http://localhost:8000`

Documentación interactiva: `http://localhost:8000/docs`

## 🌐 Configuración de CORS

Por defecto, la API permite conexiones desde cualquier origen (`*`). Para producción, configura la variable de entorno `ALLOWED_ORIGINS`:

```bash
# Windows PowerShell
$env:ALLOWED_ORIGINS="https://miapp.com,https://www.miapp.com"

# Linux/Mac
export ALLOWED_ORIGINS="https://miapp.com,https://www.miapp.com"
```

## 📡 Endpoints

### `GET /bienvenida`
Retorna el mensaje de bienvenida inicial.

**Respuesta:**
```json
{
  "respuesta": "👋 ¡Hola! Soy tu asistente de IMC...",
  "grafico": false,
  "graph_id": null
}
```

### `POST /mensaje`
Procesa un mensaje del usuario en el flujo conversacional.

**Request:**
```json
{
  "texto": "5"
}
```

**Respuesta:**
```json
{
  "respuesta": "👦 ¿Cuál es el sexo del menor?...",
  "grafico": false,
  "graph_id": null
}
```

### `GET /grafico/{graph_id}`
Obtiene el gráfico generado por su ID único.

**Parámetros:**
- `graph_id`: UUID del gráfico

**Respuesta:** Imagen PNG

### `GET /reiniciar`
Reinicia el estado conversacional del chatbot.

## 📊 Datos de Percentiles

Los datos de percentiles se encuentran en `data/tablas_percentiles.json` y cubren edades de **1 a 18 años** para niños y niñas, basados en las tablas de crecimiento de la OMS y CDC.

## 🛠️ Estructura del Proyecto

```
backend/
├── chatbot.py              # Lógica conversacional del chatbot
├── main.py                 # Aplicación FastAPI y endpoints
├── utils.py                # Funciones auxiliares (cálculo IMC, gráficos)
├── requirements.txt        # Dependencias del proyecto
├── data/
│   └── tablas_percentiles.json  # Datos de percentiles por edad y sexo
└── graficos/               # Gráficos generados (creado automáticamente)
```

## 🔒 Seguridad

- Los gráficos se generan con nombres únicos (UUID) para evitar conflictos entre usuarios
- Validación de entrada en todos los endpoints
- Manejo específico de excepciones (FileNotFoundError, JSONDecodeError, PermissionError)
- CORS configurable por variable de entorno

## 📝 Notas Importantes

1. **Rango de edad:** La API acepta edades entre 1 y 18 años con datos completos de percentiles pediátricos.

2. **Limpieza de gráficos:** Los gráficos generados se almacenan en la carpeta `graficos/`. Considera implementar un sistema de limpieza automática para archivos antiguos en producción.

3. **Escalabilidad:** Para múltiples instancias del servidor, considera usar un almacenamiento compartido (S3, Azure Blob) para los gráficos.

## 🐛 Solución de Problemas

**Error: "No se encontró el archivo de tabla de percentiles"**
- Verifica que existe el archivo `data/tablas_percentiles.json`

**Error: "Edad fuera de rango"**
- La API solo soporta edades de 1 a 12 años

**Gráfico no disponible**
- Verifica que la carpeta `graficos/` tenga permisos de escritura
- Asegúrate de que matplotlib está instalado correctamente

## 📄 Licencia

Este proyecto es parte de una aplicación de salud pediátrica.
