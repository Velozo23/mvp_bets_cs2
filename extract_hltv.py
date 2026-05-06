from bs4 import BeautifulSoup
import json
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium_stealth import stealth

url = "https://www.hltv.org/matches"

# --- Usando Selenium para carregar a página completa ---
# Configurações para rodar o Chrome em modo "headless" (sem interface gráfica)
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36")

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

# --- Aplica o "disfarce" no navegador ---
stealth(driver,
        languages=["en-US", "en"],
        vendor="Google Inc.",
        platform="Win32",
        webgl_vendor="Intel Inc.",
        renderer="Intel Iris OpenGL Engine",
        fix_hairline=True,
        )

driver.get(url)

soup = None
try:
    # 1. Tenta clicar no botão de aceitar cookies (se ele aparecer)
    try:
        cookie_button = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.ID, "CybotCookiebotDialogBodyButtonAccept"))
        )
        cookie_button.click()
        print("DEBUG: Botão de consentimento de cookies clicado.")
    except TimeoutException:
        print("DEBUG: Banner de cookies não encontrado ou já aceito.")

    # 2. Espera ATIVAMENTE até que PELO MENOS UMA PARTIDA (live ou upcoming) apareça
    print("DEBUG: Aguardando o carregamento das partidas (máx 10s)...")
    WebDriverWait(driver, 10).until(
    
        EC.presence_of_element_located((By.CSS_SELECTOR, ".matches-list"))
    )
    
    # print("DEBUG: Contêiner encontrado. Aguardando o carregamento das partidas dentro dele...")
    # # Agora, espera por um filho (uma partida) dentro do contêiner que acabamos de encontrar
    # WebDriverWait(matches_list_container, 10).until(
    #     EC.presence_of_element_located((By.CSS_SELECTOR, ".live-match, .upcoming-match"))
    # )

    print("DEBUG: Conteúdo carregado com sucesso. Extraindo dados...")
    soup = BeautifulSoup(driver.page_source, "html.parser")

except TimeoutException:
    print("ERRO CRÍTICO: A lista de partidas não foi encontrada. Salvando screenshot como 'debug_screenshot.png'")
    print("ERRO CRÍTICO: As partidas não foram carregadas a tempo. Salvando screenshot como 'debug_screenshot.png'")
    driver.save_screenshot("debug_screenshot.png")
finally:
    driver.quit() # Garante que o navegador seja sempre fechado

# --- Extração de dados via HTML (agora com o conteúdo completo) ---
matches = []
if soup:
    # 1. Extrair partidas AO VIVO
    live_matches_found = soup.select("div.live-match")
    print(f"DEBUG: Encontradas {len(live_matches_found)} partidas AO VIVO.")
    for live_match in live_matches_found:
        team_elements = live_match.select(".team-name .text")
        event_element = live_match.select_one(".event-name")
        if len(team_elements) == 2:
            team1 = team_elements[0].text.strip()
            team2 = team_elements[1].text.strip()
            event = event_element.text.strip() if event_element else "N/A"
            matches.append({"event": event, "team1": team1, "team2": team2, "time": "LIVE"})

    # 2. Extrair PRÓXIMAS partidas
    # CORREÇÃO: upcoming-match é uma tag <a>, não <div>
    upcoming_matches_found = soup.select("a.upcoming-match")
    print(f"DEBUG: Encontradas {len(upcoming_matches_found)} PRÓXIMAS partidas.")
    for upcoming_match in upcoming_matches_found:
        team_elements = upcoming_match.select(".match-team-name")
        time_element = upcoming_match.select_one(".match-time")
        event_element = upcoming_match.select_one(".match-event-name")

        if len(team_elements) == 2 and time_element:
            team1 = team_elements[0].text.strip() or "TBD"
            team2 = team_elements[1].text.strip() or "TBD"
            time_str = time_element.text.strip()
            event = event_element.text.strip() if event_element else "N/A"
            matches.append({"event": event, "team1": team1, "team2": team2, "time": time_str})

if not matches:
    print("\nAVISO: Nenhuma partida foi extraída, mesmo após o carregamento da página.")

print(matches)
