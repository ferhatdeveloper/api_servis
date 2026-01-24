import base64
import os

# Modern Professional Database Icon (Transparent Background PNG)
# Generated via generate_image tool
icon_data = "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"

def create_transparent_icon():
    try:
        data = base64.b64decode(icon_data)
        icon_path = "d:/Developer/App/EXFIN_OPS/backend/modern_database_icon_v2.png"
        with open(icon_path, "wb") as f:
            f.write(data)
        print("Success: Transparent icon created at", icon_path)
    except Exception as e:
        print("Error creating icon:", e)

if __name__ == "__main__":
    create_transparent_icon()
