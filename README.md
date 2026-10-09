# Predicción del precio de casas en California (servicio web)

Servicio web con FastAPI que expone un modelo de árbol de decisión entrenado
sobre el dataset de viviendas de California. Devuelve el precio medio estimado
de una zona censal a partir de sus características.

Autores: David Araiz Saez, Daniel Bernal Anzano

## Contenido del repositorio

- `app.py`: servicio FastAPI con los endpoints `/` (health-check) y `/predict`.
- `model_training.py`: script que entrena el modelo y genera el `.pkl`.
- `modelo_california.pkl`: modelo entrenado.
- `requirements.txt`: dependencias del proyecto.

## Pasos del despliegue en Render

1. **New Web Service** en Render.
2. Conectar el repositorio de GitHub (`danielbernalanz/practica2`).
3. **Start Command**: `uvicorn app:app --host 0.0.0.0 --port $PORT`
4. **Root Directory**: dejar vacío (despliegue desde la raíz).
5. Deploy.

## URL final
<https://practica2-7wam.onrender.com>
