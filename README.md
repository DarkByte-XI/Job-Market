# Job Market

Centralisation et recommandation d’offres d’emploi multicanal.

Ce projet vise à agréger, nettoyer et proposer des offres d’emploi issues de plusieurs sources externes (France Travail, Adzuna, JSearch) et à les exposer via une API de recherche/recommandation performante, utilisable en usage interne ou pour prototypage de projets data RH.

---

## Sommaire

- [Présentation](#présentation)
- [Architecture générale](#architecture-générale)
- [Prérequis](#prérequis)
- [Installation](#installation)
- [Configuration et variables d'environnement (.env)](#configuration-et-variables-denvironnement-env)
- [Création et initialisation de la base de données PostgreSQL](#création-et-initialisation-de-la-base-de-données-postgresql)
- [Base de données SQL et triggers](#base-de-données-sql-et-triggers)
- [Lancement](#lancement)
- [Pipeline ETL](#pipeline-etl)
    - [1. Extraction](#1-extraction)
    - [2. Transformation et normalisation](#2-transformation-et-normalisation)
    - [3. Chargement (optionnel)](#3-chargement-optionnel)
- [Structure des données](#structure-des-données)
- [API FastAPI](#api-fastapi)
    - [Endpoints](#endpoints)
    - [Exemples d’utilisation](#exemples-dutilisation)
- [Ressources et dictionnaires](#ressources-et-dictionnaires)
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
- PosgreSQL
- requirements.txt

---


## Installation

1. Cloner le dépôt
```bash
git clone <https://github.com/DarkByte-XI/Job-Market.git>
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

--- 


## Configuration et variables d'environnement (.env)

Pour sécuriser et centraliser la configuration sensible (identifiants d’API, clés secrètes, etc.), le projet utilise un fichier `.env` **non versionné**.

- Un modèle de configuration est fourni :  
  **`.env_copy`**  
  > Ce fichier contient toutes les variables attendues, mais sans valeur (ou avec des valeurs d’exemple).
Cette partie est importante pour initier les connexions avec les 
API et se connecter à la base de données
### Utilisation

1. **Copie le modèle** dans ton dossier racine :
    ```bash
    cp .env_copy .env
    ```

2. **Complète** le fichier `.env` avec tes propres identifiants :
    - Clés d’API pour France Travail, Adzuna, JSearch, etc.
    - Chemins de fichiers, settings personnalisés…
    - Exemple :
        ```
        # Identifiants API externes
        FRANCE_TRAVAIL_API_KEY=
        ADZUNA_APP_ID=
        ADZUNA_APP_KEY=
        JSEARCH_API_KEY=

        # Autres configurations
        LOG_LEVEL=INFO
        ```

3. **Ne partage jamais ton fichier `.env`**  
   Il contient des informations confidentielles (identifiants personnels, tokens…).

4. **Chargement automatique**  
   Les variables sont chargées dans l’application via une librairie telle que [`python-dotenv`](https://github.com/theskumar/python-dotenv) ou manuellement dans le code de configuration.

### Bonnes pratiques

- Le fichier `.env` **est ignoré par git** grâce à `.gitignore`.
- **Ne jamais commiter de clés réelles dans le repo !**
- Tu peux enrichir le `.env_copy` si de nouvelles variables sont ajoutées au projet.


---

## Création et initialisation de la base de données PostgreSQL

Pour activer l’audit, le reporting ou le stockage relationnel des offres, tu peux créer une base PostgreSQL dédiée.  
Les scripts SQL fournis dans le dossier `sql/` permettent de recréer l’intégralité du modèle, des indexes, triggers et vues.

### Étapes de création


1. **Installe PostgreSQL**

    - **Sur MacOS (recommandé) :**
      ```bash
      brew install postgresql
      brew services start postgresql
      ```
      *(Si Homebrew n’est pas installé, voir [https://brew.sh/](https://brew.sh/))*

    - **Sur Linux (Debian/Ubuntu) :**
      ```bash
      sudo apt update
      sudo apt install postgresql postgresql-contrib
      sudo service postgresql start
      ```

    - **Sur Windows :**
      Télécharger l’installateur officiel :  
      [https://www.postgresql.org/download/windows/](https://www.postgresql.org/download/windows/)

2. **Crée une base dédiée** (depuis un terminal) :
    ```bash
    createdb job_market_db
    ```

Une fois la base créée, il faut indiquer à l’application comment s’y connecter.

- Un fichier modèle de configuration est fourni :  
  **`src/db/config_example.py`**

- **À faire :**
1. **Copier le fichier** et le renommer en `config.py` dans le même dossier :
```bash
        cp src/db/config_example.py src/db/config.py
```

2. **Compléter les informations de connexion** dans le dictionnaire Python :
```python
DB_CONFIG = {
            "dbname": "job_market_db",
            "user": "mon_user",
            "password": "mon_password",
            "host": "localhost",
            "port": "5432"
        }
```

3. **Ne jamais versionner ce fichier** (il est déjà listé dans `.gitignore`).

- Ce fichier est utilisé par les scripts Python pour toute opération nécessitant un accès direct à la base PostgreSQL (insertion, requêtes, reporting, etc.).

> Si vous utilisez un IDE comme Pycharm ou VSCode, vous pouvez dès lors exécuter les fichiers .sql
> dans l'ordre (voir l'ordre dans [étape 4]()). Ensuite, vous pouvez passer directement à l'étape de [lancement](#lancement).
> Sinon, suivez les instructions qui suivent


3. **Connecte-toi à la base** :
    ```bash
    psql -d job_market_db
    ```

4. **Exécute les scripts SQL dans l’ordre suivant** (depuis `psql` ou avec un outil graphique) :
    ```sql
    \i sql/schema.sql
    \i sql/indexes.sql
    \i sql/triggers.sql
    \i sql/views.sql
    ```
    - Tu peux aussi utiliser `psql` en ligne de commande :
      ```bash
      psql -d job_market_db -f sql/schema.sql
      psql -d job_market_db -f sql/indexes.sql
      psql -d job_market_db -f sql/triggers.sql
      psql -d job_market_db -f sql/views.sql
      ```

5. **Vérifie la création des tables** :
    ```sql
    \dt
    ```
    - Tu dois voir apparaître les tables : `job_offers`, `companies`, `job_offers_log`, etc.

---

### Bonnes pratiques

- Utilise un utilisateur PostgreSQL avec un mot de passe robuste.
- Ne partage jamais ton accès en clair (cf. fichier `.env`).
- Les scripts peuvent être relancés si tu veux réinitialiser la structure ou mettre à jour des index/triggers.


## Lancement

1. Lancez l’API :
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

---

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
├── app.py # Streamlit app
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
Projet personnel développé et maintenu par [Dani CHMEIS]() & [Enzo Petrelluzi]().