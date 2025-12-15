from datetime import timedelta
import re

import streamlit as st
import pandas as pd

XML_FILE_URL = "https://nabory.kprm.gov.pl/pls/serwis/app.xml"

regex_dokladnie = re.compile(r"(\d+\.?\d{0,2})")
regex_widelki = re.compile(r"od (\d+\.?\d{0,2}) do (\d+\.?\d{0,2})")
regex_od = re.compile(r"nie mniej niż (\d+\.?\d{0,2})")


def netto2brutto(n: float) -> float:
    return n * 1.37  # approximate


def clean_str(s: str) -> str:
    return (
        s.replace(" zł ", " ")
        .replace("netto", "")
        .replace("brutto", "")
        .replace(",", ".")
        .replace("  ", " ")
        .strip()
    )


def parse_salary(
    string: str,
) -> tuple[str | None, str | None, float | None, float | None]:
    salary = clean_str(string)
    if salary is None or salary == "":
        return (
            "brak",
            None,
            None,
            None,
        )
    elif "około" in salary:
        salary_numeric = pd.to_numeric(salary.replace("około ", ""))
        if "netto" in string:
            salary_numeric = netto2brutto(salary_numeric)
            salary_value_type = "brutto estymowany"
        else:
            salary_value_type = "brutto"
        return (
            "~",
            salary_value_type,
            salary_numeric,
            salary_numeric,
        )
    elif match := regex_widelki.match(salary):
        salary_numeric_lower = pd.to_numeric(match.group(1))
        salary_numeric_upper = pd.to_numeric(match.group(2))
        if "netto" in string:
            salary_numeric_lower = netto2brutto(salary_numeric_lower)
            salary_numeric_upper = netto2brutto(salary_numeric_upper)
            salary_value_type = "brutto estymowany"
        else:
            salary_value_type = "brutto"
        return (
            "od_do",
            salary_value_type,
            salary_numeric_lower,
            salary_numeric_upper,
        )
    elif match := regex_od.match(salary):
        salary_numeric = pd.to_numeric(match.group(1).replace("nie mniej niż ", ""))
        if "netto" in string:
            salary_numeric = netto2brutto(salary_numeric)
            salary_value_type = "brutto estymowany"
        else:
            salary_value_type = "brutto"
        return (
            "od",
            salary_value_type,
            salary_numeric,
            None,
        )
    elif match := regex_dokladnie.fullmatch(salary):
        salary_numeric = pd.to_numeric(match.group(1))
        if "netto" in string:
            salary_numeric = netto2brutto(salary_numeric)
            salary_value_type = "brutto estymowany"
        else:
            salary_value_type = "brutto"
        return (
            "=",
            salary_value_type,
            salary_numeric,
            salary_numeric,
        )
    else:
        raise NotImplementedError(f"Could not parse string: {salary}")


@st.cache_data(
    ttl=timedelta(hours=1),
    show_spinner=True,
    show_time=True,
)
def load_data():
    print(f"Downloading data from: {XML_FILE_URL}")
    df = pd.read_xml(
        XML_FILE_URL,
        xpath=".//oferta",
        parser="etree",
        dtype_backend="pyarrow",
    )
    df = df.drop(
        columns=[
            "action",
            "poledopis",
            "etykieta_wymiaretatu",
            "etykieta_liczba_stanowisk_pracy",
            "odpisz_na_oferte",
            "etykieta_charakter_pracy",
            "etykieta1",
            "dostepnosc",
            "etykieta2",
            "etykieta_niezbedne",
            "etykieta_staz",
            "etykieta_pozostale_wym_niezbedne",
            "etykieta_wym_pozadane",
            "pozadane_etykieta_staz",
            "etykieta_pozostale_wym_pozadane",
            "etykieta4",
            "poledodatkowetext2",
            "etykieta_termin_miejsce",
            "etykieta_inne_warunki",
            "etykieta_dane_osobowe_klauzula_informacyjna",
            "etykieta_wzory_oswiadczen",
        ]
    )
    # TODO: replace with smarter approach
    df["wymiaretatu"] = pd.to_numeric(
        (
            df["wymiaretatu"]
            .str.strip()
            .str.replace("pełny etat", "1")
            .str.replace(",", ".")
            .str.replace("1/1", "1")
            .str.replace("1/2", "0.5")
            .str.replace("1/5", "0.2")
            .str.replace("2/5", "0.4")
            .str.replace("3/5", "0.6")
            .str.replace("4/5", "0.8")
            .str.replace("1/8", "0.125")
            .str.replace("2/8", "0.25")
            .str.replace("1/4", "0.25")
            .str.replace("3/8", "0.375")
            .str.replace("4/8", "0.5")
            .str.replace("5/8", "0.625")
            .str.replace("6/8", "0.75")
            .str.replace("3/4", "0.75")
            .str.replace("7/8", "0.875")
        )
    )
    df["data_wprowadzenia"] = pd.to_datetime(df["data_wprowadzenia"])
    df["czas_ekspozycji"] = pd.to_datetime(df["czas_ekspozycji"])
    df["stanowisko"] = df["stanowisko"].str.strip()
    df["miejsce_wykonywania_pracy"] = df["miejsce_wykonywania_pracy"].str.strip()
    df["lokalizacja"] = df["lokalizacja"].str.strip()
    df["wynagrodzenie"] = df["wynagrodzenie"].str.strip()

    (
        df["widelki_typ"],
        df["brutto_netto"],
        df["wynagrodzenie_od"],
        df["wynagrodzenie_do"],
    ) = zip(*df["wynagrodzenie"].apply(parse_salary))
    df["widelki_typ"] = df["widelki_typ"].astype("string[pyarrow]")
    df["brutto_netto"] = df["brutto_netto"].astype("string[pyarrow]")
    df["wynagrodzenie_od"] = df["wynagrodzenie_od"].astype("double[pyarrow]")
    df["wynagrodzenie_do"] = df["wynagrodzenie_do"].astype("double[pyarrow]")
    return df


