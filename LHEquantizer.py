# LHE Codec
# Author: Eduardo Rodes Pastor


import math, struct, os
from PIL import Image
from array import *
from numpy import zeros

# --------------#
# LHE QUANTIZER #
# --------------#

#*********************************************************************************************#
#	Function initHopsCache: # Initializes pre-computed hop values.                            #
#	This is a cache of ratio ("r") to avoid pow functions                                     #
#	We will compute cache ratio for different rmax values, although we will use               #
#	finally only rmax=25 (which means 2.5f). This function is generic and experimental        #
#	and this is the cause to compute more things than needed.                                 #
#	Given a certain h1 value and h0 luminance, the "luminance hop" of hop "i" is stored       #
#	in hn[absolute h1 value][luminance of h0 value]                                           #
#	                                                                                          #
#	For example,  h4 (null hop) is always 0, h1 is always hop1 (from 4 to 10), h2 is hop1*r,  #
#	but this is just the hop. The final luminance of h2 is luminance of h0 + hop1*r           #
#	                                                                                          #
#	hn is, therefore, the array of "hops" in terms of luminance but not the final luminances. #
#*********************************************************************************************#

def initHopsCache():
		
	h1range = 20 # Although h1range is only from 4 to 10, we will fill more possible values in the pre-computed hops
	
	h0 = zeros((h1range, 256))
	h1 = zeros((h1range, 256))
	h2 = zeros((h1range, 256))
	# h3 = h4 - hop1, and h5 = h4 + hop1, but we dont need an array for them
	h6 = zeros((h1range, 256))
	h7 = zeros((h1range, 256))
	h8 = zeros((h1range, 256)) 	
	
	# This is the real cache to be used in the LHE quantizer, and depends on the used ratio
	# Meaning: cache[h1][luminance][ratio][hop_index]
	cache = zeros((h1range, 256, 50, 9)) 
	
	# Cache of ratios (to avoid Math.pow operation)
	# Meaning: ratios[+/-][h1][h0][rmax]
	ratios = zeros((2, h1range, 256, 50)) 	
	
	for hop0 in range (0, 256):
		for hop1 in range (1, h1range):
			percent_range = 0.8 # 80%
			
			# This bucle allows computations for different values of rmax from 20 to 40, 
			# but only one value (25) is used in LHE
			for rmax in range (20, 41):
				# r values for positive hops	
				ratios[0][hop1][hop0][rmax] = pow(percent_range * (255-hop0)/(hop1), 0.33333333) 
				
				# r' values for negative hops
				ratios[1][hop1][hop0][rmax] = pow(percent_range * (hop0)/(hop1), 0.33333333) 	
				
				# Limits
				maximum = float(rmax)/10 # If rmax is 25 then max is 2.5f 
				if (ratios[0][hop1][hop0][rmax] > maximum):
					ratios[0][hop1][hop0][rmax] = maximum 
				if (ratios[1][hop1][hop0][rmax] > maximum):
					ratios[1][hop1][hop0][rmax] = maximum 

		# Assignment of precomputed hop values, for each hop1 value
		for hop1 in range(1, h1range):

			# Same bucle as before
			for rmax in range(20, 41):

		        # r value for positive hops from ratios	
				ratio_pos = ratios[0][hop1][hop0][rmax] 
				
				# r' value for negative hops from ratios
				ratio_neg = ratios[1][hop1][hop0][rmax] 

				# COMPUTATION OF LUMINANCES:
				# Luminance of positive hops
				h6[hop1][hop0] = hop1 * ratio_pos 
				h7[hop1][hop0] = h6[hop1][hop0] * ratio_pos 
				h8[hop1][hop0] = h7[hop1][hop0] * ratio_pos 

				# Luminance of negative hops	                        
				h2[hop1][hop0] = hop1 * ratio_neg 
				h1[hop1][hop0] = h2[hop1][hop0] * ratio_neg 
				h0[hop1][hop0] = h1[hop1][hop0] * ratio_neg 
			
				# Final color component (luminance or chrominance). Depends on hop1
				# From most negative hop (cache[hop1][hop0][0]) to most positive hop (cache[hop1][hop0][8])
				cache[hop1][hop0][rmax][0] = hop0  - int(h0[hop1][hop0])
				if (cache[hop1][hop0][rmax][0] <= 0):
					cache[hop1][hop0][rmax][0] = 1
				cache[hop1][hop0][rmax][1] = hop0  - int(h1[hop1][hop0])
				if (cache[hop1][hop0][rmax][1] <= 0): 
					cache[hop1][hop0][rmax][1] = 1
				cache[hop1][hop0][rmax][2] = hop0  - int(h2[hop1][hop0])  
				if (cache[hop1][hop0][rmax][2] <= 0):
					cache[hop1][hop0][rmax][2] = 1
				cache[hop1][hop0][rmax][3] = hop0 - hop1 
				if (cache[hop1][hop0][rmax][3] <= 0):
					cache[hop1][hop0][rmax][3] = 1 
				cache[hop1][hop0][rmax][4] = hop0  # Null hop
				
				# Check of null hop value. This control is used in "LHE advanced", where value of zero is forbidden
				# In basic LHE we don't need this
				if (cache[hop1][hop0][rmax][4] <= 0):
					cache[hop1][hop0][rmax][4] = 1  # Null hop
				if (cache[hop1][hop0][rmax][4] > 255):
					cache[hop1][hop0][rmax][4] = 255 # Null hop
				
				cache[hop1][hop0][rmax][5] = hop0+hop1 
				if (cache[hop1][hop0][rmax][5] > 255):
					cache[hop1][hop0][rmax][5] = 255 
				cache[hop1][hop0][rmax][6] = hop0  + int(h6[hop1][hop0])
				if (cache[hop1][hop0][rmax][6] > 255):
					cache[hop1][hop0][rmax][6] = 255
				cache[hop1][hop0][rmax][7] = hop0  + int(h7[hop1][hop0]) 
				if (cache[hop1][hop0][rmax][7] > 255):
					cache[hop1][hop0][rmax][7] = 255
				cache[hop1][hop0][rmax][8] = hop0  + int(h8[hop1][hop0]) 
				if (cache[hop1][hop0][rmax][8] > 255):
					cache[hop1][hop0][rmax][8] = 255

	return cache	


