import { app } from "/scripts/app.js";

app.registerExtension({
    name: "LoraLoaderWithTriggers",
    async beforeRegisterNodeDef(nodeType, nodeData, app) {
        if (nodeData.name === "LoraLoaderWithTriggers") {
            const onNodeCreated = nodeType.prototype.onNodeCreated;
            nodeType.prototype.onNodeCreated = function () {
                onNodeCreated?.apply(this, arguments);

                const loraNameWidget = this.widgets.find(w => w.name === "lora_name");
                const variationWidget = this.widgets.find(w => w.name === "variation");
                
                const updateVariations = async () => {
                    const lora_name = loraNameWidget.value;

                    // [!!! MODIFIED !!!] カタログが見つからない場合のエラー表示に対応
                    if (!lora_name || lora_name === "CATALOG NOT FOUND OR EMPTY") {
                        variationWidget.options.values = ["N/A"];
                        variationWidget.value = "N/A";
                        return;
                    }
                    
                    try {
                        const res = await api.fetchApi(`/lora_variations?lora_name=${encodeURIComponent(lora_name)}`);
                        if (res.status !== 200) {
                             console.error("Failed to fetch LoRA variations:", res.statusText);
                             return;
                        }

                        const data = await res.json();
                        
                        variationWidget.options.values = data.variations;
                        if (!data.variations.includes(variationWidget.value)) {
                            variationWidget.value = data.variations[0];
                        }
                        this.setDirtyCanvas(true);
                    } catch (error) {
                        console.error("Error updating LoRA variations:", error);
                    }
                };

                loraNameWidget.callback = updateVariations;
                
                setTimeout(updateVariations, 100);
            };
        }
    },
});