import streamlit as st
import requests
from components.html_cards import render_offers_with_js

st.set_page_config(page_title="Recommandation d'offres d'emploi", layout="wide")

st.title("🔎 Recommandation d'offres d'emploi High Tech")
st.markdown(
    "Saisissez un mot-clé et la localisation souhaitée "
    "(ex : `data engineer à Bordeaux`, `product owner Paris`, etc.) "
    "pour afficher les offres recommandées."
)

# Injection CSS globale (pour st.markdown si besoin ailleurs)
st.markdown(
    """
    <style>
    /* Ajustement des boutons Streamlit */
    div.stButton > button {
      background-color: #1abc9c;
      color: white;
      border-radius: 8px;
      padding: 8px 16px;
      transition: background-color 0.2s;
    }
    div.stButton > button:hover {
      background-color: #16a085;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

query = st.text_input("Votre recherche", placeholder="Ex : Data Analyst à Paris")

if st.button("Rechercher") and query:
    try:
        resp = requests.get(
            "http://localhost:8000/search", params={"query": query}
        )
        resp.raise_for_status()
        results = resp.json()

        if not results:
            st.warning("Aucune offre trouvée avec ce mot-clé.")
        else:
            st.success(f"{len(results)} offre(s) recommandée(s) :")

            # 1) Grille en colonnes
            cols = st.columns(2)
            for idx, offer in enumerate(results):
                with cols[idx % len(cols)]:
                    st.markdown(
                        f"""
                        <div class="offer-card">
                          <div class="offer-title">{offer['title'].capitalize()}</div>
                          <div class="offer-company">🏢 {offer['company'].capitalize()}</div>
                          <div class="offer-footer">
                            📍 {offer['location'].capitalize()} ({offer['code_postal']})<br>
                            {f"💶 {offer['salary_min']} - {offer['salary_max']} €" if offer['salary_min'] else ""}
                          </div>
                          <a class="offer-link" href="{offer['url']}" target="_blank">Voir l’offre →</a>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

            # 2) Variante JS plus interactive
            st.markdown("---")
            st.subheader("Vue interactive (JS/HTML)")
            render_offers_with_js(results, height=600)

    except Exception as e:
        st.error(f"Erreur lors de la requête : {e}")

elif query:
    st.info("Appuyez sur 'Rechercher' pour afficher les offres.")