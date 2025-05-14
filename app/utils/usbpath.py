import getpass,os, subprocess
def find_usb_mount_path():
    username = getpass.getuser()
    media_path = f"/media/{username}"

    if os.path.exists(media_path):
        for item in os.listdir(media_path):
            full_path = os.path.join(media_path, item)
            if os.path.ismount(full_path):
                return full_path  # Return the first mounted USB path

    return None

# def find_usb_mount_path():
#     try:
#         output = subprocess.check_output(['lsblk', '-o', 'NAME,MOUNTPOINT,TRAN'], text=True)
#         lines = output.splitlines()
#         for line in lines:
#             if 'usb' in line and '/' in line:  # looking for a mounted path and transport = usb
#                 parts = line.split()
#                 if len(parts) >= 2 and parts[1].startswith('/'):
#                     return parts[1]  # return mountpoint
#     except Exception as e:
#         print(f"Error detecting USB: {e}")
#     return None

def box_base_path():
    return "/home/aerohub/data-transfer-pro/public/"