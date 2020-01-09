# -*- coding:utf-8 -*-

import pygame
from pygame.sprite import Sprite, collide_rect
from pygame import Surface, mixer
import pyganim

mixer.pre_init(44100, -16, 1, 512)
mixer.init()
# Параметры персонажа
MOVE_SPEED = 7
JUMP_POWER = 10

GRAVITY = 0.4
COLOR = (10, 120, 10)
# анимации персонажа
ANIMATION_DELAY = 0.1
ANIMATION_STAY = [('data/player/player.png', ANIMATION_DELAY)]

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

# персонаж
class Player(Sprite):
    def __init__(self, x, y):
        Sprite.__init__(self)
        self.image = Surface((20, 20))
        self.xvel = 0
        self.yvel = 0
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.onGround = False

        def make_boltAnim(anim_list, delay):
            boltAnim = []
            for anim in anim_list:
                boltAnim.append((anim, delay))
            Anim = pyganim.PygAnimation(boltAnim)
            return Anim

        self.boltAnimStay = pyganim.PygAnimation(ANIMATION_STAY)
        self.boltAnimStay.play()

        self.boltAnimRight = make_boltAnim(ANIMATION_RIGHT, ANIMATION_DELAY)
        self.boltAnimRight.play()

        self.boltAnimLeft = make_boltAnim(ANIMATION_LEFT, ANIMATION_DELAY)
        self.boltAnimLeft.play()

        self.boltAnimUp = make_boltAnim(ANIMATION_UP, ANIMATION_DELAY)
        self.boltAnimUp.play()
        self.jump_sound = mixer.Sound('data/sounds/jump.ogg')

    def update(self, left, right, up, platforms):
        if left:
            self.xvel = -MOVE_SPEED
            self.image.fill(COLOR)
            self.boltAnimLeft.blit(self.image, (0.1, 0.1))
        if right:
            self.xvel = MOVE_SPEED
            self.image.fill(COLOR)
            self.boltAnimRight.blit(self.image, (0.1, 0.1))
        if not(left or right):
            self.xvel = 0
            if not up:
                self.image.fill(COLOR)
                self.boltAnimStay.blit(self.image, (0.1, 0.1))

        if up:
            if self.onGround:
                self.yvel = -JUMP_POWER
                self.jump_sound.play()
            self.image.fill(COLOR)
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


class Platform(pygame.sprite.Sprite): # платформа
    def __init__(self, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.image = pygame.image.load('data/platforms/platform.png')
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y


SIZE = (800, 800)
# создаем окно
window = pygame.display.set_mode(SIZE)
# создаем рабочую поверхность (игровой экран)
screen = pygame.Surface(SIZE)

# создаем героя
hero = Player(55, 55)
left = right = up = False

# создание уровня
level = [
    '------------------------------',
    '-                            -',
    '-                            -',
    '-     ---           ---      -',
    '-                   ---      -',
    '-                            -',
    '-       ---           ---    -',
    '-                            -',
    '- --            --           -',
    '-          --                -',
    '-                            -',
    '-   ---        ------------  -',
    '-                            -',
    '-      --                    -',
    '-                            -',
    '-             ---            -',
    '-       --                   -',
    '-   ---                      -',
    '-                            -',
    '-                            -',
    '------------------------------']

sprite_group = pygame.sprite.Group()
sprite_group.add(hero)
platfroms = []

x = 0
y = 0
for row in level:
    for col in row:
        if col == '-':
            pl = Platform(x, y)
            sprite_group.add(pl)
            platfroms.append(pl)
        x += 40
    y += 40
    x = 0


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
    l = -target_rect.x + SIZE[0]/2
    t = -target_rect.y + SIZE[1]/2
    w, h = camera.width, camera.height
    
    l = min(0, l)
    l = max(-(camera.width-SIZE[0]), l)
    t = max(-(camera.height-SIZE[1]), t)
    t = min(0, t)
    
    return pygame.Rect(l, t, w, h)


total_level_width = len(level[0])*40
total_level_height = len(level)*40

camera = Camera(camera_func, total_level_width, total_level_height)

# Настройка звука
pygame.mixer.pre_init(44100, -16, 1, 512)
pygame.mixer.init()
sound = pygame.mixer.Sound('data/sounds/overworld.ogg')
sound.play(-1)

# открываем игровой цикл
running = True
timer = pygame.time.Clock()
while running:
    # блок управления событиями
    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            running = False

        if e.type == pygame.KEYDOWN:
            if e.key == pygame.K_LEFT:
                left = True
            if e.key == pygame.K_RIGHT:
                right = True
            if e.key == pygame.K_UP:
                up = True

        if e.type == pygame.KEYUP:
            if e.key == pygame.K_LEFT:
                left = False
            if e.key == pygame.K_RIGHT:
                right = False
            if e.key == pygame.K_UP:
                up = False

    # закрашиваем рабочую поверхность
    screen.fill((10, 120, 10))

    # отображение героя
    hero.update(left, right, up, platfroms)
    camera.update(hero)
    for e in sprite_group:
        screen.blit(e.image, camera.apply(e))
    #sprite_group.draw(screen)

    # отображаем рабочую поверхность в окне
    window.blit(screen, (0, 0))
    # обновляем окно
    pygame.display.flip()
    timer.tick(60)
