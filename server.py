import importlib
import os
import sys
import datetime
import signal
import socket
import mimetypes
import zipfile
from flask import Flask, request, send_file, jsonify
from werkzeug.utils import secure_filename
from gevent.pywsgi import WSGIServer
from colorama import Fore, Style

required_modules = ['flask', 'gevent', 'colorama']

# Fungsi untuk memeriksa dan mengunduh modul yang diperlukan
def check_and_install_modules():
    for module_name in required_modules:
        try:
            importlib.import_module(module_name)
        except ImportError:
            print(f"Module '{module_name}' not found. Installing...")
            os.system(f"pip install {module_name}")
            importlib.reload(sys.modules.get(module_name))
        except Exception as e:
            print(f"An error occurred while importing module '{module_name}': {str(e)}")
            sys.exit(1)

check_and_install_modules()  # Memeriksa dan mengunduh modul yang diperlukan sebelum menjalankan aplikasi

# Kode lainnya

app = Flask("gretongrs")
port = None
app.access_history = []
http_server = None

def find_available_port():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    port = 8080
    while True:
        try:
            s.bind(('localhost', port))
            break
        except OSError:
            port += 1
    s.close()
    return port

@app.before_request
def log_request():
    method = request.method
    original_url = request.url
    headers = request.headers
    client_ip_address = headers.get('X-Forwarded-For', request.remote_addr)
    user_agent = headers.get('User-Agent')
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # Warna untuk setiap elemen
    color_timestamp = Fore.CYAN
    color_method = Fore.GREEN if method == 'GET' else Fore.RESET
    color_url = Fore.BLUE
    color_client_ip = Fore.YELLOW
    color_user_agent = Fore.MAGENTA

    # Format log
    access_log = f"{color_client_ip}{client_ip_address}{Style.RESET_ALL} - - {color_timestamp}[{timestamp}] {color_method}\"{method} {color_url}{original_url} HTTP/1.1\"{Style.RESET_ALL} 200 131 0.048935"

    app.access_history.append(access_log)
    print(f"{Style.BRIGHT}{Fore.WHITE}{access_log}{Style.RESET_ALL}")

    # Garis pemisah untuk setiap blok log
    print(f"{Fore.WHITE}{'-' * 80}{Style.RESET_ALL}")


    # Menyimpan log ke file log.txt
    with open('log.txt', 'a') as log_file:
        log_file.write(access_log + '\n')

def send_file_from_zip(zip_file, path):
    password = b'12345'  # Mengubah password menjadi bytes

    with zipfile.ZipFile(zip_file, 'r') as z:
        try:
            file_data = z.read(path, pwd=password)
            return file_data
        except KeyError:
            return f"File '{path}' not found in the zip."

def is_valid_file(path):
    with zipfile.ZipFile('gretongrs.zip', 'r') as z:
        return path in z.namelist()

def get_file_mimetype(path):
    mime_type, _ = mimetypes.guess_type(path)
    return mime_type

@app.route('/')
def home():
    client_ip_address = request.headers.get('X-Forwarded-For', request.remote_addr)
    print(f"Client IP address: {client_ip_address}")

    return send_file_from_zip('gretongrs.zip', 'page/home.html')

@app.route('/access-history')
def access_history():
    return jsonify(app.access_history)

@app.route('/<path:path>')
def serve_file(path):
    if not is_valid_file(path):
        return "File not found."

    file_data = send_file_from_zip('gretongrs.zip', path)
    if file_data.startswith(b'PK'):  # Menyaring file zip
        return "File not found."

    mime_type = get_file_mimetype(path)
    response = app.make_response(file_data)
    response.headers.set('Content-Type', mime_type)
    return response

def stop_server(signal, frame):
    global http_server
    if http_server is not None:
        http_server.stop()
        print(f"{Fore.GREEN}Server stopped{Style.RESET_ALL}")
    sys.exit(0)

if __name__ == '__main__':
    port = find_available_port()
    signal.signal(signal.SIGINT, stop_server)
    signal.signal(signal.SIGTERM, stop_server)
    http_server = WSGIServer(("0.0.0.0", port), app)
    print(f"{Fore.GREEN}Server running on {Fore.BLUE}http://localhost:{port}{Style.RESET_ALL}")
    print(f"{Fore.GREEN}Server running on {Fore.BLUE}http://{socket.gethostbyname(socket.gethostname())}:{port}{Style.RESET_ALL}")

    if 'RENDER' in os.environ:
        http_server.serve_forever()
    else:
        http_server.serve_forever()

    # Buka URL setelah server berjalan
    if sys.platform == 'darwin':
        subprocess.run(["open", f"http://localhost:{port}"])
    elif sys.platform.startswith('linux'):
        if os.environ.get('DESKTOP_SESSION') == 'gnome':
            subprocess.run(["xdg-open", f"http://localhost:{port}"])
        elif os.environ.get('DESKTOP_SESSION') == 'kde':
            subprocess.run(["kde-open", f"http://localhost:{port}"])
    elif sys.platform == 'win32':
        subprocess.run(["start", f"http://localhost:{port}"])
    elif 'android' in sys.platform:
        subprocess.run(["termux-open-url", f"http://localhost:{port}"])

