"""Check the vendored core is the recorded, unmodified upstream file. Offline.
Run: python tests/vendored_core.py"""
import hashlib, os, re
here = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "plugin", "agent_sandbox_backend", "_vendor")
data = open(os.path.join(here, "agent_sandbox", "core.py"), "rb").read()
blob = hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest()
want = re.search(r"git blob sha1: ([0-9a-f]{40})", open(os.path.join(here, "VENDORED.md")).read()).group(1)
assert blob == want, f"vendored core.py {blob} != recorded {want}"
assert b"from tools." not in data and b"hermes_" not in data, "core must not import Hermes"
print("vendored core ok", blob[:12])
