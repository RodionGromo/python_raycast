import pygame, time, sys
import pygame.event as pygevent
import pygame.draw as pygdraw
import pygame.font as pygfont
import pygame.mouse as pygmouse
from rclasses import Wall, Player, Renderer, Block, EmptyBlock

gameMode = True
displaySize = [1280,640]

player = Player(200, 250, angle=290)
player.density = 1
player.movementSpeed = 2
player.maxRange = 800
player.fov = 90

# you should read the config, now!
cfgFile = open("cfg.txt","r")
for line in cfgFile.readlines():
	command, value = line.split(" ")
	value = float(value)
	if command == "gameMode":
		gameMode = bool(value)
	if command == "GMScreenH":
		if gameMode:
			displaySize[1] = value
	if command == "GMScreenW":
		if gameMode:
			displaySize[0] = value
	if command == "MMScreenH":
		if not gameMode:
			displaySize[1] = value
	if command == "MMScreenW":
		if not gameMode:
			displaySize[0] = value
	if command == "fov":
		player.fov = value
	if command == "density":
		player.density = value
	if command == "maxRange":
		player.maxRange = value
cfgFile.close()

window = pygame.display.set_mode(displaySize)
buttonsDown = []
pygfont.init()
fpsFont = pygfont.SysFont("Arial",26)

objects = [
	Wall(250, 100, 400, 100),
	Wall(400, 50, 400, 350),
	Block(200, 150, 50, 50),
	EmptyBlock(10, 10, 400, 400),
	EmptyBlock(150, 150, 50, 50, disabledWalls=[1,1,0,0])
]
framerate = 0
loopTime = 0
wallRender = Renderer(displaySize[0]//2, displaySize)

if gameMode:
	wallRender = Renderer(0, displaySize, divider=0)
	pygmouse.set_visible(False)
	pygevent.set_grab(True)

while True:
	start_time = time.time()
	for event in pygevent.get():
		if event.type == pygame.QUIT:
			sys.exit()
		if event.type == pygame.KEYDOWN:
			buttonsDown.append(event.key)
		if event.type == pygame.KEYUP:
			buttonsDown.remove(event.key)
		if event.type == pygame.MOUSEMOTION:
			if gameMode:
				print(event.rel)
				if event.rel[0] > 0:
					player.angle += .25
				elif event.rel[0] < 0:
					player.angle -= .25


	if pygame.K_e in buttonsDown:
		player.angle += 2
	if pygame.K_q in buttonsDown:
		player.angle -= 2
	if pygame.K_w in buttonsDown:
		player.forward()
	if pygame.K_s in buttonsDown:
		player.backward()
	if pygame.K_a in buttonsDown:
		player.strafeLeft()
	if pygame.K_d in buttonsDown:
		player.strafeRight()
	if pygame.K_ESCAPE in buttonsDown:
		sys.exit()

	if player.x > displaySize[0]//2:
		player.setPos(0, player.y)
	if player.x < 0:
		player.setPos(displaySize[0]//2, player.y)
	if player.y > displaySize[1]:
		player.setPos(player.x, 0)
	if player.y < 0:
		player.setPos(player.x, displaySize[1])
	
	window.fill((0,0,0))
	if not gameMode:
		for wall in objects:
			wall.render(window)
		player.render(window)
		pygdraw.line(window, (255,255,0), [displaySize[0]//2, 0], [displaySize[0]//2, displaySize[1]])

	found_walls = player.floating_castRays(window, objects, draw=not gameMode)
	wallRender.renderWalls(window, found_walls, player)
	

	framerateText = fpsFont.render("{:.1f} FPS, {:.2f}ms".format(framerate, loopTime*1000), True, (144,0,0))
	window.blit(framerateText, (displaySize[0]-framerateText.get_width(), displaySize[1]-30))

	pygame.display.flip()

	loopTime = time.time() - start_time
	framerate = 1000 / (1000*(loopTime if loopTime else 1))
	#dtime.sleep(1)