st.title("📊 Informacje zbiorcze o naborach KPRM")
st.write(
    "Na stronie [nabory.kprm.gov.pl/](https://nabory.kprm.gov.pl/) opublikowane są otwarte nabory na stanowiska w służbie cywilnej."
)
st.write("Poniżej kilka informacji zbiorczych.")

df = load_data()
number_of_offers = len(df.index)
total_number_of_offers = df["liczba_stanowisk_pracy"].sum()
offers_without_salary = len(df.loc[df["widelki_typ"] == "brak"].index)
total_offers_without_salary = df.loc[df["widelki_typ"] == "brak"][
    "liczba_stanowisk_pracy"
].sum()
max_date: str = df["data_wprowadzenia"].max().date().isoformat()
total_offers_lt_fte = df.loc[df["wymiaretatu"] < 1.0]["liczba_stanowisk_pracy"].sum()

st.metric(label="📅 Najnowsza data dodania ogłoszenia", value=max_date)
st.divider()
col1, col2 = st.columns(2)
col1.metric(label="📈 Liczba ogłoszeń", value=number_of_offers)
col2.metric(label="📈 Liczba stanowisk", value=total_number_of_offers)
col1.metric(
    label="💰️ Liczba ogłoszeń z podanym wynagrodzeniem",
    value=number_of_offers - offers_without_salary,
)
col2.metric(
    label="💰️ Liczba stanowisk z podanym wynagrodzeniem",
    value=total_number_of_offers - total_offers_without_salary,
)
col1.metric(
    label="🕒️ Liczba stanowisk w niepełnym wymiarze etatu",
    value=total_offers_lt_fte,
)
st.divider()

df["wynagrodzenie_kosz"] = pd.cut(
    x=df["wynagrodzenie_od"], bins=list(range(1_000, 21_000, 1_000))
)
hist = (
    df[["wynagrodzenie_kosz", "liczba_stanowisk_pracy"]]
    .groupby(by="wynagrodzenie_kosz", observed=False)
    .sum()
    .reset_index()
)
hist["wynagrodzenie_kosz"] = hist["wynagrodzenie_kosz"].map(str)
st.bar_chart(
    data=hist,
    x="wynagrodzenie_kosz",
    y="liczba_stanowisk_pracy",
    x_label="Kategoria dolnych widełek płacowych (zł)",
    y_label="Liczba stanowisk",
)

gte_10k = (
    df.loc[df["wynagrodzenie_od"] >= 10_000][
        [
            "wynagrodzenie",
            "stanowisko",
            "do_spraw",
            "nazwa_firmy",
            "komorka_organizacyjna",
            "miejsce_wykonywania_pracy",
            "wymiaretatu",
            "liczba_stanowisk_pracy",
            "url",
            "wynagrodzenie_od",
        ]
    ]
    .sort_values(by="wynagrodzenie_od", ascending=False)
    .drop(columns=["wynagrodzenie_od"])
    .rename(
        columns={
            "wynagrodzenie": "Wynagrodzenie",
            "stanowisko": "Stanowisko",
            "do_spraw": "Do spraw",
            "nazwa_firmy": "Nazwa jednostki",
            "komorka_organizacyjna": "Komórka organizacyjna",
            "miejsce_wykonywania_pracy": "Miejsce wykonywania pracy",
            "wymiaretatu": "Wymiar etatu",
            "liczba_stanowisk_pracy": "Liczba stanowisk",
        }
    )
)
st.write("Nabory z widełkami wynagrodzeń zaczynającymi się od 10 000")
st.dataframe(
    data=gte_10k,
    hide_index=True,
    column_config={
        "url": st.column_config.LinkColumn(disabled=True),
    },
)

top_locations = (
    df[["miejsce_wykonywania_pracy", "liczba_stanowisk_pracy"]]
    .groupby(by="miejsce_wykonywania_pracy")
    .sum()
    .sort_values(by="liczba_stanowisk_pracy", ascending=False)
    .reset_index()
    .rename(
        columns={
            "miejsce_wykonywania_pracy": "Miejsce wykonywania pracy",
            "liczba_stanowisk_pracy": "Liczba stanowisk pracy",
        }
    )[:10]
)
st.write("Top 10 miejsc")
st.dataframe(top_locations, hide_index=True)

st.divider()
st.write("Podgląd danych")
st.dataframe(
    data=df,
    hide_index=True,
    column_config={
        "url": st.column_config.LinkColumn(disabled=True),
    },
)
