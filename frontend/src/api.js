const BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

async function get(path, params = {}) {
  const url = new URL(BASE + path);
  Object.entries(params).forEach(([k, v]) => {
    if (v !== undefined && v !== null && v !== "") url.searchParams.set(k, v);
  });

  const res = await fetch(url);
  if (!res.ok) {
    let detail = res.statusText;
    try {
      detail = (await res.json()).detail ?? detail;
    } catch {
      /* response wasn't JSON */
    }
    throw new Error(detail);
  }
  return res.json();
}

export const api = {
  genres: () => get("/genres"),
  sections: (userId, n = 18) => get("/sections", { user_id: userId, n }),
  byGenre: (genres, userId, n = 24) =>
    get("/recommend/genre", { genres: genres.join(","), user_id: userId, n }),
  search: (q, limit = 8) => get("/search", { q, limit }),
  similar: (movieId, n = 5) => get(`/movies/${movieId}/similar`, { n }),
};