import os
import re
import torch
import pandas as pd
from pdfminer.high_level import extract_pages
from pdfminer.layout import LTTextContainer
from transformers import pipeline, AutoTokenizer, AutoModelForCausalLM
from huggingface_hub import login

from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_core.documents import Document
from langchain_community.llms import HuggingFacePipeline
from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

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
        self.pdf_path = "recetas_fys.pdf"  # Archivo debe estar en misma carpeta
        self.check_pdf()
        self.recetas = extraer_recetas(self.pdf_path)
        self.documents = self.create_documents()
        self.retriever = self.create_vectorstore()
        self.llm = self.load_llm()
        self.chain = self.create_chain()

    def check_pdf(self):
        if not os.path.exists(self.pdf_path):
            raise FileNotFoundError(f"❌ No se encontró el archivo {self.pdf_path}. Asegúrate de que esté en la carpeta backend.")

    def create_documents(self):
        return [
            Document(
                page_content=f"Ingredientes:\n{r['ingredientes']}\n\nElaboración:\n{r['elaboracion']}",
                metadata={"titulo": r["titulo"], "condiciones": r["condiciones"], "autora": r["autora"]}
            ) for r in self.recetas
        ]

    def create_vectorstore(self):
        embeddings = HuggingFaceEmbeddings(model_name="intfloat/multilingual-e5-large")
        vectorstore = FAISS.from_documents(self.documents, embeddings)
        return vectorstore.as_retriever(search_type="similarity", search_kwargs={"k": 4})

    def load_llm(self):
        login("hf_xxxxxxxxxxxxxxxxxxxxx")
        model_id = "microsoft/phi-2"
        tokenizer = AutoTokenizer.from_pretrained(model_id)
        model = AutoModelForCausalLM.from_pretrained(model_id)

        pipe = pipeline(
            "text-generation",
            model=model,
            tokenizer=tokenizer,
            device=-1,
            torch_dtype=torch.float32,
            temperature=0.1,
            do_sample=True,
            max_new_tokens=512,
            return_full_text=False
        )
        return HuggingFacePipeline(pipeline=pipe)

    def create_chain(self):
        prompt = PromptTemplate(
            input_variables=["context", "question"],
            template="""
<|start_header_id|>user<|end_header_id|>
Eres un asistente especializado en cocina saludable para familias.
Se te proveen fragmentos extraídos de un recetario para responder una pregunta sobre recetas.
Debes dar una respuesta clara, amable, útil y en español.
La respuesta debe estar basada únicamente en la información del contexto provisto.
Si no sabes la respuesta porque no se encuentra en los fragmentos del contexto dado, responde con \"No lo sé\".
No inventes ingredientes, pasos, ni consejos que no estén presentes en el recetario.
Siempre finaliza alentando a cocinar en familia y consultar el recetario completo.
Pregunta: {question}
Contexto: {context}<|eot_id|><|start_header_id|>assistant<|end_header_id|>
"""
        )
        return (
            {"context": self.retriever | self.format_docs, "question": RunnablePassthrough()}
            | prompt
            | self.llm
            | StrOutputParser()
        )

    def format_docs(self, docs):
        return "\n\n".join(doc.page_content for doc in docs)

    def ask(self, question):
        return self.chain.invoke(question)
