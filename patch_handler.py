"""
Patch the runpod-worker-comfyui handler to support VHS video (gifs) output
and to handle S3 upload failures gracefully.

VHS_VideoCombine saves the MP4 and stores it under the 'gifs' key in the
ComfyUI history. The base worker only processes 'images' outputs, so the
generated video is silently discarded. This patch makes the worker treat
'gifs' the same as 'images': fetch the file from ComfyUI and return it.

S3 fallback: If the worker's BUCKET_ENDPOINT_URL is misconfigured (wrong
bucket name, missing bucket, etc.) the upload fails and the job returns no
output, causing the generation to fail on the backend. The fallback patch
wraps the S3 upload in a try/except so that on failure the file is returned
as base64 in the output instead — the backend's _extract_video_bytes already
handles both URL and base64 formats.
"""
import os
import sys
import glob

# Locate the handler file (path varies across worker versions)
candidates = [
    "/src/rp_handler.py",
    "/app/src/rp_handler.py",
    "/handler.py",
]
candidates += glob.glob("/opt/venv/lib/*/site-packages/*comfy*/rp_handler.py")
candidates += glob.glob("/opt/venv/lib/*/site-packages/*comfy*/handler.py")

handler_path = next((p for p in candidates if os.path.exists(p)), None)
if not handler_path:
    print("WARNING: Could not locate handler file — skipping patch")
    sys.exit(0)

print(f"Patching handler at: {handler_path}")
with open(handler_path) as f:
    src = f.read()

already_patched = '"gifs"' in src or "'gifs'" in src

patched = src

# ── Gifs / VHS output patches ────────────────────────────────────────────────

if not already_patched:
    # Pattern A: key == "images"  — handler iterates node output keys (double quotes)
    if 'key == "images"' in patched:
        patched = patched.replace(
            'key == "images"',
            'key in ("images", "gifs")',
        )
        print("Applied pattern A: key == images -> key in (images, gifs)")

    # Pattern A2: key == 'images'  — single quotes variant
    if "key == 'images'" in patched:
        patched = patched.replace(
            "key == 'images'",
            "key in ('images', 'gifs')",
        )
        print("Applied pattern A2: key == 'images' -> key in ('images', 'gifs')")

    # Pattern B: if "images" in node_output:  — double quotes
    if '"images" in node_output' in patched:
        patched = patched.replace(
            '"images" in node_output',
            'bool(set(node_output.keys()) & {"images", "gifs"})',
        )
        print('Applied pattern B: "images" in node_output -> set intersection')

    # Pattern B2: if 'images' in node_output:  — single quotes
    if "'images' in node_output" in patched:
        patched = patched.replace(
            "'images' in node_output",
            "bool(set(node_output.keys()) & {'images', 'gifs'})",
        )
        print("Applied pattern B2: 'images' in node_output -> set intersection")

    # Pattern C: node_output["images"]  — direct key access (double quotes)
    if 'node_output["images"]' in patched:
        patched = patched.replace(
            'node_output["images"]',
            'node_output.get("images", node_output.get("gifs", []))',
        )
        print('Applied pattern C: node_output["images"] -> get with gifs fallback')

    # Pattern C2: node_output['images']  — direct key access (single quotes)
    if "node_output['images']" in patched:
        patched = patched.replace(
            "node_output['images']",
            "node_output.get('images', node_output.get('gifs', []))",
        )
        print("Applied pattern C2: node_output['images'] -> get with gifs fallback")

    if patched == src:
        print("WARNING: No gifs patch patterns matched — handler structure differs from expected")
else:
    print("Handler already supports gifs output — skipping gifs patch")

# ── S3 upload failure → base64 fallback patch ─────────────────────────────────
# When BUCKET_ENDPOINT_URL is set but has a wrong bucket name (e.g. "02-26"),
# the S3 PutObject call raises NoSuchBucket and the job returns no output.
# We wrap the upload so on any S3 exception the file is base64-encoded and
# included directly in the output — the backend handles both formats.

