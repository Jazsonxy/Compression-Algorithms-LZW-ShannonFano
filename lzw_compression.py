# lzw_compression.py
import sys
import fitz  # PyMuPDF
from docx import Document

lzw_dictionary = {}

def read_pdf(filename):
    text = ""
    with fitz.open(filename) as doc:
        for page in doc:
            text += page.get_text()
    return text

def read_docx(filename):
    doc = Document(filename)
    return "\n".join([p.text for p in doc.paragraphs])

def get_memory_size(obj, bit_per_char=8):
    if isinstance(obj, str):
        return len(obj) * bit_per_char
    return sys.getsizeof(obj) * 8

def encoding(s1):
    global lzw_dictionary
    table = {chr(i): i for i in range(256)}
    p = s1[0]
    code = 256
    output_code = []
    binary_output = ""
    lzw_dictionary.clear()
    for i in range(1, len(s1)):
        c = s1[i]
        if p + c in table:
            p += c
        else:
            binary_output += format(table[p], '09b' if table[p] >= 256 else '08b')
            lzw_dictionary[p + c] = code
            table[p + c] = code
            code += 1
            p = c
    binary_output += format(table[p], '09b' if table[p] >= 256 else '08b')
    return binary_output


def biner_ke_char(binary_output):
    # Membagi string biner menjadi kelompok 8 bit
    bytes_list = [binary_output[i:i+8] for i in range(0, len(binary_output), 8)]
    
    # Mengonversi setiap kelompok biner menjadi karakter
    char = ''.join([chr(int(byte, 2)) for byte in bytes_list])
    
    return char

def decoding(binary_data):
    table = {i: chr(i) for i in range(256)}
    output_code = []
    i = 0
    while i < len(binary_data):
        if binary_data[i] == '0':
            output_code.append(int(binary_data[i:i+8], 2))
            i += 8
        else:
            output_code.append(int(binary_data[i:i+9], 2))
            i += 9

    old = output_code[0]
    s = table[old]
    output = s
    c = s
    count = 256
    for i in range(1, len(output_code)):
        if output_code[i] in table:
            entry = table[output_code[i]]
        else:
            entry = s + c
        output += entry
        c = entry[0]
        table[count] = s + c
        count += 1
        s = entry
    return output

def read_file(filename):
    encodings = ['utf-8', 'latin-1', 'iso-8859-1']
    for enc in encodings:
        try:
            with open(filename, 'r', encoding=enc) as file:
                return file.read()
        except UnicodeDecodeError:
            continue
    # If no encoding worked, read as binary and decode
    with open(filename, 'rb') as file:
        return file.read().decode('latin-1')

def write_file(filename, data):
    with open(filename, 'w', encoding='utf-8') as file:
        file.write(data)

def write_compressed_file_binary(filename, data):
    with open(filename, 'w', encoding='utf-8') as file:
        file.write(data)

def read_compressed_file_binary(filename):
    with open(filename, 'r', encoding='utf-8') as file:
        return file.read()

def calculate_bit_count(text):
    return len(text) * 8

def get_lzw_dictionary():
    return lzw_dictionary

