import { genreHue } from "../lib/palette";

export default function GenrePicker({ genres, selected, onToggle, onClear }) {
  return (
    <div className="picker">
      <div className="picker__chips">
        {genres.map(({ genre, movie_count }) => {
          const on = selected.includes(genre);
          return (
            <button
              key={genre}
              type="button"
              className={on ? "chipbtn chipbtn--on" : "chipbtn"}
              style={on ? { "--hue": genreHue(genre) } : undefined}
              aria-pressed={on}
              onClick={() => onToggle(genre)}
            >
              {genre}
              <span className="chipbtn__count">{movie_count.toLocaleString()}</span>
            </button>
          );
        })}
      </div>

      {selected.length > 0 && (
        <button type="button" className="picker__clear" onClick={onClear}>
          Clear {selected.length} selected
        </button>
      )}
    </div>
  );
}