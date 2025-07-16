import os

# --- IMPORTANT: This must be the very first Kivy-related import ---
# Tell Kivy not to create a window, which is essential for a headless environment.
os.environ['KIVY_NO_WINDOW'] = '1'

from kivy.lang import Builder
import sys

print("Checking syntax for hushos.kv...")

try:
    # Attempt to load the .kv file
    Builder.load_file('hushos.kv')
    # If it succeeds, print a success message
    print("\n✅ SUCCESS: hushos.kv syntax is OK!")
    sys.exit(0) # Exit with a success code

except Exception as e:
    # If it fails, print the error and exit with a failure code
    print("\n❌ FAILED: Found a syntax error in hushos.kv.")
    print("---------------------------------------------")
    print(e)
    print("---------------------------------------------")
    sys.exit(1)
