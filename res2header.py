#!/usr/bin/env python

import random
import string
import struct
import binascii
import argparse


xor_key = b'\xcc'

USAGE_TMPL = b'''
#include "%(header)s"

...

for(int i = 0; i < %(reslen_name)s; i++)
{
    %(res_name)s[i] = %(res_name)s[i] ^ %(key_name)s;
}
'''

HEADER_TMPL = b'''
#define %(key_name)s '%(xor_key)s'
#define %(reslen_name)s %(res_len)d

static unsigned char %(res_name)s[] = {
%(resource)s
};

'''

def res2header(res_file, header_file, xor_key):
    xor_data = b""
    with open(res_file, "rb") as rr:
        data = rr.read()
        for d in data:
            xor_data += struct.pack("B", (d if isinstance(d, int) else ord(d)) ^ ord(xor_key))

    i = 0
    fmt = []

    for d in xor_data:
        fmt.append(str(d if isinstance(d, int) else ord(d)))

    res_name = "RES_" + ''.join(random.sample(string.ascii_uppercase, 4))
    res_name = res_name.encode()

    res = {
        b"res_name": res_name,
        b"reslen_name": res_name + b"_LEN",
        b"key_name": res_name + b"_KEY",
        b"resource": (", ".join(fmt)).encode(),
        b"header": header_file.encode(),
        b"xor_key": b"\\x%s" % binascii.hexlify(xor_key),
        b"res_len": len(xor_data)
    }

    header = HEADER_TMPL % res

    with open(header_file, "wb") as wh:
        wh.write(header)

    return res


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Convert resource to C/CXX header.")
    parser.add_argument('resource', help="Resource file as input.")
    parser.add_argument('header', help="Header file as output.")
    args = parser.parse_args()

    res = res2header(args.resource, args.header, xor_key)
    usage = USAGE_TMPL % res

    print("Success! Usage: \n" + usage.decode())
