SELECT
    COUNT(*) AS total_rows,
    COUNT(*) FILTER (WHERE distress_12m = 0) AS non_distress,
    COUNT(*) FILTER (WHERE distress_12m = 1) AS distress,
    COUNT(*) FILTER (WHERE distress_12m IS NULL) AS missing_target
FROM public.model_dataset;
SELECT
    COUNT(*) AS total_rows,

    COUNT(*) FILTER (WHERE revenue IS NULL) AS missing_revenue,
    COUNT(*) FILTER (WHERE operating_income IS NULL) AS missing_operating_income,
    COUNT(*) FILTER (WHERE net_income IS NULL) AS missing_net_income,
    COUNT(*) FILTER (WHERE assets IS NULL) AS missing_assets,
    COUNT(*) FILTER (WHERE current_assets IS NULL) AS missing_current_assets,
    COUNT(*) FILTER (WHERE liabilities IS NULL) AS missing_liabilities,
    COUNT(*) FILTER (WHERE current_liabilities IS NULL) AS missing_current_liabilities,
    COUNT(*) FILTER (WHERE cash IS NULL) AS missing_cash,

    COUNT(*) FILTER (WHERE current_ratio IS NULL) AS missing_current_ratio,
    COUNT(*) FILTER (WHERE liabilities_to_assets IS NULL) AS missing_liabilities_to_assets,
    COUNT(*) FILTER (WHERE return_on_assets IS NULL) AS missing_return_on_assets,
    COUNT(*) FILTER (WHERE operating_margin IS NULL) AS missing_operating_margin,
    COUNT(*) FILTER (WHERE cash_to_assets IS NULL) AS missing_cash_to_assets,

    COUNT(*) FILTER (WHERE revenue_growth_yoy IS NULL) AS missing_revenue_growth,
    COUNT(*) FILTER (WHERE net_income_growth_yoy IS NULL) AS missing_net_income_growth,
    COUNT(*) FILTER (WHERE operating_margin_change_yoy IS NULL) AS missing_margin_change,
    COUNT(*) FILTER (WHERE leverage_change_yoy IS NULL) AS missing_leverage_change,
    COUNT(*) FILTER (WHERE current_ratio_change_yoy IS NULL) AS missing_current_ratio_change,
    COUNT(*) FILTER (WHERE cash_to_assets_change_yoy IS NULL) AS missing_cash_change,
    COUNT(*) FILTER (WHERE return_on_assets_change_yoy IS NULL) AS missing_roa_change,

    COUNT(*) FILTER (WHERE future_drawdown_12m IS NULL) AS missing_future_drawdown,
    COUNT(*) FILTER (WHERE distress_12m IS NULL) AS missing_distress

FROM public.model_dataset;
SELECT
    distress_12m,
    COUNT(*) AS observations,

    ROUND(AVG(current_ratio)::numeric, 3) AS avg_current_ratio,
    ROUND(AVG(liabilities_to_assets)::numeric, 3) AS avg_leverage,
    ROUND(AVG(return_on_assets)::numeric, 3) AS avg_roa,
    ROUND(AVG(operating_margin)::numeric, 3) AS avg_operating_margin,
    ROUND(AVG(cash_to_assets)::numeric, 3) AS avg_cash_to_assets,

    ROUND(AVG(revenue_growth_yoy)::numeric, 3) AS avg_revenue_growth_yoy,
    ROUND(AVG(net_income_growth_yoy)::numeric, 3) AS avg_net_income_growth_yoy,
    ROUND(AVG(operating_margin_change_yoy)::numeric, 3) AS avg_margin_change_yoy,
    ROUND(AVG(leverage_change_yoy)::numeric, 3) AS avg_leverage_change_yoy

FROM public.model_dataset

