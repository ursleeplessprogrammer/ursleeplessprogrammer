
from PIL import Image
import html
import argparse

ASCII_CHARS = "@%#*+=-:. "

def image_to_ascii(image_path, output_path,
                   width=100, char_aspect=0.5):

    image = Image.open(image_path).convert("L")

    height = int(
        image.height / image.width * width * char_aspect
    )

    image = image.resize((width, height))

    pixels = image.getdata()

    ascii_art = "".join(
        ASCII_CHARS[
            pixel * (len(ASCII_CHARS) - 1) // 255
        ]
        for pixel in pixels
    )

    lines = [
        ascii_art[i:i + width]
        for i in range(0, len(ascii_art), width)
    ]

    line_height = 12
    font_size = 10

    svg_height = len(lines) * line_height + 20
    svg_width = width * 7

    svg_content = f"""
    <svg xmlns="http://www.w3.org/2000/svg"
         width="{svg_width}"
         height="{svg_height}"
         viewBox="0 0 {svg_width} {svg_height}">

        <rect width="100%" height="100%" fill="#0d1117"/>

        <g fill="#c9d1d9"
           font-family="monospace"
           font-size="{font_size}"
           xml:space="preserve">
    """

    for index, line in enumerate(lines):
        escaped_line = html.escape(line)
        svg_content += (
            f'<text x="10" y="{20 + index * line_height}">'
            f'{escaped_line}</text>\n'
        )

    svg_content += """
        </g>
    </svg>
    """

    with open(output_path, "w", encoding="utf-8") as file:
        file.write(svg_content)

    print(f"ASCII SVG generated: {output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("image")
    parser.add_argument("-o", "--output", default="portrait.svg")
    parser.add_argument("-w", "--width", type=int, default=100)

    args = parser.parse_args()

    image_to_ascii(args.image, args.output, args.width)
