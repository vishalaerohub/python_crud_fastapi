from pathlib import Path
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