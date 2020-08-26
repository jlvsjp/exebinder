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


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Bind 2 exe files.")
    parser.add_argument('primary', help="Primary exe file.")
    parser.add_argument('secondary', help="secondary exe file.")
    parser.add_argument('--uac', action="store_true", help="Enable uac.")
    parser.add_argument('--gui', action="store_true", help="Enable -mwindows CXXFLAG, works when the secondary is GUI exe file.")
    parser.add_argument('--x86', action="store_true", help="Enable -m32 CXXFLAG, when build in x64 platform.")
    parser.add_argument('--ico', type=str, help="Set bind file icon.")
    parser.add_argument('--out', type=str, default="new.exe", help="Output binded exe file.")

    args = parser.parse_args()

    cxxflag = "%s %s" % (str("-mwindows" if args.gui else ""), str("-m32" if args.x86 else ""))

    if args.ico:
        img = Image.open(args.ico)
        img.save("icon.ico")
    else:
        try:
            print("Parsing %s ico." % args.primary)
            extractor = IconExtractor(args.primary)
            extractor.export_icon("icon.ico", num=0)

        except Exception as e:
            print("Error in parsing ico: %s" % e)

    os.system("windres %s --input-format=rc -O coff -i icon.rc -o icon.res" % str("-F pe-i386" if args.x86 else ""))
    icon_flag = True if os.path.exists("icon.res") else False

    res1 = res2header(args.primary, "res1.h", chr(random.randint(0, 255)))
    res2 = res2header(args.secondary, "res2.h", chr(random.randint(0, 255)))

    with open("binder.cpp", "r") as rb:
        data = rb.read()
        data = data.replace("RES_1111", res1["res_name"])
        data = data.replace("RES_2222", res2["res_name"])

    with open("main.cpp", "w") as wm:
        wm.write(data)

    if args.uac:
        os.system("windres %s --input-format=rc -O coff -i uac.rc -o uac.res" % str("-F pe-i386" if args.x86 else ""))

    os.system("g++ %s main.cpp memory_module.c %s %s -o %s" % (cxxflag, str("uac.res" if args.uac else ""), str("icon.res" if icon_flag else ""), args.out))
    os.system("strip %s" % args.out)
    print("Bind to %s success! " % args.out)

    os.remove("res1.h")
    os.remove("res2.h")
    os.remove("main.cpp")
    try:
        os.remove("uac.res")
    except:
        pass

    try:
        os.remove("icon.ico")
        os.remove("icon.res")
    except:
        pass
