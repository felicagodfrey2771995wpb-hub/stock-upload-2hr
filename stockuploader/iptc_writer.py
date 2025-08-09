import os
import shutil
import subprocess
from typing import List


EXIFTOOL = shutil.which("exiftool")


def write_metadata_with_exiftool(image_path: str, title: str, description: str, keywords: List[str]) -> bool:
    if not EXIFTOOL:
        return False
    args = [
        EXIFTOOL,
        "-overwrite_original",
        # IPTC
        f"-IPTC:Caption-Abstract={description}",
        f"-XMP-dc:Title={title}",
        f"-XMP-dc:Description={description}",
    ]
    # Clear existing keywords then set new ones (multiple -keywords= entries)
    args.append("-IPTC:Keywords=")
    args.append("-XMP-dc:Subject=")
    for kw in keywords:
        args.append(f"-IPTC:Keywords={kw}")
        args.append(f"-XMP-dc:Subject={kw}")
    args.append(image_path)
    try:
        subprocess.run(args, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return True
    except Exception:
        return False


def write_xmp_sidecar(image_path: str, title: str, description: str, keywords: List[str]) -> bool:
    base, _ = os.path.splitext(image_path)
    xmp_path = base + ".xmp"
    # Basic XMP packet
    kws_xml = "".join([f"<rdf:li>{_escape_xml(k)}</rdf:li>" for k in keywords])
    packet = f"""<?xpacket begin='\ufeff' id='W5M0MpCehiHzreSzNTczkc9d'?>
<x:xmpmeta xmlns:x='adobe:ns:meta/'>
  <rdf:RDF xmlns:rdf='http://www.w3.org/1999/02/22-rdf-syntax-ns#'>
    <rdf:Description xmlns:dc='http://purl.org/dc/elements/1.1/'
      xmlns:xmp='http://ns.adobe.com/xap/1.0/'>
      <dc:title><rdf:Alt><rdf:li xml:lang='x-default'>{_escape_xml(title)}</rdf:li></rdf:Alt></dc:title>
      <dc:description><rdf:Alt><rdf:li xml:lang='x-default'>{_escape_xml(description)}</rdf:li></rdf:Alt></dc:description>
      <dc:subject><rdf:Bag>{kws_xml}</rdf:Bag></dc:subject>
    </rdf:Description>
  </rdf:RDF>
</x:xmpmeta>
<?xpacket end='w'?>"""
    try:
        with open(xmp_path, "w", encoding="utf-8") as f:
            f.write(packet)
        return True
    except Exception:
        return False


def _escape_xml(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace("\"", "&quot;")
        .replace("'", "&apos;")
    )