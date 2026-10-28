"""Central application controller, game loop, and state transitions for Maze Explorer."""

import time
from typing import Any, Dict, List, Optional, Tuple

import pygame

from config import (
    COLOR_COIN,
    COLOR_GEM,
    COLOR_KEY,
    COLOR_SUCCESS,
    DEFAULT_DIFFICULTY,
    DEFAULT_WINDOW_HEIGHT,
    DEFAULT_WINDOW_WIDTH,
    DIFFICULTY_SETTINGS,
    GAME_TITLE,
    ITEM_COIN,
    ITEM_GEM,
    AGENT_STEP_SPEEDS,
    ITEM_KEY,
    MAX_COLS,
    MAX_ROWS,
    MODE_RACE,
    MODE_SOLO,
    PREVIEW_DURATION,
    TARGET_FPS,
)
from game.agent import Agent
from game.maze_generator import Maze
from game.pathfinding import get_hint_route
from game.player import Player
from game.renderer import Button, Renderer
from game.storage import (
    load_settings,
    save_settings,
)

# Game State Constants
STATE_MODE_SELECT = "mode_select"
STATE_LEVEL_SELECT = "level_select"
STATE_MENU = STATE_MODE_SELECT  # Backward-compatible alias
STATE_INSTRUCTIONS = "instructions"
STATE_PLAYING = "playing"
STATE_PAUSED = "paused"
STATE_LEVEL_CLEAR = "level_clear"
STATE_GAME_OVER = "game_over"
STATE_RACE_LOST = "race_lost"


