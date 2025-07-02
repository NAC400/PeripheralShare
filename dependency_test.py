import sys

def test_dependencies():
    print("=" * 50)
    print("PeripheralShare - Dependency Check")
    print("=" * 50)
    print(f"Python version: {sys.version}")
    print()
    
    dependencies = [
        ("PyQt6", "PyQt6.QtWidgets"),
        ("pynput", "pynput"),
        ("psutil", "psutil"),
        ("zeroconf", "zeroconf")
    ]
    
    available = []
    missing = []
    
    for name, module in dependencies:
        try:
            __import__(module)
            available.append(name)
            print(f"✅ {name} - Available")
        except ImportError:
            missing.append(name)
            print(f"❌ {name} - Missing")
    
    print()
    if missing:
        print("To install missing dependencies:")
        print(f"pip install {' '.join(missing)}")
        print()
        print("Or install all at once:")
        print("pip install PyQt6 pynput psutil zeroconf")
    else:
        print("🎉 All dependencies are available!")
        print("You can run the full PeripheralShare application!")
    
    return len(missing) == 0

if __name__ == "__main__":
    test_dependencies()
