/* script.js
   Simple demo: renders themes, opens modal, allows customization, computes estimate,
   and saves selection to localStorage (demo).
*/

const THEMES = [
  {id:1,name:'Wedding Decoration',price:25000,desc:'Elegant wedding stage with drapes, floral arches and romantic lighting.',items:['Stage','Flowers','Drapes','Lights']},
  {id:2,name:'Birthday Decoration',price:8000,desc:'Fun colorful birthday setup with balloons, backdrop and center pieces.',items:['Balloons','Backdrop','Table Décor']},
  {id:3,name:'Corporate Event Decoration',price:18000,desc:'Clean professional décor with branded backdrop, podium and subtle lighting.',items:['Backdrop','Podium','Branding']},
  {id:4,name:'Success Party',price:15000,desc:'A celebration of Achievement,decorate with a modern and energetic theme.',items:[' balloons, LED lights','a congratulations backdrop','photo booth props','photo booth props, table']},
  {id:5,name:'Anniversary Decoration',price:12000,desc:'Romantic and classy decoration for anniversaries with photo displays.',items:['Photo Frames','Flowers','Candles']},
  {id:6,name:'Engagement Decoration',price:20000,desc:'Lovely engagement setup with centerpiece and elegant lighting.',items:['Centerpiece','Floral Arch','Backdrop']}
];

const COLOR_THEMES = [
  {id:'gold',label:'Gold',cost:2000}, {id:'red',label:'Red',cost:1500}, {id:'white',label:'White',cost:1000}, {id:'pastel',label:'Pastel',cost:1200}
];

const STAGE_OPTS = [
  {id:'simple',label:'Simple Stage',cost:0},
  {id:'grand',label:'Grand Stage (arches & pillars)',cost:6000},
  {id:'floral',label:'Full Floral Stage',cost:8000}
];

const FLOWER_OPTS = [
  {id:'none',label:'None',cost:0},
  {id:'local',label:'Local Flowers',cost:1500},
  {id:'premium',label:'Premium Flowers',cost:4000}
];

const TABLE_OPTS = [
  {id:'basic',label:'Basic Chairs & Tables',cost:0},
  {id:'decor',label:'Decorated Tables',cost:2500},
  {id:'covered',label:'Chair Covers & Sashes',cost:1200}
];

const ENTRY_OPTS = [
  {id:'arch',label:'Welcome Arch',cost:1800},
  {id:'gate',label:'Decorative Gate',cost:3500},
  {id:'none',label:'No Entry Setup',cost:0}
];

const BACKDROP_OPTS = [
  {id:'fabric',label:'Fabric Backdrop',cost:0},
  {id:'led',label:'LED Backdrop',cost:7000},
  {id:'floral',label:'Floral Backdrop',cost:4500}
];

const BALLOON_OPTS = [
  {id:'balloons',label:'Balloons',cost:800},
  {id:'fabric',label:'Fabric Drapes',cost:1500},
  {id:'both',label:'Balloons + Drapes',cost:2000}
];

function makeThumb(title, accent){
  const svg = `data:image/svg+xml;utf8,${encodeURIComponent(`<svg xmlns='http://www.w3.org/2000/svg' width='800' height='400'><defs><linearGradient id='g' x1='0' x2='1'><stop offset='0' stop-color='${accent}'/><stop offset='1' stop-color='#e9d5ff'/></linearGradient></defs><rect width='100%' height='100%' fill='url(#g)' rx='12'/><text x='50%' y='50%' font-size='34' text-anchor='middle' fill='white' font-family='Arial' dy='.35em'>${title}</text></svg>`)} `;
  return svg;
}

