# Shorts Auto Cutter (MVP)

Um sistema local em Python para automatizar a geração de Shorts verticais (9:16) a partir de vídeos longos, focado em compilações de momentos engraçados, curiosos ou impressionantes.

## Funcionalidades da Versão 1

* **Detecção Automática:** Encontra os melhores cortes baseando-se em picos de áudio, movimento visual e mudanças de cena.
* **Ranking Viral:** Ranqueia os melhores momentos por potencial de viralização, hook, retenção, ação e áudio.
* **Renderização:** Converte automaticamente vídeos horizontais em verticais com crop inteligente, texto e contadores.
* **Reação do Papagaio:** Usa vídeos em `downloads/youtube/papagaio` na parte inferior do short, ocupando 30% da altura.
* **Suspense nas Trocas:** Adiciona um som curto nas trocas internas de cena/vídeo do corte. Se um short não tiver troca interna detectada, o som entra no meio do vídeo.
* **Efeitos por Tema:** Quando nenhum `--suspense-sound` é informado, o app escolhe um efeito local em `assets/sfx/` conforme o tema (`funny`, `fails`, `fishing`, `animals`, `money`).
* **Preset Viral:** O preset `funny` liga automaticamente legenda, papagaio, SFX, crop inteligente, hook visual e thumbnail.
* **Google Drive:** Copia os vídeos e relatórios para o Google Drive Desktop e pode apagar os MP4 locais após validar a cópia.
* **Cache de Análise:** Guarda informações de cada vídeo analisado para reaproveitar em execuções futuras.
* **Legendas Opcionais:** Transcreve o áudio e gera legendas automaticamente via `faster-whisper`.
* **Relatórios:** Gera arquivos `metadata.csv`, `metadata.json` e um `index.html` para fácil visualização e cópia de descrições/títulos.

## Limitações (MVP)

* Não remove marca d'água (apenas avisa no terminal). O sistema deve ser usado apenas com vídeos próprios ou autorizados.
* Não faz upload automático para YouTube/TikTok. A saída é salva no Google Drive local para revisão e postagem manual.
* Requer FFmpeg instalado no PATH.

## Pré-requisitos

