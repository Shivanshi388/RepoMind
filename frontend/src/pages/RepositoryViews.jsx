import React,{useEffect,useState} from 'react';import{api}from'../services/api.js';import ArchitectureGraph from '../components/ArchitectureGraph.jsx';import{Activity,ArrowDownRight,ArrowUpRight,BookOpen,Boxes,Braces,Check,ChevronRight,FileCode2,GitCommitHorizontal,GitPullRequest,Network,Search,ShieldAlert,Star,GitBranch,FileText}from'lucide-react';
export function TabIcon({name}){let I={Overview:Activity,Files:FileCode2,Architecture:Network,Insights:Activity,Risks:ShieldAlert,Search,Compare:GitPullRequest,Ask:Braces}[name];return <I size={15}/>}
export function Sketch(){
  const [active,setActive]=useState("CORE");
  const modules=[
    {name:"ENTRY",x:25,y:119,w:90,h:42,detail:"A starting point for exploring the example repository."},
    {name:"ROUTES",x:165,y:40,w:90,h:44,detail:"A sample module connected to entry points and core code."},
    {name:"MODELS",x:165,y:198,w:90,h:44,detail:"A sample module linked to routes and shared logic."},
    {name:"CORE",x:315,y:111,w:88,h:54,detail:"Highlighted example module with several illustrated connections."},
    {name:"UTILS",x:315,y:181,w:88,h:40,detail:"A sample utilities module in the diagram."}
  ];
  const chosen=modules.find(m=>m.name===active);
  return <div className="sketch-wrap">
    <svg className="module-sketch" viewBox="0 0 440 280" role="group" aria-label="Interactive sample module relationship diagram">
      <g className="sketch-links" fill="none">
        <path d="M70 140 192 62M70 140 192 218M210 62l145 62M210 218l145-62M210 62 355 138M70 140 355 138"/>
        <path className="signal-link" strokeDasharray="4 5" d="M210 218V62"/>
      </g>
      {modules.map(m=><g key={m.name} className={`sketch-node ${active===m.name?"is-active":""}`} role="button" tabIndex="0" aria-label={`${m.name}: ${m.detail}`} onMouseEnter={()=>setActive(m.name)} onFocus={()=>setActive(m.name)} onClick={()=>setActive(m.name)} onKeyDown={e=>{if(e.key==="Enter"||e.key===" "){e.preventDefault();setActive(m.name)}}}>
        <rect x={m.x} y={m.y} width={m.w} height={m.h} rx="2"/>
        <text x={m.x+m.w/2} y={m.y+m.h/2+4}>{m.name}</text>
      </g>)}
      <text className="connectivity-label" x="311" y="102">CONNECTED MODULE</text>
    </svg>
    <div className="sketch-selection" aria-live="polite"><span>{active}</span><p>{chosen?.detail}</p></div>
  </div>
}

