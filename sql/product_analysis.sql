-- Product Performance and Profitability Analysis

-- 1. Product Performance Matrix
WITH product_metrics AS (
    SELECT 
        p.product_id,
        p.product_name,
        p.category,
        p.price,
        p.cost,
        p.margin_percent,
        -- Event metrics
        COUNT(DISTINCT CASE WHEN we.event_type = 'product_view' THEN we.session_id END) as product_views,
        COUNT(DISTINCT CASE WHEN we.event_type = 'add_to_cart' THEN we.session_id END) as cart_adds,
        COUNT(DISTINCT CASE WHEN we.event_type = 'checkout_start' THEN we.session_id END) as checkouts,
        COUNT(DISTINCT CASE WHEN we.event_type = 'purchase' THEN we.session_id END) as purchases,
        -- Financial metrics
        COALESCE(SUM(o.quantity), 0) as units_sold,
        COALESCE(SUM(o.revenue), 0) as total_revenue,
        COALESCE(SUM(o.profit), 0) as total_profit,
        COALESCE(AVG(o.revenue), 0) as avg_order_value
    FROM products p
    LEFT JOIN web_events we ON p.product_id = we.product_id 
        AND we.timestamp >= DATE('now', '-30 days')
    LEFT JOIN orders o ON p.product_id = o.product_id 
        AND o.order_date >= DATE('now', '-30 days')
    GROUP BY p.product_id, p.product_name, p.category, p.price, p.cost, p.margin_percent
),
product_performance AS (
    SELECT 
        *,
        -- Conversion rates
        ROUND(100.0 * cart_adds / NULLIF(product_views, 0), 2) as view_to_cart_rate,
        ROUND(100.0 * checkouts / NULLIF(cart_adds, 0), 2) as cart_to_checkout_rate,
        ROUND(100.0 * purchases / NULLIF(checkouts, 0), 2) as checkout_to_purchase_rate,
        ROUND(100.0 * purchases / NULLIF(product_views, 0), 2) as overall_conversion_rate,
        -- Performance score (weighted combination of metrics)
        ROUND(
            (COALESCE(100.0 * cart_adds / NULLIF(product_views, 0), 0) * 0.3) +
            (COALESCE(100.0 * purchases / NULLIF(cart_adds, 0), 0) * 0.4) +
            (COALESCE(total_profit / NULLIF(total_revenue, 0) * 100, 0) * 0.3), 2
        ) as performance_score
    FROM product_metrics
    WHERE product_views > 0 OR units_sold > 0
)
SELECT 
    product_id,
    product_name,
    category,
    price,
    margin_percent,
    product_views,
    view_to_cart_rate,
    checkout_to_purchase_rate,
    overall_conversion_rate,
    units_sold,
    total_revenue,
    total_profit,
    performance_score,
    -- Performance tier
    CASE 
        WHEN performance_score >= 70 THEN 'High Performer'
        WHEN performance_score >= 40 THEN 'Medium Performer'
        ELSE 'Low Performer'
    END as performance_tier
FROM product_performance
ORDER BY performance_score DESC, total_revenue DESC;

-- 2. Category Performance Analysis
SELECT 
    p.category,
    COUNT(DISTINCT p.product_id) as total_products,
    -- Engagement metrics
    COUNT(DISTINCT CASE WHEN we.event_type = 'product_view' THEN we.session_id END) as total_views,
    COUNT(DISTINCT CASE WHEN we.event_type = 'add_to_cart' THEN we.session_id END) as total_cart_adds,
    COUNT(DISTINCT CASE WHEN we.event_type = 'purchase' THEN we.session_id END) as total_purchases,
    -- Financial metrics
    COALESCE(SUM(o.revenue), 0) as category_revenue,
    COALESCE(SUM(o.profit), 0) as category_profit,
    ROUND(AVG(p.price), 2) as avg_price,
    ROUND(AVG(p.margin_percent), 2) as avg_margin,
    -- Conversion rates
    ROUND(100.0 * COUNT(DISTINCT CASE WHEN we.event_type = 'add_to_cart' THEN we.session_id END) / 
          NULLIF(COUNT(DISTINCT CASE WHEN we.event_type = 'product_view' THEN we.session_id END), 0), 2) as category_view_to_cart,
    ROUND(100.0 * COUNT(DISTINCT CASE WHEN we.event_type = 'purchase' THEN we.session_id END) / 
          NULLIF(COUNT(DISTINCT CASE WHEN we.event_type = 'product_view' THEN we.session_id END), 0), 2) as category_conversion_rate
