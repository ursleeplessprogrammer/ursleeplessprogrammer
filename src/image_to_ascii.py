
import os
import html
import argparse
from PIL import Image

# ASCII characters ordered from darkest to brightest
ASCII_CHARS = "@%#*+=-:. "


def image_to_ascii(
    image_path,
    output_path="assets/portrait.svg",
    width=120,
    char_aspect=0.5,
    font_size=10,
    foreground="#c9d1d9",
    background="#0d1117"
):
    """
    Convert an image into an ASCII portrait and export it as SVG.

    Parameters:
        image_path: Input image path.
        output_path: Output SVG path.
        width: ASCII character width.
        char_aspect: Character aspect ratio correction.
        font_size: SVG font size.
        foreground: ASCII character color.
        background: SVG background color.
    """

    # Validate input image
    if not os.path.exists(image_path):
        raise FileNotFoundError(
            f"Image not found: {image_path}"
        )

    # Load image and convert to grayscale
    image = Image.open(image_path).convert("L")

    # Calculate output dimensions
    height = int(
        image.height / image.width * width * char_aspect
    )

    # Resize image
    image = image.resize(
        (width, height),
        Image.Resampling.LANCZOS
    )

    # Convert pixels into ASCII characters
    pixels = list(image.getdata())

    ascii_pixels = [
        ASCII_CHARS[
            pixel * (len(ASCII_CHARS) - 1) // 255
        ]
        for pixel in pixels
    ]

    # Split ASCII characters into lines
    lines = [
        "".join(ascii_pixels[i:i + width])
        for i in range(0, len(ascii_pixels), width)
    ]

    # SVG dimensions
    line_height = font_size * 1.2
    padding = 20

    svg_width = int(
        width * font_size * 0.65 + padding * 2
    )

    svg_height = int(
        len(lines) * line_height + padding * 2
    )

    # Build SVG document
    svg_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg"
     width="{svg_width}"
     height="{svg_height}"
     viewBox="0 0 {svg_width} {svg_height}">

    <rect
        width="100%"
        height="100%"
        fill="{html.escape(background, quote=True)}"
    />

    <g
        fill="{html.escape(foreground, quote=True)}"
        font-family="monospace"
        font-size="{font_size}"
        xml:space="preserve"
    >
'''

    # Add each ASCII line
    for index, line in enumerate(lines):

        escaped_line = html.escape(line)

        y_position = padding + (index + 1) * line_height

        svg_content += f'''
        <text x="{padding}" y="{y_position:.2f}">{escaped_line}</text>
'''

    # Close SVG
    svg_content += '''
    </g>
</svg>
'''

    # Create output directory if necessary
    output_directory = os.path.dirname(output_path)

    if output_directory:
        os.makedirs(output_directory, exist_ok=True)

    # Export SVG
    with open(
        output_path,
        "w",
        encoding="utf-8"
    ) as file:
        file.write(svg_content)

    print("ASCII portrait generated successfully!")
    print(f"Input : {image_path}")
    print(f"Output: {output_path}")
    print(f"Size  : {width} characters wide")


def main():

    parser = argparse.ArgumentParser(
        description="Convert an image into an ASCII SVG portrait."
    )

    parser.add_argument(
        "image",
        help="Path to the input image."
    )

    parser.add_argument(
        "-o",
        "--output",
        default="assets/portrait.svg",
        help="Output SVG path (default: assets/portrait.svg)."
    )

    parser.add_argument(
        "-w",
        "--width",
        type=int,
        default=120,
        help="ASCII character width (default: 120)."
    )

    parser.add_argument(
        "--aspect",
        type=float,
        default=0.5,
        help="Character aspect ratio correction (default: 0.5)."
    )

    parser.add_argument(
        "--font-size",
        type=int,
        default=10,
        help="SVG font size (default: 10)."
    )

    parser.add_argument(
        "--foreground",
        default="#c9d1d9",
        help="ASCII character color (default: #c9d1d9)."
    )

    parser.add_argument(
        "--background",
        default="#0d1117",
        help="SVG background color (default: #0d1117)."
    )

    args = parser.parse_args()

    if args.width <= 0 or args.font_size <= 0 or args.aspect <= 0:
        parser.error("Width, font size, and aspect must be positive.")

    try:
        image_to_ascii(
            image_path=args.image,
            output_path=args.output,
            width=args.width,
            char_aspect=args.aspect,
            font_size=args.font_size,
            foreground=args.foreground,
            background=args.background
        )

    except Exception as error:
        print(f"Error: {error}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
