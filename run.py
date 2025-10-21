import os
from backend.app import create_app

# Crear una instancia de la aplicación utilizando la factory
app = create_app()

if __name__ == '__main__':
    # Obtener el puerto desde las variables de entorno o usar 5000 por defecto
    port = int(os.environ.get('PORT', 5000))
    # Ejecutar la aplicación
    # host='0.0.0.0' hace que el servidor sea accesible desde cualquier IP,
    # lo cual es útil para desarrollo y contenedores.
    app.run(host='0.0.0.0', port=port, debug=True)
