from PIL import Image, ImageDraw, ImageColor

from easul.util import Utf8EncodedImage
from .style import suggest_text_color_from_fill, wrap_text_in_space

import logging
LOG = logging.getLogger(__name__)
class InterpretedScoreImage:
    def __init__(self, theme, max_width, max_height):
        self.theme = theme
        self.max_width = max_width
        self.max_height = max_height

    def _draw_score_blocks(self, draw, result):
        idx = self.theme.pallete_start
        block_height = self.theme.single_block_height - self.theme.outer_line_width

        xpos = self.theme.outer_line_width

        # draw color blocks for each factor using the COLOURS pallete
        for f in result["matched_factors"]:
            draw.rectangle(((xpos, 0), (xpos + (self.theme.single_block_width * f["penalty"]), block_height)), fill=self.theme.bg_colours[idx])
            xpos = xpos + (self.theme.single_block_width * f["penalty"])
            idx += 1

        xpos = self.theme.outer_line_width
        idx = self.theme.pallete_start

        if not self.theme.show_interstial_lines:
            return

        # draw interstitial lines using a darkened version of the COLOURS
        for f in result["matched_factors"]:
            r, g, b = ImageColor.getcolor(self.theme.bg_colours[idx], "RGB")
            #
            r -= self.theme.line_darken_amount
            g -= self.theme.line_darken_amount
            b -= self.theme.line_darken_amount
            for item in range(0, f["penalty"]):
                draw.line(((xpos + self.theme.single_block_width, 0), (xpos + self.theme.single_block_width, block_height)), fill=(r, g, b), width=self.theme.single_line_width)
                xpos = xpos + self.theme.single_block_width

            idx += 1


    def _draw_containing_bars(self, draw, result):
        if len(result["matched_factors"])==0:
            return
        
        bar_height = self.theme.single_block_height - self.theme.outer_line_width
        bar_width = draw.im.size[0] - (self.theme.outer_line_width * 2)

        # draw the thick bars after each score contribution
        xpos = self.theme.outer_line_width + (result["matched_factors"][0]["penalty"] * self.theme.single_block_width)

        for f in result["matched_factors"][1:]:

            draw.line(((xpos, 0), (xpos, bar_height)), fill=(0, 0, 0),
                      width=self.theme.outer_line_width)
            xpos = xpos + ((self.theme.single_block_width) * f["penalty"])

        draw.line(((xpos, 0), (xpos, bar_height)), fill=(0, 0, 0), width=self.theme.outer_line_width)

        # draw thick rectangle around the figure
        draw.rectangle(((0, 0), (bar_width, bar_height)), outline="black", width=self.theme.outer_line_width)


    def _draw_factor_text(self, draw, result):
        xpos = self.theme.outer_line_width

        idx = self.theme.pallete_start

        for f in result["matched_factors"]:
            factor_width = self.theme.single_block_width * f["penalty"]
            factor_name = f.get("title")
            if not factor_name:
                factor_name = "Untitled"

            if self.theme.show_score is True:
                factor_name = " " + factor_name + " (" + str(f["penalty"]) + ") "

            font_color = suggest_text_color_from_fill(self.theme.bg_colours[idx])

            wrap_text_in_space(draw, xy=((xpos + self.theme.outer_line_width, 0), (xpos + factor_width - self.theme.outer_line_width, self.theme.single_block_height)), text = factor_name, font=self.theme.font, fill=font_color, align="center")

            xpos += factor_width
            idx = idx + 1


    def _draw_score_ranges(self, draw, result):
        for rng_name, rng in result["ranges"].items():
            if rng[0]==0:
                x_start = rng[0]*self.theme.single_block_width

            else:
                x_start = (rng[0] * self.theme.single_block_width + self.theme.outer_line_width) - self.theme.single_block_width


            if rng[1] is None:
                x_end = draw.im.size[0] - (self.theme.outer_line_width * 2)
                rng_text = str(rng[0]) + "+"
            elif rng[0] == rng[1]:
                x_end = (rng[1] * self.theme.single_block_width) + self.theme.outer_line_width
                rng_text = str(rng[0])
            else:
                x_end = (rng[1] * self.theme.single_block_width) + self.theme.outer_line_width
                rng_text = str(rng[0]) + "-" + str(rng[1])

            rng_name = " " + rng_name + " (" + rng_text + ") "

            draw.text((x_start,x_end),rng_name)
            w,h = draw.textsize(rng_name, self.theme.font)

            draw.text((x_start, self.theme.single_block_height), rng_name, fill="black", font=self.theme.font, anchor="lm")
            x_start = x_start + w

            # draw.line(
            #     ((x_start,self.theme.single_block_height),
            #     (x_end,self.theme.single_block_height)), fill="black",width=3)
            #
            # draw.line(((x_end - 6, self.theme.single_block_height - 6), (x_end, self.theme.single_block_height)), fill="black", width=3)
            # draw.line(((x_end - 6, self.theme.single_block_height + 6), (x_end, self.theme.single_block_height)), fill="black",
            #           width=3)

    def create_encoded_image(self, result):
        img = Utf8EncodedImage()

        if self.theme.expand_blocks:
            self.theme.single_block_width = self.max_width / self.theme.max_score

        im = Image.new(mode="RGB",
                       size=(self.max_width + (self.theme.outer_line_width * 2), self.max_height + self.theme.outer_line_width),
                       color=(255, 255, 255))
        draw = ImageDraw.Draw(im)

        self._draw_score_blocks(draw, result)

        self._draw_containing_bars(draw, result)

        self._draw_factor_text(draw, result)

        if result.get("ranges"):
            self._draw_score_ranges(draw, result)

        im.save(img, format="PNG")

        return img


