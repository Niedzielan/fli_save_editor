import argparse
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from hashlib import md5
from zlib import compress, decompress

def decrypt(data, key):
    cipher = AES.new(key, AES.MODE_ECB)
    decrypted = unpad(cipher.decrypt(data), 16)
    # footer is 34 bytes. u32 1, u8[16] checksum, u8[14] 0
    data_checksum = decrypted[-30:-14]
    calc_checksum = md5(decrypted[:-34]).digest()
    if data_checksum != calc_checksum:
        print("Warning: md5 checksum does not match.")
    size = int.from_bytes(decrypted[:4], byteorder='little')
    decompressed = decompress(decrypted[4:], bufsize=size)
    return decompressed

def encrypt(data, key):
    cipher = AES.new(key, AES.MODE_ECB)
    size = int.to_bytes(len(data), 4, "little")
    compressed = compress(data)
    checksum = md5(size + compressed).digest()
    footer = b'\x01\x00\x00\x00' + checksum + b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
    encrypted = cipher.encrypt(pad(size + compressed + footer, 16))
    return encrypted

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("decrypt", "encrypt"))
    parser.add_argument("input")
    parser.add_argument("output")
    parser.add_argument("--key", "-k", default='gQPZXDDr8DsT7VU9mTZwJLYa8PnruSEU', required=False, help="Optional key as ASCII string, else use default key")
    parser.add_argument("--key_hex", required=False, help="Optional key as hex string in case key is ever non-ASCII")
    args = parser.parse_args()
    if args.key_hex:
        key = bytes.fromhex(args.key_hex)
    elif args.key:
        key = args.key.encode()
    else:
        key = b'gQPZXDDr8DsT7VU9mTZwJLYa8PnruSEU'
    with open(args.input, "rb") as source:
        in_data = source.read()
    out_data = None
    if args.mode == "decrypt":
        out_data = decrypt(in_data, key)
    else:
        out_data = encrypt(in_data, key)
    if out_data != None:
        with open(args.output, "wb")  as target:
            target.write(out_data)
    
if __name__ == "__main__":
    main()