#*******************************************************************#
#	Function getImageData: This gets the width and height of an     #
#	image (in pixels) and the total number of pixels of it.         #
#	Input: image file                                               #
#	Output: width (pixels), height (pixels), number of pixels       #
#*******************************************************************#

def getImageData(filename):

	im = Image.open(filename)
	width = im.size[0]
	height = im.size[1]
	npix = im.size[0] * im.size[1]

	return width, height, npix


#*******************************************************************#
#	Function RGBtoYUV: This converts three lists (red, blue, green) #
#	in their equivalent YUV lists.                                  #
#	Input: r [], g [], b []                                         #
#	Output: y [], cb [], cr []                                      #
#*******************************************************************#

def RGBtoYUV(r, g, b): # in (0,255) range

	# All of these lists have the same length
	y = [0] * len(r) 
	cb = [0] * len(r) 
	cr = [0] * len(r)

	# This is just the formula to get YUV from RGB.
	for i in range(0, len(r)): 		
		y[i] = int(0.299 * r[i] + 0.587 * g[i] + 0.114 * b[i])
		cb[i] = int(128 - 0.168736 * r[i] - 0.331364 * g[i] + 0.5 * b[i])
		cr[i] = int(128 + 0.5 * r[i] - 0.418688 * g[i] - 0.081312 * b[i])

	return y, cb, cr


#*****************************************************************************#
#	Function getRGB: This gets the RGB values from a given file and saves     #
#	them in three lists from a given file.                                    #
#	Input: file, number of pixels of the file                                 #
#	Output: r [], g [], b []                                                  #
#*****************************************************************************#

def getRGB(filename, npix):

	# Getting image pixels RGB values
	im = Image.open(filename)
	rgb_im = im.convert('RGB')

	# Creating three lists of npix items
	r = [-1] * npix 
	g = [-1] * npix
	b = [-1] * npix

	for y in range(0, im.size[1]):
		for x in range(0, im.size[0]):

			# We get the RGB value in each pixel and save each component in an array
			rpix, gpix, bpix = rgb_im.getpixel((x,y)) 
			r[im.size[0]*y + x] = rpix
			g[im.size[0]*y + x] = gpix
			b[im.size[0]*y + x] = bpix

	return r, g, b


#*******************************************************************************#
#	Function getHops: This gets a specific hop list given the YUV ones. The hop #
#	value results on a kind of average between the previous hop and the         #
#	upper-right hop, unless the analyzed pixel doesnt have both of them.        #
#	Input: y [], cr [], cb [], component hops we want in return                 #
#	(it can be "y", "cr" or "cb"), chrominance mode and total number of pixels  #
#	Output: component hops []                                                   #
#*******************************************************************************#