export function Capability({n,icon,title,text}){return <article><div><small>{n}</small>{icon}</div><h3>{title}</h3><p>{text}</p></article>}
export function Footer({workspace}){return <footer className="footer"><span>{workspace?'ANALYSIS / COMMIT PINNED':'REPOMIND / ENGINEERING ARCHIVE'}</span><span>{workspace?'STATIC ANALYSIS â€¢ SOURCE NOT EXECUTED':'BUILT TO MAKE CODEBASES LEGIBLE'} <i/></span></footer>}
function Stat({label,value,note}){return <div className="stat"><span>{label}</span><b>{value}</b><small>{note}</small></div>}
export function Overview({repo,langs,files,ins,graph,open}) {
  const total = langs.reduce((sum, item) => sum + (Number(item[1]) || 0), 0);
  const languageCount = langs.length;
  const topFiles = (ins?.complex_files || []).slice(0, 4);

  return <div className="overview editorial-overview">
    <section className="overview-intro">
      <div>
        <small className="overview-kicker">REPOSITORY FIELD NOTES · {repo.commit_sha?.slice(0, 8) || "CURRENT REVISION"}</small>
        <h2>Understand<br/>the codebase.</h2>
        <p>{repo.description || `Explore ${repo.full_name || repo.name} through the files that make it up and the connections between them.`}</p>
      </div>
      <div className="overview-facts">
        <button onClick={() => document.querySelector('[data-tab="Files"]')?.click()}><b>{repo.file_count ?? files.length}</b><span>Files</span></button>
        <button onClick={() => document.querySelector('[data-tab="Files"]')?.click()}><b>{languageCount}</b><span>Languages</span></button>
        <button onClick={() => document.querySelector('[data-tab="Architecture"]')?.click()}><b>{repo.dependency_count ?? graph?.edges?.length ?? 0}</b><span>Links between files</span></button>
        <button onClick={() => document.querySelector('[data-tab="Insights"]')?.click()}><b>{repo.symbol_count ?? 0}</b><span>Code pieces found</span></button>
      </div>
    </section>

    <section className="beginner-guide">
  <div><small>NEW TO THIS PROJECT?</small><h3>Here is a simple way to explore.</h3></div>
  <article><b>1</b><span><strong>Choose a file</strong><small>Files are the individual pieces that make up a project.</small></span></article>
  <article><b>2</b><span><strong>Look at the map</strong><small>Lines show when one project file refers to another.</small></span></article>
  <article><b>3</b><span><strong>Open a highlight</strong><small>Start with a file RepoMind picked from the analyzed code.</small></span></article>
</section><section className="overview-map">
      <div className="overview-map-heading">
        <div><small>A SIMPLE MAP OF THE PROJECT</small><h3>See how the parts connect</h3></div>
        <button onClick={() => document.querySelector('[data-tab="Architecture"]')?.click()}>Open full map <ArrowDownRight size={15}/></button>
      </div>
      {graph?.nodes?.length
        ? <ArchitectureGraph graph={{...graph,nodes:graph.nodes.slice(0,25),edges:graph.edges.filter(e=>graph.nodes.slice(0,25).some(n=>n.id===e.source)&&graph.nodes.slice(0,25).some(n=>n.id===e.target))}} open={open}/>
        : <Empty text="No resolvable file links were found in this analysis."/>}
      <p className="overview-hint">Choose a box to open that file. Lines show which files refer to one another.</p>
    </section>

    <section className="overview-lower">
      <div className="overview-language">
        <small>LANGUAGES IN THIS REPOSITORY</small>
        {langs.length
          ? <><Languages langs={langs}/><p>{total ? "Share is calculated from analyzed source bytes." : "Language data is available for analyzed files."}</p></>
          : <p>No language data is available for this analysis.</p>}
      </div>
      <div className="overview-files">
        <small>FILES THAT MAY TAKE MORE EFFORT TO UNDERSTAND</small>
        {topFiles.length
          ? topFiles.map((item, i) => <button key={item.path} onClick={() => open(item.path)}><span>0{i + 1}</span><b>{item.path}</b><em>{item.complexity}</em><ArrowUpRight size={14}/></button>)
          : <p>No complexity observations are available.</p>}
      </div>
    </section>
  </div>;
}

