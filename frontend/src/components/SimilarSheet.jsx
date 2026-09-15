import { useEffect, useState } from "react";
import { api } from "../api";
import MovieCard from "./MovieCard";
import { tileStyle } from "../lib/palette";

export default function SimilarSheet({ movie, onClose, onSelect }) {
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    let live = true;
    setData(null);
    setError(null);
    api
      .similar(movie.movie_id, 5)
      .then((d) => live && setData(d))
      .catch((e) => live && setError(e.message));
    return () => {
      live = false;
    };
  }, [movie.movie_id]);

  useEffect(() => {
    const esc = (e) => e.key === "Escape" && onClose();
    document.addEventListener("keydown", esc);
    document.body.style.overflow = "hidden";
    return () => {
      document.removeEventListener("keydown", esc);
      document.body.style.overflow = "";
    };
  }, [onClose]);

  const seed = data?.seed ?? movie;

  return (
    <div className="sheet__scrim" onClick={onClose}>
      <div
        className="sheet"
        role="dialog"
        aria-modal="true"
        aria-label={`Movies like ${seed.title}`}
        onClick={(e) => e.stopPropagation()}
      >
        <button className="sheet__close" onClick={onClose} aria-label="Close">
          ✕
        </button>

        <div className="sheet__seed" style={tileStyle(seed)}>
          <p className="sheet__eyebrow">Because you picked</p>
          <h2>{seed.title}</h2>
          <p className="sheet__meta">
            {seed.year ?? "—"} · {seed.genres.join(" / ")}
          </p>
          <p className="sheet__stats">
            {seed.avg_rating} average across {seed.rating_count.toLocaleString()} ratings
          </p>
        </div>

        <div className="sheet__list">
          <h3>Five that land the same way</h3>

          {error && <p className="state state--bad">{error}</p>}
          {!data && !error && <p className="state">Reading the model…</p>}

          {data && (
            <div className="sheet__grid">
              {data.similar.map((m) => (
                <MovieCard key={m.movie_id} movie={m} size="sm" onSelect={onSelect} />
              ))}
            </div>
          )}

          {data?.similar.length === 0 && (
            <p className="state">
              The model has too little signal on this title. Try a more widely rated one.
            </p>
          )}
        </div>
      </div>
    </div>
  );
}