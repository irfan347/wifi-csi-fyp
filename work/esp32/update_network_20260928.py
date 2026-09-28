from pathlib import Path
import struct
import zlib

NEW_IP = b"10.202.121.192\0"
NEW_MAC = bytes.fromhex("9e1dbdf5f030")


def parse_entries(buf):
    found = []
    for page in range(0, len(buf), 4096):
        if struct.unpack_from("<I", buf, page)[0] == 0xFFFFFFFF:
            continue
        index = 0
        while index < 126:
            state = (buf[page + 32 + index // 4] >> ((index % 4) * 2)) & 3
            offset = page + 64 + index * 32
            entry = bytearray(buf[offset:offset + 32])
            if state == 2:
                assert 1 <= entry[2] <= 126 - index
                assert struct.unpack_from("<I", entry, 4)[0] == zlib.crc32(entry[:4] + entry[8:], 0xFFFFFFFF)
                found.append((offset, entry, entry[8:24].split(b"\0")[0]))
                index += entry[2]
            else:
                index += 1
    return found


for port in ("com6", "com9"):
    raw = Path(f"work/esp32/{port}-config-20260928.bin").read_bytes()
    original = raw[4096:]
    data = bytearray(original)
    entries = parse_entries(data)
    namespace = [entry[24] for _, entry, key in entries if entry[0] == 0 and key == b"csi_cfg"]
    assert len(namespace) == 1
    namespace = namespace[0]

    ip_entries = [(offset, entry) for offset, entry, key in entries if entry[0] == namespace and key == b"target_ip"]
    mac_entries = [(offset, entry) for offset, entry, key in entries if entry[0] == namespace and key == b"filter_mac" and entry[1] == 0x42]
    assert len(ip_entries) == len(mac_entries) == 1

    changed = set()
    offset, entry = ip_entries[0]
    old_length = struct.unpack_from("<H", entry, 24)[0]
    old_ip = bytes(data[offset + 32:offset + 32 + old_length])
    assert zlib.crc32(old_ip, 0xFFFFFFFF) == struct.unpack_from("<I", entry, 28)[0]
    assert len(NEW_IP) <= 32
    struct.pack_into("<H", entry, 24, len(NEW_IP))
    struct.pack_into("<I", entry, 28, zlib.crc32(NEW_IP, 0xFFFFFFFF))
    struct.pack_into("<I", entry, 4, zlib.crc32(entry[:4] + entry[8:], 0xFFFFFFFF))
    data[offset:offset + 32] = entry
    data[offset + 32:offset + 64] = NEW_IP + b"\xff" * (32 - len(NEW_IP))
    changed.update(range(offset + 4, offset + 8))
    changed.update(range(offset + 24, offset + 64))

    offset, entry = mac_entries[0]
    old_mac = bytes(data[offset + 32:offset + 38])
    assert struct.unpack_from("<H", entry, 24)[0] == 6
    assert zlib.crc32(old_mac, 0xFFFFFFFF) == struct.unpack_from("<I", entry, 28)[0]
    data[offset + 32:offset + 38] = NEW_MAC
    struct.pack_into("<I", entry, 28, zlib.crc32(NEW_MAC, 0xFFFFFFFF))
    struct.pack_into("<I", entry, 4, zlib.crc32(entry[:4] + entry[8:], 0xFFFFFFFF))
    data[offset:offset + 32] = entry
    changed.update(range(offset + 4, offset + 8))
    changed.update(range(offset + 28, offset + 38))

    assert all(a == b or index in changed for index, (a, b) in enumerate(zip(original, data)))
    Path(f"work/esp32/{port}-network-updated-20260928.bin").write_bytes(data)
    print(port, old_ip.rstrip(b"\0").decode(), "->", NEW_IP.rstrip(b"\0").decode(), old_mac.hex(":"), "->", NEW_MAC.hex(":"))
