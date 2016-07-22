# LHE Codec
# Author: Eduardo Rodes Pastor

import huff, math, struct, os
from PIL import Image
from numpy import zeros
from array import *
from encoder import *

# --------------
# LHE QUANTIZER |
# --------------

def initHopsCache(): # Initializes pre-computed hop values
	
	# This is a cache of ratio ("r") to avoid pow functions
	#float[][][][] cache_ratio  #meaning : [+/-][h1][h0][rmax]
	# we will compute cache ratio for different rmax values, although we will use 
	# finally only rmax=25 (which means 2.5f). This function is generic and experimental
	# and this is the cause to compute more things than needed.

	
	# h1 value belongs to [4..10]
	# Given a certain h1 value, and certaing h0 luminance, the "luminance hop" of hop "i" is stored here:
	# hn[absolute h1 value][luminance of h0 value]
	# for example,  h4 (null hop) is always 0, h1 is always hop1 (from 4 to 10), h2 is hop1*r,
	# however this is only the hop. the final luminance of h2 is luminace=(luminance of h0)+hop1*r    
	# hn is, therefore, the array of "hops" in terms of luminance but not the final luminances.
	# float[][] h0,h1,h2,h6,h7,h8 # h0,h1,h2 are negative hops. h6,h7,h8 are possitive hops
	
	h1range = 20 # in fact h1range is only from 4 to 10. However i am going to fill more possible values in the pre-computed hops
	
	h0 = zeros((h1range, 256))
	h1 = zeros((h1range, 256))
	h2 = zeros((h1range, 256))
	# in the center is located h3=h4-hop1, and h5=h4+hop1, but I dont need array for them
	h6 = zeros((h1range, 256))
	h7 = zeros((h1range, 256))
	h8 = zeros((h1range, 256)) 
	
	
	# pccr is the value of the REAL cache. This is the cache to be used in the LHE quantizer
	# sorry...i dont remenber why this cache is named "pccr" :) instead of "cache"
	# this array takes into account the ratio
	# meaning: pccr [h1][luminance][ratio][hop_index]
	pccr = zeros((h1range, 256, 50, 9)) 
	
	#cache of ratios ( to avoid Math.pow operation)
	#---------------------------------------------
	cache_ratio = zeros((2, h1range, 256, 50)) 
	
	
	for hop0 in range (0, 256):
		for hop1 in range (1, h1range):
			percent_range=0.8 # 80%
			
			#this bucle allows computations for different values of rmax from 20 to 40. 
			#however, finally only one value (25) is used in LHE
			for rmax in range (20, 41):
				# r values for possitive hops	
				cache_ratio[0][hop1][hop0][rmax] = pow(percent_range * (255-hop0)/(hop1), 0.33333333) 
				
				# r' values for negative hops
				cache_ratio[1][hop1][hop0][rmax] = pow(percent_range * (hop0)/(hop1), 0.3333333) 	
				
				# control of limits
				maximum = float(rmax)/10 # if rmax is 25 then max is 2.5f 
				if (cache_ratio[0][hop1][hop0][rmax] > maximum):
					cache_ratio[0][hop1][hop0][rmax] = maximum 
				if (cache_ratio[1][hop1][hop0][rmax] > maximum):
					cache_ratio[1][hop1][hop0][rmax] = maximum 
		#assignment of precomputed hop values, for each ofp value
		#--------------------------------------------------------
		for hop1 in range(1, h1range):

			#finally we will only use one value of rmax rmax=30, 
			#however we compute from r=2.0f (rmax=20) to r=4.0f (rmax=40)
			for rmax in range(20, 41):
		        #get r value for possitive hops from cache_ratio	
				ratio_pos = cache_ratio[0][hop1][hop0][rmax] 
				
				#get r' value for negative hops from cache_ratio
				ratio_neg = cache_ratio[1][hop1][hop0][rmax] 

				# COMPUTATION OF LUMINANCES:
				# luminance of possitive hops
				h6[hop1][hop0] = hop1 * ratio_pos 
				h7[hop1][hop0] = h6[hop1][hop0] * ratio_pos 
				h8[hop1][hop0] = h7[hop1][hop0] * ratio_pos 

				#luminance of negative hops	                        
				h2[hop1][hop0] =hop1 * ratio_neg 
				h1[hop1][hop0] = h2[hop1][hop0] * ratio_neg 
				h0[hop1][hop0] = h1[hop1][hop0] * ratio_neg 
			
				#final color component ( luminance or chrominance). depends on hop1
				#from most negative hop (pccr[hop1][hop0][0]) to most possitive hop (pccr[hop1][hop0][8])
				#--------------------------------------------------------------------------------------
				pccr[hop1][hop0][rmax][0] = hop0  - int(h0[hop1][hop0])
				if (pccr[hop1][hop0][rmax][0] <= 0):
					pccr[hop1][hop0][rmax][0] = 1
				pccr[hop1][hop0][rmax][1] = hop0  - int(h1[hop1][hop0])
				if (pccr[hop1][hop0][rmax][1] <= 0): 
					pccr[hop1][hop0][rmax][1] = 1
				pccr[hop1][hop0][rmax][2] = hop0  - int(h2[hop1][hop0])  
				if (pccr[hop1][hop0][rmax][2] <= 0):
					pccr[hop1][hop0][rmax][2] = 1
				pccr[hop1][hop0][rmax][3] = hop0 - hop1 
				if (pccr[hop1][hop0][rmax][3] <= 0):
					pccr[hop1][hop0][rmax][3] = 1 
				pccr[hop1][hop0][rmax][4] = hop0  # null hop
				
				#check of null hop value. This control is used in "LHE advanced", where value of zero is forbidden
				#in basic LHE there is no need for this control
				if (pccr[hop1][hop0][rmax][4] <= 0):
					pccr[hop1][hop0][rmax][4] = 1  # null hop
				if (pccr[hop1][hop0][rmax][4] > 255):
					pccr[hop1][hop0][rmax][4] = 255 # null hop
				
				pccr[hop1][hop0][rmax][5] = hop0+hop1 
				if (pccr[hop1][hop0][rmax][5] > 255):
					pccr[hop1][hop0][rmax][5] = 255 
				pccr[hop1][hop0][rmax][6] = hop0  + int(h6[hop1][hop0])
				if (pccr[hop1][hop0][rmax][6] > 255):
					pccr[hop1][hop0][rmax][6] = 255
				pccr[hop1][hop0][rmax][7] = hop0  + int(h7[hop1][hop0]) 
				if (pccr[hop1][hop0][rmax][7] > 255):
					pccr[hop1][hop0][rmax][7] = 255
				pccr[hop1][hop0][rmax][8] = hop0  + int(h8[hop1][hop0]) 
				if (pccr[hop1][hop0][rmax][8] > 255):
					pccr[hop1][hop0][rmax][8] = 255
	return pccr	

