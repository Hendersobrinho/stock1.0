"""
Gera a logo do programa em PNG e o ícone ICO multi-tamanho a partir de um desenho simples.

Saídas:
- assets/logo.png (512x512)
- assets/logo_small.png (128x128)
- assets/logo_32.png (32x32)
- data/icon.ico (16, 24, 32, 48, 64, 128, 256)

Requer: Pillow
"""

from __future__ import annotations

from pathlib import Path


def draw_logo(size: int = 512):
    from PIL import Image, ImageDraw  # type: ignore

    bg = (33, 150, 243, 255)  # #2196F3
    fg = (255, 255, 255, 255)
    img = Image.new("RGBA", (size, size), bg)
    d = ImageDraw.Draw(img)

    # Rounded border (subtle)
    d.rounded_rectangle([8, 8, size - 8, size - 8], radius=round(size * 0.11), outline=(255, 255, 255, 60), width=round(size * 0.015))

    # Bars
    bar_w = round(size * 0.11)
    gap = round(size * 0.055)
    base_y = round(size * 0.78)
    left_x = round(size * 0.215)
    heights = [round(size * 0.27), round(size * 0.39), round(size * 0.49), round(size * 0.35)]
    for i, h in enumerate(heights):
        x = left_x + i * (bar_w + gap)
        d.rounded_rectangle([x, base_y - h, x + bar_w, base_y], radius=round(bar_w * 0.25), fill=fg)

    # Check mark
    # Points proportional to size
    p1 = (round(size * 0.29), round(size * 0.58))
    p2 = (round(size * 0.43), round(size * 0.72))
    p3 = (round(size * 0.72), round(size * 0.41))
    d.line([p1, p2, p3], fill=fg, width=round(size * 0.055), joint="curve")

    return img


def main() -> None:
    try:
        from PIL import Image  # type: ignore
    except Exception as e:
        raise SystemExit("Pillow não instalado. Instale com: pip install Pillow")

    out_dir = Path("assets")
    data_dir = Path("data")
    out_dir.mkdir(parents=True, exist_ok=True)
    data_dir.mkdir(parents=True, exist_ok=True)

    logo_512 = draw_logo(512); logo_512.save(out_dir / "logo.png")
    logo_128 = draw_logo(128); logo_128.save(out_dir / "logo_small.png")
    # Conjunto de tamanhos dedicados (evita reamostrar em runtime)
    for sz in (32, 48, 64, 96, 128, 256):
        draw_logo(sz).save(out_dir / f"logo_{sz}.png")

    # ICO multi-size (inclui 256 para monitores de alta densidade)
    sizes = [16, 24, 32, 48, 64, 128, 256]
    base = draw_logo(256).convert("RGBA")
    base.save(data_dir / "icon.ico", format="ICO", sizes=[(s, s) for s in sizes])

    print("Logo gerada em assets/logo.png, assets/logo_small.png e assets/logo_32.png")
    print("Ícone gerado em data/icon.ico (16..256)")


if __name__ == "__main__":
    main()
