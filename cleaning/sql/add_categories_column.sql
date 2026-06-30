# Sourced from Calplus (https://github.com/Calplus)
-- Add travel-category, subjectivity, and geo fields to ig_posts and ig_comments.
-- All columns are nullable with DEFAULT NULL so existing rows are untouched.
-- Safe to re-run: IF NOT EXISTS prevents errors on duplicate execution.

-- ig_posts -------------------------------------------------------------------
ALTER TABLE instagram_crawl.ig_posts
  ADD COLUMN IF NOT EXISTS categories       text[]  DEFAULT NULL;
ALTER TABLE instagram_crawl.ig_posts
  ADD COLUMN IF NOT EXISTS subjectivity     text    DEFAULT NULL;
ALTER TABLE instagram_crawl.ig_posts
  ADD COLUMN IF NOT EXISTS subjectivity_score real  DEFAULT NULL;
ALTER TABLE instagram_crawl.ig_posts
  ADD COLUMN IF NOT EXISTS latitude         real    DEFAULT NULL;
ALTER TABLE instagram_crawl.ig_posts
  ADD COLUMN IF NOT EXISTS longitude        real    DEFAULT NULL;

-- ig_comments ----------------------------------------------------------------
ALTER TABLE instagram_crawl.ig_comments
  ADD COLUMN IF NOT EXISTS categories       text[]  DEFAULT NULL;
ALTER TABLE instagram_crawl.ig_comments
  ADD COLUMN IF NOT EXISTS subjectivity     text    DEFAULT NULL;
ALTER TABLE instagram_crawl.ig_comments
  ADD COLUMN IF NOT EXISTS subjectivity_score real  DEFAULT NULL;
# Sourced from Calplus (https://github.com/Calplus)

-- pinterest_pins -------------------------------------------------------------
-- NOTE: pinterest_pins was omitted from the original migration; added here.
ALTER TABLE instagram_crawl.pinterest_pins
  ADD COLUMN IF NOT EXISTS categories       text[]  DEFAULT NULL;
ALTER TABLE instagram_crawl.pinterest_pins
  ADD COLUMN IF NOT EXISTS city             text    DEFAULT NULL;

-- Indexes for category filtering (all three tables) --------------------------
CREATE INDEX IF NOT EXISTS idx_ig_posts_categories
  ON instagram_crawl.ig_posts USING GIN (categories);

CREATE INDEX IF NOT EXISTS idx_ig_comments_categories
  ON instagram_crawl.ig_comments USING GIN (categories);

CREATE INDEX IF NOT EXISTS idx_pinterest_categories
  ON instagram_crawl.pinterest_pins USING GIN (categories);
