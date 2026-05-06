"""
Cliente HTTP para comunicação com a MediaWiki API da Liquipedia.

Objetivo:
- centralizar as chamadas para a API
- reaproveitar configuracoes do config.py
- manter a logica de acesso separada do parser
"""

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
        self.endpoint = API_ENDPOINT
        self.headers = DEFAULT_HEADERS
        self.timeout = API_TIMEOUT_SECONDS
        self.interval = REQUEST_INTERVAL_SECONDS
        self.parse_interval = PARSE_REQUEST_INTERVAL_SECONDS
        self.session = requests.Session()
        self.last_request_time = None

    def get_page_content(self, page_title):
        """
        Buscar o conteudo bruto de uma pagina da Liquipedia.

        Responsabilidades futuras:
        - montar os parametros da chamada action=query
        - incluir prop=revisions
        - incluir rvslots e rvprop padrao
        - enviar requisicao para API_ENDPOINT
        - retornar payload JSON
        """
        pass

    def get_page_metadata(self, page_title):
        """
        Buscar metadados basicos da pagina.

        Pode ser util para:
        - validar se a pagina existe
        - recuperar informacoes gerais antes da extracao completa
        """
        pass

    def parse_page_html(self, page_title):
        """
        Buscar a pagina usando action=parse.

        Observacao:
        - esse metodo deve ser tratado como mais caro
        - deve respeitar o intervalo maior definido para parse
        - sera usado apenas quando realmente necessario
        """
        pass

    def build_query_params(self, page_title):
        
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
        Montar o conjunto de parametros da chamada action=parse.
        """
        pass

    def request(self, params):
        """
        Metodo generico para executar uma chamada na API.

        Responsabilidades futuras:
        - aplicar headers padrao
        - aplicar timeout
        - respeitar rate limit
        - tratar erros HTTP
        - converter resposta para JSON
        """
        pass

    def wait_before_request(self, is_parse=False):
        """
        Controlar o intervalo entre requisicoes.

        Se is_parse for True:
        - usar PARSE_REQUEST_INTERVAL_SECONDS

        Caso contrario:
        - usar REQUEST_INTERVAL_SECONDS
        """
        pass