class MazeExplorerApp:
    """Manages the full lifecycle, event loop, and game states for Maze Explorer."""

    def __init__(self, headless: bool = False, seed: Optional[int] = None) -> None:
        self.headless = headless
        self.seed = seed
        self.running = False
        self.state = STATE_MODE_SELECT

        pygame.init()
        self.width, self.height = DEFAULT_WINDOW_WIDTH, DEFAULT_WINDOW_HEIGHT
        if self.headless:
            self.screen = pygame.Surface((self.width, self.height))
        else:
            self.screen = pygame.display.set_mode((self.width, self.height), pygame.DOUBLEBUF | pygame.RESIZABLE)
            pygame.display.set_caption(GAME_TITLE)

        self.clock = pygame.time.Clock()
        self.settings = load_settings()
        self.renderer = Renderer(self.screen)

        self.difficulty = str(self.settings.get("difficulty", DEFAULT_DIFFICULTY))
        if self.difficulty not in DIFFICULTY_SETTINGS:
            self.difficulty = DEFAULT_DIFFICULTY

        self.game_mode = MODE_RACE
        self.level = 1
        self.score = 0
        self.maze: Optional[Maze] = None
        self.player: Optional[Player] = None
        self.agent: Optional[Agent] = None

        self.preview_timer = 0.0
        self.is_blind = False
        self.race_started = False
        self.winner: Optional[str] = None

        self.level_start_time = 0.0
        self.pause_start_time = 0.0
        self.total_paused_time = 0.0
        self.last_cleared_time = 0.0
        self.last_cleared_bonus = 0
        self.last_time_bonus = 0

        self.active_hint_path: Optional[List[Tuple[int, int]]] = None
        self.hint_display_until = 0.0
        self.status_message: Optional[str] = None
        self.status_message_until = 0.0
        self.key_move_delay = 0.12
        self.last_move_time = 0.0

        self.mode_buttons: List[Button] = []
        self.level_buttons: List[Button] = []
        self.menu_buttons: List[Button] = []
        self.pause_buttons: List[Button] = []
        self.clear_buttons: List[Button] = []
        self.game_over_buttons: List[Button] = []
        self.race_lost_buttons: List[Button] = []
        self.instructions_back_btn: Optional[Button] = None

        self._build_ui_buttons()

    @property
    def current_buttons(self) -> List[Button]:
        """Return the active list of buttons for the current state."""
        if self.state in (STATE_MODE_SELECT, "menu"):
            return self.mode_buttons
        if self.state == STATE_LEVEL_SELECT:
            return self.level_buttons
        if self.state == STATE_PAUSED:
            return self.pause_buttons
        if self.state == STATE_LEVEL_CLEAR:
            return self.clear_buttons
        if self.state == STATE_RACE_LOST:
            return self.race_lost_buttons
        if self.state == STATE_GAME_OVER:
            return self.game_over_buttons
        if self.state == STATE_INSTRUCTIONS and self.instructions_back_btn:
            return [self.instructions_back_btn]
        return []

    def _build_ui_buttons(self) -> None:
        cx = self.width // 2

        # 1. Interface 1: Mode Selection Cards (User Only vs User vs Agent)
        card_w, card_h = min(660, self.width - 60), 84
        sy = 175
        self.mode_buttons = [
            Button(
                pygame.Rect(cx - card_w // 2, sy, card_w, card_h),
                "USER ONLY",
                lambda: self.select_mode(MODE_SOLO),
                tag="mode_solo",
                subtitle="Solo exploration at your own pace. Collect gems and coins.",
                badge="SOLO",
                accent_color=(56, 189, 248),
            ),
            Button(
                pygame.Rect(cx - card_w // 2, sy + 100, card_w, card_h),
                "USER VS AGENT",
                lambda: self.select_mode(MODE_RACE),
                tag="mode_race",
                subtitle="4s clear preview, then race the Agent under dark fog of war!",
                badge="RACE • BLIND FOG",
                accent_color=(244, 63, 94),
            ),
            Button(
                pygame.Rect(cx - 190, sy + 215, 180, 42),
                "HOW TO PLAY",
                lambda: self.switch_state(STATE_INSTRUCTIONS),
            ),
            Button(
                pygame.Rect(cx + 10, sy + 215, 180, 42),
                "QUIT GAME",
                self.quit_app,
            ),
        ]
        self.menu_buttons = self.mode_buttons

        # 2. Interface 2: Level Selection Cards (Easy, Medium, Difficult, Hard)
        lvl_w, lvl_h = min(660, self.width - 60), 72
        ly = 165
        levels = ["Easy", "Medium", "Difficult", "Hard"]
        self.level_buttons = [
            Button(
                pygame.Rect(cx - lvl_w // 2, ly + i * 84, lvl_w, lvl_h),
                d.upper(),
                lambda d=d: self.select_level_and_start(d),
                tag=f"level_{d}",
                subtitle=DIFFICULTY_SETTINGS[d]["description"],
                badge=DIFFICULTY_SETTINGS[d]["badge"],
                accent_color=DIFFICULTY_SETTINGS[d]["accent"],
            )
            for i, d in enumerate(levels)
        ] + [
            Button(
                pygame.Rect(cx - 150, ly + len(levels) * 84 + 10, 300, 42),
                "< BACK TO MODE SELECTION",
                lambda: self.switch_state(STATE_MODE_SELECT),
            )
        ]

        def center_stack(y_start: int, actions: List[Tuple[str, Any]]) -> List[Button]:
            bw, bh = 290, 44
            return [
                Button(pygame.Rect(cx - bw // 2, y_start + i * 54, bw, bh), lbl, act)
                for i, (lbl, act) in enumerate(actions)
            ]

        self.pause_buttons = center_stack(
            self.height // 2 - 30,
            [
                ("RESUME", self.resume_game),
                ("RESTART LEVEL", self.restart_level),
                ("MAIN MENU", lambda: self.switch_state(STATE_MODE_SELECT)),
            ],
        )
        self.clear_buttons = center_stack(
            self.height // 2 + 75,
            [
                ("NEXT LEVEL", self.advance_level),
                ("MAIN MENU", lambda: self.switch_state(STATE_MODE_SELECT)),
            ],
        )
        self.race_lost_buttons = center_stack(
            self.height // 2 + 55,
            [
                ("RETRY RACE", self.restart_level),
                ("MAIN MENU", lambda: self.switch_state(STATE_MODE_SELECT)),
            ],
        )
        self.game_over_buttons = center_stack(
            self.height // 2 + 25,
            [
                ("PLAY AGAIN", lambda: self.start_new_game(self.game_mode)),
                ("MAIN MENU", lambda: self.switch_state(STATE_MODE_SELECT)),
            ],
        )
        self.instructions_back_btn = Button(
            pygame.Rect(cx - 100, self.height - 70, 200, 40),
            "BACK TO MENU",
            lambda: self.switch_state(STATE_MODE_SELECT),
        )

    def select_mode(self, mode: str) -> None:
        """Switch from Interface 1 (Mode Selection) to Interface 2 (Level Selection)."""
        self.game_mode = mode
        self.switch_state(STATE_LEVEL_SELECT)

    def select_level_and_start(self, difficulty: str) -> None:
        """Set difficulty and start game from Interface 2."""
        self.set_difficulty(difficulty)
        self.start_new_game(mode=self.game_mode)

    def set_difficulty(self, diff: str) -> None:
        if diff in DIFFICULTY_SETTINGS:
            self.difficulty = diff
            self.settings["difficulty"] = diff
            save_settings(self.settings)

    def switch_state(self, new_state: str) -> None:
        self.state = new_state

    def start_new_game(self, mode: str = MODE_RACE) -> None:
        self.game_mode = mode
        self.level = 1
        self.score = 0
        self._init_level(self.level)
        self.state = STATE_PLAYING

    def _init_level(self, level: int) -> None:
        cfg = DIFFICULTY_SETTINGS.get(self.difficulty, DIFFICULTY_SETTINGS["Medium"])
        
        # Grid dimensions: Always fixed 25x25 on all levels and difficulties
        rows = 25
        cols = 25

        seed = (self.seed + level * 107) if self.seed is not None else None
        coins = min(32, int(cfg.get("coin_count", 8)) + (level - 1) * 3)
        gems = min(16, int(cfg.get("gem_count", 4)) + (level - 1) * 2)
        require_key = bool(cfg.get("require_key", False))

        self.maze = Maze(
            rows=rows,
            cols=cols,
            seed=seed,
            coin_count=coins,
            gem_count=gems,
            require_key=require_key,
        )
        self.player = Player(start_pos=self.maze.start_pos, max_hints=cfg.get("max_hints", 3))
        self.player.score = self.score

        self.level_start_time = time.time()
        self.total_paused_time = 0.0
        self.active_hint_path = None
        self.hint_display_until = 0.0
        self.status_message = None
        self.winner = None

        if self.game_mode == MODE_RACE:
            base_speed = float(cfg.get("agent_speed", AGENT_STEP_SPEEDS.get(self.difficulty, 0.32)))
            level_agent_speed = max(0.12, base_speed - (level - 1) * 0.015)
            self.agent = Agent(
                start_pos=self.maze.start_pos,
                difficulty=self.difficulty,
                step_interval=level_agent_speed,
            )
            self.agent.calculate_path(self.maze)
            
            preview_dur = float(cfg.get("preview_duration", PREVIEW_DURATION))
            self.preview_timer = preview_dur
            self.is_blind = False
            self.race_started = False
            self._show_toast(f"LEVEL {level}: MEMORIZE 25x25 MAZE! Blindness in {int(preview_dur)}s!", 3.5)
        else:
            self.agent = None
            self.preview_timer = 0.0
            self.is_blind = False
            self.race_started = True
            self._show_toast(f"LEVEL {level} - 25x25 LABYRINTH! Find the exit!", 2.5)

        self.renderer.calculate_grid_metrics(self.maze)

    def restart_level(self) -> None:
        self._init_level(self.level)
        self.state = STATE_PLAYING

    def resume_game(self) -> None:
        if self.pause_start_time > 0:
            self.total_paused_time += (time.time() - self.pause_start_time)
            self.pause_start_time = 0.0
        self.state = STATE_PLAYING

    def pause_game(self) -> None:
        self.pause_start_time = time.time()
        self.state = STATE_PAUSED

    def advance_level(self) -> None:
        self.level += 1
        self._init_level(self.level)
        self.state = STATE_PLAYING

    def trigger_hint(self) -> None:
        if not self.maze or not self.player:
            return
        cooldown = float(DIFFICULTY_SETTINGS.get(self.difficulty, {}).get("hint_cooldown", 5.0))
        now = time.time()
        if self.player.hints_remaining <= 0:
            self._show_toast("No hints remaining on this level!")
            return
        if (now - self.player.last_hint_time) < cooldown:
            self._show_toast(f"Hint cooling down ({int(cooldown - (now - self.player.last_hint_time)) + 1}s remaining)")
            return

        route = get_hint_route(self.maze, self.player.pos, self.player.has_key)
        if route and len(route) > 1:
            self.active_hint_path = route
            self.hint_display_until = now + 4.5
            self.player.hints_remaining -= 1
            self.player.last_hint_time = now
            self._show_toast("Hint route displayed!")
        else:
            self._show_toast("No route found.")

    def _show_toast(self, message: str, duration: float = 2.5) -> None:
        self.status_message = message
        self.status_message_until = time.time() + duration

    def _get_level_elapsed_time(self) -> float:
        if self.state == STATE_PAUSED:
            return max(0.0, self.pause_start_time - self.level_start_time - self.total_paused_time)
        return max(0.0, time.time() - self.level_start_time - self.total_paused_time)

    def handle_events(self) -> None:
        pos = pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.quit_app()
                return
            elif event.type == pygame.VIDEORESIZE:
                self.width, self.height = event.w, event.h
                if not self.headless:
                    self.screen = pygame.display.set_mode((self.width, self.height), pygame.DOUBLEBUF | pygame.RESIZABLE)
                self.renderer.update_dimensions(self.width, self.height)
                self._build_ui_buttons()
                if self.maze:
                    self.renderer.calculate_grid_metrics(self.maze)
            elif event.type == pygame.MOUSEMOTION:
                self._handle_mouse_hover(pos)
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self._handle_mouse_click(pos)
            elif event.type == pygame.KEYDOWN:
                self._handle_keydown(event.key)

    def _handle_mouse_hover(self, pos: Tuple[int, int]) -> None:
        for btn in self.current_buttons:
            btn.check_hover(pos)

    def _handle_mouse_click(self, pos: Tuple[int, int]) -> None:
        for btn in self.current_buttons:
            if btn.handle_click(pos):
                break

    def _handle_keydown(self, key: int) -> None:
        if self.state == STATE_PLAYING:
            if key in (pygame.K_p, pygame.K_ESCAPE): self.pause_game()
            elif key == pygame.K_h: self.trigger_hint()
            elif key == pygame.K_r: self.restart_level()
            elif key == pygame.K_m: self.switch_state(STATE_MODE_SELECT)
            else: self._process_movement_key(key)
        elif self.state == STATE_PAUSED:
            if key in (pygame.K_p, pygame.K_ESCAPE): self.resume_game()
            elif key == pygame.K_r: self.restart_level()
            elif key == pygame.K_m: self.switch_state(STATE_MODE_SELECT)
        elif self.state in (STATE_LEVEL_CLEAR, STATE_RACE_LOST, STATE_GAME_OVER):
            if key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_r):
                if self.state == STATE_LEVEL_CLEAR: self.advance_level()
                elif self.state == STATE_RACE_LOST: self.restart_level()
                else: self.start_new_game(mode=self.game_mode)
            elif key == pygame.K_m:
                self.switch_state(STATE_MODE_SELECT)
        elif self.state == STATE_INSTRUCTIONS:
            if key in (pygame.K_ESCAPE, pygame.K_RETURN, pygame.K_SPACE, pygame.K_m):
                self.switch_state(STATE_MODE_SELECT)
        elif self.state in (STATE_MODE_SELECT, "menu"):
            if key in (pygame.K_1, pygame.K_u):
                self.select_mode(MODE_SOLO)
            elif key in (pygame.K_2, pygame.K_a):
                self.select_mode(MODE_RACE)
            elif key in (pygame.K_RETURN, pygame.K_SPACE):
                self.select_mode(self.game_mode)
            elif key == pygame.K_h:
                self.switch_state(STATE_INSTRUCTIONS)
            elif key in (pygame.K_q, pygame.K_ESCAPE):
                self.quit_app()
        elif self.state == STATE_LEVEL_SELECT:
            if key in (pygame.K_1, pygame.K_e):
                self.select_level_and_start("Easy")
            elif key in (pygame.K_2, pygame.K_m):
                self.select_level_and_start("Medium")
            elif key in (pygame.K_3, pygame.K_d):
                self.select_level_and_start("Difficult")
            elif key in (pygame.K_4, pygame.K_h):
                self.select_level_and_start("Hard")
            elif key in (pygame.K_ESCAPE, pygame.K_BACKSPACE):
                self.switch_state(STATE_MODE_SELECT)
            elif key in (pygame.K_RETURN, pygame.K_SPACE):
                self.select_level_and_start(self.difficulty)

    def _try_move(self, dr: int, dc: int) -> bool:
        if (dr or dc) and self.player and self.maze and self.player.move(dr, dc, self.maze):
            self.last_move_time = time.time()
            self._on_player_moved()
            return True
        return False

    def _process_movement_key(self, key: int) -> None:
        deltas = {pygame.K_UP: (-1, 0), pygame.K_w: (-1, 0), pygame.K_DOWN: (1, 0), pygame.K_s: (1, 0), pygame.K_LEFT: (0, -1), pygame.K_a: (0, -1), pygame.K_RIGHT: (0, 1), pygame.K_d: (0, 1)}
        if key in deltas:
            dr, dc = deltas[key]
            self._try_move(dr, dc)

    def _handle_continuous_movement(self) -> None:
        now = time.time()
        if (now - self.last_move_time) < self.key_move_delay:
            return
        keys = pygame.key.get_pressed()
        dr = (-1 if (keys[pygame.K_UP] or keys[pygame.K_w]) else (1 if (keys[pygame.K_DOWN] or keys[pygame.K_s]) else 0))
        dc = (-1 if (keys[pygame.K_LEFT] or keys[pygame.K_a]) else (1 if (keys[pygame.K_RIGHT] or keys[pygame.K_d]) else 0))
        if dr or dc:
            self._try_move(dr, dc)

    def _on_player_moved(self) -> None:
        if not self.player or not self.maze:
            return
        collected = self.player.check_collectibles(self.maze)
        if collected:
            self.score = self.player.score
            if collected == ITEM_COIN:
                self.renderer.spawn_particles(self.player.pos, COLOR_COIN, 8)
                self._show_toast("Collected Coin! +50 pts", 1.2)
            elif collected == ITEM_GEM:
                self.renderer.spawn_particles(self.player.pos, COLOR_GEM, 12)
                self._show_toast("Found Amethyst Gem! +150 pts", 1.5)
            elif collected == ITEM_KEY:
                self.renderer.spawn_particles(self.player.pos, COLOR_KEY, 16)
                self._show_toast("Golden Key Acquired! Exit Unlocked!", 2.5)
            if self.active_hint_path:
                self.active_hint_path = get_hint_route(self.maze, self.player.pos, self.player.has_key)

        if self.player.pos == self.maze.exit_pos:
            if any(t == ITEM_KEY for t in self.maze.collectibles.values()) and not self.player.has_key:
                self._show_toast("The Exit Portal is locked! Find the Golden Key first!", 2.0)
            else:
                self.winner = "player" if (self.game_mode == MODE_RACE and self.winner is None) else self.winner
                self._complete_level(is_race=(self.game_mode == MODE_RACE))

    def _complete_level(self, is_race: bool = False) -> None:
        cfg = DIFFICULTY_SETTINGS.get(self.difficulty, DIFFICULTY_SETTINGS["Medium"])
        elapsed = self._get_level_elapsed_time()
        base_bonus = int(cfg.get("base_clear_bonus", 500)) + (self.level - 1) * 250 + (1500 if is_race else 0)
        time_limit = cfg.get("time_limit")
        time_bonus = int(max(0.0, time_limit - elapsed) * 25) if time_limit is not None else max(0, int(1000 - elapsed * 10))

        self.score += base_bonus + time_bonus
        self.player.score = self.score
        self.last_cleared_time = elapsed
        self.last_cleared_bonus = base_bonus
        self.last_time_bonus = time_bonus
        self.renderer.spawn_particles(self.maze.exit_pos, COLOR_SUCCESS, 24)

        self.state = STATE_LEVEL_CLEAR

    def _handle_race_lost(self) -> None:
        self.state = STATE_RACE_LOST

    def _handle_game_over(self) -> None:
        self.state = STATE_GAME_OVER

    def update(self, dt: float) -> None:
        self.renderer.update_particles(dt)
        if self.state == STATE_PLAYING and self.player and self.maze:
            if self.game_mode == MODE_RACE and self.preview_timer > 0.0:
                self.preview_timer -= dt
                if self.preview_timer <= 0.0:
                    self.preview_timer = 0.0
                    self.is_blind = True
                    self.race_started = True
                    self._show_toast("BLINDNESS ACTIVE! RACE TO THE EXIT!", 2.5)

            if self.game_mode == MODE_RACE and self.agent and self.race_started:
                self.agent.update(dt, self.maze)
                self.agent.update_visual_pos()
                if self.agent.finished and self.winner is None:
                    self.winner = "agent"
                    self._handle_race_lost()
                    return

            self._handle_continuous_movement()
            self.player.update_visual_pos()

            time_limit = DIFFICULTY_SETTINGS.get(self.difficulty, {}).get("time_limit")
            if time_limit is not None and self._get_level_elapsed_time() >= time_limit:
                self._handle_game_over()
                return

            if self.active_hint_path and time.time() > self.hint_display_until:
                self.active_hint_path = None
            if self.status_message and time.time() > self.status_message_until:
                self.status_message = None

    def render(self) -> None:
        if self.state in (STATE_PLAYING, STATE_PAUSED) and self.maze and self.player:
            cfg = DIFFICULTY_SETTINGS.get(self.difficulty, DIFFICULTY_SETTINGS["Medium"])
            cd = float(cfg.get("hint_cooldown", 5.0))
            prog = min(1.0, (time.time() - self.player.last_hint_time) / cd) if self.player else 0.0

            self.renderer.render_gameplay(
                maze=self.maze, player=self.player, level=self.level, score=self.score,
                elapsed_time=self._get_level_elapsed_time(), time_limit=cfg.get("time_limit"),
                hint_path=self.active_hint_path, hint_message=self.status_message,
                hint_cooldown_progress=prog, agent=self.agent, is_blind=self.is_blind,
                preview_remaining=self.preview_timer, game_mode=self.game_mode,
            )
            if self.state == STATE_PAUSED:
                self.renderer.render_pause_overlay(self.pause_buttons)

        elif self.state == STATE_LEVEL_CLEAR:
            p_moves = self.player.moves_count if self.player else 0
            a_moves = self.agent.moves_count if self.agent else 0
            self.renderer.render_level_cleared(
                level=self.level, score=self.score, level_time=self.last_cleared_time,
                time_bonus=self.last_time_bonus, collectibles_bonus=self.last_cleared_bonus,
                buttons=self.clear_buttons, is_race=(self.game_mode == MODE_RACE),
                player_moves=p_moves, agent_moves=a_moves,
            )
        elif self.state == STATE_RACE_LOST:
            p_moves = self.player.moves_count if self.player else 0
            a_moves = self.agent.moves_count if self.agent else 0
            self.renderer.render_race_lost(
                level=self.level, score=self.score, buttons=self.race_lost_buttons,
                agent_time=self._get_level_elapsed_time(), player_moves=p_moves, agent_moves=a_moves,
            )
        elif self.state == STATE_GAME_OVER:
            self.renderer.render_game_over(level=self.level, score=self.score, buttons=self.game_over_buttons)
        elif self.state in (STATE_MODE_SELECT, "menu"):
            self.renderer.render_mode_select(self.mode_buttons)
        elif self.state == STATE_LEVEL_SELECT:
            self.renderer.render_level_select(self.level_buttons, self.game_mode)
        elif self.state == STATE_INSTRUCTIONS and self.instructions_back_btn:
            self.renderer.render_instructions(self.instructions_back_btn)

        if not self.headless:
            pygame.display.flip()

    def run(self, max_frames: Optional[int] = None) -> None:
        self.running = True
        frame_count = 0
        while self.running:
            dt = min(self.clock.tick(TARGET_FPS) / 1000.0, 0.1)
            self.handle_events()
            self.update(dt)
            self.render()
            frame_count += 1
            if max_frames is not None and frame_count >= max_frames:
                break
        pygame.quit()

    def quit_app(self) -> None:
        self.running = False
