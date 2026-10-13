"""The kit's own tests always run as outside CI (change 008): in CI, the kit reads the pull request's base from
these variables, which would leak into the temporary repositories the tests build."""
import os

for _name in ("GITHUB_EVENT_PATH", "GITHUB_BASE_REF"):
    os.environ.pop(_name, None)
