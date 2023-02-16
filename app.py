from flask import Flask, request, jsonify, Response, render_template, redirect, flash, url_for
from werkzeug.middleware.proxy_fix import ProxyFix
from werkzeug.utils import secure_filename
import sqlite3 
import uuid

BASE_PATH = "/pb"
RUN_HOST = "localhost"
RUN_PORT = "24407"
APP_DB = "app.db"

LANGS = [
        "markup", "html", "xml", "svg", "mathml", "ssml", "atom", "rss", "css", "clike", "javascript", 
        "abap", "abnf", "actionscript", "ada", "agda", "al", "antlr4", "apacheconf", "apl", "applescript", "aql", "arduino", "arff", "asciidoc", "aspnet", "asm6502", "autohotkey", "autoit", 
        "shell", "basic", "batch", "shortcode", "bison", "bnf", "brainfuck", "brightscript", "bro", "oscript", 
        "c", "csharp", "dotnet", "cpp", "cil", "clojure", "cmake", "coffeescript", "concurnas", "csp", "crystal", "css-extras", "cypher", 
        "d", "dart", "dax", "dhall", "diff", "django", "jinja2", "dns-zone", "dockerfile", 
        "ebnf", "editorconfig", "eiffel", "ejs", "eta", "elixir", "elm", "etlua", "erb", "erlang", "excel-formula", 
        "fsharp", "factor", "firestore-security-rules", "flow", "fortran", "ftl", 
        "gml", "gcode", "gdscript", "gedcom", "gherkin", "git", "glsl", "go", "graphql", "groovy", 
        "haml", "handlears", "haskell", "haxe", "hcl", "hlsl", "http", "hpkp", "hsts", 
        "ichigojam", "icon", "ignore", "gitignore", "hgignore", "npmignore", "inform7", "ini", "io", 
        "j", "java", "javadoc", "javadoclike", "javastacktrace", "jolie", "jq", "jsdoc", "js-extras", "json", "webmanifest", "json5", "jsonp", "jsstacktrace", "js-templates", "julia", 
        "keyman", "kotlin",  
        "latex", "tex", "latte", "less", "lilypond", "liquid", "lisp", "emacs-lisp", "livescript", "llvm", "lolcode", "lua", 
        "makefile", "markdown", "markup-templating", "matlab", "mel", "mizar", "mongodb", "monkey", "moonscript", 
        "n1ql", "n4js", "nand2tetris-hdl", "naniscript", "nasm", "neon", "nginx", "nim", "nix", "nsis", "none", 
        "objectivec", "ocaml", "opencl", "oz", 
        "parigp", "parser", "pascal", "pascaligo", "pcaxis", "peoplecode", "perl", "php", "phpdoc", "php-extras", "plsql", "powerquery", "powershell", "processing", "prolog", "properties", "protobuf", "pug", "puppet", "pure", "purebasic", "purescript", "python", 
        "q", "qml", "qore", 
        "r", "racket", "jsx", "tsx", "reason", "regex", "renpy", "rest", "rip", "roboconf", "robotframework", "ruby", "rust", 
        "sas", "sass", "scss", "scala", "scheme", "shell-session", "smali", "smalltalk", "smarty", "solidity", "solution-file", "soy", "sparql", "splunk-spl", "sqf", "sql", "stan", "iecst", "stylus", "swift", 
        "t4-templating", "t4-cs", "t4", "t4-vb", "tap", "tcl", "tt2", "textile", "toml", "turtle", "twig", "typescript", "typoscript", 
        "unrealscript", 
        "vala", "vbnet", "velocity", "verilog", "vhdl", "vim", "visual-basic",
        "warpscript", "wasm", "wiki", 
        "xeora", "xml-doc", "xojo", "xquery", 
        "yaml", "yang", 
        "zig"
        ]

#utility function
def fix_werkzeug_logging():
    from werkzeug.serving import WSGIRequestHandler

    def address_string(self):
        forwarded_for = self.headers.get(
            'X-Forwarded-For', '').split(',')

        if forwarded_for and forwarded_for[0]:
            return forwarded_for[0]
        else:
            return self.client_address[0]

    WSGIRequestHandler.address_string = address_string

app = Flask(__name__, static_url_path=f"{BASE_PATH}/static")
app.secret_key = b'=xR\\\x86\xb0\x9d{\x02/e5\xc4\xeb\xfcD'
app.wsgi_app = ProxyFix(app.wsgi_app)
app.config["JSON_AS_ASCII"] = False
app.config["JSON_SORT_KEYS"] = False
app.config["JSONIFY_PRETTYPRINT_REGULAR"] = True

@app.route(f"{BASE_PATH}/new")
def new():
    return render_template("new.html", langs=sorted(LANGS))

@app.route(f"{BASE_PATH}/create", methods = ["POST"])
def create():
    value = request.form["value"]
    name = request.form["name"].strip()
    lang = request.form["lang"]
    if lang not in LANGS:
        lang = "none"
    token = str(uuid.uuid4())
    if len(value) > 131072:
        flash("Paste too long")
        return redirect(url_for("new"))
    if len(name) > 128:
        flash("Paste name too long")
        return redirect(url_for("new"))
    if name == "":
        flash("Paste name cannot be empty")
        return redirect(url_for("new"))
    if value == "":
        flash("Paste cannot be empty")
        return redirect(url_for("new"))
    with sqlite3.connect(APP_DB) as db:
        cursor = db.cursor()
        result = cursor.execute("INSERT INTO data (name, value, token, lang) VALUES (?, ?, ?, ?)", (name, value, token, lang))
    return redirect(url_for("view", token = token))

@app.route(f"{BASE_PATH}/view/<token>")
def view(token):
    with sqlite3.connect(APP_DB) as db:
        cursor = db.cursor()
        result = cursor.execute("SELECT name, value, lang FROM data WHERE token = ?", (token,))
        try:
            name, value, lang = list(result)[0]
        except:
            return "invalid token", 404
    return render_template("view.html", name = name, lang = lang, value = value, token = token)

@app.route(f"{BASE_PATH}/download/<token>")
def send(token):
    with sqlite3.connect(APP_DB) as db:
        cursor = db.cursor()
        result = cursor.execute("SELECT name, value FROM data WHERE token = ?", (token,))
        try:
            name, value = list(result)[0]
        except:
            return "invalid token", 404
    name = secure_filename(name)
    resp = Response(value, mimetype="application/octet-stream")
    resp.headers["Content-Disposition"] = f"""attachment; filename="{name}" """
    return resp

fix_werkzeug_logging()

if __name__ == "__main__":
    app.run(host = RUN_HOST, port = RUN_PORT)

