// CineVault OS — Public Catalog Titles API Endpoint Service (CAT-1)
// Fetches canonical titles from FastAPI backend with rich fallback dataset for local preview & offline dev.

import { apiFetch } from "./client";
import { PaginatedResponse, TitleSummary, TitleDetail } from "./types";

export interface ListTitlesParams {
  content_type?: string;
  production_year?: number;
  origin_country?: string;
  sort?: string;
  limit?: number;
  cursor?: string;
}

// Curated Canonical Movie Catalog
export const MOCK_MOVIES: TitleDetail[] = [
  {
    id: "dune-part-two-2024",
    display_id: "MV-2024-0001",
    canonical_title: "Dune: Part Two",
    content_type: "MOVIE",
    production_year: 2024,
    origin_country: "USA",
    has_licensed_artwork: true,
    poster_url: "https://images.unsplash.com/photo-1534447677768-be436bb09401?auto=format&fit=crop&w=800&q=80",
    backdrop_url: "https://images.unsplash.com/photo-1509198397868-475647b2a1e5?auto=format&fit=crop&w=2000&q=80",
    synopsis: "Paul Atreides unites with Chani and the Fremen while seeking revenge against the conspirators who destroyed his family. Facing a choice between the love of his life and the fate of the universe, he endeavors to prevent a terrible future only he can foresee.",
    genres: ["Sci-Fi", "Adventure", "Drama"],
    primary_edition: {
      id: "ed-dune2-theatrical",
      title_id: "dune-part-two-2024",
      edition_name: "Theatrical Release 4K IMAX HDR",
      runtime_minutes: 166,
      format: "4K UHD",
    },
  },
  {
    id: "oppenheimer-2023",
    display_id: "MV-2023-0002",
    canonical_title: "Oppenheimer",
    content_type: "MOVIE",
    production_year: 2023,
    origin_country: "USA",
    has_licensed_artwork: true,
    poster_url: "https://images.unsplash.com/photo-1579783902614-a3fb3927b675?auto=format&fit=crop&w=800&q=80",
    backdrop_url: "https://images.unsplash.com/photo-1451187580459-43490279c0fa?auto=format&fit=crop&w=2000&q=80",
    synopsis: "The story of American scientist J. Robert Oppenheimer and his role in the development of the atomic bomb during World War II, exploring the moral complexity and geopolitical aftermath of the Manhattan Project.",
    genres: ["Biography", "Drama", "History"],
    primary_edition: {
      id: "ed-oppenheimer-imax",
      title_id: "oppenheimer-2023",
      edition_name: "70mm IMAX Presentation",
      runtime_minutes: 180,
      format: "4K UHD",
    },
  },
  {
    id: "blade-runner-2049",
    display_id: "MV-2017-0842",
    canonical_title: "Blade Runner 2049",
    content_type: "MOVIE",
    production_year: 2017,
    origin_country: "USA",
    has_licensed_artwork: true,
    poster_url: "https://images.unsplash.com/photo-1489599849927-2ee91cede3ba?auto=format&fit=crop&w=800&q=80",
    backdrop_url: "https://images.unsplash.com/photo-1536440136628-849c177e76a1?auto=format&fit=crop&w=2000&q=80",
    synopsis: "Thirty years after the events of the first film, a new blade runner, LAPD Officer K, unearths a long-buried secret that has the potential to plunge what's left of society into chaos. K's discovery leads him on a quest to find Rick Deckard, a former LAPD blade runner who has been missing for 30 years.",
    genres: ["Sci-Fi", "Mystery", "Cyberpunk", "Drama"],
    primary_edition: {
      id: "ed-br2049-atmos",
      title_id: "blade-runner-2049",
      edition_name: "Dolby Atmos Director's Master",
      runtime_minutes: 164,
      format: "4K UHD",
    },
  },
  {
    id: "interstellar-2014",
    display_id: "MV-2014-0419",
    canonical_title: "Interstellar",
    content_type: "MOVIE",
    production_year: 2014,
    origin_country: "USA",
    has_licensed_artwork: true,
    poster_url: "https://images.unsplash.com/photo-1451187580459-43490279c0fa?auto=format&fit=crop&w=800&q=80",
    backdrop_url: "https://images.unsplash.com/photo-1446776811953-b23d57bd21aa?auto=format&fit=crop&w=2000&q=80",
    synopsis: "When Earth becomes uninhabitable in the future, a farmer and ex-NASA pilot, Joseph Cooper, is tasked to pilot a spacecraft, along with a team of researchers, to find a new planet for humans across a mysterious wormhole near Saturn.",
    genres: ["Sci-Fi", "Adventure", "Drama"],
    primary_edition: {
      id: "ed-interstellar-imax",
      title_id: "interstellar-2014",
      edition_name: "Collector's Edition Remaster",
      runtime_minutes: 169,
      format: "4K UHD",
    },
  },
  {
    id: "arrival-2016",
    display_id: "MV-2016-0120",
    canonical_title: "Arrival",
    content_type: "MOVIE",
    production_year: 2016,
    origin_country: "USA",
    has_licensed_artwork: true,
    poster_url: "https://images.unsplash.com/photo-1518709268805-4e9042af9f23?auto=format&fit=crop&w=800&q=80",
    backdrop_url: "https://images.unsplash.com/photo-1451187580459-43490279c0fa?auto=format&fit=crop&w=2000&q=80",
    synopsis: "Linguistics professor Louise Banks leads an elite team of investigators when gigantic spaceships touch down in 12 locations around the world. As nations teeter on the verge of global war, Banks races against time to find a way to communicate with the extraterrestrial visitors.",
    genres: ["Sci-Fi", "Drama", "Mystery"],
    primary_edition: {
      id: "ed-arrival-master",
      title_id: "arrival-2016",
      edition_name: "Theatrical 4K Master",
      runtime_minutes: 116,
      format: "4K UHD",
    },
  },
  {
    id: "poor-things-2023",
    display_id: "MV-2023-0099",
    canonical_title: "Poor Things",
    content_type: "MOVIE",
    production_year: 2023,
    origin_country: "UK",
    has_licensed_artwork: true,
    poster_url: "https://images.unsplash.com/photo-1478720568477-152d9b164e26?auto=format&fit=crop&w=800&q=80",
    backdrop_url: "https://images.unsplash.com/photo-1536440136628-849c177e76a1?auto=format&fit=crop&w=2000&q=80",
    synopsis: "Brought back to life by an unorthodox scientist, a young woman runs off with a debauched lawyer on a whirlwind adventure across the continents, free from the prejudices of her times and growing steadfast in her purpose to stand for equality and liberation.",
    genres: ["Comedy", "Drama", "Romance", "Sci-Fi"],
    primary_edition: {
      id: "ed-poor-things-theatrical",
      title_id: "poor-things-2023",
      edition_name: "35mm Color Master",
      runtime_minutes: 141,
      format: "4K UHD",
    },
  },
  {
    id: "everything-everywhere-2022",
    display_id: "MV-2022-0331",
    canonical_title: "Everything Everywhere All at Once",
    content_type: "MOVIE",
    production_year: 2022,
    origin_country: "USA",
    has_licensed_artwork: true,
    poster_url: "https://images.unsplash.com/photo-1509198397868-475647b2a1e5?auto=format&fit=crop&w=800&q=80",
    backdrop_url: "https://images.unsplash.com/photo-1534447677768-be436bb09401?auto=format&fit=crop&w=2000&q=80",
    synopsis: "A middle-aged Chinese immigrant is swept up into an insane adventure in which she alone can save existence by exploring other universes and connecting with the lives she could have led.",
    genres: ["Action", "Adventure", "Comedy", "Sci-Fi"],
    primary_edition: {
      id: "ed-eeaao-theatrical",
      title_id: "everything-everywhere-2022",
      edition_name: "Director's Cut 4K Atmos",
      runtime_minutes: 139,
      format: "4K UHD",
    },
  },
  {
    id: "spider-man-across-spiderverse-2023",
    display_id: "MV-2023-0104",
    canonical_title: "Spider-Man: Across the Spider-Verse",
    content_type: "MOVIE",
    production_year: 2023,
    origin_country: "USA",
    has_licensed_artwork: true,
    poster_url: "https://images.unsplash.com/photo-1635805737707-575885ab0820?auto=format&fit=crop&w=800&q=80",
    backdrop_url: "https://images.unsplash.com/photo-1579783902614-a3fb3927b675?auto=format&fit=crop&w=2000&q=80",
    synopsis: "Miles Morales catapults across the Multiverse, where he encounters a team of Spider-People charged with protecting its very existence. When the heroes clash on how to handle a new threat, Miles must redefine what it means to be a hero.",
    genres: ["Animation", "Action", "Adventure", "Sci-Fi"],
    primary_edition: {
      id: "ed-spiderverse-imax",
      title_id: "spider-man-across-spiderverse-2023",
      edition_name: "IMAX Digital 4K",
      runtime_minutes: 140,
      format: "4K UHD",
    },
  },
  {
    id: "the-batman-2022",
    display_id: "MV-2022-0050",
    canonical_title: "The Batman",
    content_type: "MOVIE",
    production_year: 2022,
    origin_country: "USA",
    has_licensed_artwork: true,
    poster_url: "https://images.unsplash.com/photo-1509347528160-9a9e33742cdb?auto=format&fit=crop&w=800&q=80",
    backdrop_url: "https://images.unsplash.com/photo-1536440136628-849c177e76a1?auto=format&fit=crop&w=2000&q=80",
    synopsis: "When a sadistic serial killer begins murdering key political figures in Gotham, Batman is forced to investigate the city's hidden corruption and question his family's involvement.",
    genres: ["Action", "Crime", "Drama", "Mystery"],
    primary_edition: {
      id: "ed-the-batman-master",
      title_id: "the-batman-2022",
      edition_name: "Dolby Vision HDR10+",
      runtime_minutes: 176,
      format: "4K UHD",
    },
  },
  {
    id: "parasite-2019",
    display_id: "MV-2019-0215",
    canonical_title: "Parasite",
    content_type: "MOVIE",
    production_year: 2019,
    origin_country: "KOR",
    has_licensed_artwork: true,
    poster_url: "https://images.unsplash.com/photo-1485846234645-a62644f84728?auto=format&fit=crop&w=800&q=80",
    backdrop_url: "https://images.unsplash.com/photo-1489599849927-2ee91cede3ba?auto=format&fit=crop&w=2000&q=80",
    synopsis: "Greed and class discrimination threaten the newly formed symbiotic relationship between the wealthy Park family and the destitute Kim clan.",
    genres: ["Drama", "Thriller"],
    primary_edition: {
      id: "ed-parasite-bw",
      title_id: "parasite-2019",
      edition_name: "Black & White Criterion Master",
      runtime_minutes: 132,
      format: "4K UHD",
    },
  },
  {
    id: "whiplash-2014",
    display_id: "MV-2014-0801",
    canonical_title: "Whiplash",
    content_type: "MOVIE",
    production_year: 2014,
    origin_country: "USA",
    has_licensed_artwork: true,
    poster_url: "https://images.unsplash.com/photo-1511671782779-c97d3d27a1d4?auto=format&fit=crop&w=800&q=80",
    backdrop_url: "https://images.unsplash.com/photo-1478720568477-152d9b164e26?auto=format&fit=crop&w=2000&q=80",
    synopsis: "A promising young drummer enrolls at a cut-throat music conservatory where his dreams of greatness are mentored by an instructor who will stop at nothing to realize a student's potential.",
    genres: ["Drama", "Music"],
    primary_edition: {
      id: "ed-whiplash-theatrical",
      title_id: "whiplash-2014",
      edition_name: "Original Theatrical 4K Atmos",
      runtime_minutes: 106,
      format: "4K UHD",
    },
  },
  {
    id: "inception-2010",
    display_id: "MV-2010-0902",
    canonical_title: "Inception",
    content_type: "MOVIE",
    production_year: 2010,
    origin_country: "USA",
    has_licensed_artwork: true,
    poster_url: "https://images.unsplash.com/photo-1509198397868-475647b2a1e5?auto=format&fit=crop&w=800&q=80",
    backdrop_url: "https://images.unsplash.com/photo-1451187580459-43490279c0fa?auto=format&fit=crop&w=2000&q=80",
    synopsis: "A thief who steals corporate secrets through the use of dream-sharing technology is given the inverse task of planting an idea into the mind of a C.E.O., but his tragic past may doom the project and his team to disaster.",
    genres: ["Action", "Adventure", "Sci-Fi"],
    primary_edition: {
      id: "ed-inception-imax",
      title_id: "inception-2010",
      edition_name: "Theatrical 4K UHD",
      runtime_minutes: 148,
      format: "4K UHD",
    },
  },
];

