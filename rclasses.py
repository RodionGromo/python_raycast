import pygame.draw as pygdraw
import math, pygame, threading

class Wall:
    def __init__(self, x, y, x1, y1, color=(255,255,255)):
        self.x1 = x
        self.y1 = y
        self.x2 = x1
        self.y2 = y1
        self.color = color 

    def render(self, window):
        pygdraw.line(window, self.color, [self.x1, self.y1], [self.x2, self.y2])

    def isColliding(self, pos, errorMargin=[0,0]):
        if self.x1-errorMargin[0] < pos[0] < self.x2+errorMargin[0]:
            if self.y1-errorMargin[1] < pos[1] < self.y2+errorMargin[1]:
                return True
        return False

class Block(Wall):
    def __init__(self, x, y, w, h, color=(255,255,255)):
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.color = color

        self.x1 = x
        self.x2 = x + w
        self.y1 = y
        self.y2 = y + h

    def render(self, window):
        rect = pygame.Rect(self.x, self.y, self.w, self.h)
        pygdraw.rect(window, self.color, rect)

class EmptyBlock:
    def __init__(self, x, y, w, h, color=(255,255,255), disabledWalls=[1,1,1,1]):
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.color = color

        # we create four walls and compare them
        self.walls = [
                    Wall(self.x, self.y, self.x + self.w, self.y),
                    Wall(self.x, self.y, self.x, self.y + self.h),
                    Wall(self.x + self.h, self.y, self.x + self.h, self.y + self.h),
                    Wall(self.x, self.y + self.h, self.x + self.h, self.y + self.h)
                ]
        nw = self.walls.copy()
        for i in range(len(disabledWalls)):
            if not disabledWalls[i]:
                nw.remove(self.walls[i])
        self.walls = nw.copy()

    def render(self, window):
        for wall in self.walls:
            wall.render(window)

    def isColliding(self, pos, errorMargin=[0,0]):
        for wall in self.walls:
            if wall.isColliding(pos, errorMargin=errorMargin):
                return True

def degToRad(deg):
    return deg * (math.pi / 180)

class Raycaster:
    def getRayEnd(self, pos, distance, angle):
        rayEnd = [0,0]
        rayEnd[0] = pos[0] + (distance * math.cos(degToRad(angle)))
        rayEnd[1] = pos[1] + (distance * math.sin(degToRad(angle)))
        return rayEnd

    def raycastToObject(self, pos, angle, walls, distance=-1, step=1):
        '''
        Single raycast to first object, returns pos, distance, ray angle and object index
        Arguments:
        - "distance" can be set to limit ray length
        - "step" can be set to set ray length addition size
        '''
        rayDist = 0
        hitObject = None
        maxRayDist = 500 if distance == -1 else distance
        while rayDist < maxRayDist:
            endPos = self.getRayEnd(pos, rayDist, angle)
            for i in range(len(walls)):
                if walls[i].isColliding(endPos, errorMargin=[1,1]):
                    return (endPos, rayDist, angle, i)
            rayDist += step

class vadimRaycaster:
    def collideLines(self, line1, line2):
        x0, y0, x1, y1 = line1
        x2, y2, x3, y3 = line2
        # x point
        xP1 = y0 + y2 + ((x2*(y2-y3))/(x2-x3)) - ((x0*(y1-y0))/(x1-x0))
        xP2 = ((y2-y3)/(x2-x3)) - ((y1-y0)/(x1-x0))
        x = xP1 / xP2
        # y point
        yP1 = (x * (y2-y3)) / (x2-x3)
        yP2 = y2 - ((x2*(y2-y3))/(x2-x3))
        y = yP1 + yP2

        pos = [x,y]
        return pos

class Renderer:
    def __init__(self, xoffset, displaySize, divider=2):
        self.xoffset = xoffset
        self.displaySize = displaySize
        self.divider=divider

    @staticmethod
    def map(x, in_min, in_max, out_min, out_max):
        return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min 

    def renderWalls(self, window, walls, player):
        # walls contains: 0: endPos, 1: distance, 2: angle, 3: objectIndex
        if self.divider:
            wallWidth = (self.displaySize[0]//self.divider) // len(walls)
        else:
            wallWidth = self.displaySize[0] // len(walls)
        wallColor = [14,14,14]
        for i in range(len(walls)):
            wall = walls[i]
            if wall is None:
                continue
            h1 = (wall[1] * math.cos(degToRad(wall[2] - player.angle)))
            wallHeight = (self.displaySize[1] / h1 if h1 else 1) * 16
            wallColor = [self.map(wall[1], 0, player.maxRange, 255, 0)]*3
            rect = pygame.Rect(self.xoffset + (i * wallWidth), self.displaySize[1]/2 - wallHeight/2, wallWidth, wallHeight)
            pygdraw.rect(window, wallColor, rect)

class Player:
    def __init__(self, x, y, angle=90, fov=90, color=(255,0,0), walkSpeed=.5):
        self.x = x
        self.y = y
        self.pos = [self.x, self.y]
        self.angle = angle

        self.fov = fov
        self.color = color
        self.maxRange = 200
        self.angleLineSize = 20
        self.movementSpeed = walkSpeed

        self.raycaster = Raycaster()
        self.density = 5

    def render(self, window):
        pygdraw.circle(window, self.color, [self.x, self.y], 5)
        self.rayRender(window)

    def castRays(self, window, walls):
        walls_detected = []
        for i in range(-self.fov//2, self.fov//2, self.density):
            raycast = self.raycaster.raycastToObject(self.pos, self.angle+i, walls, distance=self.maxRange)
            if raycast is not None:
                walls_detected.append(raycast)
                pygdraw.line(window, (0,255,0), self.pos, raycast[0])
            else:
                walls_detected.append(None)
        return walls_detected

    def floating_castRays(self, window, walls, draw=True):
        walls_detected = []
        angle = -self.fov//2
        endAngle = self.fov//2
        while angle <= endAngle:
            raycast = self.raycaster.raycastToObject(self.pos, self.angle+angle, walls, distance=self.maxRange)
            if raycast is not None:
                walls_detected.append(raycast)
                if draw:
                    pygdraw.line(window, (0,255,0), self.pos, raycast[0])
            else:
                walls_detected.append(None)
            angle += self.density
        #print(len(walls_detected))
        return walls_detected

    def forward(self):
        rayEnd = self.raycaster.getRayEnd(self.pos, self.movementSpeed, self.angle)
        self.setPosList(rayEnd)

    def strafeLeft(self):
        rayEnd = self.raycaster.getRayEnd(self.pos, self.movementSpeed, self.angle-90)
        self.setPosList(rayEnd)

    def strafeRight(self):
        rayEnd = self.raycaster.getRayEnd(self.pos, self.movementSpeed, self.angle+90)
        self.setPosList(rayEnd)

    def backward(self):
        rayEnd = self.raycaster.getRayEnd(self.pos, -self.movementSpeed, self.angle)
        self.setPosList(rayEnd)

    def setPosList(self, pos):
        self.x = pos[0]
        self.y = pos[1]
        self.pos = pos

    def setPos(self, x, y):
        self.x = x
        self.y = y
        self.pos = [x,y]

    def rayRender(self, window):
        rayEnd = self.raycaster.getRayEnd(self.pos, self.angleLineSize, self.angle)
        pygdraw.line(window, self.color, self.pos, rayEnd)

