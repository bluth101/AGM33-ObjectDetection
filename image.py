from PIL import Image
import colorsys
import pygame
import random

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

def get_block_count(source):
	found = []
	for y in range(0,len(source)):
		for x in range(0,len(source[y])):
			val = source[y][x]
			if( val != 0 and not val in found ):
				found.append(val)
	return len(found)

# Start Pygame at top for timer functions
pygame.init()

# SETTINGS
checks_above = 10 # How many pixels are checked above for an object to join
lum_limit = 40.0 # Any luminosity below below % will count as dark
show_debug = True # Will highlight detected objects

# Load image
image = "real2.jpg"
im = Image.open(image)
pix = im.load()

# Variables for object detection
blocks = []
lums = []
platforms = 0
objects = 0
blockID = 0
scale = 4 # Check every *scale* pixels

# Detect dark / solid objects
for y in range(0,im.size[1]//scale):
	platform = 0
	row_blocks = []

	for x in range(0,im.size[0]//scale):
		val = rgb_to_hsl(pix[x*scale,y*scale])[2]*100

		solid = True
		if( val < lum_limit and platform == 0 ):
			# We have found a new platform
			platform = 1
			blockID += 1
		elif( platform > 0 and val < lum_limit ):
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
				for test in range(1,checks_above):
					if( test > y ):
						break
					above = blocks[y-test][x]
					if( above != blockID and above != 0 ):
						convert_block_id(blocks, above, blockID)
						convert_block_id(row_blocks, above, blockID)
						break

		lums.append( val )

	blocks.append(row_blocks)


# Initalise Pygame

pygame.font.init()

window_size = (800,600)
display = pygame.display.set_mode(window_size)
font = pygame.font.SysFont("Sans Serif", 30)

pygame.display.set_caption("Solid Object Detection")


# Load the image again TODO: Use image data from above!
pyg_image = pygame.image.load(image)
display.blit(pyg_image, (0, 0))

# Create debug surfaces
text_surface = pygame.Surface(window_size, pygame.SRCALPHA, 32)
debug_surface = pygame.Surface(window_size, pygame.SRCALPHA, 32)

text_surface = text_surface.convert_alpha()
debug_surface = debug_surface.convert_alpha()

# If enabled, loop through and colour each object
if( show_debug ):
	block_colours = []
	# Create seperate surface to draw text onto, and make it transprent
	
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
				text_surface.blit(text,(x*scale,y*scale))

			pygame.draw.rect(debug_surface, col, (x*scale,y*scale,1*scale,1*scale))

#print(blocks)
print(str(platforms) + " platform(s) detected")
print(str(get_block_count(blocks)) + " object(s) detected")

display.blit(text_surface, (0,0))
pygame.display.update()

pyg_critter = pygame.image.load("critter.bmp")
critx = 320
crity = 0

print("It took " + str(pygame.time.get_ticks()) + " seconds to start")

run = True
while run:
	for event in pygame.event.get():
		if( event.type == pygame.QUIT ):
			run = False
		#if( event.type == pygame.MOUSEBUTTONUP ):
		#	pos = pygame.mouse.get_pos()
		#	critx = pos[0]
		#	crity = pos[1]

	display.blit(pyg_image, (0,0))

	if( show_debug ):
		display.blit(debug_surface, (0,0))
		display.blit(text_surface, (0,0))

	#if( blocks[35+crity+1][critx] == 0 ):
	#	crity += 1
	#display.blit(pyg_critter, (critx-25, crity))

	pygame.display.update()

pygame.quit()
