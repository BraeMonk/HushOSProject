from kivy.lang import Builder
import sys

print("Checking syntax for hushos.kv...")

try:
    # Attempt to load the .kv file
    Builder.load_file('hushos.kv')
    # If it succeeds, print a success message
    print("✅ SUCCESS: hushos.kv syntax is OK!")
    sys.exit(0) # Exit with a success code

except Exception as e:
    # If it fails, print the error and exit with a failure code
    print("\n❌ FAILED: Found a syntax error in hushos.kv.")
    print("---------------------------------------------")
    print(e)
    print("---------------------------------------------")
    sys.exit(1)
