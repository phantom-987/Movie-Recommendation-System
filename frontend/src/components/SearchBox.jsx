import { useEffect, useRef, useState } from "react";
import { api } from "../api";

export default function SearchBox({ onSelect }) {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState([]);
  const [open, setOpen] = useState(false);
  const [error, setError] = useState(null);
  const boxRef = useRef(null);

  useEffect(() => {
    const term = query.trim();
    if (term.length < 2) {
      setResults([]);
      setError(null);
      return;
    }
    const timer = setTimeout(async () => {
      try {
        const data = await api.search(term);
        setResults(data.results);
        setError(null);
        setOpen(true);
      } catch (err) {
        setError(err.message);
      }
    }, 220);
    return () => clearTimeout(timer);
  }, [query]);

  useEffect(() => {
    const away = (e) => {
      if (boxRef.current && !boxRef.current.contains(e.target)) setOpen(false);
    };
    document.addEventListener("mousedown", away);
    return () => document.removeEventListener("mousedown", away);
  }, []);

  const pick = (movie) => {
    onSelect(movie);
    setOpen(false);
    setQuery("");
  };

  return (
    <div className="search" ref={boxRef}>
      <input
        type="search"
        value={query}
        placeholder="Search a movie to find five like it"
        onChange={(e) => setQuery(e.target.value)}
        onFocus={() => results.length && setOpen(true)}
        aria-label="Search movies"
      />

      {open && (
        <ul className="search__drop">
          {error && <li className="search__msg">{error}</li>}
          {!error && results.length === 0 && (
            <li className="search__msg">Nothing matches that title yet.</li>
          )}
          {results.map((m) => (
            <li key={m.movie_id}>
              <button type="button" onClick={() => pick(m)}>
                <span>{m.title}</span>
                <span className="search__year">{m.year ?? ""}</span>
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}