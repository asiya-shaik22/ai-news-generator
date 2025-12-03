-- Drop table if exists (optional)
DROP TABLE IF EXISTS articles;

-- Create articles table
CREATE TABLE articles (
    id          BIGSERIAL PRIMARY KEY,
    url         TEXT NOT NULL,
    title       TEXT,
    summary     TEXT,
    snippet     TEXT,
    raw_html    TEXT,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- Ensure no duplicate articles are inserted
ALTER TABLE articles
ADD CONSTRAINT unique_article_url UNIQUE (url);

-- Optional: Index for faster sorting by latest
CREATE INDEX idx_articles_created_at
ON articles (created_at DESC);
