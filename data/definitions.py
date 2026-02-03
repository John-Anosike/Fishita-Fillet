import pygame
import random
import math
import os

game_over = " "  # can either be blank, "win", or "lose"

prefabs = [pygame.Rect(100, 304, 32, 128), pygame.Rect(256, 304, 256, 256), pygame.Rect(576, 368, 128, 256)]
bullets = []
lasers = []
bullet_particles = []
player_bullet_particles = []
dash_particles = []


class Player:
    def __init__(self):
        self.hitbox = pygame.Rect(50, 432, 96, 64)
        self.speed = 8
        self.dash_time = -61
        self.dash_origin = (self.hitbox.x, self.hitbox.y)
        self.dash_ready = pygame.mixer.Sound("data/sounds/powerup.wav")
        self.is_jumping = False
        self.gravity = 0
        self.gravity_accelaration = 0.5

        self.anim = []
        self.frame = 0
        self.max_frames = 6
        self.frame_time = 0
        self.max_frame_time = 2
        self.mask = None
        self.left, self.right, self.moving = False, False, False
        self.dash_particle_direction = -1  # multiply their speed by this
        self.repetitions = 0  # how many times does the animation repeat until we transition

        self.health = 5
        self.health_anim = [pygame.image.load("data/cat/health/" + f).convert_alpha() for f in os.listdir("data/cat/health")]
        self.hurt = pygame.mixer.Sound("data/sounds/hurt.wav")
        self.damaged = 0
        self.invincible = False

    def update(self):
        keys = pygame.key.get_pressed()

        # gravity
        self.hitbox.y += self.gravity
        # collision with the basic ground
        if self.hitbox.bottom >= 560:
            self.gravity = 0
            self.hitbox.bottom = 560
            self.is_jumping = False
        else:
            self.gravity += self.gravity_accelaration

        # all movement only works if the player's alive
        if self.health > 0:
            # move forward and backward
            if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
                self.hitbox.x += self.speed
                self.right = True
                self.left = False
                self.moving = True
                self.dash_particle_direction = -1

                # border correction
                if self.hitbox.right >= 768:
                    self.hitbox.x -= self.speed
            elif keys[pygame.K_a] or keys[pygame.K_LEFT]:
                self.hitbox.x -= self.speed
                self.left = True
                self.right = False
                self.moving = True
                self.dash_particle_direction = 1

                # border correction
                if self.hitbox.left <= 0:
                    self.hitbox.x += self.speed
            else:
                self.moving = False

            # jump
            if keys[pygame.K_SPACE] or keys[pygame.K_w] or keys[pygame.K_UP]:
                self.is_jumping = True
            if self.is_jumping:
                self.frame = 2
                self.hitbox.y -= 12

            # dash
            if (keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]) and self.dash_time <= -60:
                self.dash_time = 20
                self.mask = pygame.mask.from_surface(self.anim[self.frame])
                self.dash_origin = (self.hitbox.x, self.hitbox.y)
            elif self.dash_time >= -60:
                self.dash_time -= 1
                self.invincible = False  # change back to False

            if self.dash_time >= 0:
                self.speed = 24
                self.invincible = True
            else:
                self.speed = 8
            if self.dash_time == -60:
                self.dash_ready.play()

    def damage(self, deduction):
        if not self.invincible:
            if self.health > 0:
                self.health -= deduction
            self.hurt.play()
            self.damaged = 50  # a timer for a red glow around the player to indicate damage

    def draw(self, surf, color):
        global game_over
        if self.health > 0:
            # colors
            if color == "black":
                self.anim = [pygame.transform.scale(pygame.image.load("data/cat/black/" + f).convert_alpha(), (128, 128)) for f in os.listdir(
                    "data/cat/black")]
            elif color == "white":
                self.anim = [pygame.transform.scale(pygame.image.load("data/cat/white/" + f).convert_alpha(), (128, 128)) for f in os.listdir(
                    "data/cat/white")]
            elif color == "orange":
                self.anim = [pygame.transform.scale(pygame.image.load("data/cat/orange/" + f).convert_alpha(), (128, 128)) for f in os.listdir(
                    "data/cat/orange")]

            # dash effect
            # draw an effect onto the player
            if self.moving:
                mask = pygame.mask.from_surface(self.anim[self.frame])  # mask of the player
            else:
                mask = pygame.mask.from_surface(self.anim[0])  # mask of the player
            color_surface = mask.to_surface(setcolor=(95, 205, 228))  # make a surface from the mask
            color_surface.set_colorkey((0, 0, 0))  # get rid of the black from the surface
            color_surface.set_alpha(150)  # make it slightly transparent
            if self.dash_time >= 0:
                if self.moving:
                    self.anim[self.frame].blit(color_surface, (0, 0))
                    dash_particles.append(Particle(self.hitbox.x, self.hitbox.y, 32, 32, "linear", 0, 2, 50))
                else:
                    self.dash_particle_direction = 1
                    self.anim[0].blit(color_surface, (0, 0))
                    dash_particles.append(Particle(self.hitbox.centerx, self.hitbox.centery, 32, 32, "burst", 0, 2, 50))

            # damage effect
            if self.damaged > 0:
                self.damaged -= 1
                if self.moving:
                    damaged_mask = pygame.mask.from_surface(self.anim[self.frame])  # mask of the player
                else:
                    damaged_mask = pygame.mask.from_surface(self.anim[0])  # mask of the player
                damage_surface = damaged_mask.to_surface(setcolor=(255, 0, 0))  # make a surface from the mask
                damage_surface.set_colorkey((0, 0, 0))  # get rid of the black from the surface
                damage_surface.set_alpha(150)  # make it slightly transparent
                if self.moving:
                    self.anim[self.frame].blit(damage_surface, (0, 0))
                else:
                    self.anim[0].blit(damage_surface, (0, 0))

            # animation
            if self.moving:  # moving animation
                if self.frame_time <= 0:
                    if self.frame == self.max_frames:
                        self.frame = 0
                    else:
                        self.frame += 1
                    self.frame_time = self.max_frame_time
                else:
                    self.frame_time -= 1
                if self.right:
                    surf.blit(self.anim[self.frame], (self.hitbox.x - 16, self.hitbox.y - 64))
                elif self.left:
                    surf.blit(pygame.transform.flip(self.anim[self.frame], True, False), (self.hitbox.x - 16, self.hitbox.y - 64))
            else:  # resting position
                if self.right:
                    surf.blit(self.anim[0], (self.hitbox.x - 16, self.hitbox.y - 64))
                elif self.left:
                    surf.blit(pygame.transform.flip(self.anim[0], True, False), (self.hitbox.x - 16, self.hitbox.y - 64))
                else:
                    surf.blit(self.anim[0], (self.hitbox.x - 16, self.hitbox.y - 64))
        else:
            self.max_frames = 8
            self.max_frame_time = 4
            # colors
            if color == "black":
                self.anim = [pygame.transform.scale(pygame.image.load("data/cat/dead/black/" + f).convert_alpha(), (128, 128)) for
                             f in os.listdir("data/cat/dead/black")]
            elif color == "white":
                self.anim = [pygame.transform.scale(pygame.image.load("data/cat/dead/white/" + f).convert_alpha(), (128, 128)) for
                             f in os.listdir("data/cat/dead/white")]
            elif color == "orange":
                self.anim = [pygame.transform.scale(pygame.image.load("data/cat/dead/orange/" + f).convert_alpha(), (128, 128))
                             for f in os.listdir("data/cat/dead/orange")]

            # animation
            if self.frame_time <= 0:
                self.frame_time = self.max_frame_time
                if self.frame >= self.max_frames:
                    self.frame = 0
                    self.repetitions += 1
                else:
                    self.frame += 1
            else:
                self.frame_time -= 1
            surf.blit(self.anim[self.frame], (self.hitbox.x - 16, self.hitbox.y - 64))

            if self.repetitions >= 3:
                game_over = "lose"

        # healthbar and damage
        surf.blit(pygame.transform.scale(self.health_anim[-self.health - 1], (64, 64)), (16, 16))
        if self.dash_time <= -60:
            surf.blit(pygame.transform.scale(pygame.image.load("data/cat/dash/dashbar1.png").convert_alpha(), (64, 64)), (16, 72))
        else:
            surf.blit(pygame.transform.scale(pygame.image.load("data/cat/dash/dashbar2.png").convert_alpha(), (64, 64)), (16, 72))


