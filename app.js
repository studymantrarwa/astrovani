const $=(s)=>document.querySelector(s);
const esc=(v)=>String(v??'').replace(/[&<>"']/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#039;'}[m]));
const API=location.origin;
function toast(msg,type='ok'){let t=document.querySelector('.toast');if(!t){t=document.createElement('div');t.className='toast';document.body.appendChild(t)}t.textContent=msg;t.dataset.type=type;t.classList.add('show');setTimeout(()=>t.classList.remove('show'),2600)}
function setLoading(btn,on){if(!btn)return;btn.disabled=on;btn.dataset.old=btn.dataset.old||btn.textContent;btn.textContent=on?'Please wait…':btn.dataset.old}
async function api(path,opts={}){const r=await fetch(API+path,{headers:{'Content-Type':'application/json',...(opts.headers||{})},...opts});const d=await r.json().catch(()=>({success:false,error:'Invalid server response'}));if(!r.ok||d.success===false)throw new Error(d.error||'Request failed');return d}
function saveKundli(d){localStorage.setItem('astrovaniLastKundli',JSON.stringify(d))}
function loadKundli(){try{return JSON.parse(localStorage.getItem('astrovaniLastKundli')||'null')}catch{return null}}
function signHi(n){return ['मेष','वृषभ','मिथुन','कर्क','सिंह','कन्या','तुला','वृश्चिक','धनु','मकर','कुंभ','मीन'][n-1]||''}
window.Astrovani={api,toast,setLoading,saveKundli,loadKundli,esc,signHi};