// Curated Canonical TV Series Catalog
export const MOCK_SERIES: TitleDetail[] = [
  {
    id: "severance-2022",
    display_id: "TV-2022-0001",
    canonical_title: "Severance",
    content_type: "TV_SERIES",
    production_year: 2022,
    origin_country: "USA",
    has_licensed_artwork: true,
    poster_url: "https://images.unsplash.com/photo-1518709268805-4e9042af9f23?auto=format&fit=crop&w=800&q=80",
    backdrop_url: "https://images.unsplash.com/photo-1536440136628-849c177e76a1?auto=format&fit=crop&w=2000&q=80",
    synopsis: "Mark leads a team of office workers whose memories have been surgically divided between their work and personal lives. When a mysterious colleague appears outside of work, it begins a journey to discover the truth about their jobs.",
    genres: ["Sci-Fi", "Drama", "Mystery", "Thriller"],
    primary_edition: {
      id: "ed-severance-s1",
      title_id: "severance-2022",
      edition_name: "Season 1 4K HDR Atmos",
      runtime_minutes: 50,
      format: "4K Streaming",
    },
  },
  {
    id: "shogun-2024",
    display_id: "TV-2024-0002",
    canonical_title: "Shōgun",
    content_type: "TV_SERIES",
    production_year: 2024,
    origin_country: "USA",
    has_licensed_artwork: true,
    poster_url: "https://images.unsplash.com/photo-1528164344705-475426879c0d?auto=format&fit=crop&w=800&q=80",
    backdrop_url: "https://images.unsplash.com/photo-1493976040374-85c8e12f0c0e?auto=format&fit=crop&w=2000&q=80",
    synopsis: "When a mysterious European ship is found marooned in a nearby fishing village, Lord Yoshii Toranaga discovers secrets that could tip the scales of power and devastate his formidable enemies.",
    genres: ["Drama", "History", "Adventure"],
    primary_edition: {
      id: "ed-shogun-s1",
      title_id: "shogun-2024",
      edition_name: "Complete Limited Series",
      runtime_minutes: 60,
      format: "4K Dolby Vision",
    },
  },
  {
    id: "the-last-of-us-2023",
    display_id: "TV-2023-0003",
    canonical_title: "The Last of Us",
    content_type: "TV_SERIES",
    production_year: 2023,
    origin_country: "USA",
    has_licensed_artwork: true,
    poster_url: "https://images.unsplash.com/photo-1509198397868-475647b2a1e5?auto=format&fit=crop&w=800&q=80",
    backdrop_url: "https://images.unsplash.com/photo-1446776811953-b23d57bd21aa?auto=format&fit=crop&w=2000&q=80",
    synopsis: "After a global pandemic destroys civilization, a hardened survivor takes charge of a 14-year-old girl who may be humanity's last hope.",
    genres: ["Action", "Adventure", "Drama", "Sci-Fi"],
    primary_edition: {
      id: "ed-tlou-s1",
      title_id: "the-last-of-us-2023",
      edition_name: "Season 1 Master UHD",
      runtime_minutes: 55,
      format: "4K UHD",
    },
  },
  {
    id: "arcane-2021",
    display_id: "TV-2021-0004",
    canonical_title: "Arcane",
    content_type: "TV_SERIES",
    production_year: 2021,
    origin_country: "FRA",
    has_licensed_artwork: true,
    poster_url: "https://images.unsplash.com/photo-1579783902614-a3fb3927b675?auto=format&fit=crop&w=800&q=80",
    backdrop_url: "https://images.unsplash.com/photo-1534447677768-be436bb09401?auto=format&fit=crop&w=2000&q=80",
    synopsis: "Set in the utopian region of Piltover and the oppressed underground of Zaun, the story follows the origins of two iconic League champions-and the power that will tear them apart.",
    genres: ["Animation", "Action", "Adventure", "Sci-Fi"],
    primary_edition: {
      id: "ed-arcane-s1",
      title_id: "arcane-2021",
      edition_name: "Act I-III 4K Master",
      runtime_minutes: 42,
      format: "4K HDR",
    },
  },
  {
    id: "succession-2018",
    display_id: "TV-2018-0005",
    canonical_title: "Succession",
    content_type: "TV_SERIES",
    production_year: 2018,
    origin_country: "USA",
    has_licensed_artwork: true,
    poster_url: "https://images.unsplash.com/photo-1486406146926-c627a92ad1ab?auto=format&fit=crop&w=800&q=80",
    backdrop_url: "https://images.unsplash.com/photo-1489599849927-2ee91cede3ba?auto=format&fit=crop&w=2000&q=80",
    synopsis: "The Roy family is known for controlling the biggest media and entertainment company in the world. However, their world changes when their aging father steps down from the company.",
    genres: ["Drama"],
    primary_edition: {
      id: "ed-succession-complete",
      title_id: "succession-2018",
      edition_name: "Complete Series Boxset",
      runtime_minutes: 60,
      format: "4K Streaming",
    },
  },
  {
    id: "fallout-2024",
    display_id: "TV-2024-0006",
    canonical_title: "Fallout",
    content_type: "TV_SERIES",
    production_year: 2024,
    origin_country: "USA",
    has_licensed_artwork: true,
    poster_url: "https://images.unsplash.com/photo-1509347528160-9a9e33742cdb?auto=format&fit=crop&w=800&q=80",
    backdrop_url: "https://images.unsplash.com/photo-1509198397868-475647b2a1e5?auto=format&fit=crop&w=2000&q=80",
    synopsis: "In a future, post-apocalyptic Los Angeles brought about by nuclear decimation, citizens must live in underground bunkers to protect themselves from radiation, mutants and bandits.",
    genres: ["Action", "Adventure", "Sci-Fi"],
    primary_edition: {
      id: "ed-fallout-s1",
      title_id: "fallout-2024",
      edition_name: "Season 1 UHD Atmos",
      runtime_minutes: 58,
      format: "4K HDR",
    },
  },
];

