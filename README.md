# Job Market

Centralisation et recommandation d’offres d’emploi multicanal.

Ce projet vise à agréger, nettoyer et proposer des offres d’emploi issues de plusieurs sources externes (France Travail, Adzuna, JSearch) et à les exposer via une API de recherche/recommandation performante, utilisable en usage interne ou pour prototypage de projets data RH.

---

## Sommaire

- [Présentation](#présentation)
- [Architecture générale](#architecture-générale)
- [Prérequis](#prérequis)
- [Installation & lancement](#installation--lancement)
- [Pipeline ETL](#pipeline-etl)
    - [1. Extraction](#1-extraction)
    - [2. Transformation et normalisation](#2-transformation-et-normalisation)
    - [3. Chargement (optionnel)](#3-chargement-optionnel)
- [Structure des données](#structure-des-données)
- [API FastAPI](#api-fastapi)
    - [Endpoints](#endpoints)
    - [Exemples d’utilisation](#exemples-dutilisation)
- [Ressources et dictionnaires](#ressources-et-dictionnaires)
- [Base de données SQL et triggers](#base-de-données-sql-et-triggers)
- [Organisation des fichiers](#organisation-des-fichiers)
- [Bonnes pratiques & sécurité](#bonnes-pratiques--sécurité)
- [FAQ / Limitations](#faq--limitations)
- [Auteurs](#auteurs)

---

## Présentation

**Job Market** est un projet interne de centralisation, d’analyse et de recommandation d’offres d’emploi issues de :
- **France Travail** (anciennement Pôle Emploi)
- **Adzuna** (API publique)
- **JSearch** (agrégateur d’offres d’emploi, issu de RapidAPI)

Le système permet de consolider les offres, de les nettoyer, de générer des fichiers d’offres enrichis, puis de proposer une API de recherche/recommandation rapide et fiable (FastAPI).

---

## Architecture générale

- **ETL Python** : Extraction, transformation et normalisation des offres multi-sources
- **Stockage** : Fichiers JSON dans `data/processed_data`
- **API** : Recherche et recommandation des offres via FastAPI (`/search`, `/companies`)
- **Ressources** : Dictionnaires métiers, pays, appellations, mots-clés pour enrichissement & recherche
- **SQL** : Scripts pour modéliser une base d’audit/offre, suivi de disponibilité via triggers, indexes optimisés

---

## Prérequis

- Python 3.10 ou supérieur (recommandé)
- **Packages** :  
    - `fastapi`
    - `uvicorn`
    - `scikit-learn`
    - `pydantic`
    - `requests` (pour les scripts d’appel API)
    - autres dans **requirements.txt**

Installe toutes les dépendances nécessaires :
```bash
pip install -r requirements.txt
```

---

## Installation & lancement

1. Cloner le dépôt
```bash
git clone <URL_DU_REPO>
cd Job_Market
```

2. Créez et activez un environnement virtuel :
```bash
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows
```

3. Installez les dépendances :
```bash
pip install -r requirements.txt
```

4. Exécutez le pipeline ETL pour générer les offres (voir section suivante).

5. Lancez l’API :
```bash
PYTHONPATH=src uvicorn API.main:app --reload
```
Accédez à la documentation interactive : http://localhost:8000/docs.

---

## Pipeline ETL

### 1. Extraction
Les scripts dans src/jobs_api/ extraient les offres depuis :
- France Travail : france_travail_api.py
- Adzuna : adzuna_api.py
- JSearch : jsearch_api.py


### 2. Transformation et normalisation
Les modules dans src/pipelines/ (extract.py, transform.py, load.py) :
- Extrait les données des différentes API
- Nettoient les données (accents, minuscules, etc.) via src/recommender/data_preparation.py ainsi que
via src/pipelines/transform.py pour le chargement en base de données.

### 3. Chargement (optionnel)
Les offres sont insérées dans une base SQL (voir section "Base de données SQL").
Par défaut, l’API fonctionne en mode "file-based" en lisant le dernier fichier JSON dans data/processed_data.

---

## Structure des données
### Fichiers principaux
- data/processed_data/transformed_*.json : Offres prêtes pour l’API.
- data/normalized/ : Données normalisées pour audit (optionnel). Cette option documentée dans src/recommender/recommender.py

### Champs des offres
- external_id : Identifiant unique (source externe).
- title : Intitulé du poste.
- company : Nom de l’entreprise.
- description : Description de l'offre si disponible
- location : Ville.
- code_postal : Code postal.
- salary_min, salary_max : Fourchettes salariales (float ou null).
- apply_url : URL de candidature.

## API FastAPI
L’API démarre en important le moteur de recommandation (TF-IDF, similarité cosinus) qui vectorise toutes les offres au démarrage :
**Aucune latence liée au chargement des fichiers à chaque requête.**

### Endpoints
#### 1. /search
Recherche d’offres d’emploi recommandées à partir d’une requête utilisateur.

**Requête** :
```bash
GET /search?query=data%20engineer
```

**Réponse** : liste d’offres structurées

```bash
[
  {
    "external_id": "5121612668",
    "title": "data engineer hf en alternance",
    "company": "openclassrooms",
    "location": "annecy",
    "code_postal": "74000",
    "salary_min": null,
    "salary_max": null,
    "url": "https://www.adzuna.fr/land/ad/5121612668?..."
  }
]
```
**Filtrage** : seules les offres avec un location et un code_postal sont retournées.

#### 2. /companies
Liste des entreprises distinctes extraites des offres.

**Requête**:
#### GET /companies

**Réponse** : liste d’entreprises
```bash
[
  {
    "id": "a9f5bb1c9c6e0e9b...",
    "name": "openclassrooms"
  }
]
```

L’id est un hash du nom (md5), le nom est unique.

### Exemples d’utilisation
#### - Recherche avancée : 
```bash
GET /search?query=product%20owner%20bordeaux
```
#### - Liste des entreprises : 
```bash
GET /companies
```

---

## Ressources et dictionnaires
### Dossier ressources/ :
- **appellations_code.json** : Codes métiers France Travail. 
- **data_appellations.json** : Appariement codes/intitulés pour métiers "data". 
- **job_keywords.json** : Mots-clés pour recherches Adzuna/JSearch. 
- **code_pays.json, communes_cp.csv** : Enrichissement des localisations.

---


## Base de données SQL et triggers
### Dossier sql/ :
- **schema.sql** : Modèle relationnel (tables offres, logs, etc.). 
- **indexes.sql** : Index pour optimiser les requêtes/jointures. 
- **triggers.sql** :
  - log_job_offers_changes() pour tracer les opérations (insert/update/delete) et vérifier la disponibilité des offres. 
- **views.sql** : Vues matérialisées pour analyses/reporting.

**Note** : La base SQL est optionnelle pour l’API, mais utile pour audit/traçabilité.

---

## Organisation des fichiers

```bash
Job_Market/
├── data/
│   ├── processed_data/
│   ├── normalized/
├── logs/
│   └── job_market.log
├── ressources/
├── src/
│   ├── API/
│   │   ├── schemas/
│   │   │   ├── job.py
│   │   │   ├── company.py
│   │   └── main.py
│   │   └── recommend.py
│   │   └── companies.py
│   ├── config/
│   │   ├── config_loader.py
│   │   ├── logger.py
│   ├── db/
│   │   ├── config.py
│   │   ├── db_connection.py
│   ├── jobs_api/
│   │   ├── adzuna_api.py
│   │   ├── france_travail.py
│   │   ├── jsearch_api.py
│   │   ├── utils.py
│   ├── pipelines/
│   │   ├── extract.py
│   │   ├── transform.py
│   │   ├── load.py
│   ├── recommender/
│   │   ├── data_preparation.py
│   │   ├── loader.py
│   │   ├── recommender.py
├── sql/
│       ├── indexes.sql
│       ├── schema.sql
│       ├── triggers.sql
│       ├── views.sql
├── .gitignore
├── requirements.txt
└── README.md
```

---

## Bonnes pratiques & sécurité
- Fichiers sensibles (clés, .env, logs) ignorés via .gitignore. 
- Dossiers de données ignorés sauf si .gitkeep est présent. 
- API 100% file-based, sans dépendance SQL, adaptée au prototypage. 
- Logs disponibles dans logs/job_market.log.

---


## FAQ / Limitations
- **Mise à jour des offres** : Non dynamique. Redémarrez l’API ou ajoutez un endpoint /reload. 
- **Scalabilité** : Adapté pour des datasets raisonnables (jusqu’à ~100k offres en RAM). 
- **Authentification** : Non implémentée (usage interne). Ajoutez un middleware si nécessaire. 
- **Recommandation** : Basée sur TF-IDF/similarité cosinus, sans IA avancée (embeddings).

---


## Auteurs
Projet personnel développé et maintenu par [Dani CHMEIS & Enzo Petrelluzi].