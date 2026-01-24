import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("GOOGLE_API_KEY")

if not api_key:
    print("❌ No se encontró GOOGLE_API_KEY en las variables de entorno.")
    exit(1)

genai.configure(api_key=api_key)

print(f"🔑 Verificando modelos para la API Key proporcionada...")

try:
    print("\n📋 Modelos Disponibles:")
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(f" - {m.name}")
            
    print("\n✅ Conexión exitosa. Usa uno de los nombres anteriores en tu código.")

except Exception as e:
    print(f"\n❌ Error al listar modelos: {e}")
    print("\n💡 Sugerencia: Verifica que tu API Key sea válida y tenga acceso a Google AI Studio.")
    print("   Puedes obtener una llave en: https://aistudio.google.com/app/apikey")
