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
  activeChip: null,      // index of the expanded chip detail box in the edit panel
  secondaryTab: 'history', // 'history' | 'shared' -- tab under the editor
  historyOpen: false,
};

function selectClass(id){ state.classId = id; state.catId = null; state.analysisPanel = null; render(); }
function selectCat(id){ state.catId = id; state.analysisPanel = null; state.activeChip = null; state.secondaryTab = 'history'; state.historyOpen = false; render(); }
function toggleChip(i){ state.activeChip = (state.activeChip===i) ? null : i; render(); }
function setSecondaryTab(tab){ state.secondaryTab = tab; render(); }
function toggleHistory(){ state.historyOpen = !state.historyOpen; render(); }

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
   pipeline's real (algorithmically generated, not hand-forced) scores.
   Generalized to take any catId so the same check can also power the
   inline pointer inside the edit panel, not just the fixed top banner. ============ */
const INSTRUCTION_ALERT = { catId: 'review', threshold: 60 };
function computeAlertForCategory(catId, threshold){
  threshold = threshold===undefined ? INSTRUCTION_ALERT.threshold : threshold;
  const rows = MANAGERS.map(m=>{
    const acc = m.criteria.accuracy;
    const catData = (acc.byCategory||{})[catId];
    if(!catData || catData.n < MIN_SAMPLE) return null;
    return {mgr: m, score: catData.pct};
  }).filter(r => r && r.score !== null && r.score < threshold);
  return rows.length >= 2 ? rows : null;
}
function computeAlert(){ return computeAlertForCategory(INSTRUCTION_ALERT.catId, INSTRUCTION_ALERT.threshold); }

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

