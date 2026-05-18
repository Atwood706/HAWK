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

const providerKeyFields = [
  { key: "openrouter_api_key", provider: "OpenRouter", placeholder: "sk-or-v1-..." },
  { key: "openai_api_key", provider: "OpenAI", placeholder: "sk-..." },
  { key: "deepseek_api_key", provider: "DeepSeek", placeholder: "sk-..." },
  { key: "qwen_api_key", provider: "Qwen / DashScope", placeholder: "sk-..." },
  { key: "gemini_api_key", provider: "Google Gemini", placeholder: "AIza..." },
  { key: "anthropic_api_key", provider: "Anthropic / Claude", placeholder: "sk-ant-..." },
  { key: "xai_api_key", provider: "xAI / Grok", placeholder: "xai-..." },
  { key: "groq_api_key", provider: "Groq", placeholder: "gsk_..." },
  { key: "mistral_api_key", provider: "Mistral AI", placeholder: "..." },
  { key: "perplexity_api_key", provider: "Perplexity", placeholder: "pplx-..." },
  { key: "moonshot_api_key", provider: "Kimi / Moonshot", placeholder: "sk-..." },
  { key: "zhipu_api_key", provider: "GLM / Zhipu", placeholder: "..." },
  { key: "siliconflow_api_key", provider: "SiliconFlow", placeholder: "sk-..." },
  { key: "together_api_key", provider: "Together AI", placeholder: "..." },
] as const;

type ProviderKeyField = (typeof providerKeyFields)[number]["key"];

