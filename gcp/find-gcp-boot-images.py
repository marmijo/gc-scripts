#!/usr/bin/env python3
import json
import os
import pathlib
import subprocess
from typing import Set


LIST_FILE = pathlib.Path("gcp-images-rhcos-cloud-20251118.txt")


def extract_gcp_images_from_json(blob: str) -> Set[str]:
    images: Set[str] = set()
    try:
        data = json.loads(blob)
    except Exception:
        return images

    # Older style: top-level "gcp": {"image": "..."} or {"name": "..."}
    gcp = data.get("gcp")
    if isinstance(gcp, dict):
        for key in ("image", "name"):
            val = gcp.get(key)
            if val:
                images.add(val)

    # Newer stream-style: architectures.<arch>.images.gcp.{name,image}
    archs = data.get("architectures")
    if isinstance(archs, dict):
        for arch_data in archs.values():
            if not isinstance(arch_data, dict):
                continue

            # Some very early schemas had architectures.<arch>.gcp.image; keep that too.
            arch_gcp = arch_data.get("gcp")
            if isinstance(arch_gcp, dict):
                for key in ("image", "name"):
                    val = arch_gcp.get(key)
                    if val:
                        images.add(val)

            images_block = arch_data.get("images")
            if isinstance(images_block, dict):
                gcp_img = images_block.get("gcp")
                if isinstance(gcp_img, dict):
                    for key in ("image", "name"):
                        val = gcp_img.get(key)
                        if val:
                            images.add(val)

    return images


if __name__ == "__main__":
    # Must be run from the installer/release git repo root.
    # We intentionally do not support running from elsewhere.
    repo_root = pathlib.Path(".").resolve()
    git_dir = repo_root / ".git"
    if not git_dir.exists():
        raise SystemExit("This script must be run from the root of the openshift openshift/installer git repo.")

    remote_branches_cmd = subprocess.run(
        ["git", "-C", str(repo_root), "branch", "-r"],
        check=True,
        capture_output=True,
        text=True,
    )
    branch_names = remote_branches_cmd.stdout.split()
    release_branches = [
        b.strip() for b in branch_names if "release-" in b
    ]

    rhcos_paths = (
        "data/data/coreos/rhcos.json",
        "data/data/rhcos.json",
        "data/data/coreos/scos.json",
    )

    checked_commits: Set[str] = set()
    gcp_boot_images: Set[str] = set()

    for release_branch in release_branches:
        print(f" -> Processing branch: {release_branch}")
        for rhcos_path in rhcos_paths:
            log_proc = subprocess.run(
                [
                    "git",
                    "-C",
                    str(repo_root),
                    "log",
                    "--format=%H",
                    release_branch,
                    "--",
                    rhcos_path,
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            commits_to_check = set(log_proc.stdout.split()) - checked_commits

            for installer_commit in commits_to_check:
                installer_commit = installer_commit.strip()
                if not installer_commit:
                    continue
                show_proc = subprocess.run(
                    [
                        "git",
                        "-C",
                        str(repo_root),
                        "show",
                        f"{installer_commit}:{rhcos_path}",
                    ],
                    capture_output=True,
                    text=True,
                )
                if show_proc.returncode != 0:
                    continue

                images_for_commit = extract_gcp_images_from_json(show_proc.stdout)
                if images_for_commit:
                    print(
                        f"    Commit {installer_commit} ({rhcos_path}) "
                        f"defines GCP images: {', '.join(sorted(images_for_commit))}"
                    )
                    gcp_boot_images.update(images_for_commit)
                checked_commits.add(installer_commit)

    print(f"-> Discovered {len(gcp_boot_images)} distinct GCP boot images from installer history")

    with LIST_FILE.open() as f:
        images_in_gcp = {line.strip() for line in f if line.strip()}

    present_boot_images = sorted(gcp_boot_images & images_in_gcp)

    print(f"{len(present_boot_images)} boot images are present in {LIST_FILE.name}:\n")
    for img in present_boot_images:
        print(img)
