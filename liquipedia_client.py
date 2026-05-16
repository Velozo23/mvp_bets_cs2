"""
Cliente HTTP para comunicação com a MediaWiki API da Liquipedia.

Objetivo:
- centralizar as chamadas para a API
- reaproveitar configuracoes do config.py
- manter a logica de acesso separada do parser
"""

import time

import requests

from config import (
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

