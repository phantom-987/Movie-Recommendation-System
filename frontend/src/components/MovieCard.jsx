import { tileStyle } from "../lib/palette";

export default function MovieCard({ movie, onSelect, size = "md" }) {
  const rating = movie.predicted_rating ?? movie.avg_rating;
  const isPrediction = movie.predicted_rating != null;

  return (
    <button
      type="button"
      className={`card card--${size}`}
      style={tileStyle(movie)}
      onClick={() => onSelect(movie)}
      aria-label={`${movie.title}. Show similar movies.`}
    >
              {movie.poster_url && (
        <img className="card__art" src={movie.poster_url} alt="" loading="lazy" />
      )}
      <span className="card__grain" aria-hidden="true" />

      <span className="card__top">
        {rating != null && (
          <span className={isPrediction ? "chip chip--predicted" : "chip"}>
            {Number(rating).toFixed(1)}
            {isPrediction && <span className="chip__tag">for you</span>}
          </span>
        )}
      </span>

      <span className="card__body">
        <span className="card__title">{movie.title}</span>
        <span className="card__meta">
          {movie.year ?? "—"} · {movie.genres.slice(0, 2).join(", ")}
        </span>
      </span>
    </button>
  );
}