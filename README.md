
# Asistente de Cocina Saludable (RAG con OpenAI)

Este proyecto implementa un sistema de Recuperación-Aumentada con Generación (RAG) que permite consultar un recetario saludable en formato PDF utilizando preguntas en lenguaje natural. Se basa en FastAPI para el backend, LangChain para el pipeline de RAG y OpenAI como modelo generador. Incluye una interfaz visual construida en Streamlit y puede ejecutarse localmente o dentro de un contenedor Docker.

---

## Instrucciones para instalación y ejecución del sistema

###  Ejecución local

1. Clonar el repositorio:


git clone https://github.com/tu_usuario/asistente-recetas.git
cd asistente-recetas


2. Ejecutar el script de instalación del entorno:


bash setup_api.sh


Este script creará un entorno virtual, instalará las dependencias listadas en `requirements.txt` y dejará el entorno listo.

3. Iniciar el sistema (API + Streamlit):


bash run_api.sh


Esto iniciará:
- FastAPI en [http://127.0.0.1:8000/docs]
- Streamlit en [http://localhost:8501]

---

## Ejecución en contenedor Docker

Para ejecutar todo el sistema directamente desde un contenedor Docker:


bash run_docker.sh


Este script construirá una imagen Docker llamada `recetario`, y luego ejecutará el contenedor mapeando los puertos necesarios.

Al finalizar, el sistema estará accesible en:
- [http://localhost:8000/docs] para la API
- [http://localhost:8501] para la interfaz Streamlit

---

##  Requisitos del entorno

- Python 3.11
- pip
- Docker (si se desea ejecutar en contenedor)
- Clave de API de OpenAI (colocada en archivo `.env` como `OPENAI_API_KEY=tu_clave`)

Las dependencias se instalan automáticamente con `setup_api.sh` desde el archivo `requirements.txt`.

---

##  Notas adicionales

- El archivo `.env` debe estar presente en la raíz del proyecto para permitir el acceso al modelo de OpenAI.
- Si necesitás correr todo manualmente sin los scripts, podés seguir las instrucciones tradicionales de activación de entorno y ejecución de servidores.

---

##  Descripción del sistema RAG implementado

###  Parseo del recetario

El sistema utiliza `pdfminer.six` para extraer texto del archivo PDF `recetas_fys.pdf`, específicamente entre las páginas 13 y 121, que contienen las recetas. A través de expresiones regulares se identifican las secciones clave:

- **Título** de la receta
- **Ingredientes**
- **Elaboración**
- **Condiciones especiales** (por ejemplo: sin TACC, apto diabéticos)
- **Autora** de la receta

El texto se limpia eliminando encabezados, pies de página y enlaces innecesarios.

###  Modelo de embeddings

Se utiliza el modelo `intfloat/multilingual-e5-large` vía `HuggingFaceEmbeddings` de LangChain. Este modelo transforma cada receta en un vector numérico semántico, lo que permite compararlas con las consultas del usuario.

###  Base vectorial (vectorstore)

Los vectores generados se indexan con **FAISS**, una librería eficiente para búsquedas de similitud. El sistema recupera los 4 documentos más similares a la pregunta (`k=4`), usando búsqueda por similitud coseno.

###  Prompting

El prompt está diseñado con los siguientes principios:

- Debe **responder solo con la información extraída del recetario**
- Las respuestas deben estar **en español, con un tono amable y claro**
- No se debe inventar información
- Se debe **incluir un comentario introductorio** sobre la consulta
- Se finaliza alentando a cocinar en familia y consultar el recetario completo

Se utiliza `PromptTemplate` de LangChain para construir este mensaje dinámicamente, combinando el contexto recuperado y la pregunta del usuario.

###  LLM utilizado

El modelo generador actual es `gpt-3.5-turbo`, accedido a través de la clase `ChatOpenAI` de LangChain. Este modelo garantiza:
- Fluidez y coherencia en español
- Buen manejo de respuestas estructuradas (listas, párrafos, recetas)
- Bajo costo y tiempo de inferencia razonable

Durante el desarrollo también se probaron los siguientes modelos locales:

- **Gemma 2B**: respuestas incorrectas y recuperación deficiente del contenido.
- **LLaMA-3.2-3B**: resultados aceptables pero requería demasiada memoria RAM, causando fallos al correr localmente.
- **Mistral-7B**: resultados aceptables pero requería demasiada memoria RAM, causando fallos al correr localmente.

Por estas razones se optó por usar un modelo de OpenAI, que ofrece mayor robustez y disponibilidad en producción.

---

##  Justificación de las elecciones técnicas

| Componente        | Elección               | Justificación                                                                 |
|-------------------|------------------------|-------------------------------------------------------------------------------|
| **PDF parsing**   | `pdfminer.six`         | Preciso para extracción estructurada de texto en PDFs complejos              |
| **Embeddings**    | `multilingual-e5-large`| Soporte para español y excelente rendimiento en recuperación semántica       |
| **Vector store**  | `FAISS`                | Rápido, escalable y fácil de integrar con LangChain                          |
| **LLM**           | `gpt-3.5-turbo`        | Genera respuestas de alta calidad sin requerir infraestructura local         |
| **Framework RAG** | `LangChain`            | Modular y con integración directa con OpenAI, FAISS y pipelines personalizados|
| **API**           | `FastAPI`              | Ligero, rápido y con documentación automática accesible desde `/docs`        |
| **Despliegue**    | `Docker`               | Permite portabilidad y entornos reproducibles para un despliegue sencillo    |
