import { useEffect, useState } from "react";
import {
  getSummary,
  getTeamsOverview,
  type InsightsSummary,
  type TeamInsight,
} from "../api/client";

interface DashboardProps {
  token: string;
  onLogout: () => void;
}

export function Dashboard({ token, onLogout }: DashboardProps) {
  const [summary, setSummary] = useState<InsightsSummary | null>(null);
  const [teams, setTeams] = useState<TeamInsight[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([getSummary(token), getTeamsOverview(token)])
      .then(([s, t]) => {
        setSummary(s);
        setTeams(t);
      })
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load"));
  }, [token]);

  return (
    <div style={{ maxWidth: 900, margin: "40px auto", fontFamily: "sans-serif" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <h1>ACME Team Overview</h1>
        <button onClick={onLogout}>Log out</button>
      </div>

      {error && <p style={{ color: "crimson" }}>{error}</p>}

      {summary && (
        <div style={{ display: "flex", gap: 16, marginBottom: 24, flexWrap: "wrap" }}>
          <StatCard label="Total teams" value={summary.total_teams} />
          <StatCard
            label="Leader not co-located"
            value={summary.teams_with_leader_not_colocated}
          />
          <StatCard
            label="Non-direct staff leaders"
            value={summary.teams_with_non_direct_leader}
          />
          <StatCard
            label="Non-direct ratio > 20%"
            value={summary.teams_with_high_non_direct_ratio}
          />
          <StatCard
            label="Report to org leader"
            value={summary.teams_reporting_to_org_leader}
          />
        </div>
      )}

      <table style={{ width: "100%", borderCollapse: "collapse" }}>
        <thead>
          <tr style={{ textAlign: "left", borderBottom: "2px solid #ddd" }}>
            <th>Team</th>
            <th>Location</th>
            <th>Leader</th>
            <th>Members</th>
            <th>Non-direct ratio</th>
            <th>Co-located</th>
            <th>Reports to org leader</th>
          </tr>
        </thead>
        <tbody>
          {teams.map((team) => (
            <tr key={team.id} style={{ borderBottom: "1px solid #eee" }}>
              <td>{team.name}</td>
              <td>{team.location}</td>
              <td>
                {team.leader ? `${team.leader.first_name} ${team.leader.last_name}` : "—"}
              </td>
              <td>{team.member_count}</td>
              <td>{(team.non_direct_staff_ratio * 100).toFixed(0)}%</td>
              <td>{team.leader_co_located ? "Yes" : "No"}</td>
              <td>{team.reports_to_org_leader ? "Yes" : "No"}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function StatCard({ label, value }: { label: string; value: number }) {
  return (
    <div style={{ border: "1px solid #ddd", borderRadius: 8, padding: 12, minWidth: 140 }}>
      <div style={{ fontSize: 12, color: "#666" }}>{label}</div>
      <div style={{ fontSize: 28, fontWeight: 600 }}>{value}</div>
    </div>
  );
}