/* --- Render themes --- */
const grid = document.getElementById('themesGrid');
THEMES.forEach(t => {
  const card = document.createElement('article'); card.className='card';
  const thumb = document.createElement('div'); thumb.className='thumb';
  const img = document.createElement('img'); img.alt = t.name; img.src = makeThumb(t.name, t.id%2? '#7c3aed':'#0ea5e9');
  thumb.appendChild(img);
  const meta = document.createElement('div'); meta.className='meta';
  const h3 = document.createElement('h3'); h3.textContent = t.name;
  const price = document.createElement('div'); price.className='price'; price.textContent = `₹${t.price.toLocaleString()}`;
  meta.appendChild(h3); meta.appendChild(price);
  const desc = document.createElement('div'); desc.className='desc'; desc.textContent = t.desc;
  const items = document.createElement('div'); items.className='items'; items.textContent = 'Items: ' + t.items.join(', ');
  const actions = document.createElement('div'); actions.className='actions';
  const selectBtn = document.createElement('button'); selectBtn.className='btn primary'; selectBtn.textContent='Select';
  selectBtn.addEventListener('click',()=> openModal(t));
  const viewBtn = document.createElement('button'); viewBtn.className='btn ghost'; viewBtn.textContent='View Details';
  viewBtn.addEventListener('click',()=> alert(`${t.name}\n\n${t.desc}\n\nIncluded: ${t.items.join(', ')}\nPrice: ₹${t.price}`));
  actions.appendChild(selectBtn); actions.appendChild(viewBtn);

  card.appendChild(thumb); card.appendChild(meta); card.appendChild(desc); card.appendChild(items); card.appendChild(actions);
  grid.appendChild(card);
});

/* --- Modal & controls --- */
const overlay = document.getElementById('overlay');
const modalThumb = document.getElementById('modalThumb');
const modalDesc = document.getElementById('modalDesc');
const modalTitle = document.getElementById('modalTitle');

const colorOptions = document.getElementById('colorOptions');
const stageOptions = document.getElementById('stageOptions');
const flowerOptions = document.getElementById('flowerOptions');
const tableOptions = document.getElementById('tableOptions');
const entryOptions = document.getElementById('entryOptions');
const backdropOptions = document.getElementById('backdropOptions');
const balloonOptions = document.getElementById('balloonOptions');
const lighting = document.getElementById('lighting');

const sumTheme = document.getElementById('sumTheme');
const sumBase = document.getElementById('sumBase');
const sumExtras = document.getElementById('sumExtras');
const sumTotal = document.getElementById('sumTotal');
const confirmBtn = document.getElementById('confirmBtn');
const resetBtn = document.getElementById('resetBtn');
const closeBtn = document.getElementById('closeBtn');
 const nextBtn = document.getElementById('nextBtn');

const confirmationMessage = document.getElementById('confirmationMessage');

let state = {
  themeId:null, color:'gold', lighting:'none', stage:'simple', flower:'none', table:'basic', entry:'none', backdrop:'fabric', balloon:'balloons'
};

function mkOptions(container, opts, defaultId){
  container.innerHTML = '';
  opts.forEach(o => {
    const el = document.createElement('button');
    el.className = 'chip';
    el.type = 'button';
    el.textContent = o.label + (o.cost ? ` (+₹${o.cost})` : '');
    el.dataset.id = o.id;
    el.dataset.cost = o.cost || 0;
    el.addEventListener('click', () => {
      container.querySelectorAll('.chip').forEach(c=>c.classList.remove('selected'));
      el.classList.add('selected');
      state[container.dataset.key] = o.id;
      renderSummary();
    });
    container.appendChild(el);
    if(defaultId && o.id === defaultId) el.classList.add('selected');
  });
}

colorOptions.dataset.key='color';
stageOptions.dataset.key='stage';
flowerOptions.dataset.key='flower';
tableOptions.dataset.key='table';
entryOptions.dataset.key='entry';
backdropOptions.dataset.key='backdrop';
balloonOptions.dataset.key='balloon';

mkOptions(colorOptions, COLOR_THEMES, state.color);
mkOptions(stageOptions, STAGE_OPTS, state.stage);
mkOptions(flowerOptions, FLOWER_OPTS, state.flower);
mkOptions(tableOptions, TABLE_OPTS, state.table);
mkOptions(entryOptions, ENTRY_OPTS, state.entry);
mkOptions(backdropOptions, BACKDROP_OPTS, state.backdrop);
mkOptions(balloonOptions, BALLOON_OPTS, state.balloon);

lighting.addEventListener('change', ()=> { state.lighting = lighting.value; renderSummary(); });

function findIn(arr, id){ return arr.find(x => x.id === id || x.id === String(id)); }

