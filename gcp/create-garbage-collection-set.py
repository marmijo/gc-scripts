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
        print(f"Usage: {sys.argv[0]} ALL_IMAGES_FILE BOOT_IMAGES_FILE", file=sys.stderr)
        sys.exit(1)

    all_images_file = sys.argv[1]
    boot_images_file = sys.argv[2]

    boot_images = load_set(boot_images_file)

    with open(all_images_file, "r", encoding="utf-8") as f:
        for line in f:
            s = line.strip()
            if not s or s.startswith("#"):
                continue
            if s not in boot_images:
                print(s)

if __name__ == "__main__":
    main()

