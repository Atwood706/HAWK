import { useEffect, useMemo, useState } from "react";

import { exportWorkflow, listProfiles, listTools, runWorkflow, saveWorkflow, validateWorkflow } from "../../lib/api";
import type { BuiltinTool, WorkflowGraph, WorkflowNode, WorkflowNodeData, WorkflowNodeType } from "../../types";
import { ConfigPanel } from "./ConfigPanel";
import { MedicalSkillsColumn, type MedicalSkill } from "./MedicalSkillsColumn";
import { NodePalette } from "./NodePalette";
import { RunPanel } from "./RunPanel";
import { WorkflowCanvas } from "./WorkflowCanvas";

const initialGraph: WorkflowGraph = {
  id: "openrouter_demo",
  name: "OpenRouter Demo",
  description: "Built-in single-agent demo wired to the OpenRouter profile.",
  nodes: [
    {
      id: "agent_1",
      type: "agent",
      position: { x: 80, y: 100 },
      data: {
        label: "OpenRouter agent",
        profile: "openrouter_chat",
        inputs: { prompt: "user_query" },
        outputs: { response: "final_answer" },
      },
    },
  ],
  edges: [],
};

function createNodeData(type: WorkflowNodeType, index: number): WorkflowNodeData {
  if (type === "tool") {
    return {
      label: `Tool ${index}`,
      tool_name: "arxiv_search",
      inputs: { query: "user_query" },
      outputs: { results: `tool_${index}_results` },
    };
  }
  return {
    label: `Agent ${index}`,
    profile: "openrouter_chat",
    inputs: { prompt: "user_query" },
    outputs: { response: `agent_${index}_response` },
  };
}

