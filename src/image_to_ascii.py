
from PIL import Image, ImageOps, ImageEnhance
import argparse
import html
from pathlib import Path


# Dark characters represent darker pixels.
# Light characters represent brighter pixels.
ASCII_CHARS = (
    "@%#*+=-:. "
)


def load_image(image_path):
    """Load the original image without modifying its source file."""
    image = Image.open(image_path)
    image = ImageOps.exif_transpose(image)
    return image.convert("RGB")


def resize_image(image, width, char_aspect=0.55):
    """
    Resize proportionally while accounting for the rectangular
    shape of monospace characters.

    char_aspect:
        Approximate character width / character height.
        Adjust this if the rendered portrait looks too tall or wide.
    """
    original_width, original_height = image.size

    aspect_ratio = original_height / original_width

    height = max(
        1,
        round(width * aspect_ratio * char_aspect)
    )

    return image.resize(
        (width, height),
        Image.Resampling.LANCZOS
    )


def convert_to_ascii(image, width=180, char_aspect=0.55,
                     contrast=1.0, brightness=1.0):
    """Convert an image into ASCII characters."""

    image = resize_image(image, width, char_aspect)

    # Convert to grayscale.
    grayscale = ImageOps.grayscale(image)

    # Keep enhancements neutral by default.
    if contrast != 1.0:
        grayscale = ImageEnhance.Contrast(grayscale).enhance(contrast)

    if brightness != 1.0:
        grayscale = ImageEnhance.Brightness(grayscale).enhance(brightness)

    pixels = list(grayscale.getdata())

    ascii_chars = []

    for pixel in pixels:
        index = round(
            pixel / 255 * (len(ASCII_CHARS) - 1)
        )

        ascii_chars.append(ASCII_CHARS[index])

    # Reconstruct the character rows.
    rows = []

    for y in range(image.height):
        start = y * image.width
        end = start + image.width

        rows.append("".join(ascii_chars[start:end]))

    return rows


def generate_svg(rows, output_path, font_size=8,
                 foreground="#c9d1d9", background=None):
    """Generate an SVG image from ASCII rows."""

    columns = max(len(row) for row in rows)

    # Monospace characters are approximately 0.6 times
    # the font size in width.
    char_width = font_size * 0.6

    svg_width = columns * char_width
    svg_height = len(rows) * font_size

    svg = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        (
            f'<svg xmlns="http://www.w3.org/2000/svg" '
            f'width="{svg_width}" height="{svg_height}" '
            f'viewBox="0 0 {svg_width} {svg_height}">'
        )
    ]

    if background:
        svg.append(
            f'<rect width="100%" height="100%" '
            f'fill="{background}"/>'
        )

    svg.append(
        f'<g fill="{foreground}" '
        f'font-family="Consolas, Courier New, monospace" '
        f'font-size="{font_size}" '
        f'font-weight="normal" '
        f'xml:space="preserve">'
    )

    for index, row in enumerate(rows):
        y = (index + 1) * font_size

        svg.append(
            f'<text x="0" y="{y}">{html.escape(row)}</text>'
        )

    svg.extend([
        '</g>',
        '</svg>'
    ])

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    output_path.write_text(
        "\n".join(svg),
        encoding="utf-8"
    )

    print(f"ASCII SVG saved to: {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Convert an image into an ASCII SVG portrait."
    )

    parser.add_argument("input", help="Input image path")

    parser.add_argument(
        "-o", "--output",
        default="assets/portrait.svg"
    )

    parser.add_argument(
        "-w", "--width",
        type=int,
        default=180
    )

    parser.add_argument(
        "--char-aspect",
        type=float,
        default=0.55
    )

    parser.add_argument(
        "--font-size",
        type=int,
        default=8
    )

    parser.add_argument(
        "--contrast",
        type=float,
        default=1.0
    )

    parser.add_argument(
        "--brightness",
        type=float,
        default=1.0
    )

    parser.add_argument(
        "--foreground",
        default="#c9d1d9"
    )

    parser.add_argument(
        "--background",
        default=None
    )

    args = parser.parse_args()

    if args.width <= 0 or args.font_size <= 0:
        parser.error("Width and font size must be positive.")

    if args.char_aspect <= 0:
        parser.error("Character aspect ratio must be positive.")

    image = load_image(args.input)

    rows = convert_to_ascii(
        image,
        width=args.width,
        char_aspect=args.char_aspect,
        contrast=args.contrast,
        brightness=args.brightness
    )

    generate_svg(
        rows,
        args.output,
        font_size=args.font_size,
        foreground=args.foreground,
        background=args.background
    )


if __name__ == "__main__":
    main()
