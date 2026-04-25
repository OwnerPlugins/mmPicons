<h1 align="center">🎨 mmPicons Addon</h1>

![Visitors](https://komarev.com/ghpvc/?username=Belfagor2005&label=Repository%20Views&color=blueviolet)
[![Version](https://img.shields.io/badge/Version-1.6-blue.svg)](https://github.com/Belfagor2005/mmPicons)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Python](https://img.shields.io/badge/Python-3.x-yellow.svg)](https://python.org)
[![Python package](https://github.com/Belfagor2005/mmPicons/actions/workflows/pylint.yml/badge.svg)](https://github.com/Belfagor2005/mmPicons/actions/workflows/pylint.yml)
[![Donate](https://img.shields.io/badge/_-Donate-red.svg?logo=githubsponsors&labelColor=555555&style=for-the-badge)](https://ko-fi.com/lululla)

---

**Enigma2 project**  
For my friend **mMark** – [E2Skin Blog](https://e2skin.blogspot.com/)

<p align="center">
  <img src="/usr/lib/enigma2/python/Plugins/Extensions/mmPicons/logo.png" height="120">
</p>

---

## 📖 Overview

**mmPicons** is a lightweight panel for downloading and automatically installing **Picons and Skins** on Enigma2 receivers, based on the original artwork of **mMark**.  
The plugin lets you choose from different picon sets (transparent, black, movie‑dedicated, etc.) and skins (Zeta, OpenZeta) through a simple and intuitive interface.

---

## ✨ Key Features

- **Progress bar** – real‑time download monitoring.
- **Python 3 support** – fully compatible with modern Enigma2 images (OpenATV 7.x, OpenPLi 8.x, DreamOS, etc.).
- **Customizable destination folder** for picons (USB, HDD, internal memory).
- **Automatic folder cleanup** before new downloads.
- **Preview** of picon/skin sets before installation.
- **Built‑in update checker** – notifies you when a new plugin version is available.
- **MediaFire integration** – automatic extraction of direct download links for stable transfers.

---

## 🚀 Installation

### From repository (recommended)
```bash
wget -q "--no-check-certificate" https://raw.githubusercontent.com/Belfagor2005/mmPicons/main/installer.sh -O - | /bin/sh
```

### Manual installation
1. Download the repository ZIP.
2. Extract the `mmPicons` folder to `/usr/lib/enigma2/python/Plugins/Extensions/`.
3. Restart Enigma2.

---

## 🖥️ Usage

- Go to **Plugins** → **mmPicons** (or from the main menu → Extensions).
- Choose a category (Transparent Picons, Black Picons, Skins, etc.).
- Pick the set you like and confirm the download.
- When finished, picons will be saved to your configured folder (default: `/media/hdd/picon/`).

To change the destination folder: press **MENU** from the main plugin screen and modify the path.

---

## ⚙️ Requirements

- Enigma2 (any recent image)
- Python 3.6 or higher
- Active internet connection
- `wget` and `unzip` (pre‑installed on all images)

---

## 🙏 Credits

- **mMark** – for creating the picons and skins.
- **jbleyel** – for code improvements.
- **Lululla** – for Python 3 porting, maintenance and release.
- **MMark** – for skin design.

---

## 📝 Developer Notes

The plugin has been fully converted to **Python 3**; all dependencies on `six` and Python 2 compatibility have been removed.  
Downloads use native `urllib` with a separate thread for the progress bar, ensuring a non‑blocking GUI.  
MediaFire direct links are extracted using regex and base64 decoding.

---

## 📄 License

This project is distributed under the **GPLv3** license. See the `LICENSE` file for details.

---

<p align="center">
  <a href="https://ko-fi.com/lululla"><img src="https://ko-fi.com/img/githubbutton_sm.svg" alt="Donate"></a>
</p>
