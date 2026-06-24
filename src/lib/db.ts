import { Pool } from "pg";

export const pool = new Pool({
  host: import.meta.env.DATABASE_HOST,
  port: Number(import.meta.env.DATABASE_PORT),
  database: import.meta.env.DATABASE_NAME,
  user: import.meta.env.DATABASE_USER,
  password: import.meta.env.DATABASE_PASSWORD,
});
