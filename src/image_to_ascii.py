
import argparse
import html
from pathlib import Path

from PIL import Image, ImageEnhance, ImageOps


# ============================================================
# CONFIGURATION
# ============================================================

ASCII_CHARS = "@%#*+=-:. "

DEFAULT_FOREGROUND = "#c9d1d9"
DEFAULT_BACKGROUND = "#0d1117"

DEFAULT_FONT_SIZE = 8
DEFAULT_IMAGE_WIDTH = 250

# SVG monospace character proportions
CHAR_WIDTH_RATIO = 0.60
CHAR_HEIGHT_RATIO = 1.20

# Compensate for monospace character proportions
CHAR_ASPECT_RATIO = CHAR_WIDTH_RATIO / CHAR_HEIGHT_RATIO

# Terminal animation
DEFAULT_ANIMATION_SPEED = 0.065
DEFAULT_REVEAL_DURATION = 0.12

# Terminal text sizes (independent of ASCII font size)
HEADER_FONT_SIZE = 26
FOOTER_FONT_SIZE = 25


# ============================================================
# IMAGE PROCESSING
# ============================================================

def load_image(image_path):
    """Load an image, correct EXIF orientation, and convert to RGB."""

    image_path = Path(image_path)

    if not image_path.exists():
        raise FileNotFoundError(
            f"Image not found: {image_path}"
        )

    image = Image.open(image_path)
    image = ImageOps.exif_transpose(image)

    return image.convert("RGB")


def resize_image(image, width):
    """
    Resize while preserving the original image's visual proportions.

    Character aspect compensation prevents the ASCII portrait
    from appearing vertically stretched.
    """

    original_width, original_height = image.size

    if original_width <= 0 or original_height <= 0:
        raise ValueError("Invalid image dimensions.")

    aspect_ratio = original_height / original_width

    height = round(
        width * aspect_ratio * CHAR_ASPECT_RATIO
    )

    height = max(1, height)

    return image.resize(
        (width, height),
        Image.Resampling.LANCZOS
    )


def adjust_image(image, contrast=1.0, brightness=1.0):
    """Adjust contrast and brightness without changing composition."""

    if contrast != 1.0:
        image = ImageEnhance.Contrast(image).enhance(contrast)

    if brightness != 1.0:
        image = ImageEnhance.Brightness(image).enhance(brightness)

    return image


# ============================================================
# ASCII CONVERSION
# ============================================================

def convert_to_ascii(image):
    """
    Convert an image into ASCII characters.

    Dark pixels use denser characters.
    Bright pixels use lighter characters.
    """

    grayscale = image.convert("L")
    pixels = grayscale.getdata()

    characters = []
    total_chars = len(ASCII_CHARS)

    for pixel in pixels:
        index = int(
            pixel / 255 * (total_chars - 1)
        )

        characters.append(ASCII_CHARS[index])

    width, height = grayscale.size

    rows = []

    for y in range(height):
        start = y * width
        end = start + width

        rows.append(
            "".join(characters[start:end])
        )

    return rows


# ============================================================
# ANIMATED SVG GENERATOR
# ============================================================

