# Pull request CI and merge protection

`.github/workflows/ci.yml` runs for every pull request targeting `main` or
`develop`, every push to either branch, and merge-queue groups targeting `main`.
It can also be run manually after the workflow is on the default branch.

## Required check

The stable check name is **`Required CI`**, produced by GitHub Actions. It only
passes after all of these jobs succeed:

- Complete Django tests on Python 3.11 with in-memory SQLite.
- Complete Django tests on Python 3.11 with a disposable PostgreSQL 17 service.
- Dependency validation, Django system checks, migration consistency, migration
  application, and static-file collection for both database configurations.
- A Linux/amd64 deployment-image build and an isolated container smoke check of
  dependencies, excluded environment files, IP-based health probes, collected
  CSS, and the inbound webhook route.

The final job runs even when an earlier job fails, is cancelled, or is skipped;
it succeeds only when both database tests and the container job succeeded. There
are no file-path filters or draft-PR exclusions that could leave a required check
missing. New commits to a pull request automatically cancel the older run.

All CI credentials and keys are disposable test values. The workflow uses a
read-only GitHub token, does not receive production secrets, and uses the
in-memory mail backend. Resend/Turnstile tests mock external API calls. The
container smoke check runs without network access. The workflow tests deployment
readiness; production migration, image publishing, and Lightsail deployment use
the existing manual process.

## Main merge rule

Configure `main` to require:

1. A pull request before changes are merged.
2. Successful **`Required CI`** from the **GitHub Actions** app.
3. The branch to be up to date with `main` before merging.
4. Enforcement for repository administrators as well.

No reviewer approvals are required by this CI policy. The repository owner can
merge their own PR once tests pass and the branch is up to date. The status-check
name must stay `Required CI` unless the GitHub branch rule is updated together
with the workflow. A failed, cancelled, missing, or still-running check prevents
merging. Force pushes and deletion of `main` remain disallowed.

To inspect the setting in GitHub, open **Settings → Branches → Branch protection
rules → main**. Check **Require a pull request before merging**, **Require status
checks to pass before merging**, choose **Required CI** with GitHub Actions as the
source, enable **Require branches to be up to date before merging**, and enable
**Do not allow bypassing the above settings**.

The newest app currently develops on `develop`; `main` is an older release.
Merge the CI setup into the selected integration branch, then bring the workflow
to `main` through a passing pull request. New feature branches created from
`main` will inherit it afterward. Older branches must include this workflow to
produce the required check. Checks also run on `develop` PRs, but the required
merge rule described here targets `main`.

## What to do when CI fails

Open the pull request's **Checks** tab and select the failed job/step. Fix the
failure on the feature branch and push another commit; GitHub reruns CI. If
`main` changed after the tests passed, update the feature branch with the current
`main` and wait for the new run. Do not bypass the required check.

The repository must contain all runtime modules and migrations referenced by
settings and URLs. CI checks out Git-tracked files into a fresh runner; local
untracked modules cannot make a broken commit pass remotely.

## Local checks

For quick SQLite validation with no production settings:

```sh
PYTHON_DOTENV_DISABLED=1 SECRET_KEY=ci-only-dummy-key \
DATABASE_URL=sqlite:///:memory: DEBUG=False \
EMAIL_BACKEND=django.core.mail.backends.locmem.EmailBackend \
./.venv/bin/python manage.py test --noinput
```

For the image checks:

```sh
docker build --platform linux/amd64 --tag kona-swim-hub:ci .
docker run --rm --network none --read-only --tmpfs /tmp \
  --env PYTHON_DOTENV_DISABLED=1 --env SECRET_KEY=ci-container-dummy-key \
  --env DATABASE_URL=sqlite:///:memory: --env DEBUG=False \
  --env EMAIL_BACKEND=django.core.mail.backends.locmem.EmailBackend \
  kona-swim-hub:ci python scripts/ci_container_smoke.py
```

Use a separate disposable PostgreSQL database to reproduce that matrix job
locally. The CI service's `kona_ci` database and dummy password are created only
inside its runner; never point these checks at the production database.

## References

- [GitHub required status checks](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches#require-status-checks-before-merging)
- [GitHub workflow syntax](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax)
