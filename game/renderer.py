"""Renderer for Maze Explorer: dark neon aesthetics, dynamic HUD, and overlays."""

import math
import time
from typing import Any, Callable, List, Optional, Tuple

import pygame

from config import (
    BLIND_VISION_RADIUS_CELLS,
    CELL_WALL,
    COLOR_AGENT,
    COLOR_AGENT_GLOW,
    COLOR_AGENT_TRAIL,
    COLOR_BG,
    COLOR_BTN_DEFAULT,
    COLOR_BTN_HOVER,
    COLOR_BTN_TEXT,
    COLOR_COIN,
    COLOR_DANGER,
    COLOR_EXIT,
    COLOR_EXIT_LOCKED,
    COLOR_GEM,
    COLOR_HINT_PATH,
    COLOR_KEY,
    COLOR_PANEL_BG,
    COLOR_PANEL_BORDER,
    COLOR_PATH,
    COLOR_PLAYER,
    COLOR_PLAYER_GLOW,
    COLOR_PREVIEW_BAR,
    COLOR_START,
    COLOR_SUCCESS,
    COLOR_TEXT_ACCENT,
    COLOR_TEXT_MUTED,
    COLOR_TEXT_WHITE,
    COLOR_WALL,
    COLOR_WALL_BORDER,
    COLOR_WARNING,
    ITEM_COIN,
    ITEM_GEM,
    ITEM_KEY,
    MODE_RACE,
    PREVIEW_DURATION,
)
from game.agent import Agent
from game.maze_generator import Maze
from game.player import Player


def clamp_color(color: Any, alpha: Optional[float] = None) -> Tuple[int, ...]:
    """Safely clamp and convert color components into strictly valid 0-255 RGB or RGBA integer tuples."""
    if isinstance(color, (list, tuple)):
        vals = [int(max(0, min(255, round(float(c))))) for c in color[:3]]
    elif isinstance(color, str):
        try:
            parsed = pygame.Color(color)
            vals = [parsed.r, parsed.g, parsed.b]
        except Exception:
            vals = [255, 255, 255]
    elif hasattr(color, "r") and hasattr(color, "g") and hasattr(color, "b"):
        vals = [int(max(0, min(255, round(float(color.r))))), int(max(0, min(255, round(float(color.g))))), int(max(0, min(255, round(float(color.b)))))]
    else:
        vals = [255, 255, 255]

    while len(vals) < 3:
        vals.append(0)

    if alpha is not None:
        a = int(max(0, min(255, round(float(alpha)))))
        return (vals[0], vals[1], vals[2], a)
    return (vals[0], vals[1], vals[2])


class Particle:
    """Lightweight visual spark for collectible pickups."""

    def __init__(self, x: float, y: float, color: Tuple[int, int, int]) -> None:
        self.x, self.y = x, y
        self.color = color
        self.birth = time.time()
        angle = (hash((x, y, self.birth)) % 360) * 0.01745
        speed = 30.0 + (hash(angle) % 40)
        self.vx, self.vy = math.cos(angle) * speed, math.sin(angle) * speed

    def update(self, dt: float) -> bool:
        self.x += self.vx * dt
        self.y += self.vy * dt
        return (time.time() - self.birth) < 0.35

    def draw(self, surface: pygame.Surface) -> None:
        elapsed = time.time() - self.birth
        if elapsed >= 0.35:
            return
        pct = max(0.0, min(1.0, 1.0 - elapsed / 0.35))
        sz = max(1, int(3 * pct))
        surf = pygame.Surface((sz * 2, sz * 2), pygame.SRCALPHA)
        col = clamp_color(self.color, 255.0 * pct)
        pygame.draw.circle(surf, col, (sz, sz), sz)
        surface.blit(surf, (int(self.x - sz), int(self.y - sz)))


