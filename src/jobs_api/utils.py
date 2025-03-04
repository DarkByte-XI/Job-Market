import json
import os
import re

def save_to_json(data, filename, directory="."):
    """
    Sauvegarde les données dans un fichier JSON formaté dans un répertoire donné.

    :param data: Les données à écrire dans le fichier JSON.
    :param filename: Le nom du fichier de sortie.
    :param directory: Le répertoire où enregistrer le fichier.
    """
    try:
        # S'assurer que le répertoire existe
        if not os.path.exists(directory):
            os.makedirs(directory)

        # Construire le chemin complet du fichier
        filepath = os.path.join(directory, filename)

        # Écrire les données dans le fichier JSON
        with open(filepath, mode="w", encoding="utf-8") as file:
            json.dump(data, file, indent=4, ensure_ascii=False)

        print(f"Les données ont été sauvegardées dans le fichier '{filepath}'.\n")
        print("-" * 50)
    except Exception as e:
        print(f"Erreur lors de la sauvegarde dans le fichier JSON : {e}")
        print("-" * 50)


def sanitize_filename(filename) :
    """
    Nettoie un nom de fichier en supprimant ou remplaçant les caractères invalides afin
    d'avoir un format lisible et compatible.

    :param filename: Le nom de fichier à nettoyer.
    :return: Un nom de fichier valide.
    """

    # Nettoie et supprime les caractères invalides
    filename = re.sub(r'\s*/\s*', '_', filename)
    filename = re.sub(r'\s+', '_', filename)
    filename = re.sub(r'[\\:*?"<>|]', '', filename)

    return filename