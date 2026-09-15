// No poster art in the MovieLens data, so each tile gets a duotone built from
// its lead genre. Same genre always lands on the same hue pair, which makes
// the rows scannable without a single image request.

const GENRE_HUES = {
  Horror: [352, 288],
  Action: [14, 42],
  "Sci-Fi": [192, 258],
  Romance: [326, 12],
  Thriller: [268, 212],
  Comedy: [46, 84],
  Animation: [168, 202],
  Documentary: [28, 196],
  Drama: [222, 262],
  Crime: [240, 200],
  Adventure: [96, 160],
  Fantasy: [282, 320],
  Mystery: [206, 274],
};

const FALLBACK = [214, 250];

function hues(genres = []) {
  for (const g of genres) if (GENRE_HUES[g]) return GENRE_HUES[g];
  return FALLBACK;
}

// A tiny hash so two movies in the same genre don't look identical.
function jitter(seed, spread = 14) {
  let h = 0;
  for (const ch of String(seed)) h = (h * 31 + ch.charCodeAt(0)) % 997;
  return (h % spread) - spread / 2;
}

export function tileStyle(movie) {
  const [a, b] = hues(movie.genres);
  const j = jitter(movie.movie_id ?? movie.title);
  return {
    backgroundImage: `linear-gradient(152deg,
      hsl(${a + j} 58% 26%) 0%,
      hsl(${a + j} 44% 16%) 46%,
      hsl(${b + j} 40% 12%) 100%)`,
  };
}

export function genreHue(genre) {
  return hues([genre])[0];
}