export function ConfigPage() {
  const [settings, setSettings] = useState<AppSettings | null>(null);
  const [draftTheme, setDraftTheme] = useState("light");
  const [draftLastOpenWorkflowId, setDraftLastOpenWorkflowId] = useState("");
  const [draftApiKeys, setDraftApiKeys] = useState<Record<ProviderKeyField, string>>({
    openrouter_api_key: "",
    openai_api_key: "",
    deepseek_api_key: "",
    qwen_api_key: "",
    gemini_api_key: "",
    anthropic_api_key: "",
    xai_api_key: "",
    groq_api_key: "",
    mistral_api_key: "",
    perplexity_api_key: "",
    moonshot_api_key: "",
    zhipu_api_key: "",
    siliconflow_api_key: "",
    together_api_key: "",
  });
  const [selectedProviderKey, setSelectedProviderKey] =
    useState<ProviderKeyField>("openrouter_api_key");
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
        setDraftApiKeys({
          openrouter_api_key: value.openrouter_api_key ?? "",
          openai_api_key: value.openai_api_key ?? "",
          deepseek_api_key: value.deepseek_api_key ?? "",
          qwen_api_key: value.qwen_api_key ?? "",
          gemini_api_key: value.gemini_api_key ?? "",
          anthropic_api_key: value.anthropic_api_key ?? "",
          xai_api_key: value.xai_api_key ?? "",
          groq_api_key: value.groq_api_key ?? "",
          mistral_api_key: value.mistral_api_key ?? "",
          perplexity_api_key: value.perplexity_api_key ?? "",
          moonshot_api_key: value.moonshot_api_key ?? "",
          zhipu_api_key: value.zhipu_api_key ?? "",
          siliconflow_api_key: value.siliconflow_api_key ?? "",
          together_api_key: value.together_api_key ?? "",
        });
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
      providerKeyFields.some(({ key }) => draftApiKeys[key] !== (settings[key] ?? ""))
    );
  }, [draftApiKeys, draftLastOpenWorkflowId, draftTheme, settings]);

  const isSettingsEditable = !loading && !saving && settings !== null;
  const selectedProvider = providerKeyFields.find(({ key }) => key === selectedProviderKey) ?? providerKeyFields[0];

  const handleSave = async () => {
    const nextSettings: AppSettings = {
      theme: draftTheme,
      last_open_workflow_id:
        draftLastOpenWorkflowId.trim() === "" ? null : draftLastOpenWorkflowId,
      openrouter_api_key:
        draftApiKeys.openrouter_api_key.trim() === "" ? null : draftApiKeys.openrouter_api_key,
      openai_api_key:
        draftApiKeys.openai_api_key.trim() === "" ? null : draftApiKeys.openai_api_key,
      deepseek_api_key:
        draftApiKeys.deepseek_api_key.trim() === "" ? null : draftApiKeys.deepseek_api_key,
      qwen_api_key:
        draftApiKeys.qwen_api_key.trim() === "" ? null : draftApiKeys.qwen_api_key,
      gemini_api_key:
        draftApiKeys.gemini_api_key.trim() === "" ? null : draftApiKeys.gemini_api_key,
      anthropic_api_key:
        draftApiKeys.anthropic_api_key.trim() === "" ? null : draftApiKeys.anthropic_api_key,
      xai_api_key:
        draftApiKeys.xai_api_key.trim() === "" ? null : draftApiKeys.xai_api_key,
      groq_api_key:
        draftApiKeys.groq_api_key.trim() === "" ? null : draftApiKeys.groq_api_key,
      mistral_api_key:
        draftApiKeys.mistral_api_key.trim() === "" ? null : draftApiKeys.mistral_api_key,
      perplexity_api_key:
        draftApiKeys.perplexity_api_key.trim() === "" ? null : draftApiKeys.perplexity_api_key,
      moonshot_api_key:
        draftApiKeys.moonshot_api_key.trim() === "" ? null : draftApiKeys.moonshot_api_key,
      zhipu_api_key:
        draftApiKeys.zhipu_api_key.trim() === "" ? null : draftApiKeys.zhipu_api_key,
      siliconflow_api_key:
        draftApiKeys.siliconflow_api_key.trim() === "" ? null : draftApiKeys.siliconflow_api_key,
      together_api_key:
        draftApiKeys.together_api_key.trim() === "" ? null : draftApiKeys.together_api_key,
    };

    setSaving(true);
    setError(null);

    try {
      const savedSettings = await saveSettings(nextSettings);
      setSettings(savedSettings);
      setDraftTheme(savedSettings.theme);
      setDraftLastOpenWorkflowId(savedSettings.last_open_workflow_id ?? "");
      setDraftApiKeys({
        openrouter_api_key: savedSettings.openrouter_api_key ?? "",
        openai_api_key: savedSettings.openai_api_key ?? "",
        deepseek_api_key: savedSettings.deepseek_api_key ?? "",
        qwen_api_key: savedSettings.qwen_api_key ?? "",
        gemini_api_key: savedSettings.gemini_api_key ?? "",
        anthropic_api_key: savedSettings.anthropic_api_key ?? "",
        xai_api_key: savedSettings.xai_api_key ?? "",
        groq_api_key: savedSettings.groq_api_key ?? "",
        mistral_api_key: savedSettings.mistral_api_key ?? "",
        perplexity_api_key: savedSettings.perplexity_api_key ?? "",
        moonshot_api_key: savedSettings.moonshot_api_key ?? "",
        zhipu_api_key: savedSettings.zhipu_api_key ?? "",
        siliconflow_api_key: savedSettings.siliconflow_api_key ?? "",
        together_api_key: savedSettings.together_api_key ?? "",
      });
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
          label="AI provider keys"
          value={
            settings
              ? `${providerKeyFields.filter(({ key }) => settings[key]).length}/${providerKeyFields.length} configured`
              : "Loading..."
          }
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
            <span className="config-label">AI Provider</span>
            <select
              value={selectedProviderKey}
              disabled={!isSettingsEditable}
              onChange={(event) => setSelectedProviderKey(event.target.value as ProviderKeyField)}
            >
              {providerKeyFields.map(({ key, provider }) => (
                <option key={key} value={key}>
                  {provider}
                </option>
              ))}
            </select>
          </label>

          <label className="config-field">
            <span className="config-label">API Key</span>
            <input
              type="password"
              placeholder={selectedProvider.placeholder}
              value={draftApiKeys[selectedProviderKey]}
              disabled={!isSettingsEditable}
              onChange={(event) =>
                setDraftApiKeys((current) => ({
                  ...current,
                  [selectedProviderKey]: event.target.value,
                }))
              }
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
