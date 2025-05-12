from transformers import pipeline

pipe = pipeline("text-generation", model="microsoft/phi-2", device=-1)
output = pipe("¿Cuál es la capital de Francia?", max_new_tokens=50)
print(output[0]["generated_text"])
