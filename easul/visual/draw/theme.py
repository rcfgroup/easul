from PIL import ImageFont

class RedTheme:
    factors = {}
    ranges = {}
    contributions = {}
    preamble = {}
    single_block_width = 40
    single_block_height = 150
    single_line_width = 6
    outer_line_width = 12
    text_y = 10
    pallete_start = 0
    font = ImageFont.truetype("Arial.ttf", 20)
    min_score = 0
    max_score = None
    expand_blocks = False
    show_score = True
    show_interstial_lines = True
    bg_colours = ['rgb(215,48,39)','rgb(244,109,67)','rgb(253,174,97)','rgb(254,224,144)','rgb(255,255,191)','rgb(224,243,248)','rgb(171,217,233)','rgb(116,173,209)','rgb(69,117,180)']
    line_darken_amount = 16
