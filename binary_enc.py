# LHE Codec
# Author: Eduardo Rodes Pastor

import huff, math, struct, os
from PIL import Image
from array import *

# ---------------#
# BINARY ENCODER #
# ---------------#

#******************************************************************************#
#	Function getSymbols: This converts a hops list into a symbol list. We will #
#   use a cache called distribution, so we know which symbol we need based on  #
#	the upper and the actual hop. It will also include a symbol compressor; we #
#	will use a symbol 'X' which means a variable '1' (null hops) chain. If we  #
#	have the dynamic compressor enabled, 'X' will mean a different chain each  #
#	time, based on the length of '1' chains we got before.                     #
#	Input: Hops list, width, height and number of pixels of the image.         #
#	Output: Symbols list                                                       #
#******************************************************************************#

def getSymbols(hops, width, height, npix):

	sym = [0] * npix # Symbols list
	cnt = 0 # Counter for '1' chains
	lock = 0 # So we can break the bucle when mode is 4:2:2 or 4:2:0

	# Here, we will create a list of lists for every posibility of upper hop. We will use a symbol '2' which means that this
	# hop equals the upper one. If we know that the actual symbol is different than '2', we can discard the upper hop 
	# In these arrays, we will change the original one depending on the symbol which misses (is in the upper position).
	# This original distribution means that the hop 4 (null hop) will be represented with the symbol '1'. Positive hops will 
	# be represented with even symbols and negative hops with odd symbols.

	distribution = [ [9, 7, 5, 3, 1, 2, 4, 6, 8], # Original symbols distribution: Hop 0 is '9', hop 1 is '7', hop 2 is '5'...
					 [2, 8, 6, 4, 1, 3, 5, 7, 9], # Upper hop = 0 and actual hop != 0. There is no hop 0 -> Hop 1 is 8, hop 2 is 6...
					 [9, 2, 6, 4, 1, 3, 5, 7, 8], # Upper hop = 1 
					 [9, 7, 2, 4, 1, 3, 5, 6, 8], # Upper hop = 2
					 [9, 7, 5, 2, 1, 3, 4, 6, 8], # Upper hop = 3
					 [9, 7, 5, 3, 1, 2, 4, 6, 8], # If upper hop = 4 (symbol '1'), actual symbol can be '2', since it can not represent a null hop.
					 [9, 7, 5, 3, 1, 2, 4, 6, 8], # Upper hop = 5
					 [9, 7, 5, 4, 1, 3, 2, 6, 8], # Upper hop = 6
					 [9, 7, 6, 4, 1, 3, 5, 2, 8], # Upper hop = 7
					 [9, 8, 6, 4, 1, 3, 5, 7, 2] ] # Upper hop = 8

	# We will use the symbol 'X' to represent '1' chains. The length of these chains will be saved in an array
	for i in range(0, height):
		for j in range(0, width):

			k = i*width + j # This is the pixel (hop) we are analyzing.

			if (k == len(hops)):
				lock = 1
				break

			if (hops[k] == 4): # If the hop is null, write '1' or 'X' depending on how many null hops are behind this one.
				cnt = cnt + 1 # We increase the length of the chain
				if (cnt < 8): 
					sym[k] = 1 # This symbol '1' will be removed if the chain has a length >= 8
				else:
					sym[k-7] = 'X' # If chain length reaches 8, we write 'X'.
					cnt = 0
					for p in range(0, 7): 
						sym[k-p] = 0 # We clear all the symbols '1' we wrote in this chain.
				continue

			elif (i == 0): # If we are analyzing the first row, there is no upper hop, so we use the original distribution.
				sym[k] = distribution[0][hops[k]]
				if (cnt != 0): # If we get a != '1' symbol, we reset the counter and save it in an array.
					cnt = 0 # Reset 
				continue

			elif (hops[k] == hops[k-width]): # If the upper symbol equals this one (and this one is not '1'), write '2'.
				sym[k] = 2
				if (cnt != 0): # Same as before
					cnt = 0
				continue
			else: 
				# If this hop is different than the upper one, we check our distribution for the correct symbol
				sym[k] = distribution[hops[k-width]+1][hops[k]] 
				if (cnt != 0): # Same as before
					cnt = 0
				continue
		if (lock == 1):
			break

	sym = [x for x in sym if x != 0] # This removes all '0' symbols that are remaining.

	return sym, width, height


