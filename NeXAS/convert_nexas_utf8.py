import pathlib
import re

ROOT = pathlib.Path(".").resolve()
SLN = ROOT / "NexAS.sln"

SOURCE_EXTS = {".c", ".cpp", ".h", ".hpp"}

DECODE_ORDER = (
    "cp936",   # Simplified Chinese (GB2312 / GBK) – primary
    "cp932",   # Japanese Shift-JIS – fallback
    "utf-8",   # already UTF-8
)

def extract_projects(sln_path):
    projects = []
    pattern = re.compile(r'Project\(".*?"\)\s*=\s*".*?",\s*"(.*?)"')
    for line in sln_path.read_text(errors="ignore").splitlines():
        m = pattern.search(line)
        if m:
            proj_path = (sln_path.parent / m.group(1)).resolve()
            if proj_path.exists():
                projects.append(proj_path)
    return projects

def extract_sources(proj_path):
    text = proj_path.read_text(errors="ignore")
    files = set()
    for m in re.finditer(r'Include="([^"]+)"', text):
        p = (proj_path.parent / m.group(1)).resolve()
        if p.suffix.lower() in SOURCE_EXTS and p.exists():
            files.add(p)
    return files

def decode_bytes(raw):
    for enc in DECODE_ORDER:
        try:
            return raw.decode(enc), enc
        except UnicodeDecodeError:
            continue
    return None, None

def convert_file(path):
    raw = path.read_bytes()
    text, enc = decode_bytes(raw)
    if text is None:
        print(f"[skip] undecodable: {path}")
        return
    path.write_text(text, encoding="utf-8-sig")
    print(f"[ok] {path.relative_to(ROOT)} ({enc} → utf-8)")

def main():
    if not SLN.exists():
        raise SystemExit("NexAS.sln not found – run this next to the solution file")

    projects = extract_projects(SLN)
    if not projects:
        raise SystemExit("No projects found in solution")

    sources = set()
    for proj in projects:
        sources |= extract_sources(proj)

    if not sources:
        raise SystemExit("No source files found")

    print(f"Converting {len(sources)} files to UTF-8...")
    for f in sorted(sources):
        convert_file(f)

if __name__ == "__main__":
    main()
