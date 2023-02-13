#!/usr/bin/python3.9
# This is a simple script simulating an executable of a software with file input and output.
#
import sys
import time
import os
import random


if __name__ == "__main__":
    if len(sys.argv) >= 3:
        input_file_full_path = sys.argv[1]
        output_field_full_path = sys.argv[2]
        if os.path.exists(input_file_full_path):
            # for some 'computational' time
            sl = random.randint(4, 10)
            print(sl)
            time.sleep(sl)

            # read the input value from input file
            f = open(input_file_full_path, 'r')
            val = float(f.readline())
            f.close()

            # calculate the result
            res = val*2
            print("result = %f" % res)

            # write it to output file
            f = open(output_field_full_path, 'w')
            f.write("%f" % res)
            f.close()
        else:
            print("The input file does not exist.")
            exit(1)
    else:
        print("Number of arguments does not fit. (%d)" % len(sys.argv))
        exit(1)
    exit(0)
