/* Ask AI menu. Loaded only the first time someone presses an "Ask AI" button
   (the guide itself carries just a tiny loader; see unit-chrome.html).
   No AI runs here: the prompt is a fixed template filled with the text of the
   section the student is reading, then handed to the chat site in the URL. */
(function () {
  var CTX = window.ASKAI_CTX || {};
  var MAX_TEXT = 2400;          // section text that goes into the link (links break if too long)
  var MAX_FULL = 12000;         // section text that goes into the copied prompt
  var ICON = {
    chatgpt: '<svg viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" d="M22.2819 9.8211a5.9847 5.9847 0 0 0-.5157-4.9108 6.0462 6.0462 0 0 0-6.5098-2.9A6.0651 6.0651 0 0 0 4.9807 4.1818a5.9847 5.9847 0 0 0-3.9977 2.9 6.0462 6.0462 0 0 0 .7427 7.0966 5.98 5.98 0 0 0 .511 4.9107 6.051 6.051 0 0 0 6.5146 2.9001A5.9847 5.9847 0 0 0 13.2599 24a6.0557 6.0557 0 0 0 5.7718-4.2058 5.9894 5.9894 0 0 0 3.9977-2.9001 6.0557 6.0557 0 0 0-.7475-7.0729zm-9.022 12.6081a4.4755 4.4755 0 0 1-2.8764-1.0408l.1419-.0804 4.7783-2.7582a.7948.7948 0 0 0 .3927-.6813v-6.7369l2.02 1.1686a.071.071 0 0 1 .038.052v5.5826a4.504 4.504 0 0 1-4.4945 4.4944zm-9.6607-4.1254a4.4708 4.4708 0 0 1-.5346-3.0137l.142.0852 4.783 2.7582a.7712.7712 0 0 0 .7806 0l5.8428-3.3685v2.3324a.0804.0804 0 0 1-.0332.0615L9.74 19.9502a4.4992 4.4992 0 0 1-6.1408-1.6464zM2.3408 7.8956a4.485 4.485 0 0 1 2.3655-1.9728V11.6a.7664.7664 0 0 0 .3879.6765l5.8144 3.3543-2.0201 1.1685a.0757.0757 0 0 1-.071 0l-4.8303-2.7865A4.504 4.504 0 0 1 2.3408 7.872zm16.5963 3.8558L13.1038 8.364 15.1192 7.2a.0757.0757 0 0 1 .071 0l4.8303 2.7913a4.4944 4.4944 0 0 1-.6765 8.1042v-5.6772a.79.79 0 0 0-.407-.667zm2.0107-3.0231l-.142-.0852-4.7735-2.7818a.7759.7759 0 0 0-.7854 0L9.409 9.2297V6.8974a.0662.0662 0 0 1 .0284-.0615l4.8303-2.7866a4.4992 4.4992 0 0 1 6.6802 4.66zM8.3065 12.863l-2.02-1.1638a.0804.0804 0 0 1-.038-.0567V6.0742a4.4992 4.4992 0 0 1 7.3757-3.4537l-.142.0805L8.704 5.459a.7948.7948 0 0 0-.3927.6813zm1.0976-2.3654l2.602-1.4998 2.6069 1.4998v2.9994l-2.5974 1.4997-2.6067-1.4997Z"/></svg>',
    claude: '<svg viewBox="0 0 24 24" aria-hidden="true"><path fill="#D97757" d="m4.7144 15.9555 4.7174-2.6471.079-.2307-.079-.1275h-.2307l-.7893-.0486-2.6956-.0729-2.3375-.0971-2.2646-.1214-.5707-.1215-.5343-.7042.0546-.3522.4797-.3218.686.0608 1.5179.1032 2.2767.1578 1.6514.0972 2.4468.255h.3886l.0546-.1579-.1336-.0971-.1032-.0972L6.973 9.8356l-2.55-1.6879-1.3356-.9714-.7225-.4918-.3643-.4614-.1578-1.0078.6557-.7225.8803.0607.2246.0607.8925.686 1.9064 1.4754 2.4893 1.8336.3643.3035.1457-.1032.0182-.0728-.164-.2733-1.3539-2.4467-1.445-2.4893-.6435-1.032-.17-.6194c-.0607-.255-.1032-.4674-.1032-.7285L6.287.1335 6.6997 0l.9957.1336.419.3642.6192 1.4147 1.0018 2.2282 1.5543 3.0296.4553.8985.2429.8318.091.255h.1579v-.1457l.1275-1.706.2368-2.0947.2307-2.6957.0789-.7589.3764-.9107.7468-.4918.5828.2793.4797.686-.0668.4433-.2853 1.8517-.5586 2.9021-.3643 1.9429h.2125l.2429-.2429.9835-1.3053 1.6514-2.0643.7286-.8196.85-.9046.5464-.4311h1.0321l.759 1.1293-.34 1.1657-1.0625 1.3478-.8804 1.1414-1.2628 1.7-.7893 1.36.0729.1093.1882-.0183 2.8535-.607 1.5421-.2794 1.8396-.3157.8318.3886.091.3946-.3278.8075-1.967.4857-2.3072.4614-3.4364.8136-.0425.0304.0486.0607 1.5482.1457.6618.0364h1.621l3.0175.2247.7892.522.4736.6376-.079.4857-1.2142.6193-1.6393-.3886-3.825-.9107-1.3113-.3279h-.1822v.1093l1.0929 1.0686 2.0035 1.8092 2.5075 2.3314.1275.5768-.3218.4554-.34-.0486-2.2039-1.6575-.85-.7468-1.9246-1.621h-.1275v.17l.4432.6496 2.3436 3.5214.1214 1.0807-.17.3521-.6071.2125-.6679-.1214-1.3721-1.9246L14.38 17.959l-1.1414-1.9428-.1397.079-.674 7.2552-.3156.3703-.7286.2793-.6071-.4614-.3218-.7468.3218-1.4753.3886-1.9246.3157-1.53.2853-1.9004.17-.6314-.0121-.0425-.1397.0182-1.4328 1.9672-2.1796 2.9446-1.7243 1.8456-.4128.164-.7164-.3704.0667-.6618.4008-.5889 2.386-3.0357 1.4389-1.882.929-1.0868-.0062-.1579h-.0546l-6.3385 4.1164-1.1293.1457-.4857-.4554.0608-.7467.2307-.2429 1.9064-1.3114Z"/></svg>',
    perplexity: '<svg viewBox="0 0 24 24" aria-hidden="true"><path fill="#1FB8CD" d="M22.3977 7.0896h-2.3106V.0676l-7.5094 6.3542V.1577h-1.1554v6.1966L4.4904 0v7.0896H1.6023v10.3976h2.8882V24l6.932-6.3591v6.2005h1.1554v-6.0469l6.9318 6.1807v-6.4879h2.8882V7.0896zm-3.4657-4.531v4.531h-5.355l5.355-4.531zm-13.2862.0676 4.8691 4.4634H5.6458V2.6262zM2.7576 16.332V8.245h7.8476l-6.1149 6.1147v1.9723H2.7576zm2.8882 5.0404v-3.8852h.0001v-2.6488l5.7763-5.7764v7.0111l-5.7764 5.2993zm12.7086.0248-5.7766-5.1509V9.0618l5.7766 5.7766v6.5588zm2.8882-5.0652h-1.733v-1.9723L13.3948 8.245h7.8478v8.087z"/></svg>',
    gemini: '<svg viewBox="0 0 24 24" aria-hidden="true"><path fill="#8E75B2" d="M11.04 19.32Q12 21.51 12 24q0-2.49.93-4.68.96-2.19 2.58-3.81t3.81-2.55Q21.51 12 24 12q-2.49 0-4.68-.93a12.3 12.3 0 0 1-3.81-2.58 12.3 12.3 0 0 1-2.58-3.81Q12 2.49 12 0q0 2.49-.96 4.68-.93 2.19-2.55 3.81a12.3 12.3 0 0 1-3.81 2.58Q2.49 12 0 12q2.49 0 4.68.96 2.19.93 3.81 2.55t2.55 3.81"/></svg>'
  };
  var AIS = [
    {id: 'chatgpt', name: 'ChatGPT', url: function (q) { return 'https://chatgpt.com/?q=' + encodeURIComponent(q); }},
    {id: 'claude', name: 'Claude', url: function (q) { return 'https://claude.ai/new?q=' + encodeURIComponent(q); }},
    {id: 'perplexity', name: 'Perplexity', note: 'good for sources & videos', url: function (q) { return 'https://www.perplexity.ai/search?q=' + encodeURIComponent(q); }},
    {id: 'gemini', name: 'Gemini', note: 'paste the copied prompt', copyOnly: true, url: function () { return 'https://gemini.google.com/app'; }}
  ];

  /* ---------- styles ---------- */
  var css = document.createElement('style');
  css.textContent =
    '.aa-menu{position:fixed;z-index:70;width:min(340px,calc(100vw - 24px));background:var(--surface);color:var(--ink);border:1px solid var(--line);border-radius:12px;box-shadow:0 18px 50px rgba(0,0,0,.22);padding:12px;font:14px/1.4 Inter,system-ui,sans-serif}' +
    '.aa-menu .aa-h{font-weight:700;font-size:12px;text-transform:uppercase;letter-spacing:.05em;color:var(--ink-soft);margin:0 0 2px}' +
    '.aa-menu .aa-t{font-family:Newsreader,Georgia,serif;font-size:16px;margin:0 0 10px;line-height:1.3}' +
    '.aa-menu textarea{width:100%;box-sizing:border-box;font:13.5px/1.45 Inter,system-ui,sans-serif;color:var(--ink);background:var(--paper);border:1px solid var(--line);border-radius:8px;padding:8px 10px;resize:vertical;min-height:54px;margin:0 0 8px}' +
    '.aa-menu a,.aa-menu button{display:flex;align-items:center;gap:10px;width:100%;box-sizing:border-box;padding:8px 10px;border:0;border-radius:8px;background:none;color:var(--ink);font:600 14px Inter,system-ui,sans-serif;text-decoration:none;cursor:pointer;text-align:left}' +
    '.aa-menu a:hover,.aa-menu button:hover,.aa-menu a:focus-visible,.aa-menu button:focus-visible{background:var(--paper);outline:none;text-decoration:none}' +
    '.aa-menu svg{width:20px;height:20px;flex:none}' +
    '.aa-menu .aa-n{margin-left:auto;font-weight:400;font-size:12px;color:var(--ink-faint)}' +
    '.aa-menu hr{border:0;border-top:1px solid var(--line-soft);margin:6px 0}' +
    '.aa-menu .aa-i{width:20px;text-align:center;flex:none}' +
    '.aa-menu .aa-f{font-size:11.5px;color:var(--ink-faint);margin:8px 2px 0;line-height:1.45}' +
    '.aa-toast{position:fixed;left:50%;bottom:72px;transform:translateX(-50%);z-index:80;background:var(--ink);color:var(--surface);padding:9px 14px;border-radius:999px;font:600 13px Inter,system-ui,sans-serif;box-shadow:var(--shadow);max-width:calc(100vw - 32px);text-align:center}' +
    '@media print{.aa-menu,.aa-toast{display:none!important}}';
  document.head.appendChild(css);

  /* ---------- turning the notes into plain text ---------- */
  var SKIP = [];
  var BLOCK = /^(P|DIV|LI|H1|H2|H3|H4|TR|UL|OL|TABLE|FIGURE|PRE|BLOCKQUOTE|SECTION)$/;
  function text(node, out) {
    if (node.nodeType === 3) { out.push(node.nodeValue.replace(/\s+/g, ' ')); return; }
    if (node.nodeType !== 1) return;
    var el = node, tag = el.tagName, cl = el.classList;
    if (tag === 'SCRIPT' || tag === 'STYLE' || tag === 'BUTTON' || cl.contains('askai-btn') || cl.contains('backtotop')) return;
    if (cl.contains('qmeta')) return;
    if (cl.contains('svg-wrap') || tag === 'svg') {
      var s = tag === 'svg' ? el : el.querySelector('svg'), cp = tag === 'svg' ? null : el.querySelector('.cap');
      out.push('\n[' + (cp ? cp.textContent.trim().replace(/^(Fig\s*\S+?)\.\s*/, '$1: ') : 'Diagram: ' + ((s && s.getAttribute('aria-label')) || 'see figure')) + ']\n'); return;
    }
    if (cl.contains('ov')) {   // a bar over a name means its complement: write Q0' for Q-bar with subscript 0
      var t = el.textContent.trim(), nx = el.nextSibling;
      if (nx && nx.nodeType === 1 && nx.tagName === 'SUB') { t += nx.textContent.trim(); SKIP.push(nx); }
      out.push(t.length > 2 && !/^[A-Za-z]\d*$/.test(t) ? '(' + t + ")'" : t + "'"); return;
    }
    if (SKIP.indexOf(el) >= 0) return;
    if (tag === 'SUP') { out.push('^' + el.textContent.trim()); return; }
    if (tag === 'BR') { out.push('\n'); return; }
    if (tag === 'TD' || tag === 'TH') { out.push(' | '); }
    if (BLOCK.test(tag)) out.push('\n');
    if (tag === 'LI') out.push('- ');
    for (var c = el.firstChild; c; c = c.nextSibling) text(c, out);
    if (BLOCK.test(tag)) out.push('\n');
  }
  function plain(nodes) {
    var out = [];
    nodes.forEach(function (n) { text(n, out); });
    return out.join('').replace(/[ \t]+\n/g, '\n').replace(/\n[ \t]+/g, '\n').replace(/\| \|/g, '|')
      .replace(/\n\s*\|\s*/g, '\n| ').replace(/\n{3,}/g, '\n\n').trim();
  }

  /* What part of the notes does a button belong to? */
  function chunk(btn) {
    var host = btn.closest('.qbox');
    var sec = btn.closest('section.section');
    var secLabel = sec ? sectionLabel(sec) : '';
    if (host) {
      var src = host.querySelector('.qsrc');
      return {label: 'Worked question' + (src ? ' (' + src.textContent.trim() + ')' : '') + (secLabel ? ' in ' + secLabel : ''),
        nodes: [host], anchor: host.id || (sec && sec.id) || ''};
    }
    var h = btn.closest('h2');
    if (h) {
      var nodes = [h];
      for (var n = h.nextElementSibling; n && n.tagName !== 'H2' && !n.classList.contains('backtotop'); n = n.nextElementSibling) nodes.push(n);
      return {label: clean(h) + (secLabel ? ' (from ' + secLabel + ')' : ''), nodes: nodes, anchor: h.id || (sec && sec.id) || ''};
    }
    // section heading: the intro up to the first sub-heading, plus the list of sub-headings
    var nodes2 = [], subs = [];
    for (var m = sec.querySelector('.section-head').nextElementSibling; m; m = m.nextElementSibling) {
      if (m.tagName === 'H2') { subs.push(clean(m)); continue; }
      if (!subs.length && !m.classList.contains('backtotop')) nodes2.push(m);
    }
    return {label: secLabel, nodes: nodes2, subs: subs, anchor: sec.id};
  }
  function clean(el) { var c = el.cloneNode(true); [].forEach.call(c.querySelectorAll('.askai-btn'), function (b) { b.remove(); }); return c.textContent.replace(/\s+/g, ' ').trim(); }
  function sectionLabel(s) {
    var t = s.querySelector('.section-head .tag'), h = s.querySelector('.section-head h1');
    return ((t && /^\d/.test(t.textContent.trim()) ? 'Topic ' + t.textContent.trim() + ': ' : '') + (h ? clean(h) : s.id));
  }
  function figures(nodes) {
    var figs = [];
    nodes.forEach(function (n) {
      var list = n.classList && n.classList.contains('svg-wrap') ? [n] : [].slice.call(n.querySelectorAll ? n.querySelectorAll('.svg-wrap') : []);
      list.forEach(function (w) {
        var svg = w.querySelector('svg'); if (!svg) return;
        var ce = w.querySelector('.cap') || (w.nextElementSibling && w.nextElementSibling.classList.contains('cap') ? w.nextElementSibling : null);
        var cap = ce ? ce.textContent.trim() : '';
        var m = cap.match(/^Fig\s*(\d+[a-z]?)/i);
        figs.push({svg: svg, name: m ? 'Fig ' + m[1] : 'diagram', cap: cap || svg.getAttribute('aria-label') || 'Diagram'});
      });
    });
    return figs;
  }

  /* ---------- the prompt (fixed template, no AI) ---------- */
  function prompt(c, doubt, limit) {
    var body = plain(c.nodes);
    var cut = false;
    if (body.length > limit) {
      body = body.slice(0, limit); var k = Math.max(body.lastIndexOf('. '), body.lastIndexOf('\n'));
      if (k > limit * 0.6) body = body.slice(0, k + 1);
      cut = true;
    }
    var link = (location.protocol === 'file:' && CTX.page ? CTX.page : location.origin + location.pathname) + (c.anchor ? '#' + c.anchor : '');
    var figs = figures(c.nodes);
    var L = [];
    L.push('I am a student revising ' + (CTX.course || 'my course') + (CTX.courseCode ? ' (' + CTX.courseCode + ')' : '') +
      ', Unit ' + CTX.unit + ': ' + CTX.unitTitle + '.');
    L.push('I have a doubt in this part of my class notes: "' + c.label + '".');
    L.push('');
    L.push('This is what my notes say:');
    L.push('"""');
    L.push(body || '(this part is mostly a diagram)');
    if (cut) L.push('[... trimmed. The full text is at the link below.]');
    if (c.subs && c.subs.length) L.push('\nSub-topics in this part: ' + c.subs.join('; '));
    L.push('"""');
    if (figs.length) L.push('The notes include ' + (figs.length === 1 ? 'a diagram' : figs.length + ' diagrams') + ': ' +
      figs.map(function (f) { return f.name; }).join(', ') + ', described in [brackets] above. I may paste the image too.');
    L.push('Link to this part of my notes: ' + link);
    L.push('');
    L.push('I have already read the explanation above and it did not make it clear for me. Please:');
    L.push('1. Explain it in a different way from my notes: an everyday analogy, a small worked example, or a step-by-step walk-through.');
    L.push('2. Stay within what my notes cover. Do not go far beyond my syllabus.');
    L.push('3. Point out the mistake students most often make here.');
    L.push('4. End with one short question I can answer to check that I understood.');
    L.push('5. If a video would help, tell me what to search for on YouTube. Do not make up video links.');
    L.push('');
    L.push('My doubt: ' + (doubt || 'I am not sure exactly what I am missing. Start with the core idea.'));
    return L.join('\n');
  }

  /* ---------- helpers ---------- */
  function toast(msg) {
    [].forEach.call(document.querySelectorAll('.aa-toast'), function (x) { x.remove(); });
    var t = document.createElement('div'); t.className = 'aa-toast'; t.setAttribute('role', 'status'); t.textContent = msg;
    document.body.appendChild(t); setTimeout(function () { t.remove(); }, 3800);
  }
  function copyText(s) {
    if (navigator.clipboard && navigator.clipboard.writeText) return navigator.clipboard.writeText(s).then(function () { return true; }, fallback);
    return Promise.resolve(fallback());
    function fallback() {
      var ta = document.createElement('textarea'); ta.value = s; ta.style.position = 'fixed'; ta.style.opacity = '0';
      document.body.appendChild(ta); ta.select(); var ok = false; try { ok = document.execCommand('copy'); } catch (e) {} ta.remove(); return ok;
    }
  }
  function png(svg) {   // the diagram as a picture, made only when asked for
    return new Promise(function (res, rej) {
      var vb = (svg.getAttribute('viewBox') || '0 0 600 300').split(/[\s,]+/).map(Number);
      var w = vb[2], h = vb[3], scale = Math.min(3, 1600 / w);
      var c = svg.cloneNode(true);
      c.setAttribute('xmlns', 'http://www.w3.org/2000/svg'); c.setAttribute('width', w); c.setAttribute('height', h);
      var bg = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
      bg.setAttribute('x', vb[0]); bg.setAttribute('y', vb[1]); bg.setAttribute('width', w); bg.setAttribute('height', h); bg.setAttribute('fill', '#FFFFFF');
      c.insertBefore(bg, c.firstChild);
      if (!c.querySelector('style')) {
        var st = document.createElementNS('http://www.w3.org/2000/svg', 'style');
        st.textContent = 'text{font-family:Inter,Arial,sans-serif}'; c.insertBefore(st, c.firstChild);
      }
      var img = new Image();
      img.onload = function () {
        var cv = document.createElement('canvas'); cv.width = Math.round(w * scale); cv.height = Math.round(h * scale);
        var g = cv.getContext('2d'); g.drawImage(img, 0, 0, cv.width, cv.height);
        cv.toBlob(function (b) { b ? res(b) : rej(new Error('no image')); }, 'image/png');
      };
      img.onerror = function () { rej(new Error('could not draw diagram')); };
      img.src = 'data:image/svg+xml;charset=utf-8,' + encodeURIComponent(new XMLSerializer().serializeToString(c));
    });
  }
  var wide = function () { return window.matchMedia('(pointer:fine)').matches && window.innerWidth > 900; };
  function openSide(url) {      // desktop: a narrow window beside the notes; phone: the normal way (opens the app if installed)
    if (!wide()) return false;
    var W = Math.min(560, Math.round(screen.availWidth * 0.4)), H = Math.round(screen.availHeight * 0.9);
    var L = (screen.availLeft || 0) + screen.availWidth - W, T = (screen.availTop || 0) + 20;
    var win = window.open(url, 'askai', 'popup=yes,width=' + W + ',height=' + H + ',left=' + L + ',top=' + T);
    if (win) { try { win.focus(); } catch (e) {} return true; }
    return false;
  }

  /* ---------- the menu ---------- */
  var menu, current, lastBtn;
  function close() { if (menu) { menu.remove(); menu = null; } if (lastBtn) { lastBtn.setAttribute('aria-expanded', 'false'); } }
  function place(btn) {
    // place it inside the part of the page that is actually on screen (phones may be zoomed or scrolled sideways)
    var vv = window.visualViewport, VW = vv ? vv.width : window.innerWidth, VH = vv ? vv.height : window.innerHeight,
      OX = vv ? vv.offsetLeft : 0, OY = vv ? vv.offsetTop : 0;
    if (VW <= 640) {
      menu.style.width = (VW - 24) + 'px'; menu.style.maxHeight = Math.round(VH * 0.8) + 'px'; menu.style.overflow = 'auto';
      menu.style.left = (OX + 12) + 'px'; menu.style.top = Math.max(OY + 12, OY + VH - menu.offsetHeight - 12) + 'px';
    } else {
      var r = btn.getBoundingClientRect(), mw = menu.offsetWidth, mh = menu.offsetHeight;
      var left = Math.min(Math.max(OX + 12, r.right - mw), OX + VW - mw - 12);
      var top = r.bottom + 6 + mh > OY + VH - 12 ? Math.max(OY + 12, r.top - mh - 6) : r.bottom + 6;
      menu.style.left = left + 'px'; menu.style.top = top + 'px';
    }
  }
  function build(btn) {
    close();
    lastBtn = btn; btn.setAttribute('aria-expanded', 'true');
    current = chunk(btn);
    var figs = figures(current.nodes);
    menu = document.createElement('div'); menu.className = 'aa-menu'; menu.setAttribute('role', 'dialog'); menu.setAttribute('aria-label', 'Ask an AI about this part');
    var h = '<p class="aa-h">Ask AI about</p><p class="aa-t"></p>' +
      '<textarea placeholder="What\'s confusing? (optional) e.g. why does Q1 change on the falling edge?" aria-label="Your doubt (optional)"></textarea>';
    AIS.forEach(function (a) {
      h += '<a href="#" data-ai="' + a.id + '" target="_blank" rel="noopener">' + ICON[a.id] + a.name + (a.note ? '<span class="aa-n">' + a.note + '</span>' : '') + '</a>';
    });
    h += '<hr><button type="button" data-act="copy"><span class="aa-i">📋</span>Copy prompt</button>';
    figs.forEach(function (f, i) { h += '<button type="button" data-act="fig" data-i="' + i + '"><span class="aa-i">🖼</span>Copy ' + f.name + ' as image</button>'; });
    if (navigator.share) h += '<button type="button" data-act="share"><span class="aa-i">↗</span>Share to an app…' + (figs.length ? '<span class="aa-n">with diagram</span>' : '') + '</button>';
    h += '<p class="aa-f">Opens the chat with this part of your notes filled in. Free, uses your own account. The prompt is also copied, in case you need to paste it.</p>';
    menu.innerHTML = h;
    menu.querySelector('.aa-t').textContent = current.label;
    document.body.appendChild(menu);
    place(btn);
    var ta = menu.querySelector('textarea');
    menu.addEventListener('click', function (ev) { act(ev, ta.value.trim(), figs); });
    menu.addEventListener('keydown', function (ev) { if (ev.key === 'Escape') { close(); btn.focus(); } });
    setTimeout(function () { (wide() ? ta : menu.querySelector('a')).focus(); }, 20);
  }
  function count(what) {   // anonymous tally of which parts people ask about (GoatCounter event; nothing if it isn't loaded)
    try {
      if (window.goatcounter && window.goatcounter.count)
        window.goatcounter.count({path: 'ask-ai/' + (CTX.code || '') + '/unit-' + CTX.unit + '/' + (current.anchor || '') + '/' + what,
          title: (CTX.code || '') + ' U' + CTX.unit + ' · ' + current.label + ' → ' + what, event: true});
    } catch (e) {}
  }
  function act(ev, doubt, figs) {
    var a = ev.target.closest('a[data-ai],button[data-act]'); if (!a) return;
    count(a.dataset.ai || a.dataset.act);
    var full = prompt(current, doubt, MAX_FULL);
    if (a.dataset.ai) {
      var ai = AIS.filter(function (x) { return x.id === a.dataset.ai; })[0];
      var short = prompt(current, doubt, MAX_TEXT);
      var url = ai.url(short);
      a.href = url;                     // the link opens this, if the side window is blocked or on phones
      copyText(full);
      if (openSide(url)) ev.preventDefault();
      toast(ai.copyOnly ? 'Prompt copied. Paste it into ' + ai.name + ' (Ctrl+V or long-press, Paste).' :
        (short.length < full.length ? 'Opening ' + ai.name + '. The section was long: the full prompt is copied, paste it if needed.' : 'Opening ' + ai.name + '…'));
      close(); return;
    }
    var k = a.dataset.act;
    if (k === 'copy') { copyText(full).then(function (ok) { toast(ok ? 'Prompt copied. Paste it into any AI chat.' : 'Could not copy on this browser.'); }); close(); }
    else if (k === 'fig') {
      var f = figs[+a.dataset.i];
      if (!(window.ClipboardItem && navigator.clipboard && navigator.clipboard.write)) { toast('This browser cannot copy images. Try "Share to an app" or a screenshot.'); return; }
      navigator.clipboard.write([new ClipboardItem({'image/png': png(f.svg)})]).then(
        function () { toast(f.name + ' copied. Paste it into the chat with Ctrl+V.'); },
        function () { toast('Could not copy the image on this browser. Try a screenshot.'); });
      close();
    } else if (k === 'share') {
      var data = {title: current.label, text: full};
      Promise.all(figs.slice(0, 3).map(function (f, i) {
        return png(f.svg).then(function (b) { return new File([b], (f.name.replace(/\s+/g, '-') || 'diagram-' + i) + '.png', {type: 'image/png'}); }, function () { return null; });
      })).then(function (files) {
        files = files.filter(Boolean);
        if (files.length && navigator.canShare && navigator.canShare({files: files, text: full})) data.files = files;
        return navigator.share(data);
      }).catch(function (e) { if (e && e.name !== 'AbortError') toast('Sharing did not work here. Use Copy prompt instead.'); });
      close();
    }
  }
  document.addEventListener('click', function (ev) {
    if (menu && !menu.contains(ev.target) && !ev.target.closest('.askai-btn')) close();
  });
  document.addEventListener('keydown', function (ev) { if (ev.key === 'Escape' && menu) close(); });
  window.addEventListener('resize', close);

  /* ---------- the Videos list ---------- */
  var YT = '<svg viewBox="0 0 24 24" aria-hidden="true"><path fill="#FF0000" d="M23.5 6.2a3 3 0 0 0-2.1-2.1C19.5 3.6 12 3.6 12 3.6s-7.5 0-9.4.5A3 3 0 0 0 .5 6.2 31 31 0 0 0 0 12a31 31 0 0 0 .5 5.8 3 3 0 0 0 2.1 2.1c1.9.5 9.4.5 9.4.5s7.5 0 9.4-.5a3 3 0 0 0 2.1-2.1A31 31 0 0 0 24 12a31 31 0 0 0-.5-5.8z"/><path fill="#FFF" d="M9.6 15.6 15.8 12 9.6 8.4z"/></svg>';
  function esc(x) { return String(x).replace(/[&<>"]/g, function (c) { return {'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;'}[c]; }); }
  function buildVideos(btn) {
    close();
    var x = (window.VIDEOS || [])[+btn.dataset.vid]; if (!x) return;
    lastBtn = btn; btn.setAttribute('aria-expanded', 'true');
    var sec = document.getElementById(x.s);
    current = {anchor: x.s, label: x.h || (sec ? sectionLabel(sec) : x.s)};
    menu = document.createElement('div'); menu.className = 'aa-menu aa-vid'; menu.setAttribute('role', 'dialog'); menu.setAttribute('aria-label', 'Videos on this part');
    var h = '<p class="aa-h">Videos on</p><p class="aa-t">' + esc(current.label) + '</p>';
    x.v.forEach(function (v) {
      var url = 'https://www.youtube.com/watch?v=' + v[0] + (v[6] ? '&t=' + v[6] + 's' : '');
      var from = v[6] ? ' · from ' + Math.floor(v[6] / 60) + ':' + ('0' + v[6] % 60).slice(-2) : '';
      h += '<a class="aa-v" href="' + url + '" target="_blank" rel="noopener" data-v="' + v[0] + '">' + YT +
        '<span class="aa-vt"><b>' + esc(v[1]) + '</b><span class="aa-vm">' + esc(v[2]) + ' · ' + esc(v[3]) + from +
        (v[4] === 'numerical' ? ' <span class="aa-tag">solved problem</span>' : '') + '</span>' +
        (v[5] ? '<span class="aa-vn">⚠ ' + esc(v[5]) + '</span>' : '') + '</span></a>';
    });
    h += '<p class="aa-f">Videos may use different notation or conventions than your notes. In exams, follow the notes.</p>';
    menu.innerHTML = h;
    document.body.appendChild(menu);
    place(btn);
    menu.addEventListener('click', function (ev) { var a = ev.target.closest('a[data-v]'); if (a) { count('video-' + a.dataset.v); close(); } });
    menu.addEventListener('keydown', function (ev) { if (ev.key === 'Escape') { close(); btn.focus(); } });
    setTimeout(function () { var a = menu && menu.querySelector('a'); if (a) a.focus(); }, 20);
  }
  css.textContent +=
    '.aa-menu a.aa-v{align-items:flex-start;padding:9px 10px}' +
    '.aa-menu a.aa-v svg{width:22px;height:22px;margin-top:1px}' +
    '.aa-vt{display:flex;flex-direction:column;gap:2px;min-width:0}' +
    '.aa-vt b{font-weight:600;font-size:13.5px;line-height:1.35}' +
    '.aa-vm{font-weight:400;font-size:12px;color:var(--ink-faint)}' +
    '.aa-vn{font-weight:400;font-size:12px;color:var(--ink-soft);line-height:1.4}' +
    '.aa-tag{display:inline-block;margin-left:4px;padding:0 6px;border-radius:999px;background:var(--paper);border:1px solid var(--line);color:var(--ink-soft);font-size:11px}' +
    '.aa-menu.aa-vid{width:min(380px,calc(100vw - 24px))}';

  window.AskAI = {open: function (btn) { if (menu && lastBtn === btn) { close(); return; } if (btn.dataset.vid) buildVideos(btn); else build(btn); }};
})();
