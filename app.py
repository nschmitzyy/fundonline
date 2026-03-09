import streamlit as st
import pandas as pd
from supabase_client import supabase

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