def getHops(y, cb, cr, component, filename, mode, npix):
	
	# Hop1 interval: [4,10]
	max_hop1 = 10
	min_hop1 = 4

	# We start in the center of the interval
	start_hop1 = (max_hop1+min_hop1)/2 
	hop1 = start_hop1

	hop0 = 0 # Predicted luminance signal
	hop_number = 4 # Pre-selected hop -> 4 is null hop
	oc = 0 # Original color
	pix = 0 # Pixel position, from 0 to image size        
	last_small_hop = "false" # Indicates if last hop is small. Used for h1 adaptation mechanism
	rmax = 25 # Ratio used in LHE

	# Depending on the mode we are, the length of the list this method returns changes.
	if (mode == 0 and component != "y"): 
		hops = [-1] * int(npix/4) 
		result = [-1] * int(npix/4) # 1 chrominance for 4 values in 4:2:0
	elif (mode == 1 and component != "y"):
		hops = [-1] * int(npix/2)
		result = [-1] * int(npix/2) # 1 chrominance for 2 values in 4:2:2
	else:
		hops = [-1] * npix
		result = [-1] * npix # 1 chrominance for each value in 4:4:4

	im = Image.open(filename) # Used image
	cache = initHopsCache() # Initializes the hops cache

	h = 0 # Vertical counter
	x = 0 # Horizontal counter
	k = 0 # Original color counter

	# If we are in mode 4:2:2 or 4:2:0, we need to check every 2 pixels, so width 
	# is reduced to its half.
	if (mode != 2 and component != "y"): 
		width = im.size[0]/2
	else:
		width = im.size[0] # Otherwise, we go normal

	while (h < im.size[1]): # Image height
		while (x < im.size[0]): # Image width

			# Original image luminances are stored in the array "y"
			# Chrominance values are stored in cb and cr
			if (component == "y"):
				oc = y[k]
			try:
				if (component == "cr"):
					oc = cr[k]
				elif (component == "cb"):
					oc = cb[k]
			except:
				break # Sometimes we'll get images with an odd number of horizontal pixels, so we need this to avoid errors.


			# HOP0 PREDICTION #
			# ------------------------------------------------------------------------------ #

			# If we are not in a border, we need the previous pixel and the upper-right one.
			if (h > 0 and x > 0 and x != im.size[0] - 1 and x != im.size[0]):
				hop0 = (4*result[pix-1]+3*result[pix + 1 - width])/7 

			# If we are in the beginning of a row, we reset Hop1
			elif (x == 0 and h > 0):
				hop0 = result[pix- width] 
				last_small_hop = "false" 
				hop1 = start_hop1 

			# If we are in the end of a row, we need the previous pixel and the upper one
			elif ((x == im.size[0]-1 or x == im.size[0]) and h > 0): 
				hop0 = (4*result[pix-1]+2*result[pix- width])/6 

			# If we are in the first row, the hop (from 0 to 256) will be the result of the previous pixel
			elif (h == 0 and x > 0):
				hop0 = result[pix-1] 

			# First pixel is always perfectly predicted 	
			elif (x == 0 and h == 0):
				hop0 = oc 

			# HOPS COMPUTATION #
			# ---------------------------------------------------- #

			# Initial error values 
			emin = 256 # Current minimum prediction error 
			e2 = 0 # Computed error for each hop 
			finbuc = 0 # We can optimize the code below with this

			# Positive hops computation
			if (oc - hop0 >= 0): 
				for j in range (4, 9):
					# We start checking the difference between the original color and the cache
					e2 = oc - cache[int(hop1)][int(hop0)][rmax][j] 
					if (e2 < 0): 
						e2 = - e2
						finbuc = 1 # When error is negative, we got the hop we need
					if (e2 < emin):
						hop_number = j # Hop assignment
						emin = e2
						if (finbuc == 1): # This avoids an useless iteration
							break
					else:
						break

			# Negative hops computation. Same bucle as before
			else:
				for j in range(4, -1, -1):
					e2 = cache[int(hop1)][int(hop0)][rmax][j] - oc  
					if (e2 < 0): 
						e2 = - e2
						finbuc = 1 
					if (e2 < emin): 
						hop_number = j 
						emin = e2
						if (finbuc == 1):
							break
					else:
						break 

			# Assignment of final value
			try:
				result[pix] = cache[int(hop1)][int(hop0)][25][hop_number] # Final luminance/chrominance
				hops[pix] = hop_number  # Final hop value
			except:
				break # This prevents unwanted exceptions

			# Tunning hop1 for the next hop ("h1 adaptation")
			small_hop = "false" 
			if (hop_number <= 5 and hop_number >= 3): 
				small_hop = "true" # Hop 4 is in the center and is null.
			else:
				small_hop = "false"      

			if (small_hop == "true" and last_small_hop == "true"):
				hop1 = hop1-1 
				if (hop1 < min_hop1):
					hop1 = min_hop1 
			else:
				hop1 = max_hop1

			# Let's go for the next pixel
			last_small_hop = small_hop
			pix = pix + 1

			# If we are in 4:2:2 or 4:2:0 and working with chrominance lists...
			if (mode != 2 and component != "y"):
				x = x + 2 # We check every 2 pixels
				if (mode == 0 and (x == im.size[0] or x == im.size[0] - 1)):
					k = k + im.size[0] + 2 # If we are in 4:2:0, we need to check EVERY 2 ROWS
				else:
					k = k + 2 # If we are in 4:2:2, we need to check EACH ROW
			else:
				# Otherwise, we go normal
				x = x + 1 
				k = k + 1

		x = 0 # This resets the horizontal counter

		# If we are in 4:2:0 and working with chrominance, we check every 2 rows
		if (mode == 0 and component != "y"): 
			h = h + 2
		else:
			h = h + 1 # Otherwise, we go normal

	return hops, result