export function BuildPage() {
  const [graph, setGraph] = useState<WorkflowGraph>(initialGraph);
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(initialGraph.nodes[0]?.id ?? null);
  const [status, setStatus] = useState("Ready for graph composition.");
  const [statusTone, setStatusTone] = useState<"neutral" | "success" | "error">("neutral");
  const [exportPreview, setExportPreview] = useState("Export preview will appear here.");
  const [isBusy, setIsBusy] = useState(false);
  const [profiles, setProfiles] = useState<string[]>([]);
  const [tools, setTools] = useState<BuiltinTool[]>([]);
  const [runInput, setRunInput] = useState<Record<string, unknown>>({
    user_query: "Hello from the local workbench",
  });

  useEffect(() => {
    let cancelled = false;
    listProfiles()
      .then((result) => {
        if (!cancelled) {
          setProfiles(result.map((p) => p.name));
        }
      })
      .catch(() => {
        // ignore
      });
    listTools()
      .then((result) => {
        if (!cancelled) {
          setTools(result);
        }
      })
      .catch(() => {
        // ignore
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const selectedNode = useMemo<WorkflowNode | null>(
    () => graph.nodes.find((node) => node.id === selectedNodeId) ?? null,
    [graph.nodes, selectedNodeId],
  );

  const handleAddNode = (type: WorkflowNodeType) => {
    const nextIndex = graph.nodes.filter((node) => node.type === type).length + 1;
    const nextId = `${type}_${nextIndex}`;

    setGraph((current) => ({
      ...current,
      nodes: [
        ...current.nodes,
        {
          id: nextId,
          type,
          position: {
            x: 120 + current.nodes.length * 48,
            y: 120 + current.nodes.length * 34,
          },
          data: createNodeData(type, nextIndex),
        },
      ],
    }));
    setSelectedNodeId(nextId);
    setStatus(`Added ${type} node to the canvas.`);
    setStatusTone("neutral");
  };

  const handleDeleteNode = (nodeId: string) => {
    setGraph((current) => ({
      ...current,
      nodes: current.nodes.filter((n) => n.id !== nodeId),
      edges: current.edges.filter((e) => e.source !== nodeId && e.target !== nodeId),
    }));
    setSelectedNodeId((id) => (id === nodeId ? null : id));
    setStatus("Deleted node.");
    setStatusTone("neutral");
  };

  const handleAddMedicalSkillNode = (skill: MedicalSkill) => {
    const selectedAgent = selectedNodeId
      ? graph.nodes.find((node) => node.id === selectedNodeId && node.type === "agent")
      : null;
    const nextIndex = graph.nodes.filter((node) => node.type === "agent").length + 1;
    const nextId = selectedAgent?.id ?? `agent_${nextIndex}`;
    const inputName =
      selectedAgent?.data.inputs.prompt ??
      Object.values(selectedAgent?.data.inputs ?? {})[0] ??
      `medical_skill_${nextIndex}_request`;
    const outputName = `medical_skill_${nextIndex}_response`;
    const medicalSkill = {
      name: skill.name,
      description: skill.description,
      category: skill.category,
      url: skill.url,
    };

    setGraph((current) => ({
      ...current,
      nodes: selectedAgent
        ? current.nodes.map((node) =>
            node.id === selectedAgent.id
              ? {
                  ...node,
                  data: {
                    ...node.data,
                    label: node.data.label || skill.name,
                    medical_skill: medicalSkill,
                    inputs:
                      Object.keys(node.data.inputs).length > 0
                        ? node.data.inputs
                        : { prompt: inputName },
                    outputs:
                      Object.keys(node.data.outputs).length > 0
                        ? node.data.outputs
                        : { response: outputName },
                  },
                }
              : node,
          )
        : [
            ...current.nodes,
            {
              id: nextId,
              type: "agent",
              position: {
                x: 160 + current.nodes.length * 44,
                y: 150 + current.nodes.length * 32,
              },
              data: {
                label: `Agent: ${skill.name}`,
                profile: "openrouter_chat",
                medical_skill: medicalSkill,
                inputs: { prompt: inputName },
                outputs: { response: outputName },
              },
            },
          ],
    }));

    if (!selectedAgent) {
      setSelectedNodeId(nextId);
    }
    setRunInput((current) => ({
      ...current,
      [inputName]: `Use this medical skill inside the agent.\n\nSkill: ${skill.name}\nDomain: ${skill.category}\nDescription: ${skill.description}\n\nTask: `,
    }));
    setStatus(
      selectedAgent
        ? `Attached medical skill "${skill.name}" to the selected agent.`
        : `Added an agent configured with medical skill "${skill.name}".`,
    );
    setStatusTone("neutral");
  };

  const withBusyState = async (action: () => Promise<void>) => {
    setIsBusy(true);
    try {
      await action();
    } catch (error) {
      const message = error instanceof Error ? error.message : "Request failed";
      setStatus(`Error: ${message}`);
      setStatusTone("error");
    } finally {
      setIsBusy(false);
    }
  };

  const persistCurrentGraph = async () => {
    const saved = await saveWorkflow(graph);
    setGraph(saved);
    return saved;
  };

  const handleSave = () =>
    withBusyState(async () => {
      const saved = await persistCurrentGraph();
      setStatus(`Saved workflow "${saved.name}".`);
      setStatusTone("success");
    });

  const handleValidate = () =>
    withBusyState(async () => {
      const saved = await persistCurrentGraph();
      const result = await validateWorkflow(saved.id);
      setStatus(
        result.valid
          ? `Validation passed for "${saved.name}".`
          : `Validation failed: ${result.errors.join(", ")}`,
      );
      setStatusTone(result.valid ? "success" : "error");
    });

  const handleExport = () =>
    withBusyState(async () => {
      const saved = await persistCurrentGraph();
      const result = await exportWorkflow(saved.id);
      setExportPreview(result.awdl);
      setStatus(`Exported AWDL for "${saved.name}".`);
      setStatusTone("success");
    });

  const handleRun = () =>
    withBusyState(async () => {
      const saved = await persistCurrentGraph();
      const result = await runWorkflow(saved.id, {
        input: runInput,
      });
      setStatus(`Run completed: ${result.run_id} (${result.status}). Open View to inspect details.`);
      setStatusTone("success");
    });

  return (
    <section className="build-layout">
      <NodePalette onAddNode={handleAddNode} />
      <WorkflowCanvas
        graph={graph}
        selectedNodeId={selectedNodeId}
        onSelectNode={setSelectedNodeId}
        onDeleteNode={handleDeleteNode}
        onChange={(nextGraph) => {
          setGraph((current) => {
            const currentEdgeIds = new Set(current.edges.map((e) => e.id));
            const addedEdges = nextGraph.edges.filter((e) => !currentEdgeIds.has(e.id));

            if (addedEdges.length === 0) {
              return nextGraph;
            }

            const nodeMap = new Map(nextGraph.nodes.map((n) => [n.id, n]));

            for (const edge of addedEdges) {
              const sourceNode = nodeMap.get(edge.source);
              const targetNode = nodeMap.get(edge.target);
              if (!sourceNode || !targetNode) continue;

              const sourceOutputValues = Object.values(sourceNode.data.outputs);
              if (sourceOutputValues.length === 0) continue;
              const sourceVar = sourceOutputValues[0];

              const nextInputs = { ...targetNode.data.inputs };
              let changed = false;
              for (const [key, value] of Object.entries(nextInputs)) {
                if (value === "user_query") {
                  nextInputs[key] = sourceVar;
                  changed = true;
                }
              }

              if (changed) {
                nodeMap.set(targetNode.id, {
                  ...targetNode,
                  data: { ...targetNode.data, inputs: nextInputs },
                });
              }
            }

            return {
              ...nextGraph,
              nodes: Array.from(nodeMap.values()),
            };
          });
        }}
      />
      <ConfigPanel
        node={selectedNode}
        profiles={profiles}
        tools={tools}
        onUpdateNode={(nodeId, data) =>
          setGraph((current) => ({
            ...current,
            nodes: current.nodes.map((n) =>
              n.id === nodeId ? { ...n, data } : n
            ),
          }))
        }
        onDeleteNode={() => selectedNodeId && handleDeleteNode(selectedNodeId)}
      />
      <RunPanel
        status={status}
        statusTone={statusTone}
        exportPreview={exportPreview}
        isBusy={isBusy}
        onSave={handleSave}
        onValidate={handleValidate}
        onExport={handleExport}
        onRun={handleRun}
        runInput={runInput}
        onRunInputChange={setRunInput}
      />
      <MedicalSkillsColumn onAddSkillNode={handleAddMedicalSkillNode} />
    </section>
  );
}
