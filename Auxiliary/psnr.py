"""

This module calculates the Peak Signal to Noise Ratio (PSNR) of a codified image.

"""
# LHE Codec
# Author: Eduardo Rodes Pastor

import math

# ----------------#
# PSNR CALCULATOR #
# ----------------#

#*******************************************************************************#
#   Function getHops: This calculates the Peak Signal to Noise Ratio (PSNR) of  #
#   the codified image, comparing it to the original one.                       #
#   Input: predicted luminance array, original luminance array and number of    #
#   pixels                                                                      #
#   Output: None, just prints the PSNR                                          #
#*******************************************************************************#

def calculatePSNR(y_pred, y, npix):
        """Prints the PSNR of the image luminance lists given.

        It compares the predicted luminance list with the original one and gets
        the total error between them.

        Parameters: predicted luminance (integer list with values from 0 to 255), 
        original luminance (integer list with values from 0 to 255), number of 
        pixels of the image (integer)

        Exceptions: This function does not throw an exception.

        """
        total_y = 0 # Summatory of squared errors

        for i in range(0, len(y)): 
                
                dif_y = y_pred[i] - y[i] # Simple error between predicted and original luminance

                total_y = total_y + pow(dif_y, 2) # We add its square to the summatory
                         
        meanSquaredError = float(total_y) / float(npix) # And we get the mean squared error per pixel
        
        if (meanSquaredError != 0):
                peakSignalToNoiseRatio = float(10 * math.log(255 * 255 / meanSquaredError, 10)) # We use 255*255 because we're using 8 bits for every luminance value
                print "Peak Signal to Noise Ratio (PSNR) = ", round(peakSignalToNoiseRatio, 2), " dB"
        else:
                print "Peak Signal to Noise Ratio (PSNR) = 0 dB" # Ideal case