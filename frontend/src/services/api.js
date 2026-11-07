const API=(import.meta.env.VITE_API_URL||"http://localhost:8000/api/v1").replace(/\/$/,"");

async function req(path,options={}) {
  const response=await fetch(API+path,{credentials:"include",...options});
  let data={};
  try { data=await response.json(); } catch {}
  if(!response.ok) throw Error(data.detail||`Request failed (${response.status})`);
  return data;
}

const json=(body)=>({method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(body)});

export const api={
  login:()=>window.location.assign(`${API}/auth/github/login`),
  me:()=>req("/auth/me"),
  logout:()=>req("/auth/logout",{method:"POST"}),
  myRepositories:()=>req("/auth/repositories"),
  saveRepository:repository_id=>req("/auth/repositories",json({repository_id})),

  analyze:url=>req("/repositories/analyze",json({url})),
  job:id=>req(`/repositories/jobs/${id}`),
  overview:id=>req(`/repositories/${encodeURIComponent(id)}`),
  files:id=>req(`/repositories/${encodeURIComponent(id)}/files`),
  file:(id,path)=>req(`/repositories/${encodeURIComponent(id)}/files/content?path=${encodeURIComponent(path)}`),
  graph:id=>req(`/repositories/${encodeURIComponent(id)}/architecture`),
  insights:id=>req(`/repositories/${encodeURIComponent(id)}/insights`),
  search:(id,q)=>req(`/repositories/${encodeURIComponent(id)}/search?q=${encodeURIComponent(q)}`),
  risk:id=>req(`/repositories/${encodeURIComponent(id)}/risk`),
  impact:(id,path)=>req(`/repositories/${encodeURIComponent(id)}/impact?path=${encodeURIComponent(path)}`),
  similarity:(id,path)=>req(`/repositories/${encodeURIComponent(id)}/similarity?path=${encodeURIComponent(path)}`),
  testSuggestions:id=>req(`/repositories/${encodeURIComponent(id)}/test-suggestions`),
  semanticSearch:(id,q)=>req(`/repositories/${encodeURIComponent(id)}/semantic-search?q=${encodeURIComponent(q)}`),
  chat:(id,question)=>req(`/repositories/${encodeURIComponent(id)}/chat`,json({question})),
  debug:(id,question)=>req(`/repositories/${encodeURIComponent(id)}/debug`,json({question})),
  review:(id,path)=>req(`/repositories/${encodeURIComponent(id)}/code-review`,json({path:path||null})),
  compare:(id,base,head)=>req(`/repositories/${encodeURIComponent(id)}/compare`,json({base,head})),
  pullRequest:(id,url)=>req(`/repositories/${encodeURIComponent(id)}/pull-request`,json({url}))
};