function PanelTitle({left,right}){return <div className="paneltitle"><small>{left}</small><small>{right}</small></div>}
function Languages({langs}){return <div className="languages"><div className="langbar">{langs.map(([l,v],i)=><i key={l} className={`c${i%5}`} style={{width:`${v}%`}}/>)}</div>{langs.slice(0,7).map(([l,v],i)=><div key={l}><span><i className={`dot c${i%5}`}/>{l}</span><b>{v}%</b></div>)}</div>}
function Empty({text}){return <div className="empty"><Network size={25}/><p>{text}</p></div>}
export function FilesPage({repoId,files,selected,select,file,filter,setFilter}){
 const visible=files.filter(x=>x.path.toLowerCase().includes(filter.toLowerCase())),tree={};
 for(const f of visible){let cur=tree;const parts=f.path.split('/');for(const d of parts.slice(0,-1)){cur[d]??={};cur=cur[d]}cur[parts.at(-1)]=f.path}
 const [impact,setImpact]=useState(null),[similar,setSimilar]=useState([]),[suggestion,setSuggestion]=useState(null),[findings,setFindings]=useState([]),[reviewSummary,setReviewSummary]=useState(''),[toolError,setToolError]=useState(''),[loading,setLoading]=useState(false);
 useEffect(()=>{if(!repoId||!selected)return;setLoading(true);setToolError('');setFindings([]);setReviewSummary('');Promise.all([api.impact(repoId,selected),api.similarity(repoId,selected),api.testSuggestions(repoId)]).then(([i,s,t])=>{setImpact(i);setSimilar(s.matches||[]);setSuggestion((t.suggestions||[]).find(x=>x.path===selected)||null)}).catch(e=>setToolError(e.message)).finally(()=>setLoading(false))},[repoId,selected]);
 async function review(){try{const r=await api.review(repoId,selected);setFindings(r.findings||[]);setReviewSummary(r.llm_review||'');setToolError('')}catch(e){setToolError(e.message)}}
 return <section className="filepage"><aside><PanelTitle left="REPOSITORY FILES" right={`${files.length} FILES`}/><label className="filter"><Search size={13}/><input value={filter} onChange={e=>setFilter(e.target.value)} placeholder="Filter files"/></label><div className="tree"><Tree nodes={tree} selected={selected} select={select}/></div></aside><div className="codepanel">{file?<><div className="codehead"><b><FileCode2 size={14}/>{file.path}</b><small>{file.language} / {file.line_count} LINES</small></div><div className="filedesc"><small>FILE ANALYSIS</small><p>{file.symbols?.length||0} symbols | {file.imports?.length||0} imports | complexity estimate {file.complexity}</p><div>{file.symbols?.map((s,i)=><span key={i}>{s.type} <b>{s.name}</b> :{s.start_line}-{s.end_line}</span>)}</div></div><div className="phase-tools"><section><b>CHANGE IMPACT</b>{loading?<small>Tracing dependencies...</small>:impact?.impacted?.length?impact.impacted.slice(0,6).map(x=><button key={x.path} onClick={()=>select(x.path)}>{x.path}<small>{x.kind} | depth {x.depth}</small></button>):<small>No dependent files were resolved.</small>}</section><section><b>SIMILAR CODE</b>{similar.length?similar.slice(0,5).map((x,i)=><button key={i} onClick={()=>select(x.match.path)}>{x.match.name} | {x.match.path}<small>{Math.round(x.similarity*100)}% token overlap</small></button>):<small>No strong token matches.</small>}</section><section><b>TEST SUGGESTION</b>{suggestion?<p>{suggestion.reasons.join('; ')}{suggestion.related_tests.length?` | related: ${suggestion.related_tests.join(', ')}`:''}</p>:<p>No additional static test signal for this file.</p>}<small>Suggested only; no tests were run.</small></section><section><button className="tool-action" onClick={review}>Check this file for review clues <ArrowDownRight size={13}/></button>{reviewSummary&&<p className="review-summary">{reviewSummary}</p>}{findings.map((x,i)=><p key={i} className={`finding ${x.severity}`}><b>{x.severity.toUpperCase()} | line {x.line}</b> {x.message}<code>{x.evidence}</code></p>)}</section>{toolError&&<small className="tool-error">{toolError}</small>}</div><pre className="code">{(file.content||'').split('\n').map((line,i)=><div key={i}><small>{i+1}</small><code><HighlightedLine line={line||' '} /></code></div>)}</pre></>:<Empty text="Select a source file to inspect code, impact, similarity and test suggestions."/>}</div></section>}
