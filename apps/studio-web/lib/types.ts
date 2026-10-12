export type Priority = "low" | "medium" | "high";

export type MatchEvent = {
  event_id: string;
  match_id: string;
  seq: number;
  match_clock: string;
  period: number;
  type: string;
  team_id?: string | null;
  player_id?: string | null;
  actors?: { role: string; player_id?: string | null; name?: string | null }[];
  payload?: Record<string, unknown>;
  ts: string;
  synthetic?: boolean;
};

export type MatchState = {
  match_id: string;
  match_clock: string;
  period: number;
  last_seq: number;
  score: { home: number; away: number };
  home_team_id?: string | null;
  away_team_id?: string | null;
  possessing_team_id?: string | null;
  teams: Record<
    string,
    {
      team_id: string;
      passes_attempted: number;
      pass_accuracy: number;
      shots: number;
      shots_on_target: number;
      goals: number;
      possession_pct: number;
    }
  >;
  pressure: { current: number; recent_avg: number; swing: number; tempo?: string };
  rhythm: { events_per_minute: number; tempo: string };
  last_pass_quality?: {
    distance_m?: number | null;
    accurate?: boolean | null;
    difficulty?: number | null;
  } | null;
  synthetic: boolean;
};

export type RenderPayload = {
  render_id: string;
  insight_id?: string | null;
  match_id: string;
  match_clock: string;
  duration_ms: number;
  priority: Priority;
  overlay_type: string;
  text: {
    headline: string;
    body: string;
    why_it_matters?: string | null;
  };
  entities: { kind: string; id: string; name?: string | null }[];
  source_event_seq?: number | null;
  trigger?: string | null;
  confidence?: number | null;
  synthetic: boolean;
};

export type StreamTick = {
  event: MatchEvent;
  state?: MatchState;
  insight?: Record<string, unknown>;
  render?: RenderPayload;
};

export type ViewerProfile = {
  profile_id: string;
  role: "fan" | "analyst" | "studio";
  language: string;
  favorite_club_ids: string[];
  favorite_player_ids: string[];
  modes: {
    player_focus?: string | null;
    metric_focus?: string | null;
  };
};

export type CompareResponse = {
  fan: RenderPayload;
  analyst: RenderPayload;
};

export type StoryBeat = {
  beat_id: string;
  match_id: string;
  match_clock: string;
  title: string;
  text: string;
  language: string;
  source_event_seq?: number | null;
  trigger?: string | null;
  priority?: Priority;
  synthetic?: boolean;
};

export type MatchRecap = {
  recap_id: string;
  match_id: string;
  language: string;
  title: string;
  body: string;
  word_count: number;
  estimated_read_seconds: number;
  milestones: { match_clock: string; label: string; trigger?: string | null }[];
  player_mentions: string[];
  score: { home: number; away: number };
  provider?: string;
  synthetic?: boolean;
};

export type MultiLangRecap = {
  match_id: string;
  languages: string[];
  recaps: Record<string, MatchRecap>;
  synthetic?: boolean;
};
