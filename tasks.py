# flake8: noqa: E501

# Checklist for installing label-studio
# - [ ] Make sure uv is installed and available in the PATH
# - [ ] invoke `uv pip install .[tasks]`
# - [ ] call `invoke setup`


from invoke.tasks import task
import os
import glob

NODE_VERSION = "24.13.1"


def _node_is_missing(c) -> bool:
    node_missing: bool = c.run("where node", warn=True, hide=True).failed
    return node_missing


def _is_incorrect_node_version(c, node_version):
    node_version_output = c.run("node --version", hide=True).stdout.strip()
    if node_version_output.startswith("v"):
        current_version = node_version_output[1:]
    else:
        current_version = node_version_output
    versions_agree: bool = current_version != node_version
    return versions_agree


@task
def install_node(c):
    print("Checking for nvm...")
    result = c.run("where nvm", warn=True, hide=True)
    if result.failed:
        raise RuntimeError(
            "nvm is not installed or not found in PATH. Please install nvm before proceeding."
        )

    print("Checking for Node.js...")
    if _node_is_missing(c) or _is_incorrect_node_version(c, NODE_VERSION):
        print(
            f"Node.js is missing or incorrect version. Installing Node.js {NODE_VERSION} using nvm..."
        )
        c.run(f"nvm install {NODE_VERSION}")
        c.run(f"nvm use {NODE_VERSION}")
        c.run(f'echo "{NODE_VERSION}" > .nvmrc')
        c.run("npm install --global npm")  # Update npm to latest version
        c.run("npm i -g uv")
        c.run("npm i -g cross-env")
        c.run("npm i -g yarn")
    else:
        print(
            f"Node.js is already installed and correct version ({NODE_VERSION}). Skipping installation."
        )


@task(pre=[install_node])
def install_web(c):
    # can install scoop yarn with `npm install --global yarn`

    print("Installing web dependencies and building web assets...")
    os.chdir("web")
    print(f"Current directory: {os.getcwd()}")
    print("Running yarn install...")
    c.run("yarn install --frozen-lockfile")
    print("Running yarn build...")
    c.run("yarn build")


@task
def install_sqlite3_dll(c):

    dll_zip = "packages/sqlite3-dll.zip"
    dll_extracted = "packages/sqlite3-dll"
    dll_path = os.path.join(dll_extracted, "sqlite3.dll")
    copy_to_path = os.path.join(os.getcwd(), "sqlite3.dll")
    import shutil

    print("Checking for sqlite3.dll...")
    if not os.path.exists(dll_path):
        print("sqlite3.dll not found, downloading...")
        c.run(
            f"curl -L -o {dll_zip} https://www.sqlite.org/2026/sqlite-dll-win-x64-3510200.zip"
        )
        c.run(
            f'powershell -Command "Expand-Archive -Path {dll_zip} -DestinationPath {dll_extracted} -Force"'
        )
    else:
        print("sqlite3.dll already exists, skipping download.")

    print("Copying sqlite3.dll to current directory...")
    if not os.path.exists(copy_to_path):
        print("Copying sqlite3.dll...")
        shutil.copyfile(dll_path, copy_to_path)
    else:
        print("sqlite3.dll already exists in current directory, skipping copy.")


