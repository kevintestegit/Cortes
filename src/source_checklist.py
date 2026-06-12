import os


def build_source_checklist(input_video: str, watermark_count: int = 0) -> str:
    return f"""# Checklist de fonte

- Arquivo analisado: `{input_video}`
- Direitos de uso: confirme que voce tem autorizacao, licenca adequada ou permissao para transformar e postar este video.
- Marca d'agua detectada: {watermark_count} regiao(oes).
- Musica/sons de terceiros: confirme que o audio pode ser usado no YouTube Shorts.
- Transformacao aplicada: corte vertical, legenda, hook, efeitos, reacao e metadados proprios.
- Revisao manual: assista ao short final antes de postar.
"""


def write_source_checklist(content: str, reports_dir: str) -> str:
    os.makedirs(reports_dir, exist_ok=True)
    path = os.path.join(reports_dir, "source_checklist.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return path