def generate_svg(
    rows,
    output_path,
    font_size=DEFAULT_FONT_SIZE,
    foreground=DEFAULT_FOREGROUND,
    background=DEFAULT_BACKGROUND,
    animation_speed=DEFAULT_ANIMATION_SPEED,
    reveal_duration=DEFAULT_REVEAL_DURATION
):
    """
    Generate an animated terminal-style ASCII SVG.

    Features:
    - Progressive line-by-line ASCII reveal
    - Moving cursor
    - Larger terminal header
    - Larger terminal footer
    - Proportional SVG dimensions
    - Full-width ASCII rows
    - Blinking final cursor
    """

    output_path = Path(output_path)

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    if not rows:
        raise ValueError("No ASCII rows were generated.")

    # --------------------------------------------------------
    # FONT AND DIMENSIONS
    # --------------------------------------------------------

    columns = max(len(row) for row in rows)
    line_count = len(rows)

    # Character dimensions
    char_width = font_size * CHAR_WIDTH_RATIO
    char_height = font_size * CHAR_HEIGHT_RATIO

    line_height = char_height

    # Terminal layout
    padding_x = 24
    padding_top = 70
    padding_bottom = 55

    header_height = 42

    # Calculate actual ASCII content dimensions
    content_width = columns * char_width
    content_height = line_count * line_height

    # SVG canvas
    svg_width = int(
        content_width + padding_x * 2
    )

    footer_y = (
        padding_top
        + content_height
        + 25
    )

    svg_height = int(
        footer_y + padding_bottom
    )

    text_x = padding_x
    first_line_y = padding_top

    # Animation timing
    total_animation_duration = (
        (line_count - 1) * animation_speed
        + reveal_duration
    )

    footer_start = total_animation_duration + 0.2

    # Escape colors for XML
    safe_foreground = html.escape(
        foreground,
        quote=True
    )

    safe_background = html.escape(
        background,
        quote=True
    )

    # --------------------------------------------------------
    # SVG INITIALIZATION
    # --------------------------------------------------------

    svg = []

    svg.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'width="{svg_width}" '
        f'height="{svg_height}" '
        f'viewBox="0 0 {svg_width} {svg_height}">'
    )

    # --------------------------------------------------------
    # CSS
    # --------------------------------------------------------

    svg.append(f"""
    <style>
        .terminal-text {{
            font-family: Consolas, "Courier New", monospace;
            font-size: {font_size}px;
            font-weight: 400;
        }}

        .terminal-header {{
            font-family: Consolas, "Courier New", monospace;
            font-size: {HEADER_FONT_SIZE}px;
            font-weight: 600;
        }}

        .terminal-footer {{
            font-family: Consolas, "Courier New", monospace;
            font-size: {FOOTER_FONT_SIZE}px;
            font-weight: 600;
        }}
    </style>
    """)

    # --------------------------------------------------------
    # BACKGROUND
    # --------------------------------------------------------

    svg.append(
        f'<rect x="0" y="0" '
        f'width="{svg_width}" '
        f'height="{svg_height}" '
        f'rx="10" ry="10" '
        f'fill="{safe_background}"/>'
    )

    # Terminal border
    svg.append(
        f'<rect x="0.5" y="0.5" '
        f'width="{svg_width - 1}" '
        f'height="{svg_height - 1}" '
        f'rx="10" ry="10" '
        f'fill="none" '
        f'stroke="#30363d" '
        f'stroke-width="1"/>'
    )

    # --------------------------------------------------------
    # TERMINAL HEADER
    # --------------------------------------------------------

    # Terminal controls
    # Terminal controls - larger dots
    svg.append(
        '<circle cx="22" cy="22" r="7" fill="#ff5f56"/>'
    )

    svg.append(
        '<circle cx="44" cy="22" r="7" fill="#ffbd2e"/>'
    )

    svg.append(
        '<circle cx="66" cy="22" r="7" fill="#27c93f"/>'
    )

    header_text = "ursleeplessprogrammer@github: ~$ ./portrait.sh"

    # Header text
    svg.append(
        f'<text x="{padding_x + 80}" y="27" '
        f'class="terminal-header" '
        f'fill="#8b949e">'
        f'{html.escape(header_text)}'
        f'</text>'
    )

    # Header separator
    svg.append(
        f'<line x1="0" y1="{header_height}" '
        f'x2="{svg_width}" y2="{header_height}" '
        f'stroke="#30363d" stroke-width="1"/>'
    )

    # --------------------------------------------------------
    # ASCII ROW ANIMATIONS
    # --------------------------------------------------------

    for index, row in enumerate(rows):

        y_position = (
            first_line_y
            + index * line_height
        )

        animation_begin = (
            index * animation_speed
        )

        clip_id = f"line-clip-{index}"

        safe_row = html.escape(row)

        # ----------------------------------------------------
        # CLIP PATH
        # ----------------------------------------------------

        svg.append(
            f'<clipPath id="{clip_id}">'
            f'<rect x="{text_x}" '
            f'y="{y_position - font_size}" '
            f'width="0" '
            f'height="{line_height + 2}">'
            f'<animate '
            f'attributeName="width" '
            f'from="0" '
            f'to="{content_width}" '
            f'begin="{animation_begin:.3f}s" '
            f'dur="{reveal_duration:.3f}s" '
            f'fill="freeze"/>'
            f'</rect>'
            f'</clipPath>'
        )

        # ----------------------------------------------------
        # ASCII TEXT
        # ----------------------------------------------------

        svg.append(
            f'<text x="{text_x}" '
            f'y="{y_position}" '
            f'class="terminal-text" '
            f'fill="{safe_foreground}" '
            f'xml:space="preserve" '
            f'textLength="{content_width}" '
            f'lengthAdjust="spacingAndGlyphs" '
            f'clip-path="url(#{clip_id})">'
            f'{safe_row}'
            f'</text>'
        )

        # ----------------------------------------------------
        # MOVING CURSOR
        # ----------------------------------------------------

        cursor_y = y_position - font_size + 1

        svg.append(
            f'<rect '
            f'x="{text_x}" '
            f'y="{cursor_y}" '
            f'width="{max(1, char_width)}" '
            f'height="{font_size + 2}" '
            f'fill="{safe_foreground}" '
            f'opacity="0">'

            # Horizontal movement
            f'<animate '
            f'attributeName="x" '
            f'from="{text_x}" '
            f'to="{text_x + content_width}" '
            f'begin="{animation_begin:.3f}s" '
            f'dur="{reveal_duration:.3f}s" '
            f'fill="freeze"/>'

            # Cursor visibility
            f'<animate '
            f'attributeName="opacity" '
            f'values="0;1;1;0" '
            f'keyTimes="0;0.01;0.90;1" '
            f'begin="{animation_begin:.3f}s" '
            f'dur="{reveal_duration:.3f}s" '
            f'fill="freeze"/>'

            f'</rect>'
        )

    # --------------------------------------------------------
    # TERMINAL FOOTER
    # --------------------------------------------------------

    footer_text = "ursleeplessprogrammer@github:~$ portrait generated"

    svg.append(
        f'<text x="{padding_x}" '
        f'y="{footer_y}" '
        f'class="terminal-footer" '
        f'fill="#8b949e" '
        f'opacity="0">'

        f'{html.escape(footer_text)}'

        # Footer appears after portrait animation
        f'<set attributeName="opacity" '
        f'to="1" '
        f'begin="{footer_start:.3f}s" '
        f'fill="freeze"/>'

        f'</text>'
    )

    # --------------------------------------------------------
    # BLINKING FOOTER CURSOR
    # --------------------------------------------------------

    footer_char_width = FOOTER_FONT_SIZE * CHAR_WIDTH_RATIO

    footer_cursor_x = (
        padding_x
        + len(footer_text) * footer_char_width
        + 3
    )

    svg.append(
        f'<rect '
        f'x="{footer_cursor_x}" '
        f'y="{footer_y - FOOTER_FONT_SIZE + 2}" '
        f'width="8" '
        f'height="{FOOTER_FONT_SIZE + 2}" '
        f'fill="{safe_foreground}" '
        f'opacity="0">'

        f'<set attributeName="opacity" '
        f'to="1" '
        f'begin="{footer_start:.3f}s" '
        f'fill="freeze"/>'

        f'<animate '
        f'attributeName="opacity" '
        f'values="1;0;1" '
        f'dur="0.9s" '
        f'begin="{footer_start:.3f}s" '
        f'repeatCount="indefinite"/>'

        f'</rect>'
    )

    # --------------------------------------------------------
    # CLOSE SVG
    # --------------------------------------------------------

    svg.append("</svg>")

    # --------------------------------------------------------
    # SAVE SVG
    # --------------------------------------------------------

    output_path.write_text(
        "\n".join(svg),
        encoding="utf-8"
    )

    print("\n[SUCCESS] Animated SVG generated")
    print(f"[INFO] Output: {output_path}")
    print(f"[INFO] Dimensions: {svg_width} x {svg_height}")
    print(f"[INFO] ASCII columns: {columns}")
    print(f"[INFO] ASCII rows: {line_count}")
    print(f"[INFO] ASCII font size: {font_size}px")
    print(f"[INFO] Header font size: {HEADER_FONT_SIZE}px")
    print(f"[INFO] Footer font size: {FOOTER_FONT_SIZE}px")
    print(f"[INFO] Aspect ratio: {svg_width / svg_height:.3f}")


