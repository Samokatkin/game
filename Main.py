import pygame
from pygame import *
from pygame.sprite import Sprite, collide_rect
import pyganim
import os

mixer.pre_init()
mixer.init()
# Параметры персонажа
MOVE_SPEED = 5
JUMP_POWER = 8
GRAVITY = 0.4
BACKCOLOR = (30, 60, 130)
# Параметры для анимации
ANDELAY = 500
ANIMATION_STAY = ['data/player/player_stay1.png',
                  'data/player/player_stay2.png']
ANIMATION_RIGHT = ['data/player/player_right1.png',
                   'data/player/player_right2.png']
ANIMATION_LEFT = ['data/player/player_left1.png',
                  'data/player/player_left2.png']
ANIMATION_UPR = ['data/player/player_jumpr1.png',
                 'data/player/player_jumpr2.png']
ANIMATION_UPL = ['data/player/player_jumpl1.png',
                 'data/player/player_jumpl2.png']
SLIME = ['data/mobs/slime1.png',
         'data/mobs/slime2.png',
         'data/mobs/slime3.png']
WIDTH = 512
HEIGHT = 512
DISPLAY = (WIDTH, HEIGHT)


def load_image(name, colorkey=None): # Загрузка изображения
    fullname = os.path.join('data', name)
    image = pygame.image.load(fullname).convert()
    if colorkey is not None:
        if colorkey == -1:
            colorkey = image.get_at((0, 0))
        image.set_colorkey(colorkey)
    else:
        image = image.convert_alpha()
    return image


class Camera: # Камера
    def __init__(self, camera_func, width, height):
        self.camera_func = camera_func
        self.state = pygame.Rect(0, 0, width, height)

    def apply(self, target):
        return target.rect.move(self.state.topleft)

    def update(self, target):
        self.state = self.camera_func(self.state, target.rect)


def camera_func(camera, target_rect):
    l = -target_rect.x + DISPLAY[0] / 2
    t = -target_rect.y + DISPLAY[1] / 2
    w, h = camera.width, camera.height

    l = min(0, l)
    l = max(-(camera.width - DISPLAY[0]), l)
    t = max(-(camera.height - DISPLAY[1]), t)
    t = min(0, t)

    return pygame.Rect(l, t, w, h)


def load_level(filename):  # Загрузка уровня из текстового файла
    filename = "data/levels/" + filename
    with open(filename, 'r') as mapFile:
        level_map = [line.strip() for line in mapFile]
    max_width = max(map(len, level_map))
    return level_map


def sound_switch(sound, playing):
    if playing:
        sound.stop()
        playing = False
    else:
        sound.play(-1)
        playing = True
    return playing


# Список уровней
levels = {0: load_level('map.txt'), 1: load_level('map2.txt')}


class GameScene():  # Главный класс, тут будет игра
    def __init__(self, levelno, sound, sound_play):
        up = left = right = False
        self.entities = pygame.sprite.Group()
        self.enemies = pygame.sprite.Group()
        self.player = None
        self.platforms = []
        self.levelno = levelno
        level = levels[levelno]
        self.sound_play = sound_play
        self.sound = sound
        total_level_width = len(level[0]) * 32
        total_level_height = len(level) * 32
        if levelno == 0:
            self.bg = load_image('fon1.png')
        else:
            self.bg = load_image('fon2.png')
        x = 0
        y = 0
        for row in level:  # Генерация уровня
            for col in row:
                if col == "P":  # Игрок
                    self.player = Player(x, y)
                    self.entities.add(self.player)
                    self.player.scene = self
                if col == "G":  # Трава
                    p = Platform(x, y, 'platforms/grass.png')
                    self.platforms.append(p)
                    self.entities.add(p)
                if col == "D":  # Земля
                    p = Platform(x, y, 'platforms/dirt.png')
                    self.platforms.append(p)
                    self.entities.add(p)
                if col == "B":  # Кирпич
                    p = Platform(x, y, 'platforms/brick.png')
                    self.platforms.append(p)
                    self.entities.add(p)
                if col == "E":  # Переход на след. уровень
                    e = ExitBlock(x, y, 'platforms/exit.png')
                    self.platforms.append(e)
                    self.entities.add(e)
                if col == "*":  # Смертельный блок
                    p = DeathPlatform(x, y, 'platforms/deathblock.png')
                    self.platforms.append(p)
                    self.entities.add(p)
                if col == "M":  # Вправо-влево двигающаяся платформа
                    m = MovingPlatform(x, y, 1, 0, 1, 0, 'platforms/brick.png')
                    self.platforms.append(m)
                    self.enemies.add(m)
                if col == "m":  # Вверх-вниз двигающаяся платформа
                    m = MovingPlatform(x, y, 0, 2, 0, 4, 'platforms/brick.png')
                    self.platforms.append(m)
                    self.enemies.add(m)
                if col == "S":  # Моб, который двигается вправо влево
                    m = Mob(x, y, 1, 0, 1, 0, SLIME)
                    self.platforms.append(m)
                    self.enemies.add(m)
                if col == "s":  # Моб, который двигается вверх-вниз
                    m = Mob(x, y, 0, 4, 0, 3, SLIME)
                    self.platforms.append(m)
                    self.enemies.add(m)
                x += 32
            y += 32
            x = 0

        self.camera = Camera(camera_func, total_level_width, total_level_height)  # Включаем камеру
        for e in self.enemies:
            self.entities.add(e)

    def render(self, screen):
        screen.blit(self.bg, (0, 0))

        for e in self.entities:
            screen.blit(e.image, self.camera.apply(e))

    def update(self):
        pressed = pygame.key.get_pressed()
        up, left, right = [pressed[key] for key in (K_LEFT, K_RIGHT, K_UP)]

        self.player.update(up, left, right, self.platforms)

        for e in self.enemies:
            e.update(self.platforms)

        self.camera.update(self.player)

    def exit(self):  # Если дошли до конца уровня загружаем новый или говорим о нашей победе
        if self.levelno+1 in levels:
            self.manager.go_to(GameScene(self.levelno+1, self.sound, self.sound_play))
        else:
            self.manager.go_to(YouWin())

    def handle_events(self, events):
        for e in events:
            if e.type == KEYDOWN and e.key == K_ESCAPE:  # Если нажали esc, выходим в меню
                self.manager.go_to(Menu(self.levelno))
            if e.type == KEYDOWN and e.key == K_s:
                self.sound_play = sound_switch(self.sound, self.sound_play)


