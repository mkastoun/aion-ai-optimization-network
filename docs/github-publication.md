# Review and publish the experimental preview

No remote repository, push, tag or PyPI publication is performed by release
preparation. Version remains `0.6.0.dev0`. There was no Git history or remote
before this task; only local Git initialization is authorized here.

## Owner checks before publication

Review [release readiness](release-readiness.md), the full changed-file list and
the intended public tree. Confirm the existing MIT license and your authority to
license all contributions. The existing `AION contributors` copyright notice
does not authenticate ownership. No vendored third-party implementation was
identified; Python development dependencies and external LLVM tools retain their
own licenses and are not redistributed as AION source. Do not replace MIT or
invent copyright holders without owner direction.

Provide private security/conduct contacts, enable private vulnerability reporting
where available, and review repository settings. No email/username/URL is invented
in this checkout. There are no claimed successful CI or M4 results.

The current-tree pattern audit cannot prove the absence of every secret or
establish ownership. Ignoring files does not remove existing tracked data or
history. If a real credential is discovered in history, stop, revoke/rotate it,
and agree on remediation; do not silently rewrite history.

## Local review and initial commit

From the checkout, with the development venv activated:

```bash
git status
git status --ignored=matching
git ls-files
git log --oneline -5  # An unborn repository has no log yet.
python tools/public_audit.py --output .aion/release-readiness/public-audit.json
git diff --check
git diff --cached --check
```

Review the manifest and every finding. The tool scans tracked files even if they
now match an ignore pattern, plus untracked nonignored files. Findings contain
only kind/path/line, not credential values. No history existed in this checkout;
the tool explicitly warns that any later existing history needs separate audit.
Keep `.aion/`, environments, PGO/binaries, keys and local configs on disk but out
of Git. The public audit must pass before staging/committing.

After owner review, these commands stage only the intended project categories:

```bash
git add -- .gitattributes .gitignore .github README.md ROADMAP.md LICENSE \
  CONTRIBUTING.md SECURITY.md CODE_OF_CONDUCT.md CHANGELOG.md MANIFEST.in \
  pyproject.toml src tests tools docs
git diff --cached --check
git diff --cached --stat
python tools/public_audit.py --output .aion/release-readiness/public-audit-staged.json
git commit -m "Prepare AION 0.6 MVP Preview for public review"
```

Configure your own Git identity if Git requests it. Do not fabricate an author.
Keep existing history/remotes if these instructions are used on a later checkout.

## Create and push only when authorized

Use the official GitHub CLI if installed and authenticated. Read the actual
chosen owner/repository name; no sample username is asserted to exist.
The following commands are for the owner to run after the checks above:

```bash
gh auth login
read -r -p 'GitHub OWNER/REPOSITORY: ' AION_GITHUB_REPOSITORY
git remote -v
# Only for a new repository with no origin:
gh repo create "$AION_GITHUB_REPOSITORY" --public --source=. --remote=origin
git push -u origin main
```

These publication examples use bash. On zsh use
`read -r 'AION_GITHUB_REPOSITORY?GitHub OWNER/REPOSITORY: '` for the prompt.
If you create an empty repository through the GitHub website instead, copy its
verified clone URL and use this alternative (not both remote-creation methods):

```bash
read -r -p 'Verified clone URL: ' AION_REPOSITORY_URL
git remote add origin "$AION_REPOSITORY_URL"
git push -u origin main
```

If `origin` already exists, inspect and preserve it; do not overwrite it using
these examples. No force push, release tag or package upload is needed for this
experimental source preview. Once GitHub Actions actually runs, inspect each
platform's logs/artifacts before claiming compatibility.

## Clone on M4

Use the actual published clone URL and follow the exact commands in
[the Apple Silicon guide](install-macos-apple-silicon.md). It includes native
architecture checks, Homebrew LLVM 18, tests, the real demonstration and a clean
outside-checkout wheel smoke. Actual Apple M4 validation remains pending until
those commands execute successfully on that hardware.
