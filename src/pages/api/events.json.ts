import type { APIRoute } from "astro";
import { getEvents } from "../../lib/events";

export const GET: APIRoute = async () => {
  const events = await getEvents();
  return new Response(
    JSON.stringify(events),
    {
      headers: {
        "Content-Type": "application/json",
      },
    }
  );
};
