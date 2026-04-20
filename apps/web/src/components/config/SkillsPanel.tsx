import { useEffect, useState } from "react";

import { getSkill, listSkills } from "../../lib/api";
import type { SkillDetail, SkillSummary } from "../../types";

export function SkillsPanel() {
  const [skills, setSkills] = useState<SkillSummary[]>([]);
  const [selectedSkillName, setSelectedSkillName] = useState<string | null>(null);
  const [skillDetail, setSkillDetail] = useState<SkillDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [loadingDetail, setLoadingDetail] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;

    void listSkills()
      .then((items) => {
        if (!active) {
          return;
        }

        setSkills(items);
        setSelectedSkillName((current) => current ?? items[0]?.name ?? null);
      })
      .catch((caughtError: unknown) => {
        if (!active) {
          return;
        }

        setError(caughtError instanceof Error ? caughtError.message : "Failed to load skills.");
      })
      .finally(() => {
        if (active) {
          setLoading(false);
        }
      });

    return () => {
      active = false;
    };
  }, []);

  useEffect(() => {
    if (!selectedSkillName) {
      setSkillDetail(null);
      return;
    }

    let active = true;

    setLoadingDetail(true);
    setError(null);
    void getSkill(selectedSkillName)
      .then((detail) => {
        if (!active) {
          return;
        }

        setSkillDetail(detail);
      })
      .catch((caughtError: unknown) => {
        if (!active) {
          return;
        }

        setSkillDetail(null);
        setError(caughtError instanceof Error ? caughtError.message : "Failed to load skill.");
      })
      .finally(() => {
        if (active) {
          setLoadingDetail(false);
        }
      });

    return () => {
      active = false;
    };
  }, [selectedSkillName]);

  return (
    <section className="config-panel">
      <div className="config-panel__header">
        <div>
          <p className="eyebrow">Skills</p>
          <h3>Discovered `SKILL.md` docs</h3>
        </div>
        <span className="pill">{skills.length} skills</span>
      </div>
      <p className="page-copy">
        The runtime discovers skills from its configured search paths and exposes them here.
      </p>

      {error ? <p className="view-feedback view-feedback--error">{error}</p> : null}

      <div className="config-dual-pane">
        <aside className="config-list" aria-label="Discovered skills">
          {loading ? <p className="view-feedback">Loading skills…</p> : null}
          {!loading && skills.length === 0 ? (
            <p className="view-feedback">No skills were found on this machine.</p>
          ) : null}
          {skills.map((skill) => {
            const active = skill.name === selectedSkillName;

            return (
              <button
                key={skill.name}
                className="config-list__item"
                data-active={active}
                type="button"
                onClick={() => setSelectedSkillName(skill.name)}
              >
                <strong>{skill.name}</strong>
                <span>{skill.path}</span>
              </button>
            );
          })}
        </aside>

        <div className="config-detail config-detail--document">
          {skillDetail ? (
            <>
              <div className="config-detail__header">
                <div>
                  <span className="config-label">Skill</span>
                  <strong>{skillDetail.name}</strong>
                </div>
                <div>
                  <span className="config-label">Path</span>
                  <strong>{skillDetail.path}</strong>
                </div>
              </div>

              <pre className="config-code">{skillDetail.content}</pre>
            </>
          ) : loadingDetail ? (
            <p className="view-feedback">Loading skill document…</p>
          ) : (
            <p className="view-feedback">Select a skill to inspect the full `SKILL.md` document.</p>
          )}
        </div>
      </div>
    </section>
  );
}
