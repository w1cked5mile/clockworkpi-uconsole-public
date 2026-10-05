#!/usr/bin/env python3
"""Scaffold a documentation-first hardware project repository.

Creates the directory tree, seeds every living document from the bundled templates, and writes
.gitignore / .gitattributes / CLAUDE.md. Existing files are never overwritten unless --force.

Example:
    python3 scripts/scaffold.py --path ~/projects/rover --name "Field Rover Mk1" \
        --components "Jetson Orin Nano,RPLIDAR A1,Roboclaw 2x15A" \
        --disciplines "robotics,navigation,power-systems"
"""

import argparse
import datetime as _dt
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TEMPLATES = os.path.join(os.path.dirname(HERE), "assets", "templates")

SUBDIR_DESC = {
    "learned": "Durable understanding — concepts, techniques, limits. One topic per file. Not a "
               "session dump; those go in `../findings/`.",
    "configs": "Tool configuration with the rationale behind each setting, and what to record "
               "after applying it.",
    "runbooks": "Repeatable procedures: preconditions, numbered steps with commands, "
                "verification, rollback.",
    "findings": "Dated observations with equipment, settings, time, and general location. Stays "
                "empty until there is hardware to observe.",
}

GITIGNORE = """# OS / editor
.DS_Store
Thumbs.db
*.swp
*~
.idea/
.vscode/

# Build / archives / images
*.log
*.tmp
*.zip
*.7z
*.img
*.img.xz
*.iso

# Rendered documents (regenerate from source)
*.pdf
*.pptx

# Raw capture data — keep out of git; use LFS if genuinely needed
*.iq
*.cf32
*.cs8
*.cu8
*.sigmf-data
*.pcap
*.kismet
"""

GITATTRIBUTES = "* text=auto eol=lf\n"


def slug(text):
    return "".join(c if c.isalnum() or c in "-_" else "-" for c in text.strip().lower()).strip("-")


def read_template(name):
    with open(os.path.join(TEMPLATES, name), encoding="utf-8") as fh:
        return fh.read()


def render(text, mapping):
    for key, value in mapping.items():
        text = text.replace("{{%s}}" % key, value)
    return text


