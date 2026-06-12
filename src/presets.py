from dataclasses import dataclass


@dataclass(frozen=True)
class ViralPreset:
    name: str
    theme: str
    min_duration: int
    max_duration: int
    add_subtitles: bool
    add_parrot_reaction: bool
    add_suspense: bool
    add_hook: bool
    smart_crop: bool
    suspense_volume: float


PRESETS = {
    "funny": ViralPreset(
        name="funny",
        theme="funny",
        min_duration=12,
        max_duration=28,
        add_subtitles=True,
        add_parrot_reaction=True,
        add_suspense=True,
        add_hook=True,
        smart_crop=True,
        suspense_volume=0.55,
    ),
    "fails": ViralPreset(
        name="fails",
        theme="fails",
        min_duration=10,
        max_duration=26,
        add_subtitles=True,
        add_parrot_reaction=True,
        add_suspense=True,
        add_hook=True,
        smart_crop=True,
        suspense_volume=0.65,
    ),
    "animals": ViralPreset(
        name="animals",
        theme="animals",
        min_duration=10,
        max_duration=28,
        add_subtitles=True,
        add_parrot_reaction=True,
        add_suspense=True,
        add_hook=True,
        smart_crop=True,
        suspense_volume=0.50,
    ),
    "football": ViralPreset(
        name="football",
        theme="football",
        min_duration=12,
        max_duration=30,
        add_subtitles=True,
        add_parrot_reaction=True,
        add_suspense=True,
        add_hook=True,
        smart_crop=True,
        suspense_volume=0.60,
    ),
    "podcast": ViralPreset(
        name="podcast",
        theme="podcast",
        min_duration=18,
        max_duration=45,
        add_subtitles=True,
        add_parrot_reaction=True,
        add_suspense=True,
        add_hook=True,
        smart_crop=True,
        suspense_volume=0.45,
    ),
    "curiosities": ViralPreset(
        name="curiosities",
        theme="curiosities",
        min_duration=14,
        max_duration=34,
        add_subtitles=True,
        add_parrot_reaction=True,
        add_suspense=True,
        add_hook=True,
        smart_crop=True,
        suspense_volume=0.50,
    ),
}

HOOK_TEXTS = {
    "funny": ["OLHA ISSO", "NAO TEM COMO", "QUE MOMENTO"],
    "fails": ["NAO DEU CERTO", "OLHA O FINAL", "QUE FALHA"],
    "animals": ["OLHA ESSE BICHO", "MUITO BOM", "REACTION REAL"],
    "football": ["QUE LANCE", "OLHA A JOGADA", "ABSURDO"],
    "podcast": ["PRESTA ATENCAO", "OLHA ESSA FALA", "ISSO AQUI E FORTE"],
    "curiosities": ["VOCE SABIA", "OLHA ISSO", "NINGUEM TE CONTOU"],
    "fishing": ["OLHA A PUXADA", "PEGOU PESADO", "ATE O FINAL"],
    "money": ["PRESTA ATENCAO", "ISSO MUDA TUDO", "OLHA ESSE PONTO"],
}


def get_preset(name: str | None) -> ViralPreset:
    return PRESETS.get((name or "funny").lower(), PRESETS["funny"])


def hook_text_for(theme: str, part_number: int) -> str:
    choices = HOOK_TEXTS.get((theme or "funny").lower(), HOOK_TEXTS["funny"])
    index = max(0, part_number - 1) % len(choices)
    return choices[index]
