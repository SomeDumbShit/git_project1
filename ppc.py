import pygame
import sys
import random
import json
import os

SAVE_FILE = "progress.json"

def save_progress(level):
    progress = {"level": level}
    with open(SAVE_FILE, 'w') as f:
        json.dump(progress, f)

def load_progress():
    if os.path.exists(SAVE_FILE):
        with open(SAVE_FILE, 'r') as f:
            progress = json.load(f)
            return progress.get("level", 0)
    return 0

current_level = load_progress()
# --- Основные настройки ---
pygame.init()
WIDTH, HEIGHT = 1000, 500
FPS = 60
TITLE = "Эхо-рыцарь"
TILE_SIZE = 50

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (200, 50, 50)
BLUE = (50, 50, 200)
GRAY = (100, 100, 100)
YELLOW = (255, 255, 0)
GREEN = (50, 200, 50)
ORANGE = (255, 165, 0)  # Стены, усиливающие звук
PURPLE = (128, 0, 128)  # Стены, поглощающие звук

player_health = 100
player_score = 0
max_waves = 5  # Ограничение на количество звуковых волн
current_waves = 0

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption(TITLE)
clock = pygame.time.Clock()

# --- Классы ---

def load_animation_sprites(path, frame_count):
    frames = []
    for i in range(frame_count):
        frame = pygame.image.load(f"{path}{i}.png").convert_alpha()
        frames.append(frame)
    return frames


class Player(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.animations = {
            "walk_down": load_animation_sprites("sprites/walk_down_", 4),
            "walk_up": load_animation_sprites("sprites/walk_up_", 4),
            "walk_left": load_animation_sprites("sprites/walk_left_", 4),
            "walk_right": load_animation_sprites("sprites/walk_right_", 4),
        }
        self.current_animation = "walk_down"
        self.image = self.animations[self.current_animation][0]
        self.rect = self.image.get_rect()
        self.rect.topleft = (x, y)
        self.frame_index = 0
        self.animation_speed = 0.2
        self.velocity = 5

    def update(self):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]:
            self.rect.x -= self.velocity
            self.current_animation = "walk_left"
        elif keys[pygame.K_RIGHT]:
            self.rect.x += self.velocity
            self.current_animation = "walk_right"
        elif keys[pygame.K_UP]:
            self.rect.y -= self.velocity
            self.current_animation = "walk_up"
        elif keys[pygame.K_DOWN]:
            self.rect.y += self.velocity
            self.current_animation = "walk_down"
        else:
            self.frame_index = 0

        self.frame_index += self.animation_speed
        if self.frame_index >= len(self.animations[self.current_animation]):
            self.frame_index = 0

        self.image = self.animations[self.current_animation][int(self.frame_index)]


