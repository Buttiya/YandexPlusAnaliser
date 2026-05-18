module.exports = {
    controls: [
        {
            type: "select",
            param: "preset",
            label: "Пресет",
            updateOnChange: true,
            width: "320px",
            content: [
                {title: "Еда: кешбэк", value: "eda_cashback"},
                {title: "Такси: скидка", value: "taxi_discount"},
                {title: "Лавка: баллы", value: "lavka_points"},
                {title: "Маркет: кешбэк", value: "market_cashback"},
            ],
        },
    ],
};
