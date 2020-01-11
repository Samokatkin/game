import pygame
from pygame import *
from pygame.sprite import Sprite, collide_rect
import pyganim
import os

mixer.pre_init(44100, -16, 1, 512)
mixer.init()
# Параметры персонажа
MOVE_SPEED = 7
JUMP_POWER = 10
GRAVITY = 0.4
BACKCOLOR = (30, 70, 130) #Задний фон
# анимации персонажа
ANDELAY = 0.1
ANIMATION_STAY = [('data/player/player.png', ANDELAY)]
ANIMATION_RIGHT = ['data/player/player_right1.png',
                   'data/player/player_right2.png',
                   'data/player/player_right3.png']
ANIMATION_LEFT = ['data/player/player_left1.png',
                  'data/player/player_left2.png',
                  'data/player/player_left3.png']
ANIMATION_UP = ['data/player/player_up1.png',
                'data/player/player_up2.png',
                'data/player/player_up3.png',
                'data/player/player_up4.png']
WIDTH = 1120 - 320
HEIGHT = 960 - 320

DISPLAY = (WIDTH, HEIGHT)
DEPTH = 0
FLAGS = 0
CAMERA_SLACK = 30

def load_image(name, colorkey=None):
    fullname = os.path.join('data', name)
    image = pygame.image.load(fullname).convert()
    if colorkey is not None:
        if colorkey == -1:
            colorkey = image.get_at((0, 0))
        image.set_colorkey(colorkey)
    else:
        image = image.convert_alpha()
    return image
# Камера
class Camera:
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


def load_level(filename):
    filename = "data/levels/" + filename
    # читаем уровень, убирая символы перевода строки
    with open(filename, 'r') as mapFile:
        level_map = [line.strip() for line in mapFile]
    # и подсчитываем максимальную длину
    max_width = max(map(len, level_map))
    return level_map


levels = {0: load_level('map.txt'), 1: load_level('map2.txt')}



class GameScene():
    def __init__(self, levelno):
        super(GameScene, self).__init__()
        self.bg = Surface((32,32))
        self.bg.convert()
        self.bg.fill(BACKCOLOR)
        up = left = right = False
        self.entities = pygame.sprite.Group()
        self.enemies = pygame.sprite.Group()
        self.player = None
        self.platforms = []

        self.levelno = levelno

        level = levels[levelno]
        total_level_width = len(level[0]) * 32
        total_level_height = len(level) * 32

        # build the level
        x = 0
        y = 0
        for row in level:
            for col in row:
                if col == "G":
                    p = Platform(x, y, 'platforms/grass.png')
                    self.platforms.append(p)
                    self.entities.add(p)
                if col == "D":
                    p = Platform(x, y, 'platforms/dirt.png')
                    self.platforms.append(p)
                    self.entities.add(p)
                if col == "B":
                    p = Platform(x, y, 'platforms/brick.png')
                    self.platforms.append(p)
                    self.entities.add(p)
                if col == "E":
                    e = ExitBlock(x, y, 'platforms/brick.png')
                    self.platforms.append(e)
                    self.entities.add(e)
                if col == "P":
                    self.player = Player(x, y, self.levelno)
                    self.entities.add(self.player)
                    self.player.scene = self
                x += 32
            y += 32
            x = 0

        self.camera = Camera(camera_func, total_level_width, total_level_height)
        for e in self.enemies:
            self.entities.add(e)

    def render(self, screen):
        for y in range(20):
            for x in range(25):
                screen.blit(self.bg, (x * 32, y * 32))

        for e in self.entities:
            screen.blit(e.image, self.camera.apply(e))

    def update(self):
        pressed = pygame.key.get_pressed()
        up, left, right = [pressed[key] for key in (K_LEFT, K_RIGHT, K_UP)]
        self.player.update(up, left, right, self.platforms)

        for e in self.enemies:
            e.update(self.platforms)

        self.camera.update(self.player)

    def exit(self):
        if self.levelno+1 in levels:
            self.manager.go_to(GameScene(self.levelno+1))
        else:
            self.manager.go_to(YouWin())

    def die(self):
        self.manager.go_to(GameOver(self.levelno))

    def handle_events(self, events):
        for e in events:
            if e.type == KEYDOWN and e.key == K_ESCAPE:
                self.manager.go_to(TitleScene(self.levelno))


