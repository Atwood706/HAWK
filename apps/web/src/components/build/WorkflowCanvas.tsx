import type { MouseEvent as ReactMouseEvent } from "react";
import { useEffect, useMemo } from "react";
import ReactFlow, {
  Background,
  Controls,
  MarkerType,
  useEdgesState,
  useNodesState,
  type Edge,
  type Node,
  type NodeMouseHandler,
} from "reactflow";
import "reactflow/dist/style.css";

import type { WorkflowGraph, WorkflowNodeType } from "../../types";

interface WorkflowCanvasProps {
  graph: WorkflowGraph;
  selectedNodeId: string | null;
  onSelectNode: (nodeId: string) => void;
  onDeleteNode?: (nodeId: string) => void;
  onChange?: (graph: WorkflowGraph) => void;
}

const nodeColors: Record<WorkflowNodeType, string> = {
  agent: "#f54e00",
  tool: "#5EA8A7",
};

function renderNodeLabel(node: WorkflowGraph["nodes"][number]) {
  return (
    <div className="flow-node">
      <span
        className="flow-node__dot"
        style={{ backgroundColor: nodeColors[node.type] }}
      />
      <div>
        <strong>{node.data.label ?? node.id}</strong>
        <span>{node.type}</span>
        {node.type === "agent" && node.data.medical_skill ? (
          <span className="flow-node__skill">{node.data.medical_skill.name}</span>
        ) : null}
      </div>
    </div>
  );
}

export function WorkflowCanvas({
  graph,
  selectedNodeId,
  onSelectNode,
  onDeleteNode,
  onChange,
}: WorkflowCanvasProps) {
  const initialNodes = useMemo<Node[]>(
    () =>
      graph.nodes.map((node) => ({
        id: node.id,
        position: node.position,
        data: {
          label: renderNodeLabel(node),
        },
        style: {
          width: 220,
          borderRadius: 18,
          background: "#ffffff",
          color: "#26251e",
          border: "1px solid rgba(38, 37, 30, 0.1)",
          boxShadow: "rgba(0, 0, 0, 0.02) 0px 0px 16px, rgba(0, 0, 0, 0.008) 0px 0px 8px",
        },
      })),
    [graph.nodes],
  );

  const initialEdges = useMemo<Edge[]>(
    () =>
      graph.edges.map((edge) => ({
        ...edge,
        animated: true,
        markerEnd: {
          type: MarkerType.ArrowClosed,
        },
        style: {
          stroke: "rgba(125, 211, 252, 0.75)",
          strokeWidth: 1.6,
        },
      })),
    [graph.edges],
  );

  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);

  useEffect(() => {
    setNodes((currentNodes) => {
      const currentMap = new Map(currentNodes.map((n) => [n.id, n]));
      return graph.nodes.map((node) => {
        const existing = currentMap.get(node.id);
        const data = {
          label: renderNodeLabel(node),
        };
        if (existing) {
          return { ...existing, data };
        }
        return {
          id: node.id,
          position: node.position,
          data,
          style: {
            width: 220,
            borderRadius: 18,
            background: "#ffffff",
            color: "#26251e",
            border: "1px solid rgba(38, 37, 30, 0.1)",
            boxShadow: "rgba(0, 0, 0, 0.02) 0px 0px 16px, rgba(0, 0, 0, 0.008) 0px 0px 8px",
          },
        };
      });
    });
  }, [graph.nodes, setNodes]);

  useEffect(() => {
    setNodes((currentNodes) =>
      currentNodes.map((node) => ({
        ...node,
        style: {
          width: 220,
          borderRadius: 18,
          background: "#ffffff",
          color: "#26251e",
          border:
            selectedNodeId === node.id
              ? "1px solid rgba(38, 37, 30, 0.55)"
              : "1px solid rgba(38, 37, 30, 0.1)",
          boxShadow:
            selectedNodeId === node.id
              ? "rgba(0, 0, 0, 0.06) 0px 0px 20px, rgba(0, 0, 0, 0.02) 0px 0px 10px"
              : "rgba(0, 0, 0, 0.02) 0px 0px 16px, rgba(0, 0, 0, 0.008) 0px 0px 8px",
        },
      }))
    );
  }, [selectedNodeId, setNodes]);

  useEffect(() => {
    setEdges(initialEdges);
  }, [initialEdges, setEdges]);

  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key !== "Delete" && event.key !== "Backspace") return;

      const target = event.target as HTMLElement | null;
      const tagName = target?.tagName?.toLowerCase();
      if (tagName === "input" || tagName === "textarea" || tagName === "select" || target?.isContentEditable) {
        return;
      }

      if (selectedNodeId && onDeleteNode) {
        event.preventDefault();
        onDeleteNode(selectedNodeId);
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [selectedNodeId, onDeleteNode]);

  useEffect(() => {
    if (!onChange) return;
    const nodePositions = new Map(nodes.map((n) => [n.id, n.position]));
    const nextNodes = graph.nodes.map((n) => {
      const pos = nodePositions.get(n.id);
      if (pos && (pos.x !== n.position.x || pos.y !== n.position.y)) {
        return { ...n, position: pos };
      }
      return n;
    });
    const changed = nextNodes.some((n, i) => n !== graph.nodes[i]);
    if (changed) {
      onChange({ ...graph, nodes: nextNodes });
    }
  }, [nodes, graph, onChange]);

  useEffect(() => {
    if (!onChange) return;
    const nextEdges = edges.map((e) => ({
      id: e.id,
      source: e.source,
      target: e.target,
    }));
    const equal =
      graph.edges.length === nextEdges.length &&
      graph.edges.every(
        (e, i) =>
          e.id === nextEdges[i].id &&
          e.source === nextEdges[i].source &&
          e.target === nextEdges[i].target,
      );
    if (!equal) {
      onChange({ ...graph, edges: nextEdges });
    }
  }, [edges, graph, onChange]);

  const handleNodeClick: NodeMouseHandler = (
    _event: ReactMouseEvent,
    node,
  ) => {
    onSelectNode(node.id);
  };

  return (
    <section className="build-panel build-panel--canvas">
      <div className="build-panel__header build-panel__header--inline">
        <div>
          <p className="eyebrow">Canvas</p>
          <h2>{graph.name}</h2>
        </div>
        <span className="canvas-status">{graph.nodes.length} nodes, {graph.edges.length} edges</span>
      </div>
      <p className="build-panel__copy">
        React Flow is wired for visual layout now; deeper graph editing and persistence can layer on
        top of this shell.
      </p>

      <div className="canvas-frame">
        <ReactFlow
          fitView
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onConnect={(connection) =>
            setEdges((eds) =>
              [
                ...eds,
                {
                  ...connection,
                  id: `e${connection.source}-${connection.target}`,
                  animated: true,
                  markerEnd: { type: MarkerType.ArrowClosed },
                  style: {
                    stroke: "rgba(125, 211, 252, 0.75)",
                    strokeWidth: 1.6,
                  },
                } as Edge,
              ].filter(
                (e, i, arr) =>
                  arr.findIndex(
                    (x) => x.source === e.source && x.target === e.target,
                  ) === i,
              ),
            )
          }
          onNodeClick={handleNodeClick}
        >
          <Background color="rgba(145, 162, 197, 0.18)" gap={24} />
          <Controls showInteractive={false} />
        </ReactFlow>
      </div>
    </section>
  );
}
