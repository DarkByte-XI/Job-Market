from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

def compute_similarity(query_vector, offer_vectors):
    """
    Calcule la similarité cosinus entre le vecteur de la requête et les vecteurs d'offres.
    Renvoie un tableau de scores.
    """
    scores = cosine_similarity(query_vector, offer_vectors)
    return scores.flatten()

def get_top_n_indices(scores, n=5):
    """
    Retourne les indices des n meilleures similarités.
    """
    return np.argsort(scores)[::-1][:n]
