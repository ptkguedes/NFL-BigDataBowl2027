# NFL Big Data Bowl

Baseline local para a competicao NFL Big Data Bowl. O script le CSVs oficiais que ja estejam em disco e grava uma submissao com as colunas `game_id`, `play_id`, `nfl_id` e `prediction`.

Ele nao baixa dados da competicao e nao inventa linhas. Se a pasta de entrada nao existir, ou se nao houver arquivos reais (`player_play.csv` ou `tracking_week_*.csv` com `game_id`, `play_id` e `nfl_id`), o programa termina com erro e nao cria `submission.csv`.

## Como rodar

Na pasta do projeto:

```bash
pip install -r requirements.txt
python3 generate_baseline.py --input-dir data --output submission.csv
```

- `--input-dir`: pasta que ja contem os CSVs da competicao. O script nao cria essa pasta.
- `--output`: caminho do CSV de saida. A gravacao e atomica (arquivo temporario no mesmo diretorio e, em seguida, substituicao).

Quando ha dados reais, cada linha e uma combinacao distinta de `game_id`, `play_id` e `nfl_id`, e `prediction` fica com o baseline constante `0`.
