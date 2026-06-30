# Sourced from Calplus (https://github.com/Calplus)
-- Fetch total posts and sentiment counts for ig_posts, ig_comments, and pinterest_pins

-- Total posts and sentiment counts for ig_posts
SELECT 
    'ig_posts' AS table_name,
    COUNT(*) AS total_posts,
    SUM(CASE WHEN sentiment = 'positive' THEN 1 ELSE 0 END) AS positive_count,
    SUM(CASE WHEN sentiment = 'negative' THEN 1 ELSE 0 END) AS negative_count
FROM instagram_crawl.ig_posts;

-- Total posts and sentiment counts for ig_comments
SELECT 
    'ig_comments' AS table_name,
    COUNT(*) AS total_comments,
    SUM(CASE WHEN sentiment = 'positive' THEN 1 ELSE 0 END) AS positive_count,
    SUM(CASE WHEN sentiment = 'negative' THEN 1 ELSE 0 END) AS negative_count
FROM instagram_crawl.ig_comments;
# Sourced from Calplus (https://github.com/Calplus)

-- Total posts and sentiment counts for pinterest_pins
SELECT 
    'pinterest_pins' AS table_name,
    COUNT(*) AS total_pins,
    SUM(CASE WHEN sentiment = 'positive' THEN 1 ELSE 0 END) AS positive_count,
    SUM(CASE WHEN sentiment = 'negative' THEN 1 ELSE 0 END) AS negative_count
FROM instagram_crawl.pinterest_pins;