class Fish:
    def __init__(self):
        self.hitbox = pygame.FRect(200, 400, 96, 96)
        self.gravity = 0
        self.gravity_acceleration = 0.5

        # animation stuff
        self.anim = [pygame.transform.scale(pygame.image.load("data/fishita/" + f).convert_alpha(), (96, 96)) for f in os.listdir(
            "data/fishita")]
        self.frame = 0
        self.max_frames = 3
        self.frame_time = 0
        self.max_frame_time = 6
        self.animate = False

        # boss stuff
        self.health = 100
        self.healthbar_bottom = pygame.image.load("data/boss/healthbar_bottom.png").convert_alpha()
        self.healthbar = pygame.image.load("data/boss/healthbar.png").convert_alpha()
        self.healthbar_top = pygame.image.load("data/boss/healthbar_top.png").convert_alpha()
        # there are 5 boss stages: drift (aimless roaming), laser (find the safe spot), tennis (hit the bullet back), rain (weave through the bullets), and downed (time to hit)
        self.attack_stages = ["drift", "laser", "tennis", "rain"]
        self.stage = "drift"
        self.speed = 6
        self.path_timer = 250
        self.path = [random.randint(0, 768 - self.hitbox.w), random.randint(0, 200)]
        self.bullet_timer = 150
        self.bullet_location = (0, 0)

        self.screen_alpha = 0

    def update(self, player):
        global game_over
        # simple health deduction
        if self.hitbox.colliderect(player.hitbox) and player.invincible:
            if self.health > 0:
                self.health -= 1
                hurt = pygame.mixer.Sound("data/sounds/hurt.wav")
                hurt.play()
        if self.health <= 0:
            if self.health == 0:  # ensures the particles only play once
                player_bullet_particles.append(Particle(self.hitbox.centerx, self.hitbox.centery, 64, 64, "burst", 0, 50, 50))
                player_bullet_particles.append(Particle(self.hitbox.centerx, self.hitbox.centery, 64, 64, "burst", 0, 50, 50))
            self.health -= 1
            if self.health <= -100:
                game_over = "win"
        else:
            # plot a random point for Fishita to go
            if self.path_timer <= 0:
                self.path_timer = 100  # to ensure it only chooses once
                self.stage = random.choice(self.attack_stages)
                if self.stage == "drift":
                    self.path_timer = 250

                    # x configuration
                    if self.hitbox.x >= player.hitbox.x:
                        self.path[0] = random.randint(player.hitbox.x, 768 - int(self.hitbox.w))
                    elif self.hitbox.x < player.hitbox.x:
                        self.path[0] = random.randint(int(self.hitbox.w), player.hitbox.x)

                    self.path[1] = random.randint(int(self.hitbox.h), 200)

                if self.stage == "rain":
                    self.path_timer = 500
                    self.path = [336, 4]

                if self.stage == "laser":
                    self.path_timer = 500
                    self.path = [336, -96]

                if self.stage == "tennis":
                    self.path_timer = 300
                    self.path = [336, 96]

            else:
                self.path_timer -= 1

            # x pathfinding
            if self.stage != "downed":
                if self.hitbox.x <= self.path[0] - self.speed:
                    self.hitbox.x += self.speed
                elif self.hitbox.x >= self.path[0] + self.speed:
                    self.hitbox.x -= self.speed
                else:
                    self.hitbox.x = self.path[0]

                # y pathfinding
                if self.hitbox.y <= self.path[1] - self.speed:
                    self.hitbox.y += self.speed
                elif self.hitbox.y >= self.path[1] + self.speed:
                    self.hitbox.y -= self.speed
                else:
                    self.hitbox.y = self.path[1]

            # drift mode
            if self.stage == "drift":
                if self.bullet_timer <= 0:
                    self.bullet_timer = 50
                    self.bullet_location = player.hitbox.center
                    bullets.append(Bullet(self.hitbox.centerx - 16, self.hitbox.centery - 16, self.bullet_location, "bullet"))
                    shoot = pygame.mixer.Sound("data/sounds/shoot.wav")
                    shoot.play()
                else:
                    self.bullet_timer -= 1

            # rain mode
            if self.stage == "rain" and self.hitbox.collidepoint(self.path):
                if self.bullet_timer <= 0:
                    self.bullet_timer = 10
                    self.bullet_location = player.hitbox.center  # why not ig
                    bullets.append(Bullet(random.randint(0, 736), random.randint(-200, 0), self.bullet_location, "rain"))
                else:
                    self.bullet_timer -= 1

            # laser mode
            if self.stage == "laser" and self.hitbox.x == self.path[0]:
                if self.screen_alpha < 200:
                    self.screen_alpha += 4
                if self.bullet_timer <= 0 and self.path_timer < 350:
                    self.bullet_timer = 75
                    lasers.append(Laser(player.hitbox.x))
                else:
                    self.bullet_timer -= 1
            elif self.stage != "laser" and self.screen_alpha > 0:
                self.screen_alpha -= 2

            # tennis mode
            if self.stage == "tennis" and self.hitbox.collidepoint(self.path):
                if self.bullet_timer <= 0:
                    self.bullet_timer = 200
                    self.bullet_location = player.hitbox.center
                    bullets.append((Bullet(self.hitbox.centerx - 24, self.hitbox.centery - 24, self.bullet_location, "tennis")))
                    shoot = pygame.mixer.Sound("data/sounds/shoot.wav")
                    shoot.play()
                else:
                    self.bullet_timer -= 1

            # downed stage
            if self.stage == "downed":
                self.hitbox.y += self.gravity
                if self.hitbox.bottom >= 560:
                    self.gravity = 0
                    self.hitbox.bottom = 560
                else:
                    self.gravity += self.gravity_acceleration

    def draw(self, surf):
        surf.blit(self.anim[self.frame], self.hitbox)

        if self.frame_time <= 0:
            self.frame_time = self.max_frame_time
            if self.frame >= self.max_frames:
                self.frame = 0
                self.animate = False
            else:
                self.frame += 1
        else:
            self.frame_time -= 1

        surf.blit(pygame.transform.scale(self.healthbar_bottom, (512, 32)), (128, 32))
        if self.health >= 0:
            surf.blit(pygame.transform.scale(self.healthbar, (512 * self.health / 100, 32)), (132, 32))
        surf.blit(pygame.transform.scale(self.healthbar_top, (512, 64)), (128, 32))


