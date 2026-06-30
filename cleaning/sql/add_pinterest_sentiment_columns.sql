# Sourced from Calplus (https://github.com/Calplus)
-- Add sentiment columns to pinterest_pins.
-- ig_posts and ig_comments already have these from the original schema.
-- Safe to re-run: IF NOT EXISTS prevents errors on duplicate execution.

ALTER TABLE instagram_crawl.pinterest_pins
  ADD COLUMN IF NOT EXISTS sentiment         text    DEFAULT NULL,
  ADD COLUMN IF NOT EXISTS sentiment_score   float4  DEFAULT NULL,
  ADD COLUMN IF NOT EXISTS subjectivity      text    DEFAULT NULL,
  ADD COLUMN IF NOT EXISTS subjectivity_score float4 DEFAULT NULL;
# Sourced from Calplus (https://github.com/Calplus)

-- Optional: index for sentiment filtering (matches ig_posts pattern)
CREATE INDEX IF NOT EXISTS idx_pinterest_sentiment
  ON instagram_crawl.pinterest_pins (sentiment);