# ============================================================
# MAIN
# ============================================================

def main():

    parser = argparse.ArgumentParser(
        description=(
            "Convert an image into an animated "
            "terminal-style ASCII SVG portrait."
        )
    )

    # Input and output
    parser.add_argument(
        "image",
        help="Path to the input image."
    )

    parser.add_argument(
        "-o",
        "--output",
        default="assets/portrait_animated.svg",
        help="Output SVG path."
    )

    # Image settings
    parser.add_argument(
        "-w",
        "--width",
        type=int,
        default=DEFAULT_IMAGE_WIDTH,
        help="ASCII image width in characters."
    )

    parser.add_argument(
        "--contrast",
        type=float,
        default=1.0,
        help="Image contrast multiplier."
    )

    parser.add_argument(
        "--brightness",
        type=float,
        default=1.0,
        help="Image brightness multiplier."
    )

    # SVG settings
    parser.add_argument(
        "--font-size",
        type=int,
        default=DEFAULT_FONT_SIZE,
        help="ASCII portrait font size."
    )

    parser.add_argument(
        "--foreground",
        default=DEFAULT_FOREGROUND,
        help="ASCII foreground color."
    )

    parser.add_argument(
        "--background",
        default=DEFAULT_BACKGROUND,
        help="Terminal background color."
    )

    # Animation settings
    parser.add_argument(
        "--animation-speed",
        type=float,
        default=DEFAULT_ANIMATION_SPEED,
        help="Delay between the start of each line animation."
    )

    parser.add_argument(
        "--reveal-duration",
        type=float,
        default=DEFAULT_REVEAL_DURATION,
        help="Duration of each line reveal."
    )

    args = parser.parse_args()

    # Validate arguments
    if args.width <= 0:
        parser.error("--width must be greater than zero.")

    if args.font_size <= 0:
        parser.error("--font-size must be greater than zero.")

    if args.animation_speed <= 0:
        parser.error("--animation-speed must be greater than zero.")

    if args.reveal_duration <= 0:
        parser.error("--reveal-duration must be greater than zero.")

    if args.contrast < 0 or args.brightness < 0:
        parser.error("Contrast and brightness cannot be negative.")

    # Load image
    print("[INFO] Loading image...")

    image = load_image(args.image)

    print(
        f"[INFO] Original dimensions: "
        f"{image.width} x {image.height}"
    )

    # Resize
    print("[INFO] Resizing image...")

    image = resize_image(
        image,
        args.width
    )

    # Adjust image
    print("[INFO] Adjusting image...")

    image = adjust_image(
        image,
        contrast=args.contrast,
        brightness=args.brightness
    )

    # Convert to ASCII
    print("[INFO] Converting image to ASCII...")

    rows = convert_to_ascii(image)

    # Generate SVG
    print("[INFO] Generating animated SVG...")

    generate_svg(
        rows=rows,
        output_path=args.output,
        font_size=args.font_size,
        foreground=args.foreground,
        background=args.background,
        animation_speed=args.animation_speed,
        reveal_duration=args.reveal_duration
    )


if __name__ == "__main__":
    main()
