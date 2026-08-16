# -*- coding: utf-8 -*-
import re

reuse_css = open('/tmp/reuse_css.txt', encoding='utf-8').read()
reuse_css = reuse_css.replace('<style>', '').replace('</style>', '').strip()
extra_css = open('demo/content/extra_css.txt', encoding='utf-8').read()
classes_js = open('demo/gen/CLASSES_kb.js', encoding='utf-8').read()
managers_js = open('demo/gen/MANAGERS.js', encoding='utf-8').read()

JS_LOGIC = r"""
/* ============ scoring engine constants -- identical to manager-scorecard-demo.html ============ */
const CRITERIA_META = [
  {id:'accuracy',   label:'Accuracy & criticality',        canAutofail:true,  scoped:true},
  {id:'instruction', label:'Instruction compliance',        canAutofail:false, scoped:true},
  {id:'communication', label:'Communication',                canAutofail:false, scoped:false},
  {id:'speed',       label:'First response speed',           canAutofail:false, scoped:false},
  {id:'dataQuality', label:'Classification data quality',    canAutofail:false, scoped:false},
];
const CRITERIA_WEIGHTS = {accuracy:0.35, instruction:0.25, communication:0.20, speed:0.10, dataQuality:0.10};
const MIN_SAMPLE = 15;

function findManager(id){ return MANAGERS.find(m=>m.id===id); }
function scoreClass(pct){ if(pct===null) return 'muted'; if(pct>=80) return 'ok'; if(pct>=55) return 'warn'; return 'bad'; }
function managerAggregate(mgr, scope){
  const acc = mgr.criteria.accuracy;
  const autofail = (scope && scope.type==='category')
    ? !!(acc.autofailCategories && acc.autofailCategories.includes(scope.catId))
    : !!acc.autofail;
  if(autofail){ return {autofail:true, score:null}; }
  let sum=0, wsum=0;
  CRITERIA_META.forEach(c=>{
    const cr = mgr.criteria[c.id];
    const catData = (scope && scope.type==='category' && c.scoped) ? (cr.byCategory||{})[scope.catId] : null;
    const val = catData ? catData.pct : cr.pct;
    const n = catData ? catData.n : cr.n;
    if(val===null || val===undefined || n < MIN_SAMPLE) return;
    sum += val * CRITERIA_WEIGHTS[c.id];
    wsum += CRITERIA_WEIGHTS[c.id];
  });
  if(wsum===0) return {autofail:false, score:null};
  return {autofail:false, score: Math.round(sum/wsum)};
}
function managersForCategory(catId){
  return MANAGERS.filter(m => CRITERIA_META.some(c => (m.criteria[c.id].byCategory||{})[catId]));
}
function allCats(){ return CLASSES.flatMap(c => c.items.map(it => ({...it, classId:c.id, className:c.name}))); }
function findCat(id){ return allCats().find(c=>c.id===id); }
function findClass(id){ return CLASSES.find(c=>c.id===id); }

function dialogListHtml(dialogs){
  if(!dialogs || !dialogs.length) return `<div class="empty-note" style="margin-top:8px;">No conversation-level detail wired in for this tile yet -- the % and n above are already real, conversations get connected separately once there is something to point to.</div>`;
  return `<div class="mgr-dialog-list" style="margin-top:10px;">
    <div class="empty-note" style="margin-bottom:8px;">Real tickets for this category -- topic and metadata, no full conversation text. Illustrates volume, not the exact set the % was computed from.</div>
    ${dialogs.map((d,idx)=>{
    const open = state.mgrDialogIdx===idx;
    return `<div class="mgr-dialog-item ${open?'selected':''}" onclick="event.stopPropagation(); selectMgrDialog(${idx})">
      <div class="mdi-top"><span>${d.client}</span><span>${d.date}</span></div>
      <div class="mdi-excerpt">${d.excerpt}</div>
      ${open ? `<div style="padding:8px 0 0; border-top:1px dashed var(--border); margin-top:8px; display:flex; gap:6px; flex-wrap:wrap;">
        <span class="tag-mini muted-tag">responded in ${d.responseTime}</span>
        <span class="tag-mini muted-tag">quality: ${d.quality}</span>
        <span class="tag-mini muted-tag">tone: ${d.tone}</span>
      </div>` : ''}
    </div>`;
  }).join('')}</div>`;
}

function managerAnalysisPanelHtml(){
  const scope = state.mgrScope;
  const cat = scope.type==='category' ? findCat(scope.catId) : null;
  const candidates = scope.type==='category' ? managersForCategory(scope.catId) : MANAGERS;

  if(!candidates.length){
    return `<div class="col grow standalone" id="colAnalysis">
      <div class="ad-header">
        <div><div class="ad-title">4.2 Agent Analysis</div><div class="ad-sub">${cat?cat.name:''}</div></div>
        <button class="ad-close" onclick="closeAnalysis()">✕</button>
      </div>
      <div class="empty-note">No agent data for this category yet.</div>
    </div>`;
  }
  if(!state.mgrSelectedId) state.mgrSelectedId = candidates[0].id;
  const mgr = findManager(state.mgrSelectedId);
  const agg = managerAggregate(mgr, scope);

  const switchHtml = `<div class="mgr-switch">${candidates.map(m=>{
    const a = managerAggregate(m, scope);
    const lbl = a.autofail ? '\u26a0' : (a.score!==null ? a.score+'%' : '\u2014');
    return `<span class="mgr-pill ${m.id===mgr.id?'current':''}" onclick="selectMgrManager('${m.id}')">${m.name} <span class="agg">${lbl}</span></span>`;
  }).join('')}</div>`;

  const aggHtml = agg.autofail
    ? `<div class="mgr-agg bad"><div class="num">\u26a0</div><div class="lbl">Auto-fail on "Accuracy & criticality"${scope.type==='category'?` specifically in the "${cat.name}" category`:''} -- a critical error needs attention before the overall score</div></div>`
    : `<div class="mgr-agg ${scoreClass(agg.score)}"><div class="num">${agg.score!==null?agg.score+'%':'\u2014'}</div><div class="lbl">Weighted score across 5 criteria${agg.score===null?' -- insufficient data across all criteria':''}</div></div>`;

  const scopeNote = scope.type==='category'
    ? `<div class="mgr-scope-note">Showing agents and tickets for the "${cat.name}" category -- same panel that opens from the knowledge base editor.</div>`
    : '';

  const tilesHtml = CRITERIA_META.map((cm, idx)=>{
    const cr = mgr.criteria[cm.id];
    const catData = (scope.type==='category' && cm.scoped) ? (cr.byCategory||{})[scope.catId] : null;
    const pctToShow = catData ? catData.pct : (cr.n < MIN_SAMPLE ? null : cr.pct);
    const nToShow = catData ? catData.n : cr.n;
    const insufficient = nToShow < MIN_SAMPLE && !catData;
    const cls = insufficient ? 'muted' : scoreClass(pctToShow);
    const dialogs = catData ? catData.dialogs : [];
    const open = state.mgrCritIdx === idx;
    const tileAutofail = cm.canAutofail && cr.autofail && (scope.type!=='category' || (cr.autofailCategories||[]).includes(scope.catId));
    let noteText;
    if(insufficient){ noteText = `insufficient data (n=${nToShow}, threshold ${MIN_SAMPLE})`; }
    else if(!cm.scoped){ noteText = `n=${nToShow} -- behavioral criterion, overall figure`; }
    else if(catData){ noteText = `n=${nToShow} for the "${cat.name}" category`; }
    else { noteText = `n=${nToShow} across all categories -- no data specific to "${cat?cat.name:''}" yet`; }
    return `<div class="mgr-tile ${open?'selected':''}" onclick="selectMgrCrit(${idx})">
      <div class="mt-top">
        <span class="mt-label">${cm.label}${tileAutofail ? ' <span class="tag-mini" style="background:var(--bad-bg);color:var(--bad);">auto-fail</span>' : ''}</span>
        <span class="mt-pct ${cls}">${insufficient ? '\u2014' : (pctToShow!==null?pctToShow+'%':'\u2014')}</span>
      </div>
      <div class="mgr-bar"><div class="mgr-bar-fill ${cls==='muted'?'':cls}" style="width:${insufficient?0:(pctToShow||0)}%"></div></div>
      <div class="mt-n">${noteText}</div>
      ${open ? dialogListHtml(dialogs) : ''}
    </div>`;
  }).join('');

  return `<div class="col grow standalone" id="colAnalysis">
    <div class="ad-header">
      <div><div class="ad-title">4.2 Agent Analysis</div><div class="ad-sub">${cat?cat.name:'All categories'}</div></div>
      <button class="ad-close" onclick="closeAnalysis()">\u2715</button>
    </div>
    ${scopeNote}
    ${switchHtml}
    ${aggHtml}
    <div class="mgr-tiles">${tilesHtml}</div>
  </div>`;
}

/* ============ NEW: Section-3 state + navigation ============ */
let state = {
  classId: null, catId: null,
  analysisPanel: null,   // null | 'ai' | 'manager' | 'tickets'
  mgrScope: null, mgrSelectedId: null, mgrCritIdx: null, mgrDialogIdx: null,
  bellOpen: false,
};

function selectClass(id){ state.classId = id; state.catId = null; state.analysisPanel = null; render(); }
function selectCat(id){ state.catId = id; state.analysisPanel = null; render(); }

function openAnalysisAI(){ state.analysisPanel = 'ai'; render(); }
function openAnalysisManagerForCategory(catId){
  state.analysisPanel = 'manager';
  state.mgrScope = {type:'category', catId};
  state.mgrSelectedId = null; state.mgrCritIdx = null; state.mgrDialogIdx = null;
  render();
}
function openTickets(catId){ state.analysisPanel = 'tickets'; render(); }
function closeAnalysis(){ state.analysisPanel = null; render(); }
function selectMgrManager(id){ state.mgrSelectedId=id; state.mgrCritIdx=null; state.mgrDialogIdx=null; render(); }
function selectMgrCrit(idx){ state.mgrCritIdx = (state.mgrCritIdx===idx) ? null : idx; state.mgrDialogIdx=null; render(); }
function selectMgrDialog(idx){ state.mgrDialogIdx = (state.mgrDialogIdx===idx) ? null : idx; render(); }
function toggleBell(){ state.bellOpen = !state.bellOpen; render(); }

/* ============ alert: 2+ agents independently scored low on the same
   category -- points at the instruction, not the people. Built on the
   pipeline's real (algorithmically generated, not hand-forced) scores:
   "review" naturally has 2 agents both under 60% with solid n. ============ */
const INSTRUCTION_ALERT = { catId: 'review', threshold: 60 };
function computeAlert(){
  // Deliberately checks the "Accuracy & criticality" criterion directly,
  // not the full weighted managerAggregate() score -- the weighted score
  // mixes in Communication/Speed/Data quality, which run high enough for
  // most agents to mask a real accuracy problem in the average. The
  // alert is specifically about whether the instruction itself is
  // leading agents astray on THIS category, which is an accuracy
  // question, not a blended one.
  const rows = MANAGERS.map(m=>{
    const acc = m.criteria.accuracy;
    const catData = (acc.byCategory||{})[INSTRUCTION_ALERT.catId];
    if(!catData || catData.n < MIN_SAMPLE) return null;
    return {mgr: m, score: catData.pct};
  }).filter(r => r && r.score !== null && r.score < INSTRUCTION_ALERT.threshold);
  return rows.length >= 2 ? rows : null;
}

/* ============ Uncategorized digest (bell) -- real 47-ticket backlog,
   clustered into named themes, same pattern as the recurring-topic
   digest in the original v10. ============ */
const UNCATEGORIZED_DIGEST = [
  {theme: 'General "how do I reach support" (no specific ask)', count: 19},
  {theme: 'Wants to lodge a formal claim / reclamation', count: 11},
  {theme: 'Asks for a phone number to call', count: 3},
  {theme: 'Other / unclustered', count: 15},
];
const UNCATEGORIZED_TOTAL = 47;

function bellPanelHtml(){
  if(!state.bellOpen) return '';
  const rows = UNCATEGORIZED_DIGEST.map(d=>`
    <div class="digest-row"><span>${d.theme}</span><span class="digest-count">${d.count}</span></div>
  `).join('');
  return `<div class="bell-panel">
    <h4>Uncategorized backlog</h4>
    <div class="sub">${UNCATEGORIZED_TOTAL} tickets don't fit any of the 29 fixed categories. Clustered by recurring theme -- none forced into an existing category just to clear the backlog.</div>
    ${rows}
    <div class="digest-action">Action: either add a new fixed category for a cluster this size, or leave it uncategorized -- not automated, a deliberate call each time.</div>
  </div>`;
}

/* ============ Section 3 render ============ */
function classListHtml(){
  return CLASSES.map(c=>`
    <div class="kb-item ${c.id===state.classId?'active':''}" onclick="selectClass('${c.id}')">
      ${c.name}
      <div class="kb-item-meta">${c.items.length} instructions</div>
    </div>
  `).join('');
}
function instrListHtml(){
  const cls = findClass(state.classId);
  if(!cls) return `<div style="padding:20px; color:var(--text3); font-size:12.5px;">Select a class</div>`;
  return cls.items.map(it=>`
    <div class="kb-item ${it.id===state.catId?'active':''}" onclick="selectCat('${it.id}')">
      ${it.name}
      <div class="kb-item-meta">${it.traffic} tickets</div>
    </div>
  `).join('');
}

function editPanelHtml(){
  const cat = findCat(state.catId);
  if(!cat) return `<div class="edit-panel"><div style="color:var(--text3); font-size:13px;">Select an instruction from the list to view and edit it.</div></div>`;
  const badgeClass = cat.sourceType === 'external' ? 'external' : 'internal';
  const badgeLabel = cat.sourceType === 'external' ? 'External regulation' : 'Internal policy';
  return `<div class="edit-panel">
    <div class="edit-title">${cat.name}</div>
    <div class="edit-traffic">${cat.traffic} tickets in this category</div>
    <div class="chip-row">
      <span class="chip on">\u2713 Generalized</span>
      <span class="chip on">\u2713 Reference answer</span>
      <span class="source-badge ${badgeClass}">${badgeLabel}</span>
    </div>
    <div class="legal-note"><b>Law status:</b> ${cat.legalStatement}</div>
    <div class="edit-body">${cat.text}</div>
    <div class="entry-btns">
      <button class="entry-btn" onclick="openAnalysisAI()">4.1 AI Analysis \u2194<span class="sub2">Law vs. reference-answer divergence</span></button>
      <button class="entry-btn" onclick="openAnalysisManagerForCategory('${cat.id}')">4.2 Agent Analysis \u2194<span class="sub2">Same panel as the scorecard demo</span></button>
      <button class="entry-btn" onclick="openTickets('${cat.id}')">\ud83d\udccb Tickets (${cat.traffic}) \u2194<span class="sub2">Real example tickets</span></button>
    </div>
  </div>`;
}

function aiAnalysisPanelHtml(){
  const cat = findCat(state.catId);
  const badgeClass = cat.sourceType === 'external' ? 'external' : 'internal';
  const badgeLabel = cat.sourceType === 'external' ? 'External regulation' : 'Internal policy';
  return `<div class="col grow standalone ai-panel" id="colAnalysis">
    <div class="ad-header">
      <div><div class="ad-title">4.1 AI Analysis</div><div class="ad-sub">${cat.name}</div></div>
      <button class="ad-close" onclick="closeAnalysis()">\u2715</button>
    </div>
    <div class="chip-row">
      <span class="source-badge ${badgeClass}">${badgeLabel}</span>
    </div>
    <div class="legal-note">${cat.legalStatement}</div>
    <div class="match-row">
      <div class="match-num ${cat.match>=80?'ok':cat.match>=55?'warn':'bad'}" style="color:${cat.match>=80?'var(--ok)':cat.match>=55?'var(--warn)':'var(--bad)'}">${cat.match}%</div>
      <div style="font-size:12.5px; color:var(--text2);">Divergence check: word-overlap between the AI-suggested draft and the confirmed reference answer. Not a legal judgment -- a text-similarity signal that flags when the two have drifted apart.</div>
    </div>
    <div class="compare-grid">
      <div class="compare-item q"><div class="label">Customer question (real, from source data)</div><div class="val">${cat.example.q}</div></div>
      <div class="compare-item"><div class="label">AI-suggested draft</div><div class="val">${cat.example.ai}</div></div>
      <div class="compare-item"><div class="label">Agent's actual reply (real, from source data)</div><div class="val">${cat.example.mgr}</div></div>
      <div class="compare-item etalon"><div class="label">Confirmed reference answer</div><div class="val">${cat.example.etalon}</div></div>
    </div>
  </div>`;
}

function ticketsPanelHtml(){
  const cat = findCat(state.catId);
  const rows = TICKETS_BY_CATEGORY[cat.id] || [];
  if(!rows.length){
    return `<div class="col grow standalone" id="colAnalysis">
      <div class="ad-header">
        <div><div class="ad-title">\ud83d\udccb Tickets</div><div class="ad-sub">${cat.name}</div></div>
        <button class="ad-close" onclick="closeAnalysis()">\u2715</button>
      </div>
      <div class="empty-note">No example rows cached for this category in the demo bundle.</div>
    </div>`;
  }
  const trs = rows.map(r=>`
    <tr><td>${r.client}</td><td>${r.topic}</td><td>${r.agent}</td></tr>
  `).join('');
  return `<div class="col grow standalone" id="colAnalysis">
    <div class="ad-header">
      <div><div class="ad-title">\ud83d\udccb Tickets</div><div class="ad-sub">${cat.name} \u00b7 ${rows.length} of ${cat.traffic}</div></div>
      <button class="ad-close" onclick="closeAnalysis()">\u2715</button>
    </div>
    <table class="patent" style="width:100%; border-collapse:collapse; font-size:11.5px;">
      <thead><tr><th style="text-align:left; padding:6px 8px; border-bottom:1px solid var(--border);">Client</th><th style="text-align:left; padding:6px 8px; border-bottom:1px solid var(--border);">Topic</th><th style="text-align:left; padding:6px 8px; border-bottom:1px solid var(--border);">Agent</th></tr></thead>
      <tbody>${trs}</tbody>
    </table>
  </div>`;
}

function alertBannerHtml(){
  const alert = computeAlert();
  if(!alert) return '';
  const cat = findCat(INSTRUCTION_ALERT.catId);
  const names = alert.map(r=>`${r.mgr.name} (${r.score}%)`).join(', ');
  return `<div class="alert-banner" onclick="selectClass('${cat.classId}'); selectCat('${cat.id}'); openAnalysisManagerForCategory('${cat.id}');">
    \u26a0 <span><b>${alert.length} agents</b> independently scored under ${INSTRUCTION_ALERT.threshold}% on <b>${cat.name}</b> (${names}) -- possibly the instruction, not the people.</span>
    <span class="go">Investigate \u2192</span>
  </div>`;
}

function render(){
  let html = '';
  html += alertBannerHtml();

  const hasAnyCase = !!state.catId;
  html += `<div class="kb-cols ${state.analysisPanel ? 'collapsed' : ''}" id="kbCols">
    <div class="kb-col ${state.analysisPanel ? 'hide' : ''}">
      <div class="kb-col-head">Classes</div>
      ${classListHtml()}
    </div>
    <div class="kb-col ${state.analysisPanel ? 'hide' : ''}">
      <div class="kb-col-head">Instructions</div>
      ${instrListHtml()}
    </div>
    ${state.analysisPanel === 'ai' ? aiAnalysisPanelHtml()
      : state.analysisPanel === 'manager' ? managerAnalysisPanelHtml()
      : state.analysisPanel === 'tickets' ? ticketsPanelHtml()
      : editPanelHtml()}
  </div>`;

  document.getElementById('app').innerHTML = html;
  document.getElementById('bellSlot').innerHTML = bellPanelHtml();
  document.getElementById('bellBadge').textContent = UNCATEGORIZED_TOTAL;
}
render();
"""

