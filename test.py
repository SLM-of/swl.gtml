import tkinter as tk
from tkinter import messagebox, filedialog
import os
import webbrowser

def extraire_texte_et_style(ligne):
    if "<style:" in ligne:
        texte = ligne.split('"')[1]
        bloc = ligne.split("<style:")[1].split(">")[0]
        props = [p.strip().lower() for p in bloc.split(";")]
        style = []
        for p in props:
            if p == "bold":
                style.append("font-weight:bold")
            elif p == "italic":
                style.append("font-style:italic")
            elif p.endswith("px") or p.isdigit():
                style.append(f"font-size:{p if 'px' in p else p+'px'}")
            elif p in ["red", "blue", "black", "green", "white"]:
                style.append(f"color:{p}")
            else:
                style.append(f"font-family:{p}")
        return texte, "; ".join(style)
    elif '"' in ligne:
        texte = ligne.split('"')[1]
        return texte, ""
    else:
        return ligne, ""

def parse_sml(texte_sml):
    html = ['<!DOCTYPE html>', '<html>']
    body = []
    theme_css = ""
    js_code = """
    <script>
    function togglePassword(id, icon) {
        const input = document.getElementById(id);
        if (input.type === "password") {
            input.type = "text";
            icon.innerText = "🙈";
        } else {
            input.type = "password";
            icon.innerText = "👁️";
        }
    }
    </script>
    """
    lignes = texte_sml.strip().splitlines()
    in_list = False
    in_box = False
    input_counter = 0

    for ligne in lignes:
        ligne = ligne.strip()
        if not ligne:
            continue

        if ligne.startswith("\\theme dark"):
            theme_css = """
            <style>
            body { background:#111; color:white; font-family:sans-serif; }
            button { background:#333; color:white; border:none; padding:10px 20px; margin:5px; cursor:pointer; }
            input { background:#222; color:white; border:1px solid #555; padding:8px; margin:6px; }
            .input-wrap { position:relative; display:inline-block; }
            .eye-btn {
                position: absolute;
                right: 10px;
                top: 50%;
                transform: translateY(-50%);
                background: transparent;
                border: none;
                color: white;
                cursor: pointer;
            }
            </style>
            """
        elif ligne.startswith("\\page"):
            continue
        elif ligne.startswith("\\title"):
            texte, style = extraire_texte_et_style(ligne)
            html.insert(1, f"<title>{texte}</title>")
            body.append(f'<h1{" style=\""+style+"\"" if style else ""}>{texte}</h1>')
        elif ligne.startswith("\\T1"):
            texte, style = extraire_texte_et_style(ligne)
            body.append(f'<h1{" style=\""+style+"\"" if style else ""}>{texte}</h1>')
        elif ligne.startswith("\\T2"):
            texte, style = extraire_texte_et_style(ligne)
            body.append(f'<h2{" style=\""+style+"\"" if style else ""}>{texte}</h2>')
        elif ligne.startswith("\\text"):
            texte, style = extraire_texte_et_style(ligne)
            body.append(f'<p{" style=\""+style+"\"" if style else ""}>{texte}</p>')
        elif ligne.startswith("\\img#"):
            try:
                contenu = ligne[5:].split("#")
                url = contenu[0].strip()
                dim = contenu[1].strip() if len(contenu) > 1 else ""
                if "x" in dim:
                    dim = dim.replace("[", "").replace("]", "").lower()
                    w, h = dim.split("x")
                    body.append(f'<img src="{url}" width="{w}" height="{h}">')
                else:
                    body.append(f'<img src="{url}">')
            except:
                body.append("<!-- image invalide -->")
        elif ligne.startswith("\\enter "):
            try:
                contenu = ligne[7:].strip()
                placeholder = contenu.split('"')[1]
                nom = "champ"
                if "[" in contenu and "]" in contenu:
                    nom = contenu.split("[")[1].split("]")[0].strip()
                input_counter += 1
                input_id = f"input{input_counter}"

                if nom.lower() == "password":
                    champ = f'''
                    <div class="input-wrap">
                        <input type="password" id="{input_id}" name="{nom}" placeholder="{placeholder}">
                        <button class="eye-btn" onclick="togglePassword('{input_id}', this)">👁️</button>
                    </div>
                    '''
                    body.append(champ)
                else:
                    body.append(f'<input type="text" name="{nom}" placeholder="{placeholder}">')
            except:
                body.append("<!-- champ invalide -->")
        elif ligne.startswith("\\box {"):
            body.append('<div style="border:1px solid #ccc;padding:10px;margin:10px 0;">')
            in_box = True
        elif ligne == "}":
            if in_list:
                body.append("</ul>")
                in_list = False
            elif in_box:
                body.append("</div>")
                in_box = False
        elif in_list:
            body.append(f"<li>{ligne}</li>")
        elif ligne.startswith("\\list {"):
            body.append("<ul>")
            in_list = True
        elif ligne.startswith("\\link#"):
            try:
                contenu = ligne[6:].split("#")
                texte = contenu[0].replace('"', '').strip()
                url = contenu[1].strip()
                body.append(f'<a href="{url}">{texte}</a>')
            except:
                body.append("<!-- lien invalide -->")
        elif ligne.startswith("<btn::"):
            try:
                texte_btn = ligne.split('"')[1]
                url = ligne.split("::*")[1].split("*")[0]
                body.append(f'<a href="{url}"><button>{texte_btn}</button></a>')
            except:
                body.append("<!-- bouton invalide -->")
        else:
            body.append(f"<p>{ligne}</p>")

    html.append("<head>")
    html.append(theme_css)
    html.append(js_code)
    html.append("</head>")
    html.append("<body>")
    html.extend(body)
    html.append("</body></html>")
    return "\n".join(html)

