import os


THEME_SFX = {
    "funny": "funny-pop.wav",
    "fails": "impact-pop.wav",
    "animals": "funny-pop.wav",
    "money": "cash-pop.wav",
    "fishing": "suspense-pop.wav",
    "football": "impact-pop.wav",
    "podcast": "suspense-pop.wav",
    "curiosities": "suspense-pop.wav",
}
DEFAULT_SFX = "funny-pop.wav"


def resolve_suspense_sound(
    theme: str,
    explicit_sound: str | None,
    base_dir: str = ".",
) -> str | None:
    if explicit_sound:
        return explicit_sound

    filename = THEME_SFX.get((theme or "").lower(), DEFAULT_SFX)
    themed_path = os.path.join(base_dir, "assets", "sfx", filename)
    if os.path.isfile(themed_path):
        return themed_path

    fallback_path = os.path.join(base_dir, "assets", "sfx", DEFAULT_SFX)
    if os.path.isfile(fallback_path):
        return fallback_path

    return None