/* ============ small text/diff helpers, ported from the original mockup ============ */
function escapeHtml(s){ return (s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;'); }
function diffWords(oldStr, newStr){
  const a = (oldStr||'').split(/(\s+)/), b = (newStr||'').split(/(\s+)/);
  const n=a.length, m=b.length;
  const dp = Array.from({length:n+1},()=>new Array(m+1).fill(0));
  for(let i=n-1;i>=0;i--) for(let j=m-1;j>=0;j--)
    dp[i][j] = a[i]===b[j] ? dp[i+1][j+1]+1 : Math.max(dp[i+1][j], dp[i][j+1]);
  let i=0,j=0,html='';
  while(i<n && j<m){
    if(a[i]===b[j]){ html+=escapeHtml(a[i]); i++; j++; }
    else if(dp[i+1][j] >= dp[i][j+1]){ html+=`<del>${escapeHtml(a[i])}</del>`; i++; }
    else { html+=`<ins>${escapeHtml(b[j])}</ins>`; j++; }
  }
  while(i<n){ html+=`<del>${escapeHtml(a[i])}</del>`; i++; }
  while(j<m){ html+=`<ins>${escapeHtml(b[j])}</ins>`; j++; }
  return html;
}
// A real, if narrow, auto-scan: flags unresolved template placeholders
// ({{Order Number}} etc, exactly the tokens visible in the real ticket
// examples this demo shows in 4.1) or a specific-looking ticket/order
// number (#12345) left in the *published* instruction text -- both are
// signs a specific customer's case leaked into what is supposed to be a
// generalized instruction. It cannot detect every way text could be
// under-generalized (no scan can); it only catches these two concrete,
// checkable patterns, and says so in the UI rather than implying more.
function autoScanClean(text){ return !/\{\{[^}]+\}\}|#\d{3,}/.test(text||''); }

/* ============ instruction text editing --------------------------------
   The pipeline's CLASSES export is the published, source-of-truth text.
   EDITS overlays that per-category with an in-session draft/publish
   state, plus the review flags (generalized / law verdicts) that publishing
   invalidates -- mirroring the original mockup's draft -> publish flow.
   Labeled honestly: this demo has no backend, so "publish" here only ever
   writes into this browser tab's memory, never back to the export CSV or
   the pipeline. Refreshing the page reverts everything. SESSION_HISTORY
   is the in-session append-only log publish() writes to, shown alongside
   each category's real (pre-demo) history entry. ============ */
const EDITS = {}; // catId -> {published, draft, generalizationConfirmed, legalVerdicts}
const SESSION_HISTORY = {}; // catId -> [{who, when, note, snapshotText}], newest first
function publishedText(cat){ const e = EDITS[cat.id]; return (e && e.published !== null && e.published !== undefined) ? e.published : cat.text; }
function draftText(cat){ const e = EDITS[cat.id]; return (e && e.draft !== null && e.draft !== undefined) ? e.draft : publishedText(cat); }
function isDraftPending(cat){ const e = EDITS[cat.id]; return !!(e && e.draft !== null && e.draft !== undefined && e.draft !== publishedText(cat)); }
function ensureEdit(catId){ if(!EDITS[catId]) EDITS[catId] = {published:null, draft:null, generalizationConfirmed:null, legalVerdicts:null}; return EDITS[catId]; }
function currentGeneralizationConfirmed(cat){ const e = EDITS[cat.id]; return (e && e.generalizationConfirmed !== null && e.generalizationConfirmed !== undefined) ? e.generalizationConfirmed : cat.generalizationConfirmed; }
function currentLegalStatements(cat){ const e = EDITS[cat.id]; return (e && e.legalVerdicts) ? e.legalVerdicts : cat.legalStatements; }
function legalStatusFor(cat){
  const arr = currentLegalStatements(cat);
  if(!arr || !arr.length) return 'unknown';
  if(arr.some(s=>s.verdict==='disputed')) return 'bad';
  if(arr.some(s=>s.verdict==='unverified')) return 'warning';
  return 'ok'; // 'confirmed' or 'internal' (no external law to verify against)
}
function sharedBlockFor(cat){ return cat.sharedBlockId ? SHARED_BLOCKS[cat.sharedBlockId] : null; }
function historyFor(cat){ return (SESSION_HISTORY[cat.id]||[]).concat(cat.history||[]); }

function onInstructionInput(catId){
  const cat = findCat(catId);
  const ta = document.getElementById('editTextarea-'+catId);
  if(!ta) return;
  const dirty = ta.value !== draftText(cat);
  const shell = document.getElementById('editorShell-'+catId);
  if(shell) shell.classList.toggle('dirty', dirty);
  const status = document.getElementById('saveStatus-'+catId);
  if(status){ status.textContent = dirty ? 'Unsaved changes' : 'No unsaved changes'; status.classList.remove('ok'); }
}
function saveInstructionDraft(catId){
  const ta = document.getElementById('editTextarea-'+catId);
  if(!ta) return;
  ensureEdit(catId).draft = ta.value;
  render();
  const status = document.getElementById('saveStatus-'+catId);
  if(status){ status.textContent = 'Saved as draft for this session (demo only -- not written back to the pipeline export)'; status.classList.add('ok'); }
}
// Publishing does three things, same as the original mockup: (1) writes the
// new published text, (2) drops the pending draft, (3) invalidates review
// state that no longer necessarily applies to the new wording -- law
// verdicts on externally-sourced categories go back to "unverified" and the
// generalized flag is un-set, both requiring a human (or the auto-scan) to
// clear them again, instead of silently carrying old approvals over to
// text nobody has actually re-checked.
function publishInstructionText(catId){
  const ta = document.getElementById('editTextarea-'+catId);
  if(!ta) return;
  const cat = findCat(catId);
  const oldText = publishedText(cat);
  const newText = ta.value;
  const e = ensureEdit(catId);
  e.published = newText;
  e.draft = null;
  if(newText !== oldText){
    e.generalizationConfirmed = false;
    if(cat.sourceType === 'external'){
      e.legalVerdicts = currentLegalStatements(cat).map(s => ({
        statement: s.statement,
        verdict: 'unverified',
        note: 'Needs re-check -- the instruction text changed since this citation was last confirmed.',
      }));
    }
    if(!SESSION_HISTORY[catId]) SESSION_HISTORY[catId] = [];
    SESSION_HISTORY[catId].unshift({
      who: 'You (this session)', when: 'just now',
      note: 'Published a new version.',
      snapshotText: oldText,
    });
  }
  state.historyOpen = true;
  render();
  const status = document.getElementById('saveStatus-'+catId);
  if(status){ status.textContent = 'Published for this session (demo only -- not written back to the pipeline export)'; status.classList.add('ok'); }
}
function discardInstructionDraft(catId){
  const e = ensureEdit(catId);
  e.draft = null;
  render();
}
function restoreVersion(catId, historyIdx){
  const cat = findCat(catId);
  const entry = historyFor(cat)[historyIdx];
  if(!entry || !entry.snapshotText) return;
  const current = publishedText(cat);
  const e = ensureEdit(catId);
  e.published = entry.snapshotText;
  e.draft = null;
  if(!SESSION_HISTORY[catId]) SESSION_HISTORY[catId] = [];
  SESSION_HISTORY[catId].unshift({
    who: 'You (this session)', when: 'just now',
    note: `Restored an earlier version (from ${entry.when}).`,
    snapshotText: current,
  });
  state.historyOpen = true;
  render();
}
function confirmGeneralization(catId){ ensureEdit(catId).generalizationConfirmed = true; render(); }
function confirmLegalStatement(catId, idx){
  const cat = findCat(catId);
  const arr = currentLegalStatements(cat).map((s,i)=> i===idx ? {
    statement: s.statement, verdict: 'confirmed',
    note: (s.note ? s.note + ' ' : '') + 'Confirmed manually, this session.',
  } : s);
  ensureEdit(catId).legalVerdicts = arr;
  render();
}
function saveSharedBlock(blockId, btn){
  const wrap = btn.closest('.shared-block-panel');
  const ta = wrap.querySelector('textarea.editor-textarea');
  SHARED_BLOCKS[blockId].text = ta.value;
  const status = wrap.querySelector('.save-status');
  if(status){ status.textContent = 'Updated for this session -- every category using this shared block now shows the new text.'; status.classList.add('ok'); }
}

/* Same alert mechanics as the top banner (computeAlertForCategory), but
   surfaced right next to the instruction text for whichever category is
   currently open -- so you see it exactly where you'd act on it, not just
   in a global banner for one hardcoded category. */
function managerPatternPointerHtml(cat){
  const alert = computeAlertForCategory(cat.id, INSTRUCTION_ALERT.threshold);
  if(!alert) return '';
  const names = alert.map(r=>`${r.mgr.name} (${r.score}%)`).join(', ');
  return `<div class="alert dup compact" onclick="openAnalysisManagerForCategory('${cat.id}')">
    \ud83d\udc65 ${alert.length} agents independently scored under ${INSTRUCTION_ALERT.threshold}% here (${names}) -- possibly the instruction, not the people. Details in 4.2 \u2192
  </div>`;
}
// Word-overlap divergence pointer: only fires below 80% match. Every
// category in this rebuild currently sits at match:100 (the pipeline's
// AI-drafted answer and the confirmed reference answer are identical), so
// in today's data this pointer stays dormant -- it will light up the
// moment a category's AI-suggested draft and reference answer actually
// diverge, same trigger condition as in the original mockup.
function divergencePointerHtml(cat){
  if(cat.match===null || cat.match===undefined || cat.match>=80) return '';
  return `<div class="alert div compact" onclick="openAnalysisAI()">
    \ud83d\udd00 Divergence detected (${cat.match}% match) -- details in 4.1 \u2192
  </div>`;
}

function editPanelHtml(){
  const cat = findCat(state.catId);
  if(!cat) return `<div class="edit-panel"><div style="color:var(--text3); font-size:13px;">Select an instruction from the list to view and edit it.</div></div>`;
  const badgeClass = cat.sourceType === 'external' ? 'external' : 'internal';
  const badgeLabel = cat.sourceType === 'external' ? 'External regulation' : 'Internal policy';
  const current = draftText(cat);
  const isDraft = isDraftPending(cat);
  const statusPill = isDraft
    ? `<span class="status-pill draft">\ud83d\udfe1 Draft</span>`
    : `<span class="status-pill pub">\ud83d\udfe2 Published</span>`;
  const draftBanner = isDraft ? `<div class="draft-banner">
      <span>Draft differs from the published text (this session only)</span>
      <span class="btns">
        <button class="btn sm" onclick="publishInstructionText('${cat.id}')">Publish</button>
        <button class="btn ghost sm" onclick="discardInstructionDraft('${cat.id}')">Discard draft</button>
      </span>
    </div>` : '';

  // ---- chip row: Generalized / Law / Reference answer, each backed by real state ----
  const clean = autoScanClean(publishedText(cat));
  const genConfirmed = currentGeneralizationConfirmed(cat);
  const genState = !clean ? 'warn' : genConfirmed ? 'ok' : 'unk';
  const genIcon = !clean ? '\u26a0\ufe0f' : genConfirmed ? '\u2705' : '\u2754';
  const genDetail = !clean
    ? `Auto-scan found a template placeholder (<code>{{...}}</code>) or a specific-looking ticket/order number in the published text -- that looks like a detail from one real case, not a generalized instruction. Fix the text before this can be marked generalized.`
    : genConfirmed
      ? `Confirmed manually -- reviewed and marked as properly generalized.`
      : `Auto-scan found no leaked placeholders or ticket numbers, but a human still needs to confirm the wording overall.<br><button class="btn sm secondary" style="margin-top:6px;" onclick="confirmGeneralization('${cat.id}')">Mark as generalized</button>`;

  const ls = legalStatusFor(cat);
  const legalArr = currentLegalStatements(cat) || [];
  const legalIcon = ls==='ok' ? '\u2705' : ls==='warning' ? '\u26a0\ufe0f' : ls==='bad' ? '\u26a0\ufe0f' : '\u2754';
  const legalDetail = legalArr.length ? legalArr.map((s,i)=>{
    const verdictClass = s.verdict==='disputed' ? 'neverno' : s.verdict==='unverified' ? 'somnitelno' : 'verno';
    return `<div class="legal-mini">
      <span class="verdict ${verdictClass}">${s.verdict.toUpperCase()}</span>
      <span class="txt">${s.statement}${s.note?`<div class="legal-note" style="margin:4px 0 0; padding:0; background:none;">${s.note}</div>`:''}</span>
      ${s.verdict!=='confirmed' && s.verdict!=='internal' ? `<button class="btn sm secondary" onclick="confirmLegalStatement('${cat.id}', ${i})">Confirm</button>` : ''}
    </div>`;
  }).join('') : `<div class="empty-note">No law statement recorded for this category.</div>`;

  const etalonOk = etalonConfirmed(cat.id);
  const chips = [
    {state: genState, icon: genIcon, label: 'Generalized', detail: genDetail},
    {state: ls==='ok' ? 'ok' : ls==='unknown' ? 'unk' : 'warn', icon: legalIcon, label: 'Law', detail: legalDetail},
    {state: etalonOk ? 'ok' : 'unk', icon: etalonOk ? '\u2705' : '\u2754',
     label: 'Reference answer',
     detail: etalonOk
       ? `Confirmed as the reference answer for this category -- see the comparison grid in 4.1 AI Analysis.`
       : `Not currently confirmed. <button class="btn sm secondary" style="margin-top:6px;" onclick="toggleEtalon('${cat.id}')">Confirm as reference answer</button>`},
  ];
  const chipRow = `<div class="chip-row">
    ${chips.map((c,i)=>`<span class="chip ${c.state} ${state.activeChip===i?'active':''}" onclick="toggleChip(${i})">${c.icon} ${c.label}</span>`).join('')}
    <span class="source-badge ${badgeClass}">${badgeLabel}</span>
  </div>`;
  const chipDetail = state.activeChip!==null ? `<div class="chip-detail-box">${chips[state.activeChip].detail}</div>` : '';

  // ---- secondary tabs: History / Shared block ----
  const shared = sharedBlockFor(cat);
  const history = historyFor(cat);
  const tabsHtml = `<div class="sec-tabs">
    <button class="sec-tab ${state.secondaryTab==='history'?'active':''}" onclick="setSecondaryTab('history')">History (${history.length})</button>
    ${shared ? `<button class="sec-tab ${state.secondaryTab==='shared'?'active':''}" onclick="setSecondaryTab('shared')">\ud83d\udd17 Shared block</button>` : ''}
  </div>`;
  let secPanel = '';
  if(state.secondaryTab==='history' || !shared){
    secPanel = history.map((h,idx)=>`<div class="history-row">
      <div class="hr-text">
        <b>${h.who}</b> \u00b7 ${h.when}<br>${h.note}
        ${h.snapshotText ? `<details class="hist-diff"><summary>Show what changed from this version to now</summary><div class="diff-box">${diffWords(h.snapshotText, publishedText(cat))}</div></details>` : ''}
      </div>
      ${h.snapshotText ? `<span class="restore-link" onclick="restoreVersion('${cat.id}', ${idx})">Restore</span>` : ''}
    </div>`).join('');
  } else if(state.secondaryTab==='shared' && shared){
    const otherIds = shared.usedIn.filter(id=>id!==cat.id);
    const parts = otherIds.map(id=>{
      const other = findCat(id);
      return other ? `<a onclick="selectClass('${other.classId}'); setTimeout(()=>selectCat('${other.id}'),0);">${other.name}</a>` : id;
    });
    secPanel = `<div class="shared-block-panel">
      <div class="editor-shell">
        <div class="editor-toolbar"><span>Shared block text</span><span class="editor-hint">Editing this updates every category listed below</span></div>
        <textarea class="editor-textarea" style="min-height:100px;">${shared.text}</textarea>
      </div>
      <div class="save-row"><button class="btn sm secondary" onclick="saveSharedBlock('${cat.sharedBlockId}', this)">Save shared block</button><span class="save-status"></span></div>
      <div class="used-in">Also used in: ${parts.join(', ') || '\u2014'}. Editing here updates the text everywhere it's referenced, immediately.</div>
    </div>`;
  }

  return `<div class="edit-panel">
    <div class="edit-title-row">
      <div class="edit-title">${cat.name}</div>
      ${statusPill}
    </div>
    <div class="edit-traffic">${cat.traffic} tickets in this category</div>
    ${chipRow}
    ${chipDetail}
    ${divergencePointerHtml(cat)}
    ${managerPatternPointerHtml(cat)}
    <div class="editor-shell" id="editorShell-${cat.id}">
      <div class="editor-toolbar">
        <span>Instruction text</span>
        <span class="editor-hint">Editable in this demo -- saves in this browser tab only, not to the pipeline export</span>
      </div>
      <textarea class="editor-textarea" id="editTextarea-${cat.id}" oninput="onInstructionInput('${cat.id}')">${current}</textarea>
    </div>
    <div class="save-row">
      <button class="btn sm" onclick="saveInstructionDraft('${cat.id}')">Save draft</button>
      <button class="btn secondary sm" onclick="publishInstructionText('${cat.id}')">Publish</button>
      <span class="save-status" id="saveStatus-${cat.id}">No unsaved changes</span>
    </div>
    ${draftBanner}
    <div class="entry-btns" style="margin-bottom:16px;">
      <button class="entry-btn" onclick="openAnalysisAI()">4.1 AI Analysis \u2194<span class="sub2">Law vs. reference-answer divergence</span></button>
      <button class="entry-btn" onclick="openAnalysisManagerForCategory('${cat.id}')">4.2 Agent Analysis \u2194<span class="sub2">Same panel as the scorecard demo</span></button>
      <button class="entry-btn" onclick="openTickets('${cat.id}')">\ud83d\udccb Tickets (${cat.traffic}) \u2194<span class="sub2">Real example tickets</span></button>
    </div>
    ${tabsHtml}
    <div class="sec-panel">${secPanel}</div>
  </div>`;
}

const ETALON_STATUS = {}; // catId -> 'confirmed' | 'unconfirmed'; absent = confirmed (this dataset ships with a curated etalon per category)
function etalonConfirmed(catId){ return ETALON_STATUS[catId] !== 'unconfirmed'; }
function toggleEtalon(catId){ ETALON_STATUS[catId] = etalonConfirmed(catId) ? 'unconfirmed' : 'confirmed'; render(); }

function aiAnalysisPanelHtml(){
  const cat = findCat(state.catId);
  const badgeClass = cat.sourceType === 'external' ? 'external' : 'internal';
  const badgeLabel = cat.sourceType === 'external' ? 'External regulation' : 'Internal policy';
  const legalArr = currentLegalStatements(cat) || [];
  const legalRows = legalArr.length ? legalArr.map((s,i)=>{
    const verdictClass = s.verdict==='disputed' ? 'neverno' : s.verdict==='unverified' ? 'somnitelno' : 'verno';
    return `<div class="legal-mini">
      <span class="verdict ${verdictClass}">${s.verdict.toUpperCase()}</span>
      <span class="txt">${s.statement}${s.note?`<div class="legal-note" style="margin:4px 0 0; padding:0; background:none;">${s.note}</div>`:''}</span>
      ${s.verdict!=='confirmed' && s.verdict!=='internal' ? `<button class="btn sm secondary" onclick="confirmLegalStatement('${cat.id}', ${i}); render();">Confirm</button>` : ''}
    </div>`;
  }).join('') : `<div class="empty-note">No law statement recorded for this category.</div>`;
  const confirmed = etalonConfirmed(cat.id);
  return `<div class="col grow standalone ai-panel" id="colAnalysis">
    <div class="ad-header">
      <div><div class="ad-title">4.1 AI Analysis</div><div class="ad-sub">${cat.name}</div></div>
      <button class="ad-close" onclick="closeAnalysis()">\u2715</button>
    </div>
    <div class="chip-row">
      <span class="source-badge ${badgeClass}">${badgeLabel}</span>
    </div>
    <div class="card">
      <div class="card-title">Law status</div>
      ${legalRows}
    </div>
    <div class="match-row">
      <div class="match-num ${cat.match>=80?'ok':cat.match>=55?'warn':'bad'}" style="color:${cat.match>=80?'var(--ok)':cat.match>=55?'var(--warn)':'var(--bad)'}">${cat.match}%</div>
      <div style="font-size:12.5px; color:var(--text2);">Divergence check: word-overlap between the AI-suggested draft and the confirmed reference answer. Not a legal judgment -- a text-similarity signal that flags when the two have drifted apart.</div>
    </div>
    <div class="compare-grid">
      <div class="compare-item q"><div class="label">Customer question (real, from source data)</div><div class="val">${cat.example.q}</div></div>
      <div class="compare-item"><div class="label">AI-suggested draft</div><div class="val">${cat.example.ai}</div></div>
      <div class="compare-item"><div class="label">Agent's actual reply (real, from source data)</div><div class="val">${cat.example.mgr}</div></div>
      <div class="compare-item etalon"><div class="label">Confirmed reference answer${confirmed ? '' : ' -- unconfirmed'}</div><div class="val">${cat.example.etalon}</div></div>
    </div>
    <div class="save-row" style="margin-top:-4px;">
      <button class="btn sm ${confirmed?'ghost':''}" onclick="toggleEtalon('${cat.id}')">${confirmed ? 'Unconfirm reference answer' : 'Confirm as reference answer'}</button>
      <span class="save-status">${confirmed ? 'Currently used as the reference answer for this category.' : 'Not currently confirmed -- the "Reference answer" chip on the edit panel will reflect this.'}</span>
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

  // Same mechanic as the original mockup: opening 4.1/4.2/Tickets hides
  // Classes + Instructions to make room, but keeps the edit panel on
  // screen -- the analysis panel opens NEXT TO it, not instead of it, so
  // the instruction text/chips you were just looking at don't disappear.
  // Two equal columns when an analysis panel is open, three sized columns
  // otherwise; nothing is ever left rendering into empty grid space.
  const analysisHtml = state.analysisPanel === 'ai' ? aiAnalysisPanelHtml()
    : state.analysisPanel === 'manager' ? managerAnalysisPanelHtml()
    : state.analysisPanel === 'tickets' ? ticketsPanelHtml()
    : '';

  html += `<div class="kb-cols ${state.analysisPanel ? 'collapsed' : ''}" id="kbCols">
    <div class="kb-col ${state.analysisPanel ? 'hide' : ''}">
      <div class="kb-col-head">Classes</div>
      ${classListHtml()}
    </div>
    <div class="kb-col ${state.analysisPanel ? 'hide' : ''}">
      <div class="kb-col-head">Instructions</div>
      ${instrListHtml()}
    </div>
    ${editPanelHtml()}
    ${analysisHtml}
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