GROUP BY distress_12m
ORDER BY distress_12m;
SELECT
    distress_12m,
    COUNT(*) AS observations,

    ROUND(PERCENTILE_CONT(0.5) WITHIN GROUP
        (ORDER BY current_ratio)::numeric, 3) AS median_current_ratio,

    ROUND(PERCENTILE_CONT(0.5) WITHIN GROUP
        (ORDER BY liabilities_to_assets)::numeric, 3) AS median_leverage,

    ROUND(PERCENTILE_CONT(0.5) WITHIN GROUP
        (ORDER BY return_on_assets)::numeric, 3) AS median_roa,

    ROUND(PERCENTILE_CONT(0.5) WITHIN GROUP
        (ORDER BY operating_margin)::numeric, 3) AS median_operating_margin,

    ROUND(PERCENTILE_CONT(0.5) WITHIN GROUP
        (ORDER BY cash_to_assets)::numeric, 3) AS median_cash_to_assets,

    ROUND(PERCENTILE_CONT(0.5) WITHIN GROUP
        (ORDER BY revenue_growth_yoy)::numeric, 3) AS median_revenue_growth_yoy,

    ROUND(PERCENTILE_CONT(0.5) WITHIN GROUP
        (ORDER BY net_income_growth_yoy)::numeric, 3) AS median_net_income_growth_yoy,

    ROUND(PERCENTILE_CONT(0.5) WITHIN GROUP
        (ORDER BY operating_margin_change_yoy)::numeric, 3) AS median_margin_change_yoy,

    ROUND(PERCENTILE_CONT(0.5) WITHIN GROUP
        (ORDER BY leverage_change_yoy)::numeric, 3) AS median_leverage_change_yoy

FROM public.model_dataset
GROUP BY distress_12m
ORDER BY distress_12m;
SELECT
    company,
    COUNT(*) AS observations,
    SUM(distress_12m) AS distress_events,
    ROUND(AVG(distress_12m)::numeric, 3) AS distress_rate,
    ROUND(AVG(future_drawdown_12m)::numeric, 3) AS avg_future_drawdown,
    ROUND(MIN(future_drawdown_12m)::numeric, 3) AS worst_future_drawdown
FROM public.model_dataset
GROUP BY company
ORDER BY distress_rate DESC, company;
SELECT
    year,
    COUNT(*) AS observations,
    SUM(distress_12m) AS distress_events,
    ROUND(AVG(distress_12m)::numeric, 3) AS distress_rate,
    ROUND(AVG(future_drawdown_12m)::numeric, 3) AS avg_future_drawdown,
    ROUND(MIN(future_drawdown_12m)::numeric, 3) AS worst_future_drawdown
FROM public.model_dataset
GROUP BY year
ORDER BY year;
SELECT
    ROUND(CORR(current_ratio, future_drawdown_12m)::numeric, 3)
        AS corr_current_ratio,

    ROUND(CORR(liabilities_to_assets, future_drawdown_12m)::numeric, 3)
        AS corr_leverage,

    ROUND(CORR(return_on_assets, future_drawdown_12m)::numeric, 3)
        AS corr_roa,

    ROUND(CORR(operating_margin, future_drawdown_12m)::numeric, 3)
        AS corr_operating_margin,

    ROUND(CORR(cash_to_assets, future_drawdown_12m)::numeric, 3)
        AS corr_cash_to_assets,

    ROUND(CORR(revenue_growth_yoy, future_drawdown_12m)::numeric, 3)
        AS corr_revenue_growth,

    ROUND(CORR(operating_margin_change_yoy, future_drawdown_12m)::numeric, 3)
        AS corr_margin_change,

    ROUND(CORR(leverage_change_yoy, future_drawdown_12m)::numeric, 3)
        AS corr_leverage_change,

    ROUND(CORR(current_ratio_change_yoy, future_drawdown_12m)::numeric, 3)
        AS corr_liquidity_change,

    ROUND(CORR(cash_to_assets_change_yoy, future_drawdown_12m)::numeric, 3)
        AS corr_cash_change,

    ROUND(CORR(return_on_assets_change_yoy, future_drawdown_12m)::numeric, 3)
        AS corr_roa_change

FROM public.model_dataset;