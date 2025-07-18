[app]
# (str) Title of your application
title = HushOS

# (str) Package name
package.name = hushos

# (str) Package domain (needed for android/ios packaging)
package.domain = org.hushos

# (str) Source code directory
source.dir = .

# (list) Source file extensions to include
source.include_exts = py,png,jpg,kv,atlas,wav,json,txt

# (str) Application versioning
version = 0.1

# (list) List of modules to bundle with your application
# Removed google-generativeai and google-api-python-client as they don't work with p4a
# Added certifi for SSL certificate handling
requirements = python3,kivy,kivymd,pillow,pyjnius,android,openssl,sqlite3,requests,urllib3,tqdm,certifi

# (str) Icon of the application
icon.filename = %(source.dir)s/assets/icon.png

# (str) Supported orientation
orientation = portrait

[android]
# (str) Presplash background color
presplash_color = #fdfae6

# (str) Presplash image
presplash_png = %(source.dir)s/assets/icon.png

# (list) The Android archs to build for
archs = arm64-v8a, armeabi-v7a

# (list) Permissions
permissions = INTERNET,VIBRATE

# (int) Android API target. 33 is very stable for CI builds.
api = 33

# (int) Minimum API required
minapi = 21

# (str) Explicitly set the Build Tools version for reliability
build_tools_version = 34.0.0

# (str) A known stable NDK version
ndk_version = 25.2.9519653

# These blank paths force Buildozer to use the SDK and NDK from the
# environment, which are set up by the GitHub Actions workflow.
sdk_path = 
ndk_path =

# (str) How the app window behaves when the keyboard appears.
window_soft_input_mode = adjustResize

# (bool) Enables Android auto backup feature
allow_backup = True

# (bool) Accept SDK license automatically
accept_sdk_license = True

[p4a]
# (str) The python-for-android branch to use. 'develop' often has more recent recipes.
branch = develop

[buildozer]
# (int) Log level for buildozer
log_level = 2

# (int) Display warning if buildozer is run as root
warn_on_root = 1