FROM products p
LEFT JOIN web_events we ON p.product_id = we.product_id 
    AND we.timestamp >= DATE('now', '-30 days')
LEFT JOIN orders o ON p.product_id = o.product_id 
    AND o.order_date >= DATE('now', '-30 days')
GROUP BY p.category
ORDER BY category_revenue DESC;

-- 3. Price Sensitivity Analysis
WITH price_bands AS (
    SELECT 
        product_id,
        product_name,
        category,
        price,
        CASE 
            WHEN price < 25 THEN 'Under $25'
            WHEN price < 50 THEN '$25-$50'
            WHEN price < 100 THEN '$50-$100'
            WHEN price < 200 THEN '$100-$200'
            ELSE 'Over $200'
        END as price_band
    FROM products
)
SELECT 
    pb.price_band,
    COUNT(DISTINCT pb.product_id) as products_in_band,
    -- Performance metrics
    COUNT(DISTINCT CASE WHEN we.event_type = 'product_view' THEN we.session_id END) as views,
    COUNT(DISTINCT CASE WHEN we.event_type = 'add_to_cart' THEN we.session_id END) as cart_adds,
    COUNT(DISTINCT CASE WHEN we.event_type = 'purchase' THEN we.session_id END) as purchases,
    -- Conversion rates by price band
    ROUND(100.0 * COUNT(DISTINCT CASE WHEN we.event_type = 'add_to_cart' THEN we.session_id END) / 
          NULLIF(COUNT(DISTINCT CASE WHEN we.event_type = 'product_view' THEN we.session_id END), 0), 2) as view_to_cart_rate,
    ROUND(100.0 * COUNT(DISTINCT CASE WHEN we.event_type = 'purchase' THEN we.session_id END) / 
          NULLIF(COUNT(DISTINCT CASE WHEN we.event_type = 'add_to_cart' THEN we.session_id END), 0), 2) as cart_to_purchase_rate,
    -- Revenue metrics
    COALESCE(SUM(o.revenue), 0) as total_revenue,
    ROUND(AVG(pb.price), 2) as avg_price_in_band
FROM price_bands pb
LEFT JOIN web_events we ON pb.product_id = we.product_id 
    AND we.timestamp >= DATE('now', '-30 days')
LEFT JOIN orders o ON pb.product_id = o.product_id 
    AND o.order_date >= DATE('now', '-30 days')
GROUP BY pb.price_band
ORDER BY 
    CASE pb.price_band
        WHEN 'Under $25' THEN 1
        WHEN '$25-$50' THEN 2
        WHEN '$50-$100' THEN 3
        WHEN '$100-$200' THEN 4
        WHEN 'Over $200' THEN 5
    END;

-- 4. Product Affinity Analysis (Products often viewed together)
WITH session_products AS (
    SELECT DISTINCT 
        session_id,
        product_id
    FROM web_events
    WHERE event_type = 'product_view'
      AND timestamp >= DATE('now', '-30 days')
),
product_pairs AS (
    SELECT 
        sp1.product_id as product_a,
        sp2.product_id as product_b,
        COUNT(*) as sessions_together
    FROM session_products sp1
    JOIN session_products sp2 ON sp1.session_id = sp2.session_id 
        AND sp1.product_id < sp2.product_id
    GROUP BY sp1.product_id, sp2.product_id
    HAVING sessions_together >= 5
)
SELECT 
    pp.product_a,
    pa.product_name as product_a_name,
    pa.category as product_a_category,
    pp.product_b,
    pb.product_name as product_b_name,
    pb.category as product_b_category,
    pp.sessions_together,
    ROUND(100.0 * pp.sessions_together / 
          (SELECT COUNT(DISTINCT session_id) FROM session_products WHERE product_id = pp.product_a), 2) as affinity_score