# done with bullets
class Bullet:
    def __init__(self, x, y, target, bullet_type):
        self.hitbox = pygame.Rect(x, y, 32, 32)
        self.type = bullet_type
        self.angle = math.atan2(target[1] - y, target[0] - x)
        self.target = target
        self.x_speed, self.y_speed = 6 * math.cos(self.angle), 6 * math.sin(self.angle)
        self.player_bullet = False

        self.explode = pygame.mixer.Sound("data/sounds/explosion.wav")

    def update(self, surf, player, fish):
        if self.type == "bullet":  # standard bullet
            if self.hitbox.colliderect(player.hitbox) and not player.invincible:  # health deduction
                self.explode.set_volume(1)
                self.explode.play()
                bullet_particles.append(Particle(self.hitbox.centerx, self.hitbox.centery, 64, 64, "burst", 0, 25, 10))
                self.x_speed, self.y_speed = 0, 0
                self.hitbox.x = -100
                self.hitbox.y = -100
                player.damage(1)
            if (self.hitbox.colliderect(player.hitbox) or self.hitbox.y >= 560) and not player.invincible:  # fancy particles
                self.explode.set_volume(1)
                self.explode.play()
                self.hitbox.x = -100
                self.hitbox.y = -100

            # draw the bullet
            if self.player_bullet:
                surf.blit(pygame.transform.scale(pygame.image.load("data/boss/player_bullet.png").convert_alpha(), (32, 32)), self.hitbox)
            else:
                surf.blit(pygame.transform.scale(pygame.image.load("data/boss/bullet.png").convert_alpha(), (32, 32)), self.hitbox)
        elif self.type == "rain":  # rain
            self.x_speed = 0
            if not self.player_bullet:
                self.y_speed = 6
            self.hitbox.w = 16
            # player-rain collision
            if self.hitbox.colliderect(player.hitbox) and not player.invincible:
                self.explode.set_volume(1)
                self.explode.play()
                bullet_particles.append(Particle(self.hitbox.centerx, self.hitbox.centery, 64, 64, "burst", 0, 25, 10))
                self.x_speed, self.y_speed = 0, 0
                self.hitbox.x = -100
                self.hitbox.y = -100
                player.damage(1)
            if (self.hitbox.colliderect(player.hitbox) or self.hitbox.y >= 560) and not player.invincible:
                self.explode.set_volume(0.5)
                self.explode.play()
                self.hitbox.x = -100
                self.hitbox.y = -100

            # draw the player rain
            if self.player_bullet:
                surf.blit(pygame.transform.scale(pygame.image.load("data/boss/laser/player_laser.png").convert_alpha(), (16, 32)), self.hitbox)
            else:
                surf.blit(pygame.transform.scale(pygame.image.load("data/boss/laser/laser1.png").convert_alpha(), (16, 32)), self.hitbox)
        elif self.type == "tennis":
            self.hitbox.w, self.hitbox.h = 48, 48
            if not self.player_bullet and self.hitbox.x > 0:  # the > 0 part ensures that it won't track the player when it's offscreen
                self.target = player.hitbox.center
                self.angle = math.atan2(self.target[1] - self.hitbox.centery, self.target[0] - self.hitbox.centerx)
                self.x_speed, self.y_speed = 8 * math.cos(self.angle), 8 * math.sin(self.angle)
            if self.hitbox.colliderect(player.hitbox) and not player.invincible:  # health deduction
                self.explode.set_volume(1)
                self.explode.play()
                bullet_particles.append(Particle(self.hitbox.centerx, self.hitbox.centery, 64, 64, "burst", 0, 25, 10))
                self.x_speed, self.y_speed = 0, 0
                self.hitbox.x = -100
                self.hitbox.y = -100
                if player.health >= 2:
                    player.damage(2)
                else:
                    player.damage(1)
            if self.player_bullet:
                surf.blit(pygame.transform.rotate(pygame.transform.scale(pygame.image.load(
                    "data/boss/fish_bullet.png").convert_alpha(), (96, 96)), 180), self.hitbox)
            else:
                surf.blit(pygame.transform.rotate(pygame.transform.scale(pygame.image.load(
                    "data/boss/fish_bullet.png").convert_alpha(), (96, 96)), 90 - math.degrees(self.angle)), self.hitbox)

        # fish collision
        if self.hitbox.colliderect(fish.hitbox) and self.player_bullet:
            if self.type == "tennis":
                fish.stage = "downed"
                fish.path_timer = random.randrange(100, 350, 50)
            self.explode.set_volume(1)
            self.explode.play()
            player_bullet_particles.append(Particle(fish.hitbox.centerx, fish.hitbox.centery, 64, 64, "burst", 0, 10, 50))
            player_bullet_particles.append(Particle(fish.hitbox.centerx, fish.hitbox.centery, 64, 64, "burst", 0, 10, 50))
            self.x_speed, self.y_speed = 0, 0
            self.hitbox.x = -100
            self.hitbox.y = -100
            if not self.type == "tennis":
                fish.health -= 2
            else:
                fish.health -= 5
        self.hitbox.x += self.x_speed
        self.hitbox.y += self.y_speed

        if self.hitbox.colliderect(player.hitbox) and player.invincible and not self.player_bullet:
            self.player_bullet = True
            if self.type == "tennis":
                self.x_speed, self.y_speed = 0, -12
            else:
                self.x_speed, self.y_speed = -self.x_speed, -self.y_speed  # done with bullets

        # remove offscreen bullets
        if self.hitbox.x <= 0 or self.hitbox.x >= 768 or self.hitbox.y >= 576:
            bullets.remove(self)
        if self.hitbox.y <= 0 and self.type != "rain" and self in bullets:
            bullets.remove(self)


