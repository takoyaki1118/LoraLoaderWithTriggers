import os
import json
import random
import torch
import folder_paths

# --------------------------------------------------------------------------------
# 1. カタログ管理クラス
# --------------------------------------------------------------------------------
class LoraCatalog:
    def __init__(self, catalog_path):
        self.catalog_path = catalog_path
        self.data = {}
        self.load_catalog()

    def load_catalog(self):
        """カタログファイルを読み込み、データをメモリにロードする"""
        if os.path.exists(self.catalog_path):
            try:
                with open(self.catalog_path, 'r', encoding='utf-8') as f:
                    self.data = json.load(f)
                print(f"[LoraLoaderWithTriggers] LoRA Catalog loaded from {self.catalog_path}")
            except json.JSONDecodeError:
                print(f"[LoraLoaderWithTriggers] ERROR: '{self.catalog_path}' is not a valid JSON file.")
            except Exception as e:
                print(f"[LoraLoaderWithTriggers] ERROR: Could not load LoRA Catalog: {e}")
        else:
            # カタログファイルは必須ではないので、見つからない場合は警告のみ
            print(f"[LoraLoaderWithTriggers] WARNING: Catalog file not found at '{self.catalog_path}'. Please create it for trigger functionality.")

    def get_lora_info(self, lora_name):
        """指定されたLoRAの情報をカタログから取得する"""
        return self.data.get(lora_name)

# --- カタログファイルのパス定義 ---
# ComfyUIのルートディレクトリからの相対パスで指定すると、環境に依存しにくくなります。
# ここでは'loras'フォルダの直下にあることを想定しています。
CATALOG_FILENAME = "lora_catalog.json"
CATALOG_PATH = os.path.join(folder_paths.get_folder_paths("loras")[0], CATALOG_FILENAME)
# Colab環境など、特定のパスを優先したい場合は以下のように直接指定も可能です。
if os.path.exists("/content/drive/MyDrive/ComfyUI_MyLoRAs/lora_catalog.json"):
    CATALOG_PATH = "/content/drive/MyDrive/ComfyUI_MyLoRAs/lora_catalog.json"

# カタログクラスのインスタンスを作成
lora_catalog = LoraCatalog(CATALOG_PATH)

# --------------------------------------------------------------------------------
# 2. カスタムノード本体
# --------------------------------------------------------------------------------
class LoraLoaderWithTriggers:
    def __init__(self):
        self.loaded_lora = None

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "model": ("MODEL",),
                "clip": ("CLIP",),
                "lora_name": (folder_paths.get_filename_list("loras"),),
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
# 3. ComfyUIへのノード登録
# --------------------------------------------------------------------------------
import comfy.utils
import comfy.sd

NODE_CLASS_MAPPINGS = {
    "LoraLoaderWithTriggers": LoraLoaderWithTriggers,
}
NODE_DISPLAY_NAME_MAPPINGS = {
    "LoraLoaderWithTriggers": "💾 LoRA Loader w/ Triggers",
}

# --- JavaScriptファイルのパスを定義 ---
# このPythonファイルと同じディレクトリにあるjsフォルダの中身を自動で読み込ませる
WEB_DIRECTORY = "./js"