function openModal(theme){
  state.themeId = theme.id;
  modalTitle.textContent = `Customize — ${theme.name}`;
  modalDesc.textContent = theme.desc;
  modalThumb.innerHTML = `<img src="${makeThumb(theme.name, theme.id%2? '#7c3aed':'#0ea5e9')}" alt="${theme.name}">`;
  sumTheme.textContent = theme.name;
  sumBase.textContent = `₹${theme.price.toLocaleString()}`;
  // set defaults (ensure chips reflect state)
  // (chips already created with defaults)
  overlay.classList.add('show');
  overlay.setAttribute('aria-hidden','false');
  renderSummary();
}

/* Close handlers */
closeBtn.addEventListener('click', ()=> closeModal());
overlay.addEventListener('click', (e)=> { if(e.target === overlay) closeModal(); });
function closeModal(){
  overlay.classList.remove('show');
  overlay.setAttribute('aria-hidden','true');
  confirmationMessage.style.display = 'none';
}

/* Compute extras */
function computeExtras(){
  let extras = 0;
  const theme = THEMES.find(t=>t.id === state.themeId);
  if(!theme) return 0;
  // color
  const color = findIn(COLOR_THEMES, state.color); extras += color ? (color.cost||0) : 0;
  const stage = findIn(STAGE_OPTS, state.stage); extras += stage ? (stage.cost||0) : 0;
  const flower = findIn(FLOWER_OPTS, state.flower); extras += flower ? (flower.cost||0) : 0;
  const table = findIn(TABLE_OPTS, state.table); extras += table ? (table.cost||0) : 0;
  const entry = findIn(ENTRY_OPTS, state.entry); extras += entry ? (entry.cost||0) : 0;
  const backdrop = findIn(BACKDROP_OPTS, state.backdrop); extras += backdrop ? (backdrop.cost||0) : 0;
  const balloon = findIn(BALLOON_OPTS, state.balloon); extras += balloon ? (balloon.cost||0) : 0;
  // lighting select (read data-cost attr)
  const lightingOption = lighting.options[lighting.selectedIndex];
  const lightingCost = parseInt(lightingOption.dataset.cost || '0', 10);
  extras += lightingCost;
  return extras;
}

function renderSummary(){
  const theme = THEMES.find(t=>t.id === state.themeId);
  const base = theme ? theme.price : 0;
  const extras = computeExtras();
  sumBase.textContent = `₹${base.toLocaleString()}`;
  sumExtras.textContent = `₹${extras.toLocaleString()}`;
  sumTotal.textContent = `₹${(base + extras).toLocaleString()}`;
}

/* Confirm / Reset */
confirmBtn.addEventListener('click', ()=>{
  const theme = THEMES.find(t=>t.id === state.themeId);
  const selection = {
    themeId: state.themeId,
    color: state.color,
    lighting: state.lighting,
    stage: state.stage,
    flower: state.flower,
    table: state.table,
    entry: state.entry,
    backdrop: state.backdrop,
    balloon: state.balloon,
    estimatedTotal: sumTotal.textContent
  };

  // demo: save to localStorage
  const key = 'decoration_selection_demo';
  localStorage.setItem(key, JSON.stringify(selection));
  if (theme) {
    localStorage.setItem("decorationTheme", theme.name);
  }
  confirmationMessage.style.display = 'block';
});

nextBtn.addEventListener('click', () => {
  const totalText = sumTotal.textContent || "₹0";
  const totalNumber = Number(totalText.replace(/[^\d]/g, "")) || 0;
  localStorage.setItem("decorationPrice", String(totalNumber));
  window.location.href = "/booking";
});

resetBtn.addEventListener('click', ()=>{
  // reset to defaults
  state = { themeId: state.themeId, color:'gold', lighting:'none', stage:'simple', flower:'none', table:'basic', entry:'none', backdrop:'fabric', balloon:'balloons' };
  // restore chip visuals
  mkOptions(colorOptions, COLOR_THEMES, state.color);
  mkOptions(stageOptions, STAGE_OPTS, state.stage);
  mkOptions(flowerOptions, FLOWER_OPTS, state.flower);
  mkOptions(tableOptions, TABLE_OPTS, state.table);
  mkOptions(entryOptions, ENTRY_OPTS, state.entry);
  mkOptions(backdropOptions, BACKDROP_OPTS, state.backdrop);
  mkOptions(balloonOptions, BALLOON_OPTS, state.balloon);
  lighting.value = 'none';
  renderSummary();
});

/* initial (no modal shown) */
renderSummary();