1. **Python 3.11+**
2. **FFmpeg**
   * **Windows:** Baixe em [gyan.dev](https://www.gyan.dev/ffmpeg/builds/), extraia e adicione a pasta `bin` às variáveis de ambiente (PATH).
   * **Linux (Ubuntu/Debian):** `sudo apt install ffmpeg python3-tk`

> `python3-tk` é necessário para abrir o painel visual no Linux. Sem ele, a interface mostra uma mensagem de instalação e encerra.

## Instalação

1. Clone o repositório ou baixe a pasta.
2. Setup rapido:
   ```bash
   # Linux
   ./scripts/setup_linux.sh
   ./scripts/run_gui_linux.sh
   ```
   ```powershell
   # Windows PowerShell
   .\scripts\setup_windows.ps1
   .\scripts\run_gui_windows.ps1
   ```

Ou configure manualmente:

1. Crie um ambiente virtual (recomendado):
   ```bash
   python -m venv .venv
   # Windows
   .venv\Scripts\activate
   # Linux
   source .venv/bin/activate
   ```
2. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```

3. Instale dependências opcionais se for usar legendas automáticas ou ranking com IA:
   ```bash
   pip install -r requirements-optional.txt
   ```

*Nota: O `faster-whisper` é necessário para `--add-subtitles true`. O `openai` é necessário para `--use-llm-ranking true`.*

## Como Usar

Coloque seu vídeo na pasta `input/`, por exemplo: `input/meu_video.mp4`.

Execute o script principal:

```bash
python -m src.main --input input/meu_video.mp4 --preset funny --max-shorts 5
```

Ou abra o painel visual:

```bash
python app.py
```

Para gerar direto pela linha de comando apos o setup:

```bash
./scripts/run_preset_linux.sh input/meu_video.mp4 funny 5
```

```powershell
.\scripts\run_preset_windows.ps1 -InputVideo input\meu_video.mp4 -Preset funny -MaxShorts 5
```

No Windows, o painel usa automaticamente `.venv\Scripts\python.exe` quando existir. No Linux/macOS, usa `.venv/bin/python` quando existir.

### Parâmetros Suportados

* `--input` (Obrigatório): Caminho para o vídeo (ex: `input/video.mp4`).
* `--preset` (Opcional): Pacote de edição viral (`funny`, `fails`, `animals`, `football`). Padrão: `funny`. Use `none` para configurar tudo manualmente.
* `--max-shorts` (Opcional): Máximo de vídeos a gerar (padrão: 10).
* `--min-duration` (Opcional): Duração mínima em segundos (padrão: 18).
* `--max-duration` (Opcional): Duração máxima em segundos (padrão: 45).
* `--theme` (Opcional): Tema para geração de títulos (`funny`, `fishing`, `fails`). Padrão: `funny`.
* `--add-subtitles` (Opcional): `true` ou `false` (padrão: `false`).
* `--add-logo` (Opcional): `true` ou `false` (padrão: `true`). Se verdadeiro, busca uma logo em `assets/logo.png`.
* `--add-parrot` (Opcional): `true` ou `false` (padrão: `true`). Se verdadeiro, adiciona um vídeo de reação na parte inferior do short.
* `--parrot-dir` (Opcional): Pasta com vídeos do papagaio (padrão na interface: `downloads/youtube/papagaio`). A pasta `downloads/youtube` também é aceita como fallback.
* `--add-suspense` (Opcional): `true` ou `false` (padrão: `true`). Adiciona um som de suspense nas trocas internas de cena/vídeo do corte.
* `--suspense-sound` (Opcional): Caminho para um arquivo de som próprio (`.wav`, `.mp3`, `.aac`, `.m4a`, `.ogg` ou `.flac`). Se não for informado, o app tenta usar um efeito local de `assets/sfx/` conforme o tema; se não encontrar, o FFmpeg gera um tom curto automaticamente.
* `--suspense-volume` (Opcional): Volume do som de suspense de `0.0` a `1.0` (padrão: `0.45`).
* `--smart-crop` (Opcional): `true` ou `false` (padrão: `true`). Usa rosto/movimento para preencher o vídeo vertical com imagem nítida.
* `--blur-watermark` (Opcional): `true` ou `false` (padrão: `false`). Se ativado, borra regiões detectadas como marca d'água. Fica desligado por padrão para evitar borrar o vídeo inteiro.
* `--use-llm-ranking` (Opcional): `true` ou `false` (padrão: `false`). Usa OpenAI para reranquear candidatos se `OPENAI_API_KEY` estiver configurada.
* `--llm-model` (Opcional): modelo OpenAI para ranking (padrão: `gpt-4o-mini`).
* `--copy-to-drive` (Opcional): `true` ou `false` (padrão: `false`). Copia shorts e relatórios para o Google Drive Desktop.
* `--drive-output-dir` (Opcional): pasta de destino dentro do Drive. Se não informar, o app tenta detectar `G:\Meu Drive`, `G:\My Drive` ou pastas comuns.
* `--delete-local-after-drive` (Opcional): `true` ou `false` (padrão: `false`). Apaga os arquivos de mídia locais após uma cópia validada no Drive.
* `--use-cache` (Opcional): `true` ou `false` (padrão: `true`). Reaproveita análise anterior do mesmo arquivo.
* `--refresh-cache` (Opcional): `true` ou `false` (padrão: `false`). Ignora cache antigo e refaz a análise.
* `--add-hook` (Opcional): `true` ou `false` (padrão: `true`). Adiciona texto de hook nos primeiros segundos.
* `--generate-thumbnail` (Opcional): `true` ou `false` (padrão: `true`). Gera capas `.jpg` em `output/thumbnails/`.

### Exemplos

Gerar compilações de falhas, com duração entre 15 e 30 segundos, com legendas ativadas:
```bash
python -m src.main --input input/fails.mp4 --theme fails --min-duration 15 --max-duration 30 --add-subtitles true --max-shorts 3 --copy-to-drive true
```

## Estrutura de Saída

* `output/shorts/`: Área temporária com os vídeos renderizados e arquivos de legenda `.srt`/`.ass`.
* `output/reports/metadata.csv` e `.json`: Contém dados de start/end, notas e títulos de cada corte.
* `output/reports/index.html`: Dashboard visual com ranking viral, player embutido e botão para copiar títulos/hashtags.
* `output/reports/package_manifest.json`: Manifesto do pacote gerado, com preset, tema, pastas e relatório.
* `output/thumbnails/`: Capas JPG geradas automaticamente para cada short.
* `G:\Meu Drive\Shorts Auto Cutter\...`: destino padrão quando o Google Drive Desktop está montado. Cada execução cria uma pasta com `shorts/`, `reports/` e `drive_manifest.json`.
* `output/last_run.json`: aponta para o relatório mais recente, local ou no Drive.
* `output/cache/analysis/`: cache local das análises de vídeo. Pode ser apagado se você quiser forçar tudo do zero.

## Próximos Passos
* Adicionar suporte nativo à remoção/blur de marca d'água.
* Implementar IA avançada para reconhecimento de conteúdo (ex: GPT-4 Vision).
* Melhorar o ranking usando sinais reais de retenção dos vídeos já postados.