html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>OrbitDesk Knowledge Base -- editor demo</title>
<style>
{reuse_css}
{extra_css}
</style>
</head>
<body>
<div class="app">
  <div class="topbar">
    <h1>\U0001F4DA OrbitDesk Knowledge Base</h1>
    <span class="sub">Classes \u2192 Instructions \u2192 Edit \u00b7 4.1 AI Analysis \u2194 4.2 Agent Analysis \u2194 Tickets, one slot at a time</span>
    <span class="demo-banner">Demo \u00b7 29 categories, sample data derived from the public Bitext dataset + hand-written knowledge base content</span>
    <div class="bell-wrap">
      <button class="bell-btn" onclick="toggleBell()">\U0001F514<span class="bell-badge" id="bellBadge"></span></button>
      <div id="bellSlot"></div>
    </div>
  </div>
  <div class="app-wrap" id="app"></div>
</div>

<script>
{classes_js}

{managers_js}

const TICKETS_BY_CATEGORY = {{}}; // populated below from real pipeline export
{open('demo/gen/TICKETS.js', encoding='utf-8').read()}
{JS_LOGIC}
</script>
</body>
</html>
"""

open('demo/knowledge-base-editor-demo.html', 'w', encoding='utf-8').write(html)
print("wrote demo/knowledge-base-editor-demo.html,", len(html.splitlines()), "lines")
