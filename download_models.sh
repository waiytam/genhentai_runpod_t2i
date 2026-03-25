#!/bin/bash
# Download T2I models to the RunPod Network Volume if not already present.
# Idempotent: re-running on an already-populated volume is a fast no-op.
set -e

MODELS_DIR="/runpod-volume/models"
CKPT_DIR="$MODELS_DIR/checkpoints"
LORA_DIR="$MODELS_DIR/loras"

HF_BASE="https://huggingface.co/waiytam/genhentai-lora-t2i/resolve/main"

download_if_missing() {
  local dest="$1"
  local url="$2"
  if [ ! -f "$dest" ]; then
    echo "Downloading $(basename "$dest")..."
    mkdir -p "$(dirname "$dest")"
    if [ -n "$HF_TOKEN" ]; then
      wget -q --show-progress --header="Authorization: Bearer $HF_TOKEN" -O "$dest" "$url" \
        || { echo "FAILED: $url"; rm -f "$dest"; }
    else
      wget -q --show-progress -O "$dest" "$url" \
        || { echo "FAILED: $url"; rm -f "$dest"; }
    fi
  else
    echo "Already present: $(basename "$dest")"
  fi
}

# ── Checkpoints ───────────────────────────────────────────────────────────────

for f in \
  "IL-akiumLumenILLBase_baseV3.safetensors" \
  "IL-dessertModels_eclair.safetensors" \
  "IL-dessertModels_gelato.safetensors" \
  "IL-divingIllustriousReal_v70VAE.safetensors" \
  "IL-excelaxl_20251018b.safetensors" \
  "IL-hassakuXLIllustrious_v34.safetensors" \
  "IL-hyphoriaIlluNAI_v001.safetensors" \
  "IL-pieModels_blueberryPie.safetensors" \
  "IL-pleasurechest_v2.safetensors" \
  "IL-prefectiousXLNSFW_v10.safetensors" \
  "IL-REALISMVirtual_v35.safetensors" \
  "IL-semiRealIllustrious_v20.safetensors"; do
  download_if_missing "$CKPT_DIR/$f" "$HF_BASE/$f"
done

# ── LoRAs ─────────────────────────────────────────────────────────────────────

# Standard filenames (URL-safe)
for f in \
  "IL-DetailerILv2-000008.safetensors" \
  "IL-ATRex_style-12.safetensors" \
  "IL-ThickOutline.safetensors" \
  "IL-Thick_Lines_-_Illustrious-000010.safetensors" \
  "IL-Realim_Lora_BSY_IL_V1_RA42.safetensors" \
  "Pony-Beautiful_Girls_V4.safetensors" \
  "IL-Western_Comic_Art_Style_ILLUSTRIOUS_XL_by_UOC.safetensors" \
  "IL-SethxZoeIllust.safetensors" \
  "IL-satouKuukiXL_il_lokr_V6311P.safetensors" \
  "IL-kccccXL_il_lokr_V531.safetensors" \
  "IL-IckpotIXL_v1.safetensors" \
  "IL-jimaXL_il_lokr_V53P1.safetensors" \
  "IL-blackedgens-koto-illustrious.safetensors" \
  "IL-cunnyFunkyXL_il1_lokr_V6311P.safetensors" \
  "IL-thiccwithaq-artist-richy-v1_ixl.safetensors" \
  "IL-retro_scifi_artstyle_illustriousXL-000021.safetensors"; do
  download_if_missing "$LORA_DIR/$f" "$HF_BASE/$f"
done

# Filenames with spaces (must be quoted in dest path, URL-encoded in URL)
download_if_missing "$LORA_DIR/IL-Ani-B - Basic [LoRA] - Illustrious-XL v0.1.safetensors" \
  "$HF_BASE/IL-Ani-B%20-%20Basic%20%5BLoRA%5D%20-%20Illustrious-XL%20v0.1.safetensors"

download_if_missing "$LORA_DIR/IL-[NoodleNood] Assorted Doujin Style Blend Illustrious.safetensors" \
  "$HF_BASE/IL-%5BNoodleNood%5D%20Assorted%20Doujin%20Style%20Blend%20Illustrious.safetensors"

download_if_missing "$LORA_DIR/IL-Traditional Ink Painting [LoRA] - Illustrious-XL v0.1.safetensors" \
  "$HF_BASE/IL-Traditional%20Ink%20Painting%20%5BLoRA%5D%20-%20Illustrious-XL%20v0.1.safetensors"

download_if_missing "$LORA_DIR/IL-Watercolor Realistic [LoRA] - Illustrious-XL v0.1.safetensors" \
  "$HF_BASE/IL-Watercolor%20Realistic%20%5BLoRA%5D%20-%20Illustrious-XL%20v0.1.safetensors"

download_if_missing "$LORA_DIR/IL-Watercolor Anime [LoRA] - Illustrious-XL v0.1.safetensors" \
  "$HF_BASE/IL-Watercolor%20Anime%20%5BLoRA%5D%20-%20Illustrious-XL%20v0.1.safetensors"

download_if_missing "$LORA_DIR/IL-[WAI][Style]Asanagi-figure-20.safetensors" \
  "$HF_BASE/IL-%5BWAI%5D%5BStyle%5DAsanagi-figure-20.safetensors"

download_if_missing "$LORA_DIR/IL-S1 Dramatic Lighting Illustrious_V2.safetensors" \
  "$HF_BASE/IL-S1%20Dramatic%20Lighting%20Illustrious_V2.safetensors"

download_if_missing "$LORA_DIR/IL-tonton shuicai Illustrious-XL.safetensors" \
  "$HF_BASE/IL-tonton%20shuicai%20Illustrious-XL.safetensors"

download_if_missing "$LORA_DIR/IL-shC398nE79EAC.mcat.safetensors" \
  "$HF_BASE/IL-shC398nE79EAC.mcat.safetensors"

# Japanese filename LoRA (special percent-encoded URL provided by user)
download_if_missing "$LORA_DIR/IL-AIイラストおじさん_V3-Exp-Compact.safetensors" \
  "https://huggingface.co/waiytam/genhentai-lora-t2i/resolve/main/IL-AI%E3%82%A4%E3%83%A9%E3%82%B9%E3%83%88%E3%81%8A%E3%81%97%E3%82%99%E3%81%95%E3%82%93_V3-Exp-Compact.safetensors"

echo "T2I model check complete."
