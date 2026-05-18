'''O código abaixo é um conjunto de testes para o cliente Liquipedia.
Ele inclui funções para testar a obtenção de metadados e conteúdo de uma página específica, 
usando o título da página definido em `TEST_PAGE_MD3`. O teste imprime os resultados no console,
incluindo informações sobre a página e os primeiros caracteres do conteúdo.'''



from config import TEST_PAGE_MD3
from liquipedia_client import LiquipediaClient

def print_separator():
    print("-" * 80)


def test_page_metadata(client, page_title):
    print_separator()
    print("Testando metadados da página...")
    print(f"Titulo da pagina é: {page_title}")

    metadata = client.get_page_metadata(page_title)

    if metadata is None:
        print("Pagina nao encontrada.")
        return
    
    print(f"Page ID: {metadata.get('pageid')}")
    print(f"Titulo: {metadata.get('title')}")
    print(f"Missing: {metadata.get('missing')}")
    print(f"Invalid: {metadata.get('invalid')}")


def test_page_content(client, page_title):
    print_separator()
    print("Testando conteudo da página...")
    print(f"titulo da pagina é: {page_title}")

    content = client.get_page_content(page_title)

    if content is None:
        print("Pagina nao encontrada.")
        return
    
    print(f"tamanho do conteudo: {len(content)} caracteres")
    print("Conteudo da pagina:")
    print(content[:1000])  # Imprime os primeiros 1000 caracteres do conteúdo


def main():
    client = LiquipediaClient()
    page_title = TEST_PAGE_MD3

    test_page_metadata(client, page_title)
    test_page_content(client, page_title)

    print_separator()
    print("Testes concluídos.")
    
    return True


if __name__ == "__main__":
    main()