class YouWin():
    def __init__(self):
        super(YouWin, self).__init__()
        self.sfont = pygame.font.SysFont('Arial', 32)

    def render(self, screen):
        # ugly!
        screen.fill((0, 200, 0))
        text1 = self.sfont.render('>>Press any button to restart game<<', True, (255, 255, 255))
        screen.blit(text1, (200, 50))

    def update(self):
        pass

    def handle_events(self, events):
        for e in events:
            if e.type == KEYDOWN:
                self.manager.go_to(TitleScene())


class GameOver():
    def __init__(self, level):
        self.level = level
        super(GameOver, self).__init__()
        self.sfont = pygame.font.SysFont('Arial', 32)

    def render(self, screen):
        # ugly!
        screen.fill((0, 200, 0))
        text1 = self.sfont.render('>>Press any button to try again<<', True, (255, 255, 255))
        screen.blit(text1, (200, 50))

    def update(self):
        pass

    def handle_events(self, events):
        for e in events:
            if e.type == KEYDOWN:
                self.manager.go_to(GameScene(self.level))


class TitleScene():
    def __init__(self, level=0):
        super(TitleScene, self).__init__()
        self.font = pygame.font.SysFont('Arial', 56)
        self.sfont = pygame.font.SysFont('Arial', 32)
        self.level = level

    def render(self, screen):
        # ugly!
        screen.fill((0, 200, 0))
        text1 = self.font.render('Это игра', True, (255, 255, 255))
        text2 = self.sfont.render('>> press space to start/continue <<', True, (255, 255, 255))
        screen.blit(text1, (200, 50))
        screen.blit(text2, (200, 350))

    def update(self):
        pass

    def handle_events(self, events):
        for e in events:
            if e.type == KEYDOWN and e.key == K_SPACE:
                self.manager.go_to(GameScene(self.level))


class SceneMananger():
    def __init__(self):
        self.go_to(TitleScene())

    def go_to(self, scene):
        self.scene = scene
        self.scene.manager = self


class Platform(Sprite):  # платформа
    def __init__(self, x, y, pic):
        Sprite.__init__(self)
        self.image = load_image(pic)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y


class ExitBlock(Platform):
    def __init__(self, x, y, pic):
        Platform.__init__(self, x, y, pic)
        self.image = load_image(pic)
        self.image.convert()
        self.rect = Rect(x, y, 32, 32)


class Player(Sprite):  # Персонаж
    def __init__(self, x, y, level):
        Sprite.__init__(self)
        self.image = Surface((20, 20))
        self.level = level
        self.xvel = 0
        self.yvel = 0
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.onGround = False
        self.image.set_colorkey(0, 0)

        def makeanim(anim_list, delay):
            boltAnim = []
            for anim in anim_list:
                boltAnim.append((anim, delay))
            Anim = pyganim.PygAnimation(boltAnim)
            return Anim

        self.boltAnimStay = pyganim.PygAnimation(ANIMATION_STAY)
        self.boltAnimStay.play()

        self.boltAnimRight = makeanim(ANIMATION_RIGHT, ANDELAY)
        self.boltAnimRight.play()

        self.boltAnimLeft = makeanim(ANIMATION_LEFT, ANDELAY)
        self.boltAnimLeft.play()

        self.boltAnimUp = makeanim(ANIMATION_UP, ANDELAY)
        self.boltAnimUp.play()
        self.jump_sound = mixer.Sound('data/sounds/jump.ogg')

    def update(self, left, right, up, platforms):
        if self.rect.top > 1440 or self.rect.top < 0:
            GameOver(self.level)
        if self.rect.left > 1408 or self.rect.right < 0:
            GameOver(self.level)
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
                self.jump_sound.play()
            self.image.fill(BACKCOLOR)
            self.boltAnimUp.blit(self.image, (0.1, 0.1))
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


def main():
    pygame.init()
    screen = pygame.display.set_mode(DISPLAY, FLAGS, DEPTH)
    pygame.display.set_caption("Wow Look! Nothing!")
    timer = pygame.time.Clock()
    running = True

    manager = SceneMananger()

    while running:
        timer.tick(60)

        if pygame.event.get(QUIT):
            running = False
            return
        manager.scene.handle_events(pygame.event.get())
        manager.scene.update()
        manager.scene.render(screen)
        pygame.display.flip()


if __name__ == "__main__":
    main()