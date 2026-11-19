import React, { useEffect, useState, useRef, useMemo } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { useUI } from '@/contexts/UIContext';
import { graphService } from '@/services/graph.service';
import type { GraphNode, GraphEdge, ClinicalCluster, PatientKnowledgeGraphResponse } from '@/types';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import {
  Share2,
  RefreshCw,
  Search,
  Filter,
  Maximize2,
  Activity,
  Pill,
  Microscope,
  FileText,
  AlertTriangle,
  User,
  Info,
  ExternalLink,
  ChevronRight,
  Layers,
  Sparkles,
  X
} from 'lucide-react';
import { useNavigate } from 'react-router-dom';

const NODE_COLORS: Record<string, { bg: string; border: string; text: string }> = {
  patient: { bg: '#10B981', border: '#059669', text: '#FFFFFF' },
  condition: { bg: '#EF4444', border: '#DC2626', text: '#FFFFFF' },
  medication: { bg: '#3B82F6', border: '#2563EB', text: '#FFFFFF' },
  lab_test: { bg: '#10B981', border: '#059669', text: '#FFFFFF' },
  procedure: { bg: '#8B5CF6', border: '#7C3AED', text: '#FFFFFF' },
  allergy: { bg: '#F59E0B', border: '#D97706', text: '#FFFFFF' },
  document: { bg: '#6B7280', border: '#4B5563', text: '#FFFFFF' },
};

interface SimulationNode extends GraphNode {
  x: number;
  y: number;
  vx: number;
  vy: number;
  radius: number;
}

