#!/bin/bash
# Entrypoint wrapper for the RunPod T2I worker.
# Downloads any missing models from HuggingFace to the Network Volume,
# then hands off to the base image's /start.sh.

mkdir -p /runpod-volume/models

echo "=== Checking/downloading T2I models to network volume ==="
/download_models.sh
echo "=== Starting worker ==="
exec /start.sh
