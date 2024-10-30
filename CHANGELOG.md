## 0.1.2 (2024-10-29)

### Maintenance

- support node v22, warn on v18 (#4644)
- Bump cryptography from 42.0.7 to 43.0.1 in the pip

## 0.1.1 (2024-06-28)

### Maintenance

- use correct audit step name
- switch to ci boot
- fix production release
- add release workflow, wait for certain passes

## 0.1.0 (2024-06-21)

### Added

- save build container metrics to API
- Add dev deployment env for PRs to staging
- Switch to using harden container for cf-image

### Fixed

- Decrypt predefined keys in build params
- Run build CalledProcessError exception
- remove puts to git-resource in ci pipeline
- install required usg dependencies
- node 16 temporarily allowed
- Add additional lib deps for site builds
- Remove stack param since it is docker image
- Update tests to account for request timeout kwarg addition
- Add timeout to requests based on bandit findings
- CI slack emoji for successful nightly restage
- CI pipeline to properly use src input for nightly rebuild
- Update tests with additional mock calls
- Remove f-string for gem update command

### Performance

- run uploader task in threads

### Maintenance

- update docs, drop nightly restage
- use correct input pipeline names
- use pipeline tasks, use pr/main/tag release
- Bump requests to v2.32.3
- Add decrypt to build site params
- Enable Dependabot security scanning (#458)
- container hardening
- Add dependency auditing with pip-audit (#458)
- **ci**: Switch to general-task and registry-image for CI jobs
- Add hardened git resource
- Simplify CI notifications from task hooks
- Update resource types and python deps to use hardened images
- Adjust for Github GPG token expiration
- don't build node 16
- default to node 18 (#437)
- Update app stack to cflinuxfs4
- Add gem update --system for Jekyll builds
