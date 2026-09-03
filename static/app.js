const backend = document.querySelector('#backend');
const blender = document.querySelector('#blender');
const learning = document.querySelector('#learning');
const version = document.querySelector('#version');
const setupWorkflowsButton = document.querySelector('#setupWorkflows');
const form = document.querySelector('#generateForm');
const message = document.querySelector('#message');
const button = document.querySelector('#generateButton');
const generationsEl = document.querySelector('#generations');
const viewer = document.querySelector('#viewer');
const viewerEmpty = document.querySelector('#viewerEmpty');
const viewerMeta = document.querySelector('#viewerMeta');
const downloadBest = document.querySelector('#downloadBest');
const multiInputs = [...document.querySelectorAll('.multiOnly input[type=file]')];

function selectedMode(){ return form.querySelector('input[name=mode]:checked').value; }
function selectedQuality(){ return form.querySelector('input[name=quality]:checked').value; }
function updateMode(){ const multi=selectedMode()==='multiview'; document.body.classList.toggle('isMulti',multi); multiInputs.forEach(input=>input.disabled=!multi); refreshStatus(); }
function updateFileLabel(input){ const label=input.closest('.viewSlot'); const target=label?.querySelector('.fileName'); if(target) target.textContent=input.files?.[0]?.name||'Bild waehlen'; label?.classList.toggle('hasFile',Boolean(input.files?.length)); }
function setViewer(id,title,variant='best',repairStatus=''){ viewer.src=`/api/generations/${id}/model?variant=${variant}&t=${Date.now()}`; viewerEmpty.hidden=true; downloadBest.href=`/api/generations/${id}/file?variant=${variant}`; downloadBest.classList.remove('disabled'); viewerMeta.textContent=`${title||'Modell'} · ${variant==='repaired'?'reparierte Version':variant==='raw'?'Rohmodell':'beste verfuegbare Version'}${repairStatus?` · Repair: ${repairStatus}`:''}`; }

async function refreshStatus(){
  try{
    const [s,l]=await Promise.all([fetch('/api/status').then(r=>r.json()),fetch('/api/learning/stats').then(r=>r.json())]);
    version.textContent=`v${s.version}`;
    learning.textContent=`${l.approved} freigegeben · ${l.feedback} Bewertungen · ${l.classified_projects||0} klassifiziert`;
    const all=Object.values(s.workflows||{}); const ready=all.length===4&&all.every(x=>x.exists);
    setupWorkflowsButton.textContent=ready?'Workflows neu erzeugen':'Workflows automatisch einrichten'; setupWorkflowsButton.classList.toggle('ready',ready);
    const key=`${selectedMode()}_${selectedQuality()}`; const wf=s.workflows?.[key];
    if(s.comfy.online&&wf?.exists){ backend.textContent=`TRELLIS bereit · ${selectedMode()==='multiview'?'MultiView':'SingleView'} ${selectedQuality()}`; backend.className='pill ok'; }
    else { const missing=[]; if(!s.comfy.online) missing.push('ComfyUI offline'); if(!wf?.exists) missing.push(`${key}-Workflow fehlt`); backend.textContent=missing.join(' / '); backend.className='pill bad'; }
    if(s.blender?.available){ blender.textContent='Blender Auto-Repair bereit'; blender.className='subpill good'; }
    else { blender.textContent='Blender nicht gefunden · Rohmodell bleibt nutzbar'; blender.className='subpill warn'; }
  }catch(e){ backend.textContent='Statusfehler'; backend.className='pill bad'; }
}

