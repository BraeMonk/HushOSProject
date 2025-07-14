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
# Added 'json' to ensure all your data and log files are included
source.include_exts = py,png,jpg,kv,atlas,wav,json

# (str) Application versioning
version = 0.1

# (list) List of modules to bundle with your application
# Added 'kivymd' as a common UI library, and specified the google-generativeai recipe
requirements = python3,kivy,google-generativeai,pillow,pyjnius==1.6.1

# (str) Presplash background color
android.presplash_color = #fdfae6

# (str) Presplash image
android.presplash_png = %(source.dir)s/assets/icon.png

# (str) Icon of the application
icon.filename = %(source.dir)s/assets/icon.png

# (str) Supported orientation
orientation = portrait

# (list) Permissions
android.permissions = INTERNET,VIBRATE

# (int) Android API target. 34 is the latest as of recent updates.
android.api = 34

# (int) Minimum API required. 21 is a good baseline.
android.minapi = 21

# (str) How the app window behaves when the keyboard appears.
android.window_soft_input_mode = adjustResize

# (str) Android NDK version to use. 26b is a stable, recent choice.
android.ndk_version = 26b

# (str) The python-for-android branch to use. 'develop' often has more recent recipes.
p4a.branch = develop

# (bool) Enables Android auto backup feature
android.allow_backup = True

# (int) Log level for buildozer
log_level = 2

# (int) Display warning if buildozer is run as root
warn_on_root = 1
