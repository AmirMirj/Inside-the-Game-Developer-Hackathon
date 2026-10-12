import type {
  CompareResponse,
  MatchRecap,
  MatchState,
  MultiLangRecap,
  RenderPayload,
  StoryBeat,
} from "./types";

export const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE?.replace(/\/$/, "") || "http://127.0.0.1:8000";

export const DEFAULT_MATCH_ID =
  process.env.NEXT_PUBLIC_DEFAULT_MATCH_ID || "syn-northbridge-harbor-001";

export type MatchSummary = {
  match_id: string;
  label?: string;
  synthetic?: boolean;
  kind?: string;
};

export async function fetchMatches(): Promise<MatchSummary[]> {
  const res = await fetch(`${API_BASE}/api/v1/matches`, { cache: "no-store" });
  if (!res.ok) throw new Error(`Failed to load matches (${res.status})`);
  return res.json();
}

export async function fetchRenderTimeline(
  matchId: string,
  limit = 20,
): Promise<RenderPayload[]> {
  const url = new URL(`${API_BASE}/api/v1/matches/${matchId}/render/timeline`);
  url.searchParams.set("use_mock", "true");
  url.searchParams.set("min_priority", "medium");
  url.searchParams.set("limit", String(limit));
  const res = await fetch(url.toString(), { cache: "no-store" });
  if (!res.ok) throw new Error(`Failed to load timeline (${res.status})`);
  return res.json();
}

export async function compareAtSeq(
  matchId: string,
  seq: number,
  opts: { favoriteClubId?: string; playerFocus?: string } = {},
): Promise<CompareResponse> {
  const url = new URL(
    `${API_BASE}/api/v1/matches/${matchId}/personalize/${seq}/compare`,
  );
  url.searchParams.set("favorite_club_id", opts.favoriteClubId || "northbridge");
  url.searchParams.set("player_focus", opts.playerFocus || "nb-9");
  const res = await fetch(url.toString(), { method: "POST", cache: "no-store" });
  if (!res.ok) {
    const detail = await res.text();
    throw new Error(`Compare failed (${res.status}): ${detail}`);
  }
  return res.json();
}

export async function compareInsight(
  insight: Record<string, unknown>,
  state: MatchState | null,
  opts: { favoriteClubId?: string; playerFocus?: string } = {},
): Promise<CompareResponse> {
  const fan = {
    profile_id: "ui-fan",
    role: "fan",
    language: "en",
    favorite_club_ids: [opts.favoriteClubId || "northbridge"],
    favorite_player_ids: [opts.playerFocus || "nb-9"],
    modes: { player_focus: opts.playerFocus || "nb-9", metric_focus: null },
  };
  const analyst = {
    profile_id: "ui-analyst",
    role: "analyst",
    language: "en",
    favorite_club_ids: [],
    favorite_player_ids: [],
    modes: { player_focus: null, metric_focus: "pressure" },
  };
  const res = await fetch(`${API_BASE}/api/v1/personalize/compare`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ insight, state, fan, analyst }),
    cache: "no-store",
  });
  if (!res.ok) throw new Error(`Compare failed (${res.status})`);
  return res.json();
}

export async function fetchFirstMomentSeq(matchId: string): Promise<number> {
  const res = await fetch(`${API_BASE}/api/v1/matches/${matchId}/moments`, {
    cache: "no-store",
  });
  if (!res.ok) throw new Error(`Moments failed (${res.status})`);
  const moments = (await res.json()) as { event_seq: number }[];
  if (!moments.length) throw new Error("No moments for this match");
  return moments[0].event_seq;
}

export function streamUrl(
  matchId: string,
  opts: { speed?: number; includeState?: boolean; includeInsights?: boolean } = {},
): string {
  const url = new URL(`${API_BASE}/api/v1/matches/${matchId}/stream`);
  url.searchParams.set("speed", String(opts.speed ?? 8));
  url.searchParams.set("include_state", String(opts.includeState ?? true));
  url.searchParams.set("include_insights", String(opts.includeInsights ?? true));
  return url.toString();
}

export async function fetchNarrativeBeats(
  matchId: string,
  language: "en" | "es" = "en",
): Promise<StoryBeat[]> {
  const url = new URL(`${API_BASE}/api/v1/matches/${matchId}/narrative/beats`);
  url.searchParams.set("language", language);
  url.searchParams.set("min_priority", "medium");
  const res = await fetch(url.toString(), { cache: "no-store" });
  if (!res.ok) throw new Error(`Beats failed (${res.status})`);
  return res.json();
}

export async function fetchMultilangRecap(matchId: string): Promise<MultiLangRecap> {
  const res = await fetch(
    `${API_BASE}/api/v1/matches/${matchId}/narrative/recap/multilang`,
    { cache: "no-store" },
  );
  if (!res.ok) throw new Error(`Recap failed (${res.status})`);
  return res.json();
}

export async function fetchRecap(
  matchId: string,
  language: "en" | "es" = "en",
): Promise<MatchRecap> {
  const url = new URL(`${API_BASE}/api/v1/matches/${matchId}/narrative/recap`);
  url.searchParams.set("language", language);
  const res = await fetch(url.toString(), { cache: "no-store" });
  if (!res.ok) throw new Error(`Recap failed (${res.status})`);
  return res.json();
}
