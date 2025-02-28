# Table des matières

- [Étape 1 : Récolte des données par API](#étape-1--récolte-des-données-par-API)


# Projet Job Market

- Nous allons regrouper des informations sur les offres d’emplois récupérées par API, et les compagnies qui les proposent.

- Notre objectif est d'analyser les offres liées aux métiers `Data Engineer` (DE), `Data Analyst` (DA) et `Data Scientist` (DS) :
  - évolution de la répartition des offres de ces 3 métiers
  - compétences les plus demandées (mots qui apparaissent le plus)
  - secteurs recrutant le plus
  - régions/villes les plus actives (avec carte de France de densité de recrutement)
  - top 20 des entreprises qui recrutent le plus
  - etc... (à compléter)


## Étape 1 : Récolte des données par API

### API de "France Travail"

- France Travail (https://francetravail.io/data/api) met à disposition plusieurs APIs pour récolter diverses données.

- Nous utilisons l'API "Offres d'emploi" (`GET https://api.francetravail.io/partenaire/offresdemploi`) qui proposent plusieurs endpoints :

  - Le endpoint `GET https://api.francetravail.io/partenaire/offresdemploi/v2/offres/search` nous permet de récupérer les offres d'emplois actuelles selon plusieurs paramètres dont :
    - le code des appellations ROME, codes récupérés à partir du endpoint `GET https://api.francetravail.io/partenaire/offresdemploi/v2/referentiel/appellations`

      ```json
      { "code": "38971",  "libelle": "Data analyst" },
      { "code": "38972",  "libelle": "Data scientist" },
      { "code": "404278", "libelle": "Data engineer" },
      ...
      ```

    - le code des pays, codes récupérés à partir du endpoint `GET https://api.francetravail.io/partenaire/offresdemploi/v2/referentiel/pays`

      ```json
      { "code": "01", "libelle": "France" },    // inclut les offres en France d'outre-mer
      { "code": "02", "libelle": "Allemagne" }, // les pays étrangers ne retournent malheureusement pas d'offres sur les métiers à analyser
      ...
      ```

    - le paramètre `range` qui limite les résultats à 150 offres par requête (status code `206` si une requête renvoie plus de 150 offres), sachant que le nombre d'offres maximum récupérables est de 3150 offres.
      - Ainsi, si une requête peut renvoyer 351 offres, il faut enchainer 3 requêtes pour obtenir toutes les offres :
        - une première requête pour les offres `0-149` (status code 206),
        - une deuxième requête pour les offres `150-299` (status code 206),
        - une troisième requête pour les offres `300-350` (status code 200)

    - note : les paramètres liés aux dates (`minCreationDate`, `maxCreationDate`, `publieeDepuis`) ne permettent pas d'obtenir des offres expirées (celles qui ont permis de recruter quelqu'un).


- Cet API nous retourne des offres sous forme de documents json avec beaucoup d'informations dont l'identifiant de l'offre, son intitulé, sa description, le lieu de travail, des informations sur l'entreprise et sur le contrat, les compétences demandées et l'expérience nécessaires, etc...

- Toutefois, l'API retourne aussi énormément d'offres sans lien avec le métier renseigné en paramètre (par exemple, une requête renseignant l'appellation "Data Engineer" peut renvoyer une offre telle que "Product Owner" car les termes "Data Engineer" peuvent être présents dans la description de l'offre d'emploi).

- Nous requêtons ainsi un maximum d'appellations ROME en utilisant les 29 appellations ayant un lien avec la data, ainsi que 32 autres appellations ayant un lien avec les métiers de la tech (dev, sécurité, devops), pour maximiser les chances d'obtenir le plus d'offres d'emploi ayant un lien avec les métiers DE, DA et DS.

  - En effet, des offres de "Data Engineer" peuvent être présentes en requêtant l'appellation "Data_Manager" par exemple.

- Nous obtenons finalement 61 fichiers json contenant toutes les offres d'emploi liés ou pas à la data, pour la France et DOM-TOM uniquement car France Travail ne renvoie quasiment pas d'offre d'emploi teintée data pour les autres pays.

  - Ces 61 fichiers json seront fusionnés dans un seul fichier json, avec nous supprimons les doublons. Ce fichier json sera notre jeu de données pour l'API de France Travail.


- Nous filtrerons toutes les offres à la prochaine étape.

- On notera que les offres d"emploi retournées peuvent provenir soit de France Travail, soit des "partenaires", par exemple ("CADREMPLOI', "DIRECTEMPLOI", "INDEED", etc...)

  <!-- - En effet, pour filtrer les offres de "Data Engineer", nous testons si l'intitulé d'une offre matche avec plusieurs regex définies dans le fichier `filtres_offres.yml`, et aussi si elle ne matche pas d'autres regex aussi présente dans le même fichier.

    - Par exemple, pour filtrer les offres DE, pour chaque offre, la chaîne de caractère d'un intitulé est mis en miniscule et les accents retirés, et nous gardons l'offre si l'intitulé matche la regex `(ing|eng)(.*?)(data|donnee)`, et si l'intitulé ne matche pas `scientist`.
        - Une offre dont l'intitulé est `Inginieur de donnees` sera vu comme une offre DE, malgré la typo involontaire du recruteur et déjà rencontré.
        - Une offre dont l'intitulé est `Ingénieur Data Scientist` ne sera pas vu comme une offre DE, car c'est en réalité une offre DS. -->




### API de "The Muse"

L'API `GET https://www.themuse.com/api/public/jobs` permet de récupérer les offres d'emploi sur 3 critères principales :
  - la catégorie du métier ("category")
    - par exemple : "Data and Analytics", "Data Science"
  - le niveau d'expérience requis pour l'offre ("level")
    - par exemple : "Entry Level", "Mid Level", "Senior Level"
  - la localisation ("location")
    - par exemple "Paris, France"
    - il y a près de 21 000 villes proposés, dont 409 villes françaises, que nous devons sélectionner pour la requête (ce qui fait une requête énorme)

Parmi les résultats, les offres de télétravail sont présentes (on veut les retirer ? sûrement oui).

Une requête donne au maximum 20 offres, nous faisons donc une requête initiale pour voir combien de requêtes sont nécessaires pour récupérer toutes les offres (clé "page_count" de la réponse).




### API "Adzuna"

Adzuna est une plateforme de recherche d'emploi qui propose une API permettant d'accéder à une large base de données d'annonces d'emploi à travers différents pays. Dans ce projet, l'API Adzuna est utilisée pour effectuer des recherches d'annonces d'emploi en fonction de critères spécifiques tels que des mots-clés, un lieu géographique, et des exclusions (ex. "freelance", "stagiaire", etc.). L'API prend également en charge la pagination pour récupérer plusieurs pages de résultats.

### Configuration
Pour utiliser l'API Adzuna, les informations suivantes sont nécessaires :
- **App ID** et **App Key** : Ces identifiants doivent être obtenus en s'inscrivant sur le [portail développeur d'Adzuna](https://developer.adzuna.com/).
- **Pays pris en charge** : Les recherches peuvent être effectuées par pays via leur code ISO 3166 (ex : `fr` pour la France, DOM-TOM inclus, `us` pour les États-Unis).
Voir la liste des pays disponibles dans le paramètre [country](https://developer.adzuna.com/activedocs#!/adzuna/search)

### Fonctionnalités implémentées
- **Recherche personnalisée** : Récupération d'annonces selon des critères définis (mots-clés, exclusions, etc.).
- **Pagination** : Extraction automatique des annonces sur plusieurs pages.
- **Enregistrement JSON** : Les résultats sont sauvegardés sous forme de fichiers JSON et incluent le nombre total d'annonces par fichier.
  - Chaque fichier de sortie correspond au nom de la requête et est enregistré sous le format ***jobs_{query}***. Pour une requête de recherche d'offre d'emploi en tant que consultant digital par exemple,
le fichier généré est ***jobs_consultant_digital.json***
  - Un fichier de consolidation contient toutes les offres d'emploi uniques si plusieurs requêtes sont utilisées, intitulé ***all_jobs_results.json***
  - Les requêtes avec en sortie aucun résultat sont enregistrées dans un fichier intitulé ***no_results_queries.json***. Une fonction est intégrée également pour retirer les termes 
  sans résultat de fichier des requêtes principales, ici ***job_keywords.json*** pour réduire les appels inutiles.
- **Inclusions & Exclusions** : L'API permet de réaliser des requêtes avec plusieurs termes recherchés et d'autres exclus pour affiner les résultats fournis à partir du
fichier ***job_keywords.json***.


### Exemple de critères de recherche :

```json
{
  "country": "fr",
  "query": "Data Engineer",
  "what_exclude": "freelance stagiaire stage alternance",
  "results_per_page": 50
}
```

#### **Attention** : Les requêtes et les exclusions sont gérées à partir du fichier intitulé ***job_keywords.json***. 
Le code a été mis à jour pour prendre en compte ces critères à partir du fichier directement.
Les clés ***"query"*** et ***"what_exclude"*** dans le bloc ci-dessus permettent de vulgariser le mode de fonctionnement.
Les exclusions sont bien séparées par un **espace**.

### Exemple de sortie du fichier combiné: 

```json
"total_count": 15720,
    "jobs": [
        {
            "id": "5003327854",
            "title": "Data Architect H/F",
            "company": "Limagrain",
            "location": "Pont-du-Château, Clermont-Ferrand",
            "location_area": [
                "France",
                "Auvergne-Rhône-Alpes",
                "Puy-de-Dôme",
                "Clermont-Ferrand",
                "Pont-du-Château"
            ],
            "description": "En tant qu'Architecte Data, vous préconisez les solutions techniques à mettre en oeuvre dans les projets nécessitant la collecte, le stockage ou l'utilisation de données. Vous intervenez sur de nombreux projets et mettez en place des solutions génériques pour faciliter le travail des équipes de développeurs. Les solutions préconisées permettent le suivi opérationnel et financier. En tant que Data Architect, vous serez en charge de : L'architecture Data : - Vous préconisez des solutions techniqu…",
            "salary_min": null,
            "salary_max": null,
            "redirect_url": "https://www.adzuna.fr/land/ad/5003327854?se=tOTtLOLS7xGXDUlWOH7jYQ&utm_medium=api&utm_source=32ef67cb&v=B994F4E8C765CCD3A51365F570BF71BDD41A2EFD",
            "longitude": 3.22038,
            "latitude": 45.86958,
            "field": "Unknown"
        }

[...]
```
