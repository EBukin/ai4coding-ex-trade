"""Build the farm-trade-support download for agentic exercise 1.

Replays the commit spec in _build/history/commits.py into a fresh Git
repository in a temporary folder, checks that the final `main` tree equals
_build/project/, and zips the project with its .git folder into
lessons/agentic-exercises/files/farm-trade-support.zip.

The course repository never holds a nested .git folder: the repository is
built in the system temp folder and only the zip is written here. The zip is
git-ignored. Runs as a Quarto pre-render script, on Windows and in Linux CI.
Needs Python (standard library only) and the git command line.

Determinism: identities, dates and messages come from the spec, and user and
system Git config are ignored, so the same input gives the same commit
hashes on every machine.

Run by hand from the repository root:
    python lessons/agentic-exercises/_build/build_history.py
"""

import difflib
import getpass
import hashlib
import os
import re
import runpy
import shutil
import stat
import subprocess
import sys
import tempfile
import zipfile
from datetime import datetime
from pathlib import Path

BUILD = Path(__file__).resolve().parent
ROOT = BUILD.parents[2]
PROJECT = BUILD / "project"
HISTORY = BUILD / "history"
OUT = BUILD.parent / "files" / "farm-trade-support.zip"
TOP = "farm-trade-support"
# Fixed zip timestamp, as in scripts/build_template_zip.py.
STAMP = (2026, 8, 14, 12, 0, 0)
BINARY = {".png", ".xlsx"}
# Words that must never appear in a commit message (no AI attribution).
BANNED = ["co-authored", "claude", "generated with", "chatgpt", "copilot"]
# Identity and date for every git call, so nothing git writes on its own
# (reflogs are off anyway) can fall back to the builder's name or clock.
BUILDER = ("Build", "build@example.org", "2026-08-14T12:00:00+00:00")


# ---- File contents ------------------------------------------------------------


def read(path):
    """File bytes; text files get LF line endings (a Windows checkout has CRLF)."""
    data = path.read_bytes()
    return data if path.suffix in BINARY else data.replace(b"\r\n", b"\n")


def final(rel):
    return read(PROJECT / rel)


def text(rel):
    return final(rel).decode("utf-8")


def cut(s, old, new=""):
    """Replace exactly one occurrence of `old`, or fail loudly."""
    if s.count(old) != 1:
        sys.exit(f"build_history: expected one match of {old[:60]!r}, found {s.count(old)}")
    return s.replace(old, new)


def cut_between(s, start, end, new=""):
    """Replace everything from `start` up to (not including) `end`."""
    i, j = s.index(start), s.index(end)
    return s[:i] + new + s[j:]


def drop_rows(s, prefix, n):
    """Drop the `n` lines that start with `prefix`."""
    lines = s.splitlines(keepends=True)
    kept = [x for x in lines if not x.startswith(prefix)]
    if len(lines) - len(kept) != n:
        sys.exit(f"build_history: expected {n} lines starting {prefix!r}")
    return "".join(kept)


