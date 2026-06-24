import { pool } from "./db";

export async function getEvents() {
  try {
    const result = await pool.query(`
      SELECT *
      FROM calendar.events
      ORDER BY start_datetime ASC
    `);
    return result.rows;
  } catch (err: any) {
    console.error('getEvents - DB query failed:', err?.message || err);
    // Detect permission-denied and give actionable guidance
    if (err?.code === '42501' || /permission denied/i.test(String(err?.message))) {
      throw new Error(
        'Database permission denied for table `events`. Grant SELECT to the DB user or use a schema the user can access. Example SQL: GRANT SELECT ON calendar.events TO calendar_user;'
      );
    }
    throw err;
  }
}
