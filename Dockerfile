FROM runpod/worker-comfyui:5.5.1-base

# Disable torch.compile (dynamo) to prevent FP8 Triton kernel compilation errors
ENV TORCHDYNAMO_DISABLE=1

# T2I uses only standard ComfyUI nodes — no custom nodes required.
# (CheckpointLoaderSimple, CLIPTextEncode, KSampler, VAEDecode,
#  LoraLoaderModelOnly, CLIPSetLastLayer, SaveImage are all built-in)

# Patch the worker handler for S3 fallback to base64 on upload failures.
COPY patch_handler.py /tmp/patch_handler.py
RUN python3 /tmp/patch_handler.py

# Model download startup script — models live on a RunPod Network Volume
# mounted at /runpod-volume. The script is idempotent: fast no-op if files exist.
COPY download_models.sh /download_models.sh
RUN chmod +x /download_models.sh

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

CMD ["/entrypoint.sh"]
