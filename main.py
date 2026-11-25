#!/usr/bin/env python3
"""Entry program for make.fun's news-image-20261125 bounty.

The repository holds entry.png: one cover-style image summing up the world
news of Wednesday 25 November 2026 -- one dominant visual (the CIA and the
Office of the Director of National Intelligence hit by a cyberattack,
reported 25 November) plus two supporting stories (a Houthi drone hits
Riyadh's tallest tower, 11 wounded; the WHO evacuates Ebola staff from a
hospital in DR Congo). This program copies the image to the output
directory. Standard library only; no network, no clock, no randomness,
so two runs always write the same bytes.
"""

import binascii
import os
import struct
import sys

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
MAX_BYTES = 1048576
EXPECT_W = 1024
EXPECT_H = 1024


def fail(message):
    sys.stderr.write("news image: %s\n" % message)
    sys.exit(1)


def verify_png(buf):
    """Fail unless buf is a 1024x1024 PNG under the 1 MiB cap."""
    if len(buf) < 33 or buf[:8] != PNG_SIGNATURE:
        fail("entry.png is not a PNG file")
    if buf[12:16] != b"IHDR":
        fail("entry.png has no IHDR chunk")
    width, height = struct.unpack(">II", buf[16:24])
    if (width, height) != (EXPECT_W, EXPECT_H):
        fail("entry.png is %dx%d, expected 1024x1024" % (width, height))
    if len(buf) > MAX_BYTES:
        fail("entry.png is %d bytes, over the 1 MiB limit" % len(buf))
    # Walk every chunk: each must fit inside the file, carry a valid CRC,
    # and the file must end with IEND, so the image is whole.
    pos = 8
    seen_iend = False
    while pos + 8 <= len(buf):
        (length,) = struct.unpack(">I", buf[pos:pos + 4])
        ctype = buf[pos + 4:pos + 8]
        end = pos + 12 + length
        if end > len(buf):
            fail("entry.png chunk %r runs past the end of the file" % ctype)
        (crc,) = struct.unpack(">I", buf[end - 4:end])
        if binascii.crc32(buf[pos + 4:end - 4]) & 0xFFFFFFFF != crc:
            fail("entry.png chunk %r has a bad CRC" % ctype)
        pos = end
        if ctype == b"IEND":
            seen_iend = True
            break
    if not seen_iend or pos != len(buf):
        fail("entry.png does not end with a whole IEND chunk")


def option(name, fallback):
    """Read a --name value from argv, or use the fallback."""
    flag = "--%s" % name
    if flag in sys.argv:
        at = sys.argv.index(flag)
        if at + 1 < len(sys.argv):
            return sys.argv[at + 1]
    joined = "--%s=" % name
    for arg in sys.argv:
        if arg.startswith(joined):
            return arg[len(joined):]
    return fallback


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    source = os.path.join(here, "entry.png")
    if not os.path.exists(source):
        fail("entry.png is missing from the repository")
    with open(source, "rb") as fh:
        buf = fh.read()
    verify_png(buf)

    out_dir = option("output", os.environ.get("MAKEFUN_OUTPUT_DIR", "/output"))
    os.makedirs(out_dir, exist_ok=True)
    target = os.path.join(out_dir, "entry.png")
    with open(target, "wb") as fh:
        fh.write(buf)
    # Confirm the copy landed whole: the grader reads exactly these bytes.
    if os.path.getsize(target) != len(buf):
        fail("entry.png copy is incomplete")
    sys.stdout.write("news image: wrote %s (%d bytes)\n" % (target, len(buf)))


if __name__ == "__main__":
    main()
