"""
Custom Welcome Image Generator for Discord Bot (clean version, no emoji)
- 2x render/downsample for crisp text
- Gold ring avatar, subtle gradient bg
- Robust avatar fetching and font fitting
"""

import io
import asyncio
import aiohttp
import logging
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import discord

LOGGER = logging.getLogger(__name__)

class WelcomeImageGenerator:
    def __init__(
        self,
        width: int = 800,
        height: int = 400,
        bg_top=(0, 0, 0),
        bg_bottom=(18, 18, 18),
        gold=(255, 215, 0),
        white=(255, 255, 255),
        text_margin=40,
        title_size_max=32,
        subtitle_size_max=28,
        text_size_max=20,
        avatar_size=200,
        avatar_ring=6,  # thickness of the gold ring (0 = no ring)
    ):
        # Base canvas (render at 2x for quality then downscale)
        self.width = width
        self.height = height
        self.scale = 2
        self.W = width * self.scale
        self.H = height * self.scale

        # Colors
        self.bg_top = bg_top
        self.bg_bottom = bg_bottom
        self.gold = gold
        self.white = white

        # Layout
        self.text_margin = text_margin * self.scale
        self.title_size_max = title_size_max * self.scale
        self.subtitle_size_max = subtitle_size_max * self.scale
        self.text_size_max = text_size_max * self.scale
        self.avatar_size = avatar_size * self.scale
        self.avatar_ring = avatar_ring * self.scale

        # Fonts
        self.bold_font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
        self.reg_font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

    async def create_welcome_image(self, member: discord.Member, guild_name: str = "RIVALZ MLB THE SHOW"):
        """Return a discord.File('welcome.png') with a premium welcome card."""
        try:
            # --- Base ---
            img = Image.new("RGB", (self.W, self.H), self.bg_top)
            draw = ImageDraw.Draw(img)

            # Gradient background
            for y in range(self.H):
                t = y / max(1, self.H - 1)
                r = int(self.bg_top[0] + (self.bg_bottom[0] - self.bg_top[0]) * t)
                g = int(self.bg_top[1] + (self.bg_bottom[1] - self.bg_top[1]) * t)
                b = int(self.bg_top[2] + (self.bg_bottom[2] - self.bg_top[2]) * t)
                draw.line([(0, y), (self.W, y)], fill=(r, g, b))

            # --- Avatar ---
            avatar = await self._get_user_avatar(member)
            if avatar is None:
                avatar = self._fallback_initials_avatar(member.display_name)

            avatar = avatar.resize((self.avatar_size, self.avatar_size), Image.Resampling.LANCZOS)
            mask = Image.new("L", (self.avatar_size, self.avatar_size), 0)
            ImageDraw.Draw(mask).ellipse((0, 0, self.avatar_size, self.avatar_size), fill=255)

            ax = (self.W - self.avatar_size) // 2
            ay = int(40 * self.scale)
            avatar_rgba = avatar.convert("RGBA")
            avatar_rgba.putalpha(mask)

            if self.avatar_ring > 0:
                ring_img = Image.new(
                    "RGBA",
                    (self.avatar_size + self.avatar_ring * 2, self.avatar_size + self.avatar_ring * 2),
                    (0, 0, 0, 0),
                )
                ring_draw = ImageDraw.Draw(ring_img)
                ring_draw.ellipse(
                    (0, 0, self.avatar_size + self.avatar_ring * 2, self.avatar_size + self.avatar_ring * 2),
                    fill=(0, 0, 0, 0),
                    outline=self.gold,
                    width=self.avatar_ring,
                )
                img.paste(ring_img, (ax - self.avatar_ring, ay - self.avatar_ring), ring_img)

            img.paste(avatar_rgba, (ax, ay), avatar_rgba)

            # --- Texts (no emojis) ---
            welcome_text = f"Hey, {member.display_name}!"
            title_text = f"Welcome to {guild_name}!"

            # Fonts
            title_font = self._fit_font(self.bold_font_path, title_text, self.title_size_max, draw, self.W - 2 * self.text_margin)
            subtitle_font = self._fit_font(self.bold_font_path, welcome_text, self.subtitle_size_max, draw, self.W - 2 * self.text_margin)

            wy = int(260 * self.scale)
            ty = int(310 * self.scale)
            wx = self._center_x(draw, welcome_text, subtitle_font)
            tx = self._center_x(draw, title_text, title_font)

            stroke_w = max(2, self.scale)

            draw.text((wx, wy), welcome_text, font=subtitle_font, fill=self.white, stroke_width=stroke_w, stroke_fill=(0, 0, 0))
            draw.text((tx, ty), title_text, font=title_font, fill=self.gold, stroke_width=stroke_w, stroke_fill=(0, 0, 0))

            # Downscale + sharpen
            img = img.resize((self.width, self.height), Image.Resampling.LANCZOS)
            img = img.filter(ImageFilter.UnsharpMask(radius=1, percent=140, threshold=2))

            buf = io.BytesIO()
            img.save(buf, format="PNG", optimize=True)
            buf.seek(0)
            return discord.File(buf, filename="welcome.png")

        except Exception as e:
            LOGGER.error(f"Error creating welcome image: {e}", exc_info=True)
            return None

    async def _get_user_avatar(self, member: discord.Member):
        """Downloads the user's display avatar as a PIL image (RGBA). Returns None on failure."""
        try:
            url = str(member.display_avatar.url)
            timeout = aiohttp.ClientTimeout(total=10)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url) as resp:
                    if resp.status == 200:
                        data = await resp.read()
                        return Image.open(io.BytesIO(data)).convert("RGB")
        except Exception as e:
            LOGGER.error(f"Error downloading avatar: {e}")
        return None

    def _fallback_initials_avatar(self, name: str):
        """Create a simple initials-based avatar if no image is available."""
        size = self.avatar_size
        img = Image.new("RGB", (size, size), (24, 24, 24))
        draw = ImageDraw.Draw(img)
        parts = [p for p in name.strip().split() if p]
        initials = (parts[0][0] + (parts[1][0] if len(parts) > 1 else "")).upper() if parts else "U"
        font = self._fit_font(self.bold_font_path, initials, int(size * 0.6), draw, size - int(size * 0.15))
        w, h = self._text_size(draw, initials, font)
        draw.ellipse((0, 0, size, size), fill=(40, 40, 40))
        draw.text(((size - w)//2, (size - h)//2), initials, font=font, fill=self.gold)
        return img

    def _center_x(self, draw, text, font) -> int:
        w, _ = self._text_size(draw, text, font)
        return (self.W - w) // 2

    def _text_size(self, draw, text, font):
        bbox = draw.textbbox((0, 0), text, font=font)
        return bbox[2] - bbox[0], bbox[3] - bbox[1]

    def _fit_font(self, path, text, max_px, draw, max_width):
        try:
            _ = ImageFont.truetype(path, 12)
            path_ok = True
        except Exception:
            path_ok = False
        if not path_ok:
            return ImageFont.load_default()

        lo, hi = 10, max_px
        best = lo
        while lo <= hi:
            mid = (lo + hi) // 2
            font = ImageFont.truetype(path, mid)
            w, _ = self._text_size(draw, text, font)
            if w <= max_width:
                best = mid
                lo = mid + 1
            else:
                hi = mid - 1
        return ImageFont.truetype(path, best)


