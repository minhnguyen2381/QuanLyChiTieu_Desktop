import subprocess
import sys

def build():
    print("Bắt đầu build ứng dụng QuanLyChiTieu bằng Nuitka...")
    command = [
        sys.executable, "-m", "nuitka",
        "--standalone",
        "--windows-disable-console",
        "--output-dir=build_output",
        "--include-data-dir=locales=locales",
        "main.py",
    ]

    try:
        subprocess.run(command, check=True)
        print("\nBuild thành công! Thư mục kết quả nằm trong 'build_output/main.dist'")
    except subprocess.CalledProcessError as e:
        print(f"\nLỗi khi build: {e}")
        sys.exit(1)

if __name__ == "__main__":
    build()