function Tree({nodes,selected,select,depth=0}){return Object.entries(nodes).sort(([a,av],[b,bv])=>typeof av==='string'&&typeof bv!=='string'?-1:typeof av!=='string'&&typeof bv==='string'?1:a.localeCompare(b)).map(([name,val])=>typeof val==='string'?<button className={`treefile ${selected===val?'chosen':''}`} style={{paddingLeft:12+depth*14}} key={name} onClick={()=>select(val)}><FileCode2 size={13}/>{name}</button>:<details open={depth<1} key={name}><summary style={{paddingLeft:10+depth*14}}><ChevronRight size={12}/>{name}</summary><Tree nodes={val} selected={selected} select={select} depth={depth+1}/></details>)}
export function Architecture({graph,open}){return <div className="report"><div className="reporthead"><small>DEPENDENCY ANALYSIS / FILE LEVEL</small><h2>How the project files connect</h2><p>Lines show project files that refer to one another. Packages installed separately are not shown.</p></div><div className="largegraph">{graph?.nodes?.length?<ArchitectureGraph graph={graph} open={open}/>:<Empty text="No resolvable edges found."/>}</div><section className="panel edges"><PanelTitle left="RESOLVED EDGES" right={`${graph?.edges?.length||0} TOTAL`}/>{graph?.edges?.slice(0,80).map((e,i)=><div key={i}><span>{e.source}</span><ArrowDownRight size={14}/><button onClick={()=>open(e.target)}>{e.target}</button></div>)}</section></div>}
export function Insights({ins,open}){return <div className="report"><div className="reporthead"><small>STATIC OBSERVATIONS / NOT PREDICTIONS</small><h2>What stands out</h2><p>Measurements help prioritize exploration; they are not evidence of defects.</p></div><div className="insgrid"><Insight title="Largest files" unit="LINES" data={ins?.large_files?.map(x=>({path:x.path,value:x.line_count}))} open={open}/><Insight title="Highest complexity estimate" unit="BRANCH SIGNAL" data={ins?.complex_files?.map(x=>({path:x.path,value:x.complexity}))} open={open}/><Insight title="Most imported files" unit="INCOMING LINKS" data={ins?.connected_files?.map(x=>({path:x.path,value:x.incoming}))} open={open}/></div></div>}
function Insight({title,unit,data=[],open}){return <section className="panel insight"><PanelTitle left={title} right={unit}/>{data?.length?data.map(x=><button key={x.path} onClick={()=>open(x.path)}><span>{x.path}</span><b>{x.value}</b></button>):<p>No data.</p>}</section>}
export function Risks({files,report,open}){const rows=report?.items||[];return <div className="report"><div className="reporthead"><small>FILES THAT MAY DESERVE A CLOSER LOOK</small><h2>{report?.model?.trained?'A time-tested review ranking':'History signals and baseline'}</h2><p>{report?.model?.trained?`Logistic regression trained on earlier history snapshots. Test F1 ${report.model.f1}; PR-AUC ${report.model.pr_auc}. Scores are relative rankings, not bug probabilities.`:report?.model?.reason||'Loading commit history and training data...'}</p></div><div className="risk-model"><b>{report?.model?.trained?'MODEL':'HEURISTIC FALLBACK'}</b><span>{report?.history_commits||0} commit details inspected</span><small>{report?.model?.label_note||'Commit-message labels are noisy indicators, not confirmed bugs.'}</small></div><section className="panel risks">{(rows.length?rows:[...files].sort((a,b)=>b.complexity-a.complexity).map(f=>({path:f.path,score:f.complexity,score_type:'static complexity only',risk_level:'untrained',features:{complexity_estimate:f.complexity},evidence:[`complexity estimate ${f.complexity}`]}))).slice(0,25).map((f,i)=><button key={f.path} onClick={()=>open(f.path)}><span>0{i+1}</span><b>{f.path}<small>{f.score_type} | {f.risk_level}</small></b><em>REVIEW SIGNAL <strong>{f.score}</strong></em><ArrowUpRight size={14}/></button>)}</section><p className="caveat"><ShieldAlert size={14}/> Heuristic bug-fix labels are noisy. Scores are not calibrated probabilities or confirmed defects.</p>{report?.model?.trained&&<div className="metrics-row">Time split | {report.model.training_examples} train rows | {report.model.test_examples} holdout rows | precision {report.model.precision} | recall {report.model.recall} | churn-baseline F1 {report.model.churn_baseline?.f1}</div>}</div>}
export function SearchPage({repoId,query,setQuery,hits,open}){const[semantic,setSemantic]=useState(false),[semHits,setSemHits]=useState([]),[available,setAvailable]=useState(false);useEffect(()=>{if(!semantic||!query.trim()){setSemHits([]);return}const t=setTimeout(()=>api.semanticSearch(repoId,query).then(x=>{setSemHits(x.results||[]);setAvailable(x.semantic_available)}).catch(()=>setSemHits([])),250);return()=>clearTimeout(t)},[semantic,query,repoId]);const results=semantic?semHits:hits;return <div className="report"><div className="reporthead"><small>HYBRID RETRIEVAL / LOCAL EMBEDDINGS OPTIONAL</small><h2>Search for a word or phrase</h2></div><div className="searchbox"><Search size={17}/><input value={query} onChange={e=>setQuery(e.target.value)} placeholder="Search symbols, filenames, or code"/><kbd>{semantic?(available?'OLLAMA':'LEXICAL FALLBACK'):'BM25'}</kbd></div><label className="semantic-toggle"><input type="checkbox" checked={semantic} onChange={e=>setSemantic(e.target.checked)}/> Rerank with local Ollama embeddings when available</label><small className="searchcount">{results.length} MATCHES / CITATIONS OPEN SOURCE CONTEXT</small><div>{results.map((h,i)=><button className="result" key={`${h.path}:${h.start_line||h.line}:${i}`} onClick={()=>open(h.path)}><small>{h.path}<span>lines {h.start_line||h.line}-{h.end_line||h.line}</span></small>{h.symbol&&<b>{h.symbol}</b>}<code>{h.snippet}</code></button>)}</div>{query&&!results.length&&<Empty text="No matches found."/>}</div>}
export function Compare({repo,repoId}){const[base,setBase]=useState(repo.default_branch),[head,setHead]=useState(repo.commit_sha),[prUrl,setPrUrl]=useState(''),[result,setResult]=useState(null),[error,setError]=useState(''),[busy,setBusy]=useState(false);async function run(fn){setBusy(true);setError('');try{setResult(await fn())}catch(e){setError(e.message);setResult(null)}finally{setBusy(false)}}return <div className="report"><div className="reporthead"><small>REVISION AND PULL REQUEST ANALYSIS</small><h2>See what changed</h2><p>GitHub metadata and changed paths are retrieved read-only. RepoMind does not approve, merge, or execute PR code.</p></div><section className="compare-form"><b>COMPARE REVISIONS</b><div><input value={base} onChange={e=>setBase(e.target.value)} placeholder="Starting version"/><ArrowDownRight size={15}/><input value={head} onChange={e=>setHead(e.target.value)} placeholder="Version to compare"/><button disabled={busy} onClick={()=>run(()=>api.compare(repoId,base,head))}>Compare</button></div><b>LOOK AT A GITHUB CHANGE</b><div><input className="wide" value={prUrl} onChange={e=>setPrUrl(e.target.value)} placeholder={`https://github.com/${repo.full_name}/pull/123`}/><button disabled={busy} onClick={()=>run(()=>api.pullRequest(repoId,prUrl))}>Analyze PR</button></div></section>{error&&<p className="tool-error">{error}</p>}{result&&<section className="panel compare-result">{result.llm_summary&&<p className="review-summary">{result.llm_summary}</p>}<h3>{result.title||`${result.base} → ${result.head}`}</h3><p>{result.total_commits??result.files?.length} commits/files | {result.ahead_by??''} commits ahead</p>{result.files?.map((f,i)=><article key={i}><b>{f.path}</b><small>{f.status} | +{f.additions}/âˆ’{f.deletions} | {f.changes} edits</small>{f.impact?.impacted?.slice(0,4).map(x=><span key={x.path}>Impact: {x.path}</span>)}{f.static_findings?.map((x,j)=><span key={j}>{x.severity}: {x.message}</span>)}{f.patch_excerpt&&<code>{f.patch_excerpt}</code>}</article>)}</section>}</div>}
export function AskPanel({repoId,openFile}){
  const[q,setQ]=useState(''),[mode,setMode]=useState('ask'),[result,setResult]=useState(null),[error,setError]=useState(''),[busy,setBusy]=useState(false);
  const questions=[
    {title:'What is this project for?',note:'Get a plain-English explanation based on the project files.'},
    {title:'Where should I start exploring?',note:'Find useful starting points in this repository.'},
    {title:'What do the lines on the map mean?',note:'Understand how the project files connect.'},
    {title:'Which files may be harder to understand?',note:'Ask about the files and signals RepoMind found.'},
    {title:'Are the review suggestions confirmed bugs?',note:'Learn what RepoMind can and cannot conclude.'},
    {title:'What is a pull request?',note:'Get a simple explanation of this GitHub term.'}
  ];
  async function ask(question){
    setMode('ask');setQ(question);setBusy(true);setError('');setResult(null);
    try{setResult(await api.chat(repoId,question))}
    catch(x){setError(x.message)}
    finally{setBusy(false)}
  }
  async function submit(e){
    e.preventDefault();if(!q.trim())return;
    setBusy(true);setError('');setResult(null);
    try{setResult(await(mode==='ask'?api.chat(repoId,q):api.debug(repoId,q)))}
    catch(x){setError(x.message)}
    finally{setBusy(false)}
  }
  return <section className="ask-panel">
    <div className="ask-intro">
      <small>ASK ABOUT THIS PROJECT</small>
      <h2>Questions welcome. GitHub knowledge not required.</h2>
      <p>Ask in plain English. RepoMind looks only at the repository you analyzed, and shows the files behind its answers. If it cannot find enough evidence, it will say so.</p>
    </div>
    <div className="ask-beginner">
      <div className="ask-section-heading"><b>TRY A STARTER QUESTION</b><span>Choose one to get an answer</span></div>
      <div className="ask-question-grid">
        {questions.map((item,i)=><button type="button" key={item.title} onClick={()=>ask(item.title)} disabled={busy}>
          <span className="ask-question-number">0{i+1}</span><span><strong>{item.title}</strong><small>{item.note}</small></span><ArrowDownRight size={15}/>
        </button>)}
      </div>
    </div>
    <form onSubmit={submit} className="ask-form">
      <label htmlFor="repomind-question">ASK YOUR OWN QUESTION</label>
      <div className="ask-controls">
        <select aria-label="Question type" value={mode} onChange={e=>setMode(e.target.value)}>
          <option value="ask">Project question</option><option value="debug">Explain an error</option>
        </select>
        <input id="repomind-question" value={q} onChange={e=>setQ(e.target.value)} placeholder="For example: What happens when someone signs in?" required/>
        <button disabled={busy}>{busy?'Finding an answer...':mode==='ask'?'Get an answer':'Investigate'}</button>
      </div>
    </form>
    {busy&&<p className="ask-status" aria-live="polite">Looking through this repository for useful evidence...</p>}
    {error&&<p className="tool-error">{error}</p>}
    {result&&<div className="answer" aria-live="polite">
      <div className="answer-heading"><b>AN ANSWER FROM THIS PROJECT</b>{result.grounded&&<span>Based on repository evidence</span>}</div>
      <p>{result.answer}</p>

      {result.hypotheses?.map((x,i)=><p key={i}>{x}</p>)}
      {(result.citations||result.evidence||[]).length>0&&<div className="answer-citations">
        <b>FILES USED</b>
        {(result.citations||result.evidence||[]).map((x,i)=><button type="button" key={`${x.path}:${i}`} onClick={()=>openFile(x.path)}><span>{x.path}</span><small>Lines {x.start_line||x.line}{x.end_line&&x.end_line!==(x.start_line||x.line)?`-${x.end_line}`:''}</small><ArrowDownRight size={13}/></button>)}
      </div>}
    </div>}
  </section>
}
function HighlightedLine({line}){const re=/(\"(?:\\.|[^\"\\])*\"|'(?:\\.|[^'\\])*'|`(?:\\.|[^`\\])*`|\/\/.*|#.*|\b(?:async|await|class|const|def|elif|else|export|extends|false|for|from|function|if|import|in|interface|let|new|null|return|self|static|this|throw|true|try|var|while|yield)\b|\b\d+(?:\.\d+)?\b)/g;const parts=[];let last=0,m;while((m=re.exec(line))){if(m.index>last)parts.push(line.slice(last,m.index));const t=m[0],kind=/^[\"'`]/.test(t)?'tok-string':t.startsWith('//')||t.startsWith('#')?'tok-comment':/^\d/.test(t)?'tok-number':'tok-keyword';parts.push(<span className={kind} key={m.index}>{t}</span>);last=re.lastIndex}if(last<line.length)parts.push(line.slice(last));return parts}





