# LHE Codec
# Author: Eduardo Rodes Pastor

import huff, math, struct, os
from PIL import Image
from array import *
from numpy import zeros

# --------------#
# IMAGE DECODER #
# --------------#

#*********************************************************************************************#
#	Function initHopsCache: # Initializes pre-computed hop values.                            #
#   This is a cache of ratio ("r") to avoid pow functions                                     #
#	We will compute cache ratio for different rmax values, although we will use               #
#	finally only rmax=25 (which means 2.5f). This function is generic and experimental        #
#	and this is the cause to compute more things than needed.                                 #
#	Given a certain h1 value and h0 luminance, the "luminance hop" of hop "i" is stored		  #
# 	in hn[absolute h1 value][luminance of h0 value]											  #
#																							  #
#	For example,  h4 (null hop) is always 0, h1 is always hop1 (from 4 to 10), h2 is hop1*r,  #
#	but this is just the hop. The final luminance of h2 is luminance=(luminance of h0)+hop1*r # 
#   																						  #
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
				ratios[1][hop1][hop0][rmax] = pow(percent_range * (hop0)/(hop1), 0.3333333) 	
				
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
				h2[hop1][hop0] =hop1 * ratio_neg 
				h1[hop1][hop0] = h2[hop1][hop0] * ratio_neg 
				h0[hop1][hop0] = h1[hop1][hop0] * ratio_neg 
			
				# Final color component (luminance or chrominance). depends on hop1
				# from most negative hop (cache[hop1][hop0][0]) to most possitive hop (cache[hop1][hop0][8])
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


#*******************************************************************************#
#	Function symbolsToHops: Given a list of symbols, this returns a list of the #
#	hops they represent. We will use a list of lists called distribution which  #
#	will work as a cache, since two symbols mean different hops based on their  #
#	upper symbol. 																#
#	Input: Symbols list, output image width, component symbols we want and 		#
#	chrminance mode												                #
#	(it can be "y", "cr" or "cb"), chrominance mode and total number of pixels  #
#	Output: List of component hops                                              #
#*******************************************************************************#

def symbolsToHops(sym_list, width, component, mode): 

	sym_list = ['11111111' if e == 'X' else str(e) for e in sym_list]
	sym_list = ''.join(sym_list) # We get all the symbols in a big string

	hops = [0] * len(sym_list)

	distribution = [[4, 0, 5, 3, 6, 2, 7, 1, 8], # If upper hop = 0, symbol 1 is 4, symbol 2 is 0 (up) and so on
					[4, 1, 5, 3, 6, 2, 7, 8, 0], # ...
					[4, 2, 5, 3, 6, 7, 1, 8, 0], 
					[4, 3, 5, 6, 2, 7, 1, 8, 0], 
					[4, 5, 3, 6, 2, 7, 1, 8, 0], # Distribution of hops if upper hop equals 1 or doesnt exist
					[4, 5, 3, 6, 2, 7, 1, 8, 0], # If upper hop = 5, we get the same list as before
					[4, 6, 5, 3, 2, 7, 1, 8, 0], # If upper hop = 6, symbol 1 is 4, symbol 2 is 6 (up) and so on.						
					[4, 7, 5, 3, 6, 2, 1, 8, 0], # ...
					[4, 8, 5, 3, 6, 2, 7, 1, 0]]

	# Hop calculation
	for i in range(0, len(sym_list)):

		# If symbol is 1, hop will always be 4.
		if (sym_list[i] == '1'):
			hops[i] = 4
			continue

		# If we are in the first row, upper symbol doesnt exist and we use distribution[4] (or [5])
		elif (i <= width-1):
			hops[i] = distribution[5][int(sym_list[i])-1]
			continue

		# If upper symbol is not 2, we get the cache (distribution) value
		elif (sym_list[i] != '2'):
			hops[i] = distribution [int(hops[i-width])] [int(sym_list[i])-1]
			continue

		# If upper hop is not 4, we check the upper hop of it, until we get a
		# different hop or we reach the first row
		else:
			if (hops[i-width] != 4):

				try:
					hops[i] = hops[i-width]

				# If upper hop doesnt exist, we use distribution[4] (or [5])
				except:
					hops[i] = distribution[5][int(sym_list[i])-1]

			# If symbol is 2 and upper symbol is 1, hop is always 5
			else:
				hops[i] = 5
			continue

	return hops


