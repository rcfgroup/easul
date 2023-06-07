from PIL import ImageColor
def wrap_text_in_space(draw, xy, text, font, **kwargs):
    space_w = xy[1][0] - xy[0][0]
    space_h = xy[1][1] - xy[0][1]

    text = _coerce_text_to_fit(draw, space_w, text, font)

    w, h = draw.multiline_textsize(text, font)
    text_x = xy[0][0] + (space_w / 2) - (w / 2)
    text_y = xy[0][1] + (space_h / 2) - (h / 2)

    draw.multiline_text((text_x, text_y), text=text, font=font, **kwargs)


def _coerce_text_to_fit(draw, max_width, text, font):
    w, h = draw.multiline_textsize(text, font)
    if w<max_width:
        return text

    text_bits = text.split(" ")
    line = []
    lines = []
    for text_bit in text_bits:
        w, h = draw.multiline_textsize(" ".join(line+[text_bit]), font)
        if w>max_width:
            lines.append(line)
            line = [text_bit]
            continue

        line.append(text_bit)
    lines.append(line)

    return "\n".join([" ".join(line) for line in lines])

def suggest_text_color_from_fill(fill):
    # Used simpler approach than W3C recommended approach. See:
    # https://stackoverjourney.com/questions/3942878/how-to-decide-font-color-in-white-or-black-depending-on-background-color
    r, g, b = ImageColor.getcolor(fill, "RGB")

    if (r * 0.299 + g * 0.587 + b * 0.114) > 186:
        return "black"
    else:
        return "white"


def get_styled_factors(factors, theme):

    styled_factors = []
    for idx, factor in enumerate(factors):
        factor["fill"] = theme.bg_colours[idx+theme.pallete_start]
        factor["color"] = suggest_text_color_from_fill(theme.bg_colours[idx+ theme.pallete_start])
        styled_factors.append(factor)

    return styled_factors

