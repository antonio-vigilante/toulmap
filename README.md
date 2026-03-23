# ToulMap — Istruzioni per la distribuzione Windows

## Struttura dei file

```
toulmin_map.py          ← il programma principale
toulmap.spec            ← configurazione PyInstaller
toulmap_installer.iss   ← script Inno Setup per l'installer
build_windows.bat       ← script automatico (fa tutto lui)
```

---

## Metodo rapido (consigliato)

1. Metti tutti i file nella stessa cartella
2. Apri il Prompt dei comandi in quella cartella
3. Lancia:
   ```
   build_windows.bat
   ```
   Lo script installa le dipendenze, compila l'eseguibile e (se Inno Setup
   è presente) crea anche il file di installazione.

---

## Metodo manuale — passo per passo

### Passo 1 — Installa le dipendenze

```
pip install PyQt5 reportlab pyinstaller
```

### Passo 2 — Compila l'eseguibile con PyInstaller

```
pyinstaller toulmap.spec --noconfirm
```

Al termine troverai la cartella `dist\ToulMap\` contenente `ToulMap.exe`
e tutte le librerie necessarie. Questa cartella è già autonoma e
distribuibile: basta copiarla su qualsiasi PC Windows senza installare Python.

### Passo 3 — Crea l'installer (opzionale)

Scarica e installa **Inno Setup 6** da:
https://jrsoftware.org/isinfo.php

Poi esegui:
```
iscc toulmap_installer.iss
```

Troverai il file `installer_output\ToulMap_Setup_v1.0.exe`.
Questo è il file da distribuire: l'utente lo avvia, segue il wizard e
ToulMap viene installato con icona sul desktop e voce nel menu Start.

---

## Dimensioni attese

| Artefatto | Dimensione approssimativa |
|---|---|
| Cartella `dist\ToulMap\` | ~120–160 MB |
| `ToulMap_Setup_v1.0.exe` | ~55–70 MB (compressa) |

---

## Note

- L'installer non richiede privilegi di amministratore (`PrivilegesRequired=lowest`):
  ogni utente può installarlo nella propria cartella profilo.
- Se vuoi aggiungere un'icona `.ico`, mettila nella stessa cartella,
  decommenta la riga `icon='toulmap.ico'` nel file `.spec` e la riga
  `SetupIconFile=toulmap.ico` nel file `.iss`.
- Per aggiornare la versione, modifica `#define MyAppVersion` in
  `toulmap_installer.iss` e il nome del file `.exe` si aggiornerà di conseguenza.
