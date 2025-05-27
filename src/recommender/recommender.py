import os
import json
import glob
from sklearn.metrics.pairwise import cosine_similarity
from src.recommender.data_preparation import prepare_offer_data, text_normalization, vectorize_texts, transform_text
from src.pipelines.extract import BASE_DIR

# Définition du chemin complet du dossier processed_data
PROCESSED_DATA_DIR = os.path.join(BASE_DIR, "data/processed_data")


def compute_similarity(query_vector, offer_vectors):
    """
    Calcule la similarité cosinus entre le vecteur de la requête et les vecteurs d'offres.
    Renvoie un tableau de scores.
    """
    scores = cosine_similarity(query_vector, offer_vectors)
    return scores.flatten()


def get_latest_transformed_file(directory: str) -> str:
    """
    Récupère le dernier fichier transformed_{timestamp}.json dans le répertoire donné.
    """
    pattern = os.path.join(directory, "transformed_*.json")
    files = glob.glob(pattern)
    if not files:
        raise FileNotFoundError(f"Aucun fichier transformed trouvé dans le dossier {directory}")
    latest_file = max(files, key = os.path.getmtime)
    return latest_file


def load_processed_offers(file_path: str):
    """
    Charge les offres transformées depuis un fichier JSON.
    """
    with open(file_path, 'r', encoding = 'utf-8') as f:
        processed_offers = json.load(f)
    return processed_offers


def build_recommendation_engine_from_folder(folder_path: str,
                                            weight_title: int = 1,
                                            weight_location: int = 1,
                                            weight_description: int = 0):
    """
    Construit le moteur de recommandation à partir du dernier fichier JSON transformé
    trouvé dans le dossier donné.
    Chaque offre est prétraitée et les champs sont pondérés pour la vectorisation.

    Pour chaque offre, la pondération de la description est ajustée :
      - Si la description est présente, on utilise le poids passé en paramètre.
      - Sinon, on ne prend pas en compte ce champ (poids = 0).
    """
    latest_file = get_latest_transformed_file(folder_path)
    processed_offers = load_processed_offers(latest_file)

    combined_text_list = []
    for _offer in processed_offers:
        # Normalisation des données du fichier selon les règles de normalisation présentes dans data_preparation.py :
        data = prepare_offer_data(_offer)

        # Combination des champs pour obtenir une sortie composé de toutes les informations :
        current_weight_description = weight_description if data["description"] else 0
        combined_text = " ".join(
            [data["title"]] * weight_title +
            [data["location"]] * weight_location +
            [data["description"]] * current_weight_description
        )
        combined_text_list.append(combined_text)

    offers_vectorizer, processed_offer_vectors = vectorize_texts(combined_text_list)
    return processed_offers, offers_vectorizer, processed_offer_vectors, combined_text_list


def recommend_offers(user_input: str, offers_vectorizer, processed_offer_vectors, processed_offers: list, top_n=5,
                     score_threshold: float = 0.7):
    """
    Donne des recommandations d'offres basées sur l'input utilisateur.
    L'input est vectorisé et la similarité cosinus est calculée pour retourner
    uniquement les offres dont le score est supérieur ou égal au seuil défini.

    Si moins d'offres répondent au critère, seules celles-là seront retournées.
    """
    # Pré-traiter l'input utilisateur
    user_input_normalized = text_normalization(user_input)
    query_vector = transform_text(offers_vectorizer, user_input_normalized)
    scores = compute_similarity(query_vector, processed_offer_vectors)

    # On filtre uniquement les offres dont le score de similarité est au moins égal au seuil
    scored_offers = [(i, score) for i, score in enumerate(scores) if score >= score_threshold]

    # Trier par ordre décroissant de score
    scored_offers.sort(key = lambda x: x[1], reverse = True)

    # Extraire les indices pour les top n offres (si elles existent)
    top_indices = [i for i, score in scored_offers][:top_n]

    recommended_offers = [processed_offers[i] for i in top_indices]
    return recommended_offers


if __name__ == "__main__":
    # Utilisation du dossier processed_data défini via PROCESSED_DATA_DIR
    offers, vectorizer, offer_vectors, texts = build_recommendation_engine_from_folder(PROCESSED_DATA_DIR)

    # Requête utilisateur
    user_query = input("Chercher un job par intitulé de poste : \n -> ")
    recommendations = recommend_offers(user_query, vectorizer, offer_vectors, offers, top_n = 10)

    print("Offres recommandées :")
    for offer in recommendations:
        print(offer)
