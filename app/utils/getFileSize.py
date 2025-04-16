from pathlib import Path
import os
def list_files_with_sizes(folder_path: str):
    path = Path(folder_path)

    if not path.exists() or not path.is_dir():
        return {"error": "Folder not found"}

    files_info = []
    for file in path.rglob("*"):
        if file.is_file():
            size_bytes = file.stat().st_size
            size_kb = round(size_bytes/1024, 2)
            size_mb = round(size_bytes / (1024 * 1024), 2)
            files_info.append({
                "name": file.name,
                "size_bytes": size_bytes,
                "size_kb": size_kb,
                "size_mb": size_mb
            })

    return {
        "folder": path.name,
        "total_files": len(files_info),
        "files": files_info
    }
    
def get_folder_size(path):
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            # Skip broken symlinks
            if os.path.exists(fp):
                total_size += os.path.getsize(fp)
    return total_size

def list_folders_with_sizes(base_path):
    folders = []
    for name in os.listdir(base_path):
        full_path = os.path.join(base_path, name)
        if os.path.isdir(full_path):
            size_bytes = get_folder_size(full_path)
            folders.append({
                "name": name,
                "size_bytes": size_bytes,
                "size_mb": round(size_bytes / (1024 * 1024), 2)
            })
    return folders