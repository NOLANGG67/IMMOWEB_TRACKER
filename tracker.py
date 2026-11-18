import csv
import re
import time
from datetime import datetime
from playwright.sync_api import sync_playwright

URLS = {
    "appartements": "https://www.immoweb.be/fr/recherche/appartement/a-louer/bruxelles/region?countries=BE",
    "maisons": "https://www.immoweb.be/fr/recherche/maison/a-louer/bruxelles/region?countries=BE"
}
FICHIER_CSV = "locations_bruxelles.csv"

def extraire_compteur(page, url):
    page.goto(url, wait_until="domcontentloaded", timeout=60000)
    
    # Accepter les cookies si la bannière apparaît
    try:
        page.locator("button#uc-btn-accept-banner").click(timeout=5000)
    except:
        pass

    time.sleep(3) # Laisser le temps au compteur dynamique de s'afficher

    # Tentative 1 : Chercher via le sélecteur d'en-tête de résultats d'Immoweb
    try:
        element = page.locator("h1.search-results-cluster__title, .classifieds-count").first
        texte = element.inner_text()
        match = re.search(r"([\d\s\u202f]+)", texte)
        if match:
            nombre_propre = re.sub(r"[^\d]", "", match.group(1))
            if nombre_propre:
                return int(nombre_propre)
    except:
        pass

    # Tentative 2 : Recherche de secours dans tout le texte de la page
    texte_page = page.inner_text("body")
    match = re.search(r"([\d\s\u202f]+)\s+(?:résultat|bien)", texte_page, re.IGNORECASE)
    if match:
        nombre_propre = re.sub(r"[^\d]", "", match.group(1))
        if nombre_propre:
            return int(nombre_propre)
            
    return None

def lancer_releve():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        nb_apparts = extraire_compteur(page, URLS["appartements"])
        time.sleep(3)
        nb_maisons = extraire_compteur(page, URLS["maisons"])

        browser.close()
        return nb_apparts, nb_maisons

def sauvegarder_donnee(apparts, maisons):
    maintenant = datetime.now()
    date_str = maintenant.strftime("%Y-%m-%d")
    heure_str = maintenant.strftime("%H:%M:%S")
    total = (apparts or 0) + (maisons or 0)

    try:
        with open(FICHIER_CSV, "r", encoding="utf-8") as f:
            fichier_existe = True
    except FileNotFoundError:
        fichier_existe = False

    with open(FICHIER_CSV, mode="a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not fichier_existe:
            writer.writerow(["date", "heure", "appartements", "maisons", "total_logements"])
        writer.writerow([date_str, heure_str, apparts, maisons, total])

if __name__ == "__main__":
    apparts, maisons = lancer_releve()
    print(f"Résultats lus -> Appartements: {apparts}, Maisons: {maisons}")
    if apparts is not None or maisons is not None:
        sauvegarder_donnee(apparts, maisons)
        print("Succès : Données enregistrées dans le CSV.")
    else:
        print("Erreur : impossible de lire les compteurs.")
