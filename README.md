# ToulMap  

*ToulMap* è un piccolo software per realizzare mappe argomentative secondo il modello di Stephen Toulmin.

## Interfaccia

<img width="1163" height="691" alt="image" src="https://github.com/user-attachments/assets/ae1a19a7-ea22-4555-8a1d-d0d20dd1bd3a" />

## Il modello di Toulmin

Stephen Toulmin (1922-2009) propose in *The Uses of Argument* (1958) un modello
per analizzare la struttura logica degli argomenti, alternativo alla sillogistica
classica e piu' vicino al ragionamento ordinario. Il modello articola ogni
argomento in sei componenti:

| Componente | Descrizione |
|---|---|
| **Tesi** (*Claim*) | L'affermazione che si vuole sostenere |
| **Dati** (*Data/Grounds*) | I fatti o le prove su cui si basa l'argomento |
| **Garanzia** (*Warrant*) | Il principio generale che collega dati e tesi |
| **Sostegno** (*Backing*) | Le ragioni che legittimano la garanzia |
| **Qualificatore** (*Qualifier*) | Il grado di certezza della tesi |
| **Confutazione** (*Rebuttal*) | Le eccezioni o condizioni di inapplicabilita' |

---

## Funzionalità

- Inserimento interattivo dei sei componenti con aggiornamento in tempo reale
- Titolo personalizzabile per ogni mappa
- Esportazione in **PNG**, **HTML** e **PDF**
- Salvataggio e riapertura dei progetti in formato **JSON**
- Interfaccia in italiano

---

## Installazione

### Metodo 1 - Installer Windows (consigliato)

1. Vai alla sezione [Releases](../../releases) di questo repository
2. Scarica `ToulMap_Setup_vX.X.exe`
3. Avvia il file e segui il wizard di installazione

Non e' necessario installare Python o altre dipendenze.

### Metodo 2 - Versione portatile

1. Vai alla sezione [Releases](../../releases)
2. Scarica `ToulMap_portable_vX.X.zip`
3. Estrai la cartella e lancia `ToulMap.exe`

Funziona da qualsiasi cartella, anche da una chiavetta USB.

### Metodo 3 - Da sorgente (richiede Python)

```bash
# Clona il repository
git clone https://github.com/antonio-vigilante/toulmap.git
cd toulmap

# Installa le dipendenze
pip install PyQt5 reportlab

# Avvia il programma
python toulmap.py
```

---

## Build da sorgente (Windows)

Per ricreare l'installer a partire dal codice sorgente sono necessari:

- Python 3.10 o superiore
- [Inno Setup 6](https://jrsoftware.org/isinfo.php)

Poi lancia:

```
.\build_windows.bat
```

Lo script installa automaticamente le dipendenze Python, compila l'eseguibile
con PyInstaller e genera il file di installazione con Inno Setup.

---

## Licenza

ToulMap e' software libero, rilasciato con licenza
[GNU General Public License v3.0](LICENSE).

---

## Autore

**Antonio Vigilante**  
[antonio-vigilante.github.io/toulmap](https://antonio-vigilante.github.io/toulmap)
