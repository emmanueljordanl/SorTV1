"""RP2040 flash BIN -> UF2, per Microsoft UF2 spec. No hardware claims.

Used only for the Windows build without native picotool. Linux CI uses SDK picotool.
The BIN is produced by arm-none-eabi-objcopy from the actual linked Pico SDK ELF.
"""
import argparse
import struct
from pathlib import Path

def convert(source: Path, output: Path):
    data=source.read_bytes()
    if not 256 < len(data) <= 2*1024*1024: raise ValueError("Pico W flash image size")
    count=(len(data)+255)//256; blocks=[]
    for n in range(count):
        payload=data[n*256:(n+1)*256].ljust(256,b'\0')
        blocks.append(struct.pack('<8I',0x0A324655,0x9E5D5157,0x2000,0x10000000+n*256,256,n,count,0xE48BFF56)+payload+bytes(220)+struct.pack('<I',0x0AB16F30))
    output.write_bytes(b''.join(blocks))
    verify(output,source)

def verify(path: Path, source: Path=None):
    data=path.read_bytes()
    if not data or len(data)%512: raise ValueError("UF2 alignment")
    count=len(data)//512; payload=[]
    for n in range(count):
        block=data[n*512:(n+1)*512]; h=struct.unpack('<8I',block[:32])
        if h!=(0x0A324655,0x9E5D5157,0x2000,0x10000000+n*256,256,n,count,0xE48BFF56) or struct.unpack('<I',block[508:])[0]!=0x0AB16F30: raise ValueError("UF2 header/family/address")
        payload.append(block[32:288])
    if source:
        original=source.read_bytes()
        if b''.join(payload)[:len(original)]!=original: raise ValueError("UF2 payload mismatch")
    return count

if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('source',type=Path); p.add_argument('output',type=Path)
    a=p.parse_args(); convert(a.source,a.output); print(f"UF2 verified: {verify(a.output,a.source)} flash blocks")
