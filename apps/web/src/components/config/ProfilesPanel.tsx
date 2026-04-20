import { useEffect, useMemo, useRef, useState } from "react";

import {
  getProfile,
  listProfiles,
  saveProfile,
  deleteProfile,
  listSkills,
  listTools,
} from "../../lib/api";
import { parseToml, serializeToml } from "../../lib/toml";
import type { ProfileDetail, ProfileSummary } from "../../types";

interface ProfileForm {
  model?: string;
  base_url?: string;
  api_key?: string;
  max_turns?: number;
  temperature?: number;
  system_prompt?: string;
  skills?: string[];
  tools?: string[];
  [key: string]: unknown;
}

function makeDefaultForm(): ProfileForm {
  return {
    model: "deepseek-chat",
    max_turns: 4,
    temperature: 0.2,
    system_prompt: "",
    skills: [],
    tools: [],
  };
}

export function ProfilesPanel() {
  const hasUserInteractedRef = useRef(false);
  const [profiles, setProfiles] = useState<ProfileSummary[]>([]);
  const [selectedProfile, setSelectedProfile] = useState<string | null>(null);
  const [isCreatingNew, setIsCreatingNew] = useState(true);
  const [profileName, setProfileName] = useState("");
  const [form, setForm] = useState<ProfileForm>(makeDefaultForm());
  const [savedSnapshot, setSavedSnapshot] = useState<ProfileDetail | null>(
    null,
  );
  const [loading, setLoading] = useState(true);
  const [loadingProfile, setLoadingProfile] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [status, setStatus] = useState<string>("Ready.");
  const [availableSkills, setAvailableSkills] = useState<string[]>([]);
  const [availableTools, setAvailableTools] = useState<string[]>([]);

  useEffect(() => {
    let active = true;
    void listProfiles()
      .then((items) => {
        if (!active) return;
        setProfiles(items);
        setLoading(false);
        if (hasUserInteractedRef.current) return;
        if (items.length === 0) {
          setSelectedProfile(null);
          setIsCreatingNew(true);
          setProfileName("");
          setForm(makeDefaultForm());
          setSavedSnapshot(null);
          setStatus("Create the first profile.");
          return;
        }
        setSelectedProfile((current) => current ?? items[0].name);
        setIsCreatingNew(false);
      })
      .catch((caughtError: unknown) => {
        if (!active) return;
        setLoading(false);
        setError(
          caughtError instanceof Error
            ? caughtError.message
            : "Failed to load profiles.",
        );
      });
    return () => {
      active = false;
    };
  }, []);

  useEffect(() => {
    let active = true;
    void listSkills()
      .then((items) => {
        if (active) setAvailableSkills(items.map((s) => s.name));
      })
      .catch(() => {});
    return () => {
      active = false;
    };
  }, []);

  useEffect(() => {
    let active = true;
    void listTools()
      .then((items) => {
        if (active) setAvailableTools(items.map((t) => t.name));
      })
      .catch(() => {});
    return () => {
      active = false;
    };
  }, []);

  useEffect(() => {
    if (isCreatingNew || selectedProfile === null) {
      return;
    }
    let active = true;
    setLoadingProfile(true);
    setError(null);
    void getProfile(selectedProfile)
      .then((profile) => {
        if (!active) return;
        let parsed: ProfileForm;
        try {
          parsed = parseToml(profile.content) as ProfileForm;
        } catch {
          parsed = {};
        }
        setProfileName(profile.name);
        setForm({
          ...makeDefaultForm(),
          ...parsed,
          skills: Array.isArray(parsed.skills) ? parsed.skills : [],
          tools: Array.isArray(parsed.tools) ? parsed.tools : [],
        });
        setSavedSnapshot(profile);
        setStatus(`Loaded profile ${profile.name}.`);
      })
      .catch((caughtError: unknown) => {
        if (!active) return;
        setError(
          caughtError instanceof Error
            ? caughtError.message
            : "Failed to load profile.",
        );
      })
      .finally(() => {
        if (active) setLoadingProfile(false);
      });
    return () => {
      active = false;
    };
  }, [isCreatingNew, selectedProfile]);

  const currentContent = useMemo(() => serializeToml(form), [form]);

  const hasChanges = useMemo(() => {
    if (isCreatingNew) {
      return (
        profileName.trim().length > 0 ||
        currentContent !== serializeToml(makeDefaultForm())
      );
    }
    if (!savedSnapshot) return false;
    const nameChanged = profileName.trim() !== savedSnapshot.name;
    const contentChanged = currentContent !== savedSnapshot.content;
    return nameChanged || contentChanged;
  }, [currentContent, isCreatingNew, profileName, savedSnapshot]);

  const handleSelectProfile = (name: string) => {
    hasUserInteractedRef.current = true;
    setSelectedProfile(name);
    setIsCreatingNew(false);
    setStatus(`Selected profile ${name}.`);
  };

  const handleNewProfile = () => {
    hasUserInteractedRef.current = true;
    setSelectedProfile(null);
    setIsCreatingNew(true);
    setProfileName("");
    setForm(makeDefaultForm());
    setSavedSnapshot(null);
    setError(null);
    setStatus("Start a new profile.");
  };

  const handleSave = async () => {
    const targetName = profileName.trim();
    const previousName = selectedProfile;
    if (!targetName) {
      setError("Profile name is required.");
      return;
    }
    setSaving(true);
    setError(null);
    try {
      const content = serializeToml(form);
      const savedProfile = await saveProfile(targetName, { content });

      if (!isCreatingNew && previousName && previousName !== targetName) {
        await deleteProfile(previousName);
      }

      const updatedProfiles = await listProfiles();
      setProfiles(updatedProfiles);
      setSelectedProfile(savedProfile.name);
      setIsCreatingNew(false);
      setProfileName(savedProfile.name);
      let parsed: ProfileForm;
      try {
        parsed = parseToml(savedProfile.content) as ProfileForm;
      } catch {
        parsed = {};
      }
      setForm({
        ...makeDefaultForm(),
        ...parsed,
        skills: Array.isArray(parsed.skills) ? parsed.skills : [],
        tools: Array.isArray(parsed.tools) ? parsed.tools : [],
      });
      setSavedSnapshot(savedProfile);
      setStatus(`Saved profile ${savedProfile.name}.`);
    } catch (caughtError: unknown) {
      setError(
        caughtError instanceof Error
          ? caughtError.message
          : "Failed to save profile.",
      );
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async () => {
    if (isCreatingNew) return;
    const targetName = selectedProfile;
    if (!targetName) return;
    if (!window.confirm(`Delete profile "${targetName}"? This cannot be undone.`)) {
      return;
    }
    setSaving(true);
    setError(null);
    try {
      await deleteProfile(targetName);
      const updatedProfiles = await listProfiles();
      setProfiles(updatedProfiles);
      if (updatedProfiles.length > 0) {
        setSelectedProfile(updatedProfiles[0].name);
        setIsCreatingNew(false);
      } else {
        setSelectedProfile(null);
        setIsCreatingNew(true);
        setProfileName("");
        setForm(makeDefaultForm());
        setSavedSnapshot(null);
      }
      setStatus(`Deleted profile ${targetName}.`);
    } catch (caughtError: unknown) {
      setError(
        caughtError instanceof Error
          ? caughtError.message
          : "Failed to delete profile.",
      );
    } finally {
      setSaving(false);
    }
  };

  const updateField = <K extends keyof ProfileForm>(
    key: K,
    value: ProfileForm[K],
  ) => {
    hasUserInteractedRef.current = true;
    setForm((current) => ({ ...current, [key]: value }));
  };

  const toggleInArray = (key: "skills" | "tools", value: string) => {
    hasUserInteractedRef.current = true;
    setForm((current) => {
      const arr = Array.isArray(current[key])
        ? [...(current[key] as string[])]
        : [];
      const next = arr.includes(value)
        ? arr.filter((v) => v !== value)
        : [...arr, value];
      return { ...current, [key]: next };
    });
  };

  return (
    <section className="config-panel">
      <div className="config-panel__header">
        <div>
          <p className="eyebrow">Profiles</p>
          <h3>Local presets</h3>
        </div>
        <button
          className="ghost-button"
          type="button"
          onClick={handleNewProfile}
        >
          New profile
        </button>
      </div>
      <p className="page-copy">
        Profiles define model settings, system prompts, skills, and tools. Edit
        them here and select a profile when building workflows.
      </p>

      {error ? (
        <p className="view-feedback view-feedback--error">{error}</p>
      ) : null}
      <p className="view-feedback">{status}</p>

      <div className="config-dual-pane">
        <aside className="config-list" aria-label="Profiles list">
          {loading ? <p className="view-feedback">Loading profiles…</p> : null}
          {!loading && profiles.length === 0 ? (
            <p className="view-feedback">
              No profiles found. Create one to get started.
            </p>
          ) : null}
          {profiles.map((profile) => {
            const active = profile.name === selectedProfile && !isCreatingNew;
            return (
              <button
                key={profile.name}
                className="config-list__item"
                data-active={active}
                type="button"
                onClick={() => handleSelectProfile(profile.name)}
              >
                <strong>{profile.name}</strong>
                <span>TOML profile</span>
              </button>
            );
          })}
        </aside>

        <div className="config-editor">
          <div className="config-editor__row">
            <label className="config-field">
              <span>Profile name</span>
              <input
                value={profileName}
                onChange={(event) => {
                  hasUserInteractedRef.current = true;
                  setProfileName(event.target.value);
                }}
                placeholder="coder"
              />
            </label>

            <div className="config-editor__meta">
              <span className="config-label">Mode</span>
              <strong>{isCreatingNew ? "Create" : "Edit"}</strong>
            </div>
          </div>

          <div className="config-form-grid">
            <label className="config-field">
              <span className="config-label">Model</span>
              <input
                type="text"
                value={form.model ?? ""}
                onChange={(e) => updateField("model", e.target.value)}
                placeholder="deepseek-chat"
              />
            </label>

            <label className="config-field">
              <span className="config-label">Base URL</span>
              <input
                type="text"
                value={form.base_url ?? ""}
                onChange={(e) => updateField("base_url", e.target.value)}
                placeholder="https://api.openrouter.ai/api/v1"
              />
            </label>

            <label className="config-field">
              <span className="config-label">API Key</span>
              <input
                type="text"
                value={form.api_key ?? ""}
                onChange={(e) => updateField("api_key", e.target.value)}
                placeholder="sk-..."
              />
            </label>

            <label className="config-field">
              <span className="config-label">Max turns</span>
              <input
                type="number"
                value={form.max_turns ?? ""}
                onChange={(e) =>
                  updateField("max_turns", parseInt(e.target.value, 10) || 0)
                }
                placeholder="4"
              />
            </label>

            <label className="config-field">
              <span className="config-label">Temperature</span>
              <input
                type="number"
                step="0.1"
                value={form.temperature ?? ""}
                onChange={(e) =>
                  updateField("temperature", parseFloat(e.target.value) || 0)
                }
                placeholder="0.2"
              />
            </label>
          </div>

          <label className="config-field config-field--stacked">
            <span className="config-label">System prompt</span>
            <textarea
              className="config-textarea"
              rows={5}
              value={form.system_prompt ?? ""}
              onChange={(e) => updateField("system_prompt", e.target.value)}
              placeholder="You are a helpful assistant..."
              style={{ minHeight: 100 }}
            />
          </label>

          {availableSkills.length > 0 && (
            <div className="config-field config-field--stacked">
              <span className="config-label">Skills</span>
              <div
                className="config-check-list"
                style={{
                  marginTop: 8,
                  display: "grid",
                  gap: 6,
                  gridTemplateColumns: "repeat(2, 1fr)",
                }}
              >
                {availableSkills.map((skill) => (
                  <label
                    key={skill}
                    style={{
                      display: "flex",
                      alignItems: "center",
                      gap: 8,
                      fontSize: 13,
                      cursor: "pointer",
                    }}
                  >
                    <input
                      type="checkbox"
                      checked={(form.skills ?? []).includes(skill)}
                      onChange={() => toggleInArray("skills", skill)}
                      style={{ maxWidth: "10px" }}
                    />
                    <span>{skill}</span>
                  </label>
                ))}
              </div>
            </div>
          )}

          {availableTools.length > 0 && (
            <div className="config-field config-field--stacked">
              <span className="config-label">Tools</span>
              <div
                className="config-check-list"
                style={{
                  marginTop: 8,
                  display: "grid",
                  gap: 6,
                  gridTemplateColumns: "repeat(2, 1fr)",
                }}
              >
                {availableTools.map((tool) => (
                  <label
                    key={tool}
                    style={{
                      display: "flex",
                      alignItems: "center",
                      gap: 8,
                      fontSize: 13,
                      cursor: "pointer",
                    }}
                  >
                    <input
                      type="checkbox"
                      checked={(form.tools ?? []).includes(tool)}
                      onChange={() => toggleInArray("tools", tool)}
                      style={{ maxWidth: "10px" }}
                    />
                    <span>{tool}</span>
                  </label>
                ))}
              </div>
            </div>
          )}

          <div className="config-toolbar">
            <button
              className="action-button action-button--primary"
              type="button"
              onClick={handleSave}
              disabled={saving || loadingProfile}
            >
              {saving ? "Saving..." : "Save profile"}
            </button>
            {!isCreatingNew && (
              <button
                className="ghost-button"
                type="button"
                onClick={handleDelete}
                disabled={saving || loadingProfile}
                style={{ color: "#dc2626" }}
              >
                Delete
              </button>
            )}
            <span className="config-toolbar__status">
              {loadingProfile
                ? "Loading profile content…"
                : hasChanges
                  ? "Unsaved changes"
                  : "Up to date"}
            </span>
          </div>
        </div>
      </div>
    </section>
  );
}
