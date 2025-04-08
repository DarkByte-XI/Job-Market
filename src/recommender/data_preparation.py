import re
import unicodedata

def text_normalization(text: str) -> str:
    """
    Normalise le texte en supprimant les accents, en le passant en minuscules
    et en supprimant les caractères spéciaux.
    """
    if not text or not isinstance(text, str):
        return ""
    # Supprimer les accents
    text = unicodedata.normalize("NFD", text).encode("ascii", "ignore").decode("utf-8")
    # Mettre en minuscules
    text = text.lower()
    # Supprimer les caractères non alphanumériques (sauf espaces)
    text = re.sub(r"[^a-z0-9\s]", "", text)
    # Supprimer les espaces multiples
    text = re.sub(r"\s+", " ", text)
    return text.strip()

def prepare_offer_data(offer: dict) -> dict:
    """
    Prépare et nettoie les données d'une offre d'emploi.
    On normalise l'intitulé, la localisation et la description.
    """
    prepared = {
        "job_title": text_normalization(offer.get("job_title", "")),
        "location": text_normalization(offer.get("location", "")),
        "description": text_normalization(offer.get("description", "")),
    }
    return prepared