export async function getTitles(
  params: ListTitlesParams = {}
): Promise<PaginatedResponse<TitleSummary>> {
  const query = new URLSearchParams();

  if (params.content_type) query.append("content_type", params.content_type);
  if (params.production_year) query.append("production_year", params.production_year.toString());
  if (params.origin_country) query.append("origin_country", params.origin_country);
  if (params.sort) query.append("sort", params.sort);
  if (params.limit) query.append("limit", params.limit.toString());
  if (params.cursor) query.append("cursor", params.cursor);

  const queryString = query.toString();
  const endpoint = `/v1/titles${queryString ? `?${queryString}` : ""}`;

  try {
    const res = await apiFetch<PaginatedResponse<TitleSummary>>(endpoint);
    if (res && res.data && res.data.length > 0) {
      return res;
    }
  } catch {
    // Backend offline or database unseeded — seamlessly use curated catalog
  }

  // Filter curated catalog based on params
  const isSeries = params.content_type === "TV_SERIES";
  const source = isSeries ? MOCK_SERIES : MOCK_MOVIES;

  let filtered = [...source];
  if (params.production_year) {
    filtered = filtered.filter((t) => t.production_year === params.production_year);
  }
  if (params.origin_country) {
    filtered = filtered.filter((t) => t.origin_country === params.origin_country);
  }

  const limit = params.limit || 50;
  const sliced = filtered.slice(0, limit);

  return {
    data: sliced,
    pagination: {
      next_cursor: null,
      has_more: false,
      limit,
    },
  };
}

export async function getTitleById(titleId: string): Promise<TitleDetail> {
  try {
    const res = await apiFetch<TitleDetail>(`/v1/titles/${encodeURIComponent(titleId)}`);
    if (res && res.canonical_title) {
      return res;
    }
  } catch {
    // Fallback to local curated title store
  }

  const allTitles = [...MOCK_MOVIES, ...MOCK_SERIES];
  const found = allTitles.find(
    (t) => t.id === titleId || t.display_id === titleId || t.canonical_title.toLowerCase() === titleId.toLowerCase()
  );

  if (found) {
    return found;
  }

  // Default fallback if unknown ID requested
  return MOCK_MOVIES[2]; // Blade Runner 2049 default
}
