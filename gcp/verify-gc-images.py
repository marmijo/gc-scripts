#!/usr/bin/env python3
import sys

def load_set(path):
    items = set()
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            s = line.strip()
            if not s or s.startswith("#"):
                continue
            items.add(s)
    return items

def main():
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} DELETE_LIST_FILE BOOT_IMAGES_FILE", file=sys.stderr)
        sys.exit(1)

    delete_list_file = sys.argv[1]
    boot_images_file = sys.argv[2]

    delete_list = load_set(delete_list_file)
    boot_images = load_set(boot_images_file)

    overlap = delete_list & boot_images
    if overlap:
        print("ERROR: The following images are in both files:")
        for img in sorted(overlap):
            print(img)
        sys.exit(1)
    else:
        print("OK: No images in the delete list are present in the boot-images file.")
        sys.exit(0)

if __name__ == "__main__":
    main()
