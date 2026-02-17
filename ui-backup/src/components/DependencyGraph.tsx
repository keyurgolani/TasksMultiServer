import React, { useEffect, useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { Task, Status } from '../types';

interface DependencyGraphProps {
  tasks: Task[];
  highlightTaskId?: string;
}

interface GraphNode {
  id: string;
  task: Task;
  x: number;
  y: number;
  level: number;
}

interface GraphEdge {
  from: string;
  to: string;
  isCircular: boolean;
}

const DependencyGraph: React.FC<DependencyGraphProps> = ({ tasks, highlightTaskId }) => {
  const navigate = useNavigate();
  const svgRef = useRef<SVGSVGElement>(null);
  const [nodes, setNodes] = useState<GraphNode[]>([]);
  const [edges, setEdges] = useState<GraphEdge[]>([]);
  const [circularDeps, setCircularDeps] = useState<Set<string>>(new Set());
  const [hoveredNode, setHoveredNode] = useState<string | null>(null);

  // Constants for layout
  const NODE_WIDTH = 200;
  const NODE_HEIGHT = 80;
  const LEVEL_HEIGHT = 150;
  const NODE_SPACING = 50;
  const PADDING = 50;

  useEffect(() => {
    if (tasks.length === 0) {
      setNodes([]);
      setEdges([]);
      setCircularDeps(new Set());
      return;
    }

    // Build adjacency list for dependency graph
    const adjList = new Map<string, string[]>();
    const allEdges: GraphEdge[] = [];
    
    tasks.forEach((task) => {
      if (!adjList.has(task.id)) {
        adjList.set(task.id, []);
      }
      task.dependencies.forEach((dep) => {
        adjList.get(task.id)!.push(dep.task_id);
        allEdges.push({ from: task.id, to: dep.task_id, isCircular: false });
      });
    });

    // Detect circular dependencies using DFS
    const circular = new Set<string>();
    const visited = new Set<string>();
    const recStack = new Set<string>();

    const detectCycle = (nodeId: string): boolean => {
      visited.add(nodeId);
      recStack.add(nodeId);

      const neighbors = adjList.get(nodeId) || [];
      for (const neighbor of neighbors) {
        if (!visited.has(neighbor)) {
          if (detectCycle(neighbor)) {
            circular.add(nodeId);
            circular.add(neighbor);
            return true;
          }
        } else if (recStack.has(neighbor)) {
          circular.add(nodeId);
          circular.add(neighbor);
          return true;
        }
      }

      recStack.delete(nodeId);
      return false;
    };

    tasks.forEach((task) => {
      if (!visited.has(task.id)) {
        detectCycle(task.id);
      }
    });

    setCircularDeps(circular);

    // Mark circular edges
    allEdges.forEach((edge) => {
      if (circular.has(edge.from) && circular.has(edge.to)) {
        edge.isCircular = true;
      }
    });

    setEdges(allEdges);

    // Calculate levels using topological sort (for non-circular nodes)
    const levels = new Map<string, number>();
    const inDegree = new Map<string, number>();

    // Initialize in-degrees
    tasks.forEach((task) => {
      inDegree.set(task.id, 0);
    });

    tasks.forEach((task) => {
      task.dependencies.forEach((dep) => {
        if (tasks.find((t) => t.id === dep.task_id)) {
          inDegree.set(task.id, (inDegree.get(task.id) || 0) + 1);
        }
      });
    });

    // BFS to assign levels
    const queue: string[] = [];
    tasks.forEach((task) => {
      if (inDegree.get(task.id) === 0) {
        queue.push(task.id);
        levels.set(task.id, 0);
      }
    });

    while (queue.length > 0) {
      const current = queue.shift()!;
      const currentLevel = levels.get(current) || 0;

      tasks.forEach((task) => {
        if (task.dependencies.some((dep) => dep.task_id === current)) {
          const newInDegree = (inDegree.get(task.id) || 0) - 1;
          inDegree.set(task.id, newInDegree);

          if (newInDegree === 0) {
            queue.push(task.id);
            levels.set(task.id, currentLevel + 1);
          }
        }
      });
    }

    // Assign default level to circular nodes
    tasks.forEach((task) => {
      if (!levels.has(task.id)) {
        levels.set(task.id, 0);
      }
    });

    // Group nodes by level
    const levelGroups = new Map<number, Task[]>();
    tasks.forEach((task) => {
      const level = levels.get(task.id) || 0;
      if (!levelGroups.has(level)) {
        levelGroups.set(level, []);
      }
      levelGroups.get(level)!.push(task);
    });

    // Calculate positions
    const graphNodes: GraphNode[] = [];
    levelGroups.forEach((tasksInLevel, level) => {
      const levelWidth = tasksInLevel.length * (NODE_WIDTH + NODE_SPACING) - NODE_SPACING;
      const startX = PADDING + (levelWidth > 0 ? 0 : NODE_WIDTH / 2);

      tasksInLevel.forEach((task, index) => {
        const x = startX + index * (NODE_WIDTH + NODE_SPACING);
        const y = PADDING + level * LEVEL_HEIGHT;
        graphNodes.push({
          id: task.id,
          task,
          x,
          y,
          level,
        });
      });
    });

    setNodes(graphNodes);
  }, [tasks]);

  // Calculate SVG dimensions
  const maxX = nodes.reduce((max, node) => Math.max(max, node.x + NODE_WIDTH), 0);
  const maxY = nodes.reduce((max, node) => Math.max(max, node.y + NODE_HEIGHT), 0);
  const svgWidth = Math.max(800, maxX + PADDING);
  const svgHeight = Math.max(600, maxY + PADDING);

  // Get node center coordinates
  const getNodeCenter = (nodeId: string): { x: number; y: number } => {
    const node = nodes.find((n) => n.id === nodeId);
    if (!node) return { x: 0, y: 0 };
    return {
      x: node.x + NODE_WIDTH / 2,
      y: node.y + NODE_HEIGHT / 2,
    };
  };

  // Get status color
  const getStatusColor = (status: Status): string => {
    switch (status) {
      case Status.NOT_STARTED:
        return '#9e9e9e';
      case Status.IN_PROGRESS:
        return '#2196f3';
      case Status.BLOCKED:
        return '#f44336';
      case Status.COMPLETED:
        return '#4caf50';
      default:
        return '#9e9e9e';
    }
  };

  // Handle node click
  const handleNodeClick = (taskId: string) => {
    navigate(`/tasks/${taskId}`);
  };

  if (tasks.length === 0) {
    return (
      <div style={{
        padding: '2rem',
        textAlign: 'center',
        color: '#666',
        backgroundColor: '#f5f5f5',
        border: '1px solid #ddd',
        borderRadius: '8px',
      }}>
        No tasks to display in dependency graph
      </div>
    );
  }

  return (
    <div style={{
      backgroundColor: 'white',
      border: '1px solid #ddd',
      borderRadius: '8px',
      padding: '1rem',
      overflow: 'auto',
    }}>
      <div style={{ marginBottom: '1rem' }}>
        <h3 style={{ margin: '0 0 0.5rem 0' }}>Dependency Graph</h3>
        {circularDeps.size > 0 && (
          <div style={{
            padding: '0.75rem',
            backgroundColor: '#ffebee',
            color: '#c62828',
            borderRadius: '4px',
            fontSize: '0.875rem',
            marginBottom: '0.5rem',
          }}>
            ⚠️ Circular dependencies detected! Tasks highlighted in red are part of a dependency cycle.
          </div>
        )}
        <div style={{ fontSize: '0.875rem', color: '#666' }}>
          Click on a task to view details. Arrows show dependencies (task depends on the task it points to).
        </div>
      </div>

      <svg
        ref={svgRef}
        width={svgWidth}
        height={svgHeight}
        style={{
          border: '1px solid #e0e0e0',
          borderRadius: '4px',
          backgroundColor: '#fafafa',
        }}
      >
        {/* Draw edges */}
        <defs>
          <marker
            id="arrowhead"
            markerWidth="10"
            markerHeight="10"
            refX="9"
            refY="3"
            orient="auto"
          >
            <polygon points="0 0, 10 3, 0 6" fill="#666" />
          </marker>
          <marker
            id="arrowhead-circular"
            markerWidth="10"
            markerHeight="10"
            refX="9"
            refY="3"
            orient="auto"
          >
            <polygon points="0 0, 10 3, 0 6" fill="#f44336" />
          </marker>
        </defs>

        {edges.map((edge, index) => {
          const from = getNodeCenter(edge.from);
          const to = getNodeCenter(edge.to);
          
          return (
            <line
              key={`edge-${index}`}
              x1={from.x}
              y1={from.y}
              x2={to.x}
              y2={to.y}
              stroke={edge.isCircular ? '#f44336' : '#666'}
              strokeWidth={edge.isCircular ? 3 : 2}
              markerEnd={edge.isCircular ? 'url(#arrowhead-circular)' : 'url(#arrowhead)'}
              opacity={0.6}
            />
          );
        })}

        {/* Draw nodes */}
        {nodes.map((node) => {
          const isHighlighted = node.id === highlightTaskId;
          const isHovered = node.id === hoveredNode;
          const isCircular = circularDeps.has(node.id);
          const statusColor = getStatusColor(node.task.status);

          return (
            <g
              key={node.id}
              transform={`translate(${node.x}, ${node.y})`}
              onClick={() => handleNodeClick(node.id)}
              onMouseEnter={() => setHoveredNode(node.id)}
              onMouseLeave={() => setHoveredNode(null)}
              style={{ cursor: 'pointer' }}
            >
              {/* Node background */}
              <rect
                width={NODE_WIDTH}
                height={NODE_HEIGHT}
                rx={8}
                fill="white"
                stroke={isCircular ? '#f44336' : isHighlighted ? '#61dafb' : '#ddd'}
                strokeWidth={isCircular ? 4 : isHighlighted ? 3 : 2}
                style={{
                  filter: isHovered ? 'drop-shadow(0 4px 8px rgba(0,0,0,0.2))' : 'none',
                  transition: 'all 0.2s',
                }}
              />

              {/* Status indicator */}
              <rect
                x={0}
                y={0}
                width={NODE_WIDTH}
                height={8}
                rx={8}
                fill={statusColor}
              />

              {/* Task title */}
              <text
                x={NODE_WIDTH / 2}
                y={30}
                textAnchor="middle"
                fontSize="14"
                fontWeight="bold"
                fill="#333"
                style={{
                  pointerEvents: 'none',
                  userSelect: 'none',
                }}
              >
                {node.task.title.length > 20
                  ? node.task.title.substring(0, 20) + '...'
                  : node.task.title}
              </text>

              {/* Task status */}
              <text
                x={NODE_WIDTH / 2}
                y={50}
                textAnchor="middle"
                fontSize="11"
                fill="#666"
                style={{
                  pointerEvents: 'none',
                  userSelect: 'none',
                }}
              >
                {node.task.status.replace('_', ' ')}
              </text>

              {/* Dependency count */}
              <text
                x={NODE_WIDTH / 2}
                y={68}
                textAnchor="middle"
                fontSize="10"
                fill="#999"
                style={{
                  pointerEvents: 'none',
                  userSelect: 'none',
                }}
              >
                {node.task.dependencies.length} {node.task.dependencies.length === 1 ? 'dependency' : 'dependencies'}
              </text>
            </g>
          );
        })}
      </svg>

      {/* Legend */}
      <div style={{
        marginTop: '1rem',
        padding: '1rem',
        backgroundColor: '#f9f9f9',
        borderRadius: '4px',
        display: 'flex',
        gap: '2rem',
        flexWrap: 'wrap',
        fontSize: '0.875rem',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <div style={{ width: 20, height: 20, backgroundColor: '#4caf50', borderRadius: '4px' }} />
          <span>Completed</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <div style={{ width: 20, height: 20, backgroundColor: '#2196f3', borderRadius: '4px' }} />
          <span>In Progress</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <div style={{ width: 20, height: 20, backgroundColor: '#f44336', borderRadius: '4px' }} />
          <span>Blocked</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <div style={{ width: 20, height: 20, backgroundColor: '#9e9e9e', borderRadius: '4px' }} />
          <span>Not Started</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <div style={{ width: 20, height: 3, backgroundColor: '#f44336' }} />
          <span>Circular Dependency</span>
        </div>
      </div>
    </div>
  );
};

export default DependencyGraph;
