import React,{useMemo,useState} from "react";

export default function ArchitectureGraph({graph,open}) {
  const [active,setActive]=useState(null);
  const nodes=graph?.nodes||[];
  const columns=Math.min(5,Math.max(1,nodes.length));
  const rows=Math.ceil(nodes.length/columns);
  const nodeW=190,nodeH=54,gapX=40,gapY=64,pad=36;
  const width=pad*2+columns*nodeW+(columns-1)*gapX;
  const height=pad*2+rows*nodeH+(rows-1)*gapY;
  const positions=useMemo(()=>{
    const map={};
    nodes.forEach((n,i)=>{
      map[n.id]={x:pad+(i%columns)*(nodeW+gapX),y:pad+Math.floor(i/columns)*(nodeH+gapY)};
    });
    return map;
  },[nodes,columns]);
  const selected=nodes.find(n=>n.id===active);

  return <div className="architecture-map-wrap">
    <svg className="graph" viewBox={`0 0 ${width} ${height}`} role="group" aria-label="Repository file relationship map">
      <g className="map-edges">
        {(graph?.edges||[]).map((e,i)=>{
          const a=positions[e.source],b=positions[e.target];
          if(!a||!b)return null;
          return <line key={`${e.source}-${e.target}-${i}`}
            x1={a.x+nodeW/2} y1={a.y+nodeH/2}
            x2={b.x+nodeW/2} y2={b.y+nodeH/2}
            className={active===e.source||active===e.target?"edge-related":""}/>;
        })}
      </g>
      {nodes.map(n=>{
        const p=positions[n.id];
        const label=(n.label||n.path||n.id||"file").split("/").pop();
        return <g key={n.id} className={`map-node ${active===n.id?"is-active":""}`}
          role="button" tabIndex="0" aria-label={`Open ${n.path||label}`}
          onMouseEnter={()=>setActive(n.id)} onFocus={()=>setActive(n.id)}
          onClick={()=>{setActive(n.id);open?.(n.path)}}
          onDoubleClick={()=>open?.(n.path)}
          onKeyDown={e=>{if(e.key==="Enter"){open?.(n.path)}else if(e.key===" "){e.preventDefault();setActive(n.id)}}}>
          <title>{n.path||label}</title><rect x={p.x} y={p.y} width={nodeW} height={nodeH} rx="3"/>
          <text x={p.x+nodeW/2} y={p.y+nodeH/2+5}>{label.length>19?label.slice(0,16)+"...":label}</text>
        </g>;
      })}
    </svg>
    <div className="map-selection" aria-live="polite">
      {selected?<><b>{selected.path||selected.label||selected.id}</b><span>Select once to open the file.</span></>:<span>Select a file to open it. Connections show imports resolved inside this repository.</span>}
    </div>
  </div>;
}


