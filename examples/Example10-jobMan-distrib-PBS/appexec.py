# This is a simple script simulating an executable of a software with file input and output.
#
import sys
import time
import os


if __name__ == "__main__":
    # for some 'computational' time
    time.sleep(3.)

    if len(sys.argv) >= 3:
        inpfile = sys.argv[1]
        outfile = sys.argv[2]
        print("input file = %s" % inpfile)
        print("output file = %s" % outfile)
        if os.path.exists(inpfile):

            # read the input value from input file
            f = open(inpfile, 'r')
            val = float(f.readline())
            f.close()

            # calculate the result
            res = val*val*val
            print("result = %f" % res)

            # write it to output file
            f = open(outfile, 'w')
            f.write("%f" % res)
            f.close()
