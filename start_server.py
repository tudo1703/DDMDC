import os
import subprocess
import sys
import re
import glob

def install_java_via_sdkman():
    sdkman_init_paths = [
        "/usr/local/sdkman/bin/sdkman-init.sh",
        os.path.expanduser("~/.sdkman/bin/sdkman-init.sh")
    ]
    sdkman_init = None
    for path in sdkman_init_paths:
        if os.path.exists(path):
            sdkman_init = path
            break
            
    if not sdkman_init:
        return False
        
    try:
        print("[+] Dang doc danh sach phien ban Java tu SDKMAN...")
        cmd = f"bash -c 'source {sdkman_init} && sdk list java'"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode != 0:
            return False
            
        # Tim kiem phien ban Java 11 truoc
        versions = list(dict.fromkeys(re.findall(r'\b(11\.[0-9a-zA-Z.-]+)\b', result.stdout)))
        if not versions:
            # Neu khong co Java 11 thi tim Java 8
            versions = list(dict.fromkeys(re.findall(r'\b(8\.[0-9a-zA-Z.-]+)\b', result.stdout)))
            
        if versions:
            # Uu tien phien ban cua Microsoft (-ms) hoac Temurin (-tem) vi chung rat on dinh
            selected_version = None
            for v in versions:
                if '-ms' in v or '-tem' in v:
                    selected_version = v
                    break
            if not selected_version:
                selected_version = versions[0]
                
            print(f"[+] Tim thay phien ban Java phu hop trong SDKMAN: {selected_version}")
            print(f"[+] Dang tien hanh cai dat {selected_version} qua SDKMAN...")
            install_cmd = f"bash -c 'source {sdkman_init} && yes | sdk install java {selected_version}'"
            res = subprocess.run(install_cmd, shell=True)
            return res.returncode == 0
    except Exception as e:
        print(f"[-] Loi khi tu dong cai dat qua SDKMAN: {e}")
    return False

