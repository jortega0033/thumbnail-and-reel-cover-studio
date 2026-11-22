# Security policy

## Supported versions

Only the default branch (`main`) is supported. Fixes land there.

## Reporting a vulnerability

Report it privately through GitHub: open the repository's **Security** tab and choose **Report a vulnerability** (private vulnerability reporting). Do not open a public issue or pull request for a vulnerability.

Include the affected file or route, the steps to reproduce, and the effect you expect an attacker to get. The server binds `127.0.0.1` only and has no accounts, so the most relevant reports are Host or Origin check bypasses, path traversal through the static file whitelist, SQL injection, and user text reaching the page as markup.
