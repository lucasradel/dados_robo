import streamlit as st
import pandas as pd
import sqlite3
import altair as alt
import os

# Configuração da página
st.set_page_config(page_title="Dashboard SIH/SUS", layout="wide")

# Título
st.title("Dashboard de Produção SIH/SUS")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(BASE_DIR, 'baixados', 'producao_sih_playwright.csv')
DB_PATH = os.path.join(BASE_DIR, 'baixados', 'producao_sih.db')
TABLE_NAME = 'producao_sih'

# Conectar ao banco de dados
@st.cache_data
def load_data():
    if os.path.exists(DB_PATH):
        conn = sqlite3.connect(DB_PATH)
        df = pd.read_sql_query(f"SELECT * FROM {TABLE_NAME}", conn)
        conn.close()
    elif os.path.exists(CSV_PATH):
        df = pd.read_csv(CSV_PATH, sep=';', quotechar='"', engine='python')
    else:
        raise FileNotFoundError(
            f"Nenhum dado encontrado. Coloque o arquivo CSV em: {CSV_PATH} ou crie o banco em: {DB_PATH}."
        )

    # Limpar e converter colunas numéricas
    for col in ['Quantidade aprovada', 'Valor aprovado']:
        if col in df.columns:
            df[col] = df[col].astype(str).str.replace('.', '', regex=False).str.replace(',', '.', regex=False)
            df[col] = pd.to_numeric(df[col], errors='coerce')

    # Limpar período e converter para datetime
    if 'periodo' in df.columns:
        df['periodo'] = df['periodo'].astype(str).str.replace('\n', ' ', regex=False).str.strip()
        df['periodo_date'] = pd.to_datetime(df['periodo'], format='%b/%Y', errors='coerce')
    else:
        df['periodo_date'] = pd.NaT

    return df

try:
    df = load_data()
except Exception as error:
    st.error(str(error))
    st.stop()

# Sidebar para filtros
st.sidebar.header("Filtros")
municipios = st.sidebar.multiselect("Selecione Municípios", options=df['Município'].unique(), default=[])
periodos = st.sidebar.multiselect("Selecione Períodos", options=df['periodo'].unique(), default=[])

# Aplicar filtros
df_filtered = df.copy()
if municipios:
    df_filtered = df_filtered[df_filtered['Município'].isin(municipios)]
if periodos:
    df_filtered = df_filtered[df_filtered['periodo'].isin(periodos)]

# Abas
tab1, tab2, tab3 = st.tabs(["Lista de Dados", "Estatísticas Descritivas", "Gráficos"])

with tab1:
    st.header("Lista de Dados Armazenados")
    st.dataframe(df_filtered)

with tab2:
    st.header("Estatísticas Descritivas")
    st.write(df_filtered.describe())

with tab3:
    st.header("Gráficos")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Top 10 Municípios por Quantidade Aprovada")
        if not df_filtered.empty:
            top_municipios = df_filtered.groupby('Município')['Quantidade aprovada'].sum().nlargest(10).reset_index()
            chart = alt.Chart(top_municipios).mark_bar().encode(
                x=alt.X('Município:N', sort='-y'),
                y='Quantidade aprovada:Q',
                tooltip=['Município', 'Quantidade aprovada']
            ).properties(height=400)
            st.altair_chart(chart, use_container_width=True)
        else:
            st.write("Nenhum dado disponível com os filtros aplicados.")

    with col2:
        st.subheader("Top 10 Municípios por Valor Aprovado")
        if not df_filtered.empty:
            top_municipios_valor = df_filtered.groupby('Município')['Valor aprovado'].sum().nlargest(10).reset_index()
            chart = alt.Chart(top_municipios_valor).mark_bar().encode(
                x=alt.X('Município:N', sort='-y'),
                y='Valor aprovado:Q',
                tooltip=['Município', 'Valor aprovado']
            ).properties(height=400)
            st.altair_chart(chart, use_container_width=True)
        else:
            st.write("Nenhum dado disponível com os filtros aplicados.")

    st.subheader("Top 10 Municípios por Quantidade Aprovada (Pizza)")
    if not df_filtered.empty:
        top_municipios_pie = df_filtered.groupby('Município')['Quantidade aprovada'].sum().nlargest(10).reset_index()
        chart = alt.Chart(top_municipios_pie).mark_arc().encode(
            theta='Quantidade aprovada:Q',
            color='Município:N',
            tooltip=['Município', 'Quantidade aprovada']
        ).properties(height=400)
        st.altair_chart(chart, use_container_width=True)
    else:
        st.write("Nenhum dado disponível com os filtros aplicados.")

    st.subheader("Evolução da Quantidade Aprovada ao Longo do Tempo")
    if not df_filtered.empty and 'periodo_date' in df_filtered.columns:
        time_series = df_filtered.groupby('periodo_date')['Quantidade aprovada'].sum().reset_index()
        chart = alt.Chart(time_series).mark_line(point=True).encode(
            x='periodo_date:T',
            y='Quantidade aprovada:Q',
            tooltip=['periodo_date', 'Quantidade aprovada']
        ).properties(height=400)
        st.altair_chart(chart, use_container_width=True)
    else:
        st.write("Dados insuficientes para gráfico de tempo.")

    st.subheader("Evolução do Valor Aprovado ao Longo do Tempo")
    if not df_filtered.empty and 'periodo_date' in df_filtered.columns:
        time_series_valor = df_filtered.groupby('periodo_date')['Valor aprovado'].sum().reset_index()
        chart = alt.Chart(time_series_valor).mark_line(point=True).encode(
            x='periodo_date:T',
            y='Valor aprovado:Q',
            tooltip=['periodo_date', 'Valor aprovado']
        ).properties(height=400)
        st.altair_chart(chart, use_container_width=True)
    else:
        st.write("Dados insuficientes para gráfico de tempo.")

    st.subheader("Top 10 Municípios (Pizza) - Quantidade")
    if not df_filtered.empty:
        pie_data = df_filtered.groupby('Município')['Quantidade aprovada'].sum().nlargest(10).reset_index()
        chart = alt.Chart(pie_data).mark_arc().encode(
            theta='Quantidade aprovada:Q',
            color='Município:N',
            tooltip=['Município', 'Quantidade aprovada']
        ).properties(height=400)
        st.altair_chart(chart, use_container_width=True)
    else:
        st.write("Nenhum dado disponível.")

    st.subheader("Top 10 Municípios (Pizza) - Valor")
    if not df_filtered.empty:
        pie_data_valor = df_filtered.groupby('Município')['Valor aprovado'].sum().nlargest(10).reset_index()
        chart = alt.Chart(pie_data_valor).mark_arc().encode(
            theta='Valor aprovado:Q',
            color='Município:N',
            tooltip=['Município', 'Valor aprovado']
        ).properties(height=400)
        st.altair_chart(chart, use_container_width=True)
    else:
        st.write("Nenhum dado disponível.")
