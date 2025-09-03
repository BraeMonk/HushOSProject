[app]
# (str) Title of your application
title = Jerry
# (str) Package name
package.name = jerry
# (str) Package domain (needed for android/ios packaging)
package.domain = org.jerry
# (str) Source code directory
source.dir = .
# (list) Source file extensions to include
source.include_exts = py,png,jpg,kv,atlas,wav,json,txt,env
source.include_patterns = .env
# (str) Application versioning
version = 0.1
# (list) List of modules to bundle with your application
# Removed google-generativeai and google-api-python-client as they don't work with p4a
# Added certifi for SSL certificate handling
requirements = python3,kivy,kivymd,pillow,pyjnius,android,openssl,sqlite3,requests,urllib3,tqdm,certifi,openai,typing_extensions,pydantic,httpx,anyio,sniffio,charset_normalizer,distro,python-dotenv,idna
# (str) Icon of the application
icon.filename = %(source.dir)s/assets/JerryIcon.png
# (str) Supported orientation
orientation = portrait
android.add_assets = assets
env.filename = .env

[android]
# (str) Presplash background color
presplash_color = #fdfae6
# (str) Presplash image
presplash_png = %(source.dir)s/assets/new_splash.png
# (list) The Android archs to build for - reduced to save memory
archs = arm64-v8a
# (list) Permissions
permissions = INTERNET,VIBRATE
# (int) Android API target. Use 31 for better compatibility with CI
api = 31
# (int) Minimum API required
minapi = 21
# (str) Explicitly set the Build Tools version for reliability
build_tools_version = 34.0.0
# (str) Use the short NDK version format that matches your workflow
ndk_version = 25b
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
# (str) Set maximum heap size for Gradle
gradle_java_max_heap_size = 4g
# (list) Gradle dependencies (keep empty to avoid conflicts)
gradle_dependencies = 
# (list) Additional Gradle repositories (keep empty to avoid issues)
add_gradle_maven = 
# (str) Additional gradle options to reduce memory usage
gradle_options = --no-daemon, --parallel, --max-workers=2

[p4a]
# (str) The python-for-android branch to use. 'develop' often has more recent recipes.
branch = master
# (int) Set the number of processes to use for compilation (reduce for memory)
ndk_api = 21

[buildozer]
# (int) Log level for buildozer
log_level = 2
# (int) Display warning if buildozer is run as root
warn_on_root = 1
