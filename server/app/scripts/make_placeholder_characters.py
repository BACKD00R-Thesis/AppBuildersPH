"""Draw simple blob-face PNGs for the default characters with FFmpeg.

Usage: python -m app.scripts.make_placeholder_characters
Writes assets/characters/tito-boy.png and bunso.png (512x512, transparent).
Replace them with real art any time; keep the file names from manifest.json.
"""

import subprocess

from app.config import get_settings

SIZE = 512

# (file name, face color, extra feature)
CHARACTERS = (
    ("tito-boy", (224, 160, 110), "mustache"),  # clay-2
    ("bunso", (47, 107, 79), "cap"),  # green-2
)


def _face(rgb: tuple[int, int, int], feature: str) -> str:
    body = "lt(hypot(X-256,Y-290),210)"
    eyes = "(lt(hypot(X-182,Y-250),50)+lt(hypot(X-330,Y-250),50))"
    pupils = "(lt(hypot(X-194,Y-258),22)+lt(hypot(X-342,Y-258),22))"
    mouth = "(lt(abs(hypot(X-256,Y-300)-110),12)*gt(Y,340))"
    hat = (
        "(between(X,136,376)*between(Y,40,92)+between(X,226,286)*between(Y,92,120))"
        if feature == "cap"
        else "0"
    )
    mustache = (
        "(lt(hypot((X-216)/1.6,Y-326),20)+lt(hypot((X-296)/1.6,Y-326),20))" if feature == "mustache" else "0"
    )

    def channel(value: int) -> str:
        return f"if(gt({hat},0),30,if(gt({pupils}+{mouth}+{mustache},0),20,if(gt({eyes},0),255,{value})))"

    r, g, b = rgb
    alpha = f"if(gt({body}+{hat},0),255,0)"
    return f"format=rgba,geq=r='{channel(r)}':g='{channel(g)}':b='{channel(b)}':a='{alpha}'"


def main() -> None:
    settings = get_settings()
    out_dir = settings.assets_dir / "characters"
    out_dir.mkdir(parents=True, exist_ok=True)
    for name, rgb, feature in CHARACTERS:
        out = out_dir / f"{name}.png"
        subprocess.run(
            [
                settings.ffmpeg_path, "-y", "-hide_banner", "-loglevel", "error",
                "-f", "lavfi", "-i", f"color=c=black:s={SIZE}x{SIZE}",
                "-vf", _face(rgb, feature), "-frames:v", "1", str(out),
            ],
            check=True,
        )  # fmt: skip
        print(f"Wrote {out}")


if __name__ == "__main__":
    main()