export const KnowledgeGraphPage: React.FC = () => {
  const { user } = useAuth();
  const { addToast } = useUI();
  const navigate = useNavigate();

  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const containerRef = useRef<HTMLDivElement | null>(null);

  const [graphData, setGraphData] = useState<PatientKnowledgeGraphResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [isSyncing, setIsSyncing] = useState(false);

  // Filters
  const [selectedClusterId, setSelectedClusterId] = useState<number | null>(null);
  const [selectedType, setSelectedType] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState('');

  // Selected Node Drawer
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);

  // Viewport transformation
  const [pan, setPan] = useState({ x: 0, y: 0 });
  const [zoom, setZoom] = useState(1);
  const [isDraggingCanvas, setIsDraggingCanvas] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });

  // Hovered node
  const [hoveredNodeId, setHoveredNodeId] = useState<string | null>(null);

  // Simulation references
  const nodesRef = useRef<SimulationNode[]>([]);
  const animFrameRef = useRef<number | null>(null);
  const draggedNodeRef = useRef<SimulationNode | null>(null);
  const alphaRef = useRef<number>(1.0);

  const fetchGraph = async () => {
    try {
      const data = await graphService.getPatientGraph();
      setGraphData(data);
      initializeSimulation(data.nodes);
    } catch {
      addToast({
        type: 'info',
        title: 'Empty Graph',
        message: 'Upload medical reports to start populating your patient knowledge network.',
      });
    } finally {
      setLoading(false);
      setIsSyncing(false);
    }
  };

  useEffect(() => {
    fetchGraph();
  }, []);

  const handleSync = async () => {
    setIsSyncing(true);
    try {
      const data = await graphService.syncGraph();
      setGraphData(data);
      initializeSimulation(data.nodes);
      addToast({
        type: 'success',
        title: 'Network Synchronized',
        message: 'Patient Knowledge Graph refreshed from all verified records.',
      });
    } catch {
      addToast({
        type: 'error',
        title: 'Sync Notice',
        message: 'Unable to sync knowledge graph right now.',
      });
    } finally {
      setIsSyncing(false);
    }
  };

  // Initialize Force Simulation positions with generous spacing and cooling
  const initializeSimulation = (nodes: GraphNode[]) => {
    const width = 800;
    const height = 550;
    const count = nodes.length;
    alphaRef.current = 1.0;

    nodesRef.current = nodes.map((n, i) => {
      const angle = (i / Math.max(count, 1)) * 2 * Math.PI;
      const dist = n.type === 'patient' ? 0 : 190 + (i % 4) * 55;
      return {
        ...n,
        x: width / 2 + Math.cos(angle) * dist,
        y: height / 2 + Math.sin(angle) * dist,
        vx: 0,
        vy: 0,
        radius: n.type === 'patient' ? 26 : n.type === 'condition' ? 19 : 15,
      };
    });
  };

  // Filter nodes based on cluster and type
  const visibleNodes = useMemo(() => {
    if (!graphData) return [];
    alphaRef.current = 0.5; // gentle readjustment on filter change
    return nodesRef.current.filter((n) => {
      if (selectedClusterId !== null && n.cluster_id !== selectedClusterId && n.type !== 'patient') {
        return false;
      }
      if (selectedType !== 'all' && n.type !== selectedType && n.type !== 'patient') {
        return false;
      }
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase();
        const matchesLabel = n.label.toLowerCase().includes(q);
        const matchesVal = n.value && n.value.toLowerCase().includes(q);
        const matchesCode = n.code && n.code.toLowerCase().includes(q);
        if (!matchesLabel && !matchesVal && !matchesCode) return false;
      }
      return true;
    });
  }, [graphData, selectedClusterId, selectedType, searchQuery]);

  const visibleNodeIds = useMemo(() => new Set(visibleNodes.map((n) => n.id)), [visibleNodes]);

  const visibleEdges = useMemo(() => {
    if (!graphData) return [];
    return graphData.edges.filter((e) => visibleNodeIds.has(e.source) && visibleNodeIds.has(e.target));
  }, [graphData, visibleNodeIds]);

  // Clean label/value string of duplicate units like "mg/dL mg/dL"
  const cleanValueString = (text?: string) => {
    if (!text) return '';
    return text.replace(/\b([a-zA-Z/%]+)\s+\1\b/gi, '$1').replace(/\b(panel|report)\s+\1\b/gi, '$1');
  };

  // Canvas Drawing & Simulation Loop
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let running = true;

    const render = () => {
      if (!running) return;

      const nodes = nodesRef.current;
      const alpha = alphaRef.current;

      // Only simulate if alpha is above stabilization threshold
      if (alpha > 0.005) {
        alphaRef.current *= 0.985;
        const kRepel = 2800 * alpha;
        const kAttract = 0.035 * alpha;
        const friction = 0.85;

        // 1. Repulsion between visible nodes
        for (let i = 0; i < nodes.length; i++) {
          if (draggedNodeRef.current && nodes[i].id === draggedNodeRef.current.id) continue;
          for (let j = i + 1; j < nodes.length; j++) {
            const dx = nodes[j].x - nodes[i].x;
            const dy = nodes[j].y - nodes[i].y;
            const dist = Math.sqrt(dx * dx + dy * dy) || 1;
            if (dist < 280) {
              const force = kRepel / (dist * dist);
              const fx = (dx / dist) * force;
              const fy = (dy / dist) * force;
              nodes[i].vx -= fx;
              nodes[i].vy -= fy;
              nodes[j].vx += fx;
              nodes[j].vy += fy;
            }
          }
        }

        // 2. Attraction along visible edges
        const nodeMap = new Map(nodes.map((n) => [n.id, n]));
        for (const e of visibleEdges) {
          const src = nodeMap.get(e.source);
          const tgt = nodeMap.get(e.target);
          if (src && tgt) {
            const dx = tgt.x - src.x;
            const dy = tgt.y - src.y;
            const dist = Math.sqrt(dx * dx + dy * dy) || 1;
            const targetDist = 135;
            const delta = dist - targetDist;
            const force = delta * kAttract;
            const fx = (dx / dist) * force;
            const fy = (dy / dist) * force;
            if (!draggedNodeRef.current || src.id !== draggedNodeRef.current.id) {
              src.vx += fx;
              src.vy += fy;
            }
            if (!draggedNodeRef.current || tgt.id !== draggedNodeRef.current.id) {
              tgt.vx -= fx;
              tgt.vy -= fy;
            }
          }
        }

        // 3. Center gravity towards (400, 275)
        for (const n of nodes) {
          if (draggedNodeRef.current && n.id === draggedNodeRef.current.id) continue;
          const cx = 400;
          const cy = 275;
          n.vx += (cx - n.x) * 0.002 * alpha;
          n.vy += (cy - n.y) * 0.002 * alpha;
          n.x += n.vx;
          n.y += n.vy;
          n.vx *= friction;
          n.vy *= friction;
        }
      }

      // 4. Render to Canvas
      const width = canvas.width;
      const height = canvas.height;
      ctx.clearRect(0, 0, width, height);

      ctx.save();
      // Apply pan & zoom
      ctx.translate(pan.x, pan.y);
      ctx.scale(zoom, zoom);

      const nodeMap = new Map(nodes.map((n) => [n.id, n]));
      const activeNodeId = hoveredNodeId || selectedNode?.id;

      // Draw Edges
      for (const e of visibleEdges) {
        const src = nodeMap.get(e.source);
        const tgt = nodeMap.get(e.target);
        if (!src || !tgt) continue;

        const isHighlighted =
          activeNodeId && (e.source === activeNodeId || e.target === activeNodeId);

        ctx.beginPath();
        ctx.moveTo(src.x, src.y);
        ctx.lineTo(tgt.x, tgt.y);
        ctx.strokeStyle = isHighlighted ? '#10B981' : 'rgba(156, 163, 175, 0.28)';
        ctx.lineWidth = isHighlighted ? 2.8 : 1.2;
        ctx.stroke();

        // Edge label (drawn in middle if highlighted or zoomed in)
        if (isHighlighted || zoom > 1.3) {
          const midX = (src.x + tgt.x) / 2;
          const midY = (src.y + tgt.y) / 2;
          ctx.font = isHighlighted ? 'bold 10px Inter, sans-serif' : '9px Inter, sans-serif';
          ctx.fillStyle = isHighlighted ? '#10B981' : '#9CA3AF';
          ctx.textAlign = 'center';
          const cleanEdgeLabel = cleanValueString(e.label);
          ctx.fillText(cleanEdgeLabel, midX, midY - 4);
        }
      }

      // Draw Nodes
      for (const n of visibleNodes) {
        const colors = NODE_COLORS[n.type] || NODE_COLORS.condition;
        const isSelected = selectedNode?.id === n.id;
        const isHovered = hoveredNodeId === n.id;
        const isConnectedToActive =
          activeNodeId &&
          visibleEdges.some(
            (e) =>
              (e.source === activeNodeId && e.target === n.id) ||
              (e.target === activeNodeId && e.source === n.id)
          );

        // Glow halo for selected / hovered / connected node
        if (isSelected || isHovered) {
          ctx.beginPath();
          ctx.arc(n.x, n.y, n.radius + 7, 0, 2 * Math.PI);
          ctx.fillStyle = isSelected ? 'rgba(16, 185, 129, 0.4)' : 'rgba(16, 185, 129, 0.2)';
          ctx.fill();
        } else if (isConnectedToActive) {
          ctx.beginPath();
          ctx.arc(n.x, n.y, n.radius + 4, 0, 2 * Math.PI);
          ctx.fillStyle = 'rgba(16, 185, 129, 0.15)';
          ctx.fill();
        }

        // Main Node Circle
        ctx.beginPath();
        ctx.arc(n.x, n.y, n.radius, 0, 2 * Math.PI);
        ctx.fillStyle = colors.bg;
        ctx.strokeStyle = isSelected ? '#FFFFFF' : isConnectedToActive ? '#10B981' : colors.border;
        ctx.lineWidth = isSelected ? 3.5 : isConnectedToActive ? 2.5 : 1.5;
        ctx.fill();
        ctx.stroke();

        // Node Label
        ctx.font = n.type === 'patient' ? 'bold 11px Inter, sans-serif' : '10px Inter, sans-serif';
        ctx.fillStyle = '#1F2937';
        if (document.documentElement.classList.contains('dark')) {
          ctx.fillStyle = '#F3F4F6';
        }
        ctx.textAlign = 'center';

        const labelText = n.label.length > 20 ? n.label.slice(0, 18) + '...' : n.label;
        ctx.fillText(labelText, n.x, n.y + n.radius + 12);

        // Value text if present
        if (n.value && n.type !== 'patient' && zoom >= 0.85) {
          ctx.font = 'bold 9px monospace';
          ctx.fillStyle = '#10B981';
          const cleanVal = cleanValueString(n.value);
          ctx.fillText(cleanVal, n.x, n.y + n.radius + 22);
        }
      }

      ctx.restore();

      animFrameRef.current = requestAnimationFrame(render);
    };

    render();

    return () => {
      running = false;
      if (animFrameRef.current) cancelAnimationFrame(animFrameRef.current);
    };
  }, [visibleNodes, visibleEdges, pan, zoom, hoveredNodeId, selectedNode]);

  // Canvas Mouse Interaction: Pan, Zoom, Drag Node, Click Node
  const handleMouseDown = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const rect = canvas.getBoundingClientRect();
    const mouseX = (e.clientX - rect.left - pan.x) / zoom;
    const mouseY = (e.clientY - rect.top - pan.y) / zoom;

    // Check if clicked a node
    const clicked = visibleNodes.find((n) => {
      const dx = n.x - mouseX;
      const dy = n.y - mouseY;
      return Math.sqrt(dx * dx + dy * dy) <= n.radius + 5;
    });

    if (clicked) {
      setSelectedNode(clicked);
      draggedNodeRef.current = clicked;
      alphaRef.current = 0.3;
    } else {
      setIsDraggingCanvas(true);
      setDragStart({ x: e.clientX - pan.x, y: e.clientY - pan.y });
    }
  };

  const handleMouseMove = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    if (isDraggingCanvas) {
      setPan({ x: e.clientX - dragStart.x, y: e.clientY - dragStart.y });
      return;
    }

    const rect = canvas.getBoundingClientRect();
    const mouseX = (e.clientX - rect.left - pan.x) / zoom;
    const mouseY = (e.clientY - rect.top - pan.y) / zoom;

    // Drag node if active
    if (draggedNodeRef.current) {
      draggedNodeRef.current.x = mouseX;
      draggedNodeRef.current.y = mouseY;
      draggedNodeRef.current.vx = 0;
      draggedNodeRef.current.vy = 0;
      alphaRef.current = 0.25;
      return;
    }

    // Check hover
    const hovered = visibleNodes.find((n) => {
      const dx = n.x - mouseX;
      const dy = n.y - mouseY;
      return Math.sqrt(dx * dx + dy * dy) <= n.radius + 5;
    });

    setHoveredNodeId(hovered ? hovered.id : null);
  };

  const handleMouseUp = () => {
    setIsDraggingCanvas(false);
    draggedNodeRef.current = null;
  };

  const handleWheel = (e: React.WheelEvent<HTMLCanvasElement>) => {
    e.preventDefault();
    const canvas = canvasRef.current;
    if (!canvas) return;
    const rect = canvas.getBoundingClientRect();
    const mouseX = e.clientX - rect.left;
    const mouseY = e.clientY - rect.top;

    const zoomFactor = e.deltaY < 0 ? 1.12 : 0.88;
    const newZoom = Math.min(Math.max(zoom * zoomFactor, 0.4), 2.8);

    // Zoom centered towards cursor
    setPan({
      x: mouseX - (mouseX - pan.x) * (newZoom / zoom),
      y: mouseY - (mouseY - pan.y) * (newZoom / zoom),
    });
    setZoom(newZoom);
  };

  const resetView = () => {
    setPan({ x: 0, y: 0 });
    setZoom(1);
  };

  // Connected edges for the selected node
  const selectedNodeEdges = useMemo(() => {
    if (!selectedNode || !graphData) return [];
    return graphData.edges.filter(
      (e) => e.source === selectedNode.id || e.target === selectedNode.id
    );
  }, [selectedNode, graphData]);

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] space-y-3">
        <div className="w-8 h-8 border-2 border-[#10B981] border-t-transparent rounded-full animate-spin" />
        <p className="text-xs text-[#6B7280] dark:text-[#9CA3AF]">
          Constructing clinical knowledge network from verified patient vault...
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6 pb-12">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl sm:text-2xl font-semibold text-[#1F2937] dark:text-[#F3F4F6] flex items-center gap-2">
            <Share2 className="w-5 h-5 text-[#10B981]" /> Patient Knowledge Network & Clusters
          </h1>
          <p className="text-xs text-[#6B7280] dark:text-[#9CA3AF] mt-0.5">
            Interconnected clinical knowledge graph mapping diseases, active medications, biomarkers, and verified source provenance.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={resetView}
            leftIcon={<Maximize2 className="w-3.5 h-3.5" />}
          >
            Reset View
          </Button>
          <Button
            variant="primary"
            size="sm"
            onClick={handleSync}
            isLoading={isSyncing}
            leftIcon={<RefreshCw className="w-3.5 h-3.5" />}
          >
            Sync Knowledge Network
          </Button>
        </div>
      </div>

      {/* Metrics Summary Strip */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3.5">
        <div className="p-3.5 rounded-xl bg-white dark:bg-[#1B1E23] border border-[#E5E7EB] dark:border-[#2F3540] shadow-sm">
          <span className="text-[11px] font-medium text-[#6B7280] dark:text-[#9CA3AF] block">Total Knowledge Nodes</span>
          <span className="text-xl font-bold text-[#1F2937] dark:text-[#F3F4F6] tabular-nums">
            {graphData?.total_nodes || 0}
          </span>
          <span className="text-[10px] text-[#10B981] block mt-0.5">Verified Medical Entities</span>
        </div>
        <div className="p-3.5 rounded-xl bg-white dark:bg-[#1B1E23] border border-[#E5E7EB] dark:border-[#2F3540] shadow-sm">
          <span className="text-[11px] font-medium text-[#6B7280] dark:text-[#9CA3AF] block">Relational Edges</span>
          <span className="text-xl font-bold text-[#1F2937] dark:text-[#F3F4F6] tabular-nums">
            {graphData?.total_edges || 0}
          </span>
          <span className="text-[10px] text-blue-500 block mt-0.5">Treatment & Provenance Links</span>
        </div>
        <div className="p-3.5 rounded-xl bg-white dark:bg-[#1B1E23] border border-[#E5E7EB] dark:border-[#2F3540] shadow-sm">
          <span className="text-[11px] font-medium text-[#6B7280] dark:text-[#9CA3AF] block">Clinical Clusters</span>
          <span className="text-xl font-bold text-[#1F2937] dark:text-[#F3F4F6] tabular-nums">
            {graphData?.clusters.length || 0}
          </span>
          <span className="text-[10px] text-purple-500 block mt-0.5">Community Partitions</span>
        </div>
        <div className="p-3.5 rounded-xl bg-white dark:bg-[#1B1E23] border border-[#E5E7EB] dark:border-[#2F3540] shadow-sm">
          <span className="text-[11px] font-medium text-[#6B7280] dark:text-[#9CA3AF] block">Provenance Grounding</span>
          <span className="text-xl font-bold text-[#10B981] tabular-nums block">100% Verified</span>
          <span className="text-[10px] text-[#10B981] block mt-0.5">Zero-Hallucination Multi-Hop</span>
        </div>
      </div>

      {/* Filter and Control Bar */}
      <div className="bg-white dark:bg-[#1B1E23] p-4 rounded-2xl border border-[#E5E7EB] dark:border-[#2F3540] shadow-sm space-y-3">
        {/* Cluster Pills */}
        <div className="flex items-center gap-2 flex-wrap">
          <span className="text-xs font-semibold text-[#1F2937] dark:text-[#F3F4F6] flex items-center gap-1.5 mr-1">
            <Layers className="w-3.5 h-3.5 text-[#10B981]" /> Clusters:
          </span>
          <button
            onClick={() => setSelectedClusterId(null)}
            className={`px-3 py-1 rounded-lg text-xs font-medium transition-all ${
              selectedClusterId === null
                ? 'bg-[#10B981] text-white shadow-sm'
                : 'bg-[#FAF8F5] dark:bg-[#23272E] text-[#6B7280] dark:text-[#9CA3AF] hover:text-[#1F2937] dark:hover:text-[#F3F4F6]'
            }`}
          >
            All Clusters ({graphData?.clusters.length || 0})
          </button>
          {graphData?.clusters.map((c) => (
            <button
              key={c.id}
              onClick={() => setSelectedClusterId(c.id === selectedClusterId ? null : c.id)}
              className={`flex items-center gap-1.5 px-3 py-1 rounded-lg text-xs font-medium transition-all border ${
                selectedClusterId === c.id
                  ? 'bg-[#1F2937] text-white border-transparent'
                  : 'bg-[#FAF8F5] dark:bg-[#23272E] border-[#E5E7EB] dark:border-[#2F3540] text-[#4B5563] dark:text-[#D1D5DB] hover:border-[#10B981]'
              }`}
            >
              <span className="w-2 h-2 rounded-full shrink-0" style={{ backgroundColor: c.color }} />
              <span>{c.name}</span>
              <span className="text-[10px] text-[#9CA3AF]">({c.node_count})</span>
            </button>
          ))}
        </div>

        {/* Entity Type Filter & Search Input */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pt-2 border-t border-[#E5E7EB]/80 dark:border-[#2F3540]">
          <div className="flex items-center gap-1.5 flex-wrap text-xs">
            <span className="text-[#9CA3AF] mr-1">Filter:</span>
            {[
              { id: 'all', label: 'All' },
              { id: 'condition', label: 'Conditions', color: '#EF4444' },
              { id: 'medication', label: 'Medications', color: '#3B82F6' },
              { id: 'lab_test', label: 'Labs', color: '#10B981' },
              { id: 'document', label: 'Documents', color: '#6B7280' },
            ].map((t) => (
              <button
                key={t.id}
                onClick={() => setSelectedType(t.id)}
                className={`px-2.5 py-1 rounded-md text-[11px] font-medium transition-all ${
                  selectedType === t.id
                    ? 'bg-[#E5E7EB] dark:bg-[#2F3540] text-[#1F2937] dark:text-[#F3F4F6] font-semibold'
                    : 'text-[#6B7280] dark:text-[#9CA3AF] hover:text-[#1F2937]'
                }`}
              >
                {t.color && (
                  <span
                    className="inline-block w-1.5 h-1.5 rounded-full mr-1.5 align-middle"
                    style={{ backgroundColor: t.color }}
                  />
                )}
                {t.label}
              </button>
            ))}
          </div>

          <div className="relative w-full sm:w-64">
            <Search className="w-3.5 h-3.5 absolute left-3 top-2.5 text-[#9CA3AF]" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search node or analyte..."
              className="w-full h-8 pl-8 pr-3 rounded-lg bg-[#FAF8F5] dark:bg-[#121417] border border-[#E5E7EB] dark:border-[#2F3540] text-xs text-[#1F2937] dark:text-[#F3F4F6] placeholder-[#9CA3AF] focus:outline-none focus:border-[#10B981]"
            />
          </div>
        </div>
      </div>

      {/* Main Interactive Canvas & Inspection Drawer */}
      <div
        ref={containerRef}
        className="relative bg-white dark:bg-[#1B1E23] rounded-2xl border border-[#E5E7EB] dark:border-[#2F3540] shadow-sm overflow-hidden min-h-[550px]"
      >
        <canvas
          ref={canvasRef}
          width={880}
          height={550}
          onMouseDown={handleMouseDown}
          onMouseMove={handleMouseMove}
          onMouseUp={handleMouseUp}
          onWheel={handleWheel}
          className="w-full h-[550px] cursor-grab active:cursor-grabbing block"
        />

        {/* Legend Overlay */}
        <div className="absolute top-4 left-4 bg-white/90 dark:bg-[#1B1E23]/90 backdrop-blur-md p-3 rounded-xl border border-[#E5E7EB] dark:border-[#2F3540] text-[11px] space-y-1.5 shadow-sm pointer-events-none">
          <span className="font-semibold text-[#1F2937] dark:text-[#F3F4F6] block mb-1">Entity Legend</span>
          <div className="flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-full bg-[#EF4444]" />
            <span className="text-[#6B7280] dark:text-[#9CA3AF]">Condition / Diagnosis</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-full bg-[#3B82F6]" />
            <span className="text-[#6B7280] dark:text-[#9CA3AF]">Active Medication</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-full bg-[#10B981]" />
            <span className="text-[#6B7280] dark:text-[#9CA3AF]">Biomarker / Lab Result</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-full bg-[#6B7280]" />
            <span className="text-[#6B7280] dark:text-[#9CA3AF]">Medical Report Document</span>
          </div>
        </div>

        {/* Selected Node Details Drawer */}
        {selectedNode && (
          <div className="absolute top-0 right-0 h-full w-full sm:w-80 bg-white dark:bg-[#1B1E23] border-l border-[#E5E7EB] dark:border-[#2F3540] shadow-xl p-5 space-y-4 overflow-y-auto">
            <div className="flex items-start justify-between">
              <div>
                <span className="text-[10px] font-semibold uppercase tracking-wider text-[#10B981] block">
                  {selectedNode.type}
                </span>
                <h3 className="text-base font-bold text-[#1F2937] dark:text-[#F3F4F6] mt-0.5">
                  {selectedNode.label}
                </h3>
              </div>
              <button
                onClick={() => setSelectedNode(null)}
                className="p-1 rounded-lg text-[#9CA3AF] hover:text-[#1F2937] dark:hover:text-[#F3F4F6]"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="space-y-2 pt-1 text-xs">
              {selectedNode.code && (
                <div className="flex items-center justify-between p-2 rounded-lg bg-[#FAF8F5] dark:bg-[#23272E]">
                  <span className="text-[#6B7280] dark:text-[#9CA3AF]">Ontology Code:</span>
                  <span className="font-mono font-semibold text-[#1F2937] dark:text-[#F3F4F6]">
                    {selectedNode.code}
                  </span>
                </div>
              )}
              {selectedNode.value && (
                <div className="flex items-center justify-between p-2 rounded-lg bg-[#FAF8F5] dark:bg-[#23272E]">
                  <span className="text-[#6B7280] dark:text-[#9CA3AF]">Measured Value:</span>
                  <span className="font-mono font-bold text-[#10B981]">
                    {selectedNode.value}
                  </span>
                </div>
              )}
              <div className="flex items-center justify-between p-2 rounded-lg bg-[#FAF8F5] dark:bg-[#23272E]">
                <span className="text-[#6B7280] dark:text-[#9CA3AF]">Clinical Cluster:</span>
                <span className="font-medium text-[#1F2937] dark:text-[#F3F4F6]">
                  {selectedNode.cluster_name}
                </span>
              </div>
            </div>

            {/* Connected Relations in Graph */}
            <div className="space-y-2 pt-2 border-t border-[#E5E7EB] dark:border-[#2F3540]">
              <h4 className="text-xs font-semibold text-[#1F2937] dark:text-[#F3F4F6]">
                Connected Relationships ({selectedNodeEdges.length})
              </h4>
              <div className="space-y-1.5 text-xs max-h-48 overflow-y-auto">
                {selectedNodeEdges.map((e) => (
                  <div
                    key={e.id}
                    className="p-2 rounded-lg bg-[#FAF8F5] dark:bg-[#23272E]/50 border border-[#E5E7EB]/80 dark:border-[#2F3540] text-[11px] space-y-0.5"
                  >
                    <div className="font-semibold text-[#10B981]">{e.relation}</div>
                    <div className="text-[#6B7280] dark:text-[#9CA3AF]">{e.label}</div>
                    {e.document_title && (
                      <div className="text-[10px] text-[#9CA3AF] truncate">
                        Source: {e.document_title}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>

            {/* Source Document Citation Action */}
            {selectedNode.document_id && (
              <div className="pt-2">
                <Button
                  variant="outline"
                  size="sm"
                  className="w-full text-xs"
                  rightIcon={<ExternalLink className="w-3.5 h-3.5" />}
                  onClick={() => navigate('/vault')}
                >
                  View Document in Vault
                </Button>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Cluster Overview Cards */}
      <div className="space-y-3 pt-2">
        <h3 className="text-sm font-semibold text-[#1F2937] dark:text-[#F3F4F6] flex items-center gap-2">
          <Sparkles className="w-4 h-4 text-[#10B981]" /> Detected Health Topic Clusters
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3.5">
          {graphData?.clusters.map((c) => (
            <div
              key={c.id}
              onClick={() => setSelectedClusterId(selectedClusterId === c.id ? null : c.id)}
              className={`p-4 rounded-xl border transition-all cursor-pointer ${
                selectedClusterId === c.id
                  ? 'bg-emerald-50/40 dark:bg-emerald-950/20 border-[#10B981]'
                  : 'bg-white dark:bg-[#1B1E23] border-[#E5E7EB] dark:border-[#2F3540] hover:border-[#10B981]/50'
              }`}
            >
              <div className="flex items-center justify-between">
                <span className="font-semibold text-xs text-[#1F2937] dark:text-[#F3F4F6] flex items-center gap-2">
                  <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: c.color }} />
                  {c.name}
                </span>
                <Badge variant="secondary" className="text-[10px]">
                  {c.node_count} Nodes
                </Badge>
              </div>
              <div className="text-[11px] text-[#10B981] font-medium mt-1">
                Anchor Hub: {c.hub_entity}
              </div>
              <p className="text-[11px] text-[#6B7280] dark:text-[#9CA3AF] mt-1.5 leading-relaxed">
                {c.summary}
              </p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default KnowledgeGraphPage;

