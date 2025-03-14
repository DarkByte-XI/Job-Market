import logging
from colorama import Fore, Style

# Configuration globale du logger
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Définition des niveaux de logs avec couleurs
def info(message):
    logging.info(Fore.GREEN + message + Style.RESET_ALL)

def warning(message):
    logging.warning(Fore.YELLOW + message + Style.RESET_ALL)

def error(message):
    logging.error(Fore.RED + message + Style.RESET_ALL)
