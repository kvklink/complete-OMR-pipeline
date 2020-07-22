"""
@file hough_lines.py
@brief This program demonstrates line finding with the Hough transform
"""
import sys
import math
import cv2 as cv
import numpy as np
import matplotlib.pyplot as plt

DIR = 'images/sheets/mscd-15/' #trombone/'
INPUT_PATH = DIR + 'input.png'
OUTPUT_PATH = DIR + 'deskew-hough.png'

def main():    
    filename = INPUT_PATH
    src = cv.imread(cv.samples.findFile(filename), cv.IMREAD_GRAYSCALE)
    # Check if image is loaded fine
    if src is None:
        print ('Error opening image!')
        return -1
    imshow("Source", src)

    # Edge detection
    # TODO
    dst = cv.Canny(src, 50, 200, None, 3)
    imshow("Edge detection", dst)

    # Copy edges to the images that will display the results in BGR
    cdst = cv.cvtColor(dst, cv.COLOR_GRAY2BGR)
    cdstP = np.copy(cdst)
    
    # Standard Hough
    res_rho = 1                 # 1 pixel
    res_theta = np.pi / 180     # 1 degree
    threshold = 250 #150
    lines = cv.HoughLines(dst, res_rho, res_theta, threshold, None, 0, 0)
    
    if lines is not None:
        for i in range(0, len(lines)):
            rho = lines[i][0][0]
            theta = lines[i][0][1]
            a = math.cos(theta)
            b = math.sin(theta)
            x0 = a * rho
            y0 = b * rho
            pt1 = (int(x0 + 1000*(-b)), int(y0 + 1000*(a)))
            pt2 = (int(x0 - 1000*(-b)), int(y0 - 1000*(a)))
            cv.line(cdst, pt1, pt2, (0,0,255), thickness=1, lineType=cv.LINE_AA)
    
    # Probabalistic Hough
    pthreshold = 100 #20 #50
    min_len = 500 #100 #50 #100 #50
    max_gap = 50 #10
    linesP = cv.HoughLinesP(dst, res_rho, res_theta, pthreshold, None, min_len, max_gap)
    
    if linesP is not None:
        for i in range(0, len(linesP)):
            l = linesP[i][0]
            cv.line(cdstP, (l[0], l[1]), (l[2], l[3]), (0,0,255), thickness=1, lineType=cv.LINE_AA)
    
    
    imshow("Detected Lines (in red) - Standard Hough Line Transform", cdst)
    imshow("Detected Lines (in red) - Probabilistic Line Transform", cdstP)
    cv.imwrite(OUTPUT_PATH, cdstP)
    
    cv.waitKey()
    return 0
    
def imshow(title, image):
    plt.imshow(image)
    plt.title(title)
    plt.show()
    return

if __name__ == "__main__":
    main()