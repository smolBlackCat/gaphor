"""Support classes for dealing with text."""

from typing import Tuple, Union

import gi
from gaphas.canvas import instant_cairo_context
from gaphas.freehand import FreeHandCairoContext
from gaphas.geometry import Rectangle
from gaphas.painter import CairoBoundingBoxContext

from gaphor.core.styling import FontStyle, FontWeight, Style, TextAlign, TextDecoration

# fmt: off
gi.require_version('PangoCairo', '1.0')  # noqa: isort:skip
from gi.repository import GLib, Pango, PangoCairo  # noqa: isort:skip
# fmt: on


class Layout:
    def __init__(
        self,
        text="",
        font=None,
        text_align=TextAlign.CENTER,
        default_size=(0, 0),
    ):
        self.layout = PangoCairo.create_layout(instant_cairo_context())
        self.underline = False
        self.font_id = None
        self.text = ""
        self.width = -1
        self.default_size = default_size

        if font:
            self.set_font(font)
        if text:
            self.set_text(text)
        self.set_alignment(text_align)

    def set(self, text=None, font=None, width=None, text_align=None):
        # Since text expressions can return False, we should also accomodate for that
        if text not in (None, False):
            self.set_text(text)
        if font:
            self.set_font(font)
        if width is not None:
            self.set_width(width)
        if text_align:
            self.set_alignment(text_align)

    def set_font(self, font: Style):
        font_family = font.get("font-family")
        font_size = font.get("font-size")
        font_weight = font.get("font-weight")
        font_style = font.get("font-style")
        assert font_family, "Font family should be set"
        assert font_size, "Font size should be set"

        font_id = (font_family, font_size, font_weight, font_style)
        if font_id == self.font_id:
            return

        self.font_id = font_id

        fd = Pango.FontDescription.new()
        fd.set_family(font_family)
        fd.set_absolute_size(font_size * Pango.SCALE)

        if font_weight:
            assert isinstance(font_weight, FontWeight)
            fd.set_weight(getattr(Pango.Weight, font_weight.name))
        if font_style:
            assert isinstance(font_style, FontStyle)
            fd.set_style(getattr(Pango.Style, font_style.name))

        self.layout.set_font_description(fd)

        underline = (
            font.get("text-decoration", TextDecoration.NONE) == TextDecoration.UNDERLINE
        )

        if self.underline != underline:
            self.underline = underline
            self.update_text()

    def set_text(self, text: str):
        if text != self.text:
            self.text = text
            self.update_text()

    def update_text(self):
        if self.underline:
            # TODO: can this be done via Pango attributes instead?
            self.layout.set_markup(
                f"<u>{GLib.markup_escape_text(self.text)}</u>", length=-1
            )
        else:
            self.layout.set_text(self.text, length=-1)

    def set_width(self, width: int):
        self.width = width
        if width == -1:
            self.layout.set_width(-1)
        else:
            self.layout.set_width(int(width * Pango.SCALE))

    def set_alignment(self, text_align: TextAlign):
        self.layout.set_alignment(getattr(Pango.Alignment, text_align.name))

    def size(self):
        if not self.text:
            return self.default_size
        self.set_width(self.width)
        return self.layout.get_pixel_size()

    def show_layout(self, cr, width=None, default_size=None):
        layout = self.layout
        if not self.text:
            return default_size or self.default_size
        if width is not None:
            layout.set_width(int(width * Pango.SCALE))

        if isinstance(cr, FreeHandCairoContext):
            PangoCairo.show_layout(cr.cr, layout)
        elif isinstance(cr, CairoBoundingBoxContext):
            w, h = layout.get_pixel_size()
            cr.rel_line_to(w, h)
            cr.stroke()
        else:
            PangoCairo.show_layout(cr, layout)


def focus_box_pos(
    bounding_box: Rectangle,
    text_size: Tuple[Union[float, int], Union[float, int]],
    text_align: TextAlign,
) -> Tuple[int, int]:
    """Calculate the focus box position based on alignment style."""
    x, y, width, height = bounding_box
    w, h = text_size

    if text_align is TextAlign.CENTER:
        x += (width - w) / 2
    elif text_align is TextAlign.RIGHT:
        x += width - w

    y += (height - h) / 2

    return x, y


