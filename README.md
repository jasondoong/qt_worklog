# qt_worklog

A PySide6 application skeleton.

## Environment Setup

### Ubuntu

1.  **Install Python 3.12 and Poetry:**

    ```bash
    sudo apt-get update
    sudo apt-get install python3.12 python3.12-venv python3-pip
    curl -sSL https://install.python-poetry.org | python3 -
    ```

2.  **Install Qt dependencies:**

    ```bash
    sudo apt-get install -y libxkbcommon-x11-0 libxcb-icccm4 libxcb-image0 libxcb-keysyms1 libxcb-randr0 libxcb-render-util0 libxcb-xinerama0 libxcb-xfixes0 libxcb-shape0 libxcb-cursor0
    ```

### Running the application

```bash
poetry install
poetry run qt-worklog
```
