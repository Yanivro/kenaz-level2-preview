/* KENAZ Level 2 — analytics with cookie consent: Google Analytics 4 + Microsoft Clarity
   -------------------------------------------------------------------------------------
   Nothing loads until the visitor accepts. Choice is remembered in localStorage.
   Both IDs below are public (they ship in page source) — not secrets.
   - Clarity:  clarity.microsoft.com → project → Settings → "Clarity project id"
   - GA4:      analytics.google.com → Admin → Data Streams → web stream → "Measurement ID"    */
(function () {
  var CLARITY_ID = 'xn6q18q3lw';        // Clarity project "KENAZ Level 2"
  var GA4_ID     = 'G-SWKVTGGXT6';       // GA4 property 545861585 "KENAZ Level 2"
  var STORE_KEY  = 'kenaz_consent_v1';

  var gaOn      = /^G-[A-Z0-9]{6,}$/.test(GA4_ID);
  var clarityOn = /^[a-z0-9]{6,}$/i.test(CLARITY_ID);
  var page = (location.pathname.split('/').pop() || 'index.html');

  window.dataLayer = window.dataLayer || [];
  function gtag(){ dataLayer.push(arguments); }
  window.track = function(){};   // no-op until consent is granted

  /* ---------- load providers + wire events (only after consent) ---------- */
  function initAnalytics(){
    if (window.__kenazAnalytics) return; window.__kenazAnalytics = true;

    if (gaOn) {
      var g = document.createElement('script');
      g.async = true;
      g.src = 'https://www.googletagmanager.com/gtag/js?id=' + GA4_ID;
      document.head.appendChild(g);
      gtag('js', new Date());
      gtag('config', GA4_ID, { anonymize_ip: true });
    }

    if (clarityOn) {
      (function(c,l,a,r,i,t,y){
        c[a]=c[a]||function(){(c[a].q=c[a].q||[]).push(arguments)};
        t=l.createElement(r);t.async=1;t.src="https://www.clarity.ms/tag/"+i;
        y=l.getElementsByTagName(r)[0];y.parentNode.insertBefore(t,y);
      })(window,document,"clarity","script",CLARITY_ID);
    }

    function track(name, params){
      params = params || {};
      if (gaOn) gtag('event', name, params);
      if (clarityOn && window.clarity){
        try {
          window.clarity('event', name);
          Object.keys(params).forEach(function(k){ window.clarity('set', k, String(params[k])); });
        } catch(e){}
      }
    }
    window.track = track;
    if (clarityOn && window.clarity){ try { window.clarity('set', 'page', page); } catch(e){} }

    /* CTA / button clicks (which buttons get clicked) */
    document.addEventListener('click', function(ev){
      var el = ev.target.closest('a.btn, button.btn, .nav-cta, [data-cta]');
      if(!el) return;
      var label = (el.getAttribute('data-cta') || el.textContent || '').trim().replace(/\s+/g,' ').slice(0,80);
      track('cta_click', { cta_text: label, cta_href: el.getAttribute('href') || '', page: page });
    }, true);

    /* outbound links */
    document.addEventListener('click', function(ev){
      var a = ev.target.closest('a[href]');
      if(!a) return;
      var href = a.getAttribute('href') || '';
      if(/^https?:\/\//i.test(href) && a.host && a.host !== location.host){
        track('outbound_click', { url: href, page: page });
      }
    }, true);

    /* scroll depth (25 / 50 / 75 / 100%) */
    var marks = [25,50,75,100], hit = {};
    window.addEventListener('scroll', function(){
      var d = document.documentElement;
      var max = d.scrollHeight - window.innerHeight;
      if (max <= 0) return;
      var pct = (window.scrollY / max) * 100;
      for (var i=0;i<marks.length;i++){
        var m = marks[i];
        if (pct >= m && !hit[m]){ hit[m]=1; track('scroll_depth', { percent: m, page: page }); }
      }
    }, { passive: true });
  }

  /* ---------- consent gate ---------- */
  var choice = null;
  try { choice = localStorage.getItem(STORE_KEY); } catch(e){}
  if (choice === 'granted') initAnalytics();
  else if (choice !== 'denied') showConsentBanner();

  function decide(v){
    try { localStorage.setItem(STORE_KEY, v); } catch(e){}
    var el = document.getElementById('kz-consent');
    if (el && el.parentNode) el.parentNode.removeChild(el);
    if (v === 'granted') initAnalytics();
  }
  window.kenazSetConsent = decide;   // lets a "cookie settings" link re-trigger if you add one

  function showConsentBanner(){
    function build(){
      if (document.getElementById('kz-consent')) return;
      var css =
        '#kz-consent{position:fixed;left:0;right:0;bottom:0;z-index:9999;display:flex;justify-content:center;'+
        'padding:16px;pointer-events:none;font-family:"Raleway",-apple-system,system-ui,sans-serif}'+
        '#kz-consent .kz-in{pointer-events:auto;max-width:780px;width:100%;background:#1b1b1b;color:#fff;'+
        'border:1px solid rgba(212,175,55,.4);border-radius:6px;box-shadow:0 12px 40px rgba(0,0,0,.4);'+
        'padding:17px 20px;display:flex;gap:18px;align-items:center;flex-wrap:wrap;justify-content:space-between}'+
        '#kz-consent p{margin:0;font-size:13.5px;line-height:1.55;color:rgba(255,255,255,.82);font-weight:300;flex:1 1 340px}'+
        '#kz-consent a{color:#d4af37;text-decoration:underline}'+
        '#kz-consent .kz-btns{display:flex;gap:10px;flex:0 0 auto}'+
        '#kz-consent button{font-family:inherit;font-size:12px;letter-spacing:.1em;text-transform:uppercase;'+
        'font-weight:500;cursor:pointer;padding:11px 20px;border-radius:3px;border:1px solid;transition:.25s}'+
        '#kz-consent .kz-no{background:transparent;color:rgba(255,255,255,.8);border-color:rgba(255,255,255,.35)}'+
        '#kz-consent .kz-no:hover{border-color:#fff;color:#fff}'+
        '#kz-consent .kz-yes{background:#d4af37;color:#241d05;border-color:#d4af37}'+
        '#kz-consent .kz-yes:hover{background:#e0bd4f}'+
        '@media(max-width:560px){#kz-consent .kz-in{flex-direction:column;align-items:stretch}#kz-consent .kz-btns{justify-content:flex-end}}';
      var style = document.createElement('style'); style.textContent = css; document.head.appendChild(style);

      var wrap = document.createElement('div');
      wrap.id = 'kz-consent';
      wrap.setAttribute('role','dialog');
      wrap.setAttribute('aria-label','Cookie consent');
      wrap.innerHTML =
        '<div class="kz-in">'+
          '<p>We use cookies for analytics (Google Analytics and Microsoft Clarity) to understand how this page is used and improve it. Nothing is loaded until you choose.</p>'+
          '<div class="kz-btns">'+
            '<button type="button" class="kz-no">Decline</button>'+
            '<button type="button" class="kz-yes">Accept</button>'+
          '</div>'+
        '</div>';
      document.body.appendChild(wrap);
      wrap.querySelector('.kz-yes').addEventListener('click', function(){ decide('granted'); });
      wrap.querySelector('.kz-no').addEventListener('click', function(){ decide('denied'); });
    }
    if (document.body) build();
    else document.addEventListener('DOMContentLoaded', build);
  }
})();