FROM product_pairs pp
JOIN products pa ON pp.product_a = pa.product_id
JOIN products pb ON pp.product_b = pb.product_id
ORDER BY pp.sessions_together DESC, affinity_score DESC
LIMIT 20;

-- 5. Seasonal/Trending Products
SELECT 
    p.product_id,
    p.product_name,
    p.category,
    -- Current month performance
    COUNT(DISTINCT CASE WHEN we.event_type = 'product_view' AND we.timestamp >= DATE('now', '-30 days') 
          THEN we.session_id END) as views_current_month,
    COUNT(DISTINCT CASE WHEN we.event_type = 'purchase' AND we.timestamp >= DATE('now', '-30 days') 
          THEN we.session_id END) as purchases_current_month,
    -- Previous month performance  
    COUNT(DISTINCT CASE WHEN we.event_type = 'product_view' 
                            AND we.timestamp >= DATE('now', '-60 days') 
                            AND we.timestamp < DATE('now', '-30 days')
          THEN we.session_id END) as views_previous_month,
    COUNT(DISTINCT CASE WHEN we.event_type = 'purchase' 
                            AND we.timestamp >= DATE('now', '-60 days') 
                            AND we.timestamp < DATE('now', '-30 days')
          THEN we.session_id END) as purchases_previous_month,
    -- Growth rates
    ROUND(
        (COUNT(DISTINCT CASE WHEN we.event_type = 'product_view' AND we.timestamp >= DATE('now', '-30 days') 
              THEN we.session_id END) - 
         COUNT(DISTINCT CASE WHEN we.event_type = 'product_view' 
                                AND we.timestamp >= DATE('now', '-60 days') 
                                AND we.timestamp < DATE('now', '-30 days')
              THEN we.session_id END)) * 100.0 / 
        NULLIF(COUNT(DISTINCT CASE WHEN we.event_type = 'product_view' 
                                      AND we.timestamp >= DATE('now', '-60 days') 
                                      AND we.timestamp < DATE('now', '-30 days')
                    THEN we.session_id END), 0), 1
    ) as view_growth_rate,
    -- Trend classification
    CASE 
        WHEN COUNT(DISTINCT CASE WHEN we.event_type = 'product_view' AND we.timestamp >= DATE('now', '-30 days') 
                  THEN we.session_id END) > 
             COUNT(DISTINCT CASE WHEN we.event_type = 'product_view' 
                                    AND we.timestamp >= DATE('now', '-60 days') 
                                    AND we.timestamp < DATE('now', '-30 days')
                  THEN we.session_id END) * 1.2 THEN 'Trending Up'
        WHEN COUNT(DISTINCT CASE WHEN we.event_type = 'product_view' AND we.timestamp >= DATE('now', '-30 days') 
                  THEN we.session_id END) < 
             COUNT(DISTINCT CASE WHEN we.event_type = 'product_view' 
                                    AND we.timestamp >= DATE('now', '-60 days') 
                                    AND we.timestamp < DATE('now', '-30 days')
                  THEN we.session_id END) * 0.8 THEN 'Declining'
        ELSE 'Stable'
    END as trend_status
FROM products p
LEFT JOIN web_events we ON p.product_id = we.product_id 
    AND we.timestamp >= DATE('now', '-60 days')
WHERE EXISTS (
    SELECT 1 FROM web_events we2 
    WHERE we2.product_id = p.product_id 
      AND we2.timestamp >= DATE('now', '-60 days')
)
ORDER BY view_growth_rate DESC NULLS LAST;