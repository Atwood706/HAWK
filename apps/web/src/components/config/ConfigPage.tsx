import { useEffect, useMemo, useState } from "react";

import { getSettings, saveSettings } from "../../lib/api";
import type { AppSettings } from "../../types";
import { ProfilesPanel } from "./ProfilesPanel";
import { SkillsPanel } from "./SkillsPanel";
import { ToolsPanel } from "./ToolsPanel";

function SettingCard({ label, value }: { label: string; value: string }) {
  return (
    <article className="config-summary-card">
      <span>{label}</span>
      <strong>{value}</strong>
    </article>
  );
}

export function ConfigPage() {
  const [settings, setSettings] = useState<AppSettings | null>(null);
  const [draftTheme, setDraftTheme] = useState("light");
  const [draftLastOpenWorkflowId, setDraftLastOpenWorkflowId] = useState("");
  const [draftOpenRouterApiKey, setDraftOpenRouterApiKey] = useState("");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [status, setStatus] = useState("Loading settings...");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;

    void getSettings()
      .then((value) => {
        if (!active) {
          return;
        }

        setSettings(value);
        setDraftTheme(value.theme);
        setDraftLastOpenWorkflowId(value.last_open_workflow_id ?? "");
        setDraftOpenRouterApiKey(value.openrouter_api_key ?? "");
        setStatus("Settings loaded.");
        setLoading(false);
      })
      .catch((caughtError: unknown) => {
        if (!active) {
          return;
        }

        setError(
          caughtError instanceof Error
            ? caughtError.message
            : "Failed to load settings.",
        );
        setStatus("Unable to load settings.");
        setLoading(false);
      });

    return () => {
      active = false;
    };
  }, []);

  const hasChanges = useMemo(() => {
    if (!settings) {
      return false;
    }

    return (
      draftTheme !== settings.theme ||
      draftLastOpenWorkflowId !== (settings.last_open_workflow_id ?? "") ||
      draftOpenRouterApiKey !== (settings.openrouter_api_key ?? "")
    );
  }, [draftLastOpenWorkflowId, draftOpenRouterApiKey, draftTheme, settings]);

  const isSettingsEditable = !loading && !saving && settings !== null;

  const handleSave = async () => {
    const nextSettings: AppSettings = {
      theme: draftTheme,
      last_open_workflow_id:
        draftLastOpenWorkflowId.trim() === "" ? null : draftLastOpenWorkflowId,
      openrouter_api_key:
        draftOpenRouterApiKey.trim() === "" ? null : draftOpenRouterApiKey,
    };

    setSaving(true);
    setError(null);

    try {
      const savedSettings = await saveSettings(nextSettings);
      setSettings(savedSettings);
      setDraftTheme(savedSettings.theme);
      setDraftLastOpenWorkflowId(savedSettings.last_open_workflow_id ?? "");
      setDraftOpenRouterApiKey(savedSettings.openrouter_api_key ?? "");
      setStatus("Settings saved.");
    } catch (caughtError: unknown) {
      setError(
        caughtError instanceof Error
          ? caughtError.message
          : "Failed to save settings.",
      );
      setStatus("Save failed.");
    } finally {
      setSaving(false);
    }
  };

  return (
    <section className="panel config-page">
      <header className="config-page__header">
        <div>
          <p className="eyebrow">Config</p>
          <h2>Profiles, tools, skills, and backend settings</h2>
        </div>
        <p className="page-copy">
          Edit profiles, inspect runtime capabilities, and change local
          settings without leaving the workbench.
        </p>
      </header>

      {error ? (
        <p className="view-feedback view-feedback--error">{error}</p>
      ) : null}
      <p className="view-feedback">{status}</p>

      <div className="config-summary">
        <SettingCard label="Theme" value={settings?.theme ?? "Loading..."} />
        <SettingCard
          label="Last open workflow"
          value={settings?.last_open_workflow_id ?? "None recorded"}
        />
        <SettingCard
          label="OpenRouter key"
          value={settings?.openrouter_api_key ? "Configured" : "Missing"}
        />
        <SettingCard
          label="Settings source"
          value="Backend-managed local storage"
        />
      </div>

      <section className="config-panel">
        <div className="config-panel__header">
          <div>
            <p className="eyebrow">Settings</p>
            <h3>Edit persisted preferences</h3>
          </div>
          <button
            className="ghost-button"
            type="button"
            onClick={handleSave}
            disabled={!isSettingsEditable || !hasChanges}
          >
            {saving ? "Saving..." : "Save settings"}
          </button>
        </div>

        <div className="config-form-grid">
          <label className="config-field">
            <span className="config-label">Theme</span>
            <select
              value={draftTheme}
              disabled={!isSettingsEditable}
              onChange={(event) => setDraftTheme(event.target.value)}
            >
              <option value="light">light</option>
              <option value="dark">dark</option>
              <option value="system">system</option>
            </select>
          </label>

          <label className="config-field">
            <span className="config-label">Last open workflow ID</span>
            <input
              type="text"
              placeholder="workflow id"
              value={draftLastOpenWorkflowId}
              disabled={!isSettingsEditable}
              onChange={(event) =>
                setDraftLastOpenWorkflowId(event.target.value)
              }
            />
          </label>

          <label className="config-field">
            <span className="config-label">OpenRouter API Key</span>
            <input
              type="text"
              placeholder="sk-or-v1-..."
              value={draftOpenRouterApiKey}
              disabled={!isSettingsEditable}
              onChange={(event) => setDraftOpenRouterApiKey(event.target.value)}
            />
          </label>
        </div>
      </section>

      <div className="config-stack">
        <ProfilesPanel />
        <ToolsPanel />
        <SkillsPanel />
      </div>
    </section>
  );
}
