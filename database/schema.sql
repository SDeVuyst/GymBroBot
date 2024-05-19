CREATE TABLE IF NOT EXISTS command_stats (
  id SERIAL PRIMARY KEY,
  command varchar(20) NOT NULL,
  user_id varchar(20) NOT NULL,
  count INTEGER DEFAULT 0
);