def getImageData(filename):

	im = Image.open(filename)
	width = im.size[0]
	height = im.size[1]
	npix = im.size[0] * im.size[1] # Total number of pixels in the image

	return width, height, npix


#********************************************************************
#	Function RGBtoYUV: This converts three lists (red, blue, green) #
#   in their equivalent YUV lists.                                  #
#	Input: r [], g [], b []                                         #
#	Output: y [], cr [], cb []                                      #
#********************************************************************
def RGBtoYUV(r, g, b): # in (0,255) range

	y = [0] * len(r) # All of them have the same length
	cb = [0] * len(r) 
	cr = [0] * len(r)

	# This is just the formula to get YUV from RGB.
	for i in range(0, len(r)): 		
		y[i] = int(0.299 * r[i] + 0.587 * g[i] + 0.114 * b[i])
		cb[i] = int(128 - 0.168736 * r[i] - 0.331364 * g[i] + 0.5 * b[i])
		cr[i] = int(128 + 0.5 * r[i] - 0.418688 * g[i] - 0.081312 * b[i])

	return y, cb, cr

#******************************************************************************
#	Function getYUV: This gets the YUV lists from a given file. First,        #
#	it gets the RGB lists from the image, converts them to YUV and            #
#	decimates the chrominance ones based on the YUV mode given.               #
#	Input: file, YUV mode (it can be 444 (4:4:4), 422 (4:2:2) or 420 (4:2:0)) #
#	Output: y [], cr [], cb []                                                #
#******************************************************************************
def getRGB(filename, npix):

	im = Image.open(filename)
	rgb_im = im.convert('RGB')

	r = [-1] * npix 
	g = [-1] * npix
	b = [-1] * npix

	for y in range(0, im.size[1]):
		for x in range(0, im.size[0]):

			rpix, gpix, bpix = rgb_im.getpixel((x,y)) # We get the RGB value in each pixel and save each component in an array
			r[im.size[0]*y + x] = rpix
			g[im.size[0]*y + x] = gpix
			b[im.size[0]*y + x] = bpix

	return r, g, b