# Pattern S1: rp_upload_image raises on S3 error (common in v5.x)
# The function typically ends with: return {"image": b64, ...} or raises.
# We target the specific boto3 put_object call pattern.
_s3_raise_pattern = (
    "            raise\n"
    "        except Exception as e:\n"
    "            raise"
)
_s3_fallback = (
    "            import base64 as _b64\n"
    "            logging.warning(f\"S3 upload failed ({e}); falling back to base64 output\")\n"
    "            with open(tmp_file, 'rb') as _f:\n"
    "                return {\"image\": _b64.b64encode(_f.read()).decode()}\n"
    "        except Exception as e:\n"
    "            import base64 as _b64\n"
    "            logging.warning(f\"S3 upload failed ({e}); falling back to base64 output\")\n"
    "            with open(tmp_file, 'rb') as _f:\n"
    "                return {\"image\": _b64.b64encode(_f.read()).decode()}"
)
if _s3_raise_pattern in patched:
    patched = patched.replace(_s3_raise_pattern, _s3_fallback, 1)
    print("Applied pattern S1: S3 upload raise -> base64 fallback")

# Pattern S2: simpler single-raise S3 error block
_s3_raise_simple = (
    "        except ClientError as e:\n"
    "            raise\n"
)
_s3_fallback_simple = (
    "        except ClientError as e:\n"
    "            import base64 as _b64\n"
    "            logging.warning(f\"S3 upload failed ({e}); falling back to base64 output\")\n"
    "            if 'tmp_file' in dir() and os.path.exists(tmp_file):\n"
    "                with open(tmp_file, 'rb') as _f:\n"
    "                    return {\"image\": _b64.b64encode(_f.read()).decode()}\n"
    "            return None\n"
)
if _s3_raise_simple in patched:
    patched = patched.replace(_s3_raise_simple, _s3_fallback_simple, 1)
    print("Applied pattern S2: ClientError raise -> base64 fallback")

# ── WebSocket polling interval patch ─────────────────────────────────────────
# The 40-second gap before generation progress appears is ComfyUI's
# preprocessing time (CLIP encode + image VAE encode + WAN 2.2 setup).
# The handler logs "Websocket receive timed out. Still waiting..." on each
# polling cycle. Increasing the default interval from 10 s to 60 s reduces
# the noise from 4 messages to 1 while waiting for the model to start.
#
# The ENV COMFY_POLLING_INTERVAL_MS=60000 in the Dockerfile handles this at
# the env-var level; these patterns are a belt-and-suspenders fallback for
# handler versions that hardcode the interval.

# Pattern W1: default 10-second timeout (integer seconds)
for _ws_old, _ws_new in [
    ('os.environ.get("COMFY_POLLING_INTERVAL_MS", 10)', 'os.environ.get("COMFY_POLLING_INTERVAL_MS", 60)'),
    ("os.environ.get('COMFY_POLLING_INTERVAL_MS', 10)", "os.environ.get('COMFY_POLLING_INTERVAL_MS', 60)"),
    # millisecond variants
    ('os.environ.get("COMFY_POLLING_INTERVAL_MS", "10000")', 'os.environ.get("COMFY_POLLING_INTERVAL_MS", "60000")'),
    ("os.environ.get('COMFY_POLLING_INTERVAL_MS', '10000')", "os.environ.get('COMFY_POLLING_INTERVAL_MS', '60000')"),
    ('os.environ.get("COMFY_POLLING_INTERVAL_MS", 10000)', 'os.environ.get("COMFY_POLLING_INTERVAL_MS", 60000)'),
    ("os.environ.get('COMFY_POLLING_INTERVAL_MS', 10000)", "os.environ.get('COMFY_POLLING_INTERVAL_MS', 60000)"),
]:
    if _ws_old in patched:
        patched = patched.replace(_ws_old, _ws_new)
        print(f"Applied WebSocket polling interval patch: {_ws_old!r} -> {_ws_new!r}")

# ── Write patched handler ─────────────────────────────────────────────────────

if patched == src:
    print("WARNING: No patch patterns matched — handler structure differs from expected")
    sys.exit(0)

with open(handler_path, "w") as f:
    f.write(patched)
print("Handler patched successfully")
