import hashlib
import os


def get_hash_of_dirs(directory: str, verbose: int = 0) -> str:
    """Return the hash of a DIRECTORY"""
    md5hash = hashlib.md5()
    if not os.path.exists(directory):
        return "-1"
    try:
        for root, dirs, files in os.walk(directory):
            for names in files:
                if verbose == 1:
                    print(f"Hashing: {names}")
                filepath = os.path.join(root, names)
                try:
                    f1 = open(filepath, 'r', encoding="utf-8")
                except Exception as e:
                    # You can't open the file for some reason
                    f1.close()
                    continue
                while 1:
                    # Read file in as little chunks
                    buf = f1.read(4096)
                    if not buf:
                        break
                    md5hash.update(
                        bytearray(hashlib.md5(
                            bytearray(buf, "utf-8")).hexdigest(),
                                  "utf-8"))
                f1.close()
    except Exception as e:
        import traceback
        # Print the stack traceback
        traceback.print_exc(e)
        return "-2"

    return md5hash.hexdigest()

