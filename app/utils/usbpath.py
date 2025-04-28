import getpass,os
def find_usb_mount_path():
    username = getpass.getuser()
    media_path = f"/media/{username}"

    if os.path.exists(media_path):
        for item in os.listdir(media_path):
            full_path = os.path.join(media_path, item)
            if os.path.ismount(full_path):
                return full_path  # Return the first mounted USB path

    return None

def box_base_path():
    return "/home/vishal/aerohub/python_crud_fastapi/public/"