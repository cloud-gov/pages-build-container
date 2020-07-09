CREATE TABLE IF NOT EXISTS buildlog (id serial PRIMARY KEY, build integer, source varchar, output varchar);
ALTER TABLE buildlog ADD COLUMN IF NOT EXISTS "createdAt" timestamp;
ALTER TABLE buildlog ADD COLUMN IF NOT EXISTS "updatedAt" timestamp;