class YouWin():  # Выводим если прошли последний уровень
    def __init__(self):
        self.bg = load_image('youwin.png')

    def render(self, screen):
        screen.blit(self.bg, (0, 0))

    def update(self):
        pass

    def handle_events(self, events):
        for e in events:
            if e.type == KEYDOWN:
                self.manager.go_to(Menu())


class Menu():  # Главное меню
    def __init__(self, level=0):
        self.level = level
        self.sound_play = False
        self.bg = load_image('Menu.png')
        self.sound = pygame.mixer.Sound('data/sounds/Music by Stlasyx.ogg')
        self.sound_play = sound_switch(self.sound, self.sound_play)

    def render(self, screen):
        screen.blit(self.bg, (0, 0))

    def update(self):
        pass

    def handle_events(self, events):
        for e in events:
            if e.type == KEYDOWN and e.key == K_SPACE:
                self.manager.go_to(GameScene(self.level, self.sound, self.sound_play))
            if e.type == KEYDOWN and e.key == K_s:
                self.sound_play = sound_switch(self.sound, self.sound_play)


class Manager():  # Класс, который переключает сцены
    def __init__(self):
        self.go_to(Menu())

    def go_to(self, scene):
        self.scene = scene
        self.scene.manager = self


def makeanim(anim_list, delay):  # Функция, которая создает анимацию
    boltAnim = []
    for anim in anim_list:
        boltAnim.append((anim, delay))
    Anim = pyganim.PygAnimation(boltAnim)
    return Anim


class Mob(Sprite):  # Моб
    def __init__(self, x, y, left, up, maxlengthhor, maxlengthver, anim):
        Sprite.__init__(self)
        self.image = Surface((32, 32))
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.image.set_colorkey(BACKCOLOR)
        self.rect.x = x
        self.rect.y = y
        self.startX = x
        self.startY = y
        self.maxlengthhor = maxlengthhor
        self.maxlengthver = maxlengthver
        self.xvel = left
        self.yvel = up
        self.boltAnim = makeanim(anim, ANDELAY)
        self.boltAnim.play()

    def update(self, platforms):
        self.image.fill(BACKCOLOR)
        self.boltAnim.blit(self.image, (0, 0))
        self.rect.y += self.yvel
        self.rect.x += self.xvel

        self.collide(platforms)

        if self.startX - self.rect.x > self.maxlengthhor:
            self.xvel = -self.xvel
        if self.startY - self.rect.y > self.maxlengthver:
            self.yvel = -self.yvel

    def collide(self, platforms):
        for pl in platforms:
            if sprite.collide_rect(self, pl) and self != pl:
                self.xvel = - self.xvel
                self.yvel = - self.yvel


class Platform(Sprite):  # Платформа по которым перемещается персонаж
    def __init__(self, x, y, pic):
        Sprite.__init__(self)
        self.image = load_image(pic)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y


class ExitBlock(Platform):  # Блок который переводит на следующий уровень
    def __init__(self, x, y, pic):
        Platform.__init__(self, x, y, pic)
        self.image = load_image(pic, -1)
        self.image.convert()
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y