#*******************************************************************************#
#	Function hopsToYUV: This gets a specific YUV list given its hops list.      #
#   This method is similar to GetHops in LHEquantizer, since it's its inverse   #
#   function.    															    #
#	Input: component hops list, original color of the first pixel, width and 	#
#   height of the resulting image, component YUV we want in return. 			#
#	chrominance mode 												            #
#	(it can be "y", "cr" or "cb"), chrominance mode and total number of pixels  #
#	Output: component hops []                                                   #
#*******************************************************************************#

def hopsToYUV(hops, oc, width, height, component, mode):
	
	# Hop1 interval: [4,10]
	max_hop1 = 10
	min_hop1 = 4

	# We start in the center of the interval
	start_hop1 = (max_hop1+min_hop1)/2 
	hop1 = start_hop1

	hop0 = 0 # Predicted luminance signal
	hop_number = 4 # Pre-selected hop -> 4 is null hop
	oc = 0 # Original color
	pix = 0 # Pixel possition, from 0 to image size        
	last_small_hop = "false" # indicates if last hop is small. Used for h1 adaptation mechanism
	rmax = 25 # Ratio used in LHE

	npix = width * height # Total number of pixels in the image
	result = [-1] * npix  # List where we will save the YUV component values

	cache = initHopsCache()	# Initializing hops cache

	x = 0 # Horizontal counter
	h = 0 # Vertical counter

	# If we are in mode 4:2:2 or 4:2:0, we need to check every 2 pixels, so width 
	# is reduced to its half.
	if (mode != 2 and component != "y"): 
		width_adj = width/2
	else:
		width_adj = width # Otherwise, we go normal

	while (h < height): # Output image height
		while (x < width): # Output image width

			try:
				hop_number = hops[pix]
			except:
				break # This prevents unwanted exceptions when using 4:2:2 and 4:2:0

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

			# Assignment of final value
			result[pix] = cache[int(hop1)][int(hop0)][rmax][hop_number] # Final luminance/chrominance
			
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

			# If we are in 4:2:2 or 4:2:0, we need to check every 2 pixels in a row.
			if (mode != 2 and component != "y"): 
				x = x + 2
			else:
				x = x + 1 # Otherwise, we go normal

		x = 0 # This resets the horizontal counter

		# If we are in 4:2:0, we need to check pixels every 2 rows.
		if (mode == 0 and component != "y"): 
			h = h + 2
		else:
			h = h + 1 # Otherwise, we go normal

	# We give the result list a more readable format
	for i in range(0, len(result)):
		result[i] = int(result[i]) 

	# Here, we will duplicate values of the chrominance lists if we are in 4:2:2 or 4:2:0, 
	# so they will have the same length as the luminance list.
	if (mode != 2 and component != "y"):
		result = [x for x in result if x != -1] # We remove all non-used slots in the list
		result = [x for x in result for _ in (0, 1)] # We duplicate every element, so we get the same chrominance in 2 consecutive elements.
		
		if (mode == 0):
			i = 0 # Reseting i
			len_res = 2*len(result) # Remember len(result) is half the value of the luminance list length

			# This whole bucle copies every line of values in the image to the row below, so we get a 4:2:0 mode.
			while (i < len_res):

				# We get a new line
				result_width = result[i:i+width] 
				i = i + width

				# We insert that lane in a new one below the original
				for j in range(0, width): 
					result.insert(i, result_width[j])
					i = i + 1

	return result 

def YUVtoRGB(y, cb, cr):

	r = [0] * len(y)
	g = [0] * len(y)
	b = [0] * len(y)
	result = [0] * len(y)

	for i in range(0, len(y)):
		r[i] = int(y[i] + 1.4075 * (cr[i]-128))
		g[i] = int(y[i] - .3455 * (cb[i]-128) - .7169 * (cr[i]-128))
		b[i] = int(y[i] + 1.779 * (cb[i]-128))
		result[i] = (r[i], g[i], b[i])

	return r, g, b, result

def RGBtoBMP(rgb, size):
	im = Image.new('RGB', size)
	im.putdata(rgb)

	im.save("output_lhe/images/output-image.bmp", 'BMP')