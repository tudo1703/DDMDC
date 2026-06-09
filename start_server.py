import os
import subprocess
import sys

# Chuyển thư mục làm việc về thư mục chứa file script này
script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)

# Lấy thông tin Codespace để tạo IP kết nối
codespace_name = os.environ.get("CODESPACE_NAME")
port_domain = os.environ.get("GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN", "app.github.dev")

print("=" * 70)
print("             MINECRAFT FORGE 1.16.5 SERVER LAUNCHER")
print("=" * 70)

if codespace_name:
    public_ip = f"{codespace_name}-25565.{port_domain}"
    print(f"\n[+] Phát hiện đang chạy trong GitHub Codespace!")
    print(f"[+] Cổng Server Minecraft: 25565")
    print(f"[+] ĐỊA CHỈ IP ĐỂ KẾT NỐI (Minecraft Server IP):")
    print(f"    \033[92m\033[1m{public_ip}\033[0m")
    print("\n[!] HƯỚNG DẪN KẾT NỐI:")
    print("    1. Vào tab 'Ports' (Cạnh Terminal).")
    print("    2. Nhấp chuột phải vào port 25565 -> Port Visibility -> Public.")
    print("    3. Copy địa chỉ trên vào mục Direct Connection trong game Minecraft.")
else:
    print(f"\n[+] Đang chạy ở máy local.")
    print(f"[+] IP kết nối: localhost:25565")

# Tạo thư mục crash-reports nếu chưa tồn tại
os.makedirs("crash-reports", exist_ok=True)

print("=" * 70)
print("Khởi động Minecraft Server... Vui lòng đợi...")
print("=" * 70)

# Khởi chạy server tùy theo hệ điều hành
try:
    # Cấu hình RAM tối thiểu 4GB (-Xms4G) và tối đa 8GB (-Xmx8G)
    ram_args = ["-Xms4G", "-Xmx8G", "-XX:+UseG1GC"]
    jar_file = "forge-1.16.5-36.2.42.jar"
    
    if os.name == 'nt':
        # Chạy trên Windows
        cmd = ["java"] + ram_args + ["-jar", jar_file, "nogui"]
        print(f"[+] Lệnh khởi chạy: {' '.join(cmd)}")
        subprocess.run(cmd, shell=True)
    else:
        # Chạy trên Linux / Codespace
        # Tìm Java 8 hoặc 11 (Forge 1.16.5 cần Java 8/11 để hoạt động tốt nhất)
        import glob
        java_cmd = "java"
        possible_patterns = [
            "/usr/local/sdkman/candidates/java/8*/bin/java",
            "/usr/local/sdkman/candidates/java/11*/bin/java",
            "/usr/lib/jvm/java-8*/bin/java",
            "/usr/lib/jvm/java-1.8.0*/bin/java",
            "/usr/lib/jvm/java-11*/bin/java",
            "/usr/lib/jvm/jdk-11*/bin/java",
            # Fallback sang Java 17 nếu không tìm thấy Java 8/11
            "/usr/local/sdkman/candidates/java/17*/bin/java",
            "/usr/lib/jvm/java-17*/bin/java",
        ]
        found_java_paths = []
        for pattern in possible_patterns:
            found_java_paths.extend(glob.glob(pattern))
        
        if found_java_paths:
            java_cmd = found_java_paths[0]
            print(f"[+] Tìm thấy Java tại: {java_cmd}")
        else:
            print("[-] CẢNH BÁO: Không tìm thấy phiên bản Java phù hợp (Java 8/11) trong hệ thống!")
            print("[+] Các phiên bản Java đang có sẵn trong SDKMAN:")
            if os.path.exists("/usr/local/sdkman/candidates/java/"):
                try:
                    print("    " + ", ".join(os.listdir("/usr/local/sdkman/candidates/java/")))
                except Exception:
                    pass

        cmd = [java_cmd] + ram_args + ["-jar", jar_file, "nogui"]
        print(f"[+] Lệnh khởi chạy: {' '.join(cmd)}")
        subprocess.run(cmd)
except KeyboardInterrupt:
    print("\n[!] Đang tắt server...")
except Exception as e:
    print(f"[!] Lỗi khi chạy server: {e}")
