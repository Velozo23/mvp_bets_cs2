# MVP Bets CS2

Projeto em desenvolvimento para coletar partidas de Counter-Strike 2 na
Liquipedia, transformar os dados em estruturas padronizadas e, nas proximas
etapas, persistir os resultados em SQLite.

O foco do MVP e extrair informacoes de series e mapas a partir do wikitexto
retornado pela MediaWiki API da Liquipedia.

## Objetivo

Construir um fluxo simples e rastreavel:

```text
Liquipedia API
-> wikitexto bruto
-> parser de series e mapas
-> modelos estruturados
-> validacao
-> SQLite
```

Nesta fase, o projeto ja cobre a coleta via API e boa parte do parser de
partidas.

## Escopo Do MVP

O MVP busca suportar:

- series bo1, bo3 e bo5
- mapas finalizados
- mapas marcados como `skip`
- placar de mapas sem overtime
- placar de mapas com overtime
- inferencia do vencedor do mapa
- inferencia do placar e vencedor da serie
- jogos futuros ou ainda sem times definidos como `TBD`

Fora do escopo imediato:

- odds
- estatisticas avancadas de jogador
- scraping direto do HTML publico
- integracao com outras fontes
- atualizacao incremental sofisticada

## Arquivos Principais

### `config.py`

Centraliza configuracoes do projeto, como:

- endpoint da API da Liquipedia
- headers HTTP
- intervalos entre requisicoes
- paginas de teste
- configuracoes futuras do SQLite

### `liquipedia_client.py`

Cliente responsavel por conversar com a MediaWiki API da Liquipedia.

Principais responsabilidades:

- montar parametros de consulta
- buscar metadados de paginas
- buscar wikitexto bruto com `action=query`
- buscar HTML renderizado com `action=parse`, quando necessario
- respeitar intervalo entre requisicoes
- centralizar headers, timeout e tratamento HTTP basico

### `models.py`

Define os modelos de dados usados pelo parser.

Modelos principais:

- `MatchSeries`: representa uma serie/partida completa
- `MatchMap`: representa um mapa dentro de uma serie

Esses modelos funcionam como contrato entre parser, validacao e persistencia.

### `liquipedia_parser.py`

Parser responsavel por transformar wikitexto da Liquipedia em objetos
estruturados.

Atualmente extrai:

- blocos de partidas
- time 1 e time 2
- data bruta da partida
- status da serie
- mapas da serie
- nome e status dos mapas
- placar normal
- placar com overtime
- vencedor do mapa
- tipo da serie (`bo1`, `bo3`, `bo5`)
- placar e vencedor da serie

### `test_liquipedia_client.py`

Script manual para validar a coleta via API.

Ele testa:

- metadados de uma pagina
- conteudo bruto retornado pela Liquipedia

### `test_liquipedia_parser.py`

Script manual para validar o parser em uma pagina real.

Ele busca uma pagina da Liquipedia, executa o parser e imprime um resumo das
series encontradas.

## Como Rodar

Os exemplos abaixo assumem terminal bash no VS Code em ambiente Windows.

### Testar o cliente da Liquipedia

```bash
./.venv/Scripts/python.exe ./test_liquipedia_client.py
```

### Testar o parser

```bash
./.venv/Scripts/python.exe ./test_liquipedia_parser.py
```

O teste do parser atualmente usa:

```text
CS_Asia_Championships/2026
```

Essa pagina foi escolhida por conter partidas ja finalizadas e partidas futuras,
o que ajuda a validar cenarios reais de campeonato em andamento.

## Exemplo De Saida Do Parser

```text
Total de series encontradas: 30

[1] falcons vs bc.game
Data: May 20, 2026 - 14:30 {{Abbr/CST}}
Serie: bo1 | Score: 1 x 0 | Winner: team1
  Map 1: Dust II | 13 x 11 | winner=team1 | OT=False
```

Para jogos ainda nao definidos, a saida usa valores amigaveis:

```text
TBD vs TBD
Map 1: TBD | status=not_played
```

## Status Atual

Concluido:

- configuracao central do projeto
- cliente da Liquipedia
- teste manual do cliente
- modelos `MatchSeries` e `MatchMap`
- parser de series
- parser de mapas
- calculo de placar com e sem overtime
- calculo de vencedor de mapa
- calculo de placar e vencedor da serie
- teste manual do parser com pagina real

Proximas etapas:

- criar `validators.py` para identificar dados incompletos ou inconsistentes
- criar camada SQLite (`database.py`)
- criar repositorio de persistencia (`repository.py`)
- criar orquestrador final de coleta (`collect_matches.py`)

## Observacoes

Este projeto ainda esta em fase de MVP e aprendizado incremental. Os scripts
`test_*.py` sao testes manuais de desenvolvimento, nao uma suite automatizada
com `pytest`.

A estrategia atual prioriza clareza e rastreabilidade antes de otimizar ou
generalizar demais o parser.
