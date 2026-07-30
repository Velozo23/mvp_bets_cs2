"""
Cliente HTTP para comunicação com a MediaWiki API da Liquipedia.

Objetivo:
- centralizar as chamadas para a API
- reaproveitar configuracoes do config.py
- manter a logica de acesso separada do parser
"""

import re
import time
from urllib.parse import urljoin

import requests

from config import (
    API_BASE_URL,
    API_ENDPOINT,
    API_TIMEOUT_SECONDS,
    DEFAULT_ACTION,
    DEFAULT_FORMAT,
    DEFAULT_FORMAT_VERSION,
    DEFAULT_HEADERS,
    DEFAULT_RVPROP,
    DEFAULT_RVSLOTS,
    PARSE_REQUEST_INTERVAL_SECONDS,
    REQUEST_INTERVAL_SECONDS,
    DEFAULT_PROP,
)


class LiquipediaClient:
    """
    Cliente responsavel por encapsular o acesso a MediaWiki API.

    Nesta etapa, o foco e apenas definir a interface principal
    do cliente e deixar claro quais responsabilidades ele tera.
    """

    def __init__(self):
        """
        Inicializa o cliente com configuracoes padrao da API.

        Tambem cria uma sessao HTTP reutilizavel e prepara o controle
        de tempo usado para respeitar o intervalo entre requisicoes.
        """
        self.endpoint = API_ENDPOINT
        self.headers = DEFAULT_HEADERS
        self.timeout = API_TIMEOUT_SECONDS
        self.interval = REQUEST_INTERVAL_SECONDS
        self.parse_interval = PARSE_REQUEST_INTERVAL_SECONDS
        self.session = requests.Session()
        self.last_request_time = None

    def get_page_content(self, page_title):
        """
        Busca o wikitexto bruto de uma pagina da Liquipedia.

        Esse e o metodo principal para o MVP, pois o parser de partidas
        deve trabalhar sobre o conteudo retornado por action=query.
        """
        params = self.build_query_params(page_title)
        data = self.request(params)
        pages = data.get("query", {}).get("pages", [])

        if not pages:
            return None
        
        page = pages[0]

        if page.get("missing"):
            return None
        
        revisions = page.get("revisions", [])

        if not revisions:
            return None

        revision = revisions[0]
        slots = revision.get("slots", {})
        main_slot = slots.get("main", {})
        content = main_slot.get("content")

        return content

    def get_page_metadata(self, page_title):
        """
        Busca metadados basicos de uma pagina.

        Serve para validar se a pagina existe e recuperar informacoes
        simples antes de tentar extrair o conteudo completo.
        """
        params = {
            "action": DEFAULT_ACTION,
            "format": DEFAULT_FORMAT,
            "formatversion": DEFAULT_FORMAT_VERSION,
            "titles": page_title,
            "prop": "info",
        }

        data = self.request(params)

        pages = data.get("query", {}).get("pages", [])

        if not pages:
            return None

        page = pages[0]

        metadata = {
            "pageid": page.get("pageid"),
            "title": page.get("title"),
            "missing": page.get("missing", False),
            "invalid": page.get("invalid", False),      
        }

        return metadata

    def parse_page_html(self, page_title):
        """
        Busca o HTML renderizado de uma pagina via action=parse.

        Esse metodo e secundario e deve ser usado apenas para inspecao
        ou casos em que o wikitexto bruto nao for suficiente.
        """
        params = self.build_parse_params(page_title)
        data = self.request(params, is_parse=True)

        parse_data = data.get("parse", {})
        text_data = parse_data.get("text")

        if isinstance(text_data, dict):
            return text_data.get("*")
        
        return text_data

    def get_page_links(self, page_title):
        """Retorna links internos depois da expansao dos templates da pagina."""
        params = {
            "action": "parse",
            "format": DEFAULT_FORMAT,
            "formatversion": DEFAULT_FORMAT_VERSION,
            "page": page_title,
            "prop": "links",
        }
        data = self.request(params, is_parse=True)
        links = data.get("parse", {}).get("links", [])
        return sorted({
            item.get("title", "").strip()
            for item in links
            if isinstance(item, dict) and item.get("title")
        })

    def build_query_params(self, page_title):
        """
        Monta os parametros da chamada action=query.

        Essa chamada busca as revisoes da pagina e retorna o conteudo
        bruto que sera usado pelo parser.
        """
        params = {
            "action": DEFAULT_ACTION,
            "format": DEFAULT_FORMAT,
            "formatversion": DEFAULT_FORMAT_VERSION,
            "titles": page_title,
            "prop": DEFAULT_PROP,
            "rvslots": DEFAULT_RVSLOTS,
            "rvprop": DEFAULT_RVPROP,
        }

        return params
    
    def build_parse_params(self, page_title):
        """
        Monta os parametros da chamada action=parse.

        Essa chamada retorna o HTML renderizado da pagina, usado como
        apoio para investigacao da estrutura da Liquipedia.
        """
        params = {
            "action": "parse",
            "format": DEFAULT_FORMAT,
            "formatversion": DEFAULT_FORMAT_VERSION,
            "page": page_title,
            "prop": "text",
        }

        return params

    def extract_candidate_pages(self, wikitext):
        """
        Extrai páginas candidatas a partir de um wikitexto da Liquipedia.

        O objetivo é encontrar links para páginas de eventos, estágios e
        resultados recentes sem exigir uma lista manual de URLs.
        """
        if not wikitext:
            return []

        candidates = set()

        # Catalogo tecnico da Liquipedia:
        # **BLAST/Bounty/2026/Summer|BLAST Bounty Summer 2026|iconfile=...
        for match in re.finditer(r"^\s*\*+\s*([^|\r\n]+)\|", wikitext, re.MULTILINE):
            raw_value = match.group(1).strip()
            if "/" in raw_value and not raw_value.startswith(
                ("Template:", "Category:", "File:", "User:")
            ):
                candidates.add(raw_value)

        for match in re.finditer(r"\[\[([^\]|]+)(?:\|[^\]]*)?\]\]", wikitext):
            raw_value = match.group(1).strip()
            if not raw_value:
                continue

            if raw_value.startswith(("Template:", "Category:", "File:", "User:")):
                continue

            if "/" not in raw_value and " " not in raw_value:
                continue

            candidates.add(raw_value)

        for match in re.finditer(r"https://liquipedia\.net/counterstrike/([^\s\]\)\"']+)", wikitext):
            raw_value = match.group(1).strip()
            if not raw_value:
                continue

            if raw_value.startswith(("Template:", "Category:", "File:", "User:")):
                continue

            candidates.add(raw_value)

        return sorted(candidates)

    def filter_organizer_pages(self, candidate_pages, organizer_prefixes, years_back=1):
        """Mantem eventos recentes pertencentes as organizadoras configuradas."""
        if not candidate_pages:
            return []

        prefixes = tuple(
            prefix.casefold()
            for values in organizer_prefixes.values()
            for prefix in values
        )
        current_year = time.localtime().tm_year
        accepted_years = {
            str(current_year - offset)
            for offset in range(max(0, years_back) + 1)
        }
        relevant = []

        for page in candidate_pages:
            normalized = page.replace(" ", "_").strip()
            if not normalized.casefold().startswith(prefixes):
                continue

            years = set(re.findall(r"(?:^|/)(20\d{2})(?:/|$)", normalized))
            if years and years.isdisjoint(accepted_years):
                continue

            relevant.append(normalized)

        return sorted(set(relevant))

    def filter_relevant_pages(self, candidate_pages):
        """
        Filtra páginas candidatas para manter apenas páginas de eventos
        e resultados relevantes para a coleta.
        """
        if not candidate_pages:
            return []

        relevant = []
        current_year = time.localtime().tm_year
        keywords = [
            r"(blast|esl|pgl|iem|major|championships|open|league|premier|spring|fall|summer|winter|cologne|masters)",
            r"(cct|esea|fissure|circuit|stars)",
        ]
        pattern = re.compile("|".join(keywords), re.IGNORECASE)
        season_pattern = re.compile(r"/(20\d{2}|season|spring|summer|fall|winter)", re.IGNORECASE)

        for page in candidate_pages:
            if page.startswith(("Template:", "Category:", "File:", "User:")):
                continue

            if page.startswith("Portal:"):
                continue

            if "/" not in page:
                continue

            if not pattern.search(page):
                continue

            has_recent_year = f"/{current_year}" in page or f"/{current_year - 1}" in page
            has_season_token = season_pattern.search(page) is not None

            if not has_recent_year and not has_season_token:
                continue

            relevant.append(page)

        return relevant

    def has_match_content(self, wikitext):
        """
        Verifica se um wikitexto parece conter blocos de partidas reais.
        """
        if not wikitext:
            return False

        if re.search(r"\{\{Match(?:\||list)", wikitext):
            return True

        if re.search(r"\|opponent1=.*\|opponent2=.*\|date=", wikitext, re.DOTALL):
            return True

        return False

    def request(self, params, is_parse=False):
        """
        Executa uma requisicao HTTP generica contra a API da Liquipedia.

        Centraliza headers, timeout, controle de intervalo, validacao
        de erro HTTP e conversao da resposta para JSON.
        """
        self.wait_before_request(is_parse=is_parse)

        response = self.session.get(
            self.endpoint,
            params=params,
            headers=self.headers,
            timeout=self.timeout,
        )

        self.last_request_time = time.time()

        response.raise_for_status()

        return response.json()

    def get_binary(self, url):
        """
        Baixa um arquivo binario respeitando o mesmo intervalo e User-Agent.

        Usado para manter em cache local imagens resolvidas pela API.
        """
        self.wait_before_request()
        response = self.session.get(
            urljoin(API_BASE_URL, url),
            headers=self.headers,
            timeout=self.timeout,
        )
        self.last_request_time = time.time()
        response.raise_for_status()
        return response


    def wait_before_request(self, is_parse=False):
        """
        Aguarda o tempo minimo entre chamadas para respeitar a API.

        Usa um intervalo normal para action=query e um intervalo maior
        para action=parse, que e uma chamada mais custosa.
        """
        interval = self.parse_interval if is_parse else self.interval

        if self.last_request_time is None:
            return

        current_time = time.time()
        elapsed_time = current_time - self.last_request_time
        remaining_time = interval - elapsed_time

        if remaining_time > 0:
            time.sleep(remaining_time)
