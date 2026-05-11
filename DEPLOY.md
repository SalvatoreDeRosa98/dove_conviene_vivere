# Deploy su Streamlit Community Cloud

Guida completa per portare l'app online in ~10 minuti, gratis.

---

## 1. Crea il repository GitHub

```bash
# Nella cartella del progetto
cd /Users/salvatorederosa/Desktop/calcolatore

git init
git add .
git commit -m "feat: prima versione — dove conviene vivere con il mio stipendio"

# Crea un repo su github.com (tasto "New repository")
# Nome suggerito: dove-conviene-vivere
# Visibilità: Public (necessario per il piano free di Streamlit Cloud)

git remote add origin https://github.com/TUO_USERNAME/dove-conviene-vivere.git
git branch -M main
git push -u origin main
```

---

## 2. Collega Streamlit Community Cloud

1. Vai su **[share.streamlit.io](https://share.streamlit.io)** e accedi con GitHub
2. Clicca **"New app"**
3. Compila il form:
   - **Repository**: `TUO_USERNAME/dove-conviene-vivere`
   - **Branch**: `main`
   - **Main file path**: `fase5_streamlit.py`
4. Clicca **"Deploy!"**

Streamlit installerà automaticamente i pacchetti da `requirements.txt` e darà un URL del tipo:  
`https://dove-conviene-vivere-XXXX.streamlit.app`

---

## 3. Aggiornamenti futuri

Ogni `git push` su `main` aggiorna l'app in automatico:

```bash
git add .
git commit -m "fix: descrizione della modifica"
git push
```

---

## Note

- Il piano **Community (free)** è sufficiente per un portfolio: l'app "dorme" dopo 7 giorni di inattività ma si riattiva al primo accesso.
- Non servono segreti o API key: l'app usa solo dati locali e tile OpenStreetMap pubbliche.
- Se vuoi un dominio personalizzato, puoi usare il piano **Teams** oppure un redirect da un dominio che già possiedi.
