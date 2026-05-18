const selectedPreset = Editor.getParam("preset");
const preset = Array.isArray(selectedPreset) ? selectedPreset[0] : selectedPreset;

module.exports = {
    offerPrediction: {
        apiConnectionId: Editor.getId("offerApi"),
        path: `/predict-ui?preset=${encodeURIComponent(preset || "eda_cashback")}`,
        method: "GET",
        ui: true,
    },
};
