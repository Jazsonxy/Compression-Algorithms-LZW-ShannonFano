import os
from flask import Flask, request, render_template, send_from_directory, url_for
from werkzeug.utils import secure_filename
import lzw_compression
import shannon_fano_compression
import fitz  # PyMuPDF for PDF handling
from docx import Document  # for DOCX handling

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 30 * 1024 * 1024  # 30 MB

if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

# Function to read the uploaded file based on its extension
def read_uploaded_file(file_path, file_ext):
    if file_ext == '.pdf':
        return lzw_compression.read_pdf(file_path)
    elif file_ext == '.docx':
        return lzw_compression.read_docx(file_path)
    else:
        return lzw_compression.read_file(file_path)

# Function to decompress using Shannon-Fano
def decompress_shannon_fano(compressed_text, codes):
    return shannon_fano_compression.decompress_text(compressed_text, codes)

@app.route('/')
def upload_form():
    return render_template('upload.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files or request.files['file'].filename == '':
        return 'No file part' if 'file' not in request.files else 'No selected file', 400

    file = request.files['file']
    filename = secure_filename(file.filename)
    file_ext = os.path.splitext(filename)[1].lower()
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(file_path)
    
    try:
        user_input = read_uploaded_file(file_path, file_ext)
        original_size = os.path.getsize(file_path) * 8  # in bits

        # LZW Compression
        lzw_binary_output = lzw_compression.encoding(user_input)
        lzw_compressed_size = len(lzw_binary_output)  # in bits
        lzw_binary_representation = ' '.join([lzw_binary_output[i:i+8] for i in range(0, len(lzw_binary_output), 8)])
        lzw_compression_ratio = 100 - (lzw_compressed_size / original_size * 100)
        lzw_redundancy = (original_size - lzw_compressed_size) / original_size
        lzw_dictionary = lzw_compression.get_lzw_dictionary()
        lzw_compressed_path = os.path.join(app.config['UPLOAD_FOLDER'], f'lzw_{filename}')
        with open(lzw_compressed_path, 'wb') as f:
            f.write(bytearray(int(lzw_binary_output[i:i+8], 2) for i in range(0, len(lzw_binary_output), 8)))

        # Shannon-Fano Compression
        frequencies = shannon_fano_compression.calculate_frequencies(user_input)
        shannon_fano_codes = shannon_fano_compression.create_shannon_fano_codes(frequencies)
        shannon_fano_compressed_text = shannon_fano_compression.compress_text(user_input, shannon_fano_codes)
        shannon_fano_compressed_size = len(shannon_fano_compressed_text)  # in bits
        shannon_fano_binary_representation = ' '.join([shannon_fano_compressed_text[i:i+8] for i in range(0, len(shannon_fano_compressed_text), 8)])
        shannon_fano_compression_ratio = 100 - (shannon_fano_compressed_size / original_size * 100)
        shannon_fano_redundancy = (original_size - shannon_fano_compressed_size) / original_size
        shannon_fano_compressed_path = os.path.join(app.config['UPLOAD_FOLDER'], f'sf_{filename}')
        with open(shannon_fano_compressed_path, 'wb') as f:
            f.write(bytearray(int(shannon_fano_compressed_text[i:i+8], 2) for i in range(0, len(shannon_fano_compressed_text), 8)))

        # Decompress to verify
        lzw_decompressed_output = lzw_compression.decoding(lzw_binary_output)
        shannon_fano_decompressed_output = decompress_shannon_fano(shannon_fano_compressed_text, shannon_fano_codes)

        # Save decompressed files
        lzw_decompressed_path = os.path.join(app.config['UPLOAD_FOLDER'], f'lzw_decompressed_{filename}')
        shannon_fano_decompressed_path = os.path.join(app.config['UPLOAD_FOLDER'], f'sf_decompressed_{filename}')
        with open(lzw_decompressed_path, 'wb') as f:
            f.write(lzw_decompressed_output.encode('latin1'))
        with open(shannon_fano_decompressed_path, 'wb') as f:
            f.write(shannon_fano_decompressed_output.encode('latin1'))

        file_info = {
            'filename': filename,
            'original_size': original_size,
            'lzw_compressed_size': lzw_compressed_size,
            'shannon_fano_compressed_size': shannon_fano_compressed_size,
            'lzw_compression_ratio': lzw_compression_ratio,
            'shannon_fano_compression_ratio': shannon_fano_compression_ratio,
            'lzw_redundancy': lzw_redundancy,
            'shannon_fano_redundancy': shannon_fano_redundancy,
            'content_display': user_input[:500],  # Display first 500 characters
        }

        return render_template('result.html', file_info=file_info,
                               lzw_download=url_for('download_file', filename=f'lzw_{filename}'),
                               shannon_fano_download=url_for('download_file', filename=f'sf_{filename}'),
                               lzw_decompressed_download=url_for('download_file', filename=f'lzw_decompressed_{filename}'),
                               shannon_fano_decompressed_download=url_for('download_file', filename=f'sf_decompressed_{filename}'),
                               lzw_binary_representation=lzw_binary_representation,
                               lzw_dictionary=lzw_dictionary,
                               shannon_fano_binary_representation=shannon_fano_binary_representation,
                               shannon_fano_codes=shannon_fano_codes)
    
    except Exception as e:
        return f'Error processing file: {e}', 500

    finally:
        os.remove(file_path)

@app.route('/download/<filename>')
def download_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
