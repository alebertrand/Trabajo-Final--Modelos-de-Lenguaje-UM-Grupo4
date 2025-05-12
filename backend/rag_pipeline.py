import os
import re
import pandas as pd
from pdfminer.high_level import extract_pages
from pdfminer.layout import LTTextContainer
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_core.documents import Document
from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

# ====================================
# CARGA VARIABLES DE ENTORNO
# ====================================

load_dotenv(dotenv_path="backend/OpenAi.env")  # Asegura que OPENAI_API_KEY esté disponible en el entorno

# ====================================
# FUNCIONES AUXILIARES
# ====================================

def limpiar_encabezados_pies(texto):
    patrones = [
        r'http\S+',
        r'\d{1,3}\s*/\s*\d{1,3}',
        r'FYS\s*\|.*',
        r'www\.fys\.com\.ar',
        r'\s+Página\s+\d+',
        r'Puedes encontrar más recetas e informacion en',
    ]
    for patron in patrones:
        texto = re.sub(patron, '', texto, flags=re.IGNORECASE)
    return re.sub(r'\n+', '\n', texto).strip()

def extraer_recetas(path_to_pdf, pagina_inicio=13, pagina_fin=121):
    recetas = []
    for i, page_layout in enumerate(extract_pages(path_to_pdf)):
        numero_pagina = i + 1
        if numero_pagina < pagina_inicio or numero_pagina > pagina_fin:
            continue

        texto_pagina = "".join(
            element.get_text() for element in page_layout if isinstance(element, LTTextContainer)
        )
        texto_limpio = limpiar_encabezados_pies(texto_pagina)
        partes = re.split(r'\bINGREDIENTES\b', texto_limpio, flags=re.IGNORECASE)
        if len(partes) < 2:
            continue

        subpartes = re.split(r'\bELABORACIÓN\b', partes[1], flags=re.IGNORECASE)
        if len(subpartes) < 2:
            continue

        ingredientes = subpartes[0].strip()
        elaboracion = subpartes[1].strip()

        condiciones = ""
        match_cond = re.search(r'(Esta receta es apta.*)', elaboracion, re.IGNORECASE)
        if match_cond:
            condiciones = match_cond.group(1).strip()
            elaboracion = re.sub(r'(Esta receta es apta.*)', '', elaboracion, flags=re.IGNORECASE).strip()

        autora = ""
        match_aut = re.search(r'Autora?:\s*(.*)', texto_limpio, re.IGNORECASE)
        if match_aut:
            autora = match_aut.group(1).strip()
            elaboracion = re.sub(r'Autora?:\s*.*', '', elaboracion, flags=re.IGNORECASE).strip()

        titulo = " ".join(dict.fromkeys([l.strip() for l in partes[0].strip().split("\n") if l.strip()])).title()

        recetas.append({
            "titulo": titulo,
            "ingredientes": ingredientes,
            "elaboracion": elaboracion,
            "condiciones": condiciones,
            "autora": autora
        })

    return recetas

# ====================================
# PIPELINE PRINCIPAL
# ====================================

class RAGPipeline:
    def __init__(self):
        self.pdf_path = "backend/recetas_fys.pdf"
        self.check_pdf()
        self.recetas = extraer_recetas(self.pdf_path)
        self.documents = self.create_documents()
        self.retriever = self.create_vectorstore()
        self.llm = self.load_llm()
        self.chain = self.create_chain()

    def check_pdf(self):
        if not os.path.exists(self.pdf_path):
            raise FileNotFoundError(f"No se encontró {self.pdf_path}")

    def create_documents(self):
        return [
            Document(
                page_content=f"RECETA: {r['titulo']}\n\nIngredientes:\n{r['ingredientes']}\n\nElaboración:\n{r['elaboracion']}",
                metadata={"titulo": r["titulo"], "condiciones": r["condiciones"], "autora": r["autora"]}
            ) for r in self.recetas
        ]

    def create_vectorstore(self):
        embeddings = HuggingFaceEmbeddings(model_name="intfloat/multilingual-e5-large")
        vectorstore = FAISS.from_documents(self.documents, embeddings)
        return vectorstore.as_retriever(search_type="similarity", search_kwargs={"k": 4})

    def load_llm(self):
        return ChatOpenAI(model="gpt-3.5-turbo", temperature=0.1, max_tokens=700)

    def create_chain(self):
        prompt = PromptTemplate(
            input_variables=["context", "question"],
            template="""
Eres un asistente especializado en cocina saludable para familias.
Se te proveen fragmentos de varias recetas. Tu tarea es identificar las recetas relevantes a la pregunta y listar sus títulos, ingredientes y pasos por separado.
Además, de proveer las recetas, debes dar un breve comentario al inicio sobre la pregunta del user o las recetas provistas.
Debes dar una respuesta clara, amable, útil y en español. No mezcles información de recetas diferentes.
La respuesta debe estar basada únicamente en la información del contexto provisto.
Si no sabes la respuesta porque no se encuentra en los fragmentos del contexto dado, responde con \"No lo sé, no forma parte del recetario\" y absolutamente nada más.
No inventes ingredientes, pasos, ni consejos que no estén presentes en el recetario.
Siempre finaliza alentando a cocinar en familia, comer saludable y consultar el recetario completo.
Pregunta: {question}
Contexto:
{context}
"""
        )
        return (
            {"context": self.retriever | self.format_docs, "question": RunnablePassthrough()}
            | prompt
            | self.llm
            | StrOutputParser()
        )

    def format_docs(self, docs):
        return "\n\n---\n\n".join(doc.page_content for doc in docs)

    def ask(self, question):
        return self.chain.invoke(question)
