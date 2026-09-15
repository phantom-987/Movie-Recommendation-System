import { useRef } from "react";
import MovieCard from "./MovieCard";
import { genreHue } from "../lib/palette";

export default function Rail({ title, subtitle, movies, onSelect }) {
  const trackRef = useRef(null);

  const nudge = (direction) => {
    const track = trackRef.current;
    if (!track) return;
    track.scrollBy({ left: direction * track.clientWidth * 0.8, behavior: "smooth" });
  };

  if (!movies?.length) return null;

  return (
    <section className="rail">
      <header className="rail__head">
        <h2 className="rail__title">
          <span
            className="rail__tick"
            style={{ background: `hsl(${genreHue(title)} 70% 52%)` }}
            aria-hidden="true"
          />
          {title}
        </h2>
        {subtitle && <p className="rail__sub">{subtitle}</p>}
        <div className="rail__nav">
          <button type="button" onClick={() => nudge(-1)} aria-label={`Scroll ${title} left`}>
            ‹
          </button>
          <button type="button" onClick={() => nudge(1)} aria-label={`Scroll ${title} right`}>
            ›
          </button>
        </div>
      </header>

      <div className="rail__track" ref={trackRef}>
        {movies.map((m) => (
          <MovieCard key={m.movie_id} movie={m} onSelect={onSelect} />
        ))}
      </div>
    </section>
  );
}