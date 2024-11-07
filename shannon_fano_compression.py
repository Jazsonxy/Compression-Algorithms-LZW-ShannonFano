# shannon_fano_compression.py
import json

def calculate_frequencies(text):
    frequencies = {}
    for char in text:
        frequencies[char] = frequencies.get(char, 0) + 1
    return frequencies

def split_characters(frequencies):
    sorted_freq = sorted(frequencies.items(), key=lambda x: x[1], reverse=True)
    middle = len(sorted_freq) // 2
    group1 = dict(sorted_freq[:middle])
    group2 = dict(sorted_freq[middle:])
    return group1, group2

def create_shannon_fano_codes(frequencies, prefix=""):
    if len(frequencies) == 1:
        char, _ = frequencies.popitem()
        return {char: prefix}
    group1, group2 = split_characters(frequencies)
    codes = {}
    codes.update(create_shannon_fano_codes(group1, prefix + "0"))
    codes.update(create_shannon_fano_codes(group2, prefix + "1"))
    return codes

def compress_text(text, codes):
    compressed_text = "".join(codes[char] for char in text)
    return compressed_text

def decompress_text(compressed_text, codes):
    reversed_codes = {v: k for k, v in codes.items()}
    decompressed_text = ""
    current_code = ""
    for bit in compressed_text:
        current_code += bit
        if current_code in reversed_codes:
            decompressed_text += reversed_codes[current_code]
            current_code = ""
    return decompressed_text

def calculate_bit_count(text):
    return len(text) * 8

def write_compressed_file(filename, compressed_text):
    with open(filename, 'w', encoding='utf-8') as file:
        file.write(compressed_text)

def write_codes_file(filename, codes):
    with open(filename, 'w', encoding='utf-8') as file:
        json.dump(codes, file)

def read_codes_file(filename):
    with open(filename, 'r', encoding='utf-8') as file:
        return json.load(file)

def write_compressed_binary_file(filename, compressed_text):
    binary_data = bytearray()
    for i in range(0, len(compressed_text), 8):
        byte = compressed_text[i:i + 8]
        if len(byte) < 8:
            byte = byte.ljust(8, '0')
        binary_data.append(int(byte, 2))
    with open(filename, 'wb') as file:
        file.write(binary_data)

def read_compressed_binary_file(filename):
    with open(filename, 'rb') as file:
        binary_data = file.read()
    compressed_text = ''.join(f'{byte:08b}' for byte in binary_data)
    return compressed_text


