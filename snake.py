import json
import math
import random
from collections import deque
from pathlib import Path

import pygame


CELL_SIZE = 28
GRID_WIDTH = 28
GRID_HEIGHT = 19
HUD_HEIGHT = 76
BOARD_WIDTH = CELL_SIZE * GRID_WIDTH
BOARD_HEIGHT = CELL_SIZE * GRID_HEIGHT
SCREEN_WIDTH = BOARD_WIDTH
SCREEN_HEIGHT = HUD_HEIGHT + BOARD_HEIGHT
RENDER_FPS = 60

BACKGROUND = (10, 14, 18)
BOARD = (17, 23, 28)
GRID = (25, 33, 39)
TEXT = (232, 239, 242)
MUTED = (132, 148, 155)
GREEN = (62, 207, 126)
GREEN_DARK = (28, 139, 82)
APPLE = (244, 91, 94)
GOLD = (255, 196, 72)

UP = (0, -1)
DOWN = (0, 1)
LEFT = (-1, 0)
RIGHT = (1, 0)
OPPOSITE = {UP: DOWN, DOWN: UP, LEFT: RIGHT, RIGHT: LEFT}

SAVE_FILE = Path(__file__).with_name("snake_high_score.json")


def load_high_score():
    try:
        return max(0, int(json.loads(SAVE_FILE.read_text(encoding="utf-8"))["high_score"]))
    except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError):
        return 0


def save_high_score(score):
    try:
        SAVE_FILE.write_text(json.dumps({"high_score": score}), encoding="utf-8")
    except OSError:
        pass


def get_font(size, bold=False):
    candidates = ["Microsoft YaHei UI", "Microsoft YaHei", "SimHei", "Arial"]
    return pygame.font.SysFont(candidates, size, bold=bold)


