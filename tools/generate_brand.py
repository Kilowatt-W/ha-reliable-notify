"""Deterministically render HA / Marketplace brand icons from source SVG."""
from pathlib import Path
import cairosvg

root=Path(__file__).resolve().parents[1]/"custom_components"/"reliable_notify"/"brand"
source=(root/"icon.svg").read_bytes()
for name,size in (("icon.png",256),("icon@2x.png",512),
                  ("dark_icon.png",256),("dark_icon@2x.png",512)):
    cairosvg.svg2png(bytestring=source,write_to=str(root/name),
                     output_width=size,output_height=size)

logo=(root/"logo.svg").read_bytes()
for name,size in (("logo.png",512),("logo@2x.png",1024),
                  ("dark_logo.png",512),("dark_logo@2x.png",1024)):
    cairosvg.svg2png(bytestring=logo,write_to=str(root/name),
                     output_width=size,output_height=round(size*320/1024))
print("Brand PNG assets generated.")
