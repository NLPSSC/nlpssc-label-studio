# flake8: noqa: E501

# Checklist for installing label-studio
# - [ ] Make sure uv is installed and available in the PATH
# - [ ] invoke `uv pip install .[tasks]`
# - [ ] call `invoke setup`


from invoke.tasks import task
import os
import glob


@task
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