def install_java_via_apt():
    try:
        print("[+] Dang thu cai dat OpenJDK 11 qua apt-get (can quyen sudo)...")
        # Chay apt-get update va install
        subprocess.run(["sudo", "apt-get", "update", "-y"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(["sudo", "apt-get", "install", "-y", "openjdk-11-jre-headless"], check=True)
        return True
    except Exception as e:
        print(f"[-] Khong the cai dat bang apt-get: {e}")
    return False

# Chuyen thu muc lam viec ve thu muc chua file script nay
script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)

# Lay thong tin Codespace de tao IP ket noi
codespace_name = os.environ.get("CODESPACE_NAME")
port_domain = os.environ.get("GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN", "app.github.dev")

print("=" * 70)
print("             MINECRAFT FORGE 1.16.5 SERVER LAUNCHER")
print("=" * 70)

if codespace_name:
    public_ip = f"{codespace_name}-25565.{port_domain}"
    print(f"\n[+] Phat hien dang chay trong GitHub Codespace!")
    print(f"[+] Cong Server Minecraft: 25565")
    print(f"[+] DIA CHI IP DE KET NOI (Minecraft Server IP):")
    print(f"    \033[92m\033[1m{public_ip}\033[0m")
    print("\n[!] HUONG DAN KET NOI:")
    print("    1. Vao tab 'Ports' (Canh Terminal).")
    print("    2. Click chuot phai vao port 25565 -> Port Visibility -> Public.")
    print("    3. Copy dia chi tren vao muc Direct Connection trong game Minecraft.")
else:
    print(f"\n[+] Dang chay o may local.")
    print(f"[+] IP ket noi: localhost:25565")

# Tao thu muc crash-reports neu chua ton tai
os.makedirs("crash-reports", exist_ok=True)

def get_client_mods():
    backup_dir = "client_mods_backup"
    if not os.path.exists(backup_dir):
        return []
    client_mods = []
    for f in os.listdir(backup_dir):
        name = f
        if name.endswith(".disabled"):
            name = name[:-9]
        if name.endswith(".jar"):
            client_mods.append(name)
    return list(set(client_mods))

def restore_client_mods():
    if not os.path.exists("mods"):
        return
    restored = 0
    for f in os.listdir("mods"):
        if f.endswith(".disabled"):
            disabled_path = os.path.join("mods", f)
            original_name = f[:-9]
            original_path = os.path.join("mods", original_name)
            try:
                if os.path.exists(original_path):
                    os.remove(original_path)
                os.rename(disabled_path, original_path)
                restored += 1
            except Exception as e:
                print(f"[-] Loi restore mod {f}: {e}")
    if restored:
        print(f"[+] Da khoi phuc lai {restored} client mods trong thu muc mods/")

def disable_client_mods():
    restore_client_mods()
    client_mods = get_client_mods()
    if not client_mods:
        return []
    disabled = []
    for mod in client_mods:
        mod_path = os.path.join("mods", mod)
        if os.path.exists(mod_path):
            disabled_path = mod_path + ".disabled"
            try:
                if os.path.exists(disabled_path):
                    os.remove(disabled_path)
                os.rename(mod_path, disabled_path)
                disabled.append((mod_path, disabled_path))
            except Exception as e:
                print(f"[-] Loi vo hieu hoa mod {mod}: {e}")
    if disabled:
        print(f"[+] Da tam thoi vo hieu hoa {len(disabled)} client-side mods de khoi dong server.")
    return disabled

print("=" * 70)
print("Khoi dong Minecraft Server... Vui long doi...")
print("=" * 70)

# Khoi chay server tuy theo he dieu hanh
try:
    # Vo hieu hoa cac client mod truoc khi chay
    disable_client_mods()
    
    # Cau hinh RAM toi thieu 4GB (-Xms4G) va toi da 8GB (-Xmx8G)
    ram_args = ["-Xms4G", "-Xmx8G", "-XX:+UseG1GC"]
    jar_file = "forge-1.16.5-36.2.42.jar"
    
    if os.name == 'nt':
        # Chay tren Windows
        # Tim Java 8 hoac 11 (Forge 1.16.5 can Java 8/11)
        import glob
        java_cmd = "java"
        possible_windows_patterns = [
            "C:\\Program Files\\Java\\jre1.8.*\\bin\\java.exe",
            "C:\\Program Files\\Java\\jdk1.8.*\\bin\\java.exe",
            "C:\\Program Files\\Java\\jre-11.*\\bin\\java.exe",
            "C:\\Program Files\\Java\\jdk-11.*\\bin\\java.exe",
            "C:\\Program Files (x86)\\Java\\jre1.8.*\\bin\\java.exe",
            "C:\\Program Files (x86)\\Java\\jdk1.8.*\\bin\\java.exe",
        ]
        found_java_paths = []
        for pattern in possible_windows_patterns:
            found_java_paths.extend(glob.glob(pattern))
            
        if found_java_paths:
            java_cmd = found_java_paths[0]
            print(f"[+] Tim thay Java 8/11 tai: {java_cmd}")
        else:
            print("[-] CANH BAO: Khong tim thay phien ban Java 8/11 trong he thong!")
            print("[+] Se thu dung lenh 'java' mac dinh cua he thong.")
            
        cmd = [java_cmd] + ram_args + ["-jar", jar_file, "nogui"]
        print(f"[+] Lenh khoi chay: {' '.join(cmd)}")
        if java_cmd == "java":
            subprocess.run(cmd, shell=True)
        else:
            subprocess.run(cmd)
    else:
        # Chay tren Linux / Codespace
        # Tim Java 8 hoac 11 (Forge 1.16.5 can Java 8/11 de hoat dong tot nhat)
        java_cmd = "java"
        possible_patterns = [
            "/usr/local/sdkman/candidates/java/8*/bin/java",
            "/usr/local/sdkman/candidates/java/11*/bin/java",
            "/usr/lib/jvm/java-8*/bin/java",
            "/usr/lib/jvm/java-1.8.0*/bin/java",
            "/usr/lib/jvm/java-11*/bin/java",
            "/usr/lib/jvm/jdk-11*/bin/java",
            # Fallback sang Java 17 neu khong tim thay Java 8/11
            "/usr/local/sdkman/candidates/java/17*/bin/java",
            "/usr/lib/jvm/java-17*/bin/java",
        ]
        found_java_paths = []
        for pattern in possible_patterns:
            found_java_paths.extend(glob.glob(pattern))
        
        if found_java_paths:
            java_cmd = found_java_paths[0]
            print(f"[+] Tim thay Java tai: {java_cmd}")
        else:
            print("[-] CANH BAO: Khong tim thay phien ban Java phu hop (Java 8/11) trong he thong!")
            
            # Tu dong cai dat
            installed = False
            if install_java_via_sdkman():
                installed = True
            
            if not installed:
                if install_java_via_apt():
                    installed = True
            
            if installed:
                # Kiem tra lai danh sach phien ban
                found_java_paths = []
                for pattern in possible_patterns:
                    found_java_paths.extend(glob.glob(pattern))
                if found_java_paths:
                    java_cmd = found_java_paths[0]
                    print(f"[+] Da tu dong cai dat Java phu hop tai: {java_cmd}")
                else:
                    print("[-] Khong tim thay duong dan Java vua cai dat, su dung mac dinh.")
            else:
                print("[-] CANH BAO: Khong the tu dong cai dat Java 8/11. Se thu dung lenh 'java' mac dinh.")
                print("[+] Cac phien ban Java dang co san trong SDKMAN:")
                if os.path.exists("/usr/local/sdkman/candidates/java/"):
                    try:
                        print("    " + ", ".join(os.listdir("/usr/local/sdkman/candidates/java/")))
                    except Exception:
                        pass

        cmd = [java_cmd] + ram_args + ["-jar", jar_file, "nogui"]
        print(f"[+] Lenh khoi chay: {' '.join(cmd)}")
        subprocess.run(cmd)
except KeyboardInterrupt:
    print("\n[!] Dang tat server...")
except Exception as e:
    print(f"[!] Loi khi chay server: {e}")
finally:
    # Luon khoi phuc lai cac client mod sau khi server dung
    restore_client_mods()