def text_point_at_line(points, size, text_align):
    """Provide a position (x, y) to draw a text close to a line.

    Parameters:
     - points:  the line points, a list of (x, y) points
     - size:    size of the text, a (width, height) tuple
     - text_align: alignment to the line: left, beginning of the line, center, middle and right: end of the line
    """

    if text_align == TextAlign.LEFT:
        p0 = points[0]
        p1 = points[1]
        x, y = _text_point_at_line_end(size, p0, p1)
    elif text_align == TextAlign.CENTER:
        p0, p1 = middle_segment(points)
        x, y = _text_point_at_line_center(size, p0, p1)
    elif text_align == TextAlign.RIGHT:
        p0 = points[-1]
        p1 = points[-2]
        x, y = _text_point_at_line_end(size, p0, p1)

    return x, y


def middle_segment(points):
    """Get middle line segment."""
    m = len(points) // 2
    assert m >= 1 and m < len(points)
    return points[m - 1], points[m]


def _text_point_at_line_end(size, p1, p2):
    """Calculate position of the text relative to a line defined by points p1
    and p2.

    Parameters:
     - size: text size, a (width, height) tuple
     - p1:      beginning of line segment
     - p2:      end of line segment
    """
    name_dx = 0.0
    name_dy = 0.0
    ofs = 5

    dx = float(p2[0]) - float(p1[0])
    dy = float(p2[1]) - float(p1[1])

    name_w, name_h = size

    if dy == 0:
        rc = 1000.0  # quite a lot...
    else:
        rc = dx / dy
    abs_rc = abs(rc)
    h = dx > 0  # right side of the box
    v = dy > 0  # bottom side

    if abs_rc > 6:
        # horizontal line
        if h:
            name_dx = ofs
            name_dy = -ofs - name_h
        else:
            name_dx = -ofs - name_w
            name_dy = -ofs - name_h
    elif 0 <= abs_rc <= 0.2:
        # vertical line
        if v:
            name_dx = -ofs - name_w
            name_dy = ofs
        else:
            name_dx = -ofs - name_w
            name_dy = -ofs - name_h
    else:
        # Should both items be placed on the same side of the line?
        r = abs_rc < 1.0

        # Find out alignment of text (depends on the direction of the line)
        align_left = h ^ r
        align_bottom = v ^ r
        if align_left:
            name_dx = ofs
        else:
            name_dx = -ofs - name_w
        if align_bottom:
            name_dy = -ofs - name_h
        else:
            name_dy = ofs
    return p1[0] + name_dx, p1[1] + name_dy


# hint tuples to move text depending on quadrant
WIDTH_HINT = (-1, -1, 0)
PADDING_HINT = (1, 1, -1)
EPSILON = 1e-6


def _text_point_at_line_center(size, p1, p2):
    """Calculate position of the text relative to a line defined by points p1
    and p2.

    Parameters:
     - size:    text size, a (width, height) tuple
     - p1:      beginning of line
     - p2:      end of line
    """
    x0 = (p1[0] + p2[0]) / 2.0
    y0 = (p1[1] + p2[1]) / 2.0
    dx = p2[0] - p1[0]
    dy = p2[1] - p1[1]
    ofs = 3

    if abs(dx) < EPSILON:
        d1 = -1.0
        d2 = 1.0
    elif abs(dy) < EPSILON:
        d1 = 0.0
        d2 = 0.0
    else:
        d1 = dy / dx
        d2 = abs(d1)

    width, height = size

    # move to center and move by delta depending on line angle
    if d2 < 0.5774:  # <0, 30>, <150, 180>, <-180, -150>, <-30, 0>
        # horizontal mode
        w2 = width / 2.0
        hint = w2 * d2

        x = x0 - w2
        y = y0 + hint + ofs
    else:
        # much better in case of vertical lines

        # determine quadrant, we are interested in 1 or 3 and 2 or 4
        # see hint tuples below
        h2 = height / 2.0
        q = (d1 > 0) - (d1 < 0)
        hint = 0 if abs(dx) < EPSILON else h2 / d2
        x = x0 - hint + width * WIDTH_HINT[q]
        x = x0 - (ofs + hint) * PADDING_HINT[q] + width * WIDTH_HINT[q]
        y = y0 - h2

    return x, y
