import sys
import requests

def test_imports():
    print("Python executable:", sys.executable)
    print("Python version:", sys.version)
    print("Requests module path:", requests.__file__)

if __name__ == "__main__":
    test_imports()
    
print("✅ Setup is successful! All dependencies are working.")