def thousands(csv_bytes, column):
    """Earlier data version: `column` in thousand USD instead of USD."""
    lines = csv_bytes.decode("ascii").split("\n")
    k = lines[0].split(",").index(column)
    out = [lines[0]]
    for line in lines[1:]:
        if line:
            cells = line.split(",")
            v = int(cells[k])
            assert v % 1000 == 0, line
            cells[k] = str(v // 1000)
            line = ",".join(cells)
        out.append(line)
    return "\n".join(out).encode("ascii")


GUARD_SEM = """* Stop with a clear message if the prepared data are not in memory
capture confirm variable ln_output ln_subsidy ln_fert
if _rc {
    display as error "Run code/01_prepare.do first (or code/00_master.do)."
    exit 111
}

"""
GUARD_FIG = GUARD_SEM.replace(" ln_fert\n", "\n")
ROOT_CHECK = """* Stop early with a clear message if we are not in the project root
capture confirm file "data/clean/farm_support.csv"
if _rc {
    display as error "Run this file from the project root folder."
    exit 601
}

"""
WHO_NAMED = """| Role | Name | Works on |
|---|---|---|
| Team lead | Amina Haddad | README, data, merges |
| R analyst | Tomas Ferreira | Gravity model |
| Stata analyst | Grace Owusu | Subsidy pass-through |
| Python analyst | Mei Lin Tan | Bloc charts |
"""
WHO_ROLES = """| Role | Works on |
|---|---|
| Team lead | README, data, merges |
| R analyst | Gravity model |
| Stata analyst | Subsidy pass-through |
| Python analyst | Bloc charts |
"""
RUN_STUB = """## How to run

Each part gets a master script in `code/`: `00_master.py`, `00_master.R` and `00_master.do`.
Run it from the project root, the folder that holds this README.
Each analyst adds the run instructions for their part when their branch merges.

"""


def readme_v5():
    return cut(text("README.md"), WHO_NAMED, WHO_ROLES)


def readme_v4():
    s = drop_rows(readme_v5(), "| Stata | ", 4)
    s = cut(s, "- Stata 17 or later (optional)\n")
    s = cut(s, "All outputs are committed. If you do not have Stata or R, "
               "you can still see their results in `outputs/`.\n\n")
    return cut(s, "run one, two or all three.", "run one or both.")


def readme_v3():
    s = drop_rows(readme_v4(), "| Python | ", 5)
    s = cut(s, "- Python with `pandas` and `matplotlib`\n")
    return cut(s, "The parts are independent: run one or both.\n")


def readme_v2():
    s = cut_between(readme_v3(), "## How to run\n", "## Folder map\n", RUN_STUB)
    return cut_between(s, "## Outputs\n", "## Data sources\n")


def code_readme(*parts):
    head, *sections = text("code/README.md").split("\n## ")
    keep = [x for x in sections if x.split(":")[0] in parts]
    assert len(keep) == len(parts)
    return "\n## ".join([head] + keep)


def raw_readme_v1():
    s = cut(text("data/raw/README.md"), ", and the country size used to simulate\n"
            "  `farm_support.csv`.", ".")
    return cut(s, "\n## Synthetic data\n\n`farm_support.csv` is simulated, not "
               "downloaded. See `../clean/README.md`.\n")


def clean_readme_v2():
    return cut(text("data/clean/README.md"), " FAOSTAT values are in thousand US "
               "dollars; they\nare multiplied by 1,000 here.")


def clean_readme_v1():
    s = cut_between(clean_readme_v2(), "## `farm_support.csv` (SYNTHETIC)\n",
                    "## Sources and licences\n")
    return cut(s, "- `farm_support.csv` is synthetic. It has no source.\n")


def gravity_v3():
    s = cut(text("code/01_gravity.R"),
            "\n# Country-pair identifier (direction matters: USA->CAN differs from "
            "CAN->USA)\ntrade$pair <- paste(trade$exporter, trade$importer, sep = \"_\")\n")
    s = cut(s, "# Errors are clustered by country pair: flows of one pair are "
               "correlated\n# over time, and default (IID) standard errors are far "
               "too small here.\n")
    return cut(s, "  data = trade,\n  cluster = ~ pair\n)", "  data = trade\n)")


def sem_v2(number):
    s = cut(text("code/03_sem.do"), GUARD_SEM)
    return s if number == "03" else cut(s, "* 03_sem.do:", "* 02_sem.do:")


DERIVE = {
    "empty": lambda: "",
    "raw_readme_v1": raw_readme_v1,
    "clean_readme_v1": clean_readme_v1,
    "clean_readme_v2": clean_readme_v2,
    "gitignore_v2": lambda: cut(text(".gitignore"), "# Stata\n*.log\n*.smcl\n\n"),
    "farm_trade_v1": lambda: thousands(final("data/clean/farm_trade.csv"), "trade_usd"),
    "bloc_trade_v1": lambda: thousands(final("outputs/data/bloc_trade.csv"), "trade_usd"),
    "readme_v2": readme_v2,
    "readme_v3": readme_v3,
    "readme_v4": readme_v4,
    "readme_v5": readme_v5,
    "code_readme_v2": lambda: code_readme("R"),
    "code_readme_v3": lambda: code_readme("Python", "R"),
    "gravity_v3": gravity_v3,
    "sem_v2_as_02": lambda: sem_v2("02"),
    "sem_v2_as_03": lambda: sem_v2("03"),
    "figure_v1": lambda: cut(text("code/02_figure.do"), GUARD_FIG),
    "master_do_v3": lambda: cut(text("code/00_master.do"), ROOT_CHECK),
}


def content(path, source):
    if source == "project":
        return final(path)
    if source.startswith("files/"):
        return read(HISTORY / source)
    data = DERIVE[source.removeprefix("derive:")]()
    return data if isinstance(data, bytes) else data.encode("utf-8")


# ---- Replay the spec in memory -----------------------------------------------


def git_time(iso):
    """'2026-03-02T09:40:12+01:00' -> ('1772440812 +0100', local datetime)."""
    d = datetime.fromisoformat(iso)
    off = int(d.utcoffset().total_seconds() // 60)
    sign = "+" if off >= 0 else "-"
    return f"{int(d.timestamp())} {sign}{abs(off) // 60:02d}{abs(off) % 60:02d}", d


def ancestors(parents, c):
    seen, todo = set(), [c]
    while todo:
        x = todo.pop()
        if x not in seen:
            seen.add(x)
            todo.extend(parents[x])
    return seen


def merge_base(parents, a, b):
    common = ancestors(parents, a) & ancestors(parents, b)
    best = [c for c in common
            if not any(c != d and c in ancestors(parents, d) for d in common)]
    assert len(best) == 1, f"no unique merge base for {a} and {b}"
    return best[0]


def three_way(base, ours, theirs, label):
    out = {}
    for p in sorted(set(base) | set(ours) | set(theirs)):
        b, o, t = base.get(p), ours.get(p), theirs.get(p)
        v = o if o == t else t if o == b else o if t == b else ...
        if v is ...:
            sys.exit(f"build_history: merge conflict in {p} at {label}")
        if v is not None:
            out[p] = v
    return out


def replay(spec):
    """Check the spec and return commits with full trees, in order."""
    authors = spec["AUTHORS"]
    heads, trees, parents, out = {}, {}, {}, []
    for c in spec["COMMITS"]:
        cid, branch = c["id"], c["branch"]
        name, email = authors[c["author"]]
        assert email.endswith("@example.org"), email
        when, local = git_time(c["date"])
        if local.weekday() > 4 or not 8 <= local.hour < 19:
            sys.exit(f"build_history: {cid} is not in office hours on a weekday")
        if out and local <= datetime.fromisoformat(out[-1]["date"]):
            sys.exit(f"build_history: {cid} is not later than the commit before")
        msg = c["message"].strip() + "\n"
        if any(w in msg.lower() for w in BANNED) or " AI " in f" {msg} ":
            sys.exit(f"build_history: banned word in message of {cid}")
        if "from" in c:
            assert branch not in heads, f"{cid}: branch {branch} exists"
            first = [c["from"]]
        else:
            first = [heads[branch]] if branch in heads else []
        if "merge" in c:
            other = heads[c["merge"]]
            base = merge_base(parents, first[0], other)
            tree = three_way(trees[base], trees[first[0]], trees[other], cid)
            par = first + [other]
        else:
            tree = dict(trees[first[0]]) if first else {}
            for path, source in c["files"].items():
                if source is None:
                    del tree[path]
                else:
                    tree[path] = content(path, source)
            par = first
        if par and len(par) == 1 and tree == trees[par[0]]:
            sys.exit(f"build_history: {cid} changes nothing")
        trees[cid], parents[cid], heads[branch] = tree, par, cid
        out.append(dict(c, tree=tree, parents=par, who=f"{name} <{email}>",
                        when=when, msg=msg))
    return out, heads


# ---- Git ----------------------------------------------------------------------


def git_env(tmp):
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    empty = tmp / "empty.gitconfig"
    empty.write_text("")
    env.update(GIT_CONFIG_GLOBAL=str(empty), GIT_CONFIG_NOSYSTEM="1",
               GIT_TERMINAL_PROMPT="0", LC_ALL="C")
    name, email, date = BUILDER
    for who in ("AUTHOR", "COMMITTER"):
        env.update({f"GIT_{who}_NAME": name, f"GIT_{who}_EMAIL": email,
                    f"GIT_{who}_DATE": date})
    return env


def git(repo, env, *args, data=None, ok=(0,)):
    cmd = ["git", "-c", "core.autocrlf=false", "-c", "core.eol=lf",
           "-c", "core.safecrlf=false", "-c", "core.logAllRefUpdates=false",
           "-c", f"user.name={BUILDER[0]}", "-c", f"user.email={BUILDER[1]}",
           "-c", "commit.gpgsign=false", "-c", "core.filemode=false", *args]
    r = subprocess.run(cmd, cwd=repo, env=env, input=data, capture_output=True)
    if r.returncode not in ok:
        sys.exit(f"build_history: git {' '.join(args)} failed:\n"
                 f"{r.stderr.decode(errors='replace')}")
    return r.stdout


def fast_import_stream(commits):
    """One fast-import stream: every blob once, every commit with a full tree."""
    out, blobs, marks = [], {}, {}

    def data(b):
        out.append(b"data %d\n" % len(b) + b + b"\n")

    for c in commits:
        for b in c["tree"].values():
            if b not in blobs:
                blobs[b] = len(blobs) + 1
                out.append(b"blob\nmark :%d\n" % blobs[b])
                data(b)
    n = len(blobs)
    for c in commits:
        n += 1
        marks[c["id"]] = n
        out.append(f"commit refs/heads/{c['branch']}\nmark :{n}\n".encode())
        out.append(f"author {c['who']} {c['when']}\n".encode("utf-8"))
        out.append(f"committer {c['who']} {c['when']}\n".encode("utf-8"))
        data(c["msg"].encode("utf-8"))
        for i, p in enumerate(c["parents"]):
            out.append(f"{'from' if i == 0 else 'merge'} :{marks[p]}\n".encode())
        out.append(b"deleteall\n")
        for path in sorted(c["tree"]):
            out.append(f"M 100644 :{blobs[c['tree'][path]]} {path}\n".encode("utf-8"))
        out.append(b"\n")
    out.append(b"done\n")
    return b"".join(out)


# Reflogs stay on for learners: they are Git's undo history. The build itself
# runs with logAllRefUpdates off (see git()), and scrub() removes logs/.
CONFIG = """[core]
\trepositoryformatversion = 0
\tfilemode = false
\tbare = false
\tlogallrefupdates = true
"""


def blob_sha(b):
    return hashlib.sha1(b"blob %d\0" % len(b) + b).hexdigest()


def check_final(repo, env):
    """Fail with a diff unless main holds exactly the files in _build/project/."""
    files = sorted(p.relative_to(PROJECT).as_posix()
                   for p in PROJECT.rglob("*") if p.is_file())
    ignored = git(repo, env, "check-ignore", "--no-index", "-z", "--stdin",
                  data="\0".join(files).encode() + b"\0", ok=(0, 1))
    ignored = {x for x in ignored.decode().split("\0") if x}
    for x in sorted(ignored):
        print(f"build_history: skipping git-ignored project file {x}")
    want = {f: blob_sha(final(f)) for f in files if f not in ignored}
    have = {}
    for line in git(repo, env, "ls-tree", "-r", "-z", "main").decode().split("\0"):
        if line:
            meta, path = line.split("\t", 1)
            have[path] = meta.split()[2]
    if want == have:
        return
    report = []
    for p in sorted(set(want) | set(have)):
        if p not in have:
            report.append(f"missing from main: {p}")
        elif p not in want:
            report.append(f"extra on main: {p}")
        elif want[p] != have[p]:
            report.append(f"differs: {p}")
            if Path(p).suffix not in BINARY:
                old = git(repo, env, "cat-file", "blob", have[p]).decode().splitlines()
                new = final(p).decode().splitlines()
                report.extend(difflib.unified_diff(old, new, f"main:{p}",
                                                   f"project:{p}", lineterm=""))
    sys.exit("build_history: final main tree differs from _build/project/\n"
             + "\n".join(report))


def scrub(repo):
    """Remove files in .git that git does not need and that may name the builder."""
    git_dir = repo / ".git"
    for name in ("logs", "hooks"):
        if (git_dir / name).exists():
            shutil.rmtree(git_dir / name)
    for name in ("description", "FETCH_HEAD", "ORIG_HEAD", "COMMIT_EDITMSG"):
        (git_dir / name).unlink(missing_ok=True)
    (git_dir / "config").write_bytes(CONFIG.encode())


EMAIL = re.compile(rb"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")
# Public addresses the project files cite on purpose: the World Bank template
# README names the Open Source Program Office.
PUBLIC_EMAILS = {b"github@worldbank.org"}


def leak_check(repo, env):
    """Fail if the built .git holds a real email, the builder's name or home.

    Pack files are compressed, so the objects are read through `git cat-file`:
    every commit, tree and blob, decompressed."""
    words = {str(Path.home()).lower(), str(Path.home()).lower().replace("\\", "/")}
    try:
        user = getpass.getuser().lower()
    except Exception:  # some containers have no user name
        user = ""
    if len(user) >= 4:  # a very short name would match by chance
        words.add(user)
    git_dir = repo / ".git"
    sources = [(f.relative_to(git_dir).as_posix(), f.read_bytes())
               for f in sorted(git_dir.rglob("*"))
               if f.is_file() and not f.relative_to(git_dir).as_posix().startswith("objects/")]
    sources.append(("objects", git(repo, env, "cat-file", "--batch-all-objects", "--batch")))
    bad = []
    for rel, data in sources:
        bad += [f"{rel}: {w}" for w in sorted(words) if w.encode() in data.lower()]
        bad += [f"{rel}: {m.decode(errors='replace')}" for m in sorted(set(EMAIL.findall(data)))
                if not m.endswith(b"@example.org") and m not in PUBLIC_EMAILS]
    idents = git(repo, env, "log", "--all", "--format=%an %ae %cn %ce").decode()
    for line in sorted(set(idents.splitlines())):
        emails = [w for w in line.split() if "@" in w]
        if (any(w in line.lower() for w in words)
                or any(not e.endswith("@example.org") for e in emails)):
            bad.append(f"git log: {line}")
    if bad:
        sys.exit("build_history: the built .git may identify the builder:\n"
                 + "\n".join(bad))


def zip_repo(repo):
    def entry(path, is_dir):
        rel = path.relative_to(repo).as_posix()
        name = TOP if rel == "." else f"{TOP}/{rel}"
        info = zipfile.ZipInfo(name + ("/" if is_dir else ""), STAMP)
        info.external_attr = (0o40755 << 16 | 0x10) if is_dir else (0o100644 << 16)
        info.compress_type = zipfile.ZIP_DEFLATED
        return info

    OUT.parent.mkdir(parents=True, exist_ok=True)
    tmp_out = OUT.with_suffix(".zip.tmp")
    paths = sorted(repo.rglob("*"), key=lambda p: p.relative_to(repo).as_posix())
    with zipfile.ZipFile(tmp_out, "w") as z:
        z.writestr(entry(repo, True), b"")
        for p in paths:
            z.writestr(entry(p, p.is_dir()), b"" if p.is_dir() else p.read_bytes())
    os.replace(tmp_out, OUT)


def remove_readonly(func, path, _):
    os.chmod(path, stat.S_IWRITE)  # Git pack files are read-only on Windows
    func(path)


def main():
    spec = runpy.run_path(str(HISTORY / "commits.py"))
    commits, heads = replay(spec)
    tmp = Path(tempfile.mkdtemp(prefix="farm-trade-history-"))
    try:
        env = git_env(tmp)
        repo = tmp / TOP
        git(tmp, env, "init", "-q", "--template=", "-b", "main", str(repo))
        (repo / ".git" / "config").write_text(CONFIG)
        git(repo, env, "fast-import", "--quiet", "--done",
            data=fast_import_stream(commits))
        git(repo, env, "checkout", "-q", "-f", "main")
        check_final(repo, env)
        scrub(repo)
        leak_check(repo, env)
        if git(repo, env, "status", "--porcelain", "--untracked-files=all"):
            sys.exit("build_history: working tree is not clean after checkout")
        zip_repo(repo)
        head = git(repo, env, "rev-parse", "main").decode().strip()
    finally:
        if sys.version_info >= (3, 12):
            shutil.rmtree(tmp, onexc=remove_readonly)
        else:
            shutil.rmtree(tmp, onerror=remove_readonly)
    merges = sum(len(c["parents"]) > 1 for c in commits)
    print(f"wrote {OUT.relative_to(ROOT).as_posix()}: {len(commits)} commits, "
          f"{merges} merges, {len(heads)} branches, main {head[:12]}")


if __name__ == "__main__":
    main()
