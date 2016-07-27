# LHE Codec
# Author: Eduardo Rodes Pastor

import huff, math, struct, os
from PIL import Image
from array import *

# ---------------#
# BINARY DECODER #
# ---------------#


#*****************************************************************************#
#	Function getData: This reads some data from the .lhe file header. Since   #
#	we know the size each number has, we can identify where 4 bytes will be   #
#	needed.                                                                   #
#	Input: .lhe file                                                          #
#	Output: Data, in order: chrominance mode, image width, image height,      #
#	first pixel luminance value, first pixel chrominances values, length of   #
#	codified luminance so we can know where chrominance starts                #
#*****************************************************************************#

def getData(lhe_file):

	fp = open(lhe_file, "rb")
	data = fp.read()

	i = 0 # Value to seek
	k = 0 # Position of the list where we will write a specific data

	# We need 10 slots: lhe type, mode, width, height, 2 for number of blocks, 3 for first values of pixels and 1 for the codified luminance length
	header = [0] * 10  
	while (i <= 18): # The file header has a size of 19 bytes

		# We get a position in the file header
		fp.seek(i)

		# If this position is not 2, 6 or 15 (not width, height or codified luminance length, that data size is 1 byte
		if (i != 2 and i != 6 and i != 15):
			data = fp.read(1) # We read 1 byte
			unpacked_data = struct.unpack("B", data)[0] # 'B' is for 1 byte
			header[k] = unpacked_data # We save it in the final list
			k = k + 1 # Next position in the list to save the following value
			i = i + 1 # Seek 1 byte forward

		# Otherwise, we need 4 bytes for the value. This is the same as before:
		else:
			data = fp.read(4)
			unpacked_data = struct.unpack("I", data)[0] # 'I' is for 4 bytes
			header[k] = unpacked_data
			k = k + 1
			i = i + 4

	# We return the values we need in this decoder
	return header[1], header[2], header[3], header[6], header[7], header[8], header[9]


#*****************************************************************************#
#	Function getSymbolsLists: This returns the luminance and chrominance list #
#	of symbols given a .lhe file. It also detects the 'X' value in every      #
#	moment if the dynamic coder is enabled, otherwise writes eight '1'        #
#	symbols per 'X'.                                                          #
#	Input: .lhe file, number of pixels of the image, length of codified       #
#	luminance and chrominance mode.                                           #
#	Output: Three symbols lists: luminance and both chrominances.             #
#*****************************************************************************#

def getSymbolsLists(lhe_file, npix, lum_len, mode):
	
	# This list will always have the number of pixels as length
	y_sym = [0] * npix

	# We discard the header and we get 2 files with the Huffman codified luminance and chrominance
	with open(lhe_file, "rb", 0) as fp:
		fp.seek(19)
		data_lum = fp.read(lum_len)
		data_chrom = fp.read()
	fp.close()

	fp = open("output_lhe/out-huffman_lum.lhe", "wb")
	fp.write(data_lum)
	fp.close()
	fp = open("output_lhe/out-huffman_chrom.lhe", "wb")
	fp.write(data_chrom)
	fp.close()

	# We decode with Huffman both files
	dec = huff.Decoder("output_lhe/out-huffman_lum.lhe")
	dec.decode_as("output_lhe/out-lum.lhe")

	dec = huff.Decoder("output_lhe/out-huffman_chrom.lhe")
	dec.decode_as("output_lhe/out-chrom.lhe")

	# And we get the symbols of each file
	f = open("output_lhe/out-lum.lhe", "rb")
	lum_sym = f.read()
	f.close()
	f = open("output_lhe/out-chrom.lhe", "rb")
	chrom_sym = f.read()
	f.close()

	# We apply the pertinent changes to the 'X' symbol
	# Remember it means a variable or fixed group of '1' symbols
	lum_sym = [w.replace('X', '11111111') for w in lum_sym]
	chrom_sym = [w.replace('X', '11111111') for w in chrom_sym]
	lum_sym = ''.join(lum_sym)
	chrom_sym = ''.join(chrom_sym)

	# We save luminance final symbols
	for i in range(0, npix):
		y_sym[i] = lum_sym[i]

	# If we are in 4:4:4, all lists have the same length, the number of pixels
	# If we are in 4:2:2, chrominance lists have their length halved
	# If we are in 4:2:0, luminance list is 4 times longer than chrominance ones
	if (mode == 0):
		npix = int(npix/4)
	elif (mode == 1):
		npix = int(npix/2)

	# We assign the right length to chrominance lists
	cb_sym = [0] * npix
	cr_sym = [0] * npix 

	# We save both chrominance final symbols
	for i in range(0, npix):
			cb_sym[i] = chrom_sym[i]
			cr_sym[i] = chrom_sym[npix+i]

	# We delete the files we dont want anymore.
	os.remove("output_lhe/out-huffman_lum.lhe")
	os.remove("output_lhe/out-huffman_chrom.lhe")
	os.remove("output_lhe/out-lum.lhe")
	os.remove("output_lhe/out-chrom.lhe")

	return y_sym, cb_sym, cr_sym