-- E-Commerce Funnel Analysis Queries
-- Comprehensive analysis of conversion funnel performance

-- 1. Daily Funnel Metrics with Conversion Rates
WITH daily_funnel AS (
    SELECT 
        DATE(timestamp) as date,
        COUNT(DISTINCT CASE WHEN event_type = 'page_view' THEN session_id END) as visits,
        COUNT(DISTINCT CASE WHEN event_type = 'product_view' THEN session_id END) as product_views,
        COUNT(DISTINCT CASE WHEN event_type = 'add_to_cart' THEN session_id END) as add_to_cart,
        COUNT(DISTINCT CASE WHEN event_type = 'checkout_start' THEN session_id END) as checkout_start,
        COUNT(DISTINCT CASE WHEN event_type = 'purchase' THEN session_id END) as purchases
    FROM web_events
    WHERE timestamp >= DATE('now', '-30 days')
    GROUP BY DATE(timestamp)
),
funnel_metrics AS (
    SELECT 
        date,
        visits,
        product_views,
        add_to_cart,
        checkout_start,
        purchases,
        -- Conversion rates at each stage
        ROUND(100.0 * product_views / NULLIF(visits, 0), 2) as visit_to_view_rate,
        ROUND(100.0 * add_to_cart / NULLIF(product_views, 0), 2) as view_to_cart_rate,
        ROUND(100.0 * checkout_start / NULLIF(add_to_cart, 0), 2) as cart_to_checkout_rate,
        ROUND(100.0 * purchases / NULLIF(checkout_start, 0), 2) as checkout_to_purchase_rate,
        -- Overall conversion and abandonment rates
        ROUND(100.0 * purchases / NULLIF(visits, 0), 2) as overall_conversion_rate,
        ROUND(100.0 * (1 - purchases::FLOAT / NULLIF(checkout_start, 0)), 2) as cart_abandonment_rate
    FROM daily_funnel
)
SELECT * FROM funnel_metrics
WHERE visits > 0
ORDER BY date DESC;

-- 2. Cart Abandonment Reasons Analysis
SELECT 
    abandonment_reason,
    COUNT(*) as abandonment_count,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER(), 1) as percentage,
    -- Average time spent before abandonment
    ROUND(AVG(JULIANDAY(timestamp) - JULIANDAY(
        LAG(timestamp) OVER (PARTITION BY session_id ORDER BY timestamp)
    )) * 24 * 60, 1) as avg_minutes_before_abandon
FROM web_events
WHERE abandonment_reason IS NOT NULL
  AND timestamp >= DATE('now', '-30 days')
GROUP BY abandonment_reason
ORDER BY abandonment_count DESC;

-- 3. Device and Traffic Source Performance
SELECT 
    device_type,
    traffic_source,
    COUNT(DISTINCT session_id) as sessions,
    COUNT(DISTINCT CASE WHEN event_type = 'purchase' THEN session_id END) as conversions,
    ROUND(100.0 * COUNT(DISTINCT CASE WHEN event_type = 'purchase' THEN session_id END) / 
          COUNT(DISTINCT session_id), 2) as conversion_rate,
    -- Revenue by device/source
    COALESCE(SUM(o.revenue), 0) as total_revenue
FROM web_events we
LEFT JOIN orders o ON we.customer_id = o.customer_id 
    AND DATE(we.timestamp) = o.order_date 
    AND we.product_id = o.product_id
WHERE we.timestamp >= DATE('now', '-30 days')
GROUP BY device_type, traffic_source
HAVING sessions >= 10
ORDER BY conversion_rate DESC;

-- 4. Hourly Conversion Patterns
SELECT 
    strftime('%H', timestamp) as hour_of_day,
    COUNT(DISTINCT session_id) as sessions,
    COUNT(DISTINCT CASE WHEN event_type = 'purchase' THEN session_id END) as conversions,
    ROUND(100.0 * COUNT(DISTINCT CASE WHEN event_type = 'purchase' THEN session_id END) / 
          COUNT(DISTINCT session_id), 2) as conversion_rate
FROM web_events
WHERE timestamp >= DATE('now', '-7 days')
GROUP BY strftime('%H', timestamp)
ORDER BY hour_of_day;

-- 5. Customer Segment Funnel Performance
SELECT 
    c.customer_segment,
    COUNT(DISTINCT we.session_id) as sessions,
    COUNT(DISTINCT CASE WHEN we.event_type = 'product_view' THEN we.session_id END) as product_views,
    COUNT(DISTINCT CASE WHEN we.event_type = 'add_to_cart' THEN we.session_id END) as cart_adds,
    COUNT(DISTINCT CASE WHEN we.event_type = 'checkout_start' THEN we.session_id END) as checkouts,
    COUNT(DISTINCT CASE WHEN we.event_type = 'purchase' THEN we.session_id END) as purchases,
    -- Segment-specific conversion rates
    ROUND(100.0 * COUNT(DISTINCT CASE WHEN we.event_type = 'purchase' THEN we.session_id END) / 
          COUNT(DISTINCT we.session_id), 2) as segment_conversion_rate,
    -- Average order value by segment
    ROUND(AVG(o.revenue), 2) as avg_order_value
FROM customers c
JOIN web_events we ON c.customer_id = we.customer_id
LEFT JOIN orders o ON c.customer_id = o.customer_id
WHERE we.timestamp >= DATE('now', '-30 days')
GROUP BY c.customer_segment
ORDER BY segment_conversion_rate DESC;

-- 6. Weekly Trend Analysis
SELECT 
    strftime('%Y-W%W', timestamp) as week,
    COUNT(DISTINCT session_id) as sessions,
    COUNT(DISTINCT CASE WHEN event_type = 'purchase' THEN session_id END) as conversions,
    ROUND(100.0 * COUNT(DISTINCT CASE WHEN event_type = 'purchase' THEN session_id END) / 
          COUNT(DISTINCT session_id), 2) as conversion_rate,
    -- Week-over-week change
    LAG(ROUND(100.0 * COUNT(DISTINCT CASE WHEN event_type = 'purchase' THEN session_id END) / 
          COUNT(DISTINCT session_id), 2)) OVER (ORDER BY strftime('%Y-W%W', timestamp)) as prev_week_conversion,
    ROUND(
        (ROUND(100.0 * COUNT(DISTINCT CASE WHEN event_type = 'purchase' THEN session_id END) / 
               COUNT(DISTINCT session_id), 2) -
         LAG(ROUND(100.0 * COUNT(DISTINCT CASE WHEN event_type = 'purchase' THEN session_id END) / 
               COUNT(DISTINCT session_id), 2)) OVER (ORDER BY strftime('%Y-W%W', timestamp))) /
        LAG(ROUND(100.0 * COUNT(DISTINCT CASE WHEN event_type = 'purchase' THEN session_id END) / 
               COUNT(DISTINCT session_id), 2)) OVER (ORDER BY strftime('%Y-W%W', timestamp)) * 100, 1
    ) as wow_change_percent
FROM web_events
WHERE timestamp >= DATE('now', '-8 weeks')
GROUP BY strftime('%Y-W%W', timestamp)
ORDER BY week DESC;