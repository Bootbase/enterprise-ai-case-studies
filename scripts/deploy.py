#!/usr/bin/env python3
"""
Migration & Deploy Script
Run from repo root:  python3 scripts/deploy.py
"""

import os
import re
import shutil
import subprocess
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCS_UC = os.path.join(REPO_ROOT, "docs", "use-cases")

CATEGORY_MAP = {
    "001": "document-processing",
    "002": "document-processing",
    "100": "customer-service",
    "101": "customer-service",
    "200": "workflow-automation",
    "201": "workflow-automation",
    "202": "workflow-automation",
    "203": "workflow-automation",
    "204": "workflow-automation",
    "205": "workflow-automation",
    "206": "workflow-automation",
    "300": "code-and-devops",
    "301": "code-and-devops",
    "302": "code-and-devops",
    "400": "knowledge-management",
    "401": "knowledge-management",
    "500": "industry-specific",
    "501": "industry-specific",
    "502": "industry-specific",
    "503": "industry-specific",
    "504": "industry-specific",
    "505": "industry-specific",
    "506": "industry-specific",
    "507": "industry-specific",
    "508": "industry-specific",
    "509": "industry-specific",
}


def step1_move_to_categories():
    print("Step 1: Organizing use cases into category folders...")
    moved = 0

    if not os.path.isdir(DOCS_UC):
        print(f"  ERROR: {DOCS_UC} does not exist")
        return

    for entry in sorted(os.listdir(DOCS_UC)):
        entry_path = os.path.join(DOCS_UC, entry)
        if not os.path.isdir(entry_path):
            continue
        if not re.match(r"UC-\d{3}-", entry):
            continue

        match = re.search(r"UC-(\d{3})-", entry)
        if not match:
            continue
        uc_id = match.group(1)

        category = CATEGORY_MAP.get(uc_id)
        if not category:
            print(f"  WARN: No category for {entry}, skipping")
            continue

        dest_dir = os.path.join(DOCS_UC, category)
        dest = os.path.join(dest_dir, entry)

        if os.path.exists(dest):
            print(f"  SKIP: {category}/{entry} already exists")
            continue

        os.makedirs(dest_dir, exist_ok=True)
        shutil.move(entry_path, dest)
        print(f"  MOVED: {entry} -> {category}/{entry}")
        moved += 1

    print(f"  Moved {moved} use case folders.\n")


def step2_cleanup():
    print("Step 2: Cleaning up stale directories...")

    dirs_to_remove = [
        os.path.join(REPO_ROOT, "docs", "_use_cases"),
        os.path.join(REPO_ROOT, "use-cases"),
    ]
    files_to_remove = [
        os.path.join(REPO_ROOT, "scripts", "generate-docs.py"),
        os.path.join(REPO_ROOT, "scripts", "migrate-to-categories.py"),
        os.path.join(REPO_ROOT, "scripts", "deploy.sh"),
    ]

    for d in dirs_to_remove:
        if os.path.isdir(d):
            shutil.rmtree(d)
            print(f"  Removed: {os.path.relpath(d, REPO_ROOT)}/")

    for f in files_to_remove:
        if os.path.isfile(f):
            os.remove(f)
            print(f"  Removed: {os.path.relpath(f, REPO_ROOT)}")

    print()


def step3_show_structure():
    print("Step 3: Final structure...\n")
    print("  docs/use-cases/")
    cats = [
        "document-processing", "customer-service", "workflow-automation",
        "code-and-devops", "knowledge-management", "industry-specific",
    ]
    for cat in cats:
        cat_path = os.path.join(DOCS_UC, cat)
        if os.path.isdir(cat_path):
            count = sum(
                1 for e in os.listdir(cat_path)
                if os.path.isdir(os.path.join(cat_path, e)) and e.startswith("UC-")
            )
            print(f"    {cat}/ ({count} use cases)")
    print()


def step4_git():
    print("Step 4: Committing and pushing...")
    os.chdir(REPO_ROOT)

    subprocess.run(["git", "add", "-A"], check=True)
    result = subprocess.run(["git", "status", "--short"], capture_output=True, text=True)
    print(result.stdout)

    msg = (
        "feat: add GitHub Pages site with BootbaseBV branding\n\n"
        "- Jekyll site in docs/ with custom domain (enterprise-ai-use-cases.bootbase.be)\n"
        "- Renumbered IDs: 100 slots per category (001-099, 100-199, ..., 500-999)\n"
        "- Use cases organized by category subdirectory\n"
        "- Filterable card-grid homepage with search\n"
        "- Tabbed detail views for solution design, implementation, evaluation, references\n"
        "- GitHub Actions workflow for auto-deploy on push to main\n"
        "- Updated skills, templates, AGENTS.md for new structure\n"
        "- All markdown files include Jekyll front matter (no intermediate build step)"
    )

    confirm = input("  Commit and push? [y/N] ").strip().lower()
    if confirm == "y":
        subprocess.run(["git", "commit", "-m", msg], check=True)
        subprocess.run(["git", "push", "origin", "main"], check=True)
        print("\n  Pushed! Site will deploy via GitHub Actions.")
        print("  Check: https://enterprise-ai-use-cases.bootbase.be/")
    else:
        print("  Skipped. Run manually:")
        print("    git commit -m 'feat: add GitHub Pages site'")
        print("    git push origin main")


def main():
    print("=" * 60)
    print("  Enterprise AI Use Cases — Migration & Deploy")
    print("=" * 60)
    print()

    step1_move_to_categories()
    step2_cleanup()
    step3_show_structure()
    step4_git()

    print()
    print("=" * 60)
    print("  Done!")
    print("=" * 60)


if __name__ == "__main__":
    main()
