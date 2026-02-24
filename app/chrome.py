"""Chrome cookie scanner - extracts Claude sessionKey from all Chrome profiles."""
import glob
import json
import os
import re
import shutil
import sqlite3
import sys
import tempfile

def get_chrome_base():
    if sys.platform == "win32":
        return os.path.join(os.environ.get("LOCALAPPDATA", ""), "Google", "Chrome", "User Data")
    elif sys.platform == "darwin":
        return os.path.expanduser("~/Library/Application Support/Google/Chrome")
    else:
        return os.path.expanduser("~/.config/google-chrome")

def get_decryption_key():
    """Get the key to decrypt Chrome cookies."""
    if sys.platform == "win32":
        return _get_windows_key()
    elif sys.platform == "darwin":
        return _get_macos_key()
    else:
        raise NotImplementedError("Linux not yet supported")

def _get_macos_key():
    import subprocess
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    from cryptography.hazmat.primitives import hashes
    
    pw = subprocess.check_output(
        ["security", "find-generic-password", "-s", "Chrome Safe Storage", "-w"],
        text=True
    ).strip()
    kdf = PBKDF2HMAC(algorithm=hashes.SHA1(), length=16, salt=b'saltysalt', iterations=1003)
    return kdf.derive(pw.encode())

def _get_windows_key():
    """Get Chrome encryption key on Windows using DPAPI."""
    import base64
    try:
        import win32crypt
    except ImportError:
        raise ImportError("pywin32 is required on Windows. Install with: pip install pywin32")
    
    chrome_base = get_chrome_base()
    local_state_path = os.path.join(chrome_base, "Local State")
    
    with open(local_state_path, "r", encoding="utf-8") as f:
        local_state = json.load(f)
    
    encrypted_key = base64.b64decode(local_state["os_crypt"]["encrypted_key"])
    # Remove 'DPAPI' prefix (5 bytes)
    encrypted_key = encrypted_key[5:]
    return win32crypt.CryptUnprotectData(encrypted_key, None, None, None, 0)[1]

def decrypt_cookie_value(encrypted_value, key):
    """Decrypt a Chrome cookie value."""
    if sys.platform == "darwin":
        return _decrypt_macos(encrypted_value, key)
    elif sys.platform == "win32":
        return _decrypt_windows(encrypted_value, key)
    return None

def _decrypt_macos(encrypted_value, key):
    if encrypted_value[:3] != b'v10':
        return None
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
    iv = b' ' * 16
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv))
    d = cipher.decryptor()
    dec = d.update(encrypted_value[3:]) + d.finalize()
    pad_len = dec[-1]
    if isinstance(pad_len, int) and 1 <= pad_len <= 16:
        dec = dec[:-pad_len]
    m = re.search(rb'(sk-ant-\S+)', dec)
    return m.group(1).decode() if m else None

def _decrypt_windows(encrypted_value, key):
    """Decrypt cookie using AES-256-GCM (Chrome v80+ on Windows)."""
    if encrypted_value[:3] == b'v10' or encrypted_value[:3] == b'v11':
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        nonce = encrypted_value[3:15]
        ciphertext = encrypted_value[15:]
        aesgcm = AESGCM(key)
        try:
            dec = aesgcm.decrypt(nonce, ciphertext, None)
            return dec.decode("utf-8", errors="replace")
        except Exception:
            return None
    else:
        # Older Chrome - try DPAPI directly
        try:
            import win32crypt
            dec = win32crypt.CryptUnprotectData(encrypted_value, None, None, None, 0)[1]
            return dec.decode("utf-8", errors="replace")
        except Exception:
            return None

def get_profile_name(profile_path):
    """Get human-readable profile name from Preferences."""
    prefs_path = os.path.join(profile_path, "Preferences")
    try:
        with open(prefs_path, encoding="utf-8") as f:
            prefs = json.load(f)
        return prefs.get("profile", {}).get("name", os.path.basename(profile_path))
    except Exception:
        return os.path.basename(profile_path)

def scan_all_profiles():
    """Scan all Chrome profiles and return those with Claude sessionKeys.
    
    Returns list of dicts:
        [{"profile": "Profile 1", "profile_name": "Work", "session_key": "sk-ant-..."}]
    """
    chrome_base = get_chrome_base()
    if not os.path.exists(chrome_base):
        return []
    
    try:
        key = get_decryption_key()
    except Exception as e:
        print(f"Failed to get Chrome decryption key: {e}")
        return []
    
    results = []
    
    # Find all profile directories
    profile_dirs = []
    default_dir = os.path.join(chrome_base, "Default")
    if os.path.isdir(default_dir):
        profile_dirs.append(default_dir)
    
    for d in sorted(glob.glob(os.path.join(chrome_base, "Profile *"))):
        if os.path.isdir(d):
            profile_dirs.append(d)
    
    for profile_dir in profile_dirs:
        cookie_db = os.path.join(profile_dir, "Cookies")
        if not os.path.exists(cookie_db):
            continue
        
        # Copy to temp to avoid lock issues
        tmp = tempfile.mktemp(suffix=".db")
        try:
            shutil.copy2(cookie_db, tmp)
            conn = sqlite3.connect(tmp)
            row = conn.execute(
                "SELECT encrypted_value FROM cookies "
                "WHERE host_key LIKE '%claude.ai%' AND name='sessionKey' LIMIT 1"
            ).fetchone()
            conn.close()
            
            if not row:
                continue
            
            session_key = decrypt_cookie_value(row[0], key)
            if session_key and session_key.startswith("sk-ant-"):
                profile_name = get_profile_name(profile_dir)
                results.append({
                    "profile": os.path.basename(profile_dir),
                    "profile_name": profile_name,
                    "session_key": session_key,
                })
        except Exception as e:
            print(f"Error scanning {profile_dir}: {e}")
        finally:
            try:
                os.unlink(tmp)
            except OSError:
                pass
    
    return results
