# MVP Bets CS2

Projeto em desenvolvimento para coletar partidas de Counter-Strike 2 na
Liquipedia, transformar os dados em estruturas padronizadas e persistir os
resultados em SQLite.

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

Nesta fase, o MVP ja cobre o fluxo completo de coleta, parsing, validacao,
upsert e persistencia em SQLite. O projeto tambem mantem um catalogo local de
times e logos oficiais sincronizados pela API da Liquipedia.

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
- normalizacao avancada de datas e enriquecimento com outras fontes

## Arquivos Principais

### `config.py`

Centraliza configuracoes do projeto, como:

- endpoint da API da Liquipedia
- headers HTTP
- intervalos entre requisicoes
- paginas de teste
- paginas-alvo da coleta em `TARGET_PAGES`
- configuracoes do SQLite

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

### `validators.py`

Valida objetos `MatchSeries` e `MatchMap`.

Principais responsabilidades:

- identificar series sem times
- identificar series sem data bruta
- identificar series sem mapas
- identificar mapas sem nome ou status
- identificar mapas jogados sem placar
- identificar mapas finalizados empatados
- permitir que a coleta continue mesmo com warnings

### `database.py`

Camada de infraestrutura do SQLite.

Responsavel por:

- criar a pasta `data/`
- abrir conexoes com o banco
- criar as tabelas `match_series` e `match_maps`

### `repository.py`

Camada de persistencia dos dados.

Responsavel por:

- salvar `MatchSeries` em `match_series`
- salvar `MatchMap` em `match_maps`
- associar mapas com a serie usando `series_id`
- inserir novas series
- atualizar series ja existentes via upsert

O upsert atual usa como chave logica:

```text
page_title + team1_name + team2_name + match_datetime_raw
```

Quando uma serie ja existe, o repository atualiza os dados da serie, remove os
mapas antigos associados e insere novamente os mapas parseados no estado mais
recente.

### `team_repository.py`

Mantem o catalogo de times nas tabelas `teams` e `team_aliases`. Os aliases
preservam os nomes usados nas partidas (`navi`, `vit`, `tl`) e apontam para o
nome canonico retornado pela Liquipedia.

### `sync_team_logos.py`

Resolve os aliases em lote usando `TeamIcon` pela MediaWiki API, seleciona a
variante apropriada para dark mode e salva os arquivos em `data/team_logos/`.
Os metadados e a URL de origem ficam no SQLite; os binarios nao sao armazenados
no banco nem versionados pelo Git.

### `backfill_event_context.py`

Preenche `event_name` e `stage` para registros antigos a partir da página de
origem. As novas coletas já recebem esses campos diretamente no parser.

### `collect_matches.py`

Orquestrador principal do MVP.

Fluxo executado:

```text
LiquipediaClient
-> LiquipediaMatchParser
-> MatchValidator
-> MatchRepository
-> SQLite
```

As sementes manuais ficam em `TARGET_PAGES`, no `config.py`. A coleta tambem
descobre automaticamente eventos recentes das organizadoras configuradas em
`ORGANIZER_PAGE_PREFIXES`. Para isso, combina o catalogo tecnico
`Liquipedia:Tournaments` com os links renderizados de `Portal:Tournaments`.
Atualmente a descoberta cobre BLAST, ESL/IEM, Esports World Cup, PGL, CCT,
Circuit X e Circuit Stars, incluindo uma camada de subpaginas como Qualifier
e Playoffs.

### `inspect_database.py`

Carrega as tabelas SQLite em DataFrames pandas para facilitar a validacao dos
dados coletados.

O script exibe:

- total de series e mapas
- quantidade de series por campeonato
- partidas validas
- registros incompletos ou invalidos

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

### Rodar a coleta completa

```bash
./.venv/Scripts/python.exe ./collect_matches.py
```

### Sincronizar o catalogo e os logos dos times

```bash
./.venv/Scripts/python.exe ./sync_team_logos.py
```

O comando reutiliza logos existentes. Para baixar novamente todos os arquivos:

```bash
./.venv/Scripts/python.exe ./sync_team_logos.py --force
```

As consultas respeitam os intervalos configurados para a API, usam o
`User-Agent` identificado do projeto e mantem os resultados em cache local.
Times sem correspondencia continuam disponiveis para o frontend por meio do
fallback visual.

### Corrigir evento e fase de registros existentes

```bash
./.venv/Scripts/python.exe ./backfill_event_context.py
```

Para apenas conferir a quantidade de registros afetados:

```bash
./.venv/Scripts/python.exe ./backfill_event_context.py --dry-run
```

### Validar partidas e eventos contra a origem

```bash
./.venv/Scripts/python.exe ./validate_match_events.py
```

O relatório confirma cada registro pela combinação de times e data diretamente
na página oficial indicada em `page_title`, sem alterar o banco.

### Consultar contagem no SQLite

```bash
./.venv/Scripts/python.exe -c "from database import Database; db=Database(); conn=db.get_connection(); print(conn.execute('SELECT COUNT(*) FROM match_series').fetchone()[0]); print(conn.execute('SELECT COUNT(*) FROM match_maps').fetchone()[0]); conn.close()"
```

### Inspecionar o banco com pandas

```bash
./.venv/Scripts/python.exe ./inspect_database.py
```

A coleta usa as sementes configuradas em `TARGET_PAGES`:

```text
Esports_World_Cup/2026
CS_Asia_Championships/2026
Intel_Extreme_Masters/2026/Cologne/Stage_1
```

Essa lista e complementada pela descoberta automatica. Os catalogos, prefixos
de organizadoras, anos aceitos e profundidade maxima ficam configurados em
`DISCOVERY_CATALOG_PAGES`, `DISCOVERY_RENDERED_CATALOG_PAGES`,
`ORGANIZER_PAGE_PREFIXES`, `DISCOVERY_YEARS_BACK` e `DISCOVERY_MAX_DEPTH`.

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
- validacao de series e mapas
- criacao do banco SQLite
- persistencia de series e mapas
- orquestrador final de coleta
- upsert de series ja coletadas
- inspecao dos dados com pandas
- catalogo normalizado de times e aliases
- sincronizacao e cache local dos logos oficiais

Melhorias futuras:

- limpar registros fake usados durante testes manuais
- normalizar `match_datetime`
- criar testes automatizados com `pytest`
- ampliar suporte a outras estruturas da Liquipedia

## Observacoes

Este projeto ainda esta em fase de MVP e aprendizado incremental. Os scripts
`test_*.py` sao testes manuais de desenvolvimento, nao uma suite automatizada
com `pytest`.

A estrategia atual prioriza clareza e rastreabilidade antes de otimizar ou
generalizar demais o parser.

Ao rodar `collect_matches.py` mais de uma vez, o upsert evita inserir novamente
as mesmas series e atualiza os registros existentes com o estado mais recente
retornado pela Liquipedia.
