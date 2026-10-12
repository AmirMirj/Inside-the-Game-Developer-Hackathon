"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import { EventTicker } from "@/components/EventTicker";
import { InsightCard } from "@/components/InsightCard";
import { MatchStatePanel } from "@/components/MatchStatePanel";
import { RecapPanel } from "@/components/RecapPanel";
import { Timeline } from "@/components/Timeline";
import {
  API_BASE,
  DEFAULT_MATCH_ID,
  compareAtSeq,
  compareInsight,
  fetchFirstMomentSeq,
  fetchMatches,
  fetchMultilangRecap,
  fetchNarrativeBeats,
  fetchRenderTimeline,
  streamUrl,
  type MatchSummary,
} from "@/lib/api";
import type {
  CompareResponse,
  MatchEvent,
  MatchRecap,
  MatchState,
  MultiLangRecap,
  RenderPayload,
  StoryBeat,
  StreamTick,
} from "@/lib/types";

export function StudioConsole() {
  const [matches, setMatches] = useState<MatchSummary[]>([]);
  const [matchId, setMatchId] = useState(DEFAULT_MATCH_ID);
  const [speed, setSpeed] = useState(12);
  const [favoriteClub, setFavoriteClub] = useState("northbridge");
  const [playerFocus, setPlayerFocus] = useState("nb-9");
  const [running, setRunning] = useState(false);
  const [events, setEvents] = useState<MatchEvent[]>([]);
  const [state, setState] = useState<MatchState | null>(null);
  const [compare, setCompare] = useState<CompareResponse | null>(null);
  const [baseRender, setBaseRender] = useState<RenderPayload | null>(null);
  const [timeline, setTimeline] = useState<RenderPayload[]>([]);
  const [activeTimelineId, setActiveTimelineId] = useState<string | null>(null);
  const [recapLang, setRecapLang] = useState<"en" | "es">("en");
  const [beats, setBeats] = useState<StoryBeat[]>([]);
  const [multilang, setMultilang] = useState<MultiLangRecap | null>(null);
  const [recapLoading, setRecapLoading] = useState(false);
  const [status, setStatus] = useState(
    "Idle — start live, load replay, prove Fan vs Analyst, or generate a recap.",
  );
  const [error, setError] = useState<string | null>(null);
  const sourceRef = useRef<EventSource | null>(null);

  const activeRecap: MatchRecap | null = multilang?.recaps?.[recapLang] || null;

  const profileOpts = useMemo(
    () => ({ favoriteClubId: favoriteClub, playerFocus }),
    [favoriteClub, playerFocus],
  );

  useEffect(() => {
    fetchMatches()
      .then((list) => {
        setMatches(list);
        if (list.length && !list.some((m) => m.match_id === matchId)) {
          setMatchId(list[0].match_id);
        }
      })
      .catch((err: Error) => setError(err.message));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const stopStream = useCallback(() => {
    sourceRef.current?.close();
    sourceRef.current = null;
    setRunning(false);
  }, []);

  useEffect(() => () => stopStream(), [stopStream]);

  const applyCompare = useCallback((result: CompareResponse) => {
    setCompare(result);
    setBaseRender(null);
  }, []);

  const personalizeFromInsight = useCallback(
    async (insight: Record<string, unknown>, liveState: MatchState | null) => {
      try {
        const result = await compareInsight(insight, liveState, profileOpts);
        applyCompare(result);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Personalize failed");
      }
    },
    [applyCompare, profileOpts],
  );

  const startStream = useCallback(() => {
    stopStream();
    setEvents([]);
    setState(null);
    setCompare(null);
    setBaseRender(null);
    setError(null);
    setStatus(`Streaming ${matchId} @ speed ${speed}…`);
    setRunning(true);

    const url = streamUrl(matchId, {
      speed,
      includeState: true,
      includeInsights: true,
    });
    const es = new EventSource(url);
    sourceRef.current = es;

    const onTick = (raw: MessageEvent<string>) => {
      try {
        const tick = JSON.parse(raw.data) as StreamTick;
        if (tick.event) {
          setEvents((prev) => [...prev, tick.event]);
        }
        if (tick.state) setState(tick.state);
        if (tick.insight) {
          void personalizeFromInsight(tick.insight, tick.state || null);
        } else if (tick.render) {
          setBaseRender(tick.render);
        }
      } catch {
        setError("Failed to parse stream tick");
      }
    };

    es.addEventListener("match_tick", onTick as EventListener);
    es.addEventListener("match_event", onTick as EventListener);
    es.addEventListener("stream_end", () => {
      setStatus("Stream complete.");
      stopStream();
    });
    es.onerror = () => {
      setError(`Stream error — is the API running at ${API_BASE}?`);
      setStatus("Stream disconnected.");
      stopStream();
    };
  }, [matchId, personalizeFromInsight, speed, stopStream]);

  const loadTimeline = useCallback(async () => {
    setError(null);
    setStatus("Loading render timeline…");
    try {
      const items = await fetchRenderTimeline(matchId, 25);
      setTimeline(items);
      setStatus(`Loaded ${items.length} timed overlays for replay.`);
      if (items[0]?.source_event_seq != null) {
        const result = await compareAtSeq(
          matchId,
          items[0].source_event_seq,
          profileOpts,
        );
        applyCompare(result);
        setActiveTimelineId(items[0].render_id);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Timeline load failed");
    }
  }, [applyCompare, matchId, profileOpts]);

  const proveFanVsAnalyst = useCallback(async () => {
    setError(null);
    setStatus("Building Fan vs Analyst for one moment…");
    try {
      const seq = await fetchFirstMomentSeq(matchId);
      const result = await compareAtSeq(matchId, seq, profileOpts);
      applyCompare(result);
      setStatus(`Same moment (seq ${seq}) — Fan copy vs Analyst copy.`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Compare failed");
    }
  }, [applyCompare, matchId, profileOpts]);

  const onTimelineSelect = useCallback(
    async (item: RenderPayload) => {
      setActiveTimelineId(item.render_id);
      setBaseRender(item);
      if (item.source_event_seq == null) {
        setCompare(null);
        return;
      }
      try {
        const result = await compareAtSeq(
          matchId,
          item.source_event_seq,
          profileOpts,
        );
        applyCompare(result);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Compare failed");
      }
    },
    [applyCompare, matchId, profileOpts],
  );

  const generateNarrative = useCallback(async () => {
    setError(null);
    setRecapLoading(true);
    setStatus("Generating story beats + EN/ES recap…");
    try {
      const [beatList, multi] = await Promise.all([
        fetchNarrativeBeats(matchId, recapLang),
        fetchMultilangRecap(matchId),
      ]);
      setBeats(beatList);
      setMultilang(multi);
      const r = multi.recaps[recapLang];
      setStatus(
        r
          ? `Recap ready (${r.language.toUpperCase()}, ~${r.estimated_read_seconds}s / ${r.word_count} words).`
          : "Narrative generated.",
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "Narrative failed");
    } finally {
      setRecapLoading(false);
    }
  }, [matchId, recapLang]);

  const onRecapLanguageChange = useCallback(
    async (lang: "en" | "es") => {
      setRecapLang(lang);
      if (!multilang) return;
      try {
        const beatList = await fetchNarrativeBeats(matchId, lang);
        setBeats(beatList);
      } catch {
        /* keep existing beats if language swap for beats fails */
      }
    },
    [matchId, multilang],
  );

  const matchLabel = useMemo(() => {
    return matches.find((m) => m.match_id === matchId)?.label || matchId;
  }, [matchId, matches]);

  return (
    <div className="app-shell">
      <header className="brand-bar">
        <div>
          <div className="badge">Synthetic studio feed</div>
          <h1>Inside the Game</h1>
          <p>
            Live synthetic events, timed overlays, and Stage E personalization —
            same intelligence, Fan vs Analyst voices. {matchLabel}.
          </p>
        </div>
        <div className="clock">{state?.match_clock || "0:00"}</div>
      </header>

      <section className="controls" aria-label="Studio controls">
        <label>
          Match
          <select value={matchId} onChange={(e) => setMatchId(e.target.value)}>
            {(matches.length
              ? matches
              : [{ match_id: DEFAULT_MATCH_ID, label: DEFAULT_MATCH_ID }]
            ).map((m) => (
              <option key={m.match_id} value={m.match_id}>
                {m.label || m.match_id}
              </option>
            ))}
          </select>
        </label>
        <label>
          Stream speed
          <input
            type="number"
            min={1}
            max={10000}
            value={speed}
            onChange={(e) => setSpeed(Number(e.target.value) || 1)}
          />
        </label>
        <label>
          Favorite club
          <select
            value={favoriteClub}
            onChange={(e) => setFavoriteClub(e.target.value)}
          >
            <option value="northbridge">northbridge</option>
            <option value="harbor">harbor</option>
          </select>
        </label>
        <label>
          Player focus
          <select
            value={playerFocus}
            onChange={(e) => setPlayerFocus(e.target.value)}
          >
            <option value="nb-9">nb-9 M. Okonkwo</option>
            <option value="nb-7">nb-7 A. Reed</option>
            <option value="hb-10">hb-10 L. Vargas</option>
            <option value="hb-4">hb-4 J. Klein</option>
          </select>
        </label>
        <div className="actions">
          <button className="btn" type="button" onClick={startStream} disabled={running}>
            {running ? "Live…" : "Start live"}
          </button>
          <button className="btn secondary" type="button" onClick={stopStream} disabled={!running}>
            Stop
          </button>
          <button className="btn secondary" type="button" onClick={loadTimeline}>
            Load replay
          </button>
          <button className="btn secondary" type="button" onClick={proveFanVsAnalyst}>
            Prove Fan vs Analyst
          </button>
        </div>
      </section>

      <div className="layout">
        <section className="panel">
          <div className="panel-header">
            <h2>Match state</h2>
            <span className="pill">Stage B</span>
          </div>
          <MatchStatePanel state={state} />
          <div className="panel-header">
            <h2>Event ticker</h2>
            <span className="pill">Stage A</span>
          </div>
          <div className="panel-body">
            <EventTicker events={events} />
          </div>
        </section>

        <section className="panel">
          <div className="panel-header">
            <h2>Personalized overlays</h2>
            <span className="pill">Stage E</span>
          </div>
          <div className="panel-body">
            <p className="persona-note">
              Same moment · different copy. Fan leans story/club/player focus;
              Analyst leans pressure, rhythm, and metrics.
            </p>
            {compare ? (
              <div className="compare-grid">
                <InsightCard render={compare.fan} modeLabel="Fan" />
                <InsightCard render={compare.analyst} modeLabel="Analyst" />
              </div>
            ) : (
              <InsightCard
                render={baseRender}
                modeLabel="Base overlay (not yet personalized)"
              />
            )}
          </div>
          <div className="panel-header">
            <h2>Replay timeline</h2>
            <span className="pill">match clock</span>
          </div>
          <div className="panel-body">
            <Timeline
              items={timeline}
              activeId={activeTimelineId}
              onSelect={onTimelineSelect}
            />
          </div>
        </section>
      </div>

      <section className="panel layout-wide">
        <div className="panel-header">
          <h2>Narratives & recap</h2>
          <span className="pill">Stage 6 · EN/ES</span>
        </div>
        <RecapPanel
          beats={beats}
          recap={activeRecap}
          language={recapLang}
          onLanguageChange={onRecapLanguageChange}
          onGenerate={generateNarrative}
          loading={recapLoading}
        />
      </section>

      <p className={`status-line${error ? " error" : ""}`}>
        {error ? error : status}
      </p>
    </div>
  );
}