def write(path, content, force, created, skipped):
    if os.path.exists(path) and not force:
        skipped.append(path)
        return
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(content)
    created.append(path)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--path", required=True, help="target repository directory")
    ap.add_argument("--name", required=True, help='project name, e.g. "Field Rover Mk1"')
    ap.add_argument("--components", default="", help="comma-separated component names")
    ap.add_argument("--disciplines", default="",
                    help="comma-separated knowledge disciplines, e.g. 'robotics,navigation'")
    ap.add_argument("--budgets", default="power",
                    help="comma-separated budget kinds to seed (power, thermal, bandwidth)")
    ap.add_argument("--force", action="store_true", help="overwrite existing files")
    args = ap.parse_args()

    root = os.path.abspath(os.path.expanduser(args.path))
    date = _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%d")
    components = [c.strip() for c in args.components.split(",") if c.strip()]
    disciplines = [d.strip() for d in args.disciplines.split(",") if d.strip()]
    budgets = [b.strip() for b in args.budgets.split(",") if b.strip()]

    base = {"NAME": args.name, "DATE": date, "SLUG": slug(args.name)}
    created, skipped = [], []

    for d in ["docs/runbooks", "docs/checklists", "docs/reference", "docs/logs",
              "docs/records/invoices", "hardware/specs", "hardware/datasheets",
              "configs", "software", "firmware", "scripts", "images"]:
        os.makedirs(os.path.join(root, d), exist_ok=True)

    comp_rows = "\n".join("| %s | |" % c for c in components) or "| | |"
    bom_rows = "\n".join("| %d | %s | | 1 | | |" % (i + 1, c)
                         for i, c in enumerate(components)) or "| 1 | | | | | |"

    files = [
        ("README.md", "README.md.tmpl", {"COMPONENT_ROWS": comp_rows}),
        ("CLAUDE.md", "CLAUDE.md.tmpl", {}),
        ("TODO.md", "TODO.md.tmpl", {}),
        ("CHANGELOG.md", "CHANGELOG.md.tmpl", {}),
        ("docs/bill-of-materials.md", "bill-of-materials.md.tmpl", {"BOM_ROWS": bom_rows}),
        ("docs/accessories.md", "accessories.md.tmpl", {}),
        ("docs/records/order-and-warranty.md", "order-and-warranty.md.tmpl", {}),
        ("docs/checklists/inventory-and-inspection.md", "inventory-and-inspection.md.tmpl", {}),
        ("docs/checklists/bringup-tests.md", "bringup-tests.md.tmpl", {}),
        ("docs/logs/build-log.md", "build-log.md.tmpl", {}),
        ("docs/logs/known-issues.md", "known-issues.md.tmpl", {}),
        ("docs/logs/decisions.md", "decisions.md.tmpl", {}),
        ("docs/logs/firmware-versions.md", "firmware-versions.md.tmpl", {}),
        ("hardware/datasheets/README.md", "datasheets-readme.md.tmpl", {}),
        ("hardware/mechanical.md", "mechanical.md.tmpl", {}),
        ("docs/runbooks/TEMPLATE-runbook.md", "runbook.md.tmpl", {"TITLE": "<procedure>"}),
        ("configs/TEMPLATE-config-header.txt", "config-header.txt.tmpl", {}),
    ]
    for rel, tmpl, extra in files:
        mapping = dict(base)
        mapping.update(extra)
        write(os.path.join(root, rel), render(read_template(tmpl), mapping),
              args.force, created, skipped)

    for kind in budgets:
        mapping = dict(base)
        mapping["BUDGET_KIND"] = kind.capitalize()
        write(os.path.join(root, "docs/reference/%s-budget.md" % slug(kind)),
              render(read_template("budget.md.tmpl"), mapping), args.force, created, skipped)

    for comp in components:
        mapping = dict(base)
        mapping["COMPONENT"] = comp
        write(os.path.join(root, "hardware/specs/%s.md" % slug(comp)),
              render(read_template("spec-sheet.md.tmpl"), mapping), args.force, created, skipped)

    if disciplines:
        rows = "\n".join("| %s | [%s/](%s/README.md) |" % (d, d, d) for d in disciplines)
        mapping = dict(base)
        mapping["DISCIPLINE_ROWS"] = rows
        write(os.path.join(root, "knowledge/README.md"),
              render(read_template("knowledge-readme.md.tmpl"), mapping),
              args.force, created, skipped)
        write(os.path.join(root, "knowledge/_templates/finding.md"),
              render(read_template("finding.md.tmpl"), base), args.force, created, skipped)
        for disc in disciplines:
            mapping = dict(base)
            mapping["DISCIPLINE"] = disc
            write(os.path.join(root, "knowledge/%s/README.md" % disc),
                  render(read_template("discipline-readme.md.tmpl"), mapping),
                  args.force, created, skipped)
            for sub, desc in SUBDIR_DESC.items():
                m = dict(mapping)
                m["SUBDIR"] = sub
                m["SUBDIR_DESC"] = desc
                write(os.path.join(root, "knowledge/%s/%s/README.md" % (disc, sub)),
                      render(read_template("subdir-readme.md.tmpl"), m),
                      args.force, created, skipped)

    write(os.path.join(root, ".gitignore"), GITIGNORE, args.force, created, skipped)
    write(os.path.join(root, ".gitattributes"), GITATTRIBUTES, args.force, created, skipped)

    for tool in ("check_links.py", "audit.py"):
        src = os.path.join(HERE, tool)
        if os.path.exists(src):
            with open(src, encoding="utf-8") as fh:
                write(os.path.join(root, "scripts", tool), fh.read(),
                      args.force, created, skipped)

    print("Scaffolded %s" % root)
    print("  created: %d files" % len(created))
    if skipped:
        print("  skipped (already exist, use --force to overwrite): %d" % len(skipped))
        for p in skipped[:10]:
            print("    %s" % os.path.relpath(p, root))
    print("\nNext:")
    print("  1. Transcribe order line items verbatim into docs/records/invoices/")
    print("  2. Fill the BOM and accessory status list from those records")
    print("  3. Write spec sheets from datasheets and the vendor's own control software")
    print("  4. Build the conflict map, then stage the config fixes in configs/")
    print("  5. python3 scripts/audit.py .   before each commit")
    print("  6. git init && git add -A && git commit && gh repo create")
    return 0


if __name__ == "__main__":
    sys.exit(main())
