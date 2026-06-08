import { useEffect, useMemo, useState } from "react";

export interface MedicalSkill {
  name: string;
  description: string;
  category: string;
  url: string;
  rawUrl: string;
}

interface MedicalSkillsColumnProps {
  onAddSkillNode: (skill: MedicalSkill) => void;
}

const README_URL =
  "https://raw.githubusercontent.com/FreedomIntelligence/OpenClaw-Medical-Skills/main/README.md";
const REPO_BASE_URL =
  "https://github.com/FreedomIntelligence/OpenClaw-Medical-Skills/tree/main/";
const RAW_BASE_URL =
  "https://raw.githubusercontent.com/FreedomIntelligence/OpenClaw-Medical-Skills/main/";

function stripMarkdown(value: string): string {
  return value
    .replace(/<[^>]*>/g, "")
    .replace(/\*\*/g, "")
    .replace(/`/g, "")
    .trim();
}

function parseMedicalSkills(markdown: string): MedicalSkill[] {
  const skills: MedicalSkill[] = [];
  const contentStart = markdown.indexOf("## Skills List");
  const content = contentStart >= 0 ? markdown.slice(contentStart) : markdown;
  const sections = content.split(/\s+###\s+/g);

  for (const section of sections) {
    const headingMatch = section.match(/^(.+?)(?:\s{2,}|Click to expand|Skill\s*\|\s*Description|\| Skill \|)/);
    const category = stripMarkdown(headingMatch?.[1] ?? "General");
    const skillPattern =
      /\|\s*\[([^\]]+)\]\((skills\/[^)]+)\)\s*\|\s*([\s\S]*?)(?=\s*\|\s*\|\s*\[|\s+##\s+|\s+###\s+|$)/g;

    for (const row of section.matchAll(skillPattern)) {
      const description = stripMarkdown(row[3].replace(/\|\s*$/g, ""));
      skills.push({
        name: row[1],
        description,
        category,
        url: `${REPO_BASE_URL}${row[2]}`,
        rawUrl: `${RAW_BASE_URL}${row[2]}/SKILL.md`,
      });
    }
  }

  return skills.filter(
    (skill, index, allSkills) => allSkills.findIndex((item) => item.name === skill.name) === index,
  );
}

export function MedicalSkillsColumn({ onAddSkillNode }: MedicalSkillsColumnProps) {
  const [skills, setSkills] = useState<MedicalSkill[]>([]);
  const [query, setQuery] = useState("");
  const [category, setCategory] = useState("All");
  const [loading, setLoading] = useState(true);
  const [selectedSkill, setSelectedSkill] = useState<MedicalSkill | null>(null);
  const [skillDetail, setSkillDetail] = useState<string | null>(null);
  const [loadingDetail, setLoadingDetail] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [detailError, setDetailError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;

    void fetch(README_URL)
      .then((response) => {
        if (!response.ok) {
          throw new Error(`GitHub request failed: ${response.status}`);
        }
        return response.text();
      })
      .then((markdown) => {
        if (!active) {
          return;
        }

        const parsed = parseMedicalSkills(markdown);
        setSkills(parsed);
        setError(parsed.length === 0 ? "No medical skills were parsed from the README." : null);
      })
      .catch((caughtError: unknown) => {
        if (!active) {
          return;
        }

        setError(caughtError instanceof Error ? caughtError.message : "Failed to load medical skills.");
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

  const categories = useMemo(
    () => ["All", ...Array.from(new Set(skills.map((skill) => skill.category))).sort()],
    [skills],
  );

  const filteredSkills = useMemo(() => {
    const normalizedQuery = query.trim().toLowerCase();
    return skills.filter((skill) => {
      const matchesCategory = category === "All" || skill.category === category;
      const matchesQuery =
        normalizedQuery.length === 0 ||
        skill.name.toLowerCase().includes(normalizedQuery) ||
        skill.description.toLowerCase().includes(normalizedQuery) ||
        skill.category.toLowerCase().includes(normalizedQuery);

      return matchesCategory && matchesQuery;
    });
  }, [category, query, skills]);

  const handleShowDetail = (skill: MedicalSkill) => {
    setSelectedSkill(skill);
    setSkillDetail(null);
    setDetailError(null);
    setLoadingDetail(true);

    void fetch(skill.rawUrl)
      .then((response) => {
        if (!response.ok) {
          throw new Error(`Detail request failed: ${response.status}`);
        }
        return response.text();
      })
      .then((content) => setSkillDetail(content))
      .catch((caughtError: unknown) => {
        setDetailError(caughtError instanceof Error ? caughtError.message : "Failed to load skill detail.");
      })
      .finally(() => setLoadingDetail(false));
  };

  return (
    <aside className="build-panel build-panel--medical-skills">
      <div className="build-panel__header build-panel__header--inline">
        <div>
          <p className="eyebrow">OpenClaw</p>
          <h2>Medical Skills</h2>
        </div>
        <span className="pill">{skills.length || 869}</span>
      </div>

      <div className="medical-skills-toolbar">
        <label className="config-field">
          <span className="config-label">Search</span>
          <input
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="PubMed, oncology, variant..."
          />
        </label>
        <label className="config-field">
          <span className="config-label">Domain</span>
          <select value={category} onChange={(event) => setCategory(event.target.value)}>
            {categories.map((item) => (
              <option key={item} value={item}>
                {item}
              </option>
            ))}
          </select>
        </label>
      </div>

      {loading ? <p className="view-feedback">Loading medical skills from GitHub...</p> : null}
      {error ? <p className="view-feedback view-feedback--error">{error}</p> : null}

      <div className="medical-skills-list" aria-label="OpenClaw medical skills">
        {!loading && filteredSkills.length === 0 ? (
          <p className="view-feedback">No matching medical skills.</p>
        ) : null}

        {filteredSkills.map((skill) => (
          <article key={skill.name} className="medical-skill-card">
            <div className="medical-skill-card__header">
              <strong>{skill.name}</strong>
              <span>{skill.category}</span>
            </div>
            <p>{skill.description}</p>
            <div className="medical-skill-card__actions">
              <button type="button" className="ghost-button" onClick={() => onAddSkillNode(skill)}>
                Add
              </button>
              <button type="button" className="ghost-button" onClick={() => handleShowDetail(skill)}>
                Detail
              </button>
            </div>
          </article>
        ))}
      </div>

      {selectedSkill ? (
        <div className="medical-skill-detail" role="dialog" aria-label={`${selectedSkill.name} detail`}>
          <div className="medical-skill-detail__header">
            <div>
              <span className="config-label">Skill detail</span>
              <strong>{selectedSkill.name}</strong>
            </div>
            <button type="button" className="ghost-button" onClick={() => setSelectedSkill(null)}>
              Close
            </button>
          </div>
          {loadingDetail ? <p className="view-feedback">Loading detail...</p> : null}
          {detailError ? <p className="view-feedback view-feedback--error">{detailError}</p> : null}
          {skillDetail ? <pre className="config-code">{skillDetail}</pre> : null}
        </div>
      ) : null}
    </aside>
  );
}
