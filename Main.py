import pygame
from pygame import *
from pygame.sprite import Sprite, collide_rect
import pyganim
import os

mixer.pre_init(44100, -16, 1, 512)
mixer.init()
MOVE_SPEED = 7
LIVES = 3
JUMP_POWER = 10
GRAVITY = 0.4
BACKCOLOR = (30, 70, 130)
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
WIDTH = 600
HEIGHT = 600

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
    with open(filename, 'r') as mapFile:
        level_map = [line.strip() for line in mapFile]
    max_width = max(map(len, level_map))
    return level_map


levels = {0: load_level('map.txt'), 1: load_level('map2.txt')}


class GameScene():
    def __init__(self, levelno):
        super(GameScene, self).__init__()
        self.bg = Surface((32, 32))
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
                if col == "M":
                    m = MovingPlatform(x, y, 10, 1, 10, 1, 'platforms/longbrick.png')
                    self.platforms.append(m)
                    self.entities.add(m)
                if col == "*":
                    m = DeathPlatform(x, y, 1, 6, 20 , 4)
                    self.platforms.append(m)
                    self.entities.add(m)
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

    def handle_events(self, events):
        for e in events:
            if e.type == KEYDOWN and e.key == K_ESCAPE:
                self.manager.go_to(TitleScene(self.levelno))


class YouWin():
    def __init__(self):
        super(YouWin, self).__init__()
        self.sfont = pygame.font.SysFont('Arial', 32)

    def render(self, screen):
        screen.fill((0, 200, 0))
        text1 = self.sfont.render('>>Press any button to restart game<<', True, (255, 255, 255))
        screen.blit(text1, (200, 50))

    def update(self):
        pass

    def handle_events(self, events):
        for e in events:
            if e.type == KEYDOWN:
                self.manager.go_to(TitleScene())


class TitleScene():
    def __init__(self, level=0):
        super(TitleScene, self).__init__()
        self.font = pygame.font.SysFont('Arial', 56)
        self.sfont = pygame.font.SysFont('Arial', 32)
        self.level = level

    def render(self, screen):
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


class Manager():
    def __init__(self):
        self.go_to(TitleScene())

    def go_to(self, scene):
        self.scene = scene
        self.scene.manager = self


def makeanim(anim_list, delay):
    boltAnim = []
    for anim in anim_list:
        boltAnim.append((anim, delay))
    Anim = pyganim.PygAnimation(boltAnim)
    return Anim


class Platform(Sprite):
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


class MovingPlatform(Sprite):
    def __init__(self, x, y, left, up, max_length_hor, max_length_ver, pic):
        Sprite.__init__(self)
        self.image = load_image(pic)
        self.rect = Rect(x, y, 32, 32)
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


class Player(Sprite):
    def __init__(self, x, y, level):
        Sprite.__init__(self)
        self.image = Surface((20, 32))
        self.level = level
        self.startX = x
        self.startY = y
        self.xvel = 0
        self.yvel = 0
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.onGround = False
        self.image.set_colorkey(0, 0)

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
        if self.rect.top > 1440 or self.rect.top < 0:
            self.die()
        if self.rect.left > 1408 or self.rect.right < 0:
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
                if isinstance(pl, DeathPlatform):
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

    def teleporting(self, goX, goY):
        self.rect.x = goX
        self.rect.y = goY

    def die(self):
        time.wait(50)
        self.teleporting(self.startX, self.startY)


class DeathPlatform(Sprite):
    def __init__(self, x, y, left, up, max_length_hor, max_length_ver):
        Sprite.__init__(self)
        self.image = Surface((32, 32))
        self.rect = Rect(x, y, 32, 32)
        self.x = x  # начальные координаты
        self.y = y
        self.max_length_hor = max_length_hor
        self.max_length_ver = max_length_ver
        self.xvel = left
        self.yvel = up
        self.image.set_colorkey(Color(100, 0, 0))
        self.boltAnim = makeanim(ANIMATION_STAY, ANDELAY)
        self.boltAnim.play()

    def update(self, platforms):
        self.image.fill(Color(100, 0, 0))
        self.boltAnim.blit(self.image, (0, 0))

        self.rect.y += self.yvel
        self.rect.x += self.xvel

        self.collide(platforms)

        if self.startX - self.rect.x > self.maxLengthLeft:
            self.xvel = -self.xvel  # если прошли максимальное растояние, то идеи в обратную сторону
        if self.startY - self.rect.y > self.maxLengthUp:
            self.yvel = -self.yvel  # если прошли максимальное растояние, то идеи в обратную сторону, вертикаль

    def collide(self, platforms):
        for pl in platforms:
            if sprite.collide_rect(self, pl) and self != pl:
                self.xvel = - self.xvel
                self.yvel = - self.yvel


def main():
    pygame.init()
    screen = pygame.display.set_mode(DISPLAY, FLAGS, DEPTH)
    pygame.display.set_caption("Place name of your game here for moneh!!! :DDDDD")
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


if __name__ == "__main__":
    main()