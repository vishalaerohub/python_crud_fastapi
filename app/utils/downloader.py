import requests
import os
def downloadAndSaveFile(url: str, folder_name: str)->str|bool:
    try:
        # Send GET request to download file
        response = requests.get(url, timeout=15)

        if response.status_code == 200:
            file_contents = response.content

            # Define the full folder path (inside 'public')
            public_folder = "public"
            directory_path = os.path.join(public_folder, folder_name)

            # Create 'public' and 'folder_name' directories if they don't exist
            os.makedirs(directory_path, exist_ok=True)

            # Extract the filename from the URL
            filename = os.path.basename(url)
            full_path = os.path.join(directory_path, filename)

            # Save the file
            with open(full_path, 'wb') as f:
                f.write(file_contents)

            return full_path
        else:
            print(f"❌ Failed to download file. HTTP status: {response.status_code}")
            return False

    except Exception as e:
        print(f"❌ Error downloading file: {e}")
        return False
 