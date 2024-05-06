

logs_base_path = "./logs"

from datetime import datetime
import logging
import os

# Nastavení logovací úrovně podle portu


from dotenv import load_dotenv
load_dotenv()


logs_base_path = "./logs"

def setup_logger(name: str):
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    # Vytvoření složky pro konkrétní router, pokud neexistuje
    log_path = os.path.join(logs_base_path, name)
    os.makedirs(log_path, exist_ok=True)
    
    # Aktuální datum pro název souboru
    today_date = datetime.now().strftime('%Y-%m-%d')
    log_filename = os.path.join(log_path, f"{today_date}.csv")

    # Kontrola existence souboru a vytvoření hlavičky CSV, pokud soubor neexistuje
    if not os.path.exists(log_filename):
        with open(log_filename, 'w') as file:
            file.write('Time,Logger Name,Level,Message,Line No\n')  # Přidána hlavička 'Line No'

    # Formát a handler pro logy
    formatter = logging.Formatter('%(asctime)s, %(name)s, %(levelname)s, %(message)s, %(lineno)d', datefmt='%Y-%m-%d %H:%M:%S')
    file_handler = logging.FileHandler(log_filename)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    return logger