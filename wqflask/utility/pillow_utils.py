from PIL import Image, ImageColor, ImageDraw, ImageFont

import utility.logger
logger = utility.logger.getLogger(__name__ )

BLACK = ImageColor.getrgb("black")
WHITE = ImageColor.getrgb("white")

# def draw_rotated_text(canvas: Image, text: str, font: ImageFont, xy: tuple, fill: ImageColor=BLACK, angle: int=-90):
def draw_rotated_text(canvas, text, font, xy, fill=BLACK, angle=-90):
    # type: (Image, str, ImageFont, tuple, ImageColor, int)
    """Utility function draw rotated text"""
    tmp_img = Image.new("RGBA", font.getsize(text), color=(0,0,0,0))
    draw_text = ImageDraw.Draw(tmp_img)
    draw_text.text(text=text, xy=(0,0), font=font, fill=fill)
    tmp_img2 = tmp_img.rotate(angle, expand=1)
    tmp_img2.save("/tmp/{}.png".format(text), format="png")
    canvas.paste(im=tmp_img2, box=tuple([int(i) for i in xy]))

# def draw_open_polygon(canvas: Image, xy: tuple, fill: ImageColor=WHITE, outline: ImageColor=BLACK):
def draw_open_polygon(canvas, xy, fill=None, outline=BLACK, width=0):
    # type: (Image, tuple, ImageColor, ImageColor)
    draw_ctx = ImageDraw.Draw(canvas)
    draw_ctx.polygon(xy, fill=fill)
    draw_ctx.line(xy, fill=outline, width=width)
