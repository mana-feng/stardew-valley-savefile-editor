import os
from pathlib import Path

import PyInstaller.__main__


APP_NAME = "StardewSaveEditor"
PROJECT_ROOT = Path(__file__).resolve().parent


def _data_arg(source: str, target: str) -> str:

    return f"--add-data={source}{os.pathsep}{target}"


def build():

    os.chdir(PROJECT_ROOT)

    args = [
        "modifier/main.py",
        "--onefile",
        "--noconsole",
        f"--name={APP_NAME}",
        "--paths=modifier",
        "--icon=modifier/F.ico",
        "--clean",
        "--collect-all=ttkbootstrap",
        "--collect-all=PIL",
        _data_arg("modifier/F.png", "."),
        _data_arg("modifier/F.ico", "."),
        _data_arg("modifier/i18n", "i18n"),
        _data_arg("modifier/generated", "generated"),
        _data_arg("modifier/Installer/SMAPI/install.dat", "Installer/SMAPI"),
    ]

    print(f"Building {APP_NAME}.exe...")

    PyInstaller.__main__.run(args)

    print(f"Build completed: dist/{APP_NAME}.exe")


if __name__ == "__main__":

    build()