#******************************************************************************#
#	Function writeFile: This will create a .lhe file which will contain some   #
#	data for the decoder and both luminance and chrominance symbols with       #
#	Huffman coding. I know creating and deleting files can be a bit slow, but  #
#	I think it's the easiest way to understand what this method is doing.      #
#	Header will have the data used in the C codec (check readme), and that's   #
#	why we won't use a part of it here.                                        #
#	Input: Symbol lists, chrominance mode, luminance and chrominance value for #
#	first pixel, width and height of the image.                                #
#	Output: None, this just creates the file.                                  #
#******************************************************************************#

def writeFile(y_sym, cb_sym, cr_sym, mode, first_y_pixel, first_cb_pixel, first_cr_pixel, width, height): # This will write the image size and the 3 codified symbols lists in a file.

	# -- PAYLOAD -- #

	f = open("output_lhe/" + "payload_lum" + ".lhe", "wb")

	for item in y_sym: # We write the not codified luminance (y)
  		f.write(str(item))

  	f.close()

	enc = huff.Encoder("output_lhe/payload_lum.lhe") # We codify the luminance with Huffman 
	enc.write("output_lhe/huffman_lum.lhe") # We save codified luminance in a lhe file

	lum_len = os.path.getsize("output_lhe/huffman_lum.lhe") # This is the size of that file

	f = open("output_lhe/" + "payload_chrom" + ".lhe", "wb")

  	for item in cb_sym: # We write the not codified chrominance (cb)
  		f.write(str(item))
  	for item in cr_sym: # We write the not codified chrominance (cr)
  		f.write(str(item))
  	f.write('1') # This avoids a bug when we use black and white images and all symbols are 'X'
  	f.close()

	enc = huff.Encoder("output_lhe/payload_chrom.lhe") # We codify both chrominances with Huffman
	enc.write("output_lhe/huffman_chrom.lhe") # We save codified chrominances in a lhe file

	# -- HEADER -- #

	f = open("output_lhe/header.lhe", "wb")

	f.write(struct.pack("B", 0)) # We are in basic LHE, so we write a '00000000' byte.
	f.write(struct.pack("B", mode)) # YUV mode (00000000 for 4:2:0, 00000001 for 4:2:2 and 00000010 for 4:4:4)
	f.write(struct.pack("I", width)) # 4 bytes for width
	f.write(struct.pack("I", height)) # 4 bytes for height
	f.write(struct.pack("B", 1)) # We do not divide the image in blocks, so we write 1 block for height and width (00000001)
	f.write(struct.pack("B", 1))
	f.write(struct.pack("B", first_y_pixel)) # We need to save the first pixel of each list, so the decoder has a reference
	f.write(struct.pack("B", first_cb_pixel))
	f.write(struct.pack("B", first_cr_pixel))
	f.write(struct.pack("I", lum_len)) # 4 bytes for codified luminancy length. 
	f.close() # Total header length: 19 bytes.

	f = open("output_lhe/lhe_file.lhe", "wb") # This is the final lhe file

	# -- WRITING FILE -- #

	f2 = open("output_lhe/header.lhe", "rb") # Writing header
	f.write(f2.read())
	f2.close()
	f2 = open("output_lhe/huffman_lum.lhe", "rb") # Writing luminance
	f.write(f2.read())
	f2.close()
	f2 = open("output_lhe/huffman_chrom.lhe", "rb") # Writing chrominance
	f.write(f2.read())
	f2.close()
	f.close()

	# -- REMOVING OTHER FILES -- #

	os.remove("output_lhe/header.lhe")
	os.remove("output_lhe/huffman_lum.lhe")
	os.remove("output_lhe/huffman_chrom.lhe")
	os.remove("output_lhe/payload_lum.lhe")
	os.remove("output_lhe/payload_chrom.lhe")