class Wave(pygame.sprite.Sprite):
    def __init__(self, x, y, dx, dy):
        super().__init__()
        self.image = pygame.Surface((TILE_SIZE // 2, TILE_SIZE // 2), pygame.SRCALPHA)
        pygame.draw.circle(self.image, YELLOW, (TILE_SIZE // 4, TILE_SIZE // 4), TILE_SIZE // 4)
        self.rect = self.image.get_rect(center=(x, y))
        self.dx = dx
        self.dy = dy
        self.spawn_time = pygame.time.get_ticks()

    def update(self, walls, enemies):
        self.rect.x += self.dx
        self.rect.y += self.dy

        # Анимация волны
        current_time = pygame.time.get_ticks()
        if current_time - self.spawn_time < 1000:  # 1 секунда
            scale = 1 + (current_time - self.spawn_time) / 1000
            self.image = pygame.transform.scale(self.image, (int(TILE_SIZE // 2 * scale), int(TILE_SIZE // 2 * scale)))
            self.rect = self.image.get_rect(center=self.rect.center)

        # Отскок от стен
        for wall in walls:
            if self.rect.colliderect(wall.rect):
                if wall.absorption:
                    self.kill()
                else:
                    if abs(self.rect.right - wall.rect.left) < 10 or abs(self.rect.left - wall.rect.right) < 10:
                        self.dx = -self.dx
                    if abs(self.rect.bottom - wall.rect.top) < 10 or abs(self.rect.top - wall.rect.bottom) < 10:
                        self.dy = -self.dy
                    if wall.amplification:
                        self.dx *= 1.5
                        self.dy *= 1.5

        for enemy in enemies:
            if self.rect.colliderect(enemy.rect):
                player.score += 10  # Добавление очков за убийство врага
                enemy.take_damage()
                self.kill()


class Enemy(pygame.sprite.Sprite):
    def __init__(self, x, y, health):
        super().__init__()
        self.image = pygame.Surface((TILE_SIZE, TILE_SIZE))
        self.image.fill(RED)
        self.rect = self.image.get_rect(topleft=(x, y))
        self.speed = random.choice([-1, 1]) * random.randint(1, 3)
        self.shoot_timer = 0
        self.health = health

    def update(self, walls):
        self.rect.x += self.speed
        if self.rect.left <= 0 or self.rect.right >= WIDTH or pygame.sprite.spritecollideany(self, walls):
            self.speed = -self.speed

        if pygame.time.get_ticks() - self.shoot_timer > 1000:
            bullet = Bullet(self.rect.centerx, self.rect.centery, random.choice([-5, 5]), random.choice([-5, 5]))
            all_sprites.add(bullet)
            bullets.add(bullet)
            self.shoot_timer = pygame.time.get_ticks()

    def take_damage(self):
        self.health -= 1
        if self.health <= 0:
            player.score += 10  # Добавление очков за убийство врага
            self.kill()


class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y, dx, dy):
        super().__init__()
        self.image = pygame.Surface((TILE_SIZE // 4, TILE_SIZE // 4))
        self.image.fill(WHITE)
        self.rect = self.image.get_rect(center=(x, y))
        self.dx = dx
        self.dy = dy
        self.spawn_time = pygame.time.get_ticks()

    def update(self, walls):
        self.rect.x += self.dx
        self.rect.y += self.dy

        # Удаление пули спустя время
        if pygame.time.get_ticks() - self.spawn_time > 3000:  # 3 секунды
            self.kill()

        for wall in walls:
            if self.rect.colliderect(wall.rect):
                if abs(self.rect.right - wall.rect.left) < 10 or abs(self.rect.left - wall.rect.right) < 10:
                    self.dx = -self.dx
                if abs(self.rect.bottom - wall.rect.top) < 10 or abs(self.rect.top - wall.rect.bottom) < 10:
                    self.dy = -self.dy

        if self.rect.left > WIDTH or self.rect.right < 0 or self.rect.top > HEIGHT or self.rect.bottom < 0:
            self.kill()


class Wall(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height, absorption=False, amplification=False):
        super().__init__()
        self.image = pygame.Surface((width, height))
        if absorption:
            self.image.fill(PURPLE)
        elif amplification:
            self.image.fill(ORANGE)
        else:
            self.image.fill(GRAY)
        self.rect = self.image.get_rect(topleft=(x, y))
        self.absorption = absorption
        self.amplification = amplification


class Key(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((TILE_SIZE, TILE_SIZE))
        self.image.fill(YELLOW)
        self.rect = self.image.get_rect(topleft=(x, y))


class Door(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((TILE_SIZE, TILE_SIZE))
        self.image.fill(GREEN)
        self.rect = self.image.get_rect(topleft=(x, y))


class HealthPack(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((TILE_SIZE, TILE_SIZE))
        self.image.fill(GREEN)
        self.rect = self.image.get_rect(topleft=(x, y))


class Bonus(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((TILE_SIZE, TILE_SIZE))
        self.image.fill(BLUE)
        self.rect = self.image.get_rect(topleft=(x, y))


# --- Функции ---
def load_level(level_map):
    walls = pygame.sprite.Group()
    enemies = pygame.sprite.Group()
    health_packs = pygame.sprite.Group()
    bonus = pygame.sprite.Group()
    key = None
    door = None

    for row_idx, row in enumerate(level_map):
        for col_idx, tile in enumerate(row):
            x, y = col_idx * TILE_SIZE, row_idx * TILE_SIZE
            if tile == "W":
                walls.add(Wall(x, y, TILE_SIZE, TILE_SIZE))
            elif tile == "A":  # Стена, усиливающая звук
                walls.add(Wall(x, y, TILE_SIZE, TILE_SIZE, amplification=True))
            elif tile == "P":  # Стена, поглощающая звук
                walls.add(Wall(x, y, TILE_SIZE, TILE_SIZE, absorption=True))
            elif tile == "E":
                enemies.add(Enemy(x, y, health=1))
            elif tile == "B":
                enemies.add(Enemy(x, y, health=3))
            elif tile == "K":
                key = Key(x, y)
            elif tile == "D":
                door = Door(x, y)
            elif tile == "H":
                health_packs.add(HealthPack(x, y))
            elif tile == "X":
                bonus.add(Bonus(x, y))

    return walls, enemies, health_packs, key, door, bonus


def draw_ui(player):
    font = pygame.font.Font(None, 36)
    health_text = font.render(f"Здоровье: {player.health}", True, WHITE)
    score_text = font.render(f"Очки: {player.score}", True, WHITE)
    waves_text = font.render(f"Волны: {max_waves - current_waves}/{max_waves}", True, WHITE)
    screen.blit(health_text, (10, 10))
    screen.blit(score_text, (10, 50))
    screen.blit(waves_text, (10, 90))


def level_select_menu():
    max_level = load_progress()
    while True:
        screen.fill(BLACK)
        font = pygame.font.Font(None, 74)
        text = font.render("Выбор уровня", True, WHITE)
        screen.blit(text, (WIDTH // 2 - text.get_width() // 2, HEIGHT // 4))

        font = pygame.font.Font(None, 36)
        level_texts = []
        for i in range(len(levels)):
            if i <= max_level:
                level_text = font.render(f"Уровень {i + 1}", True, WHITE)
            else:
                level_text = font.render(f"Уровень {i + 1} (Заблокировано)", True, GRAY)
            screen.blit(level_text, (WIDTH // 2 - level_text.get_width() // 2, HEIGHT // 2 + i * 40))
            level_texts.append(level_text)

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                for i in range(len(level_texts)):
                    level_text_rect = level_texts[i].get_rect(topleft=(WIDTH // 2 - level_texts[i].get_width() // 2, HEIGHT // 2 + i * 40))
                    if level_text_rect.collidepoint(event.pos) and i <= max_level:
                        return i

def main_menu():
    while True:
        screen.fill(BLACK)
        font = pygame.font.Font(None, 74)
        text = font.render("Эхо-рыцарь", True, WHITE)
        screen.blit(text, (WIDTH // 2 - text.get_width() // 2, HEIGHT // 4))

        font = pygame.font.Font(None, 36)
        play_text = font.render("Играть", True, WHITE)
        screen.blit(play_text, (WIDTH // 2 - play_text.get_width() // 2, HEIGHT // 2))
        level_select_text = font.render("Выбор уровня", True, WHITE)
        screen.blit(level_select_text, (WIDTH // 2 - level_select_text.get_width() // 2, HEIGHT // 2 + 50))
        quit_text = font.render("Выход", True, WHITE)
        screen.blit(quit_text, (WIDTH // 2 - quit_text.get_width() // 2, HEIGHT // 2 + 100))

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if play_text.get_rect(topleft=(WIDTH // 2 - play_text.get_width() // 2, HEIGHT // 2)).collidepoint(event.pos):
                    return
                if level_select_text.get_rect(topleft=(WIDTH // 2 - level_select_text.get_width() // 2, HEIGHT // 2 + 50)).collidepoint(event.pos):
                    selected_level = level_select_menu()
                    if selected_level is not None:
                        global current_level
                        current_level = selected_level
                        restart_level()
                        return
                if quit_text.get_rect(topleft=(WIDTH // 2 - quit_text.get_width() // 2, HEIGHT // 2 + 100)).collidepoint(event.pos):
                    pygame.quit()
                    sys.exit()

def pause_menu():
    paused = True
    while paused:
        screen.fill(BLACK)
        font = pygame.font.Font(None, 74)
        text = font.render("Пауза", True, WHITE)
        screen.blit(text, (WIDTH // 2 - text.get_width() // 2, HEIGHT // 4))

        font = pygame.font.Font(None, 36)
        resume_text = font.render("Продолжить", True, WHITE)
        screen.blit(resume_text, (WIDTH // 2 - resume_text.get_width() // 2, HEIGHT // 2))
        quit_text = font.render("Выход", True, WHITE)
        screen.blit(quit_text, (WIDTH // 2 - quit_text.get_width() // 2, HEIGHT // 2 + 50))

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if resume_text.get_rect(topleft=(WIDTH // 2 - resume_text.get_width() // 2, HEIGHT // 2)).collidepoint(
                        event.pos):
                    paused = False
                if quit_text.get_rect(topleft=(WIDTH // 2 - quit_text.get_width() // 2, HEIGHT // 2 + 50)).collidepoint(
                        event.pos):
                    pygame.quit()
                    sys.exit()


def restart_level():
    global walls, enemies, health_packs, key, door, bonus, all_sprites, waves, bullets, current_waves
    player.rect.topleft = (100, 100)
    player.health = 100
    current_waves = 0
    walls, enemies, health_packs, key, door, bonus = load_level(levels[current_level])
    all_sprites = pygame.sprite.Group(player, *walls, *enemies)
    if key is not None:
        all_sprites.add(key)
    if door is not None:
        all_sprites.add(door)
    all_sprites.add(*health_packs, *bonus)
    waves = pygame.sprite.Group()
    bullets = pygame.sprite.Group()


# --- Уровни ---
levels = [
    [
        "WWWWWWWWWWWWWWWWWWWW",
        "W   H          K   W",
        "W   W  W   W       W",
        "W   W      W  W    W",
        "W   W              W",
        "W   W  E   W       W",
        "W   W      W  W    W",
        "W   W  W       D   W",
        "W   W  W   E       W",
        "WWWWWWWWWWWWWWWWWWWW",
    ],
    [
        "WWWWWWWWWWWWWWWWWWWW",
        "W   H    E     K   W",
        "W   W  W   W       W",
        "W   W      W  W    W",
        "W   W              W",
        "W   W  E   W       W",
        "W   W      W  W    W",
        "W   W  W       D   W",
        "W   W  W   E       W",
        "WWWWWWWWWWWWWWWWWWWW",
    ],
    [
        "WWWWWWWWWWWWWWWWWWWW",
        "W   H          K   W",
        "W   W  W   W       W",
        "W   W      W  W    W",
        "W   W              W",
        "W   W  B   W       W",
        "W   W      W  W    W",
        "W   W  W       D   W",
        "W   W  W   E       W",
        "WWWWWWWWWWWWWWWWWWWW",
    ],
    [
        "WWWWWWWWWWWWWWWWWWWW",
        "W   H        A  K  W",
        "W   W  W   W       W",
        "W   W      W  W    W",
        "W   W              W",
        "W   W  P   W       W",
        "W   W      W  W    W",
        "W   W  W       D   W",
        "W   W  W   E       W",
        "WWWWWWWWWWWWWWWWWWWW",
    ],
    [
        "WWWWWWWWWWWWWWWWWWWW",
        "W   H    E     K   W",
        "W   W  W   W       W",
        "W   W      W  W    W",
        "W   W              W",
        "W   W  E   W       W",
        "W   W      W  W    W",
        "W   W  W       D   W",
        "W   W  W   E       W",
        "WWWWWWWWWWWWWWWWWWWW",
    ],
    [
        "WWWWWWWWWWWWWWWWWWWW",
        "W   H          K   W",
        "W   W  W   W       W",
        "W   W      W  W    W",
        "W   W              W",
        "W   W  B   W       W",
        "W   W      W  W    W",
        "W   W  W       D   W",
        "W   W  W   E       W",
        "WWWWWWWWWWWWWWWWWWWW",
    ],
    [
        "WWWWWWWWWWWWWWWWWWWW",
        "W   H        A  K  W",
        "W   W  W   W       W",
        "W   W      W  W    W",
        "W   W              W",
        "W   W  P   W       W",
        "W   W      W  W    W",
        "W   W  W       D   W",
        "W   W  W   E       W",
        "WWWWWWWWWWWWWWWWWWWW",
    ],
    [
        "WWWWWWWWWWWWWWWWWWWW",
        "W   H    E     K   W",
        "W   W  W   W       W",
        "W   W      W  W    W",
        "W   W              W",
        "W   W  E   W       W",
        "W   W      W  W    W",
        "W   W  W       D   W",
        "W   W  W   E       W",
        "WWWWWWWWWWWWWWWWWWWW",
    ],
    [
        "WWWWWWWWWWWWWWWWWWWW",
        "W   H          K   W",
        "W   W  W   W       W",
        "W   W      W  W    W",
        "W   W              W",
        "W   W  B   W       W",
        "W   W      W  W    W",
        "W   W  W       D   W",
        "W   W  W   E       W",
        "WWWWWWWWWWWWWWWWWWWW",
    ],
    [
        "WWWWWWWWWWWWWWWWWWWW",
        "W   H        A  K  W",
        "W   W  W   W       W",
        "W   W      W  W    W",
        "W   W              W",
        "W   W  P   W       W",
        "W   W      W  W    W",
        "W   W  W       D   W",
        "W   W  W   E       W",
        "WWWWWWWWWWWWWWWWWWWW",
    ],
    [
        "WWWWWWWWWWWWWWWWWWWW",
        "W   H    E     K   W",
        "W   W  W   W       W",
        "W   W      W  W    W",
        "W   W              W",
        "W   W  E   W       W",
        "W   W      W  W    W",
        "W   W  W       D   W",
        "W   W  W   E       W",
        "WWWWWWWWWWWWWWWWWWWW",
    ],
    [
        "WWWWWWWWWWWWWWWWWWWW",
        "W   H          K   W",
        "W   W  W   W       W",
        "W   W      W  W    W",
        "W   W              W",
        "W   W  B   W       W",
        "W   W      W  W    W",
        "W   W  W       D   W",
        "W   W  W   E       W",
        "WWWWWWWWWWWWWWWWWWWW",
    ],
    [
        "WWWWWWWWWWWWWWWWWWWW",
        "W   H        A  K  W",
        "W   W  W   W       W",
        "W   W      W  W    W",
        "W   W              W",
        "W   W  P   W       W",
        "W   W      W  W    W",
        "W   W  W       D   W",
        "W   W  W   E       W",
        "WWWWWWWWWWWWWWWWWWWW",
    ],
    [
        "WWWWWWWWWWWWWWWWWWWW",
        "W   H    E     K   W",
        "W   W  W   W       W",
        "W   W      W  W    W",
        "W   W              W",
        "W   W  E   W       W",
        "W   W      W  W    W",
        "W   W  W       D   W",
        "W   W  W   E       W",
        "WWWWWWWWWWWWWWWWWWWW",
    ],
    [
        "WWWWWWWWWWWWWWWWWWWW",
        "W   H          K   W",
        "W   W  W   W       W",
        "W   W      W  W    W",
        "W   W              W",
        "W   W  B   W       W",
        "W   W      W  W    W",
        "W   W  W       D   W",
        "W   W  W   E       W",
        "WWWWWWWWWWWWWWWWWWWW",
    ],
    [
        "WWWWWWWWWWWWWWWWWWWW",
        "W   H        A  K  W",
        "W   W  W   W       W",
        "W   W      W  W    W",
        "W   W              W",
        "W   W  P   W       W",
        "W   W      W  W    W",
        "W   W  W       D   W",
        "W   W  W   E       W",
        "WWWWWWWWWWWWWWWWWWWW",
    ],
    [
        "WWWWWWWWWWWWWWWWWWWW",
        "W   H    E     K   W",
        "W   W  W   W       W",
        "W   W      W  W    W",
        "W   W              W",
        "W   W  E   W       W",
        "W   W      W  W    W",
        "W   W  W       D   W",
        "W   W  W   E       W",
        "WWWWWWWWWWWWWWWWWWWW",
    ],
    [
        "WWWWWWWWWWWWWWWWWWWW",
        "W   H          K   W",
        "W   W  W   W       W",
        "W   W      W  W    W",
        "W   W              W",
        "W   W  B   W       W",
        "W   W      W  W    W",
        "W   W  W       D   W",
        "W   W  W   E       W",
        "WWWWWWWWWWWWWWWWWWWW",
    ],
    [
        "WWWWWWWWWWWWWWWWWWWW",
        "W   H        A  K  W",
        "W   W  W   W       W",
        "W   W      W  W    W",
        "W   W              W",
        "W   W  P   W       W",
        "W   W      W  W    W",
        "W   W  W       D   W",
        "W   W  W   E       W",
        "WWWWWWWWWWWWWWWWWWWW",
    ],
]

current_level = 0


# --- Инициализация ---
player = Player(100, 100)
walls, enemies, health_packs, key, door, bonus = load_level(levels[current_level])

all_sprites = pygame.sprite.Group(player, *walls, *enemies)
if key is not None:
    all_sprites.add(key)
if door is not None:
    all_sprites.add(door)
all_sprites.add(*health_packs, *bonus)
waves = pygame.sprite.Group()
bullets = pygame.sprite.Group()

# --- Вход в главное меню ---
main_menu()

# --- Игровой цикл ---
running = True
has_key = False
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE and current_waves < max_waves:
                mouse_x, mouse_y = pygame.mouse.get_pos()
                dx = mouse_x - player.rect.centerx
                dy = mouse_y - player.rect.centery
                magnitude = (dx ** 2 + dy ** 2) ** 0.5
                wave = Wave(player.rect.centerx, player.rect.centery, dx / magnitude * 10, dy / magnitude * 10)
                waves.add(wave)
                all_sprites.add(wave)
                current_waves += 1
            if event.key == pygame.K_p:
                pause_menu()

    keys = pygame.key.get_pressed()
    player.update(keys, walls)
    waves.update(walls, enemies)
    bullets.update(walls)
    enemies.update(walls)

    # Проверка столкновений
    for health_pack in health_packs:
        if player.rect.colliderect(health_pack.rect):
            player.health = min(player.health + 20, 100)
            health_pack.kill()

    for bullet in bullets:
        if bullet.rect.colliderect(player.rect):
            player.health -= 10
            bullet.kill()
            if player.health <= 0:
                restart_level()

    if pygame.sprite.spritecollideany(player, enemies):
        player.health -= 1
        if player.health <= 0:
            restart_level()

    # Проверка столкновений
    if key is not None and player.rect.colliderect(key.rect):
        has_key = True
        key.kill()

    if has_key and door is not None and player.rect.colliderect(door.rect):
        current_level += 1
        if current_level < len(levels):
            player.rect.topleft = (100, 100)  # Сброс позиции игрока
            current_waves = 0  # Сброс количества волн
            walls, enemies, health_packs, key, door, bonus = load_level(levels[current_level])
            all_sprites = pygame.sprite.Group(player, *walls, *enemies)
            if key is not None:
                all_sprites.add(key)
            if door is not None:
                all_sprites.add(door)
            all_sprites.add(*health_packs, *bonus)
            waves = pygame.sprite.Group()
            bullets = pygame.sprite.Group()
            has_key = False
            save_progress(current_level)
        else:
            print("Вы победили!")
            running = False

    # Проверка столкновений с бонусами
    for bonus_item in bonus:
        if player.rect.colliderect(bonus_item.rect):
            player.score += 50
            bonus_item.kill()

    screen.fill(BLACK)
    all_sprites.draw(screen)
    draw_ui(player)
    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()