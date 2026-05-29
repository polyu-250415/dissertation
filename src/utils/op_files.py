from pathlib import Path
import shutil


def clear_directory(target_dir, delete_subfolders: bool = False):
    """
    Clear all files inside a directory.
    Optionally delete ALL subfolders recursively.

    Args:
        target_dir: Path to the directory to clear
        delete_subfolders: If True, remove all subdirectories; if False, keep folders
    """
    # Convert to absolute safe path
    target_path = Path(target_dir).resolve()

    # Safety check: prevent deleting system root
    if target_path in (Path("/"), Path.home(), Path("C:\\"), Path("D:\\")):
        raise RuntimeError("ERROR: Cannot clear system or home directory!")

    if not target_path.exists():
        print(f"Directory does not exist: {target_path}")
        return

    # Clear contents
    for item in target_path.iterdir():
        try:
            if item.is_file():
                item.unlink()
                print(f"Deleted file: {item}")

            elif item.is_dir() and delete_subfolders:
                shutil.rmtree(item)
                print(f"Deleted folder: {item}")

        except Exception as e:
            print(f"Failed to delete {item}: {str(e)}")

    print(f"\n✅ Directory cleared: {target_path}")


# ---------------------------
# Usage (Your PDF directory)
# ---------------------------
if __name__ == "__main__":
    # Fixed path (works no matter who calls this script)
    BASE_DIR = Path(__file__).resolve().parent
    TARGET_FOLDER = BASE_DIR / "../../data/graph/case_study/raw_pdf_m"

    # Set to True to DELETE subfolders, False to KEEP them
    clear_directory(TARGET_FOLDER, delete_subfolders=False)