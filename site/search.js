/* Section search. Needs SEARCH_BASE ("" or "../") and SEARCH_SCOPE (subject slug, or "" for all). */
(function(){
  var data=null,waiting=null,q=document.getElementById('q'),out=document.getElementById('results');
  if(!q)return;
  function load(cb){if(data){cb();return}if(waiting){waiting.push(cb);return}waiting=[cb];
    fetch(SEARCH_BASE+'search.json').then(function(r){if(!r.ok)throw r.status;return r.json()}).then(function(all){
      data=all.filter(function(d){return !SEARCH_SCOPE||d.s===SEARCH_SCOPE});
      data.forEach(function(d){d.tl=d.t.toLowerCase();d.xl=d.x.toLowerCase();});
      var w=waiting;waiting=null;w.forEach(function(f){f()});
    }).catch(function(){waiting=null;out.style.display='block';out.innerHTML='<li class="none">Search could not load. Check your connection and try again.</li>'});}
  var box=q.closest('.search')||q.parentNode,revealed=false;
  /* phones: the on-screen keyboard hides results below the box, so bring the box to the top once per focus */
  function reveal(){if(revealed)return;var vv=window.visualViewport,h=vv?vv.height:innerHeight,off=vv?vv.offsetTop:0;
    if(out.getBoundingClientRect().top-off+80<=h)return;revealed=true;
    var t=document.querySelector('.theme-toggle'),gap=t?t.getBoundingClientRect().bottom+8:8;
    window.scrollBy({top:box.getBoundingClientRect().top-off-gap,behavior:'smooth'})}
  function esc(s){return s.replace(/[&<>"]/g,function(c){return{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]})}
  function hl(s,words){var h=esc(s);words.forEach(function(w){if(w.length<2)return;h=h.replace(new RegExp('('+w.replace(/[.*+?^${}()|[\]\\]/g,'\\$&')+')','ig'),'<mark>$1</mark>')});return h}
  function snippet(d,words){var i=-1;for(var k=0;k<words.length&&i<0;k++)i=d.xl.indexOf(words[k]);
    if(i<0)return d.x.slice(0,140)+'…';var s=Math.max(0,i-60);return (s?'…':'')+d.x.slice(s,s+170)+'…'}
  function run(){var v=q.value.trim().toLowerCase();out.innerHTML='';
    if(v.length<2){out.style.display='none';box.classList.remove('has-results');return}
    if(!data){load(run);return}
    var words=v.split(/\s+/).filter(Boolean),res=[];
    data.forEach(function(d){var sc=0,ok=true;words.forEach(function(w){var inT=d.tl.indexOf(w)>=0,inX=d.xl.indexOf(w)>=0;
      if(!inT&&!inX)ok=false;sc+=(inT?10:0)+(inX?1:0)});
      if(ok){if(d.tl.indexOf(v)>=0)sc+=20;if(!/^\d/.test(d.g))sc-=15;res.push([sc,d])}});
    res.sort(function(a,b){return b[0]-a[0]});
    out.style.display='block';box.classList.add('has-results');reveal();
    if(!res.length){out.innerHTML='<li class="none">No section matches “'+esc(v)+'”.</li>';return}
    res.slice(0,12).forEach(function(p){var d=p[1],li=document.createElement('li');
      li.innerHTML='<a href="'+SEARCH_BASE+d.u+'"><div>'+(SEARCH_SCOPE?'':'<span class="rc">'+esc(d.c)+'</span>')+
        '<span class="ru">'+(d.n?'U'+esc(d.n)+(d.g?' · ':''):'')+esc(d.g||'')+'</span><span class="rt">'+hl(d.t,words)+'</span></div><div class="rs">'+hl(snippet(d,words),words)+'</div></a>';
      out.appendChild(li)});
  }
  q.addEventListener('focus',function(){revealed=false;load(function(){})});
  q.addEventListener('input',run);
  q.addEventListener('keydown',function(e){if(e.key==='Enter'){var a=out.querySelector('a');if(a)a.click()}
    if(e.key==='ArrowDown'){var a=out.querySelector('a');if(a){a.focus();e.preventDefault()}}});
  out.addEventListener('keydown',function(e){var a=document.activeElement;if(!a||a.tagName!=='A')return;var li=a.parentNode;
    if(e.key==='ArrowDown'&&li.nextSibling){li.nextSibling.querySelector('a').focus();e.preventDefault()}
    if(e.key==='ArrowUp'){if(li.previousSibling)li.previousSibling.querySelector('a').focus();else q.focus();e.preventDefault()}});
})();
