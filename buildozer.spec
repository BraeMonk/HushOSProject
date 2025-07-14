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
android.permissions = INTERNET,VIBRATE

# (int) Android API to use. 33 is more stable than 31
android.api = 33

# (int) Minimum API required. 21 covers most Android devices.
android.minapi = 21

# (str) How the app window behaves when the keyboard appears.
android.window_soft_input_mode = adjustResize

# (str) Android NDK version to use (fixed format)
android.ndk = 25.2.9519653

# (str) Version of the Android Build Tools to use (compatible with API 33)
android.build_tools_version = 33.0.2

# (str) Android SDK path (will be set by GitHub Actions)
#android.sdk_path = 

# (str) Android NDK path (will be set by GitHub Actions)
#android.ndk_path = 

# (str) Path to the Android SDK build-tools directory (helps with AIDL detection)
#android.build_tools_path = 

# (str) Path to the AIDL executable (if needed)
#android.aidl_path = 

# (str) Android entry point, default is ok for Kivy-based app
#android.entrypoint = org.kivy.android.PythonActivity

# (str) Full name including package path of the Java class that implements Android Activity
#android.activity_class_name = org.kivy.android.PythonActivity

# (str) Full name including package path of the Java class that implements Python Service
#android.service_class_name = org.kivy.android.PythonService

# (str) python-for-android fork to use, defaults to upstream (kivy)
p4a.fork = kivy

# (str) python-for-android branch to use, defaults to master
p4a.branch = master

# (str) python-for-android specific commit to use, defaults to HEAD, must be within p4a.branch
#p4a.commit = HEAD

# (str) The directory in which python-for-android should look for your own build recipes (if any)
#p4a.local_recipes = 

# (str) Comma separated list of python-for-android extensions to install
#p4a.bootstrap = sdl2

# (str) Gradle dependencies to add
#android.gradle_dependencies = 

# (str) Java classes to add as activities to the manifest.
#android.add_activities = 

# (str) python-for-android whitelist
#android.whitelist = 

# (str) Path to a custom whitelist file
#android.whitelist_src = 

# (str) Path to a custom blacklist file
#android.blacklist_src = 

# (str) Bootstrap to use for android builds
p4a.bootstrap = sdl2

# (list) Android application meta-data to set (key=value format)
#android.meta_data = 

# (str) Path to a custom info.plist template if creating an iOS app
#ios.info_plist.template = 

# (str) Bootstrap to use for android builds
#android.bootstrap = sdl2

# (int) Port number to use for the debug server
#android.debug_port = 5678

# (bool) Whether to show the splashscreen
#android.show_splashscreen = 1

# (str) Android logcat filters to use
#android.logcat_filters = *:S python:D

# (bool) Copy library instead of making a libpymodules.so
#android.copy_libs = 1

# (str) The Android arch to build for, choices: armeabi-v7a, arm64-v8a, x86, x86_64
#android.arch = armeabi-v7a

# (int) overrides automatic versionCode computation (used in Package Management)
#android.numeric_version = 1

# (bool) enables Android auto backup feature (Android API >=23)
android.allow_backup = True

# (str) XML file for backup rules (optional)
#android.backup_rules = 

# (str) If you need to insert variables into your AndroidManifest.xml file,
# you can do so with the manifestPlaceholders property.
# This property takes a map of key-value pairs. (via a string)
#android.manifest_placeholders = [:]

# (bool) Skip byte compile for .py files
#android.skip_byte_compile = False

# (str) Path to a custom launcher template to use instead of the default one
#android.launcher_template = 

[buildozer]
# (int) Log level (0 = error, 1 = info, 2 = debug (with command output))
log_level = 2

# (int) Display warning if buildozer is run as root (0 = False, 1 = True)
warn_on_root = 1

# (str) Path to build artifact storage, absolute or relative to spec file
# build_dir = ./.buildozer

# (str) Path to build output (i.e. .apk, .ipa) storage
# bin_dir = ./bin
