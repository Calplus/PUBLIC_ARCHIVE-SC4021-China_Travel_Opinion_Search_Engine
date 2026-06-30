# Sourced from Calplus (https://github.com/Calplus)
-- Performance indexes for all three tables.
-- Safe to re-run: IF NOT EXISTS prevents duplicate errors.
--
-- Columns per table (based on applied migrations):
--   ig_posts      : city, language, is_spam, posted_at, sentiment  (original schema)
--   ig_comments   : city, posted_at, sentiment                     (original + add_categories_column.sql)
--   pinterest_pins: city, scraped_at, sentiment                    (add_categories_column.sql + add_pinterest_sentiment_columns.sql)
--                   idx_pinterest_sentiment already created in add_pinterest_sentiment_columns.sql

-- posted_at — date-range filters and analytics timeline aggregations
-- Note: pinterest_pins stores scraped_at (no posted_at column exists)
CREATE INDEX IF NOT EXISTS idx_ig_posts_posted_at
  ON instagram_crawl.ig_posts (posted_at);
CREATE INDEX IF NOT EXISTS idx_ig_comments_posted_at
  ON instagram_crawl.ig_comments (posted_at);
CREATE INDEX IF NOT EXISTS idx_pinterest_scraped_at
  ON instagram_crawl.pinterest_pins (scraped_at);

-- city — city-level ranking and filter queries
CREATE INDEX IF NOT EXISTS idx_ig_posts_city
  ON instagram_crawl.ig_posts (city);
CREATE INDEX IF NOT EXISTS idx_ig_comments_city
  ON instagram_crawl.ig_comments (city);
CREATE INDEX IF NOT EXISTS idx_pinterest_city
  ON instagram_crawl.pinterest_pins (city);
# Sourced from Calplus (https://github.com/Calplus)

-- language — language filter queries (ig_posts only; ig_comments and pinterest_pins lack this column)
CREATE INDEX IF NOT EXISTS idx_ig_posts_language
  ON instagram_crawl.ig_posts (language);

-- is_spam — partial index on spam rows only (ig_posts only; ig_comments and pinterest_pins lack this column)
--   Partial index is far cheaper than a full B-tree on a low-cardinality boolean column.
CREATE INDEX IF NOT EXISTS idx_ig_posts_is_spam
  ON instagram_crawl.ig_posts (is_spam) WHERE is_spam = true;

-- is_duplicate — partial index on duplicate rows only (ig_posts only; ig_comments and pinterest_pins lack this column)
--   Required for is_duplicate=true REST queries to avoid statement timeout.
CREATE INDEX IF NOT EXISTS idx_ig_posts_is_duplicate
  ON instagram_crawl.ig_posts (is_duplicate) WHERE is_duplicate = true;

-- sentiment NOT NULL partial — speeds up write_sentiment_to_supabase scroll queries
--   pinterest_pins covered by idx_pinterest_sentiment in add_pinterest_sentiment_columns.sql
CREATE INDEX IF NOT EXISTS idx_ig_posts_sentiment_notnull
  ON instagram_crawl.ig_posts (sentiment) WHERE sentiment IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_ig_comments_sentiment_notnull
  ON instagram_crawl.ig_comments (sentiment) WHERE sentiment IS NOT NULL;
