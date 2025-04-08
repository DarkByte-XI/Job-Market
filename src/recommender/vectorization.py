from sklearn.feature_extraction.text import TfidfVectorizer

def vectorize_texts(texts: list[str]):
    """
    Vectorise une liste de textes en utilisant TF-IDF.
    Renvoie le vectorizer et la matrice des vecteurs.
    """
    vectorizer = TfidfVectorizer()
    vectors = vectorizer.fit_transform(texts)
    return vectorizer, vectors

def transform_text(vectorizer, text: str):
    """
    Transforme un texte en son vecteur en utilisant le vectorizer existant.
    """
    return vectorizer.transform([text])
