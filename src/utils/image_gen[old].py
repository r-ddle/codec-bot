"""
Image generation for rank cards with MGS aesthetic
"""
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from io import BytesIO
import aiohttp
from config.shop_config import RANK_CARD_CONFIG
from config.settings import logger


class RankCardGenerator:
    """Generate beautiful MGS-themed rank cards"""

    def __init__(self):
        self.config = RANK_CARD_CONFIG
        self.fonts_loaded = False
        self.font_regular = None
        self.font_bold = None
        self.font_title = None
        self._load_fonts()

    def _load_fonts(self):
        """Load fonts for the rank card"""
        try:
            # Try to load custom fonts, fallback to default
            try:
                self.font_title = ImageFont.truetype("arial.ttf", 36)
                self.font_bold = ImageFont.truetype("arialbd.ttf", 28)
                self.font_regular = ImageFont.truetype("arial.ttf", 22)
                self.font_small = ImageFont.truetype("arial.ttf", 18)
            except:
                # Fallback to default font
                self.font_title = ImageFont.load_default()
                self.font_bold = ImageFont.load_default()
                self.font_regular = ImageFont.load_default()
                self.font_small = ImageFont.load_default()
                logger.warning("Using default fonts - custom fonts not found")

            self.fonts_loaded = True

        except Exception as e:
            logger.error(f"Error loading fonts: {e}")
            self.fonts_loaded = False

    async def generate_rank_card(
        self,
        username: str,
        rank: str,
        xp: int,
        gmp: int,
        level_progress: float,  # 0.0 to 1.0
        next_rank: str = None,
        avatar_url: str = None,
        messages_sent: int = 0,
        tactical_words: int = 0
    ) -> BytesIO:
        """
        Generate a rank card image

        Returns: BytesIO object containing the PNG image
        """
        try:
            # Create base image
            img = Image.new('RGB', (self.config['width'], self.config['height']),
                          self.config['background_color'])
            draw = ImageDraw.Draw(img)

            # Add subtle grid pattern (MGS-style)
            self._add_grid_pattern(draw)

            # Download and add avatar if provided
            avatar_x = 30
            avatar_y = 50
            if avatar_url and self.config['show_avatar']:
                try:
                    avatar = await self._download_avatar(avatar_url)
                    if avatar:
                        # Resize and make circular
                        avatar = avatar.resize((180, 180))
                        avatar = self._make_circular(avatar)
                        img.paste(avatar, (avatar_x, avatar_y), avatar)
                except Exception as e:
                    logger.error(f"Error adding avatar: {e}")

            # Draw main content area (right side)
            content_x = 240

            # Username
            draw.text((content_x, 40), username[:20], fill=self.config['text_color'],
                     font=self.font_title)

            # Rank with accent line
            rank_y = 90
            draw.text((content_x, rank_y), f"RANK: {rank.upper()}",
                     fill=self.config['accent_color'], font=self.font_bold)

            # Accent line under rank
            draw.rectangle([content_x, rank_y + 35, content_x + 200, rank_y + 38],
                          fill=self.config['accent_color'])

            # Stats section
            stats_y = 150
            stats_x = content_x

            # XP
            draw.text((stats_x, stats_y), f"XP:", fill=self.config['secondary_text_color'],
                     font=self.font_regular)
            draw.text((stats_x + 80, stats_y), f"{xp:,}", fill=self.config['text_color'],
                     font=self.font_bold)

            # GMP
            draw.text((stats_x, stats_y + 35), f"GMP:", fill=self.config['secondary_text_color'],
                     font=self.font_regular)
            draw.text((stats_x + 80, stats_y + 35), f"{gmp:,}", fill=self.config['text_color'],
                     font=self.font_bold)

            # Activity stats (right side)
            activity_x = stats_x + 280
            draw.text((activity_x, stats_y), f"Messages: {messages_sent:,}",
                     fill=self.config['secondary_text_color'], font=self.font_small)
            draw.text((activity_x, stats_y + 30), f"Tactical Words: {tactical_words:,}",
                     fill=self.config['secondary_text_color'], font=self.font_small)

            # Progress bar (bottom)
            if next_rank:
                progress_y = 240
                bar_x = content_x
                bar_width = 600
                bar_height = 30

                # Background
                draw.rectangle([bar_x, progress_y, bar_x + bar_width, progress_y + bar_height],
                             fill=self.config['progress_bar_bg'], outline=self.config['accent_color'])

                # Fill
                fill_width = int(bar_width * level_progress)
                if fill_width > 0:
                    draw.rectangle([bar_x, progress_y, bar_x + fill_width, progress_y + bar_height],
                                 fill=self.config['progress_bar_fill'])

                # Progress text
                progress_text = f"{int(level_progress * 100)}% to {next_rank}"
                # Center text in bar
                bbox = draw.textbbox((0, 0), progress_text, font=self.font_small)
                text_width = bbox[2] - bbox[0]
                text_x = bar_x + (bar_width - text_width) // 2
                draw.text((text_x, progress_y + 6), progress_text,
                         fill=self.config['text_color'], font=self.font_small)

            # Add MGS-style corner accents
            self._add_corner_accents(draw)

            # Convert to bytes
            buffer = BytesIO()
            img.save(buffer, format='PNG')
            buffer.seek(0)

            return buffer

        except Exception as e:
            logger.error(f"Error generating rank card: {e}")
            raise

    def _add_grid_pattern(self, draw):
        """Add subtle grid pattern for MGS aesthetic"""
        grid_color = (30, 30, 40, 50)  # Very subtle
        spacing = 20

        # Vertical lines
        for x in range(0, self.config['width'], spacing):
            draw.line([(x, 0), (x, self.config['height'])], fill=(25, 25, 35), width=1)

        # Horizontal lines
        for y in range(0, self.config['height'], spacing):
            draw.line([(0, y), (self.config['width'], y)], fill=(25, 25, 35), width=1)

    def _add_corner_accents(self, draw):
        """Add MGS-style corner accents"""
        accent = self.config['accent_color']
        size = 20
        width = 3

        # Top-left
        draw.line([(10, 10), (10 + size, 10)], fill=accent, width=width)
        draw.line([(10, 10), (10, 10 + size)], fill=accent, width=width)

        # Top-right
        draw.line([(self.config['width'] - 10 - size, 10), (self.config['width'] - 10, 10)],
                 fill=accent, width=width)
        draw.line([(self.config['width'] - 10, 10), (self.config['width'] - 10, 10 + size)],
                 fill=accent, width=width)

        # Bottom-left
        draw.line([(10, self.config['height'] - 10), (10 + size, self.config['height'] - 10)],
                 fill=accent, width=width)
        draw.line([(10, self.config['height'] - 10 - size), (10, self.config['height'] - 10)],
                 fill=accent, width=width)

        # Bottom-right
        draw.line([(self.config['width'] - 10 - size, self.config['height'] - 10),
                  (self.config['width'] - 10, self.config['height'] - 10)], fill=accent, width=width)
        draw.line([(self.config['width'] - 10, self.config['height'] - 10 - size),
                  (self.config['width'] - 10, self.config['height'] - 10)], fill=accent, width=width)

    async def _download_avatar(self, url: str) -> Image:
        """Download user avatar"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as resp:
                    if resp.status == 200:
                        data = await resp.read()
                        return Image.open(BytesIO(data))
        except Exception as e:
            logger.error(f"Error downloading avatar: {e}")
        return None

    def _make_circular(self, img: Image) -> Image:
        """Make image circular with alpha channel"""
        size = img.size
        mask = Image.new('L', size, 0)
        draw = ImageDraw.Draw(mask)
        draw.ellipse((0, 0) + size, fill=255)

        output = Image.new('RGBA', size, (0, 0, 0, 0))
        output.paste(img, (0, 0))
        output.putalpha(mask)

        return output
