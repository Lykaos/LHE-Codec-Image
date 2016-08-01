# LHE Codec
# Author: Eduardo Rodes Pastor

import Aux.huff as huff
import math, struct, os
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
#	moment, since it also is the dynamic decompressor.                        #
#	Input: .lhe file, number of pixels of the image, length of codified       #
#	luminance and chrominance mode.                                           #
#	Output: Three symbols lists: luminance and both chrominances.             #
#*****************************************************************************#

def getSymbolsLists(lhe_file, npix, lum_len, mode):

	# -- LUMINANCE AND CHROMINANCE FILES -- #

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

	# We create the lists we are going to work with
	yuvlum_sym = [0] * len(lum_sym) # Provisional luminance list
	yuvchrom_sym = [0] * (len(chrom_sym)) # provisional chrominance list
	y_sym = [0] * npix # Final luminance list
	ch_sym = [0] * 2*npix # Final chrominances list

	# -- LUMINANCE DYNAMIC DECOMPRESSOR -- #

	# We apply the pertinent changes to the 'X' symbol
	# Remember it means a variable group of '1' symbols
	x_length = 8 # Starting x_length
	in_chain = "false" # If we just got a '1', we are in a chain, so x_length doesnt decrement

	for i in range(0, len(lum_sym)):

		# If we get 'X', we change it for the correct number of '1' symbols in a row 
		if lum_sym[i] == 'X':
			in_chain = "true" # 'X' is just a group of '1'
			chain = ''.join(['1'] * x_length) # We create the '1' chain
			yuvlum_sym[i] = chain # And save it in the list
			x_length = x_length + 2 # Finally, we increase x_length for the next 'X'

		# If we get '1', we save it and decrease x_length if it's the first '1' we get
		elif (lum_sym[i] == '1'):
			yuvlum_sym[i] = '1'
			if (in_chain == "false"): # '1' after a symbol which is not 'X' or '1'
				x_length = int(math.ceil(float(x_length) / 2))
			in_chain = "true"

		# Otherwise, save the symbol and we stop being in a '1' chain
		else:
			yuvlum_sym[i] = lum_sym[i]
			in_chain = "false" 

	# Resetting variables for chrominance
	x_length = 8
	in_chain = "false"

	# -- CHROMINANCE DYNAMIC DECOMPRESSOR -- #

	# Same bucle as before, but with a separator of chrominances
	for i in range(0, len(chrom_sym)):

		if chrom_sym[i] == 'X':
			in_chain = "true"
			chain = ''.join(['1'] * x_length) 
			yuvchrom_sym[i] = chain
			x_length = x_length + 2

		elif (chrom_sym[i] == '1'):
			yuvchrom_sym[i] = '1'
			if (in_chain == "false"):
				x_length = int(math.ceil(float(x_length) / 2))
			in_chain = "true"

		# '0' is the separator, so we reset variables
		elif (chrom_sym[i] == '0'):
			yuvchrom_sym[i] = '0'
			x_length = 8
			in_chain = "false"
			continue

		else:
			yuvchrom_sym[i] = chrom_sym[i]
			in_chain = "false"

	# We join the lists so we can work with them
	yuvlum_sym = ''.join(yuvlum_sym)
	yuvchrom_sym = ''.join(yuvchrom_sym)

	# Luminance saving
	for i in range(0, len(yuvlum_sym)):
		y_sym[i] = int(yuvlum_sym[i])

	k = 0 # Position in the final list of chrominance symbols

	# Chrominance saving
	for i in range(0, len(yuvchrom_sym)):
		if (int(yuvchrom_sym[i]) != 0): # We dont save the separator
			ch_sym[k] = int(yuvchrom_sym[i])
			k = k + 1 
		else:
			continue # If we get the separator, we dont increment k

	# If we are in 4:4:4, all lists have the same length, the number of pixels
	# If we are in 4:2:2, chrominance lists have their length halved
	# If we are in 4:2:0, luminance list is 4 times longer than chrominance ones
	if (mode == 0): # 4:2:0
		npix = int(npix/4)
	elif (mode == 1): # 4:2:2
		npix = int(npix/2)

	# We assign the right length to chrominance lists
	cb_sym = [0] * npix
	cr_sym = [0] * npix 
	
	# We save both chrominance final symbols
	for i in range(0, npix):
		cb_sym[i] = ch_sym[i]
		cr_sym[i] = ch_sym[npix+i]

	# We delete the files we dont want anymore.
	os.remove("output_lhe/out-huffman_lum.lhe")
	os.remove("output_lhe/out-huffman_chrom.lhe")
	os.remove("output_lhe/out-lum.lhe")
	os.remove("output_lhe/out-chrom.lhe")

	return y_sym, cb_sym, cr_sym