def generer_page():
    code = zone_code.get("1.0", tk.END)
    html = parse_sml(code)
    chemin = os.path.abspath("page_sml.html")
    with open(chemin, "w", encoding="utf-8") as f:
        f.write(html)
    try:
        webbrowser.get("windows-default").open(chemin)
    except:
        webbrowser.open(chemin)
    messagebox.showinfo("✅ Succès", "Page générée et ouverte dans le navigateur.")

def nouveau_projet():
    if messagebox.askyesno("❗ Confirmation", "Créer un nouveau projet effacera le contenu actuel. Continuer ?"):
        zone_code.delete("1.0", tk.END)

def ouvrir_projet():
    chemin = filedialog.askopenfilename(filetypes=[("Fichiers SML", "*.sml"), ("Tous les fichiers", "*.*")])
    if chemin:
        with open(chemin, "r", encoding="utf-8") as f:
            contenu = f.read()
            zone_code.delete("1.0", tk.END)
            zone_code.insert(tk.END, contenu)

def sauvegarder_projet():
    chemin = filedialog.asksaveasfilename(defaultextension=".sml", filetypes=[("Fichiers SML", "*.sml"), ("Tous les fichiers", "*.*")])
    if chemin:
        contenu = zone_code.get("1.0", tk.END)
        with open(chemin, "w", encoding="utf-8") as f:
            f.write(contenu)
        messagebox.showinfo("💾 Sauvegarde", "Projet sauvegardé avec succès.")

# Interface
fenetre = tk.Tk()
fenetre.title("🌐 SML Studio - by Suriel")

# Menu
menu_bar = tk.Menu(fenetre)
menu_fichier = tk.Menu(menu_bar, tearoff=0)
menu_fichier.add_command(label="🆕 Nouveau projet", command=nouveau_projet)
menu_fichier.add_command(label="📂 Ouvrir projet...", command=ouvrir_projet)
menu_fichier.add_command(label="💾 Sauvegarder projet...", command=sauvegarder_projet)
menu_bar.add_cascade(label="Fichier", menu=menu_fichier)
fenetre.config(menu=menu_bar)

# Éditeur
zone_code = tk.Text(fenetre, width=100, height=28, font=("Courier New", 11))
zone_code.pack(padx=10, pady=10)

# Bouton
tk.Button(fenetre, text="▶️ Générer la page web", command=generer_page).pack(pady=10)

fenetre.mainloop()
