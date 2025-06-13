import streamlit as st
import requests

st.set_page_config(page_title="Recommandation d'offres d'emploi", layout="wide")

st.title("🔎 Recommandation d'offres d'emploi")
st.markdown("Saisissez un mot-clé (ex : `data engineer`, `product owner`, etc.) pour afficher les offres recommandées selon l'API.")

query = st.text_input("Votre recherche", placeholder="Ex : data engineer")

if st.button("Rechercher") and query:
    try:
        # Adapter l'URL si besoin !
        resp = requests.get("http://localhost:8000/search", params={"query": query})
        resp.raise_for_status()
        results = resp.json()

        if not results:
            st.warning("Aucune offre trouvée avec ce mot-clé.")
        else:
            st.success(f"{len(results)} offre(s) recommandée(s) :")
            for offer in results:
                st.markdown(f"""
                <div style="border:1px solid #e2e2e2; padding:12px; border-radius:8px; margin-bottom:12px">
                <strong>{offer['title'].capitalize()}</strong> chez <em>{offer['company'].capitalize()}</em><br>
                📍 {offer['location'].capitalize()} ({offer['code_postal']})<br>
                {f"💶 {offer['salary_min']} - {offer['salary_max']} €" if offer['salary_min'] else ""}
                <br>
                <a href="{offer['url']}" target="_blank">Voir l'offre</a>
                </div>
                """, unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Erreur lors de la requête : {e}")

elif query:
    st.info("Appuyez sur 'Rechercher' pour afficher les offres.")