# done with lasers
class Laser:
    def __init__(self, x):
        self.hitbox = pygame.Rect(x, 0, 128, 576)
        self.delay = 75
        self.laser_visual_width = 0

        self.anim = [pygame.image.load("data/boss/laser/" + f).convert_alpha() for f in os.listdir("data/boss/laser")]
        self.frame = 0
        self.max_frames = 3
        self.frame_time = 0
        self.max_frame_time = 1

        self.laser = pygame.mixer.Sound("data/sounds/laser.wav")
        self.warning = pygame.mixer.Sound("data/sounds/warning.wav")

        self.damaged_player = False

    def update(self, surf, player):
        # sounds
        if self.delay == 0:
            self.laser.play()
        elif self.delay == 25:
            self.warning.play(3)

        if self.delay <= 0:
            if self.laser_visual_width < self.hitbox.w:
                self.laser_visual_width += 16
            for y in range(0, 640, 256):
                surf.blit(pygame.transform.scale(self.anim[self.frame], (self.laser_visual_width, 256)),
                          (self.hitbox.x + 64 - self.laser_visual_width // 2, y))
            if self.delay > -50 and self.hitbox.colliderect(player.hitbox) and not player.invincible and not self.damaged_player:  # health deduction:
                self.damaged_player = True
                if player.health >= 2:
                    player.damage(2)
                else:
                    player.damage(1)

            # animation
            if self.frame_time <= 0:
                self.frame_time = self.max_frame_time
                if self.frame >= self.max_frames:
                    self.frame = 0
                else:
                    self.frame += 1
            else:
                self.frame_time -= 1
        else:
            pygame.draw.line(surf, (255, 0, 0), (self.hitbox.centerx, 0), (self.hitbox.centerx, 560), 5)

        if self.delay <= -50:
            self.laser_visual_width -= 24  # to counteract the self.laser_visual_width += 16 up there; subtraction should get me a -8
            if self.laser_visual_width <= 0:
                self.delay = 25
                self.hitbox.x = -200
                lasers.remove(self)
        else:
            self.delay -= 1
            pygame.draw.line(surf, (255, 0, 0), (336, -48), player.hitbox.center, 1)
            pygame.draw.circle(surf, (255, 0, 0), player.hitbox.center, 16, 1)


# done with particles
class Particle:
    def __init__(self, x, y, w, h, pattern, angle, count, duration):
        self.origin = (x, y)  # where to place the particle generator
        self.size = (w, h)  # the range which the particles can be generated
        self.pattern = pattern   # do the particles move in a line or a burst pattern?
        self.angle = math.radians(angle)  # how rotated is the direction of movement?
        self.count = count  # how many particles can exist at a time?
        self.duration = duration  # how long until a particle dies?

        self.particles = []
        self.particle_age = []
        self.particle_size = []
        self.particle_speed = []

        self.all_clear = False

        # optional gravity
        self.gravity = 0
        self.gravity_acceleration = 0.02

    def update(self, min_size, max_size, min_speed, max_speed):
        if all(p <= 0 for p in self.particle_age) and len(self.particle_age) > 0:
            self.all_clear = True
            self.particles.clear()
            self.particle_age.clear()
            self.particle_size.clear()
            self.particle_speed.clear()

        # patterns can be linear or burst. This'll effect how speed is handled
        if len(self.particles) < self.count and not self.all_clear:
            if self.pattern == "linear":
                self.particles.append([random.randint(self.origin[0], self.origin[0] + self.size[0]),
                                       random.randint(self.origin[1], self.origin[1] + self.size[1])])
            elif self.pattern == "burst":
                self.particles.append([random.randint(self.origin[0] - self.size[0], self.origin[0] + self.size[0]),
                                       random.randint(self.origin[1] - self.size[1], self.origin[1] + self.size[1])])
            self.particle_age.append(self.duration)
            self.particle_size.append(random.randint(min_size, max_size))
            self.particle_speed.append(random.uniform(min_speed, max_speed))

    def draw(self, surf, particle_img, gravity):
        if not self.all_clear:
            for particle in self.particles:
                surf.blit(pygame.transform.scale(particle_img, (self.particle_size[self.particles.index(particle)],
                                                                self.particle_size[self.particles.index(particle)])), particle)

                if self.particle_age[self.particles.index(particle)] <= 0:
                    # instead of deleting, we're just gonna re-define the particle when they die
                    particle[0] = -100
                    particle[1] = -100
                    self.particle_size[self.particles.index(particle)] = 0
                    self.particle_speed[self.particles.index(particle)] = 0
                else:
                    self.particle_age[self.particles.index(particle)] -= 1
                    if self.pattern == "linear":
                        particle[0] += self.particle_speed[self.particles.index(particle)] * math.cos(self.angle)
                        particle[1] += self.particle_speed[self.particles.index(particle)] * math.sin(self.angle)
                    if self.pattern == "burst":
                        angle = self.angle + math.atan2(particle[1] - self.origin[1], particle[0] - self.origin[0])
                        particle[0] += self.particle_speed[self.particles.index(particle)] * math.cos(angle)
                        particle[1] += self.particle_speed[self.particles.index(particle)] * math.sin(angle)
                    if gravity:
                        particle[1] += self.gravity
                        self.gravity += self.gravity_acceleration

