import logging
from colorama import Fore, Style, init
import os

init(convert=True)

# Configuration chemins des répertoires
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
LOGS_DIR = os.path.join(BASE_DIR, "logs")
os.makedirs(LOGS_DIR, exist_ok=True)  # Crée le dossier si inexistant

# Définition du fichier des logs
LOG_FILE = os.path.join(LOGS_DIR, "job_market.log")

# Configuration globale du logger
logging.basicConfig(level=logging.DEBUG,    # DEBUG en dev
                    format="%(asctime)s - %(levelname)s - %(message)s",
                    datefmt="%Y-%d-%m %H:%M:%S",
                    handlers=[logging.FileHandler(LOG_FILE, encoding="utf-8"),
                              logging.StreamHandler()])


LOG_COLORS = {
    "INFO": Fore.LIGHTGREEN_EX + Style.BRIGHT,
    "WARNING": Fore.LIGHTYELLOW_EX + Style.BRIGHT,
    "ERROR": Fore.RED + Style.BRIGHT,
    "CRITICAL": Fore.LIGHTRED_EX + Style.BRIGHT,
    "DEBUG": Fore.LIGHTBLUE_EX + Style.BRIGHT
}

# Définition des niveaux de logs avec couleurs
def info(message):
    logging.info(LOG_COLORS["INFO"] + message + Style.RESET_ALL)

def warning(message):
    logging.warning(LOG_COLORS["WARNING"] + message + Style.RESET_ALL)

def error(message):
    logging.error(LOG_COLORS["ERROR"] + message + Style.RESET_ALL)

def critical(message):
    logging.critical(LOG_COLORS["CRITICAL"] + message + Style.RESET_ALL)

def debug(message):
    logging.debug(LOG_COLORS["DEBUG"] + message + Style.RESET_ALL)
