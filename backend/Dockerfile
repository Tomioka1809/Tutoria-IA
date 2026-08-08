FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Usuario sin privilegios: el contenedor corria como root, asi que cualquier fallo
# de la aplicacion se ejecutaba con todos los permisos dentro del contenedor.
# El uid 1000 coincide con el usuario habitual del host, para que el bind mount de
# desarrollo (./backend:/app) siga siendo escribible.
RUN useradd --create-home --uid 1000 appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

# Se invoca via /bin/sh para no depender del bit de ejecucion, que con el
# bind mount de docker-compose lo aporta el archivo del host y no la imagen.
ENTRYPOINT ["/bin/sh", "/app/docker-entrypoint.sh"]

# Sin --reload: el recargador vigila el sistema de archivos y reinicia el proceso,
# que es lo que se quiere en desarrollo y no en un despliegue. docker-compose.yml lo
# vuelve a agregar para el entorno local, de modo que la imagen queda desplegable.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
