import streamlit as st
import pandas as pd

XML_FILE_URL = "https://nabory.kprm.gov.pl/pls/serwis/app.xml"

@st.cache_data
def load_data():
    df = pd.read_xml(
        XML_FILE_URL,
        xpath=".//oferta",
        parser="etree",
        dtype_backend="pyarrow",
    )
    df = df.drop(columns=["action", "poledopis", "etykieta_wymiaretatu", "etykieta_liczba_stanowisk_pracy", "odpisz_na_oferte", "etykieta_charakter_pracy", "etykieta1", "dostepnosc", "etykieta2", "etykieta_niezbedne", "etykieta_staz", "etykieta_pozostale_wym_niezbedne", "etykieta_wym_pozadane", "pozadane_etykieta_staz", "etykieta_pozostale_wym_pozadane", "etykieta4", "poledodatkowetext2", "etykieta_termin_miejsce", "etykieta_inne_warunki", "etykieta_dane_osobowe_klauzula_informacyjna", "etykieta_wzory_oswiadczen"])
    return df

st.title("📊 Informacje zbiorcze o naborach KPRM")
st.write(
    "Na stronie [nabory.kprm.gov.pl/](https://nabory.kprm.gov.pl/) opublikowane są otwarte nabory na stanowiska w służbie cywilnej."
)
st.write(
    "Poniżej kilka informacji zbiorczych."
)

df = load_data()
number_of_offers = len(df.index)
total_number_of_offers = df["liczba_stanowisk_pracy"].sum()

st.metric(label="Liczba ogłoszeń", value=number_of_offers)
st.metric(label="Liczba stanowisk", value=total_number_of_offers)

# ---
st.write("Podgląd danych")
st.dataframe(df)
