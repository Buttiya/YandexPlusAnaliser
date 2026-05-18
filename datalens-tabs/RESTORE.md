# Restore DataLens chart with selector

If the selector is visible but the chart shows `[0.00, 0.00]`, restore these tabs:

1. `Meta` -> paste all of `Meta.json`
2. `Params` -> paste all of `Params.js`
3. `Sources` -> paste all of `Sources.js`
4. `Controls` -> paste all of `Controls.js`
5. `Prepare` -> paste all of `Prepare.js`

The most important tab for non-zero API response is `Sources.js`.
It sends the selected preset payload to:

```text
POST http://ai360.velkerr.ru:40186/predict
```

Do not paste the combined `datalens-editor-current-server.js` into one tab.
Use the separated files in this folder.