async function setupWorkflows(){
  const old=setupWorkflowsButton.textContent; setupWorkflowsButton.disabled=true; setupWorkflowsButton.textContent='Richte Workflows ein ...'; message.textContent='3DCreator richtet die lokalen TRELLIS-AMD-Profile ein ...';
  try{ const res=await fetch('/api/setup/workflows?force=true',{method:'POST'}); const data=await res.json(); if(!res.ok) throw new Error(data.detail||'Workflow-Einrichtung fehlgeschlagen'); const statuses=Object.entries(data.files||{}).map(([key,value])=>`${key}: ${value.status}`).join(' · '); message.textContent=`Workflows bereit. ${statuses}`; await refreshStatus(); }
  catch(e){ message.textContent=`Workflow-Fehler: ${e.message}`; }
  finally{ setupWorkflowsButton.disabled=false; if(setupWorkflowsButton.textContent==='Richte Workflows ein ...') setupWorkflowsButton.textContent=old; }
}

async function saveFeedback(id,root){ const rating=Number(root.querySelector('[name=rating]').value); const note=root.querySelector('[name=note]').value; const approved=root.querySelector('[name=approved]').checked; const issues=[...root.querySelectorAll('[name=issue]:checked')].map(x=>x.value); const res=await fetch(`/api/generations/${id}/feedback`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({rating,note,issues,approved_for_learning:approved})}); const data=await res.json(); if(!res.ok) throw new Error(data.detail||'Feedback konnte nicht gespeichert werden'); root.querySelector('.feedbackStatus').textContent=data.approved_for_learning?'Gespeichert und fuer Lernen freigegeben.':'Bewertung gespeichert.'; refreshStatus(); }
async function repairGeneration(id,btn,title){ const old=btn.textContent; btn.disabled=true; btn.textContent='Repariere ...'; try{ const res=await fetch(`/api/generations/${id}/repair`,{method:'POST'}); const data=await res.json(); if(!res.ok) throw new Error(data.detail||'Reparatur fehlgeschlagen'); setViewer(id,title,'repaired','done'); await refreshGenerations(); }catch(e){ alert(`Blender-Reparatur: ${e.message}`); }finally{ btn.disabled=false; btn.textContent=old; } }
function feedbackHtml(){ return `<div class="feedback"><div class="feedbackTop"><select name="rating"><option value="5">5 - perfekt</option><option value="4">4 - gut</option><option value="3">3 - mittel</option><option value="2">2 - schlecht</option><option value="1">1 - unbrauchbar</option></select><label class="learnCheck"><input type="checkbox" name="approved"> Fuer Lernen freigeben</label></div><input name="note" placeholder="Was soll 3DCreator beim naechsten Mal besser machen?"><div class="issues"><label><input type="checkbox" name="issue" value="silhouette"> Silhouette</label><label><input type="checkbox" name="issue" value="details"> Details</label><label><input type="checkbox" name="issue" value="backside"> Rueckseite</label><label><input type="checkbox" name="issue" value="thin_parts"> Zu duenn</label><label><input type="checkbox" name="issue" value="mesh_errors"> Meshfehler</label><label><input type="checkbox" name="issue" value="printability"> Druckbarkeit</label></div><button type="button" class="feedbackButton secondary">Bewertung speichern</button><span class="feedbackStatus"></span></div>`; }