class Button:
    """Interactive UI Button and rich Card with hover, badges, and click support."""

    def __init__(
        self,
        rect: pygame.Rect,
        text: str,
        callback: Optional[Callable[[], None]] = None,
        tag: str = "",
        font_size: int = 20,
        subtitle: str = "",
        badge: str = "",
        accent_color: Optional[Tuple[int, int, int]] = None,
    ) -> None:
        self.rect = rect
        self.text = text
        self.callback = callback
        self.tag = tag
        self.subtitle = subtitle
        self.badge = badge
        self.accent_color = accent_color
        self.is_hovered = False
        self.is_selected = False

    def check_hover(self, mouse_pos: Tuple[int, int]) -> bool:
        self.is_hovered = self.rect.collidepoint(mouse_pos)
        return self.is_hovered

    def handle_click(self, mouse_pos: Tuple[int, int]) -> bool:
        if self.rect.collidepoint(mouse_pos) and self.callback:
            self.callback()
            return True
        return False

    def draw(
        self,
        surface: pygame.Surface,
        font: pygame.font.Font,
        font_small: Optional[pygame.font.Font] = None,
        font_badge: Optional[pygame.font.Font] = None,
    ) -> None:
        active = self.is_hovered or self.is_selected
        accent = self.accent_color or COLOR_TEXT_ACCENT

        if self.subtitle:
            # Rich interactive card
            bg = (35, 48, 68) if active else COLOR_PANEL_BG
            border = accent if active else COLOR_PANEL_BORDER
            border_w = 2 if active else 1

            pygame.draw.rect(surface, clamp_color(bg), self.rect, border_radius=10)
            pygame.draw.rect(surface, clamp_color(border), self.rect, width=border_w, border_radius=10)

            # Left accent highlight strip when hovered or selected
            if active:
                strip = pygame.Rect(self.rect.x, self.rect.y + 6, 5, self.rect.height - 12)
                pygame.draw.rect(surface, clamp_color(accent), strip, border_radius=2)

            # Title
            title_col = accent if active else COLOR_TEXT_WHITE
            txt = font.render(self.text, True, clamp_color(title_col))
            tx = self.rect.x + (26 if active else 20)
            ty = self.rect.y + 12
            surface.blit(txt, (tx, ty))

            # Subtitle
            sub_font = font_small or font
            sub_txt = sub_font.render(self.subtitle, True, clamp_color(COLOR_TEXT_MUTED))
            surface.blit(sub_txt, (tx, ty + txt.get_height() + 4))

            # Top-right pill badge
            if self.badge and font_badge:
                b_surf = font_badge.render(self.badge, True, clamp_color(accent if active else COLOR_TEXT_MUTED))
                bw, bh = b_surf.get_width() + 16, b_surf.get_height() + 6
                bx = self.rect.right - bw - 16
                by = self.rect.y + 12
                b_rect = pygame.Rect(bx, by, bw, bh)
                b_bg = pygame.Surface((bw, bh), pygame.SRCALPHA)
                pygame.draw.rect(b_bg, clamp_color(accent, 45 if active else 25), (0, 0, bw, bh), border_radius=5)
                surface.blit(b_bg, b_rect)
                pygame.draw.rect(surface, clamp_color(accent if active else COLOR_PANEL_BORDER), b_rect, width=1, border_radius=5)
                surface.blit(b_surf, b_surf.get_rect(center=b_rect.center))
        else:
            # Standard button
            bg = COLOR_BTN_HOVER if active else COLOR_BTN_DEFAULT
            border = accent if active else COLOR_PANEL_BORDER
            pygame.draw.rect(surface, clamp_color(bg), self.rect, border_radius=7)
            pygame.draw.rect(surface, clamp_color(border), self.rect, width=2 if active else 1, border_radius=7)
            color = accent if active else COLOR_BTN_TEXT
            txt = font.render(self.text, True, clamp_color(color))
            surface.blit(txt, txt.get_rect(center=self.rect.center))


