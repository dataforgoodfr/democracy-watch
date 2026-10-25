import type { ReactNode } from "react";
import {
  type Board,
  EPICS,
  epicOf,
  githubUrl,
  ISSUES,
  type Issue,
  issueById,
  issuesOfBoard,
  STATUS_HELP,
  STATUSES,
} from "../roadmap/issues.ts";

/** Lien vers la fiche du ticket (06-roadmap/04-issues). */
const IssueLink = ({ id, children }: { id: string; children?: ReactNode }) => {
  const issue = issueById(id);
  return issue ? <a href={issue.path}>{children ?? id}</a> : <span>{id}</span>;
};

const GithubLink = ({ issue }: { issue: Issue }) =>
  issue.github ? <a href={githubUrl(issue.github)}>GitHub #{issue.github}</a> : null;

const Card = ({ issue }: { issue: Issue }) => {
  const epic = epicOf(issue);
  return (
    <li className="dw-card">
      <div className="dw-card-top">
        <IssueLink id={issue.id} />
        <span className="dw-card-tags">
          {issue.v0 ? <span className="dw-tag dw-tag-v0">V0</span> : null}
          {issue.size ? <span className="dw-tag">{issue.size}</span> : null}
        </span>
      </div>
      <p className="dw-card-title">
        <IssueLink id={issue.id}>{issue.title}</IssueLink>
      </p>
      <p className="dw-card-meta">
        {epic ? `${epic.id} · ${epic.title}` : null}
        {issue.github ? (
          <>
            {" · "}
            <GithubLink issue={issue} />
          </>
        ) : null}
      </p>
      {issue.dependsOn?.length ? (
        <p className="dw-card-meta">
          Dépend de{" "}
          {issue.dependsOn.map((id, index) => (
            <span key={id}>
              {index > 0 ? ", " : null}
              <IssueLink id={id} />
            </span>
          ))}
        </p>
      ) : null}
      {issue.note ? <p className="dw-card-note">{issue.note}</p> : null}
    </li>
  );
};

/** Tableau Kanban d'un des deux espaces : une colonne par statut. */
export const Kanban = ({ board }: { board: Board }) => {
  const issues = issuesOfBoard(board);
  return (
    <section className="dw-kanban not-prose" aria-label="Kanban">
      {STATUSES.map((status) => {
        const items = issues.filter((issue) => issue.status === status);
        return (
          <section
            key={status}
            className="dw-column"
            data-status={status}
            aria-label={`${status} — ${items.length}`}
          >
            <header className="dw-column-header" title={STATUS_HELP[status]}>
              <h3>{status}</h3>
              <span>{items.length}</span>
            </header>
            <p className="dw-column-help">{STATUS_HELP[status]}</p>
            {items.length === 0 ? (
              <p className="dw-column-empty">—</p>
            ) : (
              <ul>
                {items.map((issue) => (
                  <Card key={issue.id} issue={issue} />
                ))}
              </ul>
            )}
          </section>
        );
      })}
    </section>
  );
};

/** Grandes structures thématiques d'un espace, avec leur avancement. */
export const Epics = ({ board }: { board?: Board }) => (
  <table>
    <thead>
      <tr>
        <th>Épique</th>
        <th>Objectif</th>
        <th>Issue chapeau</th>
        <th>Avancement</th>
      </tr>
    </thead>
    <tbody>
      {EPICS.filter((epic) => !board || epic.board === board).map((epic) => {
        const items = ISSUES.filter((issue) => issue.epic === epic.id);
        const done = items.filter((issue) => issue.status === "Done").length;
        const review = items.filter((issue) => issue.status === "In Review").length;
        return (
          <tr key={epic.id}>
            <td>
              <strong>
                {epic.id} · {epic.title}
              </strong>
            </td>
            <td>{epic.goal}</td>
            <td>{epic.github ? <a href={githubUrl(epic.github)}>#{epic.github}</a> : "à créer"}</td>
            <td>
              {done} fait{done > 1 ? "s" : ""} · {review} en revue · {items.length} au total
            </td>
          </tr>
        );
      })}
    </tbody>
  </table>
);