#********************************************************************************
#	Function getHops: This gets a specific hop list given the YUV ones. The hop #
#   value results on a kind of average between the previous hop and the         #
#	upper-right hop, unless the analyzed pixel doesnt have both of them.        #
#	Input: y [], cr [], cb [], component hops we want in return                 #
#	(it can be "y", "cr" or "cb")                                               #
#	Output: component hops []                                                   #
#********************************************************************************
def getHops(y, cb, cr, component, filename, mode):
	
	max_hop1 = 10 # Hop1 interval 4..10
	min_hop1 = 4 # Minimum value of Hop1
	start_hop1 = (max_hop1+min_hop1)/2	# We start in the middle of the interval and we'll go up or down, depending on the values we find.
	

	hop1 = start_hop1
	hop0 = 0 # Predicted luminance signal
	hop_number = 4 # Pre-selected hop. 4 is NULL HOP
	oc = 0 # Original color
	pix = 0 # Pixel possition, from 0 to image size        
	last_small_hop = "false" # indicates if last hop is small. Used for h1 adaptation mechanism
	rmax = 25 
	
	im = Image.open(filename)
	npix = im.size[0] * im.size[1] # Total number of pixels in the image

	if (mode == 0 and component != "y"): # Depending on the mode we are, the length of the list this method returns changes.
		hops = [-1] * int(npix/4) 
		result = [-1] * int(npix/4) # 1 chrominance for 4 values in 4:2:0
	elif (mode == 1 and component != "y"):
		hops = [-1] * int(npix/2)
		result = [-1] * int(npix/2) # 1 chrominance for 2 values in 4:2:2
	else:
		hops = [-1] * npix
		result = [-1] * npix # 1 chrominance for each value in 4:4:4

	pccr = initHopsCache() # Initializes the hops cache

	h = 0 # Vertical counter
	x = 0 # Horizontal counter
	k = 0 # Original color counter

	if (mode != 2 and component != "y"): # If we are in mode 4:2:2 or 4:2:0, we need to check every 2 pixels, so width is reduced to its half.
		width = im.size[0]/2
	else:
		width = im.size[0] # Otherwise, we go normal

	while (h < im.size[1]): # Image height
		while (x < im.size[0]): # Image width

			# original image luminances are in the array y
			# chrominance signals are stored in cb and cr
			if (component == "y"):
				oc = y[k]
			try:
				if (component == "cr"):
					oc = cr[k]
				elif (component == "cb"):
					oc = cb[k]
			except:
				break # Sometimes we'll get images with an odd number of horizontal pixels, so we need this to avoid errors.

			# prediction of signal (hop0) , based on pixel's coordinates
			if (h > 0 and x > 0 and x != im.size[0] - 1 and x != im.size[0]):
				hop0 = (4*result[pix-1]+3*result[pix + 1 - width])/7 # If we are not in a border, we need the previous pixel and the upper-right one.

			elif (x == 0 and h > 0):
				hop0 = result[pix- width] # If we are in the beginning of a row, we reset Hop1
				last_small_hop = "false" 
				hop1 = start_hop1 

			elif ((x == im.size[0]-1 or x == im.size[0]) and h > 0): 
				hop0 = (4*result[pix-1]+2*result[pix- width])/6 # If we are in the end of a row, we need the previous pixel and the upper one.

			elif (h == 0 and x > 0):
				hop0 = result[pix-1] # If we are in the first row, hop (value from 0 to 256) will be the result of the previous pixel

			elif (x == 0 and h == 0):
				hop0 = oc # First pixel is always perfectly predicted 	

			# HOPS COMPUTATION #
			# Error initial values 
			emin = 256 # Current minimum prediction error 
			e2 = 0 # Computed error for each hop 
			finbuc = 0 # We can optimize the code below with this

			# positive hops computation
			if (oc-hop0 >= 0): 
				for j in range (4, 9):
					e2 = oc - pccr[hop1][hop0][rmax][j]
					if (e2 < 0): 
						e2=-e2
						finbuc = 1
					if (e2 < emin): # We can optimize this
						hop_number = j
						emin = e2
						if (finbuc == 1): # This avoids an useless iteration
							break
					else:
						break

			#negative hops computation
			else:
				for j in range(4, -1, -1):
					e2 = pccr[hop1][hop0][rmax][j] - oc  
					if (e2 < 0): 
						e2=-e2
						finbuc = 1 
					if (e2 < emin): 
						hop_number = j 
						emin = e2
						if (finbuc == 1):
							break
					else:
						break 

			# Assignment of final color value
			try:
				result[pix] = pccr[hop1][hop0][25][hop_number] # Final luminance/chrominance
				hops[pix] = hop_number  # Final hop value
			except:
				break

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

			if (mode != 2 and component != "y"): # If we are in 4:2:2 or 4:2:0 and working with chrominance lists...
				x = x + 2 # We check every 2 pixels
				if (mode == 0 and (x == im.size[0] or x == im.size[0] - 1)):
					k = k + im.size[0] + 2 # If we are in 4:2:0, we need to check EVERY 2 ROWS
				else:
					k = k + 2 # If we are in 4:2:2, we need to check EACH ROW
			else:
				x = x + 1 # Otherwise, we go normal
				k = k + 1

		x = 0 # This resets the horizontal counter

		if (mode == 0 and component != "y"): # If we are in 4:2:0, we check every 2 rows, so we add 2
			h = h + 2
		else:
			h = h + 1 # Otherwise, we go normal

	return hops, result