class Renderer:
    """Manages display rendering, HUD, and overlays."""

    def __init__(self, surface: pygame.Surface) -> None:
        self.surface = surface
        self.width = surface.get_width()
        self.height = surface.get_height()
        self.particles: List[Particle] = []
        self.hud_height = 68
        self.cell_size = 24
        self.offset_x = 0
        self.offset_y = 0
        self._init_fonts()

    def _init_fonts(self) -> None:
        pygame.font.init()
        font_name = None
        for name in ["Segoe UI", "Inter", "Roboto", "Arial"]:
            if name.lower() in [f.lower() for f in pygame.font.get_fonts()]:
                font_name = name
                break
        self.font_title = pygame.font.SysFont(font_name, 38, bold=True)
        self.font_heading = pygame.font.SysFont(font_name, 24, bold=True)
        self.font_card_title = pygame.font.SysFont(font_name, 20, bold=True)
        self.font_body = pygame.font.SysFont(font_name, 17)
        self.font_body_bold = pygame.font.SysFont(font_name, 17, bold=True)
        self.font_small = pygame.font.SysFont(font_name, 13)
        self.font_badge = pygame.font.SysFont(font_name, 11, bold=True)

    def update_dimensions(self, width: int, height: int) -> None:
        self.width, self.height = width, height

    def calculate_grid_metrics(self, maze: Maze) -> None:
        avail_w, avail_h = self.width - 40, self.height - self.hud_height - 30
        self.cell_size = max(14, min(48, min(avail_w // maze.cols, avail_h // maze.rows)))
        self.offset_x = (self.width - maze.cols * self.cell_size) // 2
        self.offset_y = self.hud_height + ((self.height - self.hud_height - maze.rows * self.cell_size) // 2)

    def grid_to_screen(self, row: float, col: float) -> Tuple[int, int]:
        return (int(self.offset_x + col * self.cell_size), int(self.offset_y + row * self.cell_size))

    def spawn_particles(self, pos: Tuple[int, int], color: Tuple[int, int, int], count: int = 10) -> None:
        px, py = self.grid_to_screen(pos[0] + 0.5, pos[1] + 0.5)
        self.particles.extend([Particle(px, py, color) for _ in range(count)])

    def update_particles(self, dt: float) -> None:
        self.particles = [p for p in self.particles if p.update(dt)]

    def render_gameplay(
        self,
        maze: Maze,
        player: Player,
        level: int,
        score: int,
        elapsed_time: float,
        time_limit: Optional[int],
        hint_path: Optional[List[Tuple[int, int]]],
        hint_message: Optional[str],
        hint_cooldown_progress: float,
        agent: Optional[Agent] = None,
        is_blind: bool = False,
        preview_remaining: float = 0.0,
        game_mode: str = MODE_RACE,
    ) -> None:
        self.surface.fill(COLOR_BG)
        self._draw_maze(maze)
        if hint_path:
            self._draw_hint_path(hint_path)
        self._draw_portals(maze, player.has_key)
        self._draw_collectibles(maze)
        if agent is not None:
            self._draw_agent(agent)
        self._draw_player(player)
        for p in self.particles:
            p.draw(self.surface)
        if is_blind:
            self._draw_blindness(player, agent)
        self._draw_hud(player, level, score, elapsed_time, time_limit, hint_cooldown_progress, agent, game_mode, is_blind)
        if preview_remaining > 0.0:
            self._draw_preview_banner(preview_remaining)
        if hint_message:
            self._draw_status_toast(hint_message)

    def _draw_maze(self, maze: Maze) -> None:
        cs = self.cell_size
        for r in range(maze.rows):
            for c in range(maze.cols):
                rect = pygame.Rect(self.offset_x + c * cs, self.offset_y + r * cs, cs, cs)
                if maze.grid[r][c] == CELL_WALL:
                    pygame.draw.rect(self.surface, COLOR_WALL, rect)
                    pygame.draw.rect(self.surface, COLOR_WALL_BORDER, rect, 1)
                else:
                    pygame.draw.rect(self.surface, COLOR_PATH, rect)

    def _draw_portals(self, maze: Maze, has_key: bool) -> None:
        cs = self.cell_size
        pulse = (math.sin(time.time() * 4.0) + 1.0) * 0.5
        sx, sy = self.grid_to_screen(maze.start_pos[0], maze.start_pos[1])
        pygame.draw.rect(self.surface, clamp_color(COLOR_START), pygame.Rect(sx + cs * 0.15, sy + cs * 0.15, cs * 0.7, cs * 0.7), border_radius=4)

        ex, ey = self.grid_to_screen(maze.exit_pos[0] + 0.5, maze.exit_pos[1] + 0.5)
        locked = any(t == ITEM_KEY for t in maze.collectibles.values()) and not has_key
        color = COLOR_EXIT_LOCKED if locked else COLOR_EXIT
        glow_r = max(1, int(cs * 0.4 + pulse * (cs * 0.1)))
        aura = pygame.Surface((cs * 2, cs * 2), pygame.SRCALPHA)
        pygame.draw.circle(aura, clamp_color(color, 80 + pulse * 60), (cs, cs), glow_r)
        self.surface.blit(aura, (ex - cs, ey - cs))
        pygame.draw.circle(self.surface, clamp_color(color), (ex, ey), max(1, int(cs * 0.35)))
        pygame.draw.circle(self.surface, (255, 255, 255), (ex, ey), max(2, int(cs * 0.15)))

    def _draw_collectibles(self, maze: Maze) -> None:
        cs = self.cell_size
        bob = math.sin(time.time() * 5.0) * (cs * 0.08)
        for pos, item in maze.collectibles.items():
            cx, cy = int(self.offset_x + (pos[1] + 0.5) * cs), int(self.offset_y + (pos[0] + 0.5) * cs + bob)
            if item == ITEM_COIN:
                r = max(3, int(cs * 0.28))
                pygame.draw.circle(self.surface, COLOR_COIN, (cx, cy), r)
                pygame.draw.circle(self.surface, (255, 250, 200), (cx - 1, cy - 1), max(1, r // 2))
            elif item == ITEM_GEM:
                sz = max(4, int(cs * 0.32))
                pts = [(cx, cy - sz), (cx + sz, cy), (cx, cy + sz), (cx - sz, cy)]
                pygame.draw.polygon(self.surface, COLOR_GEM, pts)
                pygame.draw.polygon(self.surface, (255, 255, 255), pts, width=1)
            elif item == ITEM_KEY:
                kr = max(3, int(cs * 0.22))
                pygame.draw.circle(self.surface, COLOR_KEY, (cx - 4, cy), kr, width=2)
                pygame.draw.line(self.surface, COLOR_KEY, (cx - 4 + kr, cy), (cx + 8, cy), width=2)
                pygame.draw.line(self.surface, COLOR_KEY, (cx + 8, cy), (cx + 8, cy + 4), width=2)

    def _draw_player(self, player: Player) -> None:
        cs = self.cell_size
        px, py = int(self.offset_x + (player.visual_col + 0.5) * cs), int(self.offset_y + (player.visual_row + 0.5) * cs)
        r = max(4, int(cs * 0.35))
        aura = pygame.Surface((cs * 2, cs * 2), pygame.SRCALPHA)
        pygame.draw.circle(aura, clamp_color(COLOR_PLAYER_GLOW, 80), (cs, cs), r + 3)
        self.surface.blit(aura, (px - cs, py - cs))
        pygame.draw.circle(self.surface, clamp_color(COLOR_PLAYER), (px, py), r)
        pygame.draw.circle(self.surface, (255, 255, 255), (px, py), max(2, r // 2))

    def _draw_agent(self, agent: Agent) -> None:
        cs = self.cell_size
        now = time.time()
        for tr, tc, tt in agent.trail:
            age = now - tt
            if 0.0 <= age < 0.8:
                tx, ty = int(self.offset_x + (tc + 0.5) * cs), int(self.offset_y + (tr + 0.5) * cs)
                dot = pygame.Surface((8, 8), pygame.SRCALPHA)
                trail_alpha = 140.0 * (1.0 - age / 0.8)
                pygame.draw.circle(dot, clamp_color(COLOR_AGENT_TRAIL, trail_alpha), (4, 4), 3)
                self.surface.blit(dot, (tx - 4, ty - 4))

        ax, ay = int(self.offset_x + (agent.visual_col + 0.5) * cs), int(self.offset_y + (agent.visual_row + 0.5) * cs)
        r = max(4, int(cs * 0.35))
        aura = pygame.Surface((cs * 2, cs * 2), pygame.SRCALPHA)
        pygame.draw.circle(aura, clamp_color(COLOR_AGENT_GLOW, 90), (cs, cs), r + 3)
        self.surface.blit(aura, (ax - cs, ay - cs))
        pygame.draw.circle(self.surface, clamp_color(COLOR_AGENT), (ax, ay), r)
        pygame.draw.circle(self.surface, (255, 230, 240), (ax, ay), max(2, r // 2))

    def _draw_hint_path(self, hint_path: List[Tuple[int, int]]) -> None:
        cs = self.cell_size
        alpha = 140.0 + (math.sin(time.time() * 8.0) + 1.0) * 45.0
        for pos in hint_path[1:-1]:
            cx, cy = int(self.offset_x + (pos[1] + 0.5) * cs), int(self.offset_y + (pos[0] + 0.5) * cs)
            dot = pygame.Surface((cs, cs), pygame.SRCALPHA)
            pygame.draw.circle(dot, clamp_color(COLOR_HINT_PATH, alpha), (cs // 2, cs // 2), max(2, int(cs * 0.16)))
            self.surface.blit(dot, (cx - cs // 2, cy - cs // 2))

    def _draw_blindness(self, player: Player, agent: Optional[Agent] = None) -> None:
        cs = self.cell_size
        px, py = int(self.offset_x + (player.visual_col + 0.5) * cs), int(self.offset_y + (player.visual_row + 0.5) * cs)
        fog = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        fog.fill((13, 17, 23, 255))

        r_pix = max(10, int(cs * BLIND_VISION_RADIUS_CELLS))
        mask = pygame.Surface((r_pix * 2, r_pix * 2), pygame.SRCALPHA)
        mask.fill((13, 17, 23, 255))
        for step in range(16, 0, -1):
            frac = step / 16
            pygame.draw.circle(mask, (0, 0, 0, int(255 * (frac ** 2))), (r_pix, r_pix), int(r_pix * frac))
        fog.blit(mask, (px - r_pix, py - r_pix), special_flags=pygame.BLEND_RGBA_MIN)

        if agent is not None:
            ax, ay = int(self.offset_x + (agent.visual_col + 0.5) * cs), int(self.offset_y + (agent.visual_row + 0.5) * cs)
            if math.hypot(px - ax, py - ay) < r_pix * 1.5:
                ar = int(cs * 1.1)
                am = pygame.Surface((ar * 2, ar * 2), pygame.SRCALPHA)
                am.fill((13, 17, 23, 255))
                pygame.draw.circle(am, (0, 0, 0, 120), (ar, ar), ar)
                fog.blit(am, (ax - ar, ay - ar), special_flags=pygame.BLEND_RGBA_MIN)

        fog.fill((0, 0, 0, 0), pygame.Rect(0, 0, self.width, self.hud_height))
        self.surface.blit(fog, (0, 0))

    def _draw_preview_banner(self, preview_remaining: float) -> None:
        bw, bh = min(560, self.width - 40), 40
        bx, by = (self.width - bw) // 2, self.hud_height + 8
        surf = pygame.Surface((bw, bh), pygame.SRCALPHA)
        pygame.draw.rect(surf, (22, 27, 34, 230), (0, 0, bw, bh), border_radius=7)
        pygame.draw.rect(surf, COLOR_PREVIEW_BAR, (0, 0, bw, bh), width=2, border_radius=7)
        self.surface.blit(surf, (bx, by))
        txt = self.font_body_bold.render(f"MEMORIZE THE MAZE! Blindness in {preview_remaining:.1f}s", True, COLOR_TEXT_WHITE)
        self.surface.blit(txt, txt.get_rect(center=(self.width // 2, by + 15)))
        fill_w = int((bw - 20) * max(0.0, min(1.0, preview_remaining / PREVIEW_DURATION)))
        pygame.draw.rect(self.surface, COLOR_PREVIEW_BAR, pygame.Rect(bx + 10, by + bh - 7, fill_w, 3), border_radius=2)

    def _draw_hud(
        self, player: Player, level: int, score: int, elapsed_time: float, time_limit: Optional[int],
        hint_cooldown_progress: float, agent: Optional[Agent] = None, game_mode: str = MODE_RACE, is_blind: bool = False
    ) -> None:
        pygame.draw.rect(self.surface, COLOR_PANEL_BG, pygame.Rect(0, 0, self.width, self.hud_height))
        pygame.draw.line(self.surface, COLOR_PANEL_BORDER, (0, self.hud_height), (self.width, self.hud_height), 1)
        cy = self.hud_height // 2

        # Level & Score
        lvl = self.font_heading.render(f"LEVEL {level}", True, COLOR_TEXT_ACCENT)
        self.surface.blit(lvl, (16, cy - lvl.get_height() // 2))
        x = 16 + lvl.get_width() + 24

        sc_lbl = self.font_small.render("SCORE", True, COLOR_TEXT_MUTED)
        sc_val = self.font_body_bold.render(f"{score:,}", True, COLOR_TEXT_WHITE)
        col_w = max(sc_lbl.get_width(), sc_val.get_width()) + 22
        self.surface.blit(sc_lbl, (x, cy - 18))
        self.surface.blit(sc_val, (x, cy - 2))
        x += col_w

        # Timer
        rem = max(0.0, time_limit - elapsed_time) if time_limit is not None else elapsed_time
        t_color = COLOR_DANGER if (time_limit and rem <= 15) else COLOR_TEXT_WHITE
        tm_lbl = self.font_small.render("TIME" if time_limit is None else "REMAINING", True, COLOR_TEXT_MUTED)
        tm_val = self.font_body_bold.render(f"{int(rem)//60:02d}:{int(rem)%60:02d}", True, t_color)
        col_w = max(tm_lbl.get_width(), tm_val.get_width()) + 24
        self.surface.blit(tm_lbl, (x, cy - 18))
        self.surface.blit(tm_val, (x, cy - 2))
        x += col_w

        # Race stats
        if game_mode == MODE_RACE and agent is not None:
            self.surface.blit(self.font_small.render("YOU vs A* AGENT", True, COLOR_AGENT), (x, cy - 18))
            mv = self.font_body_bold.render(f"{player.moves_count} vs {agent.moves_count} moves", True, COLOR_TEXT_WHITE)
            self.surface.blit(mv, (x, cy - 2))
            if is_blind:
                self.surface.blit(self.font_small.render("[BLIND ON]", True, COLOR_WARNING), (x + mv.get_width() + 8, cy - 2))

        # Items (Coins, Gems, Key)
        ix = self.width - 310
        pygame.draw.circle(self.surface, COLOR_COIN, (ix, cy), 6)
        c_txt = self.font_body_bold.render(f"{player.coins_collected}", True, COLOR_TEXT_WHITE)
        self.surface.blit(c_txt, (ix + 10, cy - c_txt.get_height() // 2))

        pygame.draw.circle(self.surface, COLOR_GEM, (ix + 55, cy), 6)
        g_txt = self.font_body_bold.render(f"{player.gems_collected}", True, COLOR_TEXT_WHITE)
        self.surface.blit(g_txt, (ix + 65, cy - g_txt.get_height() // 2))

        k_col = COLOR_KEY if player.has_key else COLOR_PANEL_BORDER
        pygame.draw.circle(self.surface, clamp_color(k_col), (ix + 115, cy), 6, width=0 if player.has_key else 2)
        k_txt = self.font_small.render("KEY READY" if player.has_key else "NEED KEY", True, COLOR_SUCCESS if player.has_key else COLOR_TEXT_MUTED)
        self.surface.blit(k_txt, (ix + 125, cy - k_txt.get_height() // 2))

        # Hints
        hx = self.width - 100
        self.surface.blit(self.font_small.render(f"HINTS [H]: {player.hints_remaining}", True, COLOR_TEXT_ACCENT), (hx, cy - 16))
        pygame.draw.rect(self.surface, COLOR_PANEL_BORDER, pygame.Rect(hx, cy + 6, 80, 4), border_radius=2)
        if hint_cooldown_progress > 0:
            pygame.draw.rect(self.surface, COLOR_TEXT_ACCENT, pygame.Rect(hx, cy + 6, int(80 * hint_cooldown_progress), 4), border_radius=2)

    def _draw_status_toast(self, message: str) -> None:
        txt = self.font_body.render(message, True, COLOR_TEXT_WHITE)
        tw, th = txt.get_width(), txt.get_height()
        bx, by = (self.width - tw - 28) // 2, self.height - th - 20
        surf = pygame.Surface((tw + 28, th + 12), pygame.SRCALPHA)
        pygame.draw.rect(surf, clamp_color(COLOR_PANEL_BG, 230), (0, 0, tw + 28, th + 12), border_radius=7)
        pygame.draw.rect(surf, clamp_color(COLOR_TEXT_ACCENT, 180), (0, 0, tw + 28, th + 12), width=1, border_radius=7)
        self.surface.blit(surf, (bx, by))
        self.surface.blit(txt, (bx + 14, by + 6))

    def _draw_modal(self, title: str, title_color: Tuple[int, int, int], subtitle: str, stats: List[Tuple[str, str]], buttons: List[Button]) -> None:
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((13, 17, 23, 210))
        self.surface.blit(overlay, (0, 0))

        cw, ch = 480, 200 + len(stats) * 32 + len(buttons) * 45
        card = pygame.Rect((self.width - cw) // 2, (self.height - ch) // 2, cw, ch)
        pygame.draw.rect(self.surface, COLOR_PANEL_BG, card, border_radius=12)
        pygame.draw.rect(self.surface, clamp_color(title_color), card, width=2, border_radius=12)

        t_surf = self.font_heading.render(title, True, clamp_color(title_color))
        self.surface.blit(t_surf, t_surf.get_rect(center=(self.width // 2, card.y + 35)))

        if subtitle:
            s_surf = self.font_small.render(subtitle, True, COLOR_TEXT_MUTED)
            self.surface.blit(s_surf, s_surf.get_rect(center=(self.width // 2, card.y + 65)))

        sy = card.y + (90 if subtitle else 75)
        for i, (lbl, val) in enumerate(stats):
            ry = sy + i * 30
            self.surface.blit(self.font_body.render(lbl, True, COLOR_TEXT_MUTED), (card.x + 40, ry))
            v = self.font_body_bold.render(val, True, COLOR_TEXT_WHITE)
            self.surface.blit(v, (card.x + cw - 40 - v.get_width(), ry))

        for btn in buttons:
            btn.draw(self.surface, self.font_body_bold)

    def render_pause_overlay(self, buttons: List[Button]) -> None:
        self._draw_modal("GAME PAUSED", COLOR_TEXT_ACCENT, "Game is currently paused", [], buttons)

    def render_level_cleared(self, level: int, score: int, level_time: float, time_bonus: int, collectibles_bonus: int, buttons: List[Button], is_race: bool = False, player_moves: int = 0, agent_moves: int = 0) -> None:
        title = "RACE WON! AGENT DEFEATED!" if is_race else f"LEVEL {level} CLEARED!"
        sub = "You escaped first in the dark maze!" if is_race else "Level completed successfully"
        stats = [("Completion Time:", f"{level_time:.1f}s"), ("Collectibles Bonus:", f"+{collectibles_bonus:,}"), ("Time Bonus:", f"+{time_bonus:,}"), ("Total Score:", f"{score:,}")]
        if is_race:
            stats.insert(1, ("Moves (You vs Agent):", f"{player_moves} vs {agent_moves}"))
        self._draw_modal(title, COLOR_SUCCESS, sub, stats, buttons)

    def render_race_lost(self, level: int, score: int, buttons: List[Button], agent_time: float, player_moves: int, agent_moves: int) -> None:
        stats = [("Agent Moves:", f"{agent_moves}"), ("Your Moves:", f"{player_moves}"), ("Current Score:", f"{score:,}")]
        self._draw_modal("AGENT ESCAPED FIRST!", COLOR_AGENT, f"The rival solved the maze in {agent_time:.1f}s", stats, buttons)

    def render_game_over(self, level: int, score: int, buttons: List[Button]) -> None:
        self._draw_modal("TIME EXPIRED!", COLOR_DANGER, f"Defeated on Level {level}", [("Final Score:", f"{score:,}")], buttons)

    def _draw_menu_background(self) -> None:
        """Render dark neon grid background for menu interfaces."""
        self.surface.fill(COLOR_BG)
        for x in range(0, self.width, 42):
            pygame.draw.line(self.surface, (18, 24, 34), (x, 0), (x, self.height), 1)
        for y in range(0, self.height, 42):
            pygame.draw.line(self.surface, (18, 24, 34), (0, y), (self.width, y), 1)

    def render_mode_select(self, buttons: List[Button]) -> None:
        """Render Interface 1: User Only vs User vs Agent mode selection."""
        self._draw_menu_background()
        cx = self.width // 2

        # Step 1 breadcrumb pill
        step_text = "STEP 1 OF 2  •  CHOOSE GAMEPLAY MODE"
        step_surf = self.font_badge.render(step_text, True, COLOR_TEXT_ACCENT)
        sw, sh = step_surf.get_width() + 24, step_surf.get_height() + 8
        s_rect = pygame.Rect(cx - sw // 2, 38, sw, sh)
        s_bg = pygame.Surface((sw, sh), pygame.SRCALPHA)
        pygame.draw.rect(s_bg, (56, 189, 248, 25), (0, 0, sw, sh), border_radius=12)
        self.surface.blit(s_bg, s_rect)
        pygame.draw.rect(self.surface, clamp_color(COLOR_TEXT_ACCENT, 140), s_rect, width=1, border_radius=12)
        self.surface.blit(step_surf, step_surf.get_rect(center=s_rect.center))

        # Title & Subtitle
        title = self.font_title.render("MAZE EXPLORER", True, COLOR_TEXT_WHITE)
        self.surface.blit(title, title.get_rect(center=(cx, 90)))

        sub = self.font_body.render("Procedural 25x25 Labyrinth • Select your game mode to begin", True, COLOR_TEXT_MUTED)
        self.surface.blit(sub, sub.get_rect(center=(cx, 126)))

        # Interactive cards & buttons
        for btn in buttons:
            btn.draw(self.surface, self.font_card_title, self.font_small, self.font_badge)

        # Footer shortcut hint
        foot = self.font_small.render("Keyboard Shortcuts: [1 / U] User Only  •  [2 / A] User vs Agent  •  [Q] Quit", True, COLOR_TEXT_MUTED)
        self.surface.blit(foot, foot.get_rect(center=(cx, self.height - 24)))

    def render_level_select(self, buttons: List[Button], selected_mode: str) -> None:
        """Render Interface 2: Difficulty selection (Easy, Medium, Difficult, Hard)."""
        self._draw_menu_background()
        cx = self.width // 2

        # Step 2 breadcrumb pill
        step_text = "STEP 2 OF 2  •  SELECT DIFFICULTY LEVEL"
        step_surf = self.font_badge.render(step_text, True, (168, 85, 247))
        sw, sh = step_surf.get_width() + 24, step_surf.get_height() + 8
        s_rect = pygame.Rect(cx - sw // 2, 32, sw, sh)
        s_bg = pygame.Surface((sw, sh), pygame.SRCALPHA)
        pygame.draw.rect(s_bg, (168, 85, 247, 28), (0, 0, sw, sh), border_radius=12)
        self.surface.blit(s_bg, s_rect)
        pygame.draw.rect(self.surface, (168, 85, 247, 150), s_rect, width=1, border_radius=12)
        self.surface.blit(step_surf, step_surf.get_rect(center=s_rect.center))

        # Title
        title = self.font_title.render("CHOOSE YOUR LEVEL", True, COLOR_TEXT_WHITE)
        self.surface.blit(title, title.get_rect(center=(cx, 80)))

        # Selected mode status indicator
        is_race = (selected_mode == MODE_RACE)
        mode_label = "SELECTED: USER VS AGENT (RACE & BLIND FOG)" if is_race else "SELECTED: USER ONLY (SOLO EXPLORATION)"
        mode_color = COLOR_AGENT if is_race else COLOR_SUCCESS
        sub = self.font_body_bold.render(mode_label, True, clamp_color(mode_color))
        self.surface.blit(sub, sub.get_rect(center=(cx, 114)))

        grid_note = self.font_small.render("All levels generated on a fixed 25x25 grid layout with increasing challenges", True, COLOR_TEXT_MUTED)
        self.surface.blit(grid_note, grid_note.get_rect(center=(cx, 138)))

        # Interactive level cards & back button
        for btn in buttons:
            btn.draw(self.surface, self.font_card_title, self.font_small, self.font_badge)

        # Footer shortcut hint
        foot = self.font_small.render("Shortcuts: [1] Easy  •  [2] Medium  •  [3] Difficult  •  [4] Hard  •  [Esc] Back", True, COLOR_TEXT_MUTED)
        self.surface.blit(foot, foot.get_rect(center=(cx, self.height - 20)))

    def render_menu(self, buttons: List[Button], selected_difficulty: str = "") -> None:
        """Legacy compatibility wrapper for main menu rendering."""
        self.render_mode_select(buttons)

    def render_instructions(self, back_button: Button) -> None:
        self.surface.fill(COLOR_BG)
        title = self.font_heading.render("INSTRUCTIONS & CONTROLS", True, COLOR_TEXT_ACCENT)
        self.surface.blit(title, title.get_rect(center=(self.width // 2, 45)))

        cw, ch = 680, 510
        card = pygame.Rect((self.width - cw) // 2, 75, cw, ch)
        pygame.draw.rect(self.surface, COLOR_PANEL_BG, card, border_radius=10)
        pygame.draw.rect(self.surface, COLOR_PANEL_BORDER, card, width=1, border_radius=10)

        lines = [
            ("CONTROLS:", COLOR_TEXT_ACCENT),
            ("  • Arrow Keys / WASD  : Move player through corridors", COLOR_TEXT_WHITE),
            ("  • H                  : Request a hint route", COLOR_TEXT_WHITE),
            ("  • P or Escape        : Pause or resume current game", COLOR_TEXT_WHITE),
            ("  • R                  : Restart current maze level", COLOR_TEXT_WHITE),
            ("  • M                  : Exit back to Main Menu", COLOR_TEXT_WHITE),
            ("", COLOR_TEXT_WHITE),
            ("LABYRINTH & LEVELS:", COLOR_SUCCESS),
            ("  • The maze is always a 25x25 grid on all difficulty levels.", COLOR_TEXT_WHITE),
            ("  • Complete each level to advance to the next level with increasing rewards!", COLOR_TEXT_WHITE),
            ("  • Collect Coins (+50 pts) and Amethyst Gems (+150 pts).", COLOR_TEXT_WHITE),
            ("", COLOR_TEXT_WHITE),
            ("GAMEPLAY MODES:", COLOR_AGENT),
            ("  1. USER ONLY         : Casual solo maze exploration at your pace.", COLOR_TEXT_ACCENT),
            ("  2. USER VS AGENT     : 4s clear preview, then darkness fog engages!", COLOR_WARNING),
            ("  • Race the Agent to the exit portal.", COLOR_TEXT_WHITE),
            ("  • On Medium, Difficult & Hard, locate the Golden Key to unlock the portal!", COLOR_KEY),
        ]
        for i, (txt, col) in enumerate(lines):
            self.surface.blit(self.font_small.render(txt, True, col), (card.x + 25, card.y + 16 + i * 23))
        back_button.draw(self.surface, self.font_body_bold, self.font_small, self.font_badge)