class MovingPlatform(Sprite):  # Двигающаяся платформа
    def __init__(self, x, y, left, up, max_length_hor, max_length_ver, pic):
        Sprite.__init__(self)
        self.image = load_image(pic)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.x = x
        self.y = y
        self.max_length_hor = max_length_hor
        self.max_length_ver = max_length_ver
        self.xvel = left
        self.yvel = up

    def update(self, platforms):

        self.rect.y += self.yvel
        self.rect.x += self.xvel

        self.collide(platforms)

        if self.x - self.rect.x > self.max_length_hor:
            self.xvel = -self.xvel
        if self.y - self.rect.y > self.max_length_ver:
            self.yvel = -self.yvel

    def collide(self, platforms):
        for pl in platforms:
            if sprite.collide_rect(self, pl) and self != pl:
                self.xvel = - self.xvel
                self.yvel = - self.yvel


class Player(Sprite):  # Игрок
    def __init__(self, x, y):
        Sprite.__init__(self)
        self.image = Surface((20, 32))
        self.startX = x
        self.startY = y
        self.xvel = 0
        self.yvel = 0
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.onGround = False
        self.image.set_colorkey(BACKCOLOR)

        self.boltAnimStay = makeanim(ANIMATION_STAY, ANDELAY)
        self.boltAnimStay.play()

        self.boltAnimRight = makeanim(ANIMATION_RIGHT, ANDELAY)
        self.boltAnimRight.play()

        self.boltAnimLeft = makeanim(ANIMATION_LEFT, ANDELAY)
        self.boltAnimLeft.play()

        self.boltAnimUpR = makeanim(ANIMATION_UPR, ANDELAY)
        self.boltAnimUpR.play()

        self.boltAnimUpL = makeanim(ANIMATION_UPL, ANDELAY)
        self.boltAnimUpL.play()

    def update(self, left, right, up, platforms):
        if self.rect.top > 1500 or self.rect.top < 0:
            self.die()
        if self.rect.left > 5000 or self.rect.right < 0:
            self.die()
        if left:
            self.xvel = -MOVE_SPEED
            self.image.fill(BACKCOLOR)
            self.boltAnimLeft.blit(self.image, (0.1, 0.1))
        if right:
            self.xvel = MOVE_SPEED
            self.image.fill(BACKCOLOR)
            self.boltAnimRight.blit(self.image, (0.1, 0.1))
        if not (left or right):
            self.xvel = 0
            if not up:
                self.image.fill(BACKCOLOR)
                self.boltAnimStay.blit(self.image, (0.1, 0.1))
        if up:
            if self.onGround:
                self.yvel = -JUMP_POWER
            if left:
                self.image.fill(BACKCOLOR)
                self.boltAnimUpL.blit(self.image, (0.1, 0.1))
            if right:
                self.image.fill(BACKCOLOR)
                self.boltAnimUpR.blit(self.image, (0.1, 0.1))
        if not self.onGround:
            self.yvel += GRAVITY
        self.onGround = False
        self.rect.x += self.xvel
        self.collide(self.xvel, 0, platforms)
        self.rect.y += self.yvel
        self.collide(0, self.yvel, platforms)

    def collide(self, xvel, yvel, platforms):
        for pl in platforms:
            if collide_rect(self, pl):
                if isinstance(pl, ExitBlock):
                    self.scene.exit()
                    return False
                if isinstance(pl, DeathPlatform) or isinstance(pl, Mob):
                    self.die()
                if xvel > 0:
                    self.rect.right = pl.rect.left
                if xvel < 0:
                    self.rect.left = pl.rect.right
                if yvel > 0:
                    self.rect.bottom = pl.rect.top
                    self.onGround = True
                    self.yvel = 0
                if yvel < 0:
                    self.rect.top = pl.rect.bottom
                    self.yvel = 0

    def teleport(self, goX, goY):
        self.rect.x = goX
        self.rect.y = goY

    def die(self):  # Если игрок умирает, ждем немного и спавним его снова
        time.wait(250)
        self.teleport(self.startX, self.startY)


class DeathPlatform(Sprite):  # Шипастая платформа
    def __init__(self, x, y, pic):
        Sprite.__init__(self)
        self.image = load_image(pic, -1)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y


def main():
    pygame.init()
    screen = pygame.display.set_mode(DISPLAY, 0, 0)
    pygame.display.set_caption("Bloxy adventure: Сделано для Яндекс Лицея")
    timer = pygame.time.Clock()
    running = True

    manager = Manager()

    while running:
        timer.tick(60)
        if pygame.event.get(QUIT):
            running = False
            return
        manager.scene.handle_events(pygame.event.get())
        manager.scene.update()
        manager.scene.render(screen)
        pygame.display.flip()


if __name__ == "__main__":  # Знаете, это был очень огромный опыт для меня.
    main()  # Спасибо что посмотрели мою программу! :)
