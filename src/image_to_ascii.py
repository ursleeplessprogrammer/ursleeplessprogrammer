
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

# Controls the terminal animation
DEFAULT_ANIMATION_SPEED = 0.065
DEFAULT_REVEAL_DURATION = 0.12

# Monospace character width-to-height ratio.
# This compensates for characters being taller than they are wide.
CHAR_ASPECT_RATIO = 0.55


# ============================================================
# IMAGE PROCESSING
# ============================================================

def load_image(image_path):
    """
    Load an image, correct its EXIF orientation,
    and convert it to RGB.
    """

    image_path = Path(image_path)

    if not image_path.exists():
        raise FileNotFoundError(
            f"Image not found: {image_path}"
        )

    image = Image.open(image_path)

    image = ImageOps.exif_transpose(image)
    image = image.convert("RGB")

    return image


def resize_image(image, width):
    """
    Resize the image while preserving its visual aspect ratio
    for monospace ASCII characters.

    Automatically compensates for character width and height.
    """

    original_width, original_height = image.size

    # Approximate monospace character dimensions
    char_width = 0.60
    char_height = 1.25

    character_ratio = char_width / char_height

    # Calculate output height using character proportions
    aspect_ratio = original_height / original_width

    height = round(
        width * aspect_ratio * character_ratio
    )

    height = max(1, height)

    return image.resize(
        (width, height),
        Image.Resampling.LANCZOS
    )


def generate_gif(
    rows,
    output_path,
    font_size=12,
    foreground="#c9d1d9",
    background="#0d1117",
    frame_duration=80
):
    """
    Generate an animated terminal-style ASCII portrait GIF.

    Each frame progressively reveals another line of ASCII art.
    Uses Pillow only.
    """

    from PIL import Image, ImageDraw, ImageFont

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Load a monospace font
    try:
        font = ImageFont.truetype("consola.ttf", font_size)
    except OSError:
        try:
            font = ImageFont.truetype(
                "C:/Windows/Fonts/consola.ttf",
                font_size
            )
        except OSError:
            font = ImageFont.load_default()

    # Measure character dimensions
    char_width = font.getlength("M")
    char_height = font_size * 1.4

    columns = max(len(row) for row in rows)
    line_count = len(rows)

    padding = 24
    header_height = 55
    footer_height = 45

    content_width = int(columns * char_width)

    width = content_width + padding * 2
    height = int(
        header_height
        + line_count * char_height
        + footer_height
        + padding
    )

    frames = []

    # Colors
    fg = foreground
    bg = background

    # Terminal header
    header_text = "portrait@github: ~$ ./portrait.sh"
    footer_text = "portrait@github:~$ portrait generated"

    # Create one frame for every progressively revealed line
    for visible_lines in range(1, line_count + 1):

        frame = Image.new("RGB", (width, height), bg)
        draw = ImageDraw.Draw(frame)

        # Terminal border
        draw.rounded_rectangle(
            (0, 0, width - 1, height - 1),
            radius=10,
            outline="#30363d",
            width=1
        )

        # Terminal controls
        draw.ellipse((18, 15, 28, 25), fill="#ff5f56")
        draw.ellipse((36, 15, 46, 25), fill="#ffbd2e")
        draw.ellipse((54, 15, 64, 25), fill="#27c93f")

        # Header
        draw.text(
            (80, 13),
            header_text,
            font=font,
            fill="#8b949e"
        )

        # Header separator
        draw.line(
            (0, header_height - 5, width, header_height - 5),
            fill="#30363d",
            width=1
        )

        # ASCII portrait
        for index in range(visible_lines):

            y = (
                header_height
                + index * char_height
            )

            draw.text(
                (padding, y),
                rows[index],
                font=font,
                fill=fg
            )

        # Moving cursor at the end of the current line
        current_row = rows[visible_lines - 1]

        cursor_x = (
            padding
            + int(len(current_row) * char_width)
        )

        cursor_y = (
            header_height
            + (visible_lines - 1) * char_height
        )

        draw.rectangle(
            (
                cursor_x,
                cursor_y,
                cursor_x + max(2, int(char_width)),
                cursor_y + font_size
            ),
            fill=fg
        )

        frames.append(frame)

    # Final terminal frame
    final_frame = frames[-1].copy()
    draw = ImageDraw.Draw(final_frame)

    footer_y = height - footer_height

    draw.text(
        (padding, footer_y),
        footer_text,
        font=font,
        fill="#8b949e"
    )

    frames.append(final_frame)

    # Blinking cursor frames
    cursor_x = (
        padding
        + int(font.getlength(footer_text))
        + 3
    )

    for visible in [True, False, True, False]:

        blink_frame = final_frame.copy()
        draw = ImageDraw.Draw(blink_frame)

        if visible:
            draw.rectangle(
                (
                    cursor_x,
                    footer_y,
                    cursor_x + max(2, int(char_width)),
                    footer_y + font_size
                ),
                fill=fg
            )

        frames.append(blink_frame)

    # Save animated GIF
    frames[0].save(
        output_path,
        save_all=True,
        append_images=frames[1:],
        duration=frame_duration,
        loop=0,
        optimize=True,
        disposal=2
    )

    print(f"[SUCCESS] Animated GIF saved: {output_path}")
    print(f"[INFO] Dimensions: {width} x {height}")
    print(f"[INFO] Frames: {len(frames)}")


