CREATE OR REPLACE VIEW public.model_features AS
SELECT
    cik,
    filed,
    year,

    current_ratio,
    liabilities_to_assets,
    return_on_assets,
    operating_margin,
    cash_to_assets,

    revenue_growth_yoy,
    net_income_growth_yoy,
    operating_margin_change_yoy,
    leverage_change_yoy,
    current_ratio_change_yoy,
    cash_to_assets_change_yoy,
    return_on_assets_change_yoy,

    future_drawdown_12m,
    distress_12m

FROM public.model_dataset;
SELECT COUNT(*) AS total_rows
FROM public.model_features;
CREATE OR REPLACE VIEW public.model_split AS
SELECT
    *,
    CASE
        WHEN filed < DATE '2022-01-01' THEN 'train'
        WHEN filed >= DATE '2022-01-01'
         AND filed < DATE '2024-01-01' THEN 'validation'
        ELSE 'test'
    END AS dataset_split
FROM public.model_features;
SELECT
    dataset_split,
    COUNT(*) AS observations,
    SUM(distress_12m) AS distress_events,
    ROUND(AVG(distress_12m)::numeric, 3) AS distress_rate,
    MIN(filed) AS first_filing,
    MAX(filed) AS last_filing
FROM public.model_split
GROUP BY dataset_split
ORDER BY MIN(filed);
SELECT
    dataset_split,
    COUNT(*) AS observations,

    COUNT(*) FILTER (WHERE current_ratio IS NULL)
        AS missing_current_ratio,

    COUNT(*) FILTER (WHERE liabilities_to_assets IS NULL)
        AS missing_leverage,

    COUNT(*) FILTER (WHERE return_on_assets IS NULL)
        AS missing_roa,

    COUNT(*) FILTER (WHERE operating_margin IS NULL)
        AS missing_operating_margin,

    COUNT(*) FILTER (WHERE cash_to_assets IS NULL)
        AS missing_cash_ratio,

    COUNT(*) FILTER (WHERE revenue_growth_yoy IS NULL)
        AS missing_revenue_growth,

    COUNT(*) FILTER (WHERE net_income_growth_yoy IS NULL)
        AS missing_net_income_growth,

    COUNT(*) FILTER (WHERE operating_margin_change_yoy IS NULL)
        AS missing_margin_change,

    COUNT(*) FILTER (WHERE leverage_change_yoy IS NULL)
        AS missing_leverage_change,

    COUNT(*) FILTER (WHERE current_ratio_change_yoy IS NULL)
        AS missing_current_ratio_change,

    COUNT(*) FILTER (WHERE cash_to_assets_change_yoy IS NULL)
        AS missing_cash_change,

    COUNT(*) FILTER (WHERE return_on_assets_change_yoy IS NULL)
        AS missing_roa_change

FROM public.model_split
GROUP BY dataset_split
ORDER BY
    CASE dataset_split
        WHEN 'train' THEN 1
        WHEN 'validation' THEN 2
        WHEN 'test' THEN 3
    END;
CREATE OR REPLACE VIEW public.model_ready AS
SELECT
    filed,
    year,
    dataset_split,

    current_ratio,
    liabilities_to_assets,
    return_on_assets,
    operating_margin,
    cash_to_assets,

    revenue_growth_yoy,
    net_income_growth_yoy,
    operating_margin_change_yoy,
    leverage_change_yoy,
    current_ratio_change_yoy,
    cash_to_assets_change_yoy,
    return_on_assets_change_yoy,

    distress_12m,
    future_drawdown_12m

FROM public.model_split;
SELECT
    COUNT(*) AS total_rows,
    COUNT(*) FILTER (WHERE dataset_split = 'train') AS train,
    COUNT(*) FILTER (WHERE dataset_split = 'validation') AS validation,
    COUNT(*) FILTER (WHERE dataset_split = 'test') AS test
FROM public.model_ready;