class Snake:
    def __init__(self):
        self.reset()

    def reset(self):
        center = (GRID_WIDTH // 2, GRID_HEIGHT // 2)
        self.body = deque(
            [(center[0], center[1]), (center[0] - 1, center[1]), (center[0] - 2, center[1])]
        )
        self.direction = RIGHT
        self.pending_directions = deque(maxlen=2)
        self.grow_by = 0

    @property
    def head(self):
        return self.body[0]

    def queue_direction(self, direction):
        reference = self.pending_directions[-1] if self.pending_directions else self.direction
        if direction != reference and direction != OPPOSITE[reference]:
            self.pending_directions.append(direction)

    def next_head(self):
        if self.pending_directions:
            self.direction = self.pending_directions.popleft()
        return (self.head[0] + self.direction[0], self.head[1] + self.direction[1])

    def move_to(self, new_head):
        self.body.appendleft(new_head)
        if self.grow_by:
            self.grow_by -= 1
        else:
            self.body.pop()

    def hits_self(self, position, will_grow=False):
        body_to_check = self.body if will_grow else list(self.body)[:-1]
        return position in body_to_check


class Game:
    def __init__(self):
        self.snake = Snake()
        self.high_score = load_high_score()
        self.particles = []
        self.state = "ready"
        self.reset()

    def reset(self):
        self.snake.reset()
        self.score = 0
        self.foods_eaten = 0
        self.food = self.spawn_food()
        self.is_golden = False
        self.move_accumulator = 0.0
        self.particles.clear()

    @property
    def move_interval(self):
        # Starts forgiving and gradually tops out at roughly 16 cells per second.
        return max(0.062, 0.135 - min(self.foods_eaten, 25) * 0.0028)

    def spawn_food(self):
        occupied = set(self.snake.body)
        empty = [
            (x, y)
            for y in range(GRID_HEIGHT)
            for x in range(GRID_WIDTH)
            if (x, y) not in occupied
        ]
        return random.choice(empty) if empty else None

    def start(self):
        if self.state in {"ready", "paused"}:
            self.state = "running"
        elif self.state == "game_over":
            self.reset()
            self.state = "running"

    def toggle_pause(self):
        if self.state == "running":
            self.state = "paused"
        elif self.state == "paused":
            self.state = "running"

    def turn(self, direction):
        if self.state == "ready":
            self.state = "running"
        if self.state == "running":
            self.snake.queue_direction(direction)

    def update(self, dt):
        self.update_particles(dt)
        if self.state != "running":
            return

        self.move_accumulator += dt
        while self.move_accumulator >= self.move_interval and self.state == "running":
            self.move_accumulator -= self.move_interval
            self.step()

    def step(self):
        new_head = self.snake.next_head()
        eating = new_head == self.food
        outside = not (0 <= new_head[0] < GRID_WIDTH and 0 <= new_head[1] < GRID_HEIGHT)
        if outside or self.snake.hits_self(new_head, will_grow=eating):
            self.finish()
            return

        self.snake.move_to(new_head)
        if not eating:
            return

        points = 3 if self.is_golden else 1
        self.score += points
        self.foods_eaten += 1
        self.snake.grow_by += 1
        self.add_particles(new_head, GOLD if self.is_golden else APPLE)
        self.is_golden = self.foods_eaten % 5 == 0
        self.food = self.spawn_food()
        if self.food is None:
            self.finish()

    def finish(self):
        self.state = "game_over"
        if self.score > self.high_score:
            self.high_score = self.score
            save_high_score(self.high_score)

    def add_particles(self, cell, color):
        px = cell[0] * CELL_SIZE + CELL_SIZE / 2
        py = HUD_HEIGHT + cell[1] * CELL_SIZE + CELL_SIZE / 2
        for _ in range(12):
            angle = random.random() * math.tau
            speed = random.uniform(45, 105)
            self.particles.append(
                [px, py, math.cos(angle) * speed, math.sin(angle) * speed, 0.45, color]
            )

    def update_particles(self, dt):
        for particle in self.particles:
            particle[0] += particle[2] * dt
            particle[1] += particle[3] * dt
            particle[4] -= dt
        self.particles = [particle for particle in self.particles if particle[4] > 0]


def rounded_cell_rect(cell, inset=3):
    return pygame.Rect(
        cell[0] * CELL_SIZE + inset,
        HUD_HEIGHT + cell[1] * CELL_SIZE + inset,
        CELL_SIZE - inset * 2,
        CELL_SIZE - inset * 2,
    )


def draw_board(screen):
    pygame.draw.rect(screen, BOARD, (0, HUD_HEIGHT, BOARD_WIDTH, BOARD_HEIGHT))
    for x in range(0, BOARD_WIDTH + 1, CELL_SIZE):
        pygame.draw.line(screen, GRID, (x, HUD_HEIGHT), (x, SCREEN_HEIGHT))
    for y in range(HUD_HEIGHT, SCREEN_HEIGHT + 1, CELL_SIZE):
        pygame.draw.line(screen, GRID, (0, y), (BOARD_WIDTH, y))


def draw_food(screen, game, now):
    if game.food is None:
        return
    center = (
        game.food[0] * CELL_SIZE + CELL_SIZE // 2,
        HUD_HEIGHT + game.food[1] * CELL_SIZE + CELL_SIZE // 2,
    )
    color = GOLD if game.is_golden else APPLE
    pulse = 1.0 + math.sin(now * 5) * 0.08
    radius = int(9 * pulse)
    glow = pygame.Surface((CELL_SIZE * 2, CELL_SIZE * 2), pygame.SRCALPHA)
    pygame.draw.circle(glow, (*color, 35), (CELL_SIZE, CELL_SIZE), radius + 7)
    screen.blit(glow, (center[0] - CELL_SIZE, center[1] - CELL_SIZE))
    pygame.draw.circle(screen, color, center, radius)
    pygame.draw.ellipse(screen, (255, 255, 255), (center[0] - 4, center[1] - 5, 4, 3))
    pygame.draw.line(screen, GREEN, (center[0], center[1] - 8), (center[0] + 4, center[1] - 13), 3)


def draw_snake(screen, snake):
    for index, segment in reversed(list(enumerate(snake.body))):
        progress = index / max(1, len(snake.body) - 1)
        color = (
            int(GREEN[0] + (GREEN_DARK[0] - GREEN[0]) * progress),
            int(GREEN[1] + (GREEN_DARK[1] - GREEN[1]) * progress),
            int(GREEN[2] + (GREEN_DARK[2] - GREEN[2]) * progress),
        )
        pygame.draw.rect(screen, color, rounded_cell_rect(segment), border_radius=7)

    head = snake.head
    cx = head[0] * CELL_SIZE + CELL_SIZE // 2
    cy = HUD_HEIGHT + head[1] * CELL_SIZE + CELL_SIZE // 2
    dx, dy = snake.direction
    perpendicular = (-dy, dx)
    for side in (-1, 1):
        eye = (
            int(cx + dx * 6 + perpendicular[0] * side * 5),
            int(cy + dy * 6 + perpendicular[1] * side * 5),
        )
        pygame.draw.circle(screen, (242, 250, 246), eye, 3)
        pygame.draw.circle(screen, (18, 34, 27), eye, 1)


def draw_particles(screen, particles):
    for x, y, _, _, life, color in particles:
        radius = max(1, int(life * 9))
        pygame.draw.circle(screen, color, (int(x), int(y)), radius)


def draw_hud(screen, game, fonts):
    title_font, score_font, small_font = fonts
    screen.blit(title_font.render("SNAKE", True, TEXT), (22, 14))
    score = score_font.render(f"{game.score:02d}", True, TEXT)
    screen.blit(score, score.get_rect(center=(SCREEN_WIDTH // 2, 32)))
    screen.blit(small_font.render("SCORE", True, MUTED), (SCREEN_WIDTH // 2 - 26, 51))

    best = small_font.render(f"BEST  {game.high_score:02d}", True, MUTED)
    screen.blit(best, best.get_rect(right=SCREEN_WIDTH - 22, centery=30))
    speed_level = min(10, 1 + game.foods_eaten // 3)
    speed = small_font.render(f"SPEED  {speed_level}", True, MUTED)
    screen.blit(speed, speed.get_rect(right=SCREEN_WIDTH - 22, centery=53))


def draw_overlay(screen, game, fonts):
    if game.state == "running":
        return
    _, _, small_font = fonts
    overlay = pygame.Surface((SCREEN_WIDTH, BOARD_HEIGHT), pygame.SRCALPHA)
    overlay.fill((5, 8, 10, 176))
    screen.blit(overlay, (0, HUD_HEIGHT))

    heading_font = get_font(42, bold=True)
    if game.state == "ready":
        heading, subline = "准备好了吗？", "方向键 / WASD 开始"
    elif game.state == "paused":
        heading, subline = "已暂停", "按空格继续"
    else:
        heading, subline = "游戏结束", f"本局 {game.score} 分 · 按 R 再来一局"

    heading_surface = heading_font.render(heading, True, TEXT)
    subline_surface = small_font.render(subline, True, (190, 204, 210))
    center_y = HUD_HEIGHT + BOARD_HEIGHT // 2
    screen.blit(heading_surface, heading_surface.get_rect(center=(SCREEN_WIDTH // 2, center_y - 22)))
    screen.blit(subline_surface, subline_surface.get_rect(center=(SCREEN_WIDTH // 2, center_y + 34)))


def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("贪吃蛇")
    clock = pygame.time.Clock()
    fonts = (get_font(24, True), get_font(32, True), get_font(15, True))
    game = Game()

    key_directions = {
        pygame.K_UP: UP,
        pygame.K_w: UP,
        pygame.K_DOWN: DOWN,
        pygame.K_s: DOWN,
        pygame.K_LEFT: LEFT,
        pygame.K_a: LEFT,
        pygame.K_RIGHT: RIGHT,
        pygame.K_d: RIGHT,
    }

    running = True
    while running:
        dt = min(clock.tick(RENDER_FPS) / 1000.0, 0.1)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key in (pygame.K_SPACE, pygame.K_p):
                    game.start() if game.state in {"ready", "game_over"} else game.toggle_pause()
                elif event.key == pygame.K_r:
                    game.reset()
                    game.state = "running"
                elif event.key in key_directions:
                    game.turn(key_directions[event.key])

        game.update(dt)
        screen.fill(BACKGROUND)
        draw_board(screen)
        draw_food(screen, game, pygame.time.get_ticks() / 1000.0)
        draw_snake(screen, game.snake)
        draw_particles(screen, game.particles)
        draw_hud(screen, game, fonts)
        draw_overlay(screen, game, fonts)
        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
