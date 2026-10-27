'use strict';
(() => {
const nav=document.querySelector('.area-nav'),main=document.querySelector('main');if(!nav||!main)return;
const ids=['cobertura','tiendas','asistencia','operacion','productividad','actualizacion'];
function arrange(){const sections=ids.map(id=>document.getElementById(id)).filter(Boolean),existing=[...main.children].filter(e=>ids.includes(e.id));if(existing.some((e,i)=>e!==sections[i])){const footer=main.querySelector('footer');for(const section of sections)main.insertBefore(section,footer);}for(const [id,label]of [['cobertura','RECLUTAMIENTO'],['asistencia','RH'],['productividad','ANÁLISIS']]){const section=document.getElementById(id);if(!section)continue;let divider=document.getElementById('area-'+id);if(!divider){divider=document.createElement('div');divider.id='area-'+id;divider.className='area-divider';divider.textContent=label;}if(divider.nextElementSibling!==section)section.before(divider);}}
function activate(link){for(const a of nav.querySelectorAll('a')){const active=a===link;a.classList.toggle('selected',active);if(active)a.setAttribute('aria-current','location');else a.removeAttribute('aria-current');}const area=link.closest('details');if(area)area.open=true;}
nav.addEventListener('click',event=>{const link=event.target.closest('a');if(link)activate(link);});
const observed=new WeakSet();const observer=new IntersectionObserver(entries=>{for(const entry of entries)if(entry.isIntersecting){const link=nav.querySelector('a[href="#'+entry.target.id+'"]');if(link)activate(link);}},{rootMargin:'-10% 0px -70% 0px'});
function sync(){arrange();for(const id of ids){const section=document.getElementById(id);if(section&&!observed.has(section)){observer.observe(section);observed.add(section);}}}
new MutationObserver(records=>{if(records.some(r=>[...r.addedNodes].some(n=>n.nodeType===1&&ids.includes(n.id))))sync();}).observe(main,{childList:true});sync();const initial=nav.querySelector('a[href="'+(ids.includes(location.hash.slice(1))?location.hash:'#cobertura')+'"]');if(initial)activate(initial);
})();
