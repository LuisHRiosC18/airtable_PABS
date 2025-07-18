Dashboard de Métricas de RH con Streamlit
Este proyecto es una aplicación web construida con Streamlit para visualizar y analizar las métricas de desempeño de un equipo de reclutamiento. Los datos se obtienen directamente desde una base de Airtable.

Características Principales
Visualización por Periodo: Filtra el desempeño por día, semana y mes.

Filtros Interactivos: Selecciona un reclutador específico y una fecha para analizar su rendimiento.

Gráficos de Medidor (Gauge Charts): Compara de forma visual e intuitiva el rendimiento actual contra las metas establecidas.

Metas Ajustables: Las metas para las vistas semanales y mensuales se pueden modificar directamente en la interfaz para simular escenarios o ajustar objetivos.

Consumo Eficiente de API: La aplicación utiliza el sistema de caché de Streamlit para minimizar las llamadas a la API de Airtable, actualizando los datos solo dos veces al día.

Infraestructura y Flujo de Datos
La aplicación sigue un flujo de datos diseñado para ser eficiente y seguro.

Método 1: Conexión Directa a Airtable (Recomendado)
Este es el método implementado por defecto en app.py.

Conexión Segura: La aplicación se conecta a la API de Airtable usando credenciales (API Key, Base ID, Table Name) almacenadas de forma segura en los "secrets" de Streamlit (.streamlit/secrets.toml).

Caché de Datos: Para evitar sobrecargar la API de Airtable, se utiliza el decorador @st.cache_data de Streamlit. Se ha configurado un TTL (Time To Live) de 43200 segundos (12 horas). Esto significa que Streamlit solo llamará a la API de Airtable para obtener nuevos datos una vez cada 12 horas. Si el usuario refresca la página dentro de ese periodo, se usarán los datos ya almacenados en caché.

Procesamiento: Los datos se cargan en un DataFrame de Pandas para su limpieza, transformación y análisis.

Visualización: Los datos procesados se muestran en la interfaz de Streamlit a través de tablas y gráficos de Plotly.

Método 2: Alternativa con Archivo CSV en GitHub
Si prefieres no conectar la app directamente a la API, puedes seguir este método:

Exporta tus datos de Airtable a un archivo datos_reclutamiento.csv.

Sube este archivo a tu repositorio de GitHub.

En el script app.py, comenta la función load_data_from_airtable y descomenta la función load_data_from_github.

Asegúrate de reemplazar la URL en load_data_from_github por la URL "raw" de tu archivo CSV en GitHub.

Cómo Configurar y Ejecutar la Aplicación
Sigue estos pasos para poner en marcha la aplicación en tu máquina local.

1. Clonar el Repositorio
git clone <URL_DE_TU_REPOSITORIO>
cd <NOMBRE_DEL_REPOSITORIO>

2. Crear un Entorno Virtual (Recomendado)
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate

3. Instalar Dependencias
pip install -r requirements.txt

4. Configurar los Secretos de Streamlit
Crea una carpeta llamada .streamlit en la raíz de tu proyecto y, dentro de ella, un archivo llamado secrets.toml. Añade tus credenciales de Airtable de la siguiente manera:

# .streamlit/secrets.toml

[airtable]
api_key = "keyXXXXXXXXXXXXXX"  # Tu API Key de Airtable
base_id = "appXXXXXXXXXXXXXX"  # El ID de tu Base de Airtable
table_name = "Nombre de tu Tabla" # El nombre exacto de tu tabla

5. Ejecutar la Aplicación
Una vez configurado, ejecuta la aplicación desde tu terminal:

streamlit run app.py

Se abrirá una nueva pestaña en tu navegador con el dashboard funcionando.
