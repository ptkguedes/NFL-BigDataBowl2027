# NFL Big Data Bowl

Pipeline baseline local para a competicao NFL Big Data Bowl. O script le CSVs oficiais que ja estejam em disco e grava uma submissao com as colunas `game_id`, `play_id`, `nfl_id` e `prediction`.

Ele nao baixa dados da competicao e nao inventa linhas. Se `--input-dir` nao existir, estiver vazia, ou nao tiver arquivos reais (`player_play.csv` ou `tracking_week_*.csv`), o programa registra o erro e termina com codigo 1, sem criar o CSV de saida.

## Como rodar

Na pasta do projeto:

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python generate_baseline.py
```

- `--input-dir`: pasta dos CSVs da competicao. Padrao: `data`. O script nao cria essa pasta.
- `--output`: caminho do CSV de saida. Padrao: `submission.csv`. A gravacao e atomica (arquivo temporario no mesmo diretorio e, em seguida, substituicao).

Quando ha dados reais, cada linha e uma combinacao distinta de `game_id`, `play_id` e `nfl_id`, e `prediction` fica com o baseline constante `0`.
