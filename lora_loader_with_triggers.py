import os
import json
import random
import torch
import folder_paths

# --------------------------------------------------------------------------------
# 1. カタログ管理クラス (変更なし)
# --------------------------------------------------------------------------------
class LoraCatalog:
    def __init__(self, catalog_path):
        self.catalog_path = catalog_path
        self.data = {}
        self.load_catalog()

    def load_catalog(self):
        if os.path.exists(self.catalog_path):
            try:
                with open(self.catalog_path, 'r', encoding='utf-8') as f:
                    self.data = json.load(f)
                print(f"[LoraLoaderWithTriggers] LoRA Catalog loaded from {self.catalog_path}")
            except Exception as e:
                print(f"[LoraLoaderWithTriggers] ERROR: Could not load LoRA Catalog: {e}")
        else:
            print(f"[LoraLoaderWithTriggers] WARNING: Catalog file not found at '{self.catalog_path}'.")

    def get_lora_info(self, lora_name):
        return self.data.get(lora_name)
    
    def get_lora_names_from_catalog(self):
        # [!!! NEW !!!] カタログに登録されているLoRAの名前リストを取得するヘルパー関数
        return list(self.data.keys())

# --- カタログファイルのパス定義 (変更なし) ---
CATALOG_FILENAME = "lora_catalog.json"
CATALOG_PATH = os.path.join(folder_paths.get_folder_paths("loras")[0], CATALOG_FILENAME)
if os.path.exists("/content/drive/MyDrive/ComfyUI_MyLoRAs/lora_catalog.json"):
    CATALOG_PATH = "/content/drive/MyDrive/ComfyUI_MyLoRAs/lora_catalog.json"

lora_catalog = LoraCatalog(CATALOG_PATH)

# --------------------------------------------------------------------------------
# 2. カスタムノード本体 (INPUT_TYPES を修正)
# --------------------------------------------------------------------------------
class LoraLoaderWithTriggers:
    def __init__(self):
        self.loaded_lora = None

    @classmethod
    def INPUT_TYPES(s):
        # [!!! MODIFIED !!!] ComfyUIの全LoRAリストの代わりに、カタログのLoRAリストを使用
        catalog_loras = lora_catalog.get_lora_names_from_catalog()
        if not catalog_loras:
            # カタログが空か読み込めない場合は、フォールバックとして全LoRAを表示し、エラーを防ぐ
            catalog_loras = ["CATALOG NOT FOUND OR EMPTY"] + folder_paths.get_filename_list("loras")

        return {
            "required": {
                "model": ("MODEL",),
                "clip": ("CLIP",),
                "lora_name": (catalog_loras,), # ここをカタログのリストに変更
                "variation": (["No Variations"],), 
                "strength_model": ("FLOAT", {"default": 1.0, "min": -10.0, "max": 10.0, "step": 0.01}),
                "strength_clip": ("FLOAT", {"default": 1.0, "min": -10.0, "max": 10.0, "step": 0.01}),
            }
        }

    RETURN_TYPES = ("MODEL", "CLIP", "STRING",)
    RETURN_NAMES = ("MODEL", "CLIP", "TRIGGERS",)
    FUNCTION = "load_lora"
    CATEGORY = "My Lora Tools"

    def load_lora(self, model, clip, lora_name, variation, strength_model, strength_clip):
        # lora_nameがフォールバックメッセージの場合、何もしない
        if lora_name == "CATALOG NOT FOUND OR EMPTY":
            return (model, clip, "")
            
        # --- 以下、LoRAの読み込みとトリガー生成ロジック (変更なし) ---
        if strength_model == 0 and strength_clip == 0:
            return (model, clip, "")
        
        lora_path = folder_paths.get_full_path("loras", lora_name)
        lora = None
        if self.loaded_lora is not None:
            if self.loaded_lora[0] == lora_path:
                lora = self.loaded_lora[1]
            else:
                self.loaded_lora = None
        if lora is None:
            lora = comfy.utils.load_torch_file(lora_path, safe_load=True)
            self.loaded_lora = (lora_path, lora)
        triggers = ""
        info = lora_catalog.get_lora_info(lora_name)
        if info:
            base_prompt = info.get("base", "")
            variations_dict = info.get("variations", {})
            if variation == "Base Only":
                triggers = base_prompt
            elif variation == "Random" and variations_dict:
                selected_variation_prompt = random.choice(list(variations_dict.values()))
                triggers = f"{base_prompt}, {selected_variation_prompt}" if base_prompt and selected_variation_prompt else base_prompt or selected_variation_prompt
            elif variation in variations_dict:
                selected_variation_prompt = variations_dict[variation]
                triggers = f"{base_prompt}, {selected_variation_prompt}" if base_prompt and selected_variation_prompt else base_prompt or selected_variation_prompt
            else:
                triggers = base_prompt
        model_lora, clip_lora = comfy.sd.load_lora_for_models(model, clip, lora, strength_model, strength_clip)
        return (model_lora, clip_lora, triggers.strip())

    # --- APIとJavaScript連携部分 (変更なし) ---
    @classmethod
    def get_web_api_data(cls, lora_name):
        lora_catalog.load_catalog()
        info = lora_catalog.get_lora_info(lora_name)
        if info:
            variations = list(info.get("variations", {}).keys())
            options = ["Base Only"]
            if variations:
                options.append("Random")
                options.extend(variations)
            return {"variations": options}
        return {"variations": ["Not in Catalog"]}

    @classmethod
    def get_web_api_routes(cls):
        return {"GET": {"/lora_variations": (cls.get_web_api_data, ["lora_name"])}}

# --------------------------------------------------------------------------------
# 3. ComfyUIへのノード登録 (変更なし)
# --------------------------------------------------------------------------------
import comfy.utils
import comfy.sd
NODE_CLASS_MAPPINGS = {"LoraLoaderWithTriggers": LoraLoaderWithTriggers}
NODE_DISPLAY_NAME_MAPPINGS = {"LoraLoaderWithTriggers": "💾 LoRA Loader w/ Triggers"}
WEB_DIRECTORY = "./js"