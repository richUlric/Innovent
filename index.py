import streamlit as st
import pandas as pd
import plotly.express as px

# ---- CONFIGURATION ----
st.set_page_config(page_title="Tableau Croisé Dynamique", layout="wide")

# ---- LISTE DES COLONNES À SUPPRIMER ----
colonnes_a_supprimer = [
    "id", "created_at", "created_by_id", "updated_at", "updated_by_id",
    "part_id", "place_id", "purchase_id", "ref", "category_id",
    "image", "price_currency", "is_locally_bought",
    "obsolete", "resell_price", "resell_price_currency"
]

# ---- STYLE CSS ----
st.markdown("""
    <style>
        .main { background-color: #F0F2F6; }
        h1 { color: #004080; text-align: center; }
        .st-bw { color: #004080 !important; }
    </style>
""", unsafe_allow_html=True)

# ---- HEADER AVEC LOGO ----
st.image("logo.png", width=150)  # Remplace "logo.png" par le chemin du logo
st.title("📊 Tableau Croisé Dynamique")

# ---- SIDEBAR ----
st.sidebar.header("📂 Importer un fichier Excel")
uploaded_file = st.sidebar.file_uploader("Choisissez un fichier", type=["xlsx", "xls"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)

    # ---- SUPPRESSION DES COLONNES ----
    df = df.loc[:, ~df.columns.duplicated(keep="first")]
    df = df.loc[:, ~df.columns.str.startswith(tuple(colonnes_a_supprimer))]
    df.drop(columns=[col for col in colonnes_a_supprimer if col in df.columns], inplace=True)

    st.sidebar.success("✅ Fichier chargé avec succès")

    # ---- FILTRES DYNAMIQUES ----
    st.sidebar.header("🔎 Filtres dynamiques")
    filter_columns = st.sidebar.multiselect("🔎 Sélectionnez les colonnes à filtrer", df.columns)

    filtered_df = df.copy()
    selected_filters = {}

    for col in filter_columns:
        unique_values = filtered_df[col].dropna().unique().tolist()
        unique_values.sort()

        with st.sidebar.expander(f"🎯 Filtrer '{col}'", expanded=True):
            search_term = st.text_input(f"🔍 Rechercher dans {col}", key=f"search_{col}")
            
            # Filtrer les valeurs affichées selon la recherche
            filtered_values = [val for val in unique_values if search_term.lower() in str(val).lower()]
            
            select_all = st.checkbox("Tout sélectionner", key=f"all_{col}", value=True)
            
            selected_values = filtered_values.copy() if select_all else []
            
            for val in filtered_values:
                checked = st.checkbox(str(val), key=f"{col}_{val}", value=select_all)
                if checked:
                    selected_values.append(val)

        if selected_values:
            selected_filters[col] = selected_values
            filtered_df = filtered_df[filtered_df[col].isin(selected_values)]

    # ---- MISE À JOUR DES OPTIONS DISPONIBLES ----
    def get_filtered_options(col):
        if col in selected_filters:
            return selected_filters[col]
        return filtered_df[col].dropna().unique().tolist()

    if len(df.columns) < 2:
        st.error("❌ Le fichier ne contient qu'une seule colonne. Impossible de générer un tableau croisé dynamique.")

        st.subheader("📋 Données importées")
        st.dataframe(df)

        col = df.columns[0]
        st.subheader(f"📊 Distribution de la colonne '{col}'")

        count_df = df[col].value_counts().reset_index()
        count_df.columns = [col, "Fréquence"]

        fig = px.bar(count_df, x=col, y="Fréquence", title=f"Distribution des valeurs dans '{col}'")
        st.plotly_chart(fig, use_container_width=True)
 
    else:
        # Prise des deux premières colonnes pour initialisation
        default_index_col = df.columns[0]
        default_columns_col = df.columns[1]

        index_col = st.sidebar.selectbox("📝 Sélectionnez l'index (lignes)", df.columns, index=0)
        columns_col = st.sidebar.selectbox("📊 Sélectionnez la colonne (colonnes)", df.columns, index=1)
        values_col = st.sidebar.selectbox("📈 Sélectionnez la valeur à agréger", df.columns)
        
        # Vérifier si la colonne de valeurs est numérique
        agg_function = "sum" if pd.api.types.is_numeric_dtype(df[values_col]) else "count"

        # ---- TABLEAU CROISÉ DYNAMIQUE ----
        filtered_df[index_col] = filtered_df[index_col].astype(str)
        filtered_df[columns_col] = filtered_df[columns_col].astype(str)

        if not pd.api.types.is_numeric_dtype(df[values_col]):
            filtered_df["count"] = 1
            values_col = "count"

        pivot_table = pd.pivot_table(filtered_df, values=values_col, index=index_col, 
                                    columns=columns_col, aggfunc=agg_function, fill_value=0)

        st.subheader("📊 Tableau Croisé Dynamique avec Filtres")
        st.dataframe(pivot_table)

        # ---- GRAPHIQUE INTERACTIF ----
        if not pivot_table.empty:
            st.subheader("📈 Graphique Interactif des Données")
            pivot_df = pivot_table.reset_index().melt(id_vars=[index_col], var_name=columns_col, value_name=values_col)

            fig = px.line(
                pivot_df, 
                x=index_col, 
                y=values_col, 
                color=columns_col,
                markers=True, 
                title=f"Évolution de '{values_col}' en fonction de '{index_col}'",
                labels={index_col: index_col, values_col: values_col, columns_col: columns_col},
                hover_name=columns_col, 
                hover_data={values_col: True, index_col: True, columns_col: True}
            )

            fig.update_layout(legend_title_text=columns_col, xaxis_tickangle=-45)
            fig.update_traces(mode="markers+lines", hoverinfo="all")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("⚠️ Aucun résultat à afficher après filtrage.")
