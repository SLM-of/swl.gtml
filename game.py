import os
import sys
import webbrowser

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QTextEdit, QMessageBox, QFileDialog,
    QPushButton, QVBoxLayout, QWidget, QMenuBar, QMenu
)
from PySide6.QtGui import QAction, QFont


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
                style.append(f"font-size:{p if 'px' in p else p + 'px'}")
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


class SMLStudio(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🌐 SML Studio - by Suriel")

        self.text_edit = QTextEdit()
        self.text_edit.setFont(QFont("Courier New", 11))

        generate_button = QPushButton("▶️ Générer la page web")
        generate_button.clicked.connect(self.generer_page)

        layout = QVBoxLayout()
        layout.addWidget(self.text_edit)
        layout.addWidget(generate_button)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        self._create_menu()

    def _create_menu(self):
        menu_bar = QMenuBar(self)
        self.setMenuBar(menu_bar)

        fichier_menu = QMenu("Fichier", self)
        menu_bar.addMenu(fichier_menu)

        nouveau_action = QAction("🆕 Nouveau projet", self)
        nouveau_action.triggered.connect(self.nouveau_projet)

        ouvrir_action = QAction("📂 Ouvrir projet...", self)
        ouvrir_action.triggered.connect(self.ouvrir_projet)

        sauvegarder_action = QAction("💾 Sauvegarder projet...", self)
        sauvegarder_action.triggered.connect(self.sauvegarder_projet)

        fichier_menu.addAction(nouveau_action)
        fichier_menu.addAction(ouvrir_action)
        fichier_menu.addAction(sauvegarder_action)

    def nouveau_projet(self):
        reply = QMessageBox.question(self, "❗ Confirmation", "Créer un nouveau projet effacera le contenu actuel. Continuer ?")
        if reply == QMessageBox.Yes:
            self.text_edit.clear()

    def ouvrir_projet(self):
        chemin, _ = QFileDialog.getOpenFileName(self, "Ouvrir un fichier SML", "", "Fichiers SML (*.sml);;Tous les fichiers (*)")
        if chemin:
            with open(chemin, "r", encoding="utf-8") as f:
                self.text_edit.setText(f.read())

    def sauvegarder_projet(self):
        chemin, _ = QFileDialog.getSaveFileName(self, "Sauvegarder le projet", "", "Fichiers SML (*.sml);;Tous les fichiers (*)")
        if chemin:
            with open(chemin, "w", encoding="utf-8") as f:
                f.write(self.text_edit.toPlainText())
            QMessageBox.information(self, "💾 Sauvegarde", "Projet sauvegardé avec succès.")

    def generer_page(self):
        code = self.text_edit.toPlainText()
        html = parse_sml(code)
        chemin = os.path.abspath("page_sml.html")
        with open(chemin, "w", encoding="utf-8") as f:
            f.write(html)
        try:
            webbrowser.get("windows-default").open(chemin)
        except:
            webbrowser.open(chemin)
        QMessageBox.information(self, "✅ Succès", "Page générée et ouverte dans le navigateur.")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    studio = SMLStudio()
    studio.resize(900, 600)
    studio.show()
    sys.exit(app.exec())
