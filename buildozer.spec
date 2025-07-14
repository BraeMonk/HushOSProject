[app]
# (str) Title of your application
title = HushOS

# (str) Package name
package.name = hushos

# (str) Package domain (needed for android/ios packaging)
package.domain = org.hushos

# (str) Source code where the main.py live
source.dir = .

# (list) Source files to include (let buildozer find them)
source.include_exts = py,png,jpg,kv,atlas,wav,json

# (str) Application versioning
version = 0.1

# (list) List of modules to bundle with your application
# Added specific, stable version of pyjnius to fix build error.
requirements = python3,kivy,google-generativeai,pillow,pyjnius==1.6.1

# (str) Presplash background color (for new android builds)
android.presplash_color = #fdfae6

# (str) Presplash image (must be in the source directory)
android.presplash_png = %(source.dir)s/assets/icon.png

# (str) Icon of the application (must be in the source directory)
icon.filename = %(source.dir)s/assets/icon.png

# (str) Supported orientation (portrait is best for this app)
orientation = portrait

# (list) Permissions
# INTERNET is required for the AI. VIBRATE can be used for notifications.
android.permissions = INTERNET,VIBRATE

# (int) Android API to use. 31 is a good modern choice.
android.api = 31

# (int) Minimum API required. 21 covers most Android devices.
android.minapi = 21

# (str) How the app window behaves when the keyboard appears.
# 'adjustResize' ensures the window resizes, preventing the keyboard from covering input fields.
android.window_soft_input_mode = adjustResize

# (int) Android NDK version to use
android.ndk = 25b

# (str) Version of the Android Build Tools to use
android.build_tools_version = 34.0.0


[buildozer]

android.sdk_path = $ANDROID_HOME

# (int) Log level (0 = error, 1 = info, 2 = debug (with command output))
log_level = 2

# (int) Display warning if buildozer is run as root (0 = False, 1 = True)
warn_on_root = 1
