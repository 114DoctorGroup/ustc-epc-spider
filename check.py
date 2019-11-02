import imageio
import numpy as np

'''
# extract the digit from checkcode
imgDat = imageio.imread('checkcode.png') 
for i in range(4):
    dig = imgDat[:, i * 10 : i * 10 + 10, :]
    imageio.imwrite('dig' + str(i) + '.png', dig)
'''

def Distance(dat1, dat2):
    d = np.sqrt(dat1[:, :, 0] - dat2[:, :, 0])
    d += np.sqrt(dat1[:, :, 1] - dat2[:, :, 1])
    d += np.sqrt(dat1[:, :, 2] - dat2[:, :, 2])
    return np.sum(d)

def Checkcode():
    # get the digit from Digit folder
    digit = []
    for i in range(10):
        imgDat = imageio.imread('Digit/' + str(i) + '.png')
        digit.append(imgDat)
        
    checkcode = ''
    # now start to find the right digit
    imgDat = imageio.imread('checkcode.png') 
    for i in range(4):
        # get next digit in the image
        data = imgDat[:, i * 10 : i * 10 + 10, :]
        
        # compare to the digit array and find the best match
        min_j = -1
        min_d = 0xffffffff
        for j in range(10):
            d = Distance(digit[j], data)
            if d < min_d:
                min_j = j
                min_d = d
        checkcode += str(min_j)
    
    return checkcode