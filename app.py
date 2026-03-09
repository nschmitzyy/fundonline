import streamlit as st
import numpy as np
import os
from PIL import Image, ImageOps
from keras.models import load_model
from supabase import create_client
import uuid

# --- KONFIGURATION & DB ---
try:
    SUPABASE_URL = st.secrets["SUPABASE_URL"]
    SUPABASE_KEY = st.secrets["eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InhidmZmeWxwdmpzZG1qdndqYWVqIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzI0NTkwOTAsImV4cCI6MjA4ODAzNTA5MH0.w6LZuXWts9jrhuv7h6KlBgGZnEySJKNqzXGNJwU_gCU"]
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
except Exception as e:
    st.error("Supabase Secrets fehlen! Bitte in .streamlit/secrets.toml oder Streamlit Cloud eintragen.")

# --- MODELL LADEN ---
@st.cache_resource
def load_ml_model():
    model_path = "keras_model.h5"
    label_path = "labels.txt"
    
    if not os.path.exists(model_path):
        st.error(f"❌ Datei '{model_path}' nicht gefunden!")
        return None, None
    
    # Laden mit Fehlerbehandlung
    try:
        model = load_model(model_path, compile=False)
        with open(label_path, "r") as f:
            labels = [line.strip() for line in f.readlines()]
        return model, labels
    except Exception as e:
        st.error(f"Fehler beim Laden des Modells: {e}")
        return None, None

model, class_names = load_ml_model()

# --- LOGIK ---
def detect_color(image):
    # Wir schauen uns nur die Mitte des Bildes an (50x50 Pixel)
    img = image.resize((100, 100))
    area = (25, 25, 75, 75)
    center_img = img.crop(area)
    img_array = np.array(center_img)
    avg_color = img_array.mean(axis=(0, 1))
    r, g, b = avg_color

    if r > g + 30 and r > b + 30: return "Rot"
    if g > r + 30 and g > b + 30: return "Grün"
    if b > r + 30 and b > g + 30: return "Blau"
    if r < 50 and g < 50 and b < 50: return "Schwarz"
    if r > 200 and g > 200 and b > 200: return "Weiß"
    return "Bunt/Andere"

def classify_image(img):
    size = (224, 224)
    image = ImageOps.fit(img, size, Image.Resampling.LANCZOS)
    image_array = np.asarray(image).astype(np.float32)
    normalized = (image_array / 127.5) - 1
    data = np.expand_dims(normalized, axis=0)

    prediction = model.predict(data)
    index = np.argmax(prediction)
    confidence = float(prediction[0][index])
    
    # Label sauber trennen (z.B. "0 T-Shirt" -> "T-Shirt")
    label = class_names[index]
    clean_label = label.split(" ", 1)[1] if " " in label else label
    
    return clean_label, confidence

# --- UI ---
st.set_page_config(page_title="KI Fundbüro", page_icon="🔍")
st.title("🔍 KI-Fundbüro")

menu = st.sidebar.radio("Navigation", ["Suchen", "Fund melden"])

if menu == "Fund melden":
    st.header("Neuen Fund registrieren")
    file = st.file_uploader("Foto machen oder hochladen", type=["jpg", "png", "jpeg"])
    
    if file and model:
        image = Image.open(file).convert("RGB")
        st.image(image, caption="Hochgeladenes Bild", width=300)
        
        if st.button("Analysieren & Speichern"):
            with st.spinner("KI arbeitet..."):
                item, conf = classify_image(image)
                color = detect_color(image)
                
                # Upload Logik
                file_name = f"{uuid.uuid4()}.jpg"
                file_bytes = file.getvalue()
                
                try:
                    supabase.storage.from_("images").upload(file_name, file_bytes)
                    url = supabase.storage.from_("images").get_public_url(file_name)
                    
                    supabase.table("items").insert({
                        "item": item,
                        "color": color,
                        "image_url": url
                    }).execute()
                    
                    st.success(f"Erfolgreich gespeichert: {color} {item} (Sicherheit: {conf:.1%})")
                except Exception as e:
                    st.error(f"Datenbankfehler: {e}")

elif menu == "Suchen":
    st.header("Gegenstand suchen")
    query = st.text_input("Was hast du verloren?")
    if query:
        res = supabase.table("items").select("*").ilike("item", f"%{query}%").execute()
        if res.data:
            cols = st.columns(2)
            for i, item in enumerate(res.data):
                with cols[i % 2]:
                    st.image(item["image_url"])
                    st.write(f"**{item['item']}** ({item['color']})")
        else:
            st.info("Nichts gefunden.")
