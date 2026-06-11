# Shorts Auto Cutter (MVP)

Um sistema local em Python para automatizar a geração de Shorts verticais (9:16) a partir de vídeos longos, focado em compilações de momentos engraçados, curiosos ou impressionantes.

## Funcionalidades da Versão 1

* **Detecção Automática:** Encontra os melhores cortes baseando-se em picos de áudio, movimento visual e mudanças de cena.
* **Ranking:** Ranqueia os melhores momentos por potencial de retenção.
* **Renderização:** Converte automaticamente vídeos horizontais em verticais com fundo desfocado (*blur*), texto e contadores.
* **Legendas Opcionais:** Transcreve o áudio e gera legendas automaticamente via `faster-whisper`.
* **Relatórios:** Gera arquivos `metadata.csv`, `metadata.json` e um `index.html` para fácil visualização e cópia de descrições/títulos.

## Limitações (MVP)

* Não remove marca d'água (apenas avisa no terminal). O sistema deve ser usado apenas com vídeos próprios ou autorizados.
* Não faz upload automático para YouTube/TikTok. A saída deve ser revisada e postada manualmente.
* Requer FFmpeg instalado no PATH.

## Pré-requisitos

1. **Python 3.11+**
2. **FFmpeg**
   * **Windows:** Baixe em [gyan.dev](https://www.gyan.dev/ffmpeg/builds/), extraia e adicione a pasta `bin` às variáveis de ambiente (PATH).
   * **Linux:** `sudo apt install ffmpeg`

## Instalação

1. Clone o repositório ou baixe a pasta.
2. Crie um ambiente virtual (recomendado):
   ```bash
   python -m venv .venv
   # Windows
   .venv\Scripts\activate
   # Linux
   source .venv/bin/activate
   ```
3. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```

*Nota: O `faster-whisper` é opcional, mas necessário se você usar `--add-subtitles true`.*

## Como Usar

Coloque seu vídeo na pasta `input/`, por exemplo: `input/meu_video.mp4`.

Execute o script principal:

```bash
python -m src.main --input input/meu_video.mp4 --max-shorts 5
```

### Parâmetros Suportados

* `--input` (Obrigatório): Caminho para o vídeo (ex: `input/video.mp4`).
* `--max-shorts` (Opcional): Máximo de vídeos a gerar (padrão: 10).
* `--min-duration` (Opcional): Duração mínima em segundos (padrão: 18).
* `--max-duration` (Opcional): Duração máxima em segundos (padrão: 45).
* `--theme` (Opcional): Tema para geração de títulos (`funny`, `fishing`, `fails`). Padrão: `funny`.
* `--add-subtitles` (Opcional): `true` ou `false` (padrão: `false`).
* `--add-logo` (Opcional): `true` ou `false` (padrão: `true`). Se verdadeiro, busca uma logo em `assets/logo.png`.
* `--add-parrot` (Opcional): `true` ou `false` (padrão: `true`). Se verdadeiro, adiciona um vídeo de reação na parte inferior do short.
* `--parrot-dir` (Opcional): Pasta com vídeos do papagaio (padrão: `downloads/youtube`). A pasta `dowloads/youtube` também é aceita como fallback.
* `--add-suspense` (Opcional): `true` ou `false` (padrão: `true`). Adiciona um som de suspense nas trocas internas de cena/vídeo do corte.
* `--suspense-sound` (Opcional): Caminho para um arquivo de som próprio (`.wav`, `.mp3`, `.aac`, `.m4a`, `.ogg` ou `.flac`). Se não for informado, o FFmpeg gera um tom curto automaticamente.
* `--suspense-volume` (Opcional): Volume do som de suspense de `0.0` a `1.0` (padrão: `0.45`).
* `--smart-crop` (Opcional): `true` ou `false` (padrão: `true`). Usa rosto/movimento para preencher o vídeo vertical com imagem nítida.
* `--blur-watermark` (Opcional): `true` ou `false` (padrão: `false`). Se ativado, borra regiões detectadas como marca d'água. Fica desligado por padrão para evitar borrar o vídeo inteiro.
* `--use-llm-ranking` (Opcional): `true` ou `false` (padrão: `false`). Usa OpenAI para reranquear candidatos se `OPENAI_API_KEY` estiver configurada.
* `--llm-model` (Opcional): modelo OpenAI para ranking (padrão: `gpt-4o-mini`).
* `--upload-youtube` (Opcional): `true` ou `false` (padrão: `false`). Faz upload dos shorts gerados para o YouTube se `client_secrets.json` estiver configurado.
* `--youtube-privacy` (Opcional): `private`, `unlisted` ou `public` (padrão: `private`).

### Exemplos

Gerar compilações de falhas, com duração entre 15 e 30 segundos, com legendas ativadas:
```bash
python -m src.main --input input/fails.mp4 --theme fails --min-duration 15 --max-duration 30 --add-subtitles true --max-shorts 3
```

## Estrutura de Saída

* `output/shorts/`: Contém os vídeos renderizados e arquivos de legenda `.srt`.
* `output/reports/metadata.csv` e `.json`: Contém dados de start/end, notas e títulos de cada corte.
* `output/reports/index.html`: Um dashboard visual para você revisar os Shorts, com player embutido e botão para copiar os títulos e hashtags sugeridas.

## Próximos Passos
* Adicionar suporte nativo à remoção/blur de marca d'água.
* Implementar IA avançada para reconhecimento de conteúdo (ex: GPT-4 Vision).
* Integração nativa com APIs do YouTube Shorts e TikTok.
