# Security policy

AION is an experimental local research tool. Only run trusted bundled workloads
and reviewed trusted catalog definitions. Compilation and execution are **not a
sandbox for arbitrary or hostile source code**. Compiler plugins, arbitrary
recipes, shell commands and model-generated source are outside the proposal
interface. Process limits reduce resource use; they do not isolate filesystem,
network or user privileges.

Version `0.6.0.dev0` is a pre-release. There is no support or response-time
guarantee. Fixes are prepared against the current development tree.

Do not post credentials, source you cannot disclose, private paths or raw local
reports in a public issue. Reports may contain command arguments, paths, host
observations and process output. Review and redact them before sharing.

For a suspected vulnerability, use GitHub's **Report a vulnerability** on the
eventual repository if private reporting has been enabled, or a private contact
explicitly provided by its maintainer. No private reporting endpoint or security
email has been configured in this local checkout. If neither channel exists,
open a public issue requesting a private contact without exploit details.

Before publication, the repository owner should enable private vulnerability
reporting, secret scanning where available, branch protection and human review.
Never include real secrets in tests. If a credential entered Git history, stop,
revoke/rotate it and agree on remediation; ignoring the file does not remove it
from existing history. Do not silently rewrite history.
