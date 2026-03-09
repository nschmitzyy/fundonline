import streamlit as st
import pandas as pd
from supabase_client import supabase

import numpy as np
from keras.models import load_model
from PIL import Image, ImageOps

np.set_printoptions(suppress=True)

# Modell laden
model = load_model("keras_Model.h5", compile=False)
class_names = open("labels.txt", "r").readlines()

def predict_image(image):

    size = (224, 224)

    image = ImageOps.fit(image, size, Image.Resampling.LANCZOS)
    image_array = np.asarray(image)

    normalized_image_array = (image_array.astype(np.float32) / 127.5) - 1

    data = np.ndarray(shape=(1, 224, 224, 3), dtype=np.float32)
    data[0] = normalized_image_array

    prediction = model.predict(data)
    index = np.argmax(prediction)

    class_name = class_names[index][2:].strip()
    confidence_score = prediction[0][index]

    return class_name, confidence_score

st.title("🔎 Online Fundbüro")

menu = st.sidebar.selectbox(
    "Menü",
    ["Fundstück melden", "Verlust melden", "Alle Einträge"]
)

def upload_item(status):

    st.subheader("Neuen Eintrag erstellen")

    title = st.text_input("Titel")
    description = st.text_area("Beschreibung")
    category = st.selectbox("Kategorie", ["Elektronik","Schlüssel","Tasche","Sonstiges"])
    location = st.text_input("Ort")

    if st.button("Speichern"):

        data = {
            "title": title,
            "description": description,
            "category": category,
            "location": location,
            "status": status
        }

        supabase.table("items").insert(data).execute()

        st.success("Eintrag gespeichert!")

def show_items():

    res = supabase.table("items").select("*").execute()
    df = pd.DataFrame(res.data)

    if len(df) > 0:
        st.dataframe(df)
    else:
        st.info("Keine Einträge vorhanden")

if menu == "Fundstück melden":
    upload_item("found")

elif menu == "Verlust melden":
    upload_item("lost")

elif menu == "Alle Einträge":
    show_items()
