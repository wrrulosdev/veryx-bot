import requests
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
from loguru import logger
from typing import Union, Tuple

from ...constants import BotConstants


class ImageUtilities:
    @staticmethod
    @logger.catch
    def create_welcome_image(avatar_url: str, num: int) -> BytesIO:
        """
        Create a welcome image for a new member by combining a background image,
        the member's avatar, and some welcome text.
        :param avatar_url: URL of the member's avatar.
        :param num: Member count
        :return: BytesIO object with the generated image.
        """
        try:
            # Load background image
            background: Image.Image = Image.open(BotConstants.WELCOME_BACKGROUND_PATH).convert("RGBA")
            width, height = background.size
            # Load avatar from URL
            avatar: Image.Image = ImageUtilities._get_avatar(avatar_url=avatar_url)
            avatar_x, avatar_y = ImageUtilities._get_avatar_position(avatar=avatar, width=width, height=height)
            # Apply avatar to background
            try:
                background.paste(avatar, (avatar_x, avatar_y), avatar)

            except ValueError:
                raise

            # Add text (welcome and number)
            ImageUtilities._add_text(background=background, width=width, height=height, avatar_y=avatar_y, avatar=avatar, num=num)
            # Save the image to a BytesIO object
            output: BytesIO = BytesIO()
            background.save(output, format="PNG")
            output.seek(0)
            return output

        except Exception as e:
            logger.error(f"Error creating welcome image: {e}")

    @staticmethod
    def _get_avatar(avatar_url: str) -> Image.Image:
        """
        Fetches the avatar image from the provided URL and resizes it.
        :param avatar_url: URL of the avatar image.
        :return: Resized avatar image.
        """
        response: requests.Response = requests.get(avatar_url)
        avatar: Image.Image = Image.open(BytesIO(response.content)).resize((400, 400))
        mask: Image.Image = avatar.convert("L").point(lambda x: min(x, 255))
        draw: ImageDraw.Draw = ImageDraw.Draw(mask)
        draw.ellipse((0, 0) + avatar.size, fill=255)
        avatar.putalpha(mask)
        return avatar

    @staticmethod
    def _get_avatar_position(avatar: Image.Image, width: int, height: int) -> Tuple[int, int]:
        """
        Calculates the position to center the avatar on the background.
        :param avatar: Avatar image.
        :param width: Width of the background image.
        :param height: Height of the background image.
        :return: (x, y) position for centering the avatar.
        """
        avatar_x: int = (width - avatar.width) // 2
        avatar_y: int = (height - avatar.height) // 2 - 200
        return avatar_x, avatar_y

    @staticmethod
    def _add_text(background: Image.Image, width: int, height: int, avatar_y: int, avatar: Image.Image, num: int) -> None:
        """
        Adds welcome and number text to the background image.
        :param background: Background image where text will be added.
        :param width: Width of the background image.
        :param height: Height of the background image.
        :param avatar_y: Y position of the avatar to calculate proper text spacing.
        :param avatar: Avatar image for reference.
        """
        draw = ImageDraw.Draw(background)
        font_large: ImageFont.FreeTypeFont = ImageFont.truetype("arial.ttf", 100)
        font_xlarge: ImageFont.FreeTypeFont = ImageFont.truetype("arial.ttf", 150)
        text_welcome: str = 'Welcome to Veryx!'
        text_number: str = f'#{str(num)}'
        text_welcome_x, text_welcome_y = ImageUtilities._get_text_position(draw, text_welcome, font_large, width,
                                                                           height, avatar_y, avatar)
        text_number_x, text_number_y = ImageUtilities._get_text_position(draw, text_number, font_xlarge, width,
                                                                         height, text_welcome_y, avatar)
        draw.text((text_welcome_x, text_welcome_y), text_welcome, font=font_large, fill="white")
        draw.text((text_number_x, text_number_y - 200), text_number, font=font_xlarge, fill="white")

    @staticmethod
    def _get_text_position(draw: ImageDraw.Draw, text: str, font: ImageFont.FreeTypeFont, width: int, height: int,
                           avatar_y: int, avatar: Image.Image) -> Tuple[int, int]:
        """
        Calculates the position of text on the image to center it.
        :param draw: The ImageDraw object to calculate text size.
        :param text: The text to be drawn.
        :param font: The font used to draw the text.
        :param width: Width of the background image.
        :param height: Height of the background image.
        :param avatar_y: Y position of the avatar to calculate proper spacing.
        :param avatar: Avatar image to determine the available space.
        :return: (x, y) position for centering the text.
        """
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width, text_height = bbox[2] - bbox[0], bbox[3] - bbox[1]
        x: int = (width - text_width) // 2
        y: int = avatar_y + avatar.height + 40
        return x, y
