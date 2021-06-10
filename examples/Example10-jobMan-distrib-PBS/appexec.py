# This is a simple script simulating an executable of a software with file input and output.
#
import sys
import time
import os


if __name__ == "__main__":
    # for some 'computational' time
    time.sleep(1.5)

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
            res = val*2
            print("result = %f" % res)

            # write it to output file
            f = open(outfile, 'w')
            f.write("%f" % res)
            f.close()
        else:
            print("The input file does not exist.")
            exit(1)
    else:
        print("Number of arguments does not fit. (%d)" % len(sys.argv))
        exit(1)
    exit(0)
