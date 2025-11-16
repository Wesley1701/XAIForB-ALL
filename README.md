# Capstone Project Group 3
- Boy Stroo (1061576)
- Niels Poldervaart (1006334)
- Quinn Rachman (1009001)
- Rick van Alphen (1006306)
- Wesley Zwaal (1026606)

## Dev Container:
### Requirements (Docker + Devcontainer):
[Dev Containers Extension](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers)

### Quick Start:
- Clone repo
```
git clone https://github.com/Wesley1701/XAIForB-ALL.git
cd XAIForB-All
```
- Open Project in VS Code
- Reopen in Dev Container
  - Press `F1` (or `Cmd+Shift+P` / `Ctrl+Shift+P`)
  - Type `Dev Containers: Reopen in Container`
  - Wait while VS Code builds the container (first time only - Can take a few minutes)
  - You're now inside the dev container, extensions are installed inside the container so you probably miss some of your personal extensions

## Download Datasets
- Download Breast Cancer Dataset (Project: TCGA-BRCA):
  - Run `download_gdc_files.py` by using this command: `python3 download_gdc_files.py ./REQUIRED/manifest.txt ./data/tsv`

> [!CAUTION]
> Might need to run the download commands again if there are missing files.

## Combine GDC files into dataset
### Convert ALL .tsv files to .pq file
- Open `gdc_to_pq.ipynb`
- Run All code blocks
- Wait until code finishes

## Run Workflow
- Open `main_notebook.ipynb`
- Run All code blocks

> [!IMPORTANT]
> Make sure that the dataset `.pq` files are inside the `./data/`