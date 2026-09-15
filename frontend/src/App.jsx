import { useCallback, useEffect, useState } from "react";
import { api } from "./api";
import GenrePicker from "./components/GenrePicker";
import MovieCard from "./components/MovieCard";
import Rail from "./components/Rail";
import SearchBox from "./components/SearchBox";
import SimilarSheet from "./components/SimilarSheet";

export default function App() {
  const [genres, setGenres] = useState([]);
  const [selected, setSelected] = useState([]);
  const [sections, setSections] = useState([]);
  const [picks, setPicks] = useState(null);
  const [userId, setUserId] = useState("");
  const [activeUser, setActiveUser] = useState(null);
  const [seed, setSeed] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Genre list once, on boot.
  useEffect(() => {
    api
      .genres()
      .then((d) => setGenres(d.genres))
      .catch((e) => setError(e.message));
  }, []);

  // The Netflix-style rows. Re-fetch when the user id changes so the rows
  // become personalised.
  useEffect(() => {
    let live = true;
    setLoading(true);
    api
      .sections(activeUser, 18)
      .then((d) => live && setSections(d.sections))
      .catch((e) => live && setError(e.message))
      .finally(() => live && setLoading(false));
    return () => {
      live = false;
    };
  }, [activeUser]);

  // Genre picks.
  useEffect(() => {
    if (selected.length === 0) {
      setPicks(null);
      return;
    }
    let live = true;
    api
      .byGenre(selected, activeUser, 24)
      .then((d) => live && setPicks(d))
      .catch((e) => live && setError(e.message));
    return () => {
      live = false;
    };
  }, [selected, activeUser]);

  const toggleGenre = useCallback((genre) => {
    setSelected((cur) =>
      cur.includes(genre) ? cur.filter((g) => g !== genre) : [...cur, genre]
    );
  }, []);

  const applyUser = (e) => {
    e.preventDefault();
    const parsed = parseInt(userId, 10);
    setActiveUser(Number.isNaN(parsed) ? null : parsed);
  };

  return (
    <div className="app">
      <header className="top">
        <div className="top__brand">
          <span className="top__mark">Reel</span>
          <span className="top__markAlt">Sense</span>
        </div>

        <SearchBox onSelect={setSeed} />

        <form className="top__user" onSubmit={applyUser}>
          <input
            type="number"
            min="1"
            value={userId}
            placeholder="MovieLens user ID"
            onChange={(e) => setUserId(e.target.value)}
            aria-label="MovieLens user ID"
          />
          <button type="submit">Use profile</button>
        </form>
      </header>

      <main>
        <section className="hero">
          <h1>
            Tell it what you're in the mood for.
            <br />
            It reads 1&nbsp;million ratings and answers.
          </h1>
          <p>
            {activeUser
              ? `Ranking everything through user ${activeUser}'s taste profile.`
              : "Ranking by how the crowd rated. Add a user ID above to make it personal."}
          </p>
          <GenrePicker
            genres={genres}
            selected={selected}
            onToggle={toggleGenre}
            onClear={() => setSelected([])}
          />
        </section>

        {error && <p className="state state--bad">{error}</p>}

        {picks && (
          <section className="picks">
            <h2 className="picks__title">
              {picks.personalized ? "Predicted for you" : "Top rated"} in{" "}
              {picks.genres.join(" + ")}
            </h2>
            <div className="picks__grid">
              {picks.results.map((m) => (
                <MovieCard key={m.movie_id} movie={m} onSelect={setSeed} />
              ))}
            </div>
            {picks.results.length === 0 && (
              <p className="state">Nothing left in that combination. Try fewer genres.</p>
            )}
          </section>
        )}

        {loading && <p className="state">Loading the catalog…</p>}

        {!loading &&
          sections.map((s) => (
            <Rail
              key={s.genre}
              title={s.genre}
              subtitle={s.personalized ? "Predicted from your ratings" : "Highest rated"}
              movies={s.items}
              onSelect={setSeed}
            />
          ))}
      </main>

      <footer className="foot">
        SVD collaborative filtering on MovieLens 32M · Precision@10 0.596
      </footer>

      {seed && (
        <SimilarSheet movie={seed} onClose={() => setSeed(null)} onSelect={setSeed} />
      )}
    </div>
  );
}