def adjust_image(image, contrast=1.0, brightness=1.0):
    """
    Adjust image contrast and brightness.

    Defaults preserve the original image brightness and contrast.
    """

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
    Convert an RGB image into ASCII characters.

    Dark pixels use dense characters.
    Bright pixels use lighter characters.

    The original image composition is preserved.
    No background removal is performed.
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

        row = "".join(characters[start:end])

        rows.append(row)

    return rows


# ============================================================
# SVG ANIMATION GENERATOR
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
    Generate an animated terminal-style SVG.

    Animation sequence:
    1. ASCII lines appear one by one.
    2. A cursor follows each line while it is revealed.
    3. The terminal footer appears after the portrait.
    4. The final terminal cursor blinks continuously.

    Uses SVG SMIL animation.
    """

    output_path = Path(output_path)

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    if not rows:
        raise ValueError("No ASCII rows were generated.")

    # --------------------------------------------------------
    # Dimensions
    # --------------------------------------------------------

    columns = max(len(row) for row in rows)

    # Approximate monospace character dimensions
    char_width = font_size * 0.60
    char_height = font_size * 1.25

    padding_x = 24
    padding_top = 70
    padding_bottom = 45

    header_height = 38
    footer_height = 35

    content_width = columns * char_width

    svg_width = int(
        content_width + (padding_x * 2)
    )

    content_height = len(rows) * char_height

    svg_height = int(
        padding_top
        + content_height
        + padding_bottom
    )

    text_x = padding_x

    first_line_y = padding_top

    # Total animation duration
    total_animation_duration = (
        len(rows) * animation_speed
        + reveal_duration
    )

    # --------------------------------------------------------
    # SVG initialization
    # --------------------------------------------------------

    svg = []

    svg.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'xmlns:xlink="http://www.w3.org/1999/xlink" '
        f'width="{svg_width}" '
        f'height="{svg_height}" '
        f'viewBox="0 0 {svg_width} {svg_height}">'
    )

    svg.append("<defs>")

    # --------------------------------------------------------
    # Animation definitions
    # --------------------------------------------------------

    # Cursor blinking animation
    svg.append("""
        <style>
            .terminal-text {
                font-family: Consolas, "Courier New", monospace;
                font-weight: 400;
            }

            .terminal-header {
                font-family: Consolas, "Courier New", monospace;
                font-size: 12px;
            }

            .terminal-footer {
                font-family: Consolas, "Courier New", monospace;
                font-size: 11px;
            }
        </style>
    """)

    svg.append("</defs>")

    # --------------------------------------------------------
    # Background
    # --------------------------------------------------------

    svg.append(
        f'<rect x="0" y="0" '
        f'width="{svg_width}" height="{svg_height}" '
        f'rx="10" ry="10" '
        f'fill="{html.escape(background, quote=True)}"/>'
    )

    # --------------------------------------------------------
    # Terminal window border
    # --------------------------------------------------------

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
    # Terminal header
    # --------------------------------------------------------

    svg.append(
        '<circle cx="20" cy="20" r="5" fill="#ff5f56"/>'
    )

    svg.append(
        '<circle cx="38" cy="20" r="5" fill="#ffbd2e"/>'
    )

    svg.append(
        '<circle cx="56" cy="20" r="5" fill="#27c93f"/>'
    )

    header_text = "portrait@github: ~$ ./portrait.sh"

    svg.append(
        f'<text x="{padding_x + 55}" y="24" '
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
    # ASCII rows
    # --------------------------------------------------------

    for index, row in enumerate(rows):

        y_position = (
            first_line_y
            + index * char_height
        )

        animation_begin = (
            index * animation_speed
        )

        clip_id = f"line-clip-{index}"
        cursor_id = f"line-cursor-{index}"

        # Escape special XML characters
        safe_row = html.escape(row)

        # ----------------------------------------------------
        # Clip path for progressive text reveal
        # ----------------------------------------------------

        svg.append(
            f'<clipPath id="{clip_id}">'
            f'<rect x="{text_x}" '
            f'y="{y_position - font_size}" '
            f'width="0" '
            f'height="{char_height + 2}">'
            f'<animate '
            f'attributeName="width" '
            f'from="0" '
            f'to="{content_width}" '
            f'begin="{animation_begin:.3f}s" '
            f'dur="{reveal_duration:.3f}s" '
            f'fill="freeze" '
            f'calcMode="linear"/>'
            f'</rect>'
            f'</clipPath>'
        )

        # ----------------------------------------------------
        # ASCII text
        # ----------------------------------------------------

        svg.append(
            f'<text x="{text_x}" '
            f'y="{y_position}" '
            f'class="terminal-text" '
            f'font-size="{font_size}" '
            f'fill="{html.escape(foreground, quote=True)}" '
            f'xml:space="preserve" '
            f'clip-path="url(#{clip_id})">'
            f'{safe_row}'
            f'</text>'
        )

        # ----------------------------------------------------
        # Moving cursor
        # ----------------------------------------------------

        cursor_y = y_position - font_size + 1

        svg.append(
            f'<rect id="{cursor_id}" '
            f'x="{text_x}" '
            f'y="{cursor_y}" '
            f'width="{max(1, font_size * 0.6)}" '
            f'height="{font_size + 2}" '
            f'fill="{html.escape(foreground, quote=True)}" '
            f'opacity="0">'
        )

        # Cursor moves from left to right
        svg.append(
            f'<animate '
            f'attributeName="x" '
            f'from="{text_x}" '
            f'to="{text_x + content_width}" '
            f'begin="{animation_begin:.3f}s" '
            f'dur="{reveal_duration:.3f}s" '
            f'fill="freeze"/>'
        )

        # Cursor appears during the reveal and disappears afterward
        svg.append(
            f'<animate '
            f'attributeName="opacity" '
            f'values="0;1;1;0" '
            f'keyTimes="0;0.01;0.90;1" '
            f'begin="{animation_begin:.3f}s" '
            f'dur="{reveal_duration:.3f}s" '
            f'fill="freeze"/>'
        )

        svg.append("</rect>")

    # --------------------------------------------------------
    # Terminal footer
    # --------------------------------------------------------

    footer_y = (
        first_line_y
        + content_height
        + 24
    )

    footer_text = "portrait@github:~$ portrait generated"

    footer_start = (
        total_animation_duration + 0.1
    )

    svg.append(
        f'<text x="{padding_x}" '
        f'y="{footer_y}" '
        f'class="terminal-footer" '
        f'fill="#8b949e" '
        f'opacity="0">'
        f'{html.escape(footer_text)}'
        f'<set attributeName="opacity" '
        f'to="1" '
        f'begin="{footer_start:.3f}s" '
        f'fill="freeze"/>'
        f'</text>'
    )

    # --------------------------------------------------------
    # Blinking footer cursor
    # --------------------------------------------------------

    footer_cursor_x = (
        padding_x
        + len(footer_text) * 6.6
    )

    svg.append(
        f'<rect x="{footer_cursor_x}" '
        f'y="{footer_y - 10}" '
        f'width="7" height="12" '
        f'fill="{html.escape(foreground, quote=True)}" '
        f'opacity="0">'
        f'<set attributeName="opacity" '
        f'to="1" '
        f'begin="{footer_start:.3f}s" '
        f'fill="freeze"/>'
        f'<animate attributeName="opacity" '
        f'values="1;0;1" '
        f'dur="0.9s" '
        f'begin="{footer_start:.3f}s" '
        f'repeatCount="indefinite"/>'
        f'</rect>'
    )

    # --------------------------------------------------------
    # Close SVG
    # --------------------------------------------------------

    svg.append("</svg>")

    # --------------------------------------------------------
    # Save file
    # --------------------------------------------------------

    output_path.write_text(
        "\n".join(svg),
        encoding="utf-8"
    )

    print(f"[SUCCESS] Animated SVG saved: {output_path}")
    print(f"[INFO] Image width: {columns} characters")
    print(f"[INFO] Image height: {len(rows)} lines")
    print(
        f"[INFO] Animation duration: "
        f"approximately {total_animation_duration:.2f} seconds"
    )


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

    # Input / output
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
        help="SVG monospace font size."
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

    # --------------------------------------------------------
    # Validate arguments
    # --------------------------------------------------------

    if args.width <= 0:
        parser.error("--width must be greater than zero.")

    if args.font_size <= 0:
        parser.error("--font-size must be greater than zero.")

    if args.animation_speed <= 0:
        parser.error("--animation-speed must be greater than zero.")

    if args.reveal_duration <= 0:
        parser.error("--reveal-duration must be greater than zero.")

    if args.contrast < 0:
        parser.error("--contrast cannot be negative.")

    if args.brightness < 0:
        parser.error("--brightness cannot be negative.")

    # --------------------------------------------------------
    # Process image
    # --------------------------------------------------------

    print("[INFO] Loading image...")

    image = load_image(args.image)

    print(
        f"[INFO] Original image size: "
        f"{image.width} x {image.height}"
    )

    print("[INFO] Resizing image...")

    image = resize_image(
        image,
        args.width
    )

    print("[INFO] Adjusting image...")

    image = adjust_image(
        image,
        contrast=args.contrast,
        brightness=args.brightness
    )

    print("[INFO] Converting image to ASCII...")

    rows = convert_to_ascii(image)

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

    generate_gif(
    rows=rows,
    output_path="assets/portrait_animated.gif",
    font_size=args.font_size,
    foreground=args.foreground,
    background=args.background,
    frame_duration=80
)


if __name__ == "__main__":
    main()
