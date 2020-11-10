import colorsys
import pygame
import random
import numpy as np
import cv2

# SETTINGS
gChecks_above = 10 # How many pixels are checked above for an object to join
gLum_limit = 40.0 # Any luminosity below below % will count as dark
gDebug = True # Will highlight detected objects
gScale = 3 # Check every *scale* pixels

# returns: hsl of rgb
def rgb_to_hsl(rgb):
	r = rgb[0]/255
	g = rgb[1]/255
	b = rgb[2]/255

	return colorsys.rgb_to_hsv(r, g, b)

	rgb = list(rgb)

	for i in range(3):
		rgb[i] = rgb[i] / 255

	rmin = min(rgb)
	rmax = max(rgb)

	luminosity = ((rmin + rmax )/2) * 100

	saturation = 0
	# If min & max are not equal, we have saturation!
	if( not rmin == rmax ):
		if( luminosity <= 0.5 ):
			saturation = (rmax - rmin)/(rmax + rmin)
		else:
			saturation = (rmax - rmin)/(2.0 - rmax - rmin)

		saturation = saturation*100

	hue = 0
	# Only calculate the hue if there's saturation
	if( not saturation == 0 ):
		r = rgb[0]
		g = rgb[1]
		b = rgb[2]

		if( rmax == r ):
			hue = (g-b)/(rmax-rmin)
		elif( rmax == g ):
			hue = 2.0 + ( (b-r)/(rmax-rmin) )
		elif( rmax == b ):
			hue = 4.0 + ( (r-g)/rmax-rmin )

		hue = hue * 60
		if( hue < 0 ):
			hue += 360

	return (hue, saturation, luminosity)
	# END OF RGB_TO_HSL

def convert_block_id(source, tochange, newid):
	for i in range(0,len(source)):
		if( isinstance(source[i], list) ):
			for y in range(0,len(source[i])):
				if source[i][y] == tochange:
					source[i][y] = newid
		else:
			if source[i] == tochange:
					source[i] = newid

# returns: number of blocks found in data
def get_block_count(source):
	found = []
	for y in range(0,len(source)):
		for x in range(0,len(source[y])):
			val = source[y][x]
			if( val != 0 and not val in found ):
				found.append(val)
	return len(found)

# returns: block data
def process_image(pix):
	read_width = len(pix)
	read_height = len(pix[0])
	# Variables for object detection
	blocks = []
	platforms = 0
	objects = 0
	blockID = 0
	hue_join = 10 # +- allowance for hue value to join blocks together

	# Detect dark / solid objects
	# originally im.size[1]
	for y in range(0,read_height//gScale):
		platform = 0
		row_blocks = []

		# originally im.size[0]
		for x in range(0,read_width//gScale):
			hsl = rgb_to_hsl(pix[x*gScale,y*gScale])
			val = hsl[2]*100
			hue = hsl[0]*255
			
			if x > 0:
				last_hue = rgb_to_hsl(pix[(x*gScale)-gScale,y*gScale])[0]*255

			solid = True
			if( val < gLum_limit and platform == 0 ):
				# We have found a new platform
				platform = 1
				blockID += 1
			elif( platform > 0 and ((val < gLum_limit) or (hue > last_hue-hue_join and hue < last_hue+hue_join)) ):
				# We have found another part of the platform
				platform += 1
			elif( platform > 0 ):
				# We have found the end of the platform
				platforms += 1
				platform = 0
			else:
				row_blocks.append(0)
				solid = False

			# If this isnt the first row, and there is a block above, join it to our current block
			if( solid ):
				row_blocks.append(blockID)
				if( y > 0 ):
					for test in range(1,gChecks_above):
						if( test > y ):
							break
						above = blocks[y-test][x]
						if( above != blockID and above != 0 ):
							convert_block_id(blocks, above, blockID)
							convert_block_id(row_blocks, above, blockID)
							break

		blocks.append(row_blocks)
	return blocks

def draw_debug(surface, blocks):
	block_colours = []
	count = 0

	for y in range(len(blocks)):
		for x in range(len(blocks[y])):
			current = blocks[y][x]
			if( current == 0 ):
				continue

			col = (255,0,0)
			if( current in block_colours ):
				col = block_colours[block_colours.index(current)+1]
			else:
				block_colours.append(current)
				block_colours.append((random.randint(0,255), random.randint(0,255), random.randint(0,255)))
				count += 1
				text = font.render(str(count), False, (255,0,0))
				display.blit(text,(x*gScale,y*gScale))

			pygame.draw.rect(surface, col, (x*gScale,y*gScale,1*gScale,1*gScale)) #debug_surface

# Initalise pygame
pygame.init()
pygame.font.init()

window_size = (800,600)
display = pygame.display.set_mode(window_size)
font = pygame.font.SysFont("Sans Serif", 30)

pygame.display.set_caption("AGM33")

# Create debug surface
debug_surface = pygame.Surface(window_size, pygame.SRCALPHA, 32)
debug_surface = debug_surface.convert_alpha()

#print(str(get_block_count(blocks)) + " object(s) detected")

# Load critters
pyg_critter = pygame.image.load("critter.bmp")
critx = 320
crity = 0

print("It took " + str(pygame.time.get_ticks()) + " seconds to start")

# Create a surface for the webcam (must be same size as webcam output)
cap = cv2.VideoCapture(0)

read_width = cap.get(3)
read_height = cap.get(4)

#cap.set(3,read_width)
#cap.set(4,read_height)

cam_surface = pygame.Surface((read_height, read_width), pygame.SRCALPHA, 32)

run = True
while run:
	for event in pygame.event.get():
		if( event.type == pygame.QUIT ):
			run = False
		#if( event.type == pygame.MOUSEBUTTONUP ):
		#	pos = pygame.mouse.get_pos()
		#	critx = pos[0]
		#	crity = pos[1]

	# Capture and process webcam image
	ret, pix = cap.read()	
	blocks = process_image(pix)

	# Draw webcam image
	pygame.surfarray.blit_array(cam_surface, pix)
	display.blit(cam_surface, (0,0))

	# If debug is enabled, process and draw that
	if( gDebug ):
		draw_debug(display, blocks)

	# Critter movement
	#if( blocks[35+crity+1][critx] == 0 ):
	#	crity += 1
	#display.blit(pyg_critter, (critx-25, crity))

	pygame.display.update()
	pygame.time.wait(1)

cap.release()
pygame.quit()
