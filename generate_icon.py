from pathlib import Path
from PIL import Image, ImageDraw


def make_icon():
    size = 512
    image = Image.new("RGBA", (size, size), "#1f5a35")
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((24, 24, 488, 488), radius=104, fill="#1f5a35")
    draw.ellipse((116, 106, 396, 386), outline="#f4e8b5", width=18)
    draw.line((256, 350, 256, 150), fill="#f4e8b5", width=16)
    for y, side in [(180, -1), (220, 1), (260, -1), (300, 1)]:
        cx = 256 + side * 34
        draw.ellipse((cx - 34, y - 24, cx + 34, y + 18),
                     fill="#f4e8b5")
    output = Path(__file__).parent / "harvesta_icon.png"
    image.save(output)
    print(output)


if __name__ == "__main__":
    make_icon()
