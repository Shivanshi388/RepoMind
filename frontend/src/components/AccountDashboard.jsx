import React,{useEffect,useState} from "react";
import {api} from "../services/api.js";

export default function AccountDashboard({user,onLogout,onOpen}) {
  const [repositories,setRepositories]=useState([]);
  const [loading,setLoading]=useState(true);
  const [error,setError]=useState("");const [opening,setOpening]=useState("");

  useEffect(()=>{
    api.myRepositories()
      .then(data=>setRepositories(data.repositories||[]))
      .catch(err=>setError(err.message))
      .finally(()=>setLoading(false));
  },[]);

  return <div className="account-dashboard">
    <div className="account-heading">
      <small>YOUR REPOMIND ACCOUNT</small>
      <h1>Your projects, in one place.</h1>
      <p>Repositories you have explored will appear here.</p>
    </div>

    <section className="account-profile">
      {user.avatar_url
        ? <img src={user.avatar_url} alt="" />
        : <div className="account-avatar">{(user.name||"U").slice(0,1).toUpperCase()}</div>}
      <div className="account-details">
        <small>SIGNED IN WITH GITHUB</small>
        <h2>{user.name}</h2>
        <p>@{user.username}{user.email?` · ${user.email}`:""}</p>
      </div>
      <button onClick={onLogout}>Sign out</button>
    </section>

    <section className="account-repositories">
      <div className="account-list-heading">
        <div><small>YOUR HISTORY</small><h2>Repositories you explored</h2></div>
        <span>{repositories.length} saved</span>
      </div>

      {loading&&<p>Loading your repositories...</p>}
      {error&&<p className="account-error">{error}</p>}
      {!loading&&!error&&!repositories.length&&
        <div className="account-empty">
          <h3>No repositories saved yet</h3>
          <p>Analyze a public repository while signed in, and it will show up here.</p>
        </div>}

      {repositories.map(repo=><article className="account-repo" key={repo.repository_id}>
        <div>
          <small>{repo.full_name}</small>
          <button type="button" className="account-repo-title" onClick={async()=>{setError("");setOpening(repo.repository_id);try{await onOpen(repo.repository_id)}catch(err){setError(err.message||"Could not open this analysis.")}finally{setOpening("")}}}>{opening===repo.repository_id?"Opening...":repo.name}</button>
          <p>{repo.description||"No description was provided on GitHub."}</p>
          <span>{repo.file_count} files analyzed · {repo.default_branch} branch</span>
        </div>
        <a href={repo.html_url} target="_blank" rel="noreferrer">View on GitHub ↗</a>
      </article>)}
    </section>
  </div>;
}

