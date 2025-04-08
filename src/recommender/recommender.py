import os
import json
import glob
from src.recommender.data_preparation import prepare_offer_data, text_normalization
from src.recommender.vectorization import vectorize_texts, transform_text
from src.recommender.similarity import compute_similarity, get_top_n_indices
from src.pipelines.extract import BASE_DIR


PROCESSED_DATA_DIR = os.path.join(BASE_DIR, "data/processed_data")

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
                                            weight_title: int = 2,
                                            weight_location: int = 1,
                                            weight_description: int = 3):
    """
    Construit le moteur de recommandation à partir du dernier fichier JSON transformé
    trouvé dans le dossier donné.
    Chaque offre est prétraitée et les champs sont pondérés pour la vectorisation.
    """
    latest_file = get_latest_transformed_file(folder_path)
    processed_offers = load_processed_offers(latest_file)

    combined_text_list = []
    for offers_ in processed_offers:
        # On suppose que dans le fichier transformé, les champs sont "title", "location" et "description"
        data = prepare_offer_data({
            "job_title": offers_.get("title", ""),
            "location": offers_.get("location", ""),
            "description": offers_.get("description", "")
        })
        # Construction du texte combiné en répétant chaque champ selon son poids
        combined_text = " ".join(
            ([data["job_title"]] * weight_title) +
            ([data["location"]] * weight_location) +
            ([data["description"]] * weight_description)
        )
        combined_text_list.append(combined_text)

    offers_vectorizer, processed_offer_vectors = vectorize_texts(combined_text_list)
    return processed_offers, offers_vectorizer, processed_offer_vectors, combined_text_list


def recommend_offers(user_input: str, offers_vectorizer, processed_offer_vectors, processed_offers: list[dict], top_n=5):
    """
    Donne des recommandations d'offres basées sur l'input utilisateur.
    L'input est vectorisé et la similarité cosinus est calculée pour retourner les offres les plus proches.
    """
    user_input_normalized = text_normalization(user_input)
    query_vector = transform_text(offers_vectorizer, user_input_normalized)
    scores = compute_similarity(query_vector, processed_offer_vectors)
    top_indices = get_top_n_indices(scores, top_n)
    recommended_offers = [processed_offers[i] for i in top_indices]
    return recommended_offers


if __name__ == "__main__":
    # Détermine le dossier processed_data à partir de la structure du projet
    base_dir = BASE_DIR
    processed_data_folder = os.path.join(BASE_DIR, PROCESSED_DATA_DIR)

    offers, vectorizer, offer_vectors, texts = build_recommendation_engine_from_folder(PROCESSED_DATA_DIR)

    # Requête utilisateur
    user_query = input(f"Chercher un job par intitulé de poste : \n -> ")
    recommendations = recommend_offers(user_query, vectorizer, offer_vectors, offers, top_n = 10)

    print("Offres recommandées :")
    for offer in recommendations:
        print(offer)