async function refreshGenerations(){
  const items=await fetch('/api/generations').then(r=>r.json());
  generationsEl.innerHTML=items.length?'':'<div class="emptyList">Noch keine Generationen.</div>';
  for(const g of items){
    const div=document.createElement('div'); div.className='item';
    const views=(g.source_images||[]).map(v=>v.label||v.view).join(' · ')||'Front';
    const repairBadge=g.repair_status&&g.repair_status!=='none'?`<span class="badge repair-${g.repair_status}">Repair ${g.repair_status}</span>`:'';
    const modeBadge=`<span class="badge">${g.mode==='multiview'?'MultiView':'SingleView'}</span>`;
    const familyLabel=g.classification?.label||g.model_family||'Unklassifiziert';
    const familyBadge=`<span class="badge">${escapeHtml(familyLabel)}</span>`;
    const viewButtons=g.status==='done'?`<div class="itemActions"><button type="button" class="miniAction viewBest">Im Viewer</button><a class="miniAction" href="/api/generations/${g.id}/file?variant=raw">Raw</a>${g.has_repaired?`<a class="miniAction" href="/api/generations/${g.id}/file?variant=repaired">Repariert</a>`:''}<button type="button" class="miniAction repairNow">${g.has_repaired?'Neu reparieren':'Reparieren'}</button></div>`:'';
    div.innerHTML=`<div class="itemTitle"><div><strong>${escapeHtml(g.project_name||'Unbenannt')}</strong><span class="${g.status}">${g.status}</span></div><div>${familyBadge}${modeBadge}${repairBadge}</div></div><div class="meta">${g.quality}px · ${views} · ${formatDate(g.created_at)}</div>${g.prompt?`<div class="prompt">${escapeHtml(g.prompt)}</div>`:''}${g.error?`<div class="error">${escapeHtml(g.error)}</div>`:''}${viewButtons}${g.status==='done'?feedbackHtml():''}`;
    const viewBtn=div.querySelector('.viewBest'); if(viewBtn) viewBtn.addEventListener('click',()=>setViewer(g.id,g.project_name,'best',g.repair_status));
    const repairBtn=div.querySelector('.repairNow'); if(repairBtn) repairBtn.addEventListener('click',()=>repairGeneration(g.id,repairBtn,g.project_name));
    const fb=div.querySelector('.feedbackButton'); if(fb) fb.addEventListener('click',()=>saveFeedback(g.id,div.querySelector('.feedback')).catch(e=>alert(e.message)));
    generationsEl.appendChild(div);
  }
}
function escapeHtml(value=''){ return String(value).replace(/[&<>"']/g,ch=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#039;'}[ch])); }
function formatDate(value){ try{return new Date(value).toLocaleString('de-DE',{dateStyle:'short',timeStyle:'short'});}catch{return value||'';} }
setupWorkflowsButton.addEventListener('click',setupWorkflows);
form.addEventListener('change',e=>{ if(e.target.matches('input[name=mode],input[name=quality]')) updateMode(); if(e.target.matches('input[type=file]')) updateFileLabel(e.target); });
form.addEventListener('submit',async e=>{
  e.preventDefault();
  if(selectedMode()==='multiview'&&!multiInputs.some(input=>input.files?.length)){ message.textContent='MultiView braucht neben Front mindestens eine weitere Ansicht.'; return; }
  const projectTitle=form.elements.name.value; message.textContent='Generation wird gestartet. 3DCreator klassifiziert zuerst den Modelltyp und startet danach TRELLIS ...'; button.disabled=true;
  try{
    const response=await fetch('/api/generate',{method:'POST',body:new FormData(form)}); const data=await response.json(); if(!response.ok) throw new Error(data.detail||JSON.stringify(data));
    const repair=data.repair?(data.repair.ok?' · Blender-Reparatur fertig':' · Rohmodell fertig, Blender-Reparatur nicht verfuegbar'):'';
    const family=data.classification?.label?` · erkannt: ${data.classification.label}`:'';
    message.textContent=`Fertig${family} · ${data.views.join(', ')}${repair}`;
    setViewer(data.generation_id,projectTitle,'best',data.repair?.ok?'done':'');
    form.reset(); document.querySelectorAll('.viewSlot').forEach(slot=>{ slot.classList.remove('hasFile'); const n=slot.querySelector('.fileName'); if(n)n.textContent='Bild waehlen'; }); updateMode();
  }catch(err){ message.textContent=`Fehler: ${err.message}`; }
  finally{ button.disabled=false; await refreshGenerations(); await refreshStatus(); }
});
viewer.addEventListener('error',()=>{ viewerMeta.textContent='Diese Rohdatei kann der Browser nicht direkt anzeigen. Nutze Blender-Reparatur, um eine lokale GLB-Vorschau zu erzeugen.'; });
updateMode(); refreshStatus(); refreshGenerations();
