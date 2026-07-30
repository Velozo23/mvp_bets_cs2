"""
Arquivo de configuração central do MVP.

Objetivo:
- concentrar constantes e parâmetros usados pelo cliente da API,
  pelo parser e pela persistência futura.
- evitar valores mágicos espalhados pelo projeto.
"""


# BLOCO 1: CONFIGURACOES GERAIS DO PROJETO
PROJECT_NAME = "mvp-cs2-matches"
ENVIRONMENT = "development"
DATA_SOURCE = "liquipedia"
DEFAULT_TIMEZONE = "UTC"
DEFAULT_ENCODING = "utf-8"

# BLOCO 2: CONFIGURACOES DA API DA LIQUIPEDIA
LIQUIPEDIA_WIKI = "counterstrike"
API_BASE_URL = "https://liquipedia.net"
API_ENDPOINT = "https://liquipedia.net/counterstrike/api.php"
API_RESPONSE_FORMAT = "json"
HUMAN_PAGE_BASE_URL = "https://liquipedia.net/counterstrike"

# BLOCO 3: HEADERS HTTP
USER_AGENT = "mvp-cs2-matches/0.1 (contato: felipe_velozo@hotmail.com)"
HTTP_ACCEPT = "application/json"
HTTP_ACCEPT_ENCODING = "gzip"
DEFAULT_HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept": HTTP_ACCEPT,
    "Accept-Encoding": HTTP_ACCEPT_ENCODING,
}

# BLOCO 4: LIMITES E CONTROLE DE REQUISICOES
API_TIMEOUT_SECONDS = 10
REQUEST_INTERVAL_SECONDS = 2
PARSE_REQUEST_INTERVAL_SECONDS = 30
MAX_RETRY_ATTEMPTS = 3
RETRY_BACKOFF_SECONDS = 5

# BLOCO 5: PARAMETROS PADRAO DE CONSULTA
DEFAULT_ACTION = "query"
DEFAULT_FORMAT = "json"
DEFAULT_FORMAT_VERSION = "2"
DEFAULT_RVSLOTS = "main"
DEFAULT_RVPROP = "content"
DEFAULT_PROP = "revisions"

# BLOCO 6: TITULOS OU PAGINAS DE TESTE
TEST_PAGE_MD3 = "BetBoom/RUSH_B!_Summit/2026/Part_Three"
TEST_PAGE_OVERTIME = "Intel_Extreme_Masters/2026/Rio"
TEST_PAGE_MATCHES_PORTAL = "Liquipedia:Tournaments"
TEST_PAGE_URL = "https://liquipedia.net/counterstrike/Portal:Matches"

# BLOCO 6.1: PAGINAS-ALVO DA COLETA
TARGET_PAGES = [
    "CS_Asia_Championships/2026",
    "Intel_Extreme_Masters/2026/Cologne",
    "Intel_Extreme_Masters/2026/Cologne/Stage_1",
    "Intel_Extreme_Masters/2026/Cologne/Stage_2",
    "Intel_Extreme_Masters/2026/Cologne/Playoffs",
    "BLAST/Open/2026/Spring",
    "ESL/Pro_League",
    "Intel_Extreme_Masters",
    "PGL/2026",
    "CCT",
    "ESEA",
    "FISSURE",
    "Circuit_Stars",
]

# Catalogos tecnicos que listam torneios atuais. A pagina
# Liquipedia:Tournaments usa linhas no formato **Pagina/Evento|Nome|...
# em vez de links [[...]], por isso possui tratamento proprio no cliente.
DISCOVERY_CATALOG_PAGES = [
    "Liquipedia:Tournaments",
]

# Este portal e renderizado por templates. action=parse com prop=links expande
# essas tabelas e cobre circuitos que nem sempre aparecem no catalogo tecnico,
# especialmente CCT e qualificatorios.
DISCOVERY_RENDERED_CATALOG_PAGES = [
    "Portal:Tournaments",
]

# Prefixos aceitos na descoberta automatica. IEM pertence a ESL, mas usa um
# caminho proprio na Liquipedia. Mantemos as duas grafias de Circuit para
# cobrir a nomenclatura informada e a semente historica do projeto.
ORGANIZER_PAGE_PREFIXES = {
    "BLAST": ("BLAST/",),
    "ESL/IEM": ("ESL/", "Intel_Extreme_Masters/"),
    "PGL": ("PGL/",),
    "CCT": ("CCT/",),
    "Circuit X": ("Circuit_X/", "Circuit_Stars/"),
}

# Depois de encontrar um evento no catalogo, visita no maximo um nivel de
# subpaginas (Qualifier, Playoffs, Stage etc.).
DISCOVERY_MAX_DEPTH = 1
DISCOVERY_YEARS_BACK = 1

# BLOCO 7: CONFIGURACOES DE LOG
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"
DEBUG_MODE = True

# BLOCO 8: CONFIGURACOES DO BANCO PARA ETAPAS FUTURAS
DATABASE_DIR = "data"
DATABASE_FILENAME = "mvp_bets.sqlite3"
DATABASE_URL = "sqlite:///data/mvp_bets.sqlite3"
TEAM_LOGOS_DIR = "data/team_logos"
TEAM_LOGO_ATTRIBUTION = "Liquipedia"