@task(pre=[install_sqlite3_dll, install_web])
def setup(c):
    # Install dependencies
    
    c.run("uv sync")

    # label-studio-sdk setup
    #   - If packages\label-studio-sdk-0b7ece0554de291d05d446ea5240e56724e384e8.zip does not exist,
    #       - combine packages\label-studio-sdk-0b7ece0554de291d05d446ea5240e56724e384e8_2.tar.00* into packages\label-studio-sdk-0b7ece0554de291d05d446ea5240e56724e384e8_2.tar
    #       - extract packages\label-studio-sdk-0b7ece0554de291d05d446ea5240e56724e384e8_2.tar
    sdk_zip = "packages/label-studio-sdk-0b7ece0554de291d05d446ea5240e56724e384e8.zip"
    sdk_tar = "packages/label-studio-sdk-0b7ece0554de291d05d446ea5240e56724e384e8_2.tar"
    sdk_tar_parts = sorted(
        glob.glob(
            "packages/label-studio-sdk-0b7ece0554de291d05d446ea5240e56724e384e8_2.tar.00*"
        )
    )
    sdk_zip_extracted = (
        "packages/label-studio-sdk-0b7ece0554de291d05d446ea5240e56724e384e8_2.zip"
    )
    sdk_dir = "packages/label-studio-sdk-0b7ece0554de291d05d446ea5240e56724e384e8/label-studio-sdk-0b7ece0554de291d05d446ea5240e56724e384e8"

    if not os.path.exists(sdk_zip):
        if not os.path.exists(sdk_tar) and sdk_tar_parts:
            # Combine tar parts
            with open(sdk_tar, "wb") as wfd:
                for part in sdk_tar_parts:
                    with open(part, "rb") as fd:
                        wfd.write(fd.read())
        if os.path.exists(sdk_tar):
            # Extract tar to get the zip
            c.run(f"tar -xf {sdk_tar} -C packages")

    #   - Unzip extract packages\label-studio-sdk-0b7ece0554de291d05d446ea5240e56724e384e8_2.zip
    if os.path.exists(sdk_zip_extracted):
        c.run(f"unzip -o {sdk_zip_extracted} -d packages")

    #   - Verify that packages\label-studio-sdk-0b7ece0554de291d05d446ea5240e56724e384e8\label-studio-sdk-0b7ece0554de291d05d446ea5240e56724e384e8 exists
    if not os.path.exists(sdk_dir):
        raise FileNotFoundError(
            f"SDK directory not found: {sdk_dir}\n"
            "Please check that the extraction steps completed successfully."
        )

    #   - uv pip install -e packages\label-studio-sdk-0b7ece0554de291d05d446ea5240e56724e384e8\label-studio-sdk-0b7ece0554de291d05d446ea5240e56724e384e8
    c.run(f"uv pip install -e {sdk_dir}")

    # install label-studio
    c.run("uv pip install -e .")

    # Build static for web???
    c.run("python label_studio/manage.py collectstatic --noinput")


@task
def setup_env_vars(c):
    # check if .venv\Scripts\activate.bat contains "set LABEL_STUDIO_ALLOW_ANONYMOUS_ACCESS=true"
    #   and if not, add "set LABEL_STUDIO_ALLOW_ANONYMOUS_ACCESS=true"
    activate_path = os.path.join(".venv", "Scripts", "activate.bat")
    deactivate_path = os.path.join(".venv", "Scripts", "deactivate.bat")

    env_var_line = "set LABEL_STUDIO_ALLOW_ANONYMOUS_ACCESS=true"
    if os.path.exists(activate_path):
        with open(activate_path, "r") as f:
            lines = f.readlines()
        if env_var_line + "\n" not in lines:
            with open(activate_path, "a") as f:
                f.write("\n" + env_var_line + "\n")
            print(f"Added environment variable to {activate_path}")
        else:
            print(f"Environment variable already set in {activate_path}")

    # check if .venv\Scripts\deactivate.bat contains "set LABEL_STUDIO_ALLOW_ANONYMOUS_ACCESS="
    #   and if not, add "set LABEL_STUDIO_ALLOW_ANONYMOUS_ACCESS="
    if os.path.exists(deactivate_path):
        with open(deactivate_path, "r") as f:
            lines = f.readlines()
        if "set LABEL_STUDIO_ALLOW_ANONYMOUS_ACCESS=" not in lines:
            with open(deactivate_path, "a") as f:
                f.write("\nset LABEL_STUDIO_ALLOW_ANONYMOUS_ACCESS=\n")
            print(f"Added environment variable to {deactivate_path}")
        else:
            print(f"Environment variable already set in {deactivate_path}")


@task
def run(c):
    c.run("label-studio")
