from flask import Flask, render_template_string, request, send_file
from Crypto.Cipher import AES
import io
import zipfile

app = Flask(__name__)

# Funkce pro šifrování jednotlivých souborů
def encrypt_file(file_data, password):
    key = password.encode().ljust(32)[:32]
    cipher = AES.new(key, AES.MODE_EAX)
    ciphertext, tag = cipher.encrypt_and_digest(file_data)
    return cipher.nonce + tag + ciphertext

# Funkce pro dešifrování jednotlivých souborů
def decrypt_file(file_data, password):
    key = password.encode().ljust(32)[:32]
    nonce, tag, ct = file_data[:16], file_data[16:32], file_data[32:]
    cipher = AES.new(key, AES.MODE_EAX, nonce=nonce)
    return cipher.decrypt_and_verify(ct, tag)

# Moderní HTML šablona s Tailwind CSS
HTML = '''
<!DOCTYPE html>
<html lang="cs">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <script src="https://cdn.tailwindcss.com"></script>
    <title>AES Šifrovač</title>
</head>
<body class="bg-slate-900 text-white p-4 flex justify-center min-h-screen items-start pt-10">
    <div class="max-w-md w-full bg-slate-800 p-8 rounded-3xl shadow-2xl border border-slate-700 text-center">
        
        <div class="mb-8">
            <h1 class="text-3xl font-black text-blue-500 uppercase tracking-tighter leading-none">AES Šifrovač</h1>
            <p class="text-slate-500 text-[10px] italic mt-1 uppercase tracking-widest">by Michal Juráň</p>
        </div>

        <form method="POST" enctype="multipart/form-data" class="space-y-4 text-left">
            <input type="password" name="password" placeholder="Bezpečnostní heslo" required 
                class="w-full p-4 bg-slate-700 rounded-xl outline-none border border-slate-600 focus:border-blue-500 text-center transition-all text-white placeholder-slate-500">
            
            <div class="border-2 border-dashed border-slate-600 rounded-2xl p-8 text-center hover:border-blue-500 transition-all cursor-pointer group relative">
                <input type="file" name="files" id="f" multiple class="hidden" onchange="updateList()">
                <label for="f" class="cursor-pointer block">
                    <span id="t" class="text-slate-400 group-hover:text-blue-400 transition-colors font-medium">Vyberte soubory k ochraně</span>
                </label>
            </div>
            
            <div id="l" class="text-[11px] text-slate-500 space-y-1 max-h-32 overflow-y-auto italic px-2 scrollbar-hide"></div>
            
            <div class="flex gap-3 pt-2">
                <button name="a" value="e" class="flex-1 bg-blue-600 hover:bg-blue-500 p-4 rounded-xl font-bold shadow-lg transform active:scale-95 transition-all uppercase text-xs">Zašifrovat</button>
                <button name="a" value="d" class="flex-1 bg-emerald-600 hover:bg-emerald-500 p-4 rounded-xl font-bold shadow-lg transform active:scale-95 transition-all uppercase text-xs">Dešifrovat</button>
            </div>
        </form>

        {% if e %}
        <div class="mt-4 p-3 bg-red-500/10 border border-red-500/50 rounded-lg">
            <p class="text-red-500 text-sm font-bold">{{e}}</p>
        </div>
        {% endif %}

        <div class="mt-10 pt-6 border-t border-slate-700/50">
            <p class="text-slate-500 text-[10px] mb-6 uppercase tracking-widest font-bold">Podpořte moji tvorbu</p>
            
            <div class="flex flex-col items-center gap-6">
                <div class="bg-white p-3 rounded-2xl shadow-xl w-40 h-40">
                    <img src="/static/qr.png" alt="QR Platba" class="w-full h-full" onerror="this.parentElement.innerHTML='<div class=\\'text-slate-400 text-[10px] py-12\\'>Zde bude váš QR kód</div>'">
                </div>
                <p class="text-[10px] text-slate-500 italic -mt-4 uppercase tracking-tight">Skenuj pro dar přes ČSOB / jinou banku</p>

                <div class="flex items-center gap-4 w-full opacity-30">
                    <div class="h-[1px] bg-slate-500 flex-1"></div>
                    <span class="text-[9px] font-bold">NEBO</span>
                    <div class="h-[1px] bg-slate-500 flex-1"></div>
                </div>

                <a href="https://ko-fi.com/michaljuran" target="_blank" 
                   class="inline-flex items-center gap-3 bg-[#29abe2] hover:bg-[#2088b5] text-white px-8 py-3 rounded-full font-bold text-sm shadow-lg transition-all transform hover:-translate-y-1">
                    <img src="https://ko-fi.com/img/cup-border.png" alt="Ko-fi" class="h-5">
                    Ko-fi
                </a>
            </div>
        </div>
    </div>

    <script>
    function updateList() {
        const i = document.getElementById('f'), l = document.getElementById('l'), t = document.getElementById('t');
        l.innerHTML = '';
        if (i.files.length > 0) {
            t.innerHTML = '<span class="text-blue-400 font-bold tracking-tight">📂 ' + i.files.length + ' souborů připraveno</span>';
            Array.from(i.files).forEach(f => {
                l.innerHTML += '<div class="truncate opacity-70 border-b border-slate-700/50 py-1 flex justify-between"><span>📄 ' + f.name + '</span><span class="text-[9px] opacity-50">' + (f.size/1024).toFixed(0) + 'KB</span></div>';
            });
        }
    }
    </script>
</body>
</html>
'''

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        pw = request.form.get("password")
        ac = request.form.get("a")
        files = request.files.getlist("files")
        
        if not files or files[0].filename == '': 
            return render_template_string(HTML, e="⚠️ Vyberte alespoň jeden soubor!")
        
        # Dynamický název ZIP souboru podle akce
        download_name = "AES_encrypted.zip" if ac == "e" else "AES_decrypted.zip"
        
        output = io.BytesIO()
        try:
            with zipfile.ZipFile(output, 'w') as zf:
                for f in files:
                    data = f.read()
                    if ac == "e":
                        res = encrypt_file(data, pw)
                        name = f.filename + ".aes"
                    else:
                        res = decrypt_file(data, pw)
                        name = f.filename.replace(".aes", "")
                    
                    zf.writestr(name, res)
            
            output.seek(0)
            return send_file(
                output, 
                download_name=download_name, 
                as_attachment=True
            )
        except Exception:
            return render_template_string(HTML, e="❌ CHYBA (Špatné heslo nebo poškozený soubor)")
            
    return render_template_string(HTML)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)