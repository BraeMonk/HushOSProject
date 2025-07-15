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
source.include_exts = py,png,jpg,kv,atlas,wav,json

# (str) Application versioning
version = 0.1

# (list) List of modules to bundle with your application
requirements = python3,kivy,google-generativeai,pillow,pyjnius,android

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

# (int) Android API target. 33 is very stable for CI builds.
android.api = 33

# (int) Minimum API required
android.minapi = 21

# (str) Explicitly set the Build Tools version for reliability
android.build_tools_version = 33.0.2

# (str) A known stable NDK version
android.ndk_version = 25.2.9519653

# These blank paths force Buildozer to use the SDK and NDK from the
# environment, which are set up by the GitHub Actions workflow.
android.sdk_path = 
android.ndk_path =

# (str) How the app window behaves when the keyboard appears.
android.window_soft_input_mode = adjustResize

# (str) The python-for-android branch to use. 'develop' often has more recent recipes.
p4a.branch = develop

# (bool) Enables Android auto backup feature
android.allow_backup = True

# (int) Log level for buildozer
log_level = 2

# (int) Display warning if buildozer is run as root
warn_on_root = 1
