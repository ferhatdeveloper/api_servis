from tray_app import create_image
import os

try:
    img = create_image('green')
    img.save('icon_preview.png')
    print("Icon generated successfully: icon_preview.png")
except Exception as e:
    print(f"Error generating icon: {e}")
