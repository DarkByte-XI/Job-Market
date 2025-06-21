# render_jobs.py
import streamlit as st

def render_jobs(results, query):
    # 1) Structure HTML
    html = (
        '<div class="jobs-container">'
        f'  <div class="result-header">{len(results)} offres recommendées {query}</div>'
    )

    for o in results:
        tag_location = (
            f'<span class="tag1">📍 {o["location"]} - {o["code_postal"]}</span>'
        )
        tag_salary = (
            f'<span class="tag2">💶 {o["salary_min"]} - {o["salary_max"]} €/an</span>'
            if o.get("salary_min")
            else ""
        )

        html += (
            '<div class="job-card">'
            '  <div class="job-content">'
            '    <div class="job-top">'
            f'      <h3 class="job-title">{o["title"]}</h3>'
            f'      <div class="job-company">{o["company"]}</div>'
            '    </div>'
            '    <div class="job-tags">'
            f'      {tag_location}'
            f'      {tag_salary}'
            '    </div>'
            '    <div class="job-bottom">'
            f'      <a href="{o["url"]}" target="_blank" class="view-btn">Voir l’offre</a>'
            '    </div>'
            '  </div>'
            '</div>'
        )

    html += '</div>'

    # 2) Ne PAS utiliser components.html : on injecte directement
    st.markdown(html, unsafe_allow_html=True)