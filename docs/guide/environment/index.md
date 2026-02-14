# Environment

Since `hikari` runs on modern, non-deprecated versions of Python, we first need to set up a proper development environment. This guide walks you through installing Python, `hikari`, and a suitable code editor.

## Installing Python

It is strongly recommended to install the **latest stable version of Python**, as it includes performance improvements, bug fixes, and new language features.

=== "Windows"

    1. Visit Python's [official download page](https://www.python.org/downloads/)
    2. Select the latest release and scroll down to the **Files** section
        ![Python Files](../../assets/guide/environment/3.10.11-files.png "Python Files")
    3. Download the **Windows installer (XX-bit)**
        - Windows 11 is always **64-bit**
        - Older versions may support both 32-bit and 64-bit
    4. Run the installer and **leave all default options enabled**
        - Ensure **Add Python to PATH** is checked
        - Ensure **pip** is selected for installation
    5. Verify Python's installation:
        ```powershell
        python --version
        ```

        ![Verify Python](../../assets/guide/environment/verify-python.png "Verify Python")
    6. Verify `pip`'s installation:
        ```powershell
        pip --version
        ```

        ![Verify pip](../../assets/guide/environment/verify-pip.png "Verify pip")

        If `pip` is not recognized, reinstall Python and make sure the **pip** option is **enabled**.

=== "macOS"

    1. Visit Python's [official download page](https://www.python.org/downloads/)
    2. Download the **macOS installer**.
        ![Python Files](../../assets/guide/environment/3.10.11-files.png "Python Files")
    3. Run the installer and leave all default options enabled.
    4. Verify Python's installation:
        ```bash
        python3 --version
        ```

        ![Verify Python](../../assets/guide/environment/verify-python.png "Verify Python")
    5. Verify `pip`'s installation;
        ```bash
        pip3 --version
        ```

        ![Verify pip](../../assets/guide/environment/verify-pip.png "Verify pip")

=== "Linux"

    Python is typically preinstalled on most Linux distributions

    **Debian / Ubuntu**

    ```bash
    sudo apt update
    sudo apt install -y python3 python3-pip
    ```

    **Arch Linux**

    ```bash
    sudo pacman -S python python-pip
    ```

    **Fedora**

    ```bash
    sudo dnf install python3 python3-pip
    ```

    Verify installation:

    ```bash
    python3 --version
    pip3 --version
    ```

## Installing hikari

Once Python and `pip` are installed, installing `hikari` is straightforward

=== "Windows"

    ```powershell
    pip install hikari
    ```

=== "macOS"

    ```bash
    pip3 install hikari
    ```

=== "Linux"

    ```bash
    pip3 install hikari
    ```

Verify installation:

```
python -c "import hikari; print(hikari.__version__)"
```

## Installing an IDE

An **IDE (Integrated Development Environment)** is where you will write and manage your code.

While any editor will work, **Visual Studio Code** or **PyCharm** is recommended for their simplicity, speed, and excellent Python tooling.

| Editor | Documented |
|--------|------------|
| [Visual Studio Code](https://code.visualstudio.com/Download) | [Yes](visual-studio-code.md) |
| [JetBrains PyCharm](https://www.jetbrains.com/pycharm/download)  | No |
| [Sublime Text](https://www.sublimetext.com/download) | No |

Once your IDE is installed, continue to [Program](../program/index.md)
