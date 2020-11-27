import colorsys
import pygame
import random
import numpy as np
import cv2

# SETTINGS
gChecks_above = 10 # How many pixels are checked above for an object to join
gLum_limit = 40.0 # Any luminosity below below % will count as dark
gDebug = False # Will highlight detected objects
gScale = 2 # Check every *scale* pixels

# returns: hsl of rgb
def rgb_to_hsl(rgb):
	r = rgb[0]/255
	g = rgb[1]/255
	b = rgb[2]/255

	return colorsys.rgb_to_hsv(r, g, b)

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

# returns: bool - if considered solid
def is_pixel_solid(pix):
	hsl = colorsys.rgb_to_hsv(pix[2]/255, pix[1]/255, pix[0]/255)
	val = hsl[2]*100
	if( val < gLum_limit ):
		return True
	else:
		return False

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
critx = 20
crity = 50

print("It took " + str(pygame.time.get_ticks()) + " seconds to start")

# Create a surface for the webcam (must be same size as webcam output)
cap = cv2.VideoCapture(0)

read_width = cap.get(3)//gScale
read_height = cap.get(4)//gScale

cap.set(3,read_width)
cap.set(4,read_height)

temp_surface = pygame.Surface((read_height, read_width), pygame.SRCALPHA, 32) # for rendering the camera output
cam_surface = pygame.Surface((read_width, read_height), pygame.SRCALPHA, 32)
buffer_surface = pygame.Surface((read_height, read_width), pygame.SRCALPHA, 32)

ret, pix = cap.read()	
blocks = process_image(pix)

scale_width = read_width//gScale
scale_height = read_height//gScale

# Main loop
run = True
while run:
	# Handle mouse / keyboard input
	for event in pygame.event.get():
		if( event.type == pygame.QUIT ):
			run = False
		if( event.type == pygame.MOUSEBUTTONUP ):
			pos = pygame.mouse.get_pos()
			# Invert them to account for surface rotation
			critx = pos[0]//gScale
			crity = pos[1]//gScale

			check = pix[critx][crity]
			val = colorsys.rgb_to_hls(check[2]/255, check[1]/255, check[0]/255)

			pygame.draw.rect(buffer_surface, pix[pos[0]][pos[1]], (400,400,30,30))
		if( event.type == pygame.KEYDOWN ):
			if( event.key == pygame.K_UP ):
				crity -= 30;

	# Draw webcam image
	if( pygame.time.get_ticks() % 2 == 0 ):
		# Capture and process webcam image
		ret, pix = cap.read()
		#blocks = process_image(pix)

		pygame.surfarray.blit_array(temp_surface, pix)
		#cam_surface = pygame.transform.rotate(temp_surface, 270)
		buffer_surface.blit(temp_surface, (0,0))
		#display.blit(pygame.transform.rotate(cam_surface, 270), (0,0))

		# If debug is enabled, process and draw that
		if( gDebug ):
			draw_debug(buffer_surface, blocks)

	# Critter movement
	sx = critx*gScale
	sy = crity*gScale

	if( sx > read_height-10 ):
		sx = 0
		critx = 0
	if( sy > read_width-10 ):
		sy = 0
		crity = 0

	# Check if the critter is colliding or falling
	if( not is_pixel_solid(pix[sx+1][sy]) ):
		critx += 1
	else:
		# if away from top, check if we need to push up
		if( critx > 5 ):
			if( is_pixel_solid(pix[sx-3][sy]) ):
				critx -= 4
		# EXPERIMENTAL: push left / right if pushed
		if( crity < read_width-20 ):
			if( is_pixel_solid(pix[sx-10][sy-10]) ):
				crity += 4
		if( 20 < read_width ):
			if( is_pixel_solid(pix[sx-10][sy+10]) ):
				crity -= 4

	buffer_surface.blit(pyg_critter, ((critx*gScale)-35, (crity*gScale)-25)) #-25, -35

	display.blit( pygame.transform.rotate(buffer_surface, 270), (0,0))
	#display.blit(buffer_surface, (0,0))

	pygame.display.update()
	pygame.time.wait(40)

cap.